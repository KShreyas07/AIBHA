import uuid

from sqlalchemy.orm import Session

from app.ml.feature_engineering import summarize_features
from app.models.forecast import Forecast
from app.services.data_processing_service import get_company_financial_dataframe
from app.services.prediction_service import get_latest_prediction


def get_dashboard(db: Session, company_id: uuid.UUID) -> dict:
    df = get_company_financial_dataframe(db, company_id)
    if df.empty:
        return {
            "has_data": False,
            "cards": {}, "charts": {}, "pie_charts": {}, "forecast": {}, "health_score_gauge": {},
        }

    features = summarize_features(df)
    prediction = get_latest_prediction(db, company_id)

    cards = {
        "revenue": features["revenue"],
        "profit": features["net_profit"],
        "expenses": features["monthly_expenses"],
        "cash_flow": features["cash_balance"],
        "health_score": float(prediction.health_score) if prediction else None,
        "risk_level": prediction.health_class if prediction else None,
        "prediction": prediction.health_class if prediction else None,
    }

    def trend(col: str) -> list[dict]:
        return [
            {"period": row.period.strftime("%Y-%m-%d"), "value": float(getattr(row, col) or 0)}
            for row in df.itertuples()
        ]

    charts = {
        "revenue_trend": trend("revenue"),
        "expense_trend": [
            {"period": row.period.strftime("%Y-%m-%d"), "value": float((row.operating_expenses or 0) + (row.cogs or 0))}
            for row in df.itertuples()
        ],
        "profit_trend": trend("net_profit"),
        "cash_flow_trend": trend("cash_balance"),
    }

    latest = df.iloc[-1]
    pie_charts = {
        "expenses": {"COGS": float(latest["cogs"]), "Operating Expenses": float(latest["operating_expenses"])},
        "revenue_composition": {
            "Net Profit": float(latest["net_profit"]),
            "COGS": float(latest["cogs"]),
            "Operating Expenses": float(latest["operating_expenses"]),
        },
        "inventory": {
            "In Stock": max(float(latest["inventory_value"]) - float(latest["inventory_sold"]), 0),
            "Sold": float(latest["inventory_sold"]),
        },
    }

    forecasts = db.query(Forecast).filter(Forecast.company_id == company_id).order_by(Forecast.period).all()
    forecast_by_metric: dict[str, list[dict]] = {}
    for f in forecasts:
        forecast_by_metric.setdefault(f.metric, []).append({
            "period": f.period.strftime("%Y-%m-%d"),
            "predicted_value": float(f.predicted_value),
            "lower_bound": float(f.lower_bound) if f.lower_bound is not None else None,
            "upper_bound": float(f.upper_bound) if f.upper_bound is not None else None,
        })

    health_score_gauge = {}
    if prediction:
        health_score_gauge = {
            "score": float(prediction.health_score),
            "label": (prediction.health_score_breakdown or {}).get("label"),
            "breakdown": (prediction.health_score_breakdown or {}).get("points"),
        }

    return {
        "has_data": True,
        "cards": cards,
        "charts": charts,
        "pie_charts": pie_charts,
        "forecast": forecast_by_metric,
        "health_score_gauge": health_score_gauge,
    }
