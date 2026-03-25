from __future__ import annotations

import re
from typing import Optional

from sqlalchemy import create_engine, Engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker


def _to_async_url(url: str) -> str:
    return re.sub(r"^postgresql(\+\w+)?://", "postgresql+asyncpg://", url)


def _to_sync_url(url: str) -> str:
    return re.sub(r"^postgresql(\+\w+)?://", "postgresql+psycopg2://", url)


_async_engine: Optional[AsyncEngine] = None
_sync_engine: Optional[Engine] = None
_async_session_factory: Optional[async_sessionmaker] = None
_sync_session_factory: Optional[sessionmaker] = None


def get_async_engine() -> AsyncEngine:
    global _async_engine
    if _async_engine is None:
        from app.config import get_settings
        _async_engine = create_async_engine(
            _to_async_url(get_settings().database_url),
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
        )
    return _async_engine


def get_sync_engine() -> Engine:
    global _sync_engine
    if _sync_engine is None:
        from app.config import get_settings
        _sync_engine = create_engine(
            _to_sync_url(get_settings().database_url),
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600,
        )
    return _sync_engine


def get_async_session_factory() -> async_sessionmaker:
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            get_async_engine(), expire_on_commit=False
        )
    return _async_session_factory


def get_sync_session_factory() -> sessionmaker:
    global _sync_session_factory
    if _sync_session_factory is None:
        _sync_session_factory = sessionmaker(
            get_sync_engine(), expire_on_commit=False
        )
    return _sync_session_factory
