"""Celery periodic task for simulation tick loop."""
from __future__ import annotations

import structlog

from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)

_engine_instance = None


def _get_engine():
    """Lazy-initialize the SimulatorEngine singleton."""
    global _engine_instance
    if _engine_instance is None:
        import os

        import redis as sync_redis

        from app.database import get_sync_session_factory
        from app.simulator.engine import SimulatorEngine
        from app.simulator.state import SimulationStateManager

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = sync_redis.from_url(redis_url)

        session_factory = get_sync_session_factory()
        session = session_factory()

        state_manager = SimulationStateManager(redis=redis_client, db_session=session)
        _engine_instance = SimulatorEngine(
            state_manager=state_manager,
            redis=redis_client,
            db_session=session,
        )

    return _engine_instance


@celery_app.task(name="app.tasks.simulation.simulator_tick")
def simulator_tick():
    """Periodic tick task. Distributed lock inside engine.tick() prevents concurrent execution."""
    try:
        _get_engine().tick()
    except Exception:
        logger.exception("simulator_tick_error")
