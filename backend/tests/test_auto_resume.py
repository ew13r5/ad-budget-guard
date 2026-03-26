"""Tests for the auto_resume_paused Celery task."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.models.campaign import CampaignStatus
from app.schemas.common import ActionResult


class TestAutoResumePaused:
    """Tests for app.tasks.auto_resume.auto_resume_paused."""

    @patch("app.providers.simulation_provider.SyncSimulationProvider.resume_campaign")
    @patch("app.database.get_sync_session_factory")
    @patch("redis.from_url")
    def test_resumes_soft_paused_campaigns(
        self, mock_from_url, mock_factory, mock_resume,
    ):
        """Campaigns soft-paused yesterday should be resumed."""
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        account = SimpleNamespace(
            id=uuid4(), is_active=True, auto_resume_enabled=True,
        )
        campaign = SimpleNamespace(
            id=uuid4(), account_id=account.id, status=CampaignStatus.PAUSED,
        )
        pause_entry = SimpleNamespace(
            campaign_id=campaign.id, resumed_at=None,
        )

        mock_session = MagicMock()
        mock_factory.return_value = MagicMock(return_value=mock_session)

        mock_session.query.return_value.filter.return_value.all.return_value = [account]
        mock_session.query.return_value.join.return_value.filter.return_value.distinct.return_value.all.return_value = [campaign]

        mock_resume.return_value = ActionResult(
            success=True, message="Resumed", campaign_id=campaign.id,
        )

        from app.tasks.auto_resume import auto_resume_paused

        result = auto_resume_paused()

        assert result["status"] == "ok"
        mock_session.commit.assert_called_once()

    @patch("app.database.get_sync_session_factory")
    @patch("redis.from_url")
    def test_skips_accounts_without_auto_resume(self, mock_from_url, mock_factory):
        """Accounts with auto_resume_enabled=False should be skipped."""
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        mock_session = MagicMock()
        mock_factory.return_value = MagicMock(return_value=mock_session)

        # No accounts with auto_resume_enabled
        mock_session.query.return_value.filter.return_value.all.return_value = []

        from app.tasks.auto_resume import auto_resume_paused

        result = auto_resume_paused()

        assert result["status"] == "ok"
        assert result["total_resumed"] == 0

    @patch("app.providers.simulation_provider.SyncSimulationProvider.resume_campaign")
    @patch("app.database.get_sync_session_factory")
    @patch("redis.from_url")
    def test_handles_resume_error_gracefully(
        self, mock_from_url, mock_factory, mock_resume,
    ):
        """If resuming a campaign fails, task continues with others."""
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        account = SimpleNamespace(
            id=uuid4(), is_active=True, auto_resume_enabled=True,
        )
        campaign = SimpleNamespace(
            id=uuid4(), account_id=account.id, status=CampaignStatus.PAUSED,
        )

        mock_session = MagicMock()
        mock_factory.return_value = MagicMock(return_value=mock_session)

        mock_session.query.return_value.filter.return_value.all.return_value = [account]
        mock_session.query.return_value.join.return_value.filter.return_value.distinct.return_value.all.return_value = [campaign]

        mock_resume.side_effect = RuntimeError("Provider error")

        from app.tasks.auto_resume import auto_resume_paused

        result = auto_resume_paused()

        assert result["status"] == "ok"
        assert result["total_resumed"] == 0

    @patch("app.database.get_sync_session_factory")
    @patch("redis.from_url")
    def test_rolls_back_on_unexpected_error(self, mock_from_url, mock_factory):
        """On unexpected error, session is rolled back."""
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        mock_session = MagicMock()
        mock_factory.return_value = MagicMock(return_value=mock_session)

        # Make account query raise
        mock_session.query.return_value.filter.return_value.all.side_effect = RuntimeError("DB error")

        from app.tasks.auto_resume import auto_resume_paused

        result = auto_resume_paused()

        assert result["status"] == "error"
        mock_session.rollback.assert_called_once()


class TestAutoResumeBeatConfig:
    """Verify beat schedule configuration."""

    def test_auto_resume_in_beat_schedule(self):
        from app.tasks.celery_app import celery_app

        assert "auto-resume-daily" in celery_app.conf.beat_schedule

    def test_auto_resume_task_name(self):
        from app.tasks.celery_app import celery_app

        entry = celery_app.conf.beat_schedule["auto-resume-daily"]
        assert entry["task"] == "app.tasks.auto_resume.auto_resume_paused"

    def test_auto_resume_schedule_is_crontab(self):
        from celery.schedules import crontab

        from app.tasks.celery_app import celery_app

        entry = celery_app.conf.beat_schedule["auto-resume-daily"]
        assert isinstance(entry["schedule"], crontab)
