import uuid
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    industry: Mapped[str] = mapped_column(String(120), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    financial_year: Mapped[str] = mapped_column(String(20), nullable=False)
    business_size: Mapped[str] = mapped_column(String(50), nullable=False)  # micro/small/medium
    employees: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner: Mapped["User"] = relationship(back_populates="companies")
    uploads: Mapped[list["Upload"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    financial_data: Mapped[list["FinancialData"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    forecasts: Mapped[list["Forecast"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    reports: Mapped[list["Report"]] = relationship(back_populates="company", cascade="all, delete-orphan")
