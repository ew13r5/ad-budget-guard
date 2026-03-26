"""Action executor for rule-triggered pauses."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.alerts.alert_manager import AlertManager
from app.models.alert_log import AlertChannel, AlertLog, AlertType
from app.models.campaign import Campaign, CampaignStatus
from app.models.pause_log import PauseLog
from app.models.rule_evaluation import EvaluationResult, RuleEvaluation

logger = logging.getLogger(__name__)


class ActionExecutor:
    """Executes pause actions and logs results."""

    def __init__(self, alert_service: AlertManager | None = None):
        self._alert_service = alert_service or AlertManager()

    def execute_soft_pause(
        self,
        provider,
        campaign_id: UUID,
        rule,
        current_value: Decimal,
        db: Session,
    ) -> bool:
        success = False
        try:
            provider.pause_campaign(str(campaign_id))
            success = True
        except Exception:
            logger.exception("Failed to pause campaign %s", campaign_id)

        # Record evaluation regardless
        evaluation = RuleEvaluation(
            rule_id=rule.id,
            result=EvaluationResult.triggered,
            current_value=current_value,
            threshold_value=rule.threshold,
            timestamp=datetime.now(timezone.utc),
            details={"action": "soft_pause", "campaign_id": str(campaign_id), "success": success},
        )
        db.add(evaluation)

        if success:
            pause_log = PauseLog(
                campaign_id=campaign_id,
                rule_id=rule.id,
                reason=f"Soft pause: {rule.rule_type.value} threshold {rule.threshold} exceeded ({current_value})",
            )
            db.add(pause_log)

            self._alert_service.send_alert(
                db=db,
                account_id=rule.account_id,
                alert_type=AlertType.pause,
                message=f"Campaign {campaign_id} paused: {rule.rule_type.value} {current_value}/{rule.threshold}",
            )

        db.flush()
        return success

    def execute_hard_pause(
        self,
        provider,
        account_id: UUID,
        rule,
        current_value: Decimal,
        db: Session,
    ) -> int:
        campaigns = (
            db.query(Campaign)
            .filter(Campaign.account_id == account_id, Campaign.status == CampaignStatus.ACTIVE)
            .all()
        )

        paused_count = 0
        for campaign in campaigns:
            try:
                provider.pause_campaign(str(campaign.id))
                pause_log = PauseLog(
                    campaign_id=campaign.id,
                    rule_id=rule.id,
                    reason=f"Hard pause: {rule.rule_type.value} threshold {rule.threshold} exceeded ({current_value})",
                )
                db.add(pause_log)
                paused_count += 1
            except Exception:
                logger.exception("Failed to hard-pause campaign %s", campaign.id)

        evaluation = RuleEvaluation(
            rule_id=rule.id,
            result=EvaluationResult.triggered,
            current_value=current_value,
            threshold_value=rule.threshold,
            timestamp=datetime.now(timezone.utc),
            details={
                "action": "hard_pause",
                "account_id": str(account_id),
                "campaigns_paused": paused_count,
                "campaigns_total": len(campaigns),
            },
        )
        db.add(evaluation)

        self._alert_service.send_alert(
            db=db,
            account_id=account_id,
            alert_type=AlertType.anomaly if rule.rule_type.value == "anomaly" else AlertType.pause,
            message=f"Hard pause on account {account_id}: {paused_count} campaigns paused. {rule.rule_type.value} {current_value}/{rule.threshold}",
        )

        db.flush()
        return paused_count
