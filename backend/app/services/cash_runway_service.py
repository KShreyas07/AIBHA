import uuid

import pandas as pd
from sqlalchemy.orm import Session

from app.ml.feature_engineering import summarize_features
from app.ml.forecasting import forecast_metric
from app.services.data_processing_service import get_company_financial_dataframe

BURN_TRAILING_MONTHS = 3
CRITICAL_MONTHS = 3
WARNING_MONTHS = 6


def get_cash_runway(db: Session, company_id: uuid.UUID) -> dict:
    """Estimate how many months of cash the company has left, from its own trailing
    burn rate, cross-checked against the validated cash-flow forecaster (Study E
    auto-select ARIMA/Prophet/linear) for a second, model-driven depletion estimate."""
    df = get_company_financial_dataframe(db, company_id)
    if df.empty:
        raise ValueError("No processed financial data available for this company yet")

    features = summarize_features(df)
    current_cash = features["cash_balance"]

    trailing_changes = df["cash_balance"].tail(BURN_TRAILING_MONTHS + 1).diff().dropna()
    avg_monthly_change = float(trailing_changes.mean()) if not trailing_changes.empty else 0.0
    burn_rate = max(0.0, -avg_monthly_change)  # only counts as "burn" when cash is actually shrinking

    latest_period = df["period"].max()

    if current_cash <= 0:
        severity = "critical"
        runway_months = 0.0
    elif burn_rate <= 0:
        severity = "healthy"
        runway_months = None
    else:
        runway_months = round(current_cash / burn_rate, 1)
        if runway_months <= CRITICAL_MONTHS:
            severity = "critical"
        elif runway_months <= WARNING_MONTHS:
            severity = "warning"
        else:
            severity = "healthy"

    depletion_date = None
    if runway_months is not None:
        depletion_date = (latest_period + pd.DateOffset(months=int(runway_months))).strftime("%Y-%m-%d")

    forecast_points: list[dict] = []
    forecast_depletion_months = None
    try:
        forecast_points = forecast_metric(df, "cash_flow", 12)
        for i, point in enumerate(forecast_points, start=1):
            if point["predicted_value"] <= 0:
                forecast_depletion_months = i
                break
    except ValueError:
        pass  # not enough history to forecast yet — burn-rate estimate above still stands

    return {
        "current_cash": round(current_cash, 2),
        "avg_monthly_burn": round(burn_rate, 2),
        "runway_months": runway_months,
        "depletion_date": depletion_date,
        "severity": severity,
        "forecast_points": forecast_points,
        "forecast_depletion_months": forecast_depletion_months,
    }
