"""Alert API — list, acknowledge, configure, test alerts."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.ad_account import user_accounts
from app.models.alert_config import AlertConfig
from app.models.alert_log import AlertLog
from app.models.user import User
from app.schemas.alert import (
    AlertConfigListResponse,
    AlertConfigRequest,
    AlertConfigResponse,
    AlertListResponse,
    AlertLogResponse,
    SendTestAlertRequest,
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


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    account_id: Optional[UUID] = Query(None),
    alert_type: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List alerts with pagination and filters."""
    if account_id:
        await _check_account_access(account_id, current_user, db)

    query = select(AlertLog)
    count_query = select(func.count(AlertLog.id))

    if account_id:
        query = query.where(AlertLog.account_id == account_id)
        count_query = count_query.where(AlertLog.account_id == account_id)
    if alert_type:
        query = query.where(AlertLog.alert_type == alert_type)
        count_query = count_query.where(AlertLog.alert_type == alert_type)
    if date_from:
        query = query.where(AlertLog.sent_at >= date_from)
        count_query = count_query.where(AlertLog.sent_at >= date_from)
    if date_to:
        query = query.where(AlertLog.sent_at <= date_to)
        count_query = count_query.where(AlertLog.sent_at <= date_to)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(AlertLog.sent_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    alerts = result.scalars().all()

    return AlertListResponse(
        alerts=[AlertLogResponse.model_validate(a) for a in alerts],
        total=total,
    )


@router.patch("/{alert_id}", response_model=AlertLogResponse)
async def acknowledge_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Acknowledge an alert."""
    result = await db.execute(select(AlertLog).where(AlertLog.id == alert_id))
    alert = result.scalar_one_or_none()
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found",
        )

    await _check_account_access(alert.account_id, current_user, db)

    alert.acknowledged = True
    await db.commit()
    await db.refresh(alert)
    return AlertLogResponse.model_validate(alert)


@router.get("/config/{account_id}", response_model=AlertConfigListResponse)
async def list_alert_configs(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List alert configs for an account."""
    await _check_account_access(account_id, current_user, db)

    result = await db.execute(
        select(AlertConfig).where(AlertConfig.account_id == account_id)
    )
    configs = result.scalars().all()
    return AlertConfigListResponse(
        configs=[AlertConfigResponse.model_validate(c) for c in configs],
        total=len(configs),
    )


@router.put("/config/{account_id}", response_model=AlertConfigResponse)
async def upsert_alert_config(
    account_id: UUID,
    body: AlertConfigRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update alert config for an account."""
    await _check_account_access(account_id, current_user, db)

    # Check if config exists for this account + channel
    result = await db.execute(
        select(AlertConfig).where(
            AlertConfig.account_id == account_id,
            AlertConfig.channel == body.channel,
        )
    )
    config = result.scalar_one_or_none()

    if config:
        config.destination = body.destination
        config.is_enabled = body.is_enabled
        config.severity_filter = body.severity_filter
    else:
        config = AlertConfig(
            account_id=account_id,
            channel=body.channel,
            destination=body.destination,
            is_enabled=body.is_enabled,
            severity_filter=body.severity_filter,
        )
        db.add(config)

    await db.commit()
    await db.refresh(config)
    return AlertConfigResponse.model_validate(config)


@router.post("/test", status_code=status.HTTP_200_OK)
async def send_test_alert(
    body: SendTestAlertRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a test alert to verify channel configuration."""
    await _check_account_access(body.account_id, current_user, db)

    if body.channel == "telegram":
        from app.alerts.telegram_sender import TelegramSender

        sender = TelegramSender()
        success = sender.send_alert(
            chat_id=body.destination,
            account_name="Test Account",
            message=body.message,
            severity="info",
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to send test alert via Telegram",
            )
        return {"status": "sent", "channel": body.channel}
    elif body.channel == "email":
        from app.alerts.email_sender import EmailSender
        from app.config import get_settings

        sender = EmailSender(get_settings())
        success = sender.send_test(body.destination)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to send test email. Check SMTP configuration.",
            )
        return {"status": "sent", "channel": body.channel}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown channel: {body.channel}",
        )
