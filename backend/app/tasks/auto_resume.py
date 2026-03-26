"""Celery daily task: auto-resume campaigns paused by soft rules at midnight."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import redis as sync_redis
import structlog

from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="app.tasks.auto_resume.auto_resume_paused")
def auto_resume_paused():
    """Resume campaigns that were soft-paused yesterday, if account has auto_resume_enabled."""
    from app.database import get_sync_session_factory
    from app.models.ad_account import AdAccount
    from app.models.campaign import Campaign, CampaignStatus
    from app.models.pause_log import PauseLog
    from app.providers.simulation_provider import SyncSimulationProvider

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = sync_redis.from_url(redis_url)

    session_factory = get_sync_session_factory()
    session = session_factory()

    try:
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)

        # Find accounts with auto_resume_enabled
        accounts = (
            session.query(AdAccount)
            .filter(
                AdAccount.is_active.is_(True),
                AdAccount.auto_resume_enabled.is_(True),
            )
            .all()
        )

        total_resumed = 0

        for account in accounts:
            # Find paused campaigns with pause_log entries from yesterday that are still paused
            paused_campaigns = (
                session.query(Campaign)
                .join(PauseLog, PauseLog.campaign_id == Campaign.id)
                .filter(
                    Campaign.account_id == account.id,
                    Campaign.status == CampaignStatus.PAUSED,
                    PauseLog.paused_at >= yesterday,
                    PauseLog.resumed_at.is_(None),
                    PauseLog.reason.like("Soft pause%"),
                )
                .distinct()
                .all()
            )

            provider = SyncSimulationProvider(db=session, redis=redis_client)

            for campaign in paused_campaigns:
                try:
                    provider.resume_campaign(campaign.id)

                    # Update pause_log with resumed_at
                    pause_entries = (
                        session.query(PauseLog)
                        .filter(
                            PauseLog.campaign_id == campaign.id,
                            PauseLog.resumed_at.is_(None),
                        )
                        .all()
                    )
                    for entry in pause_entries:
                        entry.resumed_at = now

                    total_resumed += 1
                    logger.info(
                        "campaign_auto_resumed",
                        campaign_id=str(campaign.id),
                        account_id=str(account.id),
                    )
                except Exception:
                    logger.exception(
                        "auto_resume_error",
                        campaign_id=str(campaign.id),
                    )

        session.commit()

        logger.info("auto_resume_complete", total_resumed=total_resumed)
        return {"status": "ok", "total_resumed": total_resumed}

    except Exception:
        logger.exception("auto_resume_task_error")
        session.rollback()
        return {"status": "error"}
    finally:
        session.close()
