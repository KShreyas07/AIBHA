from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_owned_company
from app.database.session import get_db
from app.models.company import Company
from app.schemas.simulation import SimulationRequest
from app.services.simulation_service import run_simulation

router = APIRouter()


@router.post("/{company_id}")
def simulate(
    payload: SimulationRequest,
    company: Company = Depends(get_owned_company),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return run_simulation(
            db,
            company.id,
            payload.revenue_change_pct,
            payload.expenses_change_pct,
            payload.debt_change_pct,
            payload.cash_injection,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
