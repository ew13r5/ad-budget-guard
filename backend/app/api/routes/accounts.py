"""Account management routes."""
from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.models.ad_account import AdAccount, user_accounts
from app.models.campaign import Campaign
from app.models.user import User
from app.schemas.account import AdAccountListResponse, AdAccountResponse
from app.schemas.campaign import CampaignListResponse, CampaignResponse

router = APIRouter()


@router.get("", response_model=AdAccountListResponse)
async def list_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List ad accounts for the authenticated user."""
    result = await db.execute(
        select(AdAccount)
        .join(user_accounts, user_accounts.c.account_id == AdAccount.id)
        .where(user_accounts.c.user_id == current_user.id)
    )
    accounts = result.scalars().all()
    return AdAccountListResponse(
        accounts=[AdAccountResponse.model_validate(a) for a in accounts],
        total=len(accounts),
    )


@router.get("/{account_id}", response_model=AdAccountResponse)
async def get_account(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get account details. Returns 403 if user has no access."""
    # Check user has access
    assoc = await db.execute(
        select(user_accounts).where(
            user_accounts.c.user_id == current_user.id,
            user_accounts.c.account_id == account_id,
        )
    )
    if assoc.first() is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access")

    result = await db.execute(select(AdAccount).where(AdAccount.id == account_id))
    account = result.scalar_one_or_none()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    return AdAccountResponse.model_validate(account)


@router.get("/{account_id}/campaigns", response_model=CampaignListResponse)
async def list_campaigns(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List campaigns for an account."""
    # Check access
    assoc = await db.execute(
        select(user_accounts).where(
            user_accounts.c.user_id == current_user.id,
            user_accounts.c.account_id == account_id,
        )
    )
    if assoc.first() is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access")

    result = await db.execute(
        select(Campaign).where(Campaign.account_id == account_id)
    )
    campaigns = result.scalars().all()
    return CampaignListResponse(
        campaigns=[CampaignResponse.model_validate(c) for c in campaigns],
        total=len(campaigns),
    )
