import uuid

from sqlalchemy.orm import Session

from app.ml.feature_engineering import summarize_features
from app.ml.health_score import calculate_health_score
from app.ml.simulation import apply_levers, compute_ratios, estimate_runway
from app.services.cash_runway_service import BURN_TRAILING_MONTHS
from app.services.data_processing_service import get_company_financial_dataframe

LEVER_BOUNDS = {
    "revenue_change_pct": (-50.0, 100.0),
    "expenses_change_pct": (-50.0, 100.0),
    "debt_change_pct": (-100.0, 100.0),
}


def _burn_rate(df) -> float:
    trailing = df["cash_balance"].tail(BURN_TRAILING_MONTHS + 1).diff().dropna()
    return max(0.0, -float(trailing.mean())) if not trailing.empty else 0.0


def run_simulation(
    db: Session,
    company_id: uuid.UUID,
    revenue_change_pct: float,
    expenses_change_pct: float,
    debt_change_pct: float,
    cash_injection: float,
) -> dict:
    for name, value in [
        ("revenue_change_pct", revenue_change_pct),
        ("expenses_change_pct", expenses_change_pct),
        ("debt_change_pct", debt_change_pct),
    ]:
        lo, hi = LEVER_BOUNDS[name]
        if not (lo <= value <= hi):
            raise ValueError(f"{name} must be between {lo} and {hi}")

    df = get_company_financial_dataframe(db, company_id)
    if df.empty:
        raise ValueError("No processed financial data available for this company yet")

    baseline_features = summarize_features(df)
    baseline_health = calculate_health_score(baseline_features)
    baseline_burn = _burn_rate(df)
    baseline_runway = estimate_runway(baseline_features["cash_balance"], baseline_burn)

    latest_row = df.iloc[-1].to_dict()
    simulated_row = apply_levers(latest_row, revenue_change_pct, expenses_change_pct, debt_change_pct, cash_injection)
    simulated_features = compute_ratios(simulated_row)
    # Trend metrics carry through unchanged — see app/ml/simulation.py docstring.
    simulated_features["revenue_growth_pct"] = baseline_features["revenue_growth_pct"]
    simulated_features["customer_growth_rate"] = baseline_features["customer_growth_rate"]
    simulated_health = calculate_health_score(simulated_features)

    baseline_operating_profit = latest_row["revenue"] - latest_row["cogs"] - latest_row["operating_expenses"]
    profit_delta = simulated_row["net_profit"] - baseline_operating_profit
    simulated_burn = max(0.0, baseline_burn - profit_delta)
    simulated_runway = estimate_runway(simulated_features["cash_balance"], simulated_burn)

    return {
        "levers": {
            "revenue_change_pct": revenue_change_pct,
            "expenses_change_pct": expenses_change_pct,
            "debt_change_pct": debt_change_pct,
            "cash_injection": cash_injection,
        },
        "baseline": {
            "features": baseline_features,
            "health_score": baseline_health["score"],
            "health_label": baseline_health["label"],
            "health_breakdown": baseline_health["breakdown"],
            "avg_monthly_burn": round(baseline_burn, 2),
            "runway_months": baseline_runway,
        },
        "simulated": {
            "features": simulated_features,
            "health_score": simulated_health["score"],
            "health_label": simulated_health["label"],
            "health_breakdown": simulated_health["breakdown"],
            "avg_monthly_burn": round(simulated_burn, 2),
            "runway_months": simulated_runway,
        },
    }
