"""ReportService — generates report data from DB."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ad_account import AdAccount
from app.models.alert_log import AlertLog
from app.models.campaign import Campaign
from app.models.spend_snapshot import SpendSnapshot
from app.schemas.report import (
    CampaignBreakdown,
    DailySpend,
    Incident,
    ReportData,
)

logger = logging.getLogger(__name__)


class ReportService:
    """Generates report data objects from the database."""

    def __init__(self, db: Session):
        self._db = db

    def _get_account(self, account_id: UUID) -> AdAccount:
        account = self._db.query(AdAccount).filter(AdAccount.id == account_id).first()
        if account is None:
            raise ValueError(f"Account {account_id} not found")
        return account

    def _get_tz(self, account: AdAccount) -> ZoneInfo:
        try:
            return ZoneInfo(account.timezone)
        except Exception:
            return ZoneInfo("UTC")

    def _get_campaign_spends(
        self,
        account_id: UUID,
        start: datetime,
        end: datetime,
    ) -> list[CampaignBreakdown]:
        campaigns = (
            self._db.query(Campaign)
            .filter(Campaign.account_id == account_id)
            .all()
        )

        breakdowns = []
        for c in campaigns:
            total_spend = (
                self._db.query(func.sum(SpendSnapshot.spend))
                .filter(
                    SpendSnapshot.campaign_id == c.id,
                    SpendSnapshot.timestamp >= start,
                    SpendSnapshot.timestamp <= end,
                )
                .scalar()
            ) or Decimal("0.00")

            utilization = None
            if c.daily_budget and c.daily_budget > 0:
                days = max((end.date() - start.date()).days, 1)
                total_budget = c.daily_budget * days
                utilization = (total_spend / total_budget * 100).quantize(Decimal("0.1"))

            breakdowns.append(
                CampaignBreakdown(
                    campaign_id=c.id,
                    campaign_name=c.name,
                    spend=total_spend,
                    daily_budget=c.daily_budget,
                    utilization_pct=utilization,
                )
            )

        return breakdowns

    def _get_daily_spends(
        self,
        account_id: UUID,
        start: datetime,
        end: datetime,
    ) -> list[DailySpend]:
        campaigns = (
            self._db.query(Campaign.id)
            .filter(Campaign.account_id == account_id)
            .all()
        )
        campaign_ids = [c.id for c in campaigns]
        if not campaign_ids:
            return []

        rows = (
            self._db.query(
                func.date(SpendSnapshot.timestamp).label("day"),
                func.sum(SpendSnapshot.spend).label("total"),
            )
            .filter(
                SpendSnapshot.campaign_id.in_(campaign_ids),
                SpendSnapshot.timestamp >= start,
                SpendSnapshot.timestamp <= end,
            )
            .group_by(func.date(SpendSnapshot.timestamp))
            .order_by(func.date(SpendSnapshot.timestamp))
            .all()
        )

        return [DailySpend(date=row.day, spend=row.total) for row in rows]

    def _get_incidents(
        self,
        account_id: UUID,
        start: datetime,
        end: datetime,
    ) -> list[Incident]:
        alerts = (
            self._db.query(AlertLog)
            .filter(
                AlertLog.account_id == account_id,
                AlertLog.sent_at >= start,
                AlertLog.sent_at <= end,
            )
            .order_by(AlertLog.sent_at)
            .all()
        )

        return [
            Incident(
                timestamp=a.sent_at,
                alert_type=a.alert_type.value if hasattr(a.alert_type, 'value') else str(a.alert_type),
                severity=getattr(a, 'severity', 'info'),
                message=a.message,
            )
            for a in alerts
        ]

    def _generate(
        self,
        account_id: UUID,
        report_type: str,
        start_date: date,
        end_date: date,
    ) -> ReportData:
        account = self._get_account(account_id)
        tz = self._get_tz(account)

        start = datetime.combine(start_date, datetime.min.time(), tzinfo=tz)
        end = datetime.combine(end_date, datetime.max.time().replace(microsecond=0), tzinfo=tz)

        campaigns = self._get_campaign_spends(account_id, start, end)
        daily_spends = self._get_daily_spends(account_id, start, end)
        incidents = self._get_incidents(account_id, start, end)

        total_spend = sum(c.spend for c in campaigns)
        daily_budget_total = sum(
            c.daily_budget for c in campaigns if c.daily_budget
        ) or None

        return ReportData(
            account_id=account_id,
            account_name=account.name,
            report_type=report_type,
            date_from=start_date,
            date_to=end_date,
            currency=account.currency,
            total_spend=total_spend,
            daily_budget_total=daily_budget_total,
            campaigns=campaigns,
            daily_spends=daily_spends,
            incidents=incidents,
            generated_at=datetime.now(timezone.utc),
        )

    def generate_daily(
        self, account_id: UUID, target_date: Optional[date] = None,
    ) -> ReportData:
        d = target_date or date.today()
        return self._generate(account_id, "daily", d, d)

    def generate_weekly(
        self, account_id: UUID, end_date: Optional[date] = None,
    ) -> ReportData:
        d = end_date or date.today()
        start = d - timedelta(days=6)
        return self._generate(account_id, "weekly", start, d)

    def generate_monthly(
        self, account_id: UUID, end_date: Optional[date] = None,
    ) -> ReportData:
        d = end_date or date.today()
        start = d.replace(day=1)
        return self._generate(account_id, "monthly", start, d)
