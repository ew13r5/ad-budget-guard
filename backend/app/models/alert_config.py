"""AlertConfig — per-account notification preferences."""
from __future__ import annotations

import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AlertSeverity(str, enum.Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class AlertConfig(Base):
    __tablename__ = "alert_configs"
    __table_args__ = (
        Index("ix_alert_configs_account_channel", "account_id", "channel"),
    )

    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("ad_accounts.id", ondelete="CASCADE"),
    )
    channel: Mapped[str] = mapped_column(String(50))
    destination: Mapped[str] = mapped_column(String(500))
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    severity_filter: Mapped[str] = mapped_column(
        String(20), default="info",
    )
