"""Celery application configuration."""
from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab

# Read broker/backend from env (avoid importing Settings which needs all vars)
broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

celery_app = Celery("ad_budget_guard")

celery_app.conf.update(
    broker_url=broker_url,
    result_backend=result_backend,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

celery_app.autodiscover_tasks(["app.tasks"])

celery_app.conf.beat_schedule = {
    "monitoring-check": {
        "task": "app.tasks.monitoring.check_all_accounts",
        "schedule": 300.0,  # every 5 minutes (split 03)
    },
    "token-health-check": {
        "task": "app.tasks.token_health.check_token_health",
        "schedule": crontab(hour=3, minute=0),  # daily 03:00 UTC
    },
    "simulator-tick": {
        "task": "app.tasks.simulation.simulator_tick",
        "schedule": 2.0,  # every 2 seconds for smooth WebSocket updates
    },
    "daily-report": {
        "task": "app.tasks.reporting.generate_daily_report",
        "schedule": crontab(hour=8, minute=0),  # daily 08:00 UTC
    },
    "weekly-report": {
        "task": "app.tasks.reporting.generate_weekly_report",
        "schedule": crontab(hour=9, minute=0, day_of_week="monday"),  # Monday 09:00 UTC
    },
    "monthly-report": {
        "task": "app.tasks.reporting.generate_monthly_report",
        "schedule": crontab(hour=9, minute=0, day_of_month="1"),  # 1st of month 09:00 UTC
    },
    "cleanup-old-reports": {
        "task": "app.tasks.reporting.cleanup_old_reports",
        "schedule": crontab(hour=4, minute=0, day_of_week="sunday"),  # Sunday 04:00 UTC
    },
    "auto-resume-daily": {
        "task": "app.tasks.auto_resume.auto_resume_paused",
        "schedule": crontab(hour=0, minute=5),  # daily 00:05 UTC
    },
}


@celery_app.task(name="app.tasks.token_health.check_token_health")
def check_token_health():
    """Check all user tokens, refresh those expiring within 7 days."""
    pass
