from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

import structlog
from redis import Redis
from sqlalchemy.orm import Session

from app.simulator.constants import (
    DEFAULT_SCENARIO,
    DEFAULT_TICK_INTERVAL,
    FLUSH_EVERY_N_TICKS,
    FORCED_ANOMALY_TTL,
    PATTERN_ANOMALY,
    PATTERN_DECLINING,
    PATTERN_PEAK_HOURS,
    PATTERN_STEADY,
    SIM_FORCED_ANOMALY_PREFIX,
    SIM_PATTERN_PREFIX,
    SIM_PUBSUB_CHANNEL,
    SIM_TICK_LOCK_KEY,
    TICK_LOCK_TTL,
    VALID_SPEED_MULTIPLIERS,
    SimEventType,
)
from app.simulator.mock_rules import MockRuleChecker
from app.simulator.patterns import (
    AnomalyPattern,
    DecliningPattern,
    PeakHoursPattern,
    SpendPattern,
    SteadyPattern,
)
from app.simulator.scenarios import get_scenario_by_name
from app.simulator.state import CampaignSpendState, SimulationStateManager

logger = structlog.get_logger(__name__)

PATTERN_MAP: dict[str, type[SpendPattern]] = {
    PATTERN_STEADY: SteadyPattern,
    PATTERN_PEAK_HOURS: PeakHoursPattern,
    PATTERN_ANOMALY: AnomalyPattern,
    PATTERN_DECLINING: DecliningPattern,
}


@dataclass
class TickResult:
    campaign_id: UUID
    delta: Decimal
    total_spend: Decimal
    budget_percent: Decimal
    status: str
    events: list[dict] = field(default_factory=list)


class SimulatorEngine:
    """Central orchestrator for the spend simulation."""

    def __init__(self, state_manager: SimulationStateManager, redis: Redis, db_session: Optional[Session] = None):
        self.state_manager = state_manager
        self.redis = redis
        self.db_session = db_session
        self.mock_rules = MockRuleChecker()
        self._patterns: dict[UUID, SpendPattern] = {}
        self._campaigns: list = []

    def _acquire_lock(self) -> bool:
        return bool(self.redis.set(SIM_TICK_LOCK_KEY, "1", nx=True, ex=TICK_LOCK_TTL))

    def _release_lock(self) -> None:
        self.redis.delete(SIM_TICK_LOCK_KEY)

    def tick(self) -> list[TickResult]:
        if not self._acquire_lock():
            return []

        try:
            state = self.state_manager.get_simulation_state()
            if state.status != "running":
                return []

            elapsed_real = float(DEFAULT_TICK_INTERVAL)
            elapsed_sim = elapsed_real * state.speed
            new_sim_time = state.sim_time + timedelta(seconds=elapsed_sim)

            results: list[TickResult] = []
            events_to_publish: list[dict] = []

            for campaign in self._campaigns:
                try:
                    if campaign.get("status") == "PAUSED":
                        continue

                    cid = campaign["id"]
                    budget = campaign["daily_budget"]
                    pattern = self._get_pattern(cid)

                    spend_state = self.state_manager.get_campaign_spend(cid)
                    current_spend = spend_state.total_today if spend_state else Decimal("0")
                    remaining = budget - current_spend

                    # Check for forced anomaly
                    if isinstance(pattern, AnomalyPattern):
                        anomaly_key = f"{SIM_FORCED_ANOMALY_PREFIX}{cid}"
                        if self.redis.get(anomaly_key):
                            pattern.force_spike()
                            self.redis.delete(anomaly_key)

                    delta = pattern.calculate_delta(new_sim_time, budget, remaining, elapsed_sim)
                    updated = self.state_manager.update_campaign_spend(cid, delta)

                    budget_pct = (updated.total_today / budget * 100) if budget > 0 else Decimal("0")

                    # Check mock rules
                    avg_delta = updated.last_delta  # simplified: use last delta as avg
                    rule_results = self.mock_rules.check(cid, updated.total_today, budget, delta, avg_delta)

                    tick_events = []
                    for rr in rule_results:
                        campaign["status"] = "PAUSED"
                        event = {
                            "type": "sim_event",
                            "event": rr.event_type,
                            "campaign_id": str(cid),
                            "reason": rr.rule_name,
                            "sim_time": new_sim_time.isoformat(),
                        }
                        tick_events.append(event)
                        events_to_publish.append(event)

                    results.append(TickResult(
                        campaign_id=cid,
                        delta=delta,
                        total_spend=updated.total_today,
                        budget_percent=budget_pct,
                        status=campaign.get("status", "ACTIVE"),
                        events=tick_events,
                    ))

                except Exception:
                    logger.exception("tick_campaign_error", campaign_id=campaign.get("id"))
                    continue

            # Publish tick results
            tick_msg = {
                "type": "tick_update",
                "sim_time": new_sim_time.isoformat(),
                "tick_count": state.tick_count + 1,
                "campaigns": [
                    {
                        "campaign_id": str(r.campaign_id),
                        "total_spend": str(r.total_spend),
                        "delta_spend": str(r.delta),
                        "budget_percent": str(r.budget_percent),
                        "status": r.status,
                    }
                    for r in results
                ],
            }
            self.redis.publish(SIM_PUBSUB_CHANNEL, json.dumps(tick_msg))

            for event in events_to_publish:
                self.redis.publish(SIM_PUBSUB_CHANNEL, json.dumps(event))

            # Update state
            new_tick_count = state.tick_count + 1
            self.state_manager.set_simulation_state(
                sim_time=new_sim_time,
                tick_count=new_tick_count,
            )

            # Periodic flush
            if new_tick_count % FLUSH_EVERY_N_TICKS == 0:
                try:
                    self.state_manager.flush_to_postgres() if hasattr(self.state_manager, 'flush_to_postgres') else None
                except Exception:
                    logger.exception("flush_error")

            return results

        finally:
            self._release_lock()

    def _get_pattern(self, campaign_id: UUID) -> SpendPattern:
        if campaign_id in self._patterns:
            return self._patterns[campaign_id]

        # Try reading from Redis
        raw = self.redis.get(f"{SIM_PATTERN_PREFIX}{campaign_id}")
        pattern_type = raw.decode() if raw else PATTERN_STEADY
        cls = PATTERN_MAP.get(pattern_type, SteadyPattern)
        pattern = cls()
        self._patterns[campaign_id] = pattern
        return pattern

    def start(self, scenario: str = DEFAULT_SCENARIO) -> None:
        config = get_scenario_by_name(scenario)

        # Apply scenario to campaigns
        for campaign in self._campaigns:
            cid = campaign["id"]
            account_name = campaign.get("account_name", "")
            matched = False

            for sc in config.campaign_configs:
                if sc.campaign_filter == "all" or sc.campaign_filter == account_name:
                    cls = PATTERN_MAP.get(sc.pattern_type, SteadyPattern)
                    self._patterns[cid] = cls(volatility=sc.volatility)
                    self.redis.set(f"{SIM_PATTERN_PREFIX}{cid}", sc.pattern_type)

                    if sc.initial_spend_percent > 0:
                        initial = campaign["daily_budget"] * Decimal(str(sc.initial_spend_percent))
                        self.state_manager.update_campaign_spend(cid, initial)

                    campaign["status"] = "ACTIVE"
                    matched = True
                    break

            if not matched:
                self._patterns[cid] = SteadyPattern()
                campaign["status"] = "ACTIVE"

        self.state_manager.set_simulation_state(
            status="running",
            scenario=scenario,
            sim_time=datetime(2024, 1, 15, 0, 0, 0),
            tick_count=0,
            speed=1,
        )

    def pause(self) -> None:
        self.state_manager.set_simulation_state(status="paused")

    def reset(self) -> None:
        self.state_manager.reset_state()
        self._patterns.clear()
        self.state_manager.set_simulation_state(status="stopped")

    def set_speed(self, multiplier: int) -> None:
        if multiplier not in VALID_SPEED_MULTIPLIERS:
            raise ValueError(f"Speed must be one of {VALID_SPEED_MULTIPLIERS}, got {multiplier}")
        self.state_manager.set_simulation_state(speed=multiplier)

    def trigger_anomaly(self, campaign_id: UUID) -> None:
        self.redis.set(
            f"{SIM_FORCED_ANOMALY_PREFIX}{campaign_id}",
            "1",
            ex=FORCED_ANOMALY_TTL,
        )

    def set_campaigns(self, campaigns: list[dict]) -> None:
        """Set campaign data for the engine to iterate over."""
        self._campaigns = campaigns
