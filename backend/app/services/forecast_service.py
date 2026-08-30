import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.ml.forecasting import forecast_metric
from app.models.forecast import Forecast
from app.services.data_processing_service import get_company_financial_dataframe

VALID_METRICS = ["revenue", "profit", "expenses", "cash_flow"]


def run_forecast(db: Session, company_id: uuid.UUID, metric: str, horizon_months: int) -> list[Forecast]:
    if metric not in VALID_METRICS:
        raise ValueError(f"metric must be one of {VALID_METRICS}")
    if horizon_months not in (6, 12):
        raise ValueError("horizon_months must be 6 or 12")

    df = get_company_financial_dataframe(db, company_id)
    if df.empty:
        raise ValueError("No processed financial data available for this company yet")

    points = forecast_metric(df, metric, horizon_months)

    # Replace any prior forecast for this metric/horizon so results stay current.
    db.query(Forecast).filter(
        Forecast.company_id == company_id, Forecast.metric == metric, Forecast.horizon_months == horizon_months
    ).delete()

    records = []
    for point in points:
        record = Forecast(
            company_id=company_id,
            metric=metric,
            horizon_months=horizon_months,
            period=datetime.strptime(point["period"], "%Y-%m-%d").date(),
            predicted_value=point["predicted_value"],
            lower_bound=point["lower_bound"],
            upper_bound=point["upper_bound"],
            model_used=point["model_used"],
        )
        db.add(record)
        records.append(record)

    db.commit()
    for r in records:
        db.refresh(r)
    return records
