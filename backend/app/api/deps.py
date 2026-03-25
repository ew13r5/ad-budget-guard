from __future__ import annotations

from typing import AsyncGenerator, Callable, Generator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.ad_account import AccountMode, AdAccount, UserRole, user_accounts
from app.models.user import User
from app.providers.base import AdDataProvider

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/facebook", auto_error=False)

# Role hierarchy: owner > manager > viewer
_ROLE_WEIGHT = {
    UserRole.owner: 3,
    UserRole.manager: 2,
    UserRole.viewer: 1,
}


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    from app.database import get_async_session_factory
    factory = get_async_session_factory()
    async with factory() as session:
        yield session


def get_sync_db() -> Generator[Session, None, None]:
    from app.database import get_sync_session_factory
    factory = get_sync_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode JWT, load user from DB. Raises 401 if invalid."""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    from app.services.token_service import verify_access_token
    user_id = verify_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


def require_role(min_role: UserRole) -> Callable:
    """Dependency factory: check user has at least min_role on the account."""

    async def _check_role(
        account_id: UUID,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        result = await db.execute(
            select(user_accounts.c.role).where(
                user_accounts.c.user_id == current_user.id,
                user_accounts.c.account_id == account_id,
            )
        )
        row = result.first()
        if row is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this account")

        role = row[0]
        if _ROLE_WEIGHT.get(role, 0) < _ROLE_WEIGHT[min_role]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")

        return current_user

    return _check_role


def get_provider_for_account(account: AdAccount, user: User) -> AdDataProvider:
    """Create provider based on account.mode, injecting user token for Meta API."""
    if account.mode == AccountMode.simulation:
        raise NotImplementedError("SimulationProvider not yet implemented (split 02)")

    from app.providers.meta_api_provider import MetaApiProvider
    return MetaApiProvider(access_token=user.access_token or "")
