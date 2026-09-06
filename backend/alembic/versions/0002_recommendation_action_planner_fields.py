"""add action planner fields to recommendations

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-31

"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("recommendations", sa.Column("confidence", sa.Numeric(5, 4), nullable=True))
    op.add_column("recommendations", sa.Column("impact_estimate", sa.Numeric(14, 2), nullable=True))
    op.add_column("recommendations", sa.Column("difficulty", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("recommendations", "difficulty")
    op.drop_column("recommendations", "impact_estimate")
    op.drop_column("recommendations", "confidence")
