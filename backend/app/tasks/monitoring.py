"""Celery periodic task for monitoring all accounts."""
from __future__ import annotations

import os

import redis as sync_redis
import structlog

from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)

MONITORING_LOCK_KEY = "monitoring:check_lock"
MONITORING_LOCK_TTL = int(os.getenv("MONITORING_LOCK_TTL", "280"))


@celery_app.task(name="app.tasks.monitoring.check_all_accounts")
def check_all_accounts():
    """Check all active accounts. Uses Redis distributed lock to prevent overlap."""
    from app.database import get_sync_session_factory
    from app.models.ad_account import AdAccount
    from app.providers.simulation_provider import SyncSimulationProvider
    from app.rules.actions import ActionExecutor
    from app.rules.engine import RuleEvaluator
    from app.rules.state import ConsecutiveStateManager
    from app.services.forecast_service import ForecastService
    from app.services.monitoring_service import MonitoringService

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = sync_redis.from_url(redis_url)

    # Distributed lock — skip if another worker is already running
    acquired = redis_client.set(
        MONITORING_LOCK_KEY, "1", nx=True, ex=MONITORING_LOCK_TTL,
    )
    if not acquired:
        logger.info("monitoring_check_skipped", reason="lock_held")
        return {"status": "skipped", "reason": "lock_held"}

    try:
        session_factory = get_sync_session_factory()
        session = session_factory()

        try:
            accounts = (
                session.query(AdAccount)
                .filter(AdAccount.is_active.is_(True))
                .all()
            )

            tracker = ConsecutiveStateManager(redis_client)
            evaluator = RuleEvaluator(tracker)
            executor = ActionExecutor()
            forecast = ForecastService()
            service = MonitoringService(evaluator, executor, forecast)

            results = []
            for account in accounts:
                try:
                    provider = SyncSimulationProvider(db=session, redis=redis_client)
                    result = service.check_account(
                        account.id, provider, session, redis_client,
                    )
                    results.append({
                        "account_id": str(account.id),
                        "evaluations": len(result.evaluations),
                        "actions": len(result.actions_taken),
                    })
                    logger.info(
                        "account_checked",
                        account_id=str(account.id),
                        evaluations=len(result.evaluations),
                        actions=len(result.actions_taken),
                    )
                except Exception:
                    logger.exception("account_check_error", account_id=str(account.id))

            return {"status": "ok", "accounts_checked": len(results), "results": results}
        finally:
            session.close()
    finally:
        redis_client.delete(MONITORING_LOCK_KEY)
