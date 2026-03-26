"""Alert service interface and stub implementation."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.alert_log import AlertChannel, AlertLog, AlertType

logger = logging.getLogger(__name__)


class AlertService(ABC):
    """Abstract base for alert delivery."""

    @abstractmethod
    def send_alert(
        self,
        account_id: UUID,
        alert_type: AlertType,
        message: str,
        details: dict | None = None,
    ) -> None: ...


class StubAlertService(AlertService):
    """In-app alert service that creates AlertLog records."""

    def __init__(self, db: Session):
        self._db = db

    def send_alert(
        self,
        account_id: UUID,
        alert_type: AlertType,
        message: str,
        details: dict | None = None,
    ) -> None:
        logger.info(
            "alert_created",
            extra={
                "account_id": str(account_id),
                "alert_type": alert_type.value,
                "message": message,
            },
        )
        alert = AlertLog(
            account_id=account_id,
            alert_type=alert_type,
            channel=AlertChannel.in_app,
            message=message,
        )
        self._db.add(alert)
        self._db.flush()
