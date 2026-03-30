"""Tests for EmailSender."""
from unittest.mock import MagicMock, patch, ANY

import pytest

from app.alerts.email_sender import EmailSender
from app.config import Settings


def _make_settings(**overrides) -> Settings:
    defaults = {
        "database_url": "postgresql://test:test@localhost/test",
        "redis_url": "redis://localhost:6379/0",
        "celery_broker_url": "redis://localhost:6379/1",
        "celery_result_backend": "redis://localhost:6379/2",
        "meta_app_id": "test",
        "meta_app_secret": "test",
        "secret_key": "test-secret",
        "encryption_key": "test-encryption-key-32chars-!!",
        "smtp_host": "smtp.test.com",
        "smtp_port": 587,
        "smtp_user": "user@test.com",
        "smtp_password": "password",
        "smtp_from": "noreply@test.com",
        "smtp_use_ssl": False,
    }
    defaults.update(overrides)
    return Settings(**defaults)


class TestEmailSender:
    def test_send_alert_skips_when_smtp_host_empty(self):
        settings = _make_settings(smtp_host="")
        sender = EmailSender(settings)
        result = sender.send_alert(
            to="user@example.com",
            subject="Test",
            alert_type="test",
            message="Hello",
            severity="info",
        )
        assert result is False

    @patch("app.alerts.email_sender.smtplib.SMTP")
    def test_send_alert_uses_starttls(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server
        mock_server.__enter__ = MagicMock(return_value=mock_server)
        mock_server.__exit__ = MagicMock(return_value=False)

        settings = _make_settings(smtp_use_ssl=False)
        sender = EmailSender(settings)
        result = sender.send_alert(
            to="user@example.com",
            subject="Test",
            alert_type="budget_exceeded",
            message="Budget exceeded",
            severity="critical",
        )

        assert result is True
        mock_smtp_cls.assert_called_once_with("smtp.test.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user@test.com", "password")
        mock_server.sendmail.assert_called_once()

    @patch("app.alerts.email_sender.smtplib.SMTP_SSL")
    def test_send_alert_uses_smtp_ssl(self, mock_smtp_ssl_cls):
        mock_server = MagicMock()
        mock_smtp_ssl_cls.return_value = mock_server
        mock_server.__enter__ = MagicMock(return_value=mock_server)
        mock_server.__exit__ = MagicMock(return_value=False)

        settings = _make_settings(smtp_use_ssl=True, smtp_port=465)
        sender = EmailSender(settings)
        result = sender.send_alert(
            to="user@example.com",
            subject="Test",
            alert_type="test",
            message="SSL test",
            severity="info",
        )

        assert result is True
        mock_smtp_ssl_cls.assert_called_once_with("smtp.test.com", 465)

    @patch("app.alerts.email_sender.smtplib.SMTP")
    def test_send_alert_returns_false_on_auth_error(self, mock_smtp_cls):
        import smtplib
        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server
        mock_server.__enter__ = MagicMock(return_value=mock_server)
        mock_server.__exit__ = MagicMock(return_value=False)
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")

        settings = _make_settings()
        sender = EmailSender(settings)
        result = sender.send_alert(
            to="user@example.com",
            subject="Test",
            alert_type="test",
            message="Auth test",
            severity="info",
        )
        assert result is False

    @patch("app.alerts.email_sender.smtplib.SMTP")
    def test_send_alert_returns_false_on_connection_refused(self, mock_smtp_cls):
        mock_smtp_cls.side_effect = ConnectionRefusedError("Connection refused")

        settings = _make_settings()
        sender = EmailSender(settings)
        result = sender.send_alert(
            to="user@example.com",
            subject="Test",
            alert_type="test",
            message="Connection test",
            severity="info",
        )
        assert result is False

    @patch("app.alerts.email_sender.smtplib.SMTP")
    def test_send_alert_returns_false_on_recipients_refused(self, mock_smtp_cls):
        import smtplib
        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server
        mock_server.__enter__ = MagicMock(return_value=mock_server)
        mock_server.__exit__ = MagicMock(return_value=False)
        mock_server.sendmail.side_effect = smtplib.SMTPRecipientsRefused(
            {"bad@example.com": (550, b"User unknown")}
        )

        settings = _make_settings()
        sender = EmailSender(settings)
        result = sender.send_alert(
            to="bad@example.com",
            subject="Test",
            alert_type="test",
            message="Recipient test",
            severity="info",
        )
        assert result is False

    @patch("app.alerts.email_sender.smtplib.SMTP")
    def test_send_test_sends_test_email(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server
        mock_server.__enter__ = MagicMock(return_value=mock_server)
        mock_server.__exit__ = MagicMock(return_value=False)

        settings = _make_settings()
        sender = EmailSender(settings)
        result = sender.send_test("user@example.com")
        assert result is True
        mock_server.sendmail.assert_called_once()

    def test_template_renders_with_variables(self):
        from jinja2 import Environment, FileSystemLoader
        from pathlib import Path

        templates_dir = Path(__file__).parent.parent / "app" / "alerts" / "templates"
        env = Environment(loader=FileSystemLoader(str(templates_dir)), autoescape=True)
        template = env.get_template("alert_email.html")
        html = template.render(
            alert_type="budget_exceeded",
            severity="critical",
            message="Daily spend exceeded $500",
            account_name="Client-Alpha",
            timestamp="2026-03-30 12:00:00 UTC",
        )
        assert "budget_exceeded" in html
        assert "Client-Alpha" in html
        assert "Daily spend exceeded $500" in html
        assert "#dc2626" in html  # critical color

    @patch("app.alerts.email_sender.smtplib.SMTP")
    def test_template_fallback_to_plain_text(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server
        mock_server.__enter__ = MagicMock(return_value=mock_server)
        mock_server.__exit__ = MagicMock(return_value=False)

        settings = _make_settings()
        sender = EmailSender(settings)
        # Break template loading
        sender._jinja_env.loader = None

        result = sender.send_alert(
            to="user@example.com",
            subject="Test",
            alert_type="test",
            message="Fallback test",
            severity="info",
        )
        # Should still send (plain text fallback)
        assert result is True
        mock_server.sendmail.assert_called_once()
