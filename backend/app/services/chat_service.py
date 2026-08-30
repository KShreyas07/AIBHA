from sqlalchemy.orm import Session

from app.ml.feature_engineering import summarize_features
from app.models.company import Company
from app.models.forecast import Forecast
from app.models.recommendation import Recommendation
from app.services.data_processing_service import get_company_financial_dataframe
from app.services.llm_service import answer_chat_llm
from app.services.prediction_service import get_latest_prediction


def _rule_based_answer(context: dict, question: str) -> str:
    q = question.lower()
    metrics = context["metrics"]
    health_score = context.get("health_score")
    health_class = context.get("health_class")
    risks = context.get("risks", [])

    if "health score" in q or "health" in q:
        breakdown = ", ".join(f"{k}: {v}" for k, v in (context.get("health_breakdown") or {}).items())
        return (f"Your Business Health Score is {health_score}/100 ({health_class}). "
                f"Breakdown — {breakdown or 'not yet calculated'}.")
    if "profit" in q:
        return (f"Latest profit margin is {metrics.get('profit_margin_pct', 0):.1f}% with net profit of "
                f"{metrics.get('net_profit', 0):,.2f}. To increase profit, focus on the expense and pricing "
                f"recommendations on your dashboard.")
    if "revenue" in q or "predict" in q or "forecast" in q:
        return (f"Latest revenue is {metrics.get('revenue', 0):,.2f} with {metrics.get('revenue_growth_pct', 0):.1f}% "
                f"month-over-month growth. Check the Forecast page for the 6/12-month projection.")
    if "expense" in q or "cost" in q:
        return (f"Monthly expenses are currently {metrics.get('monthly_expenses', 0):,.2f}, giving an operating "
                f"margin of {metrics.get('operating_margin_pct', 0):.1f}%.")
    if "risk" in q:
        if not risks:
            return "No significant risks detected in your latest data."
        return "Detected risks: " + "; ".join(f"{r['type']} ({r['severity']})" for r in risks)

    return (f"Based on your latest data: revenue {metrics.get('revenue', 0):,.2f}, profit margin "
            f"{metrics.get('profit_margin_pct', 0):.1f}%, health score {health_score}/100 ({health_class}). "
            f"Ask me about profit, revenue, expenses, or risks for more detail.")


def answer_question(db: Session, company: Company, question: str) -> str:
    df = get_company_financial_dataframe(db, company.id)
    if df.empty:
        return "I don't have any processed financial data for this company yet. Please upload and process data first."

    metrics = summarize_features(df)
    prediction = get_latest_prediction(db, company.id)
    forecasts = (
        db.query(Forecast).filter(Forecast.company_id == company.id).order_by(Forecast.period).limit(24).all()
    )
    recommendations = (
        db.query(Recommendation).filter(Recommendation.company_id == company.id).limit(10).all()
    )

    context = {
        "company": {"name": company.name, "industry": company.industry},
        "metrics": metrics,
        "health_score": float(prediction.health_score) if prediction else None,
        "health_class": prediction.health_class if prediction else None,
        "health_breakdown": (prediction.health_score_breakdown or {}).get("points") if prediction else None,
        "risks": prediction.risks if prediction else [],
        "forecasts": [
            {"metric": f.metric, "period": f.period.isoformat(), "predicted_value": float(f.predicted_value)}
            for f in forecasts
        ],
        "recommendations": [r.text for r in recommendations],
    }

    answer = answer_chat_llm(context, question)
    return answer or _rule_based_answer(context, question)
