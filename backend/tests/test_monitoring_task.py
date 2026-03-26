"""Tests for the check_all_accounts Celery task."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.models.ad_account import AccountMode
from app.rules.models import MonitoringResult


class TestCheckAllAccounts:
    """Tests for app.tasks.monitoring.check_all_accounts."""

    @patch("app.database.get_sync_session_factory")
    @patch("redis.from_url")
    def test_skips_when_lock_held(self, mock_from_url, mock_factory):
        """If another worker holds the lock, task returns 'skipped'."""
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client
        mock_client.set.return_value = False  # lock NOT acquired

        from app.tasks.monitoring import check_all_accounts

        result = check_all_accounts()

        assert result["status"] == "skipped"
        assert result["reason"] == "lock_held"

    @patch("app.database.get_sync_session_factory")
    @patch("redis.from_url")
    def test_acquires_lock_and_releases(self, mock_from_url, mock_factory):
        """Lock is acquired with NX+EX and released after completion."""
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client
        mock_client.set.return_value = True  # lock acquired

        mock_session = MagicMock()
        mock_factory.return_value = MagicMock(return_value=mock_session)
        mock_session.query.return_value.filter.return_value.all.return_value = []

        from app.tasks.monitoring import check_all_accounts

        result = check_all_accounts()

        assert result["status"] == "ok"
        assert result["accounts_checked"] == 0
        # Lock released
        mock_client.delete.assert_called_once()

    @patch("app.services.monitoring_service.MonitoringService.check_account")
    @patch("app.database.get_sync_session_factory")
    @patch("redis.from_url")
    def test_checks_all_active_accounts(
        self, mock_from_url, mock_factory, mock_check,
    ):
        """All active accounts are checked."""
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client
        mock_client.set.return_value = True

        account1 = SimpleNamespace(
            id=uuid4(), is_active=True, mode=AccountMode.simulation,
        )
        account2 = SimpleNamespace(
            id=uuid4(), is_active=True, mode=AccountMode.simulation,
        )

        mock_session = MagicMock()
        mock_factory.return_value = MagicMock(return_value=mock_session)
        mock_session.query.return_value.filter.return_value.all.return_value = [
            account1, account2,
        ]

        mock_check.return_value = MonitoringResult(
            account_id=account1.id,
            evaluations=[],
            actions_taken=[],
            timestamp=datetime.now(timezone.utc),
        )

        from app.tasks.monitoring import check_all_accounts

        result = check_all_accounts()

        assert result["status"] == "ok"
        assert result["accounts_checked"] == 2
        assert mock_check.call_count == 2

    @patch("app.services.monitoring_service.MonitoringService.check_account")
    @patch("app.database.get_sync_session_factory")
    @patch("redis.from_url")
    def test_continues_on_account_error(
        self, mock_from_url, mock_factory, mock_check,
    ):
        """If one account fails, others are still checked."""
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client
        mock_client.set.return_value = True

        account1 = SimpleNamespace(id=uuid4(), is_active=True, mode=AccountMode.simulation)
        account2 = SimpleNamespace(id=uuid4(), is_active=True, mode=AccountMode.simulation)

        mock_session = MagicMock()
        mock_factory.return_value = MagicMock(return_value=mock_session)
        mock_session.query.return_value.filter.return_value.all.return_value = [
            account1, account2,
        ]

        # First call raises, second succeeds
        mock_check.side_effect = [
            RuntimeError("boom"),
            MonitoringResult(
                account_id=account2.id,
                evaluations=[],
                actions_taken=[],
                timestamp=datetime.now(timezone.utc),
            ),
        ]

        from app.tasks.monitoring import check_all_accounts

        result = check_all_accounts()

        assert result["status"] == "ok"
        assert result["accounts_checked"] == 1

    @patch("app.database.get_sync_session_factory")
    @patch("redis.from_url")
    def test_lock_released_on_exception(self, mock_from_url, mock_factory):
        """Lock is always released even if an exception occurs."""
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client
        mock_client.set.return_value = True

        mock_factory.return_value = MagicMock(side_effect=RuntimeError("DB init failed"))

        from app.tasks.monitoring import check_all_accounts

        with pytest.raises(RuntimeError, match="DB init failed"):
            check_all_accounts()

        mock_client.delete.assert_called_once()


class TestCheckAllAccountsIntegration:
    """Integration-style tests using redis_client fixture."""

    def test_lock_key_format(self, redis_client):
        """Verify the lock key is correctly set in Redis."""
        from app.tasks.monitoring import MONITORING_LOCK_KEY

        assert MONITORING_LOCK_KEY == "monitoring:check_lock"

    def test_redis_lock_mechanism(self, redis_client):
        """Verify NX-based lock works correctly."""
        from app.tasks.monitoring import MONITORING_LOCK_KEY, MONITORING_LOCK_TTL

        # First set should succeed
        acquired = redis_client.set(MONITORING_LOCK_KEY, "1", nx=True, ex=MONITORING_LOCK_TTL)
        assert acquired is True

        # Second set should fail (lock held)
        acquired2 = redis_client.set(MONITORING_LOCK_KEY, "1", nx=True, ex=MONITORING_LOCK_TTL)
        assert acquired2 is not True

        # After delete, should succeed again
        redis_client.delete(MONITORING_LOCK_KEY)
        acquired3 = redis_client.set(MONITORING_LOCK_KEY, "1", nx=True, ex=MONITORING_LOCK_TTL)
        assert acquired3 is True
