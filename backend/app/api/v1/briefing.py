from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_owned_company
from app.database.session import get_db
from app.models.company import Company
from app.services.agent_service import run_briefing

router = APIRouter()


@router.get("/{company_id}")
def briefing(company: Company = Depends(get_owned_company), db: Session = Depends(get_db)) -> dict:
    try:
        return run_briefing(db, company)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
