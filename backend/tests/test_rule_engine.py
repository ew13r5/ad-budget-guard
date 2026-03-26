"""Tests for RuleEvaluator."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.budget_rule import RuleType
from app.models.rule_evaluation import EvaluationResult
from app.rules.engine import RuleEvaluator
from app.rules.models import EvaluationContext
from app.rules.state import ConsecutiveStateManager
from app.schemas.common import CampaignSpendData, SpendData


def _make_rule(**kwargs):
    """Create a mock BudgetRule-like object."""
    defaults = {
        "id": uuid4(),
        "account_id": uuid4(),
        "campaign_id": None,
        "rule_type": RuleType.daily_limit,
        "threshold": Decimal("200.00"),
        "action": "soft_pause",
        "is_active": True,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_context(spend_today=Decimal("100"), spend_month=Decimal("2500"),
                  rules=None, campaign_spends=None, snapshots=None):
    account_id = uuid4()
    return EvaluationContext(
        account_id=account_id,
        spend_data=SpendData(
            account_id=account_id,
            total_spend_today=spend_today,
            total_spend_month=spend_month,
            last_updated=datetime.now(timezone.utc),
        ),
        rules=rules or [],
        campaign_spends=campaign_spends or [],
        historical_snapshots=snapshots or [],
    )


@pytest.fixture
def evaluator(redis_client):
    tracker = ConsecutiveStateManager(redis_client, ttl=1800)
    return RuleEvaluator(tracker, consecutive_threshold=2)


class TestDailyLimit:
    def test_triggers_when_spend_exceeds_threshold(self, evaluator):
        rule = _make_rule(rule_type=RuleType.daily_limit, threshold=Decimal("200"))
        ctx = _make_context(spend_today=Decimal("220"), rules=[rule])

        # First eval: warning (count=1)
        results = evaluator.evaluate(ctx)
        assert results[0].result == EvaluationResult.warning
        assert results[0].action_required is False

        # Second eval: triggered (count=2)
        results = evaluator.evaluate(ctx)
        assert results[0].result == EvaluationResult.triggered
        assert results[0].action_required is True

    def test_ok_when_spend_below_threshold(self, evaluator):
        rule = _make_rule(rule_type=RuleType.daily_limit, threshold=Decimal("200"))
        ctx = _make_context(spend_today=Decimal("150"), rules=[rule])

        results = evaluator.evaluate(ctx)
        assert results[0].result == EvaluationResult.ok
        assert results[0].action_required is False


class TestMonthlyLimit:
    def test_triggers_when_monthly_spend_exceeds(self, evaluator):
        rule = _make_rule(rule_type=RuleType.monthly_limit, threshold=Decimal("5000"))
        ctx = _make_context(spend_month=Decimal("5200"), rules=[rule])

        evaluator.evaluate(ctx)  # warning
        results = evaluator.evaluate(ctx)  # triggered
        assert results[0].result == EvaluationResult.triggered


class TestHourlyRate:
    def test_triggers_when_rate_exceeds_threshold(self, evaluator):
        campaign_id = uuid4()
        rule = _make_rule(
            rule_type=RuleType.hourly_rate,
            threshold=Decimal("30"),
            campaign_id=campaign_id,
        )
        ctx = _make_context(
            rules=[rule],
            campaign_spends=[
                CampaignSpendData(
                    campaign_id=campaign_id,
                    spend_today=Decimal("100"),
                    spend_rate_per_hour=Decimal("35"),
                    last_updated=datetime.now(timezone.utc),
                )
            ],
        )
        evaluator.evaluate(ctx)
        results = evaluator.evaluate(ctx)
        assert results[0].result == EvaluationResult.triggered


class TestAnomaly:
    def test_triggers_on_spend_spike(self, evaluator):
        now = datetime.now(timezone.utc)
        # Create historical snapshots (low spend)
        historical = []
        for i in range(10):
            s = SimpleNamespace(
                spend=Decimal("5.00"),
                timestamp=now - timedelta(minutes=30 + i * 5),
            )
            historical.append(s)

        # Recent snapshots (high spike)
        recent = [
            SimpleNamespace(spend=Decimal("50.00"), timestamp=now - timedelta(minutes=5)),
            SimpleNamespace(spend=Decimal("50.00"), timestamp=now - timedelta(minutes=2)),
        ]

        rule = _make_rule(rule_type=RuleType.anomaly, threshold=Decimal("3"))
        ctx = _make_context(rules=[rule], snapshots=historical + recent)

        evaluator.evaluate(ctx)
        results = evaluator.evaluate(ctx)
        assert results[0].result == EvaluationResult.triggered
        assert results[0].details is not None


class TestRulePriority:
    def test_campaign_rules_evaluated_before_account(self, evaluator):
        campaign_id = uuid4()
        campaign_rule = _make_rule(
            rule_type=RuleType.daily_limit,
            threshold=Decimal("200"),
            campaign_id=campaign_id,
        )
        account_rule = _make_rule(
            rule_type=RuleType.monthly_limit,
            threshold=Decimal("5000"),
        )
        ctx = _make_context(spend_today=Decimal("100"), rules=[account_rule, campaign_rule])

        results = evaluator.evaluate(ctx)
        # Campaign-level rule should come first
        assert results[0].rule_type == RuleType.daily_limit
        assert results[1].rule_type == RuleType.monthly_limit


class TestDisabledRule:
    def test_disabled_rule_skipped(self, evaluator):
        rule = _make_rule(is_active=False)
        ctx = _make_context(rules=[rule])

        results = evaluator.evaluate(ctx)
        assert len(results) == 0


class TestConsecutiveState:
    def test_warning_at_count_1(self, evaluator):
        rule = _make_rule(rule_type=RuleType.daily_limit, threshold=Decimal("200"))
        ctx = _make_context(spend_today=Decimal("220"), rules=[rule])

        results = evaluator.evaluate(ctx)
        assert results[0].consecutive_count == 1
        assert results[0].result == EvaluationResult.warning

    def test_triggered_at_count_2(self, evaluator):
        rule = _make_rule(rule_type=RuleType.daily_limit, threshold=Decimal("200"))
        ctx = _make_context(spend_today=Decimal("220"), rules=[rule])

        evaluator.evaluate(ctx)
        results = evaluator.evaluate(ctx)
        assert results[0].consecutive_count == 2
        assert results[0].result == EvaluationResult.triggered
