from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.ad_account import AdAccount


class User(Base):
    __tablename__ = "users"

    facebook_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    needs_reauth: Mapped[bool] = mapped_column(Boolean, default=False)

    accounts: Mapped[List["AdAccount"]] = relationship(
        secondary="user_accounts", back_populates="users"
    )
