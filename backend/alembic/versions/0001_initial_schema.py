"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "companies",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("industry", sa.String(120), nullable=False),
        sa.Column("country", sa.String(100), nullable=False),
        sa.Column("financial_year", sa.String(20), nullable=False),
        sa.Column("business_size", sa.String(50), nullable=False),
        sa.Column("employees", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "uploads",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", pg.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("data_category", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), server_default="uploaded"),
        sa.Column("error_message", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "financial_data",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", pg.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("upload_id", pg.UUID(as_uuid=True), sa.ForeignKey("uploads.id", ondelete="SET NULL"), nullable=True),
        sa.Column("period", sa.Date, nullable=False),
        sa.Column("revenue", sa.Numeric(18, 2), server_default="0"),
        sa.Column("cogs", sa.Numeric(18, 2), server_default="0"),
        sa.Column("operating_expenses", sa.Numeric(18, 2), server_default="0"),
        sa.Column("net_profit", sa.Numeric(18, 2), server_default="0"),
        sa.Column("cash_balance", sa.Numeric(18, 2), server_default="0"),
        sa.Column("current_assets", sa.Numeric(18, 2), server_default="0"),
        sa.Column("current_liabilities", sa.Numeric(18, 2), server_default="0"),
        sa.Column("total_debt", sa.Numeric(18, 2), server_default="0"),
        sa.Column("total_equity", sa.Numeric(18, 2), server_default="0"),
        sa.Column("inventory_value", sa.Numeric(18, 2), server_default="0"),
        sa.Column("inventory_sold", sa.Numeric(18, 2), server_default="0"),
        sa.Column("customers_count", sa.Numeric(18, 2), server_default="0"),
        sa.Column("revenue_growth_pct", sa.Numeric(9, 4), nullable=True),
        sa.Column("profit_margin_pct", sa.Numeric(9, 4), nullable=True),
        sa.Column("operating_margin_pct", sa.Numeric(9, 4), nullable=True),
        sa.Column("cash_ratio", sa.Numeric(9, 4), nullable=True),
        sa.Column("current_ratio", sa.Numeric(9, 4), nullable=True),
        sa.Column("debt_ratio", sa.Numeric(9, 4), nullable=True),
        sa.Column("inventory_turnover", sa.Numeric(9, 4), nullable=True),
        sa.Column("customer_growth_rate", sa.Numeric(9, 4), nullable=True),
        sa.Column("currency", sa.String(10), server_default="USD"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_financial_data_company_period", "financial_data", ["company_id", "period"])

    op.create_table(
        "forecasts",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", pg.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("metric", sa.String(50), nullable=False),
        sa.Column("horizon_months", sa.Integer, nullable=False),
        sa.Column("period", sa.Date, nullable=False),
        sa.Column("predicted_value", sa.Numeric(18, 2), nullable=False),
        sa.Column("lower_bound", sa.Numeric(18, 2), nullable=True),
        sa.Column("upper_bound", sa.Numeric(18, 2), nullable=True),
        sa.Column("model_used", sa.String(50), server_default="prophet"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "predictions",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", pg.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("health_class", sa.String(20), nullable=False),
        sa.Column("health_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("health_score_breakdown", pg.JSON, server_default="{}"),
        sa.Column("model_used", sa.String(50), server_default="xgboost"),
        sa.Column("model_confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("risks", pg.JSON, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "recommendations",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", pg.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("priority", sa.String(20), server_default="medium"),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("based_on", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "reports",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", pg.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("report_type", sa.String(50), server_default="full"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("recommendations")
    op.drop_table("predictions")
    op.drop_table("forecasts")
    op.drop_index("ix_financial_data_company_period", table_name="financial_data")
    op.drop_table("financial_data")
    op.drop_table("uploads")
    op.drop_table("companies")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
