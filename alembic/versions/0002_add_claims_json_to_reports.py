"""add claims_json to reports

Revision ID: 0002_add_claims_json_to_reports
Revises: 0001_initial
Create Date: 2026-03-23
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_claims_json_to_reports"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("reports") as batch_op:
        batch_op.add_column(sa.Column("claims_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("reports") as batch_op:
        batch_op.drop_column("claims_json")
