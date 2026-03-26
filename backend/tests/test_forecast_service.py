"""Tests for ForecastService."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from app.rules.models import ForecastResult
from app.schemas.common import SpendData
from app.services.forecast_service import ForecastService


def _make_spend_data(spend_today=Decimal("100"), spend_month=Decimal("2500")):
    return SpendData(
        account_id=uuid4(),
        total_spend_today=spend_today,
        total_spend_month=spend_month,
        last_updated=datetime.now(timezone.utc),
    )


def _mock_db(daily_budget=Decimal("200"), snapshots=None, tz="UTC"):
    """Create a mock DB session."""
    db = MagicMock()

    # Account query
    account = SimpleNamespace(timezone=tz)
    db.query.return_value.filter.return_value.first.return_value = account

    # Daily budget sum
    mock_budget_query = MagicMock()
    mock_budget_query.filter.return_value.scalar.return_value = daily_budget

    # Snapshot query
    mock_snap_query = MagicMock()
    mock_snap_query.join.return_value.filter.return_value.order_by.return_value.all.return_value = (
        snapshots or []
    )

    call_count = [0]
    original_query = db.query

    def side_effect(*args):
        call_count[0] += 1
        if call_count[0] == 1:
            return db.query.return_value  # AdAccount query
        elif call_count[0] == 2:
            return mock_budget_query  # sum(daily_budget)
        else:
            return mock_snap_query  # SpendSnapshot query

    db.query.side_effect = side_effect
    return db


class TestForecastService:
    def test_returns_forecast_result(self):
        account_id = uuid4()
        spend = _make_spend_data()
        db = _mock_db()

        service = ForecastService()
        result = service.calculate(account_id, spend, db)

        assert isinstance(result, ForecastResult)
        assert result.account_id == account_id

    def test_no_snapshots_returns_current_spend(self):
        spend = _make_spend_data(spend_today=Decimal("150"))
        db = _mock_db(snapshots=[])

        result = ForecastService().calculate(uuid4(), spend, db)

        assert result.forecast_eod == Decimal("150")
        assert result.hourly_rate == Decimal("0")

    def test_warning_green_below_80_percent(self):
        spend = _make_spend_data(spend_today=Decimal("50"))
        db = _mock_db(daily_budget=Decimal("200"), snapshots=[])

        result = ForecastService().calculate(uuid4(), spend, db)
        assert result.warning_level == "green"

    def test_warning_red_above_95_percent(self):
        spend = _make_spend_data(spend_today=Decimal("200"))
        db = _mock_db(daily_budget=Decimal("200"), snapshots=[])

        result = ForecastService().calculate(uuid4(), spend, db)
        assert result.warning_level == "red"

    def test_warning_green_when_no_budget(self):
        spend = _make_spend_data(spend_today=Decimal("500"))
        db = _mock_db(daily_budget=None, snapshots=[])

        result = ForecastService().calculate(uuid4(), spend, db)
        assert result.warning_level == "green"
