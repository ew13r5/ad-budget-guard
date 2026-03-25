from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.campaign import Campaign


class SpendSource(str, enum.Enum):
    api = "api"
    simulator = "simulator"


class SpendSnapshot(Base):
    __tablename__ = "spend_snapshots"
    __table_args__ = (
        Index("ix_spend_snapshots_campaign_timestamp", "campaign_id", "timestamp"),
    )

    campaign_id: Mapped[UUID] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    spend: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    source: Mapped[SpendSource] = mapped_column(Enum(SpendSource))
    timestamp: Mapped[datetime] = mapped_column(server_default=func.now())

    campaign: Mapped["Campaign"] = relationship(back_populates="spend_snapshots")
