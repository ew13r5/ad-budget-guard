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
