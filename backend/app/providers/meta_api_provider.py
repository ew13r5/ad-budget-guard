"""MetaApiProvider — concrete AdDataProvider using facebook-business SDK.

Architecture: sync-in-thread pattern
    This class wraps the synchronous facebook-business SDK for use in both
    async (FastAPI) and sync (Celery) contexts.

    Async callers (FastAPI routes, async services):
        Call public async methods (get_accounts, get_current_spend, etc.).
        These use asyncio.to_thread() internally to run sync SDK calls in a
        thread pool worker, keeping the event loop free.

    Sync callers (Celery tasks, CLI scripts):
        Call the _*_sync methods directly (e.g. _get_current_spend_sync).
        While prefixed with underscore, they are the intended entry points
        for sync contexts.

    time.sleep() in _call_with_retry is safe because it only runs inside
    asyncio.to_thread() worker threads when called from async paths.
"""
from __future__ import annotations

import asyncio
import random
import time
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog

from app.providers.base import AdDataProvider
from app.schemas.common import (
    ActionResult, CampaignSpendData, DailySpend, DateRange, InsightsData, SpendData,
)

logger = structlog.get_logger(__name__)

RATE_LIMIT_CODES = {613, 17}
TOKEN_EXPIRED_CODE = 190
PERMISSION_ERROR_CODE = 10


class TokenExpiredError(Exception):
    pass


class MetaApiPermissionError(Exception):
    pass


class MetaApiProvider(AdDataProvider):
    """Wraps facebook-business SDK with retry logic and dual sync/async support.

    Stateful: lazily initializes the Facebook SDK API object via _get_api().
    Thread safety: each instance should be used from a single context (one per
    request or task). The lazy _api init is not thread-safe by design.
    """

    def __init__(
        self,
        access_token: str,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        api_version: Optional[str] = None,
    ):
        self._access_token = access_token
        self._app_id = app_id
        self._app_secret = app_secret
        self._api_version = api_version
        self._api = None  # Lazy init

    def _get_api(self):
        if self._api is None:
            from facebook_business.api import FacebookAdsApi
            self._api = FacebookAdsApi.init(
                app_id=self._app_id or "",
                app_secret=self._app_secret or "",
                access_token=self._access_token,
                api_version=self._api_version or "v19.0",
            )
        return self._api

    def _call_with_retry(self, func, *args, max_retries: int = 5, **kwargs) -> Any:
        """Execute SDK call with exponential backoff on rate limit errors.

        Retry strategy:
            - Rate limit errors (codes 613, 17): retry up to max_retries with
              delay = 2^attempt + random(0,1) seconds.
            - Token expired (code 190): raises TokenExpiredError immediately.
            - Permission error (code 10): raises MetaApiPermissionError immediately.
            - Unknown errors: retry up to 3 times maximum.

        time.sleep() is intentional and safe here — this method only runs
        inside asyncio.to_thread() worker threads when called from async paths.
        """
        from facebook_business.exceptions import FacebookRequestError

        for attempt in range(max_retries + 1):
            try:
                result = func(*args, **kwargs)
                return result
            except FacebookRequestError as e:
                code = e.api_error_code()

                if code == TOKEN_EXPIRED_CODE:
                    raise TokenExpiredError(f"Token expired: {e}")

                if code == PERMISSION_ERROR_CODE:
                    logger.error("meta_api_permission_error", code=code, message=str(e))
                    raise MetaApiPermissionError(str(e))

                if code in RATE_LIMIT_CODES:
                    if attempt >= max_retries:
                        raise
                    delay = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning("meta_api_rate_limit", code=code, attempt=attempt, delay=delay)
                    time.sleep(delay)
                    continue

                # Unknown error
                if attempt >= min(max_retries, 3):
                    raise
                delay = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(delay)

        raise RuntimeError("Max retries exceeded")

    def _get_spend_sync(self, account_id: UUID, date_preset: str) -> Decimal:
        """Sync: fetch spend from Insights API."""
        from facebook_business.adobjects.adaccount import AdAccount

        api = self._get_api()
        account = AdAccount(f"act_{account_id}")
        result = self._call_with_retry(
            account.get_insights,
            params={"date_preset": date_preset},
            fields=["spend"],
        )
        rows = list(result)
        if not rows:
            return Decimal("0")
        return Decimal(rows[0].get("spend", "0"))

    async def get_accounts(self) -> list:
        """Fetch ad accounts. Runs sync SDK call in thread pool via asyncio.to_thread()."""
        return await asyncio.to_thread(self._get_accounts_sync)

    def _get_accounts_sync(self) -> list:
        from facebook_business.adobjects.adaccount import AdAccount
        api = self._get_api()
        # Would fetch via /me/adaccounts — simplified
        return []

    async def get_campaigns(self, account_id: UUID) -> list:
        """Fetch campaigns for account. Runs sync SDK call in thread pool."""
        return await asyncio.to_thread(self._get_campaigns_sync, account_id)

    def _get_campaigns_sync(self, account_id: UUID) -> list:
        from facebook_business.adobjects.adaccount import AdAccount
        account = AdAccount(f"act_{account_id}")
        result = self._call_with_retry(
            account.get_campaigns,
            fields=["id", "name", "status", "daily_budget"],
        )
        return list(result)

    async def get_current_spend(self, account_id: UUID) -> SpendData:
        """Fetch current spend data. Runs sync SDK call in thread pool."""
        return await asyncio.to_thread(self._get_current_spend_sync, account_id)

    def _get_current_spend_sync(self, account_id: UUID) -> SpendData:
        today = self._get_spend_sync(account_id, "today")
        month = self._get_spend_sync(account_id, "this_month")
        return SpendData(
            account_id=account_id,
            total_spend_today=today,
            total_spend_month=month,
            last_updated=datetime.utcnow(),
        )

    async def get_campaign_spend(self, campaign_id: UUID) -> CampaignSpendData:
        """Fetch campaign spend data. Runs sync SDK call in thread pool."""
        return await asyncio.to_thread(self._get_campaign_spend_sync, campaign_id)

    def _get_campaign_spend_sync(self, campaign_id: UUID) -> CampaignSpendData:
        from facebook_business.adobjects.campaign import Campaign

        campaign = Campaign(str(campaign_id))
        result = self._call_with_retry(
            campaign.get_insights,
            params={"date_preset": "today"},
            fields=["spend"],
        )
        rows = list(result)
        spend = Decimal(rows[0].get("spend", "0")) if rows else Decimal("0")
        hour = max(datetime.utcnow().hour, 1)
        rate = spend / hour

        return CampaignSpendData(
            campaign_id=campaign_id,
            spend_today=spend,
            spend_rate_per_hour=rate,
            last_updated=datetime.utcnow(),
        )

    async def pause_campaign(self, campaign_id: UUID) -> ActionResult:
        """Pause a campaign. Runs sync SDK call in thread pool."""
        return await asyncio.to_thread(self._pause_campaign_sync, campaign_id)

    def _pause_campaign_sync(self, campaign_id: UUID) -> ActionResult:
        from facebook_business.adobjects.campaign import Campaign
        from facebook_business.exceptions import FacebookRequestError

        campaign = Campaign(str(campaign_id))
        try:
            self._call_with_retry(
                campaign.api_update,
                params={Campaign.Field.status: Campaign.Status.paused},
            )
            return ActionResult(success=True, message="Campaign paused", campaign_id=campaign_id)
        except (FacebookRequestError, TokenExpiredError, MetaApiPermissionError) as e:
            return ActionResult(success=False, message=str(e), campaign_id=campaign_id)

    async def resume_campaign(self, campaign_id: UUID) -> ActionResult:
        """Resume a paused campaign. Runs sync SDK call in thread pool."""
        return await asyncio.to_thread(self._resume_campaign_sync, campaign_id)

    def _resume_campaign_sync(self, campaign_id: UUID) -> ActionResult:
        from facebook_business.adobjects.campaign import Campaign
        from facebook_business.exceptions import FacebookRequestError

        campaign = Campaign(str(campaign_id))
        try:
            self._call_with_retry(
                campaign.api_update,
                params={Campaign.Field.status: Campaign.Status.active},
            )
            return ActionResult(success=True, message="Campaign resumed", campaign_id=campaign_id)
        except (FacebookRequestError, TokenExpiredError, MetaApiPermissionError) as e:
            return ActionResult(success=False, message=str(e), campaign_id=campaign_id)

    async def get_insights(self, account_id: UUID, date_range: DateRange) -> InsightsData:
        """Fetch historical spend insights. Runs sync SDK call in thread pool."""
        return await asyncio.to_thread(self._get_insights_sync, account_id, date_range)

    def _get_insights_sync(self, account_id: UUID, date_range: DateRange) -> InsightsData:
        from facebook_business.adobjects.adaccount import AdAccount

        account = AdAccount(f"act_{account_id}")
        result = self._call_with_retry(
            account.get_insights,
            params={
                "time_range": {
                    "since": str(date_range.start_date),
                    "until": str(date_range.end_date),
                },
                "time_increment": 1,
            },
            fields=["spend", "date_start"],
        )
        daily = []
        for row in result:
            daily.append(DailySpend(
                date=date.fromisoformat(row["date_start"]),
                spend=Decimal(row.get("spend", "0")),
            ))
        return InsightsData(account_id=account_id, daily_spend=daily)
