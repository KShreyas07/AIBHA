"""Business Health Digital Twin.

Applies hypothetical "what-if" levers (revenue change %, expense change %, debt change
%, one-time cash injection) to the company's latest financial snapshot, then reruns the
exact same ratio formulas (app/ml/feature_engineering.py) and health-score formula
(app/ml/health_score.py) used in production on that hypothetical snapshot. This is
deliberately not a separate model: the twin is only trustworthy if "what happens to my
health score" is computed by the same pipeline that computes the real one, just fed a
different input. Nothing here is persisted — every simulation is a stateless, one-shot
recomputation from the same live data used across the rest of the app.

Revenue growth % and customer growth % are carried through unchanged from the baseline:
they're period-over-period trend metrics, and a single hypothetical snapshot has no new
trend to derive them from.
"""


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def apply_levers(
    latest_row: dict,
    revenue_change_pct: float,
    expenses_change_pct: float,
    debt_change_pct: float,
    cash_injection: float,
) -> dict:
    baseline_operating_profit = latest_row["revenue"] - latest_row["cogs"] - latest_row["operating_expenses"]

    revenue = latest_row["revenue"] * (1 + revenue_change_pct / 100)
    cogs = latest_row["cogs"] * (1 + expenses_change_pct / 100)
    operating_expenses = latest_row["operating_expenses"] * (1 + expenses_change_pct / 100)
    net_profit = revenue - cogs - operating_expenses
    total_debt = max(0.0, latest_row["total_debt"] * (1 + debt_change_pct / 100))

    # Cash moves by the injection plus however much this month's (simplified,
    # revenue-cogs-opex) operating profit improved relative to the baseline.
    profit_delta = net_profit - baseline_operating_profit
    cash_balance = latest_row["cash_balance"] + cash_injection + profit_delta

    return {
        **latest_row,
        "revenue": revenue,
        "cogs": cogs,
        "operating_expenses": operating_expenses,
        "net_profit": net_profit,
        "total_debt": total_debt,
        "cash_balance": cash_balance,
    }


def compute_ratios(row: dict) -> dict:
    """Mirrors the per-row ratio formulas in feature_engineering.engineer_features."""
    revenue = row["revenue"]
    return {
        "revenue": revenue,
        "monthly_expenses": row["operating_expenses"] + row["cogs"],
        "net_profit": row["net_profit"],
        "cash_balance": row["cash_balance"],
        "profit_margin_pct": _safe_div(row["net_profit"], revenue) * 100,
        "operating_margin_pct": _safe_div(revenue - row["operating_expenses"] - row["cogs"], revenue) * 100,
        "cash_ratio": _safe_div(row["cash_balance"], row["current_liabilities"]),
        "current_ratio": _safe_div(row["current_assets"], row["current_liabilities"]),
        "debt_ratio": _safe_div(row["total_debt"], row["total_equity"] + row["total_debt"]),
        "inventory_turnover": _safe_div(row["inventory_sold"], row["inventory_value"]),
    }


def estimate_runway(cash_balance: float, monthly_burn: float) -> float | None:
    if cash_balance <= 0:
        return 0.0
    if monthly_burn <= 0:
        return None
    return round(cash_balance / monthly_burn, 1)
