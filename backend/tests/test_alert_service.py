"""Tests for AlertService."""
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.alert_log import AlertType
from app.services.alert_service import AlertService, StubAlertService


class TestAlertServiceABC:
    def test_cannot_instantiate_abc(self):
        with pytest.raises(TypeError):
            AlertService()


class TestStubAlertService:
    def test_creates_alert_log(self):
        db = MagicMock()
        service = StubAlertService(db)

        service.send_alert(
            account_id=uuid4(),
            alert_type=AlertType.pause,
            message="Test alert",
        )

        db.add.assert_called_once()
        db.flush.assert_called_once()

    def test_alert_has_correct_fields(self):
        db = MagicMock()
        service = StubAlertService(db)
        account_id = uuid4()

        service.send_alert(
            account_id=account_id,
            alert_type=AlertType.anomaly,
            message="Spike detected",
        )

        alert = db.add.call_args[0][0]
        assert alert.account_id == account_id
        assert alert.alert_type == AlertType.anomaly
        assert alert.message == "Spike detected"
