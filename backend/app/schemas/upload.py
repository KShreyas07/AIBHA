import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UploadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    filename: str
    file_type: str
    data_category: str
    status: str
    error_message: str | None = None
    created_at: datetime


DATA_CATEGORIES = [
    "income_statement",
    "balance_sheet",
    "cash_flow_statement",
    "sales_report",
    "expense_report",
    "inventory_report",
    "customer_data",
]
