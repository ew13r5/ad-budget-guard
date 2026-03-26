"""Pydantic models for the rule evaluation pipeline."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.budget_rule import RuleAction, RuleType
from app.models.rule_evaluation import EvaluationResult
from app.schemas.common import CampaignSpendData, SpendData


class EvaluationContext(BaseModel):
    """All data needed to evaluate rules for one account."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    account_id: UUID
    spend_data: SpendData
    campaign_spends: list[CampaignSpendData] = []
    rules: list = []  # list[BudgetRule] — SQLAlchemy instances
    historical_snapshots: list = []  # list[SpendSnapshot]


class RuleResult(BaseModel):
    """Result of evaluating a single rule."""

    rule_id: UUID
    rule_type: RuleType
    result: EvaluationResult
    current_value: Decimal
    threshold_value: Decimal
    consecutive_count: int
    action_required: bool
    details: dict | None = None


class ForecastResult(BaseModel):
    """Output of ForecastService."""

    account_id: UUID
    current_spend_today: Decimal
    hourly_rate: Decimal
    forecast_eod: Decimal
    daily_budget: Decimal
    warning_level: str  # "green", "yellow", "red"
    calculated_at: datetime


class MonitoringResult(BaseModel):
    """Summary of a full monitoring cycle for one account."""

    account_id: UUID
    evaluations: list[RuleResult] = []
    actions_taken: list[dict] = []
    forecast: ForecastResult | None = None
    timestamp: datetime
