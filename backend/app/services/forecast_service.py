"""Spend forecast service."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ad_account import AdAccount
from app.models.campaign import Campaign, CampaignStatus
from app.models.spend_snapshot import SpendSnapshot
from app.rules.models import ForecastResult
from app.schemas.common import SpendData

logger = logging.getLogger(__name__)

WARNING_THRESHOLD = Decimal("0.80")
CRITICAL_THRESHOLD = Decimal("0.95")
LOOKBACK_HOURS = 4


class ForecastService:
    """Calculates end-of-day spend forecasts."""

    def calculate(
        self,
        account_id: UUID,
        current_spend: SpendData,
        db: Session,
    ) -> ForecastResult:
        now_utc = datetime.now(timezone.utc)

        # Get account timezone
        account = db.query(AdAccount).filter(AdAccount.id == account_id).first()
        account_tz = ZoneInfo(account.timezone if account else "UTC")

        # Get total daily budget across active campaigns
        daily_budget_result = (
            db.query(func.sum(Campaign.daily_budget))
            .filter(
                Campaign.account_id == account_id,
                Campaign.status == CampaignStatus.ACTIVE,
                Campaign.daily_budget.isnot(None),
            )
            .scalar()
        )
        daily_budget = Decimal(str(daily_budget_result)) if daily_budget_result else Decimal("0")

        # Query recent snapshots (last N hours)
        lookback_start = now_utc - timedelta(hours=LOOKBACK_HOURS)
        snapshots = (
            db.query(SpendSnapshot.spend, SpendSnapshot.timestamp)
            .join(Campaign, SpendSnapshot.campaign_id == Campaign.id)
            .filter(
                Campaign.account_id == account_id,
                SpendSnapshot.timestamp >= lookback_start,
            )
            .order_by(SpendSnapshot.timestamp.asc())
            .all()
        )

        # Aggregate by timestamp
        time_totals: dict[datetime, Decimal] = {}
        for spend, ts in snapshots:
            time_totals[ts] = time_totals.get(ts, Decimal("0")) + spend

        sorted_times = sorted(time_totals.keys())

        # Calculate hourly rate
        if len(sorted_times) < 2:
            hourly_rate = Decimal("0")
            forecast_eod = current_spend.total_spend_today
        else:
            earliest = sorted_times[0]
            latest = sorted_times[-1]
            hours_elapsed = Decimal(str((latest - earliest).total_seconds())) / Decimal("3600")

            if hours_elapsed <= 0:
                hourly_rate = Decimal("0")
                forecast_eod = current_spend.total_spend_today
            else:
                total_earliest = time_totals[earliest]
                total_latest = time_totals[latest]
                hourly_rate = (total_latest - total_earliest) / hours_elapsed

                # Calculate remaining hours in account timezone
                now_local = now_utc.astimezone(account_tz)
                midnight = now_local.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                remaining_hours = Decimal(str((midnight - now_local).total_seconds())) / Decimal("3600")

                forecast_eod = current_spend.total_spend_today + (hourly_rate * remaining_hours)

        # Warning level
        if daily_budget <= 0:
            warning_level = "green"
        else:
            ratio = forecast_eod / daily_budget
            if ratio < WARNING_THRESHOLD:
                warning_level = "green"
            elif ratio < CRITICAL_THRESHOLD:
                warning_level = "yellow"
            else:
                warning_level = "red"

        return ForecastResult(
            account_id=account_id,
            current_spend_today=current_spend.total_spend_today,
            hourly_rate=hourly_rate,
            forecast_eod=forecast_eod,
            daily_budget=daily_budget,
            warning_level=warning_level,
            calculated_at=now_utc,
        )
