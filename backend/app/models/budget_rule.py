from __future__ import annotations

import enum
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.ad_account import AdAccount
    from app.models.campaign import Campaign
    from app.models.rule_evaluation import RuleEvaluation


class RuleType(str, enum.Enum):
    daily_limit = "daily_limit"
    monthly_limit = "monthly_limit"
    hourly_rate = "hourly_rate"
    anomaly = "anomaly"


class RuleAction(str, enum.Enum):
    soft_pause = "soft_pause"
    hard_pause = "hard_pause"


class BudgetRule(Base):
    __tablename__ = "budget_rules"

    account_id: Mapped[UUID] = mapped_column(ForeignKey("ad_accounts.id", ondelete="CASCADE"))
    campaign_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=True
    )
    rule_type: Mapped[RuleType] = mapped_column(Enum(RuleType))
    threshold: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    action: Mapped[RuleAction] = mapped_column(Enum(RuleAction), default=RuleAction.soft_pause)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    account: Mapped["AdAccount"] = relationship(back_populates="budget_rules")
    campaign: Mapped[Optional["Campaign"]] = relationship()
    evaluations: Mapped[List["RuleEvaluation"]] = relationship(back_populates="rule")
