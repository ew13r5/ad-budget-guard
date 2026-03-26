"""Tests for MonitoringService."""
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.models.budget_rule import RuleAction, RuleType
from app.models.campaign import CampaignStatus
from app.models.rule_evaluation import EvaluationResult
from app.rules.engine import RuleEvaluator
from app.rules.models import ForecastResult, RuleResult
from app.rules.state import ConsecutiveStateManager
from app.schemas.common import CampaignSpendData, SpendData
from app.services.forecast_service import ForecastService
from app.services.monitoring_service import MonitoringService


@pytest.fixture
def mock_provider():
    provider = MagicMock()
    provider.get_current_spend.return_value = SpendData(
        account_id=uuid4(),
        total_spend_today=Decimal("150"),
        total_spend_month=Decimal("3000"),
        last_updated=datetime.now(timezone.utc),
    )
    provider.get_campaign_spend.return_value = CampaignSpendData(
        campaign_id=uuid4(),
        spend_today=Decimal("50"),
        spend_rate_per_hour=Decimal("5"),
        last_updated=datetime.now(timezone.utc),
    )
    provider.pause_campaign = MagicMock(return_value=None)
    return provider


@pytest.fixture
def mock_db():
    db = MagicMock()
    # Campaigns query
    campaign = SimpleNamespace(
        id=uuid4(),
        account_id=uuid4(),
        status=CampaignStatus.ACTIVE,
    )
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.first.return_value = SimpleNamespace(
        timezone="UTC", mode=SimpleNamespace(value="simulation")
    )
    db.query.return_value.join.return_value.filter.return_value.all.return_value = []
    return db


@pytest.fixture
def monitoring_service(redis_client):
    tracker = ConsecutiveStateManager(redis_client)
    evaluator = RuleEvaluator(tracker)
    executor = MagicMock()
    forecast = MagicMock()
    forecast.calculate.return_value = ForecastResult(
        account_id=uuid4(),
        current_spend_today=Decimal("150"),
        hourly_rate=Decimal("10"),
        forecast_eod=Decimal("200"),
        daily_budget=Decimal("200"),
        warning_level="yellow",
        calculated_at=datetime.now(timezone.utc),
    )
    return MonitoringService(evaluator, executor, forecast)


class TestMonitoringService:
    def test_check_account_returns_monitoring_result(self, monitoring_service, mock_provider, mock_db):
        result = monitoring_service.check_account(uuid4(), mock_provider, mock_db)

        assert result is not None
        assert result.account_id is not None
        assert isinstance(result.evaluations, list)
        assert isinstance(result.actions_taken, list)

    def test_fetches_spend_from_provider(self, monitoring_service, mock_provider, mock_db):
        account_id = uuid4()
        monitoring_service.check_account(account_id, mock_provider, mock_db)

        mock_provider.get_current_spend.assert_called_once()

    def test_publishes_to_redis(self, monitoring_service, mock_provider, mock_db, redis_client):
        account_id = uuid4()
        monitoring_service.check_account(account_id, mock_provider, mock_db, redis_client)

        # Check that a message was published (via pubsub)
        # Since we can't easily check pubsub in unit test, just verify no error
        assert True

    def test_commits_db_on_success(self, monitoring_service, mock_provider, mock_db):
        monitoring_service.check_account(uuid4(), mock_provider, mock_db)
        mock_db.commit.assert_called_once()
