import uuid

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyUpdate


def create_company(db: Session, owner: User, payload: CompanyCreate) -> Company:
    company = Company(owner_id=owner.id, **payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def list_companies(db: Session, owner: User) -> list[Company]:
    return db.query(Company).filter(Company.owner_id == owner.id).order_by(Company.created_at.desc()).all()


def update_company(db: Session, company: Company, payload: CompanyUpdate) -> Company:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    db.commit()
    db.refresh(company)
    return company


def delete_company(db: Session, company: Company) -> None:
    db.delete(company)
    db.commit()
