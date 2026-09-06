import uuid

from sqlalchemy.orm import Session

from app.ml.feature_engineering import summarize_features
from app.models.chat_message import ChatMessage
from app.models.company import Company
from app.models.forecast import Forecast
from app.models.recommendation import Recommendation
from app.services.cash_runway_service import get_cash_runway
from app.services.data_processing_service import get_company_financial_dataframe
from app.services.goal_service import list_goals
from app.services.llm_service import answer_chat_llm
from app.services.prediction_service import get_latest_prediction

HISTORY_LIMIT = 20


def _rule_based_answer(context: dict, question: str) -> str:
    q = question.lower()
    metrics = context["metrics"]
    health_score = context.get("health_score")
    health_class = context.get("health_class")
    risks = context.get("risks", [])
    runway = context.get("cash_runway")
    goals = context.get("goals", [])

    if "runway" in q or ("cash" in q and ("last" in q or "left" in q or "run out" in q or "months" in q)):
        if not runway:
            return "I don't have enough cash-flow history yet to estimate runway — process a few months of data first."
        if runway["runway_months"] is None:
            return f"Cash is stable or growing (avg burn ${runway['avg_monthly_burn']:,.0f}/mo) — no runway concern right now."
        return (f"At the current burn rate (${runway['avg_monthly_burn']:,.0f}/mo), you have about "
                f"{runway['runway_months']} months of cash left, around {runway['depletion_date']}.")
    if "goal" in q:
        if not goals:
            return "You haven't set any goals yet — head to the Goals page to set a target and I'll track progress against it."
        lines = []
        for g in goals[:5]:
            status = "achieved" if g["achieved"] else ("on track" if g["on_track"] else "off track" if g["on_track"] is False else "progress unclear")
            lines.append(f"\"{g['label']}\" is {g['progress_pct']:.0f}% there and {status} for {g['target_date']}")
        return "Goal progress — " + "; ".join(lines) + "."
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
            f"Ask me about profit, revenue, expenses, risks, cash runway, or your goals for more detail.")


def _build_context(db: Session, company: Company) -> dict | None:
    df = get_company_financial_dataframe(db, company.id)
    if df.empty:
        return None

    metrics = summarize_features(df)
    prediction = get_latest_prediction(db, company.id)
    forecasts = (
        db.query(Forecast).filter(Forecast.company_id == company.id).order_by(Forecast.period).limit(24).all()
    )
    recommendations = (
        db.query(Recommendation).filter(Recommendation.company_id == company.id).limit(10).all()
    )

    try:
        cash_runway = get_cash_runway(db, company.id)
    except ValueError:
        cash_runway = None

    goals = list_goals(db, company.id)

    return {
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
        "cash_runway": {
            "avg_monthly_burn": cash_runway["avg_monthly_burn"],
            "runway_months": cash_runway["runway_months"],
            "depletion_date": cash_runway["depletion_date"],
            "severity": cash_runway["severity"],
        } if cash_runway else None,
        "goals": [
            {
                "label": g["label"], "metric": g["metric"], "target_value": g["target_value"],
                "target_date": g["target_date"].isoformat(), "progress_pct": g["progress_pct"],
                "achieved": g["achieved"], "on_track": g["on_track"],
            }
            for g in goals
        ],
    }


def get_history(db: Session, company_id: uuid.UUID) -> list[ChatMessage]:
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.company_id == company_id)
        .order_by(ChatMessage.created_at)
        .all()
    )


def clear_history(db: Session, company_id: uuid.UUID) -> None:
    db.query(ChatMessage).filter(ChatMessage.company_id == company_id).delete()
    db.commit()


def answer_question(db: Session, company: Company, question: str) -> str:
    context = _build_context(db, company)
    if context is None:
        return "I don't have any processed financial data for this company yet. Please upload and process data first."

    history = get_history(db, company.id)
    db.add(ChatMessage(company_id=company.id, role="user", content=question))
    db.commit()

    history_payload = [{"role": m.role, "content": m.content} for m in history[-HISTORY_LIMIT:]]
    answer = answer_chat_llm(context, question, history_payload) or _rule_based_answer(context, question)

    db.add(ChatMessage(company_id=company.id, role="assistant", content=answer))
    db.commit()

    return answer
