from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AlertType(str, enum.Enum):
    budget_warning = "budget_warning"
    pause = "pause"
    anomaly = "anomaly"
    error = "error"


class AlertChannel(str, enum.Enum):
    telegram = "telegram"
    email = "email"
    in_app = "in_app"


class AlertLog(Base):
    __tablename__ = "alerts_log"
    __table_args__ = (
        Index("ix_alerts_log_account_sent_at", "account_id", "sent_at"),
    )

    account_id: Mapped[UUID] = mapped_column(ForeignKey("ad_accounts.id", ondelete="CASCADE"))
    alert_type: Mapped[AlertType] = mapped_column(Enum(AlertType))
    channel: Mapped[AlertChannel] = mapped_column(Enum(AlertChannel))
    message: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(server_default=func.now())
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
