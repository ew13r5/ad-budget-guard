"""Tests for Alembic migrations. Require Docker for PostgreSQL testcontainer."""
import pytest
from tests.conftest import requires_docker


@requires_docker
class TestAlembicMigrations:
    def test_upgrade_head_succeeds(self, sync_engine):
        """Alembic upgrade head already ran in sync_engine fixture."""
        from sqlalchemy import text
        with sync_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_all_10_tables_exist(self, sync_engine):
        """All 10 tables should exist after migration."""
        from sqlalchemy import inspect as sa_inspect
        inspector = sa_inspect(sync_engine)
        tables = set(inspector.get_table_names())
        expected = {
            "users", "ad_accounts", "user_accounts", "campaigns",
            "spend_snapshots", "budget_rules", "rule_evaluations",
            "pause_log", "alerts_log", "simulation_states",
        }
        assert expected.issubset(tables), f"Missing: {expected - tables}"

    def test_all_enum_types_created(self, sync_engine):
        """All 9 PostgreSQL enum types should exist."""
        from sqlalchemy import text
        with sync_engine.connect() as conn:
            result = conn.execute(text(
                "SELECT typname FROM pg_type WHERE typtype = 'e' ORDER BY typname"
            ))
            enums = {row[0] for row in result}
        expected = {
            "accountmode", "campaignstatus", "spendsource",
            "ruletype", "ruleaction", "evaluationresult",
            "alerttype", "alertchannel", "userrole",
        }
        assert expected.issubset(enums), f"Missing: {expected - enums}"

    def test_downgrade_to_base_succeeds(self, alembic_config):
        """Downgrade to base and back up should work."""
        from alembic import command
        command.downgrade(alembic_config, "base")
        command.upgrade(alembic_config, "head")


class TestFactoryImports:
    """Verify factories are importable and produce valid objects."""

    def test_user_factory(self):
        from tests.factories import UserFactory
        user = UserFactory.build()
        assert user.facebook_id is not None
        assert user.name is not None

    def test_ad_account_factory(self):
        from tests.factories import AdAccountFactory
        account = AdAccountFactory.build()
        assert account.meta_account_id.startswith("act_")

    def test_campaign_factory(self):
        from tests.factories import CampaignFactory
        campaign = CampaignFactory.build()
        assert campaign.status.value == "ACTIVE"

    def test_budget_rule_factory(self):
        from tests.factories import BudgetRuleFactory
        rule = BudgetRuleFactory.build()
        assert rule.campaign_id is None  # account-level by default
        assert rule.is_active is True
