import uuid
from datetime import date, datetime

from sqlalchemy import String, Numeric, Date, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class FinancialData(Base):
    """Normalized monthly financial + operational record per company, produced by the
    data processing engine after cleaning and feature engineering."""

    __tablename__ = "financial_data"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    upload_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("uploads.id", ondelete="SET NULL"), nullable=True)

    period: Mapped[date] = mapped_column(Date, nullable=False)  # first day of month

    # Raw core figures
    revenue: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    cogs: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    operating_expenses: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    net_profit: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    cash_balance: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    current_assets: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    current_liabilities: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    total_debt: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    total_equity: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    inventory_value: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    inventory_sold: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    customers_count: Mapped[float] = mapped_column(Numeric(18, 2), default=0)

    # Engineered features
    revenue_growth_pct: Mapped[float | None] = mapped_column(Numeric(9, 4), nullable=True)
    profit_margin_pct: Mapped[float | None] = mapped_column(Numeric(9, 4), nullable=True)
    operating_margin_pct: Mapped[float | None] = mapped_column(Numeric(9, 4), nullable=True)
    cash_ratio: Mapped[float | None] = mapped_column(Numeric(9, 4), nullable=True)
    current_ratio: Mapped[float | None] = mapped_column(Numeric(9, 4), nullable=True)
    debt_ratio: Mapped[float | None] = mapped_column(Numeric(9, 4), nullable=True)
    inventory_turnover: Mapped[float | None] = mapped_column(Numeric(9, 4), nullable=True)
    customer_growth_rate: Mapped[float | None] = mapped_column(Numeric(9, 4), nullable=True)

    currency: Mapped[str] = mapped_column(String(10), default="USD")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="financial_data")
