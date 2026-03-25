from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, JSON, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.budget_rule import BudgetRule


class EvaluationResult(str, enum.Enum):
    ok = "ok"
    warning = "warning"
    triggered = "triggered"


class RuleEvaluation(Base):
    __tablename__ = "rule_evaluations"
    __table_args__ = (
        Index("ix_rule_evaluations_rule_timestamp", "rule_id", "timestamp"),
    )

    rule_id: Mapped[UUID] = mapped_column(ForeignKey("budget_rules.id", ondelete="CASCADE"))
    result: Mapped[EvaluationResult] = mapped_column(Enum(EvaluationResult))
    current_value: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    threshold_value: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    timestamp: Mapped[datetime] = mapped_column(server_default=func.now())
    details: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    rule: Mapped["BudgetRule"] = relationship(back_populates="evaluations")
