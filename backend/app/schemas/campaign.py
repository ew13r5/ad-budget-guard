from __future__ import annotations

from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.campaign import CampaignStatus
from app.schemas.common import ActionResult


class CampaignResponse(BaseModel):
    id: UUID
    meta_campaign_id: str
    name: str
    status: CampaignStatus
    daily_budget: Optional[Decimal] = None
    lifetime_budget: Optional[Decimal] = None

    model_config = {"from_attributes": True}


class CampaignListResponse(BaseModel):
    campaigns: List[CampaignResponse]
    total: int


class PauseResumeResponse(ActionResult):
    pass
