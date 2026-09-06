import uuid

from sqlalchemy.orm import Session

from app.ml.feature_engineering import summarize_features
from app.models.company import Company
from app.models.recommendation import Recommendation
from app.services.data_processing_service import get_company_financial_dataframe
from app.services.llm_service import generate_recommendations_llm
from app.services.prediction_service import get_latest_prediction

VALID_CATEGORIES = {"expenses", "inventory", "customer", "cash", "marketing", "debt", "revenue"}


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _estimate_impact(fraction: float, annual_base: float) -> float:
    """Order-of-magnitude estimate, not a precise forecast: `fraction` of an annualized
    base figure (revenue or expenses), scaled by how far a metric sits into its unhealthy
    range. Intentionally conservative — the UI presents this as an estimate."""
    return round(_clamp(fraction) * annual_base, 2)


def _rule_based_recommendations(features: dict, risks: list[dict]) -> list[dict]:
    recs: list[dict] = []
    annual_revenue = (features.get("revenue") or 0) * 12
    annual_expenses = (features.get("monthly_expenses") or 0) * 12

    operating_margin = features.get("operating_margin_pct") or 0
    if operating_margin < 10:
        gap = _clamp((10 - operating_margin) / 10)
        recs.append({
            "category": "expenses", "priority": "high",
            "text": f"Operating margin is {operating_margin:.1f}%. Reduce operating expenses "
                    f"or renegotiate vendor contracts to rebuild margin.",
            "based_on": "operating_margin_pct",
            "confidence": round(_clamp(0.4 + gap * 0.5), 4),
            "impact_estimate": _estimate_impact(gap * 0.15, annual_expenses),
            "difficulty": "medium",
        })

    inventory_turnover = features.get("inventory_turnover") or 0
    if inventory_turnover < 1:
        gap = _clamp(1 - inventory_turnover)
        recs.append({
            "category": "inventory", "priority": "medium",
            "text": f"Inventory turnover is {inventory_turnover:.2f}x — increase inventory "
                    f"turnover by running promotions on slow-moving stock and tightening reorder quantities.",
            "based_on": "inventory_turnover",
            "confidence": round(_clamp(0.35 + gap * 0.3), 4),
            "impact_estimate": _estimate_impact(gap * 0.08, annual_expenses),
            "difficulty": "medium",
        })

    customer_growth = features.get("customer_growth_rate") or 0
    if customer_growth < 2:
        gap = _clamp((2 - customer_growth) / 10)
        recs.append({
            "category": "customer", "priority": "medium",
            "text": f"Customer growth is {customer_growth:.1f}% — improve customer "
                    f"retention with loyalty offers and proactive outreach to at-risk accounts.",
            "based_on": "customer_growth_rate",
            "confidence": round(_clamp(0.3 + gap * 0.3), 4),
            "impact_estimate": _estimate_impact(gap * 0.05, annual_revenue),
            "difficulty": "high",
        })

    cash_ratio = features.get("cash_ratio") or 0
    if cash_ratio < 0.5:
        gap = _clamp((0.5 - cash_ratio) / 0.5)
        recs.append({
            "category": "cash", "priority": "high",
            "text": f"Cash ratio is {cash_ratio:.2f}, below the recommended 0.5 buffer — "
                    f"build cash reserves and delay non-essential spend.",
            "based_on": "cash_ratio",
            "confidence": round(_clamp(0.5 + gap * 0.4), 4),
            "impact_estimate": _estimate_impact(gap * 0.10, annual_expenses),
            "difficulty": "low",
        })

    debt_ratio = features.get("debt_ratio") or 0
    if debt_ratio > 0.5:
        gap = _clamp((debt_ratio - 0.5) / 0.5)
        recs.append({
            "category": "debt", "priority": "medium",
            "text": f"Debt ratio is {debt_ratio * 100:.0f}% of capital — prioritize paying "
                    f"down high-interest debt before taking on new financing.",
            "based_on": "debt_ratio",
            "confidence": round(_clamp(0.45 + gap * 0.35), 4),
            "impact_estimate": _estimate_impact(gap * 0.06, annual_expenses),
            "difficulty": "high",
        })

    revenue_growth = features.get("revenue_growth_pct") or 0
    if revenue_growth < 0:
        gap = _clamp(-revenue_growth / 20)
        recs.append({
            "category": "marketing", "priority": "high",
            "text": f"Revenue growth is {revenue_growth:.1f}% — increase marketing spend "
                    f"and promotional activity next quarter to reverse the decline.",
            "based_on": "revenue_growth_pct",
            "confidence": round(_clamp(0.3 + gap * 0.3), 4),
            "impact_estimate": _estimate_impact(gap * 0.08, annual_revenue),
            "difficulty": "medium",
        })

    if not recs:
        recs.append({
            "category": "revenue", "priority": "low",
            "text": "Core metrics are healthy. Consider reinvesting profit into growth initiatives such as new "
                    "product lines or expanded marketing.",
            "based_on": "overall financial summary",
            "confidence": 0.5,
            "impact_estimate": None,
            "difficulty": "low",
        })
    return recs


def generate_recommendations(db: Session, company: Company) -> list[Recommendation]:
    df = get_company_financial_dataframe(db, company.id)
    if df.empty:
        raise ValueError("No processed financial data available for this company yet")

    features = summarize_features(df)
    prediction = get_latest_prediction(db, company.id)
    risks = prediction.risks if prediction else []

    context = {
        "company": {"name": company.name, "industry": company.industry, "business_size": company.business_size},
        "metrics": features,
        "health_score": float(prediction.health_score) if prediction else None,
        "health_class": prediction.health_class if prediction else None,
        "risks": risks,
    }

    items = generate_recommendations_llm(context) or _rule_based_recommendations(features, risks)

    db.query(Recommendation).filter(Recommendation.company_id == company.id).delete()
    records = []
    for item in items:
        category = item.get("category") if item.get("category") in VALID_CATEGORIES else "revenue"
        confidence = item.get("confidence")
        difficulty = item.get("difficulty")
        record = Recommendation(
            company_id=company.id,
            category=category,
            priority=item.get("priority", "medium"),
            text=item.get("text", ""),
            based_on=item.get("based_on"),
            confidence=round(_clamp(float(confidence)), 4) if confidence is not None else None,
            impact_estimate=item.get("impact_estimate"),
            difficulty=difficulty if difficulty in {"low", "medium", "high"} else None,
        )
        db.add(record)
        records.append(record)

    db.commit()
    for r in records:
        db.refresh(r)
    return records


def list_recommendations(db: Session, company_id: uuid.UUID) -> list[Recommendation]:
    return (
        db.query(Recommendation)
        .filter(Recommendation.company_id == company_id)
        .order_by(Recommendation.created_at.desc())
        .all()
    )
