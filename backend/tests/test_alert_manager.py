"""Tests for AlertManager."""
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.alerts.alert_manager import AlertManager
from app.models.alert_log import AlertType


class TestAlertManagerDedup:
    def test_dedup_key_format_with_campaign(self):
        manager = AlertManager()
        account_id = uuid4()
        campaign_id = uuid4()
        key = manager._dedup_key(account_id, "pause", campaign_id)
        assert f"alert:dedup:{account_id}:pause:{campaign_id}" == key

    def test_dedup_key_format_without_campaign(self):
        manager = AlertManager()
        account_id = uuid4()
        key = manager._dedup_key(account_id, "budget_warning")
        assert f"alert:dedup:{account_id}:budget_warning:account" == key

    def test_is_duplicate_first_call_returns_false(self, redis_client):
        manager = AlertManager(redis_client=redis_client, cooldown_seconds=60)
        account_id = uuid4()
        result = manager._is_duplicate(account_id, "pause")
        assert result is False

    def test_is_duplicate_second_call_returns_true(self, redis_client):
        manager = AlertManager(redis_client=redis_client, cooldown_seconds=60)
        account_id = uuid4()
        manager._is_duplicate(account_id, "pause")
        result = manager._is_duplicate(account_id, "pause")
        assert result is True

    def test_different_types_not_duplicates(self, redis_client):
        manager = AlertManager(redis_client=redis_client, cooldown_seconds=60)
        account_id = uuid4()
        manager._is_duplicate(account_id, "pause")
        result = manager._is_duplicate(account_id, "anomaly")
        assert result is False


class TestAlertManagerDispatch:
    def test_dispatch_creates_in_app_alert(self, redis_client):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        manager = AlertManager(redis_client=redis_client)
        account_id = uuid4()

        manager.dispatch(
            db=db,
            account_id=account_id,
            alert_type="pause",
            severity="warning",
            message="Test alert",
        )

        db.add.assert_called_once()
        db.flush.assert_called_once()
        alert = db.add.call_args[0][0]
        assert alert.message == "Test alert"
        assert alert.severity == "warning"

    def test_dispatch_dedup_skips(self, redis_client):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        manager = AlertManager(redis_client=redis_client)
        account_id = uuid4()

        manager.dispatch(
            db=db, account_id=account_id,
            alert_type="pause", severity="warning", message="First",
        )

        db.reset_mock()

        manager.dispatch(
            db=db, account_id=account_id,
            alert_type="pause", severity="warning", message="Second",
        )

        # Second call should be deduplicated
        db.add.assert_not_called()

    @patch("app.alerts.alert_manager.AlertManager._handle_telegram")
    def test_dispatch_routes_to_telegram(self, mock_tg, redis_client):
        from app.models.alert_config import AlertConfig

        config = MagicMock(spec=AlertConfig)
        config.channel = "telegram"
        config.destination = "123"
        config.severity_filter = "info"
        config.is_enabled = True

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [config]

        manager = AlertManager(redis_client=redis_client)
        account_id = uuid4()

        manager.dispatch(
            db=db, account_id=account_id,
            alert_type="pause", severity="warning", message="Test",
        )

        mock_tg.assert_called_once_with("123", account_id, "pause", "warning", "Test")

    def test_dispatch_filters_by_severity(self, redis_client):
        from app.models.alert_config import AlertConfig

        config = MagicMock(spec=AlertConfig)
        config.channel = "telegram"
        config.destination = "123"
        config.severity_filter = "critical"
        config.is_enabled = True

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [config]

        manager = AlertManager(redis_client=redis_client)

        with patch.object(manager, "_handle_telegram") as mock_tg:
            manager.dispatch(
                db=db, account_id=uuid4(),
                alert_type="pause", severity="info", message="Low severity",
            )
            mock_tg.assert_not_called()


class TestAlertManagerCompatibility:
    def test_send_alert_matches_old_signature(self, redis_client):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        manager = AlertManager(redis_client=redis_client)
        account_id = uuid4()

        # This must work with the ActionExecutor calling pattern
        manager.send_alert(
            db=db,
            account_id=account_id,
            alert_type=AlertType.pause,
            message="Campaign paused",
        )

        db.add.assert_called_once()
        alert = db.add.call_args[0][0]
        assert alert.message == "Campaign paused"

    def test_send_alert_with_string_type(self, redis_client):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        manager = AlertManager(redis_client=redis_client)

        manager.send_alert(
            db=db,
            account_id=uuid4(),
            alert_type=AlertType.anomaly,
            message="Anomaly detected",
        )

        db.add.assert_called_once()
