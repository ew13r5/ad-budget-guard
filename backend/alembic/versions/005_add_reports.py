"""add reports table

Revision ID: 005
Revises: 004
Create Date: 2026-03-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("account_id", sa.Uuid(), sa.ForeignKey("ad_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("report_type", sa.Enum("daily", "weekly", "monthly", name="reporttype"), nullable=False),
        sa.Column("report_format", sa.Enum("pdf", "sheets", name="reportformat"), nullable=False),
        sa.Column("date_from", sa.DateTime(), nullable=False),
        sa.Column("date_to", sa.DateTime(), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=True),
        sa.Column("sheets_url", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_reports_account_type", "reports", ["account_id", "report_type"])


def downgrade() -> None:
    op.drop_index("ix_reports_account_type", table_name="reports")
    op.drop_table("reports")
    op.execute("DROP TYPE IF EXISTS reporttype")
    op.execute("DROP TYPE IF EXISTS reportformat")
