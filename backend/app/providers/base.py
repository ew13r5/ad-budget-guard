from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from app.schemas.common import (
    ActionResult, CampaignSpendData, DateRange, InsightsData, SpendData,
)


class AdDataProvider(ABC):
    """Async interface for ad data access. Used by FastAPI routes."""

    @abstractmethod
    async def get_accounts(self) -> list:
        ...

    @abstractmethod
    async def get_campaigns(self, account_id: UUID) -> list:
        ...

    @abstractmethod
    async def get_current_spend(self, account_id: UUID) -> SpendData:
        ...

    @abstractmethod
    async def get_campaign_spend(self, campaign_id: UUID) -> CampaignSpendData:
        ...

    @abstractmethod
    async def pause_campaign(self, campaign_id: UUID) -> ActionResult:
        ...

    @abstractmethod
    async def resume_campaign(self, campaign_id: UUID) -> ActionResult:
        ...

    @abstractmethod
    async def get_insights(self, account_id: UUID, date_range: DateRange) -> InsightsData:
        ...


class SyncAdDataProvider(ABC):
    """Sync interface for ad data access. Used by Celery tasks."""

    @abstractmethod
    def get_current_spend(self, account_id: UUID) -> SpendData:
        ...

    @abstractmethod
    def get_campaign_spend(self, campaign_id: UUID) -> CampaignSpendData:
        ...

    @abstractmethod
    def pause_campaign(self, campaign_id: UUID) -> ActionResult:
        ...

    @abstractmethod
    def resume_campaign(self, campaign_id: UUID) -> ActionResult:
        ...

    @abstractmethod
    def get_insights(self, account_id: UUID, date_range: DateRange) -> InsightsData:
        ...
