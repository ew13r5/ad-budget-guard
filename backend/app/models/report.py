"""Report model — stored report metadata."""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ReportType(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class ReportFormat(str, enum.Enum):
    pdf = "pdf"
    sheets = "sheets"


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (
        Index("ix_reports_account_type", "account_id", "report_type"),
    )

    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("ad_accounts.id", ondelete="CASCADE"),
    )
    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType))
    report_format: Mapped[ReportFormat] = mapped_column(Enum(ReportFormat))
    date_from: Mapped[datetime] = mapped_column()
    date_to: Mapped[datetime] = mapped_column()
    file_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    sheets_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column()
