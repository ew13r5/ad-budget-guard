"""Central monitoring orchestration service."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

import redis
from sqlalchemy.orm import Session

from app.models.ad_account import AdAccount
from app.models.budget_rule import BudgetRule
from app.models.campaign import Campaign, CampaignStatus
from app.models.rule_evaluation import EvaluationResult, RuleEvaluation
from app.models.spend_snapshot import SpendSnapshot, SpendSource
from app.rules.actions import ActionExecutor
from app.rules.engine import RuleEvaluator
from app.rules.models import EvaluationContext, MonitoringResult
from app.schemas.common import CampaignSpendData, SpendData
from app.services.forecast_service import ForecastService

logger = logging.getLogger(__name__)


class MonitoringService:
    """Orchestrates the full monitoring cycle for an account."""

    def __init__(
        self,
        evaluator: RuleEvaluator,
        executor: ActionExecutor,
        forecast: ForecastService,
    ):
        self._evaluator = evaluator
        self._executor = executor
        self._forecast = forecast

    def check_account(
        self,
        account_id: UUID,
        provider,
        db: Session,
        redis_client: redis.Redis | None = None,
    ) -> MonitoringResult:
        now = datetime.now(timezone.utc)
        actions_taken: list[dict] = []

        # 1. Fetch current spend
        spend_data = provider.get_current_spend(str(account_id))
        if not isinstance(spend_data, SpendData):
            spend_data = SpendData(
                account_id=account_id,
                total_spend_today=Decimal(str(spend_data.get("total_spend_today", 0))),
                total_spend_month=Decimal(str(spend_data.get("total_spend_month", 0))),
                last_updated=now,
            )

        # 2. Get active campaigns and their spend
        campaigns = (
            db.query(Campaign)
            .filter(Campaign.account_id == account_id, Campaign.status == CampaignStatus.ACTIVE)
            .all()
        )

        campaign_spends: list[CampaignSpendData] = []
        for campaign in campaigns:
            try:
                cs = provider.get_campaign_spend(str(campaign.id))
                if isinstance(cs, CampaignSpendData):
                    campaign_spends.append(cs)
                else:
                    campaign_spends.append(CampaignSpendData(
                        campaign_id=campaign.id,
                        spend_today=Decimal(str(cs.get("spend_today", 0))),
                        spend_rate_per_hour=Decimal(str(cs.get("spend_rate_per_hour", 0))),
                        last_updated=now,
                    ))
            except Exception:
                logger.warning("Failed to get spend for campaign %s", campaign.id)

        # 3. Save spend snapshots
        account = db.query(AdAccount).filter(AdAccount.id == account_id).first()
        source = SpendSource.simulator if account and account.mode.value == "simulation" else SpendSource.api

        for cs in campaign_spends:
            snapshot = SpendSnapshot(
                campaign_id=cs.campaign_id,
                spend=cs.spend_today,
                source=source,
                timestamp=now,
            )
            db.add(snapshot)

        # 4. Build evaluation context
        rules = (
            db.query(BudgetRule)
            .filter(BudgetRule.account_id == account_id, BudgetRule.is_active.is_(True))
            .all()
        )

        historical = (
            db.query(SpendSnapshot)
            .join(Campaign, SpendSnapshot.campaign_id == Campaign.id)
            .filter(
                Campaign.account_id == account_id,
                SpendSnapshot.timestamp >= now - timedelta(hours=1),
            )
            .all()
        )

        context = EvaluationContext(
            account_id=account_id,
            spend_data=spend_data,
            campaign_spends=campaign_spends,
            rules=rules,
            historical_snapshots=historical,
        )

        # 5. Evaluate rules
        evaluations = self._evaluator.evaluate(context)

        # 6. Execute actions for triggered rules
        for result in evaluations:
            if not result.action_required:
                continue

            rule = next((r for r in rules if r.id == result.rule_id), None)
            if not rule:
                continue

            if rule.action.value == "hard_pause":
                count = self._executor.execute_hard_pause(
                    provider, account_id, rule, result.current_value, db
                )
                actions_taken.append({
                    "action": "hard_pause",
                    "rule_id": str(rule.id),
                    "campaigns_paused": count,
                })
            else:
                campaign_id = rule.campaign_id or (campaigns[0].id if campaigns else None)
                if campaign_id:
                    success = self._executor.execute_soft_pause(
                        provider, campaign_id, rule, result.current_value, db
                    )
                    actions_taken.append({
                        "action": "soft_pause",
                        "rule_id": str(rule.id),
                        "campaign_id": str(campaign_id),
                        "success": success,
                    })

        # 7. Create RuleEvaluation records for non-triggered results
        for result in evaluations:
            if not result.action_required:
                eval_record = RuleEvaluation(
                    rule_id=result.rule_id,
                    result=result.result,
                    current_value=result.current_value,
                    threshold_value=result.threshold_value,
                    timestamp=now,
                    details=result.details,
                )
                db.add(eval_record)

        # 8. Forecast
        forecast_result = None
        try:
            forecast_result = self._forecast.calculate(account_id, spend_data, db)
        except Exception:
            logger.exception("Forecast failed for account %s", account_id)

        # 9. Publish to Redis Pub/Sub
        if redis_client:
            try:
                payload = {
                    "account_id": str(account_id),
                    "spend_today": str(spend_data.total_spend_today),
                    "evaluations": len(evaluations),
                    "actions": len(actions_taken),
                    "forecast_eod": str(forecast_result.forecast_eod) if forecast_result else None,
                    "warning_level": forecast_result.warning_level if forecast_result else None,
                    "timestamp": now.isoformat(),
                }
                redis_client.publish(
                    f"monitoring:updates:{account_id}",
                    json.dumps(payload),
                )
            except Exception:
                logger.warning("Failed to publish monitoring update")

        # 10. Commit
        db.commit()

        return MonitoringResult(
            account_id=account_id,
            evaluations=evaluations,
            actions_taken=actions_taken,
            forecast=forecast_result,
            timestamp=now,
        )
