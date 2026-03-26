"""Tests for rule evaluation Pydantic models."""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.budget_rule import RuleType
from app.models.rule_evaluation import EvaluationResult
from app.rules.models import EvaluationContext, ForecastResult, MonitoringResult, RuleResult
from app.schemas.common import SpendData


def _make_spend_data(**kwargs):
    defaults = {
        "account_id": uuid4(),
        "total_spend_today": Decimal("100.00"),
        "total_spend_month": Decimal("2500.00"),
        "last_updated": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return SpendData(**defaults)


class TestEvaluationContext:
    def test_validates_required_fields(self):
        ctx = EvaluationContext(
            account_id=uuid4(),
            spend_data=_make_spend_data(),
        )
        assert ctx.account_id is not None
        assert ctx.campaign_spends == []
        assert ctx.rules == []

    def test_rejects_missing_account_id(self):
        with pytest.raises(ValidationError):
            EvaluationContext(spend_data=_make_spend_data())

    def test_accepts_empty_campaign_spends(self):
        ctx = EvaluationContext(
            account_id=uuid4(),
            spend_data=_make_spend_data(),
            campaign_spends=[],
        )
        assert len(ctx.campaign_spends) == 0


class TestRuleResult:
    def test_action_required_true_when_consecutive_met(self):
        rr = RuleResult(
            rule_id=uuid4(),
            rule_type=RuleType.daily_limit,
            result=EvaluationResult.triggered,
            current_value=Decimal("220.00"),
            threshold_value=Decimal("200.00"),
            consecutive_count=2,
            action_required=True,
        )
        assert rr.action_required is True

    def test_action_required_false_when_consecutive_not_met(self):
        rr = RuleResult(
            rule_id=uuid4(),
            rule_type=RuleType.daily_limit,
            result=EvaluationResult.triggered,
            current_value=Decimal("220.00"),
            threshold_value=Decimal("200.00"),
            consecutive_count=1,
            action_required=False,
        )
        assert rr.action_required is False

    def test_details_optional(self):
        rr = RuleResult(
            rule_id=uuid4(),
            rule_type=RuleType.anomaly,
            result=EvaluationResult.ok,
            current_value=Decimal("10.00"),
            threshold_value=Decimal("30.00"),
            consecutive_count=0,
            action_required=False,
        )
        assert rr.details is None


class TestMonitoringResult:
    def test_contains_expected_fields(self):
        mr = MonitoringResult(
            account_id=uuid4(),
            evaluations=[
                RuleResult(
                    rule_id=uuid4(),
                    rule_type=RuleType.daily_limit,
                    result=EvaluationResult.ok,
                    current_value=Decimal("50.00"),
                    threshold_value=Decimal("200.00"),
                    consecutive_count=0,
                    action_required=False,
                )
            ],
            actions_taken=[{"action": "none"}],
            timestamp=datetime.now(timezone.utc),
        )
        assert len(mr.evaluations) == 1
        assert len(mr.actions_taken) == 1
        assert mr.forecast is None


class TestForecastResult:
    @pytest.mark.parametrize("level", ["green", "yellow", "red"])
    def test_warning_level_accepts_valid_values(self, level):
        fr = ForecastResult(
            account_id=uuid4(),
            current_spend_today=Decimal("150.00"),
            hourly_rate=Decimal("12.50"),
            forecast_eod=Decimal("200.00"),
            daily_budget=Decimal("200.00"),
            warning_level=level,
            calculated_at=datetime.now(timezone.utc),
        )
        assert fr.warning_level == level
