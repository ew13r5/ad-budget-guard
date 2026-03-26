"""add simulation_log table

Revision ID: 002
Revises: 001
Create Date: 2026-03-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "simulation_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), sa.ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sim_time", sa.DateTime(), nullable=False),
        sa.Column("real_time", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_simulation_log_event_type_real_time", "simulation_log", ["event_type", "real_time"])
    op.create_index("ix_simulation_log_campaign_id_real_time", "simulation_log", ["campaign_id", "real_time"])


def downgrade() -> None:
    op.drop_index("ix_simulation_log_campaign_id_real_time", table_name="simulation_log")
    op.drop_index("ix_simulation_log_event_type_real_time", table_name="simulation_log")
    op.drop_table("simulation_log")
