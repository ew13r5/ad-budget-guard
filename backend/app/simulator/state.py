from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

import structlog
from redis import Redis

from app.simulator.constants import (
    SIM_SPEND_PREFIX,
    SIM_STATE_KEY,
)

logger = structlog.get_logger(__name__)


@dataclass
class SimState:
    sim_time: datetime
    speed: int
    status: str
    tick_count: int
    scenario: str


@dataclass
class CampaignSpendState:
    campaign_id: UUID
    total_today: Decimal
    last_delta: Decimal
    last_tick: datetime


class SimulationStateManager:
    """Manages simulation state across Redis (hot) and PostgreSQL (persistence)."""

    def __init__(self, redis: Redis, db_session=None):
        self.redis = redis
        self.db_session = db_session

    def get_simulation_state(self) -> SimState:
        try:
            data = self.redis.hgetall(SIM_STATE_KEY)
        except Exception:
            logger.warning("redis_read_error", key=SIM_STATE_KEY)
            data = {}

        if not data:
            return SimState(
                sim_time=datetime.utcnow(),
                speed=1,
                status="stopped",
                tick_count=0,
                scenario="normal",
            )

        # Redis returns bytes, decode
        decoded = {k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v for k, v in data.items()}

        return SimState(
            sim_time=datetime.fromisoformat(decoded.get("sim_time", datetime.utcnow().isoformat())),
            speed=int(decoded.get("speed", "1")),
            status=decoded.get("status", "stopped"),
            tick_count=int(decoded.get("tick_count", "0")),
            scenario=decoded.get("scenario", "normal"),
        )

    def set_simulation_state(self, **kwargs) -> None:
        mapping = {}
        for k, v in kwargs.items():
            if isinstance(v, datetime):
                mapping[k] = v.isoformat()
            else:
                mapping[k] = str(v)
        if mapping:
            self.redis.hset(SIM_STATE_KEY, mapping=mapping)

    def update_campaign_spend(self, campaign_id: UUID, delta: Decimal) -> CampaignSpendState:
        key = f"{SIM_SPEND_PREFIX}{campaign_id}"
        now = datetime.utcnow().isoformat()

        # Integer cents arithmetic to avoid float precision loss
        raw = self.redis.hget(key, "total_cents")
        current_cents = int(raw) if raw else 0
        delta_cents = int(delta * 100)
        new_cents = current_cents + delta_cents
        total_str = f"{new_cents / 100:.2f}"

        pipe = self.redis.pipeline()
        pipe.hset(key, mapping={
            "total_cents": str(new_cents),
            "total_today": total_str,
            "last_delta": str(delta),
            "last_tick": now,
        })
        pipe.execute()

        return CampaignSpendState(
            campaign_id=campaign_id,
            total_today=Decimal(total_str),
            last_delta=delta,
            last_tick=datetime.fromisoformat(now),
        )

    def get_campaign_spend(self, campaign_id: UUID) -> Optional[CampaignSpendState]:
        key = f"{SIM_SPEND_PREFIX}{campaign_id}"
        data = self.redis.hgetall(key)
        if not data:
            return None

        decoded = {k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v for k, v in data.items()}
        return CampaignSpendState(
            campaign_id=campaign_id,
            total_today=Decimal(decoded.get("total_today", "0.00")),
            last_delta=Decimal(decoded.get("last_delta", "0.00")),
            last_tick=datetime.fromisoformat(decoded["last_tick"]) if "last_tick" in decoded else datetime.utcnow(),
        )

    def reset_state(self) -> None:
        cursor = 0
        while True:
            cursor, keys = self.redis.scan(cursor=cursor, match="simulation:*", count=100)
            if keys:
                self.redis.delete(*keys)
            if cursor == 0:
                break
