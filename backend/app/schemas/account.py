from __future__ import annotations

from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel

from app.models.ad_account import AccountMode


class AdAccountResponse(BaseModel):
    id: UUID
    meta_account_id: str
    name: str
    mode: AccountMode
    currency: str
    timezone: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AdAccountListResponse(BaseModel):
    accounts: List[AdAccountResponse]
    total: int


class ModeUpdateRequest(BaseModel):
    account_id: UUID
    mode: AccountMode


class ModeResponse(BaseModel):
    account_id: UUID
    mode: AccountMode
