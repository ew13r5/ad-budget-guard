from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PauseLog(Base):
    __tablename__ = "pause_log"
    __table_args__ = (
        Index("ix_pause_log_campaign_paused_at", "campaign_id", "paused_at"),
    )

    campaign_id: Mapped[UUID] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    rule_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("budget_rules.id", ondelete="SET NULL"), nullable=True
    )
    paused_at: Mapped[datetime] = mapped_column(server_default=func.now())
    resumed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
