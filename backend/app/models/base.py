from __future__ import annotations

import enum
from datetime import datetime
from typing import Any
import uuid as _uuid
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from uuid_utils import uuid7


def _uuid7_stdlib() -> _uuid.UUID:
    return _uuid.UUID(str(uuid7()))


class Base(DeclarativeBase):
    __abstract__ = True

    id: Mapped[UUID] = mapped_column(primary_key=True, default=_uuid7_stdlib)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
