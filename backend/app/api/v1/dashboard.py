from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_owned_company
from app.database.session import get_db
from app.models.company import Company
from app.services.benchmark_service import get_benchmark
from app.services.dashboard_service import get_dashboard

router = APIRouter()


@router.get("/{company_id}")
def dashboard(company: Company = Depends(get_owned_company), db: Session = Depends(get_db)) -> dict:
    return get_dashboard(db, company.id)


@router.get("/{company_id}/benchmark")
def benchmark(company: Company = Depends(get_owned_company), db: Session = Depends(get_db)) -> dict:
    try:
        return get_benchmark(db, company)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
