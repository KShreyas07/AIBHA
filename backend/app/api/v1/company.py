import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_company
from app.database.session import get_db
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyOut
from app.services import company_service

router = APIRouter()


@router.post("", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> CompanyOut:
    company = company_service.create_company(db, current_user, payload)
    return CompanyOut.model_validate(company)


@router.get("", response_model=list[CompanyOut])
def list_companies(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[CompanyOut]:
    companies = company_service.list_companies(db, current_user)
    return [CompanyOut.model_validate(c) for c in companies]


@router.get("/{company_id}", response_model=CompanyOut)
def get_company(company: Company = Depends(get_owned_company)) -> CompanyOut:
    return CompanyOut.model_validate(company)


@router.put("/{company_id}", response_model=CompanyOut)
def update_company(payload: CompanyUpdate, company: Company = Depends(get_owned_company), db: Session = Depends(get_db)) -> CompanyOut:
    updated = company_service.update_company(db, company, payload)
    return CompanyOut.model_validate(updated)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company: Company = Depends(get_owned_company), db: Session = Depends(get_db)) -> None:
    company_service.delete_company(db, company)
