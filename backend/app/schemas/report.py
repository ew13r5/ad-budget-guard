"""Report schemas — Pydantic v2 models for report endpoints."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class CampaignBreakdown(BaseModel):
    campaign_id: UUID
    campaign_name: str
    spend: Decimal
    daily_budget: Optional[Decimal] = None
    utilization_pct: Optional[Decimal] = None


class DailySpend(BaseModel):
    date: date
    spend: Decimal


class Incident(BaseModel):
    timestamp: datetime
    alert_type: str
    severity: str
    message: str
    campaign_id: Optional[UUID] = None


class ReportData(BaseModel):
    account_id: UUID
    account_name: str
    report_type: str
    date_from: date
    date_to: date
    currency: str = "USD"
    total_spend: Decimal
    daily_budget_total: Optional[Decimal] = None
    campaigns: List[CampaignBreakdown] = []
    daily_spends: List[DailySpend] = []
    incidents: List[Incident] = []
    generated_at: datetime


class ReportResponse(BaseModel):
    id: UUID
    account_id: UUID
    report_type: str
    report_format: str
    date_from: datetime
    date_to: datetime
    file_path: Optional[str] = None
    sheets_url: Optional[str] = None
    generated_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    reports: List[ReportResponse]
    total: int


class ReportGenerateRequest(BaseModel):
    account_id: UUID
    report_type: str = "daily"
    report_format: str = "pdf"
    date_from: Optional[date] = None
    date_to: Optional[date] = None
