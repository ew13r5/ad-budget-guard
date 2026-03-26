from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad_account import AccountMode, AdAccount
from app.models.campaign import Campaign, CampaignStatus
from app.models.spend_snapshot import SpendSnapshot, SpendSource
from app.providers.base import AdDataProvider, SyncAdDataProvider
from app.schemas.common import (
    ActionResult,
    CampaignSpendData,
    DailySpend,
    DateRange,
    InsightsData,
    SpendData,
)
from app.simulator.constants import SIM_SPEND_PREFIX, SIM_STATE_KEY


class SimulationProvider(AdDataProvider):
    """Async provider reading simulation state from Redis + PostgreSQL."""

    def __init__(self, db, redis):
        self.db = db
        self.redis = redis

    async def get_accounts(self) -> list:
        result = await self.db.execute(
            select(AdAccount).where(AdAccount.mode == AccountMode.simulation)
        )
        return list(result.scalars().all())

    async def get_campaigns(self, account_id: UUID) -> list:
        result = await self.db.execute(
            select(Campaign).where(Campaign.account_id == account_id)
        )
        return list(result.scalars().all())

    async def get_current_spend(self, account_id: UUID) -> SpendData:
        campaigns = await self.get_campaigns(account_id)
        total = Decimal("0")

        for c in campaigns:
            raw = await self.redis.hget(f"{SIM_SPEND_PREFIX}{c.id}", "total_today")
            if raw:
                val = raw.decode() if isinstance(raw, bytes) else raw
                total += Decimal(val)

        sim_time_raw = await self.redis.hget(SIM_STATE_KEY, "sim_time")
        last_updated = datetime.utcnow()
        if sim_time_raw:
            val = sim_time_raw.decode() if isinstance(sim_time_raw, bytes) else sim_time_raw
            try:
                last_updated = datetime.fromisoformat(val)
            except (ValueError, TypeError):
                pass

        return SpendData(
            account_id=account_id,
            total_spend_today=total,
            total_spend_month=total,
            last_updated=last_updated,
        )

    async def get_campaign_spend(self, campaign_id: UUID) -> CampaignSpendData:
        data = await self.redis.hgetall(f"{SIM_SPEND_PREFIX}{campaign_id}")
        decoded = {
            (k.decode() if isinstance(k, bytes) else k): (v.decode() if isinstance(v, bytes) else v)
            for k, v in data.items()
        }

        spend_today = Decimal(decoded.get("total_today", "0"))

        sim_time_raw = await self.redis.hget(SIM_STATE_KEY, "sim_time")
        last_updated = datetime.utcnow()
        hours_elapsed = 1
        if sim_time_raw:
            val = sim_time_raw.decode() if isinstance(sim_time_raw, bytes) else sim_time_raw
            try:
                st = datetime.fromisoformat(val)
                last_updated = st
                hours_elapsed = max(st.hour + st.minute / 60, 1)
            except (ValueError, TypeError):
                pass

        rate = spend_today / Decimal(str(hours_elapsed))

        return CampaignSpendData(
            campaign_id=campaign_id,
            spend_today=spend_today,
            spend_rate_per_hour=rate,
            last_updated=last_updated,
        )

    async def pause_campaign(self, campaign_id: UUID) -> ActionResult:
        result = await self.db.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            return ActionResult(success=False, message="Campaign not found", campaign_id=campaign_id)

        campaign.status = CampaignStatus.PAUSED
        await self.db.commit()
        return ActionResult(success=True, message="Campaign paused", campaign_id=campaign_id)

    async def resume_campaign(self, campaign_id: UUID) -> ActionResult:
        result = await self.db.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            return ActionResult(success=False, message="Campaign not found", campaign_id=campaign_id)

        campaign.status = CampaignStatus.ACTIVE
        await self.db.commit()
        return ActionResult(success=True, message="Campaign resumed", campaign_id=campaign_id)

    async def get_insights(self, account_id: UUID, date_range: DateRange) -> InsightsData:
        from sqlalchemy import func as sa_func

        stmt = (
            select(
                sa_func.date(SpendSnapshot.timestamp).label("day"),
                sa_func.sum(SpendSnapshot.spend).label("total"),
            )
            .join(Campaign, Campaign.id == SpendSnapshot.campaign_id)
            .where(
                Campaign.account_id == account_id,
                SpendSnapshot.timestamp >= date_range.start_date,
                SpendSnapshot.timestamp <= date_range.end_date,
            )
            .group_by(sa_func.date(SpendSnapshot.timestamp))
            .order_by(sa_func.date(SpendSnapshot.timestamp))
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        return InsightsData(
            account_id=account_id,
            daily_spend=[DailySpend(date=row.day, spend=row.total) for row in rows],
        )


class SyncSimulationProvider(SyncAdDataProvider):
    """Sync provider for Celery tasks."""

    def __init__(self, db, redis):
        self.db = db
        self.redis = redis

    def get_current_spend(self, account_id: UUID) -> SpendData:
        from sqlalchemy import select as sync_select
        campaigns = self.db.execute(
            sync_select(Campaign).where(Campaign.account_id == account_id)
        ).scalars().all()

        total = Decimal("0")
        for c in campaigns:
            raw = self.redis.hget(f"{SIM_SPEND_PREFIX}{c.id}", "total_today")
            if raw:
                val = raw.decode() if isinstance(raw, bytes) else raw
                total += Decimal(val)

        return SpendData(
            account_id=account_id,
            total_spend_today=total,
            total_spend_month=total,
            last_updated=datetime.utcnow(),
        )

    def get_campaign_spend(self, campaign_id: UUID) -> CampaignSpendData:
        data = self.redis.hgetall(f"{SIM_SPEND_PREFIX}{campaign_id}")
        decoded = {
            (k.decode() if isinstance(k, bytes) else k): (v.decode() if isinstance(v, bytes) else v)
            for k, v in data.items()
        }
        spend = Decimal(decoded.get("total_today", "0"))
        return CampaignSpendData(
            campaign_id=campaign_id,
            spend_today=spend,
            spend_rate_per_hour=spend,
            last_updated=datetime.utcnow(),
        )

    def pause_campaign(self, campaign_id: UUID) -> ActionResult:
        from sqlalchemy import select as sync_select
        campaign = self.db.execute(
            sync_select(Campaign).where(Campaign.id == campaign_id)
        ).scalar_one_or_none()
        if not campaign:
            return ActionResult(success=False, message="Not found", campaign_id=campaign_id)
        campaign.status = CampaignStatus.PAUSED
        self.db.commit()
        return ActionResult(success=True, message="Paused", campaign_id=campaign_id)

    def resume_campaign(self, campaign_id: UUID) -> ActionResult:
        from sqlalchemy import select as sync_select
        campaign = self.db.execute(
            sync_select(Campaign).where(Campaign.id == campaign_id)
        ).scalar_one_or_none()
        if not campaign:
            return ActionResult(success=False, message="Not found", campaign_id=campaign_id)
        campaign.status = CampaignStatus.ACTIVE
        self.db.commit()
        return ActionResult(success=True, message="Resumed", campaign_id=campaign_id)

    def get_insights(self, account_id: UUID, date_range: DateRange) -> InsightsData:
        return InsightsData(account_id=account_id, daily_spend=[])
