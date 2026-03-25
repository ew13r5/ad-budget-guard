from __future__ import annotations

import enum
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.ad_account import AdAccount
    from app.models.spend_snapshot import SpendSnapshot


class CampaignStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"


class Campaign(Base):
    __tablename__ = "campaigns"

    account_id: Mapped[UUID] = mapped_column(ForeignKey("ad_accounts.id", ondelete="CASCADE"))
    meta_campaign_id: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus), default=CampaignStatus.ACTIVE
    )
    daily_budget: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    lifetime_budget: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)

    account: Mapped["AdAccount"] = relationship(back_populates="campaigns")
    spend_snapshots: Mapped[List["SpendSnapshot"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )
