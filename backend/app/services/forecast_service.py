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

        # Calculate weighted hourly rate (recent 2 hours weighted 2x)
        if len(sorted_times) < 2:
            hourly_rate = Decimal("0")
            forecast_eod = current_spend.total_spend_today
        else:
            # Weighted average: recent 2 hours get 2x weight
            recent_cutoff = now_utc - timedelta(hours=2)
            weighted_deltas = []
            for i in range(1, len(sorted_times)):
                prev_t = sorted_times[i - 1]
                curr_t = sorted_times[i]
                dt_hours = Decimal(str((curr_t - prev_t).total_seconds())) / Decimal("3600")
                if dt_hours <= 0:
                    continue
                delta_spend = time_totals[curr_t] - time_totals[prev_t]
                rate = delta_spend / dt_hours
                weight = Decimal("2") if curr_t >= recent_cutoff else Decimal("1")
                weighted_deltas.append((rate, weight))

            if weighted_deltas:
                total_weight = sum(w for _, w in weighted_deltas)
                hourly_rate = sum(r * w for r, w in weighted_deltas) / total_weight
            else:
                earliest = sorted_times[0]
                latest = sorted_times[-1]
                hours_elapsed = Decimal(str((latest - earliest).total_seconds())) / Decimal("3600")
                hourly_rate = (time_totals[latest] - time_totals[earliest]) / hours_elapsed if hours_elapsed > 0 else Decimal("0")

            # Day-of-week adjustment: weekends typically have lower spend
            now_local = now_utc.astimezone(account_tz)
            is_weekend = now_local.weekday() >= 5
            if is_weekend:
                hourly_rate = hourly_rate * Decimal("0.8")

            # Calculate remaining hours in account timezone
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
