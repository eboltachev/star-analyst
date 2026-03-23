"""add rerun_runs table

Revision ID: 0003_add_rerun_runs
Revises: 0002_add_claims_json_to_reports
Create Date: 2026-03-23
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_add_rerun_runs"
down_revision = "0002_add_claims_json_to_reports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rerun_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("request_id", sa.String(36), sa.ForeignKey("requests.id"), index=True),
        sa.Column("source_ids", sa.JSON),
        sa.Column("status", sa.String(32)),
        sa.Column("created_at", sa.DateTime),
    )


def downgrade() -> None:
    op.drop_table("rerun_runs")
