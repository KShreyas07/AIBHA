from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_owned_company
from app.database.session import get_db
from app.models.company import Company
from app.schemas.prediction import PredictionOut
from app.services.prediction_service import run_prediction, get_latest_prediction

router = APIRouter()


@router.post("/{company_id}", response_model=PredictionOut)
def predict_health(company: Company = Depends(get_owned_company), db: Session = Depends(get_db)) -> PredictionOut:
    try:
        prediction = run_prediction(db, company.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return PredictionOut.model_validate(prediction)


@router.get("/{company_id}", response_model=PredictionOut)
def latest_prediction(company: Company = Depends(get_owned_company), db: Session = Depends(get_db)) -> PredictionOut:
    prediction = get_latest_prediction(db, company.id)
    if not prediction:
        raise HTTPException(status_code=404, detail="No prediction yet. Run POST /api/predict/{company_id} first.")
    return PredictionOut.model_validate(prediction)
