"""Tests for MockRuleChecker."""
from decimal import Decimal
from uuid import uuid4

import pytest

from app.simulator.mock_rules import MockRuleChecker, MockRuleResult


@pytest.fixture
def checker():
    return MockRuleChecker()


@pytest.fixture
def cid():
    return uuid4()


class TestBudgetLimitCheck:
    def test_triggers_when_spend_meets_budget(self, checker, cid):
        results = checker.check(cid, Decimal("100"), Decimal("100"), Decimal("2"), Decimal("2"))
        budget_results = [r for r in results if r.rule_name == "budget_limit"]
        assert len(budget_results) == 1
        assert budget_results[0].action == "soft_pause"
        assert budget_results[0].event_type == "budget_exceeded"

    def test_triggers_when_spend_exceeds_budget(self, checker, cid):
        results = checker.check(cid, Decimal("110"), Decimal("100"), Decimal("2"), Decimal("2"))
        assert any(r.rule_name == "budget_limit" for r in results)

    def test_does_not_trigger_below_budget(self, checker, cid):
        results = checker.check(cid, Decimal("99.99"), Decimal("100"), Decimal("2"), Decimal("2"))
        assert not any(r.rule_name == "budget_limit" for r in results)


class TestAnomalyDetection:
    def test_triggers_on_spike(self, checker, cid):
        results = checker.check(cid, Decimal("50"), Decimal("100"), Decimal("11"), Decimal("2"))
        anomaly = [r for r in results if r.rule_name == "anomaly_detection"]
        assert len(anomaly) == 1
        assert anomaly[0].action == "hard_pause"
        assert anomaly[0].event_type == "anomaly_detected"

    def test_does_not_trigger_normal(self, checker, cid):
        results = checker.check(cid, Decimal("50"), Decimal("100"), Decimal("9"), Decimal("2"))
        assert not any(r.rule_name == "anomaly_detection" for r in results)

    def test_handles_zero_avg_delta(self, checker, cid):
        results = checker.check(cid, Decimal("50"), Decimal("100"), Decimal("5"), Decimal("0"))
        assert not any(r.rule_name == "anomaly_detection" for r in results)


class TestCheckCombined:
    def test_empty_when_no_triggers(self, checker, cid):
        results = checker.check(cid, Decimal("50"), Decimal("100"), Decimal("2"), Decimal("2"))
        assert results == []

    def test_both_rules_can_trigger(self, checker, cid):
        results = checker.check(cid, Decimal("100"), Decimal("100"), Decimal("20"), Decimal("2"))
        assert len(results) == 2
        names = {r.rule_name for r in results}
        assert names == {"budget_limit", "anomaly_detection"}

    def test_result_has_correct_fields(self, checker, cid):
        results = checker.check(cid, Decimal("100"), Decimal("100"), Decimal("2"), Decimal("2"))
        r = results[0]
        assert hasattr(r, "rule_name")
        assert hasattr(r, "action")
        assert hasattr(r, "event_type")
        assert hasattr(r, "message")
