from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.budget_rule import RuleType, RuleAction


class RuleCreateRequest(BaseModel):
    rule_type: RuleType
    threshold: Decimal
    action: RuleAction = RuleAction.soft_pause
    campaign_id: Optional[UUID] = None


class RuleUpdateRequest(BaseModel):
    threshold: Optional[Decimal] = None
    action: Optional[RuleAction] = None
    is_active: Optional[bool] = None


class RuleResponse(BaseModel):
    id: UUID
    account_id: UUID
    campaign_id: Optional[UUID] = None
    rule_type: RuleType
    threshold: Decimal
    action: RuleAction
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RuleListResponse(BaseModel):
    rules: List[RuleResponse]
    total: int


class MonitoringSpendResponse(BaseModel):
    account_id: UUID
    total_spend_today: Decimal
    total_spend_month: Decimal
    last_updated: datetime


class MonitoringStatusResponse(BaseModel):
    account_id: UUID
    active_rules: int
    triggered_rules: int
    paused_campaigns: int
    forecast_eod: Optional[Decimal] = None
    warning_level: Optional[str] = None
    last_check: Optional[datetime] = None
