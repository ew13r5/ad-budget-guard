"""Monitoring endpoints — spend and status."""
from __future__ import annotations

from uuid import UUID

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.config import get_settings
from app.models.ad_account import AdAccount, user_accounts
from app.models.budget_rule import BudgetRule
from app.models.campaign import Campaign, CampaignStatus
from app.models.rule_evaluation import EvaluationResult, RuleEvaluation
from app.models.user import User
from app.providers.simulation_provider import SimulationProvider
from app.schemas.rule import MonitoringSpendResponse, MonitoringStatusResponse

router = APIRouter()


async def _check_account_access(
    account_id: UUID, user: User, db: AsyncSession,
) -> None:
    result = await db.execute(
        select(user_accounts).where(
            user_accounts.c.user_id == user.id,
            user_accounts.c.account_id == account_id,
        )
    )
    if result.first() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No access",
        )


@router.get("/spend", response_model=MonitoringSpendResponse)
async def get_spend(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current spend for an account."""
    await _check_account_access(account_id, current_user, db)

    settings = get_settings()
    redis = aioredis.from_url(settings.redis_url)
    try:
        provider = SimulationProvider(db=db, redis=redis)
        spend = await provider.get_current_spend(account_id)
        return MonitoringSpendResponse(
            account_id=account_id,
            total_spend_today=spend.total_spend_today,
            total_spend_month=spend.total_spend_month,
            last_updated=spend.last_updated,
        )
    finally:
        await redis.close()


@router.get("/status", response_model=MonitoringStatusResponse)
async def get_status(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get monitoring status for an account."""
    await _check_account_access(account_id, current_user, db)

    # Count active rules
    active_rules_result = await db.execute(
        select(func.count(BudgetRule.id)).where(
            BudgetRule.account_id == account_id,
            BudgetRule.is_active.is_(True),
        )
    )
    active_rules = active_rules_result.scalar() or 0

    # Count triggered evaluations (most recent per rule)
    triggered_result = await db.execute(
        select(func.count())
        .select_from(RuleEvaluation)
        .join(BudgetRule, BudgetRule.id == RuleEvaluation.rule_id)
        .where(
            BudgetRule.account_id == account_id,
            RuleEvaluation.result == EvaluationResult.triggered,
        )
    )
    triggered_rules = triggered_result.scalar() or 0

    # Count paused campaigns
    paused_result = await db.execute(
        select(func.count(Campaign.id)).where(
            Campaign.account_id == account_id,
            Campaign.status == CampaignStatus.PAUSED,
        )
    )
    paused_campaigns = paused_result.scalar() or 0

    return MonitoringStatusResponse(
        account_id=account_id,
        active_rules=active_rules,
        triggered_rules=triggered_rules,
        paused_campaigns=paused_campaigns,
    )
