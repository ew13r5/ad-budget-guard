"""Rule evaluation engine."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from app.models.budget_rule import RuleType
from app.models.rule_evaluation import EvaluationResult
from app.rules.models import EvaluationContext, RuleResult
from app.rules.state import ConsecutiveStateManager

logger = logging.getLogger(__name__)


class RuleEvaluator:
    """Evaluates all budget rules for an account."""

    def __init__(
        self,
        tracker: ConsecutiveStateManager,
        consecutive_threshold: int = 2,
    ):
        self._tracker = tracker
        self._consecutive_threshold = consecutive_threshold

    def evaluate(self, context: EvaluationContext) -> list[RuleResult]:
        results: list[RuleResult] = []

        active_rules = [r for r in context.rules if r.is_active]
        # Campaign-level rules first (higher priority)
        active_rules.sort(key=lambda r: (0 if r.campaign_id else 1))

        for rule in active_rules:
            try:
                result = self._evaluate_single(rule, context)
                results.append(result)
            except Exception:
                logger.exception("Error evaluating rule %s", rule.id)
        return results

    def _evaluate_single(self, rule, context: EvaluationContext) -> RuleResult:
        entity_id = rule.campaign_id or context.account_id

        checkers = {
            RuleType.daily_limit: self._check_daily_limit,
            RuleType.monthly_limit: self._check_monthly_limit,
            RuleType.hourly_rate: self._check_hourly_rate,
            RuleType.anomaly: self._check_anomaly,
        }

        checker = checkers.get(rule.rule_type)
        if not checker:
            return RuleResult(
                rule_id=rule.id,
                rule_type=rule.rule_type,
                result=EvaluationResult.ok,
                current_value=Decimal("0"),
                threshold_value=rule.threshold,
                consecutive_count=0,
                action_required=False,
            )

        triggered, current_value, details = checker(rule, context)

        if triggered:
            count = self._tracker.increment(rule.id, entity_id)
        else:
            self._tracker.reset(rule.id, entity_id)
            count = 0

        if count >= self._consecutive_threshold:
            eval_result = EvaluationResult.triggered
            action_required = True
        elif count > 0:
            eval_result = EvaluationResult.warning
            action_required = False
        else:
            eval_result = EvaluationResult.ok
            action_required = False

        return RuleResult(
            rule_id=rule.id,
            rule_type=rule.rule_type,
            result=eval_result,
            current_value=current_value,
            threshold_value=rule.threshold,
            consecutive_count=count,
            action_required=action_required,
            details=details,
        )

    def _check_daily_limit(
        self, rule, context: EvaluationContext
    ) -> tuple[bool, Decimal, dict | None]:
        spend = context.spend_data.total_spend_today
        return spend >= rule.threshold, spend, None

    def _check_monthly_limit(
        self, rule, context: EvaluationContext
    ) -> tuple[bool, Decimal, dict | None]:
        spend = context.spend_data.total_spend_month
        return spend >= rule.threshold, spend, None

    def _check_hourly_rate(
        self, rule, context: EvaluationContext
    ) -> tuple[bool, Decimal, dict | None]:
        # Find campaign spend rate; if campaign-level rule, use specific campaign
        rate = Decimal("0")
        for cs in context.campaign_spends:
            if rule.campaign_id and cs.campaign_id == rule.campaign_id:
                rate = cs.spend_rate_per_hour
                break
            elif not rule.campaign_id:
                rate += cs.spend_rate_per_hour

        # threshold is percentage of daily budget — but we store it as absolute for simplicity
        return rate > rule.threshold, rate, {"spend_rate_per_hour": str(rate)}

    def _check_anomaly(
        self, rule, context: EvaluationContext
    ) -> tuple[bool, Decimal, dict | None]:
        snapshots = context.historical_snapshots
        if not snapshots:
            return False, Decimal("0"), None

        now = datetime.now(timezone.utc)
        window = timedelta(minutes=15)

        recent = [s for s in snapshots if (now - s.timestamp) <= window]
        historical = [s for s in snapshots if (now - s.timestamp) > window]

        if not recent or not historical:
            return False, Decimal("0"), None

        recent_spend = sum(s.spend for s in recent)
        avg_spend = sum(s.spend for s in historical) / len(historical) * len(recent)

        if avg_spend <= 0:
            return False, recent_spend, None

        multiplier = recent_spend / avg_spend
        triggered = multiplier >= rule.threshold

        return triggered, recent_spend, {
            "multiplier": str(multiplier),
            "avg_spend": str(avg_spend),
            "recent_spend": str(recent_spend),
        }
