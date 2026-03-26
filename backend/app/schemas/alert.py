"""Alert schemas — Pydantic v2 models for alert config & log endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


# ---------- AlertConfig ----------
class AlertConfigRequest(BaseModel):
    channel: str
    destination: str
    is_enabled: bool = True
    severity_filter: str = "info"


class AlertConfigResponse(BaseModel):
    id: UUID
    account_id: UUID
    channel: str
    destination: str
    is_enabled: bool
    severity_filter: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- AlertLog ----------
class AlertLogResponse(BaseModel):
    id: UUID
    account_id: UUID
    alert_type: str
    channel: str
    message: str
    severity: str
    sent_at: datetime
    acknowledged: bool

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    alerts: List[AlertLogResponse]
    total: int


class AlertConfigListResponse(BaseModel):
    configs: List[AlertConfigResponse]
    total: int


class SendTestAlertRequest(BaseModel):
    account_id: UUID
    channel: str
    destination: str
    message: str = "This is a test alert from Ad Budget Guard"
