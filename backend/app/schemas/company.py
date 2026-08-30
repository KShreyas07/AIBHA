import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CompanyBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    industry: str
    country: str
    financial_year: str
    business_size: str
    employees: int = 0


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = None
    industry: str | None = None
    country: str | None = None
    financial_year: str | None = None
    business_size: str | None = None
    employees: int | None = None


class CompanyOut(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
