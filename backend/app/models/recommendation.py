import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Numeric, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)

    category: Mapped[str] = mapped_column(String(50), nullable=False)  # expenses/inventory/customer/cash/marketing/debt
    priority: Mapped[str] = mapped_column(String(20), default="medium")  # low/medium/high
    text: Mapped[str] = mapped_column(Text, nullable=False)
    based_on: Mapped[str] = mapped_column(Text, nullable=True)  # short note on which metrics drove this

    # Action Planner fields: turns advice into a decision-support ranking.
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)  # 0-1
    impact_estimate: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)  # est. annualized $ impact
    difficulty: Mapped[str | None] = mapped_column(String(20), nullable=True)  # low/medium/high

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="recommendations")
