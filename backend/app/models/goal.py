import uuid
from datetime import date, datetime

from sqlalchemy import String, Numeric, Date, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Goal(Base):
    """A user-set target for one metric (revenue/profit/expenses/cash_flow) by a
    given date. `baseline_value` is captured at creation time so progress can be
    measured as distance travelled toward the target, not a raw ratio."""

    __tablename__ = "goals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)

    label: Mapped[str] = mapped_column(String(200), nullable=False)
    metric: Mapped[str] = mapped_column(String(50), nullable=False)  # revenue/profit/expenses/cash_flow
    target_value: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    baseline_value: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="goals")
