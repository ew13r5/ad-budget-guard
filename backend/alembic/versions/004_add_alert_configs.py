"""add alert_configs table and severity column to alerts_log

Revision ID: 004
Revises: 003
Create Date: 2026-03-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "alert_configs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("account_id", sa.Uuid(), sa.ForeignKey("ad_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("destination", sa.String(500), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("severity_filter", sa.String(20), nullable=False, server_default="info"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_alert_configs_account_channel", "alert_configs", ["account_id", "channel"])

    op.add_column(
        "alerts_log",
        sa.Column("severity", sa.String(20), nullable=False, server_default="info"),
    )


def downgrade() -> None:
    op.drop_column("alerts_log", "severity")
    op.drop_index("ix_alert_configs_account_channel", table_name="alert_configs")
    op.drop_table("alert_configs")
