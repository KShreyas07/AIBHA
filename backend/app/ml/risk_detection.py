"""Risk detection: rule-based checks for known risk categories plus Isolation Forest
outlier detection to catch anomalies the fixed rules don't anticipate."""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


def _rule_based_risks(latest: pd.Series, features: dict) -> list[dict]:
    risks: list[dict] = []

    revenue_growth = features.get("revenue_growth_pct") or 0
    if revenue_growth < -10:
        risks.append({"type": "Revenue Drop", "severity": "high", "description": f"Revenue declined {abs(revenue_growth):.1f}% vs. the prior month."})
    elif revenue_growth < 0:
        risks.append({"type": "Revenue Drop", "severity": "medium", "description": f"Revenue is down {abs(revenue_growth):.1f}% vs. the prior month."})

    profit_margin = features.get("profit_margin_pct") or 0
    op_margin = features.get("operating_margin_pct") or 0
    if op_margin < 0 or (latest.get("operating_expenses", 0) + latest.get("cogs", 0)) > latest.get("revenue", 0):
        risks.append({"type": "High Expenses", "severity": "high", "description": "Operating costs exceed revenue, driving margins negative."})
    elif profit_margin < 5:
        risks.append({"type": "High Expenses", "severity": "medium", "description": f"Profit margin is thin at {profit_margin:.1f}%."})

    cash_ratio = features.get("cash_ratio") or 0
    if cash_ratio < 0.2:
        risks.append({"type": "Cash Flow Issues", "severity": "high", "description": "Cash reserves cover less than 20% of current liabilities."})
    elif cash_ratio < 0.5:
        risks.append({"type": "Cash Flow Issues", "severity": "medium", "description": "Cash reserves are below the recommended buffer."})

    inventory_turnover = features.get("inventory_turnover") or 0
    if inventory_turnover < 0.3:
        risks.append({"type": "Inventory Problems", "severity": "medium", "description": "Inventory is turning over slowly, tying up working capital."})

    debt_ratio = features.get("debt_ratio") or 0
    if debt_ratio > 0.7:
        risks.append({"type": "Debt Risk", "severity": "high", "description": f"Debt makes up {debt_ratio * 100:.0f}% of capital structure."})
    elif debt_ratio > 0.5:
        risks.append({"type": "Debt Risk", "severity": "medium", "description": f"Debt ratio of {debt_ratio * 100:.0f}% is above a healthy threshold."})

    return risks


def _outlier_risks(df: pd.DataFrame) -> list[dict]:
    numeric_cols = ["revenue", "net_profit", "operating_expenses", "cash_balance"]
    available = [c for c in numeric_cols if c in df.columns]
    if len(df) < 5 or not available:
        return []

    X = df[available].fillna(0).values
    model = IsolationForest(contamination=0.15, random_state=42)
    preds = model.fit_predict(X)

    if preds[-1] == -1:
        return [{
            "type": "Outlier Detected",
            "severity": "medium",
            "description": "The latest month's financials deviate significantly from your historical pattern — worth a manual review.",
        }]
    return []


def detect_risks(df: pd.DataFrame, features: dict) -> list[dict]:
    if df.empty:
        return []
    latest = df.iloc[-1]
    return _rule_based_risks(latest, features) + _outlier_risks(df)
