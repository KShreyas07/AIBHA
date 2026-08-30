from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_owned_company
from app.database.session import get_db
from app.models.company import Company
from app.schemas.prediction import RecommendationOut
from app.services.recommendation_service import generate_recommendations, list_recommendations

router = APIRouter()


@router.post("/{company_id}", response_model=list[RecommendationOut])
def generate(company: Company = Depends(get_owned_company), db: Session = Depends(get_db)) -> list[RecommendationOut]:
    try:
        recs = generate_recommendations(db, company)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [RecommendationOut.model_validate(r) for r in recs]


@router.get("/{company_id}", response_model=list[RecommendationOut])
def list_for_company(company: Company = Depends(get_owned_company), db: Session = Depends(get_db)) -> list[RecommendationOut]:
    return [RecommendationOut.model_validate(r) for r in list_recommendations(db, company.id)]
