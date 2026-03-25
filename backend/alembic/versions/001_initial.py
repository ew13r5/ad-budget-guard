"""initial

Revision ID: 001
Revises:
Create Date: 2026-03-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Enum types
accountmode = postgresql.ENUM("sandbox", "simulation", "production", name="accountmode", create_type=False)
userrole = postgresql.ENUM("owner", "manager", "viewer", name="userrole", create_type=False)
campaignstatus = postgresql.ENUM("ACTIVE", "PAUSED", name="campaignstatus", create_type=False)
spendsource = postgresql.ENUM("api", "simulator", name="spendsource", create_type=False)
ruletype = postgresql.ENUM("daily_limit", "monthly_limit", "hourly_rate", "anomaly", name="ruletype", create_type=False)
ruleaction = postgresql.ENUM("soft_pause", "hard_pause", name="ruleaction", create_type=False)
evaluationresult = postgresql.ENUM("ok", "warning", "triggered", name="evaluationresult", create_type=False)
alerttype = postgresql.ENUM("budget_warning", "pause", "anomaly", "error", name="alerttype", create_type=False)
alertchannel = postgresql.ENUM("telegram", "email", "in_app", name="alertchannel", create_type=False)


def upgrade() -> None:
    # Create enum types
    accountmode.create(op.get_bind(), checkfirst=True)
    userrole.create(op.get_bind(), checkfirst=True)
    campaignstatus.create(op.get_bind(), checkfirst=True)
    spendsource.create(op.get_bind(), checkfirst=True)
    ruletype.create(op.get_bind(), checkfirst=True)
    ruleaction.create(op.get_bind(), checkfirst=True)
    evaluationresult.create(op.get_bind(), checkfirst=True)
    alerttype.create(op.get_bind(), checkfirst=True)
    alertchannel.create(op.get_bind(), checkfirst=True)

    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("facebook_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("needs_reauth", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("facebook_id"),
    )
    op.create_index("ix_users_facebook_id", "users", ["facebook_id"])

    # ad_accounts
    op.create_table(
        "ad_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("meta_account_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("mode", accountmode, nullable=False, server_default="simulation"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="UTC"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meta_account_id"),
    )

    # user_accounts
    op.create_table(
        "user_accounts",
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", sa.Uuid(), sa.ForeignKey("ad_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", userrole, nullable=False, server_default="viewer"),
        sa.PrimaryKeyConstraint("user_id", "account_id"),
    )

    # campaigns
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), sa.ForeignKey("ad_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("meta_campaign_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", campaignstatus, nullable=False, server_default="ACTIVE"),
        sa.Column("daily_budget", sa.Numeric(12, 2), nullable=True),
        sa.Column("lifetime_budget", sa.Numeric(12, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # spend_snapshots
    op.create_table(
        "spend_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("spend", sa.Numeric(12, 2), nullable=False),
        sa.Column("source", spendsource, nullable=False),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_spend_snapshots_campaign_timestamp", "spend_snapshots", ["campaign_id", "timestamp"])

    # budget_rules
    op.create_table(
        "budget_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), sa.ForeignKey("ad_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=True),
        sa.Column("rule_type", ruletype, nullable=False),
        sa.Column("threshold", sa.Numeric(12, 2), nullable=False),
        sa.Column("action", ruleaction, nullable=False, server_default="soft_pause"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # rule_evaluations
    op.create_table(
        "rule_evaluations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("rule_id", sa.Uuid(), sa.ForeignKey("budget_rules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("result", evaluationresult, nullable=False),
        sa.Column("current_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("threshold_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rule_evaluations_rule_timestamp", "rule_evaluations", ["rule_id", "timestamp"])

    # pause_log
    op.create_table(
        "pause_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule_id", sa.Uuid(), sa.ForeignKey("budget_rules.id", ondelete="SET NULL"), nullable=True),
        sa.Column("paused_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("resumed_at", sa.DateTime(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pause_log_campaign_paused_at", "pause_log", ["campaign_id", "paused_at"])

    # alerts_log
    op.create_table(
        "alerts_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), sa.ForeignKey("ad_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alert_type", alerttype, nullable=False),
        sa.Column("channel", alertchannel, nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("acknowledged", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alerts_log_account_sent_at", "alerts_log", ["account_id", "sent_at"])

    # simulation_states
    op.create_table(
        "simulation_states",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), sa.ForeignKey("ad_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("state_data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("is_running", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("last_tick", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("simulation_states")
    op.drop_table("alerts_log")
    op.drop_table("pause_log")
    op.drop_table("rule_evaluations")
    op.drop_table("budget_rules")
    op.drop_table("spend_snapshots")
    op.drop_table("campaigns")
    op.drop_table("user_accounts")
    op.drop_table("ad_accounts")
    op.drop_table("users")

    for name in ["alertchannel", "alerttype", "evaluationresult", "ruleaction",
                  "ruletype", "spendsource", "campaignstatus", "userrole", "accountmode"]:
        op.execute(f"DROP TYPE IF EXISTS {name}")
