import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RiskItem(BaseModel):
    type: str
    severity: str  # low/medium/high
    description: str


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    health_class: str
    health_score: float
    health_score_breakdown: dict
    model_used: str
    model_confidence: float | None = None
    risks: list[dict]
    created_at: datetime


class ForecastPoint(BaseModel):
    period: str
    predicted_value: float
    lower_bound: float | None = None
    upper_bound: float | None = None


class ForecastOut(BaseModel):
    metric: str
    horizon_months: int
    model_used: str
    points: list[ForecastPoint]


class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category: str
    priority: str
    text: str
    based_on: str | None = None
    created_at: datetime


class ChatRequest(BaseModel):
    company_id: uuid.UUID
    message: str


class ChatResponse(BaseModel):
    answer: str
