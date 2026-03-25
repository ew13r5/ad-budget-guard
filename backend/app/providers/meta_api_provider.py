"""MetaApiProvider — skeleton. Full implementation in section 05."""
from __future__ import annotations

from uuid import UUID

from app.providers.base import AdDataProvider
from app.schemas.common import (
    ActionResult, CampaignSpendData, DateRange, InsightsData, SpendData,
)


class MetaApiProvider(AdDataProvider):
    def __init__(self, access_token: str):
        self._access_token = access_token

    async def get_accounts(self) -> list:
        raise NotImplementedError

    async def get_campaigns(self, account_id: UUID) -> list:
        raise NotImplementedError

    async def get_current_spend(self, account_id: UUID) -> SpendData:
        raise NotImplementedError

    async def get_campaign_spend(self, campaign_id: UUID) -> CampaignSpendData:
        raise NotImplementedError

    async def pause_campaign(self, campaign_id: UUID) -> ActionResult:
        raise NotImplementedError

    async def resume_campaign(self, campaign_id: UUID) -> ActionResult:
        raise NotImplementedError

    async def get_insights(self, account_id: UUID, date_range: DateRange) -> InsightsData:
        raise NotImplementedError
