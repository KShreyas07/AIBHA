from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_owned_company
from app.database.session import get_db
from app.ml.feature_engineering import summarize_features
from app.models.company import Company
from app.schemas.financial_data import FinancialDataOut
from app.services.data_processing_service import get_company_financial_dataframe, recompute_engineered_features

router = APIRouter()


@router.post("/{company_id}")
def run_analysis(company: Company = Depends(get_owned_company), db: Session = Depends(get_db)) -> dict:
    """Re-run cleaning + feature engineering across all of a company's uploaded data
    and return a summary of the latest engineered metrics."""
    df = recompute_engineered_features(db, company.id)
    if df.empty:
        raise HTTPException(status_code=400, detail="No processed financial data yet. Upload and wait for processing to complete.")
    return {"company_id": str(company.id), "months_of_data": len(df), "summary": summarize_features(df)}


@router.get("/{company_id}/financial-data", response_model=list[FinancialDataOut])
def get_financial_data(company: Company = Depends(get_owned_company), db: Session = Depends(get_db)):
    from app.models.financial_data import FinancialData

    records = (
        db.query(FinancialData)
        .filter(FinancialData.company_id == company.id)
        .order_by(FinancialData.period)
        .all()
    )
    return [FinancialDataOut.model_validate(r) for r in records]
