import uuid
from datetime import datetime

from sqlalchemy import String, Numeric, DateTime, JSON, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Prediction(Base):
    """Stores classification (health status) + risk detection results for a company
    at a point in time."""

    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)

    health_class: Mapped[str] = mapped_column(String(20), nullable=False)  # Healthy/Warning/Critical
    health_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)  # 0-100
    health_score_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    model_used: Mapped[str] = mapped_column(String(50), default="xgboost")
    model_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)

    risks: Mapped[list] = mapped_column(JSON, default=list)  # list of {type, severity, description}

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="predictions")
