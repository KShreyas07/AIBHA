import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.ml.feature_engineering import summarize_features
from app.ml.forecasting import forecast_metric
from app.models.company import Company
from app.models.goal import Goal
from app.services.data_processing_service import get_company_financial_dataframe

VALID_METRICS = ["revenue", "profit", "expenses", "cash_flow"]
LOWER_IS_BETTER = {"expenses"}  # every other tracked metric is "higher is better"

FEATURE_KEY = {
    "revenue": "revenue",
    "profit": "net_profit",
    "expenses": "monthly_expenses",
    "cash_flow": "cash_balance",
}


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def create_goal(db: Session, company: Company, label: str, metric: str, target_value: float, target_date: date) -> Goal:
    if metric not in VALID_METRICS:
        raise ValueError(f"metric must be one of {VALID_METRICS}")

    df = get_company_financial_dataframe(db, company.id)
    if df.empty:
        raise ValueError("No processed financial data available for this company yet")

    features = summarize_features(df)
    baseline_value = features[FEATURE_KEY[metric]]

    goal = Goal(
        company_id=company.id,
        label=label,
        metric=metric,
        target_value=target_value,
        target_date=target_date,
        baseline_value=baseline_value,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def _progress(metric: str, baseline: float, current: float, target: float) -> dict:
    """Progress as distance already travelled from baseline toward target — not a raw
    ratio, since a raw current/target ratio is meaningless for a reduction goal
    (expenses) and misleading for a goal whose baseline is already close to target."""
    lower_is_better = metric in LOWER_IS_BETTER
    achieved = current <= target if lower_is_better else current >= target

    if achieved:
        return {"achieved": True, "progress_pct": 100.0}

    denom = (baseline - target) if lower_is_better else (target - baseline)
    if denom == 0:
        return {"achieved": False, "progress_pct": 0.0}

    numer = (baseline - current) if lower_is_better else (current - baseline)
    return {"achieved": False, "progress_pct": round(_clamp(numer / denom * 100), 1)}


def _on_track(df, metric: str, target_value: float, target_date: date, achieved: bool, current: float) -> tuple[bool | None, float | None]:
    if achieved:
        return True, None

    latest_period = df["period"].max()
    months_ahead = (target_date.year - latest_period.year) * 12 + (target_date.month - latest_period.month)

    if months_ahead < 1:
        # Deadline is this month or already past — no future to project, just report
        # whether it's currently met.
        lower_is_better = metric in LOWER_IS_BETTER
        met = current <= target_value if lower_is_better else current >= target_value
        return met, None

    if months_ahead > 12:
        return None, None  # beyond the forecaster's supported horizon

    try:
        points = forecast_metric(df, metric, months_ahead)
    except ValueError:
        return None, None

    projected_value = points[-1]["predicted_value"]
    lower_is_better = metric in LOWER_IS_BETTER
    on_track = projected_value <= target_value if lower_is_better else projected_value >= target_value
    return on_track, round(projected_value, 2)


def list_goals(db: Session, company_id: uuid.UUID) -> list[dict]:
    df = get_company_financial_dataframe(db, company_id)
    if df.empty:
        return []

    features = summarize_features(df)
    goals = db.query(Goal).filter(Goal.company_id == company_id).order_by(Goal.target_date).all()

    results = []
    for g in goals:
        current_value = features.get(FEATURE_KEY[g.metric], float(g.baseline_value))
        progress = _progress(g.metric, float(g.baseline_value), current_value, float(g.target_value))
        on_track, projected_value = _on_track(
            df, g.metric, float(g.target_value), g.target_date, progress["achieved"], current_value
        )

        results.append({
            "id": g.id,
            "label": g.label,
            "metric": g.metric,
            "target_value": float(g.target_value),
            "target_date": g.target_date,
            "baseline_value": float(g.baseline_value),
            "current_value": round(current_value, 2),
            "progress_pct": progress["progress_pct"],
            "achieved": progress["achieved"],
            "on_track": on_track,
            "projected_value": projected_value,
            "created_at": g.created_at,
        })
    return results


def delete_goal(db: Session, company_id: uuid.UUID, goal_id: uuid.UUID) -> bool:
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.company_id == company_id).first()
    if not goal:
        return False
    db.delete(goal)
    db.commit()
    return True
