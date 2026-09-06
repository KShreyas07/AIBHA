import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class GoalCreate(BaseModel):
    label: str = Field(min_length=1, max_length=200)
    metric: str  # revenue/profit/expenses/cash_flow
    target_value: float
    target_date: date


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    label: str
    metric: str
    target_value: float
    target_date: date
    baseline_value: float
    current_value: float
    progress_pct: float
    achieved: bool
    on_track: bool | None = None
    projected_value: float | None = None
    created_at: datetime
