"""AlertManager — central dispatch for all alert channels."""
from __future__ import annotations

import json
import logging
import os
from typing import Optional
from uuid import UUID

import redis as sync_redis
from sqlalchemy.orm import Session

from app.models.alert_config import AlertConfig
from app.models.alert_log import AlertChannel, AlertLog, AlertType

logger = logging.getLogger(__name__)

# Severity weights for filtering
_SEVERITY_WEIGHT = {"info": 0, "warning": 1, "critical": 2}

DEFAULT_COOLDOWN_SECONDS = int(os.getenv("ALERT_COOLDOWN_SECONDS", "300"))


class AlertManager:
    """Routes alerts to configured channels with deduplication."""

    def __init__(
        self,
        redis_client: Optional[sync_redis.Redis] = None,
        cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS,
    ):
        self._redis = redis_client
        self._cooldown = cooldown_seconds

    def _get_redis(self) -> sync_redis.Redis:
        if self._redis is None:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self._redis = sync_redis.from_url(redis_url)
        return self._redis

    def _dedup_key(
        self, account_id: UUID, alert_type: str, campaign_id: Optional[UUID] = None
    ) -> str:
        suffix = str(campaign_id) if campaign_id else "account"
        return f"alert:dedup:{account_id}:{alert_type}:{suffix}"

    def _is_duplicate(
        self, account_id: UUID, alert_type: str, campaign_id: Optional[UUID] = None
    ) -> bool:
        try:
            r = self._get_redis()
            key = self._dedup_key(account_id, alert_type, campaign_id)
            if r.exists(key):
                return True
            r.setex(key, self._cooldown, "1")
            return False
        except Exception:
            logger.exception("dedup_check_failed")
            return False

    def dispatch(
        self,
        db: Session,
        account_id: UUID,
        alert_type: str,
        severity: str,
        message: str,
        details: Optional[dict] = None,
        campaign_id: Optional[UUID] = None,
    ) -> None:
        """Dispatch alert to all configured channels for the account."""
        if self._is_duplicate(account_id, alert_type, campaign_id):
            logger.info("alert_deduplicated", extra={
                "account_id": str(account_id),
                "alert_type": alert_type,
            })
            return

        # Get configs for this account
        configs = (
            db.query(AlertConfig)
            .filter(
                AlertConfig.account_id == account_id,
                AlertConfig.is_enabled.is_(True),
            )
            .all()
        )

        # Always create in-app alert
        self._handle_in_app(db, account_id, alert_type, severity, message)

        for config in configs:
            config_severity_weight = _SEVERITY_WEIGHT.get(config.severity_filter, 0)
            alert_severity_weight = _SEVERITY_WEIGHT.get(severity, 0)
            if alert_severity_weight < config_severity_weight:
                continue

            channel = config.channel
            if channel == "telegram":
                self._handle_telegram(config.destination, account_id, alert_type, severity, message)
            elif channel == "email":
                self._handle_email(config.destination, message, alert_type, severity, str(account_id))
            else:
                logger.warning("unknown_channel", extra={"channel": channel})

    def _handle_in_app(
        self,
        db: Session,
        account_id: UUID,
        alert_type: str,
        severity: str,
        message: str,
    ) -> None:
        try:
            at = AlertType(alert_type) if alert_type in AlertType.__members__ else AlertType.error
        except (ValueError, KeyError):
            at = AlertType.error

        alert = AlertLog(
            account_id=account_id,
            alert_type=at,
            channel=AlertChannel.in_app,
            message=message,
            severity=severity,
        )
        db.add(alert)
        db.flush()

        # Publish to Redis Pub/Sub for real-time
        try:
            r = self._get_redis()
            r.publish(
                f"alerts:{account_id}",
                json.dumps({
                    "alert_id": str(alert.id),
                    "alert_type": alert_type,
                    "severity": severity,
                    "message": message,
                }),
            )
        except Exception:
            logger.exception("pubsub_publish_failed")

    def _handle_telegram(
        self,
        destination: str,
        account_id: UUID,
        alert_type: str,
        severity: str,
        message: str,
    ) -> None:
        try:
            from app.alerts.telegram_sender import TelegramSender

            sender = TelegramSender()
            sender.send_alert(
                chat_id=destination,
                account_name=str(account_id),
                message=message,
                severity=severity,
            )
        except Exception:
            logger.exception("telegram_dispatch_failed")

    def _handle_email(
        self,
        destination: str,
        message: str,
        alert_type: str = "",
        severity: str = "info",
        account_name: str = "",
    ) -> None:
        try:
            from app.alerts.email_sender import EmailSender
            from app.config import get_settings

            sender = EmailSender(get_settings())
            subject = f"[{severity.upper()}] Ad Budget Guard — {alert_type}"
            sender.send_alert(
                to=destination,
                subject=subject,
                alert_type=alert_type,
                message=message,
                severity=severity,
                account_name=account_name,
            )
        except Exception:
            logger.exception("email_dispatch_failed")

    def send_alert(
        self,
        db: Session,
        account_id: UUID,
        alert_type: AlertType,
        message: str,
    ) -> None:
        """Compatibility interface for ActionExecutor.

        Matches the old AlertService.send_alert(db, account_id, alert_type, message) signature.
        """
        self.dispatch(
            db=db,
            account_id=account_id,
            alert_type=alert_type.value if isinstance(alert_type, AlertType) else alert_type,
            severity="warning",
            message=message,
        )
