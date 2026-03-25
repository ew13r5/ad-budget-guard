from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SimulationState(Base):
    __tablename__ = "simulation_states"

    account_id: Mapped[UUID] = mapped_column(ForeignKey("ad_accounts.id", ondelete="CASCADE"))
    state_data: Mapped[Any] = mapped_column(JSON, default=dict)
    is_running: Mapped[bool] = mapped_column(Boolean, default=False)
    last_tick: Mapped[Optional[datetime]] = mapped_column(nullable=True)
