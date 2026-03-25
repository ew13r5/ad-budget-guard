"""Tests for database models and SQLAlchemy configuration."""
import enum
from uuid import UUID

import pytest
from sqlalchemy import inspect


class TestURLConversion:
    def test_to_async_url(self):
        from app.database import _to_async_url
        assert _to_async_url("postgresql://u:p@h/d") == "postgresql+asyncpg://u:p@h/d"
        assert _to_async_url("postgresql+psycopg2://u:p@h/d") == "postgresql+asyncpg://u:p@h/d"

    def test_to_sync_url(self):
        from app.database import _to_sync_url
        assert _to_sync_url("postgresql://u:p@h/d") == "postgresql+psycopg2://u:p@h/d"
        assert _to_sync_url("postgresql+asyncpg://u:p@h/d") == "postgresql+psycopg2://u:p@h/d"


class TestModelImports:
    def test_all_models_importable(self):
        from app.models import (
            Base, User, AdAccount, user_accounts, Campaign,
            SpendSnapshot, BudgetRule, RuleEvaluation,
            PauseLog, AlertLog, SimulationState,
        )
        assert Base is not None
        assert User.__tablename__ == "users"
        assert AdAccount.__tablename__ == "ad_accounts"
        assert Campaign.__tablename__ == "campaigns"
        assert SpendSnapshot.__tablename__ == "spend_snapshots"
        assert BudgetRule.__tablename__ == "budget_rules"
        assert RuleEvaluation.__tablename__ == "rule_evaluations"
        assert PauseLog.__tablename__ == "pause_log"
        assert AlertLog.__tablename__ == "alerts_log"
        assert SimulationState.__tablename__ == "simulation_states"

    def test_base_has_10_tables(self):
        from app.models import Base
        tables = Base.metadata.tables
        expected = {
            "users", "ad_accounts", "user_accounts", "campaigns",
            "spend_snapshots", "budget_rules", "rule_evaluations",
            "pause_log", "alerts_log", "simulation_states",
        }
        assert expected == set(tables.keys())


class TestEnums:
    def test_account_mode_values(self):
        from app.models import AccountMode
        assert set(e.value for e in AccountMode) == {"sandbox", "simulation", "production"}

    def test_campaign_status_values(self):
        from app.models import CampaignStatus
        assert set(e.value for e in CampaignStatus) == {"ACTIVE", "PAUSED"}

    def test_spend_source_values(self):
        from app.models import SpendSource
        assert set(e.value for e in SpendSource) == {"api", "simulator"}

    def test_rule_type_values(self):
        from app.models import RuleType
        assert set(e.value for e in RuleType) == {
            "daily_limit", "monthly_limit", "hourly_rate", "anomaly"
        }

    def test_rule_action_values(self):
        from app.models import RuleAction
        assert set(e.value for e in RuleAction) == {"soft_pause", "hard_pause"}

    def test_evaluation_result_values(self):
        from app.models import EvaluationResult
        assert set(e.value for e in EvaluationResult) == {"ok", "warning", "triggered"}

    def test_alert_type_values(self):
        from app.models import AlertType
        assert set(e.value for e in AlertType) == {
            "budget_warning", "pause", "anomaly", "error"
        }

    def test_alert_channel_values(self):
        from app.models import AlertChannel
        assert set(e.value for e in AlertChannel) == {"telegram", "email", "in_app"}

    def test_user_role_values(self):
        from app.models import UserRole
        assert set(e.value for e in UserRole) == {"owner", "manager", "viewer"}


class TestModelColumns:
    def test_user_has_facebook_id_unique(self):
        from app.models import User
        mapper = inspect(User)
        col = mapper.columns["facebook_id"]
        assert col.unique is True

    def test_ad_account_has_mode(self):
        from app.models import AdAccount
        mapper = inspect(AdAccount)
        assert "mode" in mapper.columns

    def test_campaign_has_account_fk(self):
        from app.models import Campaign
        mapper = inspect(Campaign)
        fks = [fk.target_fullname for col in mapper.columns for fk in col.foreign_keys]
        assert "ad_accounts.id" in fks

    def test_spend_snapshot_has_campaign_fk(self):
        from app.models import SpendSnapshot
        mapper = inspect(SpendSnapshot)
        fks = [fk.target_fullname for col in mapper.columns for fk in col.foreign_keys]
        assert "campaigns.id" in fks

    def test_budget_rule_campaign_nullable(self):
        from app.models import BudgetRule
        mapper = inspect(BudgetRule)
        assert mapper.columns["campaign_id"].nullable is True

    def test_user_accounts_has_role(self):
        from app.models import user_accounts
        col_names = [c.name for c in user_accounts.columns]
        assert "role" in col_names


class TestIndexes:
    def test_spend_snapshot_composite_index(self):
        from app.models import SpendSnapshot
        indexes = {idx.name for idx in SpendSnapshot.__table__.indexes}
        assert "ix_spend_snapshots_campaign_timestamp" in indexes

    def test_rule_evaluation_composite_index(self):
        from app.models import RuleEvaluation
        indexes = {idx.name for idx in RuleEvaluation.__table__.indexes}
        assert "ix_rule_evaluations_rule_timestamp" in indexes

    def test_alert_log_composite_index(self):
        from app.models import AlertLog
        indexes = {idx.name for idx in AlertLog.__table__.indexes}
        assert "ix_alerts_log_account_sent_at" in indexes

    def test_pause_log_composite_index(self):
        from app.models import PauseLog
        indexes = {idx.name for idx in PauseLog.__table__.indexes}
        assert "ix_pause_log_campaign_paused_at" in indexes
