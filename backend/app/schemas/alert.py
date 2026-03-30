"""Alert schemas — Pydantic v2 models for alert config & log endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ---------- AlertConfig ----------
class AlertConfigRequest(BaseModel):
    channel: str = Field(max_length=50)
    destination: str = Field(max_length=500)
    is_enabled: bool = True
    severity_filter: str = Field(default="info", max_length=20)

    @field_validator("destination")
    @classmethod
    def validate_destination(cls, v, info):
        channel = info.data.get("channel", "")
        if channel == "email" and "@" not in v:
            raise ValueError("Invalid email address")
        return v


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
    channel: str = Field(max_length=50)
    destination: str = Field(max_length=500)
    message: str = Field(default="This is a test alert from Ad Budget Guard", max_length=2000)
