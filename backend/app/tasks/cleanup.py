"""Data retention Celery task — delete old spend snapshots."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.cleanup.cleanup_old_snapshots")
def cleanup_old_snapshots(retention_days: int = 90):
    """Delete spend snapshots older than retention_days."""
    from app.database import get_sync_session_factory
    from app.models.spend_snapshot import SpendSnapshot

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

    session_factory = get_sync_session_factory()
    session = session_factory()
    total_deleted = 0

    try:
        while True:
            rows = (
                session.query(SpendSnapshot)
                .filter(SpendSnapshot.timestamp < cutoff)
                .limit(1000)
                .all()
            )
            if not rows:
                break

            for row in rows:
                session.delete(row)
            session.commit()
            total_deleted += len(rows)

        logger.info("cleanup_complete", extra={
            "deleted": total_deleted,
            "cutoff": cutoff.isoformat(),
        })
    except Exception:
        logger.exception("cleanup_error")
        session.rollback()
    finally:
        session.close()

    return {"deleted": total_deleted}
