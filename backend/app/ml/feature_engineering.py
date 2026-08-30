import numpy as np
import pandas as pd


def _safe_div(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return (numerator / denominator.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the derived financial ratios used by the ML models and dashboard, given a
    cleaned, monthly, chronologically-sorted DataFrame for a single company."""
    df = df.sort_values("period").reset_index(drop=True)

    for col in [
        "revenue", "cogs", "operating_expenses", "net_profit", "cash_balance",
        "current_assets", "current_liabilities", "total_debt", "total_equity",
        "inventory_value", "inventory_sold", "customers_count",
    ]:
        if col not in df.columns:
            df[col] = 0.0

    df["revenue_growth_pct"] = df["revenue"].pct_change() * 100
    df["profit_margin_pct"] = _safe_div(df["net_profit"], df["revenue"]) * 100
    df["operating_margin_pct"] = _safe_div(df["revenue"] - df["operating_expenses"] - df["cogs"], df["revenue"]) * 100
    df["cash_ratio"] = _safe_div(df["cash_balance"], df["current_liabilities"])
    df["current_ratio"] = _safe_div(df["current_assets"], df["current_liabilities"])
    df["debt_ratio"] = _safe_div(df["total_debt"], df["total_equity"] + df["total_debt"])
    df["inventory_turnover"] = _safe_div(df["inventory_sold"], df["inventory_value"])
    df["customer_growth_rate"] = df["customers_count"].pct_change() * 100

    ratio_cols = [
        "revenue_growth_pct", "profit_margin_pct", "operating_margin_pct", "cash_ratio",
        "current_ratio", "debt_ratio", "inventory_turnover", "customer_growth_rate",
    ]
    df[ratio_cols] = df[ratio_cols].replace([np.inf, -np.inf], np.nan)

    return df


def summarize_features(df: pd.DataFrame) -> dict:
    """Aggregate figures used across dashboard/health-score/report: latest month values
    plus trailing averages."""
    if df.empty:
        return {}

    latest = df.iloc[-1]
    trailing = df.tail(3)

    return {
        "average_monthly_revenue": float(trailing["revenue"].mean()),
        "monthly_expenses": float(latest["operating_expenses"] + latest["cogs"]),
        "net_profit": float(latest["net_profit"]),
        "revenue": float(latest["revenue"]),
        "cash_balance": float(latest["cash_balance"]),
        "revenue_growth_pct": float(latest["revenue_growth_pct"]) if pd.notna(latest["revenue_growth_pct"]) else 0.0,
        "profit_margin_pct": float(latest["profit_margin_pct"]) if pd.notna(latest["profit_margin_pct"]) else 0.0,
        "operating_margin_pct": float(latest["operating_margin_pct"]) if pd.notna(latest["operating_margin_pct"]) else 0.0,
        "cash_ratio": float(latest["cash_ratio"]) if pd.notna(latest["cash_ratio"]) else 0.0,
        "current_ratio": float(latest["current_ratio"]) if pd.notna(latest["current_ratio"]) else 0.0,
        "debt_ratio": float(latest["debt_ratio"]) if pd.notna(latest["debt_ratio"]) else 0.0,
        "inventory_turnover": float(latest["inventory_turnover"]) if pd.notna(latest["inventory_turnover"]) else 0.0,
        "customer_growth_rate": float(latest["customer_growth_rate"]) if pd.notna(latest["customer_growth_rate"]) else 0.0,
    }
