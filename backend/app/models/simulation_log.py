from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SimulationLog(Base):
    __tablename__ = "simulation_log"
    __table_args__ = (
        Index("ix_simulation_log_event_type_real_time", "event_type", "real_time"),
        Index("ix_simulation_log_campaign_id_real_time", "campaign_id", "real_time"),
    )

    event_type: Mapped[str] = mapped_column(String(50))
    campaign_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True
    )
    sim_time: Mapped[datetime] = mapped_column()
    real_time: Mapped[datetime] = mapped_column(server_default=func.now())
    details: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
