"""Rule-based Business Health Score (0-100).

Weights: Revenue Growth 20, Profit Margin 20, Cash Flow 20, Inventory 15, Debt 15,
Customer Growth 10.
"""


def _scale(value: float, worst: float, best: float, points: float) -> float:
    """Linearly scale value into [0, points], clamped, where `best` maps to full points
    and `worst` (or below) maps to 0. Works whether best > worst or best < worst."""
    if best == worst:
        return points / 2
    pct = (value - worst) / (best - worst)
    pct = max(0.0, min(1.0, pct))
    return round(pct * points, 2)


def calculate_health_score(features: dict) -> dict:
    revenue_growth = _scale(features.get("revenue_growth_pct", 0) or 0, worst=-20, best=20, points=20)
    profit_margin = _scale(features.get("profit_margin_pct", 0) or 0, worst=-10, best=25, points=20)
    cash_ratio = _scale(features.get("cash_ratio", 0) or 0, worst=0, best=2, points=20)
    inventory_turnover = _scale(features.get("inventory_turnover", 0) or 0, worst=0, best=4, points=15)
    debt_ratio = _scale(features.get("debt_ratio", 0) or 0, worst=1, best=0, points=15)  # lower debt is better
    customer_growth = _scale(features.get("customer_growth_rate", 0) or 0, worst=-10, best=15, points=10)

    breakdown = {
        "revenue_growth": revenue_growth,
        "profit_margin": profit_margin,
        "cash_flow": cash_ratio,
        "inventory": inventory_turnover,
        "debt": debt_ratio,
        "customer_growth": customer_growth,
    }
    total = round(sum(breakdown.values()), 2)

    if total >= 85:
        label = "Excellent"
    elif total >= 70:
        label = "Good"
    elif total >= 50:
        label = "Average"
    elif total >= 30:
        label = "Poor"
    else:
        label = "Critical"

    return {"score": total, "label": label, "breakdown": breakdown}
