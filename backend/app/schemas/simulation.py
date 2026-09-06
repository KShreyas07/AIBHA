from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    revenue_change_pct: float = Field(0.0, ge=-50, le=100)
    expenses_change_pct: float = Field(0.0, ge=-50, le=100)
    debt_change_pct: float = Field(0.0, ge=-100, le=100)
    cash_injection: float = 0.0
