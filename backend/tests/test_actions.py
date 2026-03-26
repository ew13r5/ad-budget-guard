"""Tests for ActionExecutor."""
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.models.budget_rule import RuleAction, RuleType
from app.alerts.alert_manager import AlertManager
from app.rules.actions import ActionExecutor


def _make_rule(**kwargs):
    defaults = {
        "id": uuid4(),
        "account_id": uuid4(),
        "campaign_id": None,
        "rule_type": RuleType.daily_limit,
        "threshold": Decimal("200.00"),
        "action": RuleAction.soft_pause,
        "is_active": True,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_mock_db(campaign_results=None):
    """Create a mock DB that handles both Campaign and AlertConfig queries."""
    from app.models.alert_config import AlertConfig
    from app.models.campaign import Campaign

    db = MagicMock()

    def _query_side_effect(model):
        q = MagicMock()
        if model is Campaign and campaign_results is not None:
            q.filter.return_value.all.return_value = campaign_results
        else:
            q.filter.return_value.all.return_value = []
        return q

    db.query.side_effect = _query_side_effect
    return db


@pytest.fixture
def mock_db():
    return _make_mock_db()


@pytest.fixture
def mock_provider():
    provider = MagicMock()
    provider.pause_campaign = MagicMock(return_value=None)
    return provider


@pytest.fixture
def alert_service():
    return AlertManager()


@pytest.fixture
def executor(alert_service):
    return ActionExecutor(alert_service)


class TestSoftPause:
    def test_calls_provider_pause(self, executor, mock_provider, mock_db):
        rule = _make_rule()
        campaign_id = uuid4()

        executor.execute_soft_pause(mock_provider, campaign_id, rule, Decimal("220"), mock_db)
        mock_provider.pause_campaign.assert_called_once_with(str(campaign_id))

    def test_creates_pause_log_on_success(self, executor, mock_provider, mock_db):
        rule = _make_rule()
        result = executor.execute_soft_pause(mock_provider, uuid4(), rule, Decimal("220"), mock_db)

        assert result is True
        # db.add called for: RuleEvaluation, PauseLog, AlertLog
        assert mock_db.add.call_count >= 2

    def test_creates_evaluation_on_success(self, executor, mock_provider, mock_db):
        rule = _make_rule()
        executor.execute_soft_pause(mock_provider, uuid4(), rule, Decimal("220"), mock_db)

        # First add should be RuleEvaluation
        args = mock_db.add.call_args_list
        assert len(args) >= 1

    def test_no_pause_log_on_failure(self, executor):
        provider = MagicMock()
        provider.pause_campaign.side_effect = Exception("API error")
        rule = _make_rule()
        mock_db = _make_mock_db()

        result = executor.execute_soft_pause(provider, uuid4(), rule, Decimal("220"), mock_db)

        assert result is False
        # Should still have RuleEvaluation but no PauseLog/AlertLog
        add_calls = mock_db.add.call_args_list
        # Only RuleEvaluation added (no PauseLog, no AlertLog)
        assert len(add_calls) == 1


class TestHardPause:
    def test_pauses_all_campaigns(self, executor, mock_provider):
        from app.models.campaign import CampaignStatus

        campaigns = [
            SimpleNamespace(id=uuid4(), status=CampaignStatus.ACTIVE),
            SimpleNamespace(id=uuid4(), status=CampaignStatus.ACTIVE),
            SimpleNamespace(id=uuid4(), status=CampaignStatus.ACTIVE),
        ]
        mock_db = _make_mock_db(campaign_results=campaigns)

        rule = _make_rule(action=RuleAction.hard_pause)
        count = executor.execute_hard_pause(mock_provider, rule.account_id, rule, Decimal("900"), mock_db)

        assert count == 3
        assert mock_provider.pause_campaign.call_count == 3

    def test_continues_on_single_failure(self, executor):
        from app.models.campaign import CampaignStatus

        campaigns = [
            SimpleNamespace(id=uuid4(), status=CampaignStatus.ACTIVE),
            SimpleNamespace(id=uuid4(), status=CampaignStatus.ACTIVE),
        ]
        mock_db = _make_mock_db(campaign_results=campaigns)

        provider = MagicMock()
        provider.pause_campaign.side_effect = [Exception("fail"), None]

        rule = _make_rule(action=RuleAction.hard_pause)
        count = executor.execute_hard_pause(provider, rule.account_id, rule, Decimal("900"), mock_db)

        # One succeeded, one failed
        assert count == 1
        assert provider.pause_campaign.call_count == 2
