from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_owned_company
from app.database.session import get_db
from app.models.company import Company
from app.schemas.prediction import ForecastOut, ForecastPoint
from app.services.forecast_service import run_forecast

router = APIRouter()


@router.post("/{company_id}", response_model=ForecastOut)
def forecast(
    metric: str = Query(..., description="revenue | profit | expenses | cash_flow"),
    horizon_months: int = Query(6, ge=6, le=12),
    company: Company = Depends(get_owned_company),
    db: Session = Depends(get_db),
) -> ForecastOut:
    try:
        records = run_forecast(db, company.id, metric, horizon_months)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ForecastOut(
        metric=metric,
        horizon_months=horizon_months,
        model_used=records[0].model_used if records else "prophet",
        points=[
            ForecastPoint(
                period=r.period.strftime("%Y-%m-%d"),
                predicted_value=float(r.predicted_value),
                lower_bound=float(r.lower_bound) if r.lower_bound is not None else None,
                upper_bound=float(r.upper_bound) if r.upper_bound is not None else None,
            )
            for r in records
        ],
    )
