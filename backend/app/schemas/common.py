from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List
from uuid import UUID

from pydantic import BaseModel


class DateRange(BaseModel):
    start_date: date
    end_date: date


class DailySpend(BaseModel):
    date: date
    spend: Decimal


class SpendData(BaseModel):
    account_id: UUID
    total_spend_today: Decimal
    total_spend_month: Decimal
    last_updated: datetime


class CampaignSpendData(BaseModel):
    campaign_id: UUID
    spend_today: Decimal
    spend_rate_per_hour: Decimal
    last_updated: datetime


class ActionResult(BaseModel):
    success: bool
    message: str
    campaign_id: UUID


class InsightsData(BaseModel):
    account_id: UUID
    daily_spend: List[DailySpend]
