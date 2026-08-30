import uuid
from datetime import date, datetime

from sqlalchemy import String, Numeric, Date, DateTime, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Forecast(Base):
    __tablename__ = "forecasts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)

    metric: Mapped[str] = mapped_column(String(50), nullable=False)  # revenue/profit/expenses/cash_flow
    horizon_months: Mapped[int] = mapped_column(Integer, nullable=False)  # 6 or 12
    period: Mapped[date] = mapped_column(Date, nullable=False)
    predicted_value: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    lower_bound: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    upper_bound: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    model_used: Mapped[str] = mapped_column(String(50), default="prophet")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="forecasts")
