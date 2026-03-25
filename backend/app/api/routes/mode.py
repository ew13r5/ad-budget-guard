"""Mode switching routes."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.ad_account import AdAccount, UserRole, user_accounts
from app.models.user import User
from app.schemas.account import ModeResponse, ModeUpdateRequest

router = APIRouter()


@router.get("", response_model=ModeResponse)
async def get_mode(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current operating mode for an account."""
    result = await db.execute(select(AdAccount).where(AdAccount.id == account_id))
    account = result.scalar_one_or_none()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return ModeResponse(account_id=account.id, mode=account.mode)


@router.put("", response_model=ModeResponse)
async def set_mode(
    body: ModeUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Switch operating mode. Requires owner role."""
    # Check owner role
    assoc = await db.execute(
        select(user_accounts.c.role).where(
            user_accounts.c.user_id == current_user.id,
            user_accounts.c.account_id == body.account_id,
        )
    )
    row = assoc.first()
    if row is None or row[0] != UserRole.owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner role required")

    result = await db.execute(select(AdAccount).where(AdAccount.id == body.account_id))
    account = result.scalar_one_or_none()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    account.mode = body.mode
    await db.commit()

    return ModeResponse(account_id=account.id, mode=account.mode)
