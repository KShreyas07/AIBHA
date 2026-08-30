import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict


class FinancialDataOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    period: date
    revenue: float
    cogs: float
    operating_expenses: float
    net_profit: float
    cash_balance: float
    current_assets: float
    current_liabilities: float
    total_debt: float
    total_equity: float
    inventory_value: float
    inventory_sold: float
    customers_count: float
    revenue_growth_pct: float | None = None
    profit_margin_pct: float | None = None
    operating_margin_pct: float | None = None
    cash_ratio: float | None = None
    current_ratio: float | None = None
    debt_ratio: float | None = None
    inventory_turnover: float | None = None
    customer_growth_rate: float | None = None
    currency: str
