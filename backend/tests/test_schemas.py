"""Tests for Pydantic schemas."""
import json
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4


class TestSpendData:
    def test_validates_decimal_fields(self):
        from app.schemas.common import SpendData
        data = SpendData(
            account_id=uuid4(),
            total_spend_today="45.67",  # string coerced
            total_spend_month="1234.56",
            last_updated=datetime.utcnow(),
        )
        assert data.total_spend_today == Decimal("45.67")
        assert data.total_spend_month == Decimal("1234.56")


class TestCampaignSpendData:
    def test_validates_decimal_fields(self):
        from app.schemas.common import CampaignSpendData
        data = CampaignSpendData(
            campaign_id=uuid4(),
            spend_today=Decimal("12.34"),
            spend_rate_per_hour=Decimal("5.00"),
            last_updated=datetime.utcnow(),
        )
        assert isinstance(data.spend_today, Decimal)


class TestActionResult:
    def test_serializes_to_json(self):
        from app.schemas.common import ActionResult
        uid = uuid4()
        result = ActionResult(success=True, message="paused", campaign_id=uid)
        js = result.model_dump_json()
        parsed = json.loads(js)
        assert parsed["success"] is True
        assert parsed["message"] == "paused"
        assert parsed["campaign_id"] == str(uid)


class TestInsightsData:
    def test_contains_daily_spend_list(self):
        from app.schemas.common import InsightsData, DailySpend
        data = InsightsData(
            account_id=uuid4(),
            daily_spend=[
                DailySpend(date=date(2026, 1, 1), spend=Decimal("100.00")),
                DailySpend(date=date(2026, 1, 2), spend=Decimal("200.00")),
            ],
        )
        assert len(data.daily_spend) == 2
        assert data.daily_spend[0].spend == Decimal("100.00")
