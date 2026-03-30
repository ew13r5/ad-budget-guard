"""SMTP email sender for alert notifications. Sync — used from Celery workers."""
from __future__ import annotations

import logging
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from app.config import Settings

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "templates"


class EmailSender:
    """Sends HTML alert emails via SMTP. Sync — used from Celery workers."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._jinja_env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=True,
        )

    def send_alert(
        self,
        to: str,
        subject: str,
        alert_type: str,
        message: str,
        severity: str,
        account_name: str = "",
    ) -> bool:
        """Send an HTML alert email. Returns True on success."""
        if not self._settings.smtp_host:
            logger.info("smtp_not_configured")
            return False

        # Render HTML body
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        try:
            template = self._jinja_env.get_template("alert_email.html")
            html_body = template.render(
                alert_type=alert_type,
                severity=severity,
                message=message,
                account_name=account_name,
                timestamp=timestamp,
            )
        except TemplateNotFound:
            logger.warning("email_template_not_found, using plain text fallback")
            html_body = None
        except Exception:
            logger.exception("email_template_render_error")
            html_body = None

        # Build MIME message
        msg = MIMEMultipart("alternative")
        msg["From"] = self._settings.smtp_from or self._settings.smtp_user
        msg["To"] = to
        msg["Subject"] = subject

        msg.attach(MIMEText(message, "plain"))
        if html_body:
            msg.attach(MIMEText(html_body, "html"))

        # Send
        try:
            if self._settings.smtp_use_ssl:
                server = smtplib.SMTP_SSL(
                    self._settings.smtp_host, self._settings.smtp_port
                )
            else:
                server = smtplib.SMTP(
                    self._settings.smtp_host, self._settings.smtp_port
                )
                server.ehlo()
                server.starttls()

            with server:
                if self._settings.smtp_user and self._settings.smtp_password:
                    server.login(self._settings.smtp_user, self._settings.smtp_password)
                server.sendmail(msg["From"], [to], msg.as_string())

            logger.info("email_sent", extra={"to": to, "subject": subject})
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("smtp_auth_failed", extra={"host": self._settings.smtp_host})
            return False
        except smtplib.SMTPRecipientsRefused as e:
            logger.error("smtp_recipients_refused", extra={"recipients": str(e.recipients)})
            return False
        except ConnectionRefusedError:
            logger.error("smtp_connection_refused", extra={
                "host": self._settings.smtp_host,
                "port": self._settings.smtp_port,
            })
            return False
        except Exception:
            logger.exception("smtp_send_error")
            return False

    def send_test(self, to: str) -> bool:
        """Send a test email to verify SMTP configuration."""
        return self.send_alert(
            to=to,
            subject="Ad Budget Guard — Test Email",
            alert_type="test",
            message="This is a test alert from Ad Budget Guard. If you received this, your email configuration is working correctly.",
            severity="info",
            account_name="Test",
        )
