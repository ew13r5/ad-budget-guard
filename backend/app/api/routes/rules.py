"""Budget rules CRUD endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.ad_account import user_accounts
from app.models.budget_rule import BudgetRule
from app.models.user import User
from app.schemas.rule import (
    RuleCreateRequest,
    RuleListResponse,
    RuleResponse,
    RuleUpdateRequest,
)

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


@router.get("", response_model=RuleListResponse)
async def list_rules(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all budget rules for an account."""
    await _check_account_access(account_id, current_user, db)

    result = await db.execute(
        select(BudgetRule).where(BudgetRule.account_id == account_id)
    )
    rules = result.scalars().all()
    return RuleListResponse(
        rules=[RuleResponse.model_validate(r) for r in rules],
        total=len(rules),
    )


@router.post("", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    account_id: UUID,
    body: RuleCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new budget rule."""
    await _check_account_access(account_id, current_user, db)

    rule = BudgetRule(
        account_id=account_id,
        rule_type=body.rule_type,
        threshold=body.threshold,
        action=body.action,
        campaign_id=body.campaign_id,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return RuleResponse.model_validate(rule)


@router.patch("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: UUID,
    body: RuleUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing budget rule."""
    result = await db.execute(select(BudgetRule).where(BudgetRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if rule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found",
        )

    await _check_account_access(rule.account_id, current_user, db)

    if body.threshold is not None:
        rule.threshold = body.threshold
    if body.action is not None:
        rule.action = body.action
    if body.is_active is not None:
        rule.is_active = body.is_active

    await db.commit()
    await db.refresh(rule)
    return RuleResponse.model_validate(rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a budget rule."""
    result = await db.execute(select(BudgetRule).where(BudgetRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if rule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found",
        )

    await _check_account_access(rule.account_id, current_user, db)

    await db.delete(rule)
    await db.commit()
