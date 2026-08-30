import uuid

from sqlalchemy.orm import Session

from app.ml.feature_engineering import summarize_features
from app.models.company import Company
from app.models.recommendation import Recommendation
from app.services.data_processing_service import get_company_financial_dataframe
from app.services.llm_service import generate_recommendations_llm
from app.services.prediction_service import get_latest_prediction

VALID_CATEGORIES = {"expenses", "inventory", "customer", "cash", "marketing", "debt", "revenue"}


def _rule_based_recommendations(features: dict, risks: list[dict]) -> list[dict]:
    recs: list[dict] = []

    if (features.get("operating_margin_pct") or 0) < 10:
        recs.append({
            "category": "expenses", "priority": "high",
            "text": f"Operating margin is {features.get('operating_margin_pct', 0):.1f}%. Reduce operating expenses "
                    f"or renegotiate vendor contracts to rebuild margin.",
            "based_on": "operating_margin_pct",
        })
    if (features.get("inventory_turnover") or 0) < 1:
        recs.append({
            "category": "inventory", "priority": "medium",
            "text": f"Inventory turnover is {features.get('inventory_turnover', 0):.2f}x — increase inventory "
                    f"turnover by running promotions on slow-moving stock and tightening reorder quantities.",
            "based_on": "inventory_turnover",
        })
    if (features.get("customer_growth_rate") or 0) < 2:
        recs.append({
            "category": "customer", "priority": "medium",
            "text": f"Customer growth is {features.get('customer_growth_rate', 0):.1f}% — improve customer "
                    f"retention with loyalty offers and proactive outreach to at-risk accounts.",
            "based_on": "customer_growth_rate",
        })
    if (features.get("cash_ratio") or 0) < 0.5:
        recs.append({
            "category": "cash", "priority": "high",
            "text": f"Cash ratio is {features.get('cash_ratio', 0):.2f}, below the recommended 0.5 buffer — "
                    f"build cash reserves and delay non-essential spend.",
            "based_on": "cash_ratio",
        })
    if (features.get("debt_ratio") or 0) > 0.5:
        recs.append({
            "category": "debt", "priority": "medium",
            "text": f"Debt ratio is {features.get('debt_ratio', 0) * 100:.0f}% of capital — prioritize paying "
                    f"down high-interest debt before taking on new financing.",
            "based_on": "debt_ratio",
        })
    if (features.get("revenue_growth_pct") or 0) < 0:
        recs.append({
            "category": "marketing", "priority": "high",
            "text": f"Revenue growth is {features.get('revenue_growth_pct', 0):.1f}% — increase marketing spend "
                    f"and promotional activity next quarter to reverse the decline.",
            "based_on": "revenue_growth_pct",
        })

    if not recs:
        recs.append({
            "category": "revenue", "priority": "low",
            "text": "Core metrics are healthy. Consider reinvesting profit into growth initiatives such as new "
                    "product lines or expanded marketing.",
            "based_on": "overall financial summary",
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
        record = Recommendation(
            company_id=company.id,
            category=category,
            priority=item.get("priority", "medium"),
            text=item.get("text", ""),
            based_on=item.get("based_on"),
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
