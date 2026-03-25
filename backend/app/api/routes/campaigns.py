"""Campaign routes: pause/resume."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_provider_for_account, require_role
from app.models.ad_account import AdAccount, UserRole, user_accounts
from app.models.campaign import Campaign, CampaignStatus
from app.models.user import User
from app.schemas.common import ActionResult

router = APIRouter()


@router.post("/{campaign_id}/pause", response_model=ActionResult)
async def pause_campaign(
    campaign_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pause a campaign. Requires manager role on parent account."""
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    # Check role
    assoc = await db.execute(
        select(user_accounts.c.role).where(
            user_accounts.c.user_id == current_user.id,
            user_accounts.c.account_id == campaign.account_id,
        )
    )
    row = assoc.first()
    if row is None or row[0] == UserRole.viewer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")

    result_obj = await db.execute(select(AdAccount).where(AdAccount.id == campaign.account_id))
    account = result_obj.scalar_one()

    provider = get_provider_for_account(account, current_user)
    action_result = await provider.pause_campaign(campaign_id)

    if action_result.success:
        campaign.status = CampaignStatus.PAUSED
        await db.commit()

    return action_result


@router.post("/{campaign_id}/resume", response_model=ActionResult)
async def resume_campaign(
    campaign_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resume a paused campaign. Requires manager role."""
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    assoc = await db.execute(
        select(user_accounts.c.role).where(
            user_accounts.c.user_id == current_user.id,
            user_accounts.c.account_id == campaign.account_id,
        )
    )
    row = assoc.first()
    if row is None or row[0] == UserRole.viewer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")

    result_obj = await db.execute(select(AdAccount).where(AdAccount.id == campaign.account_id))
    account = result_obj.scalar_one()

    provider = get_provider_for_account(account, current_user)
    action_result = await provider.resume_campaign(campaign_id)

    if action_result.success:
        campaign.status = CampaignStatus.ACTIVE
        await db.commit()

    return action_result
