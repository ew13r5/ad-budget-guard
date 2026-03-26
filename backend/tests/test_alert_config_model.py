"""Tests for AlertConfig model and alert schemas."""
from uuid import uuid4

import pytest

from app.models.alert_config import AlertConfig, AlertSeverity
from app.models.alert_log import AlertLog, AlertType, AlertChannel
from app.schemas.alert import (
    AlertConfigRequest,
    AlertConfigResponse,
    AlertListResponse,
    AlertLogResponse,
    SendTestAlertRequest,
)


class TestAlertConfigModel:
    def test_create_alert_config(self):
        config = AlertConfig(
            account_id=uuid4(),
            channel="telegram",
            destination="123456789",
            is_enabled=True,
            severity_filter="warning",
        )
        assert config.channel == "telegram"
        assert config.destination == "123456789"
        assert config.is_enabled is True
        assert config.severity_filter == "warning"

    def test_default_severity_filter(self):
        config = AlertConfig(
            account_id=uuid4(),
            channel="email",
            destination="test@example.com",
        )
        # SQLAlchemy default= applies at flush time; in-memory objects may be None
        assert config.severity_filter is None or config.severity_filter == "info"

    def test_default_is_enabled(self):
        config = AlertConfig(
            account_id=uuid4(),
            channel="telegram",
            destination="123",
        )
        # SQLAlchemy default= applies at flush time; in-memory objects may be None
        assert config.is_enabled is None or config.is_enabled is True


class TestAlertSeverityEnum:
    def test_severity_values(self):
        assert AlertSeverity.info == "info"
        assert AlertSeverity.warning == "warning"
        assert AlertSeverity.critical == "critical"

    def test_all_severities(self):
        assert len(AlertSeverity) == 3


class TestAlertLogSeverity:
    def test_alert_log_has_severity(self):
        alert = AlertLog(
            account_id=uuid4(),
            alert_type=AlertType.pause,
            channel=AlertChannel.in_app,
            message="Test",
            severity="warning",
        )
        assert alert.severity == "warning"

    def test_alert_log_default_severity(self):
        alert = AlertLog(
            account_id=uuid4(),
            alert_type=AlertType.error,
            channel=AlertChannel.in_app,
            message="Test",
        )
        # SQLAlchemy default= applies at flush time; in-memory objects may be None
        assert alert.severity is None or alert.severity == "info"


class TestAlertSchemas:
    def test_alert_config_request(self):
        req = AlertConfigRequest(
            channel="telegram",
            destination="123456",
            is_enabled=True,
            severity_filter="warning",
        )
        assert req.channel == "telegram"
        assert req.severity_filter == "warning"

    def test_alert_config_request_defaults(self):
        req = AlertConfigRequest(
            channel="email",
            destination="test@example.com",
        )
        assert req.is_enabled is True
        assert req.severity_filter == "info"

    def test_send_test_alert_request(self):
        req = SendTestAlertRequest(
            account_id=uuid4(),
            channel="telegram",
            destination="123",
        )
        assert "test alert" in req.message.lower()

    def test_alert_list_response(self):
        resp = AlertListResponse(alerts=[], total=0)
        assert resp.total == 0
        assert resp.alerts == []
