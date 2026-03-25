"""Tests for Celery app configuration and Beat schedule."""
from celery.schedules import crontab


class TestCeleryApp:
    def test_celery_app_instance(self):
        from app.tasks.celery_app import celery_app
        assert celery_app.main == "ad_budget_guard"

    def test_broker_configured(self):
        from app.tasks.celery_app import celery_app
        assert celery_app.conf.broker_url is not None

    def test_json_serializer(self):
        from app.tasks.celery_app import celery_app
        assert celery_app.conf.task_serializer == "json"


class TestBeatSchedule:
    def test_has_all_scheduled_tasks(self):
        from app.tasks.celery_app import celery_app
        schedule = celery_app.conf.beat_schedule
        expected_keys = {
            "monitoring-check",
            "token-health-check",
            "simulator-tick",
            "daily-report",
        }
        assert expected_keys == set(schedule.keys())

    def test_token_health_daily_at_3am(self):
        from app.tasks.celery_app import celery_app
        entry = celery_app.conf.beat_schedule["token-health-check"]
        assert isinstance(entry["schedule"], crontab)
        assert str(entry["schedule"]._orig_hour) == "3"
        assert str(entry["schedule"]._orig_minute) == "0"

    def test_monitoring_every_5_minutes(self):
        from app.tasks.celery_app import celery_app
        entry = celery_app.conf.beat_schedule["monitoring-check"]
        assert entry["schedule"] == 300.0

    def test_each_entry_has_task_and_schedule(self):
        from app.tasks.celery_app import celery_app
        for name, entry in celery_app.conf.beat_schedule.items():
            assert "task" in entry, f"{name} missing 'task'"
            assert "schedule" in entry, f"{name} missing 'schedule'"


class TestTaskRegistration:
    def test_token_health_task_registered(self):
        from app.tasks.celery_app import celery_app
        assert "app.tasks.token_health.check_token_health" in celery_app.tasks
