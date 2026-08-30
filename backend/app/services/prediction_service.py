import uuid

from sqlalchemy.orm import Session

from app.ml.classification import get_classifier
from app.ml.feature_engineering import summarize_features
from app.ml.health_score import calculate_health_score
from app.ml.risk_detection import detect_risks
from app.models.prediction import Prediction
from app.services.data_processing_service import get_company_financial_dataframe


def run_prediction(db: Session, company_id: uuid.UUID) -> Prediction:
    df = get_company_financial_dataframe(db, company_id)
    if df.empty:
        raise ValueError("No processed financial data available for this company yet")

    features = summarize_features(df)
    classifier = get_classifier()
    classification = classifier.predict(features)
    health = calculate_health_score(features)
    risks = detect_risks(df, features)

    if hasattr(classifier, "explain") and classification["health_class"] != "Healthy":
        # Only surface model-driven "reasons" when there's actually elevated risk to
        # explain — for a Healthy company these SHAP contributions are individually
        # tiny and not a meaningful "why", just noise around a near-zero prediction.
        for factor in classifier.explain(features):
            risks.append({
                "type": f"Key Risk Factor: {factor['label']}",
                "severity": "high" if factor["increases_risk"] else "low",
                "description": (
                    f"{factor['label']} is one of the strongest drivers of this "
                    f"risk assessment (SHAP contribution "
                    f"{factor['shap_contribution']:+.3f})."
                ),
            })

    prediction = Prediction(
        company_id=company_id,
        health_class=classification["health_class"],
        health_score=health["score"],
        health_score_breakdown={"label": health["label"], "points": health["breakdown"]},
        model_used=classification["model_used"],
        model_confidence=classification["confidence"],
        risks=risks,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def get_latest_prediction(db: Session, company_id: uuid.UUID) -> Prediction | None:
    return (
        db.query(Prediction)
        .filter(Prediction.company_id == company_id)
        .order_by(Prediction.created_at.desc())
        .first()
    )
