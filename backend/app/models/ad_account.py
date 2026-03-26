from __future__ import annotations

import enum
from typing import TYPE_CHECKING, List
from uuid import UUID

from sqlalchemy import Column, Enum, ForeignKey, String, Boolean, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.budget_rule import BudgetRule
    from app.models.user import User


class AccountMode(str, enum.Enum):
    sandbox = "sandbox"
    simulation = "simulation"
    production = "production"


class UserRole(str, enum.Enum):
    owner = "owner"
    manager = "manager"
    viewer = "viewer"


user_accounts = Table(
    "user_accounts",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("account_id", ForeignKey("ad_accounts.id", ondelete="CASCADE"), primary_key=True),
    Column("role", Enum(UserRole), nullable=False, default=UserRole.viewer),
)


class AdAccount(Base):
    __tablename__ = "ad_accounts"

    meta_account_id: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    mode: Mapped[AccountMode] = mapped_column(
        Enum(AccountMode), default=AccountMode.simulation
    )
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_resume_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    users: Mapped[List["User"]] = relationship(
        secondary=user_accounts, back_populates="accounts"
    )
    campaigns: Mapped[List["Campaign"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    budget_rules: Mapped[List["BudgetRule"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
