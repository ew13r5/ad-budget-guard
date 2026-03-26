from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass
class MockRuleResult:
    rule_name: str
    action: str
    event_type: str
    message: str


class MockRuleChecker:
    """Simple built-in rules for demo: budget limit + anomaly detection."""

    def check(
        self,
        campaign_id: UUID,
        total_spend: Decimal,
        daily_budget: Decimal,
        delta: Decimal,
        avg_delta: Decimal,
    ) -> list[MockRuleResult]:
        results: list[MockRuleResult] = []

        if total_spend >= daily_budget:
            results.append(MockRuleResult(
                rule_name="budget_limit",
                action="soft_pause",
                event_type="budget_exceeded",
                message=f"Campaign {campaign_id}: spend {total_spend} >= budget {daily_budget}",
            ))

        if avg_delta > 0 and delta > avg_delta * 5:
            results.append(MockRuleResult(
                rule_name="anomaly_detection",
                action="hard_pause",
                event_type="anomaly_detected",
                message=f"Campaign {campaign_id}: delta {delta} > 5x avg {avg_delta}",
            ))

        return results
