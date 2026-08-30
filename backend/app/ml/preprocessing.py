import re

import numpy as np
import pandas as pd

NUMERIC_FIELDS = [
    "revenue", "cogs", "operating_expenses", "net_profit", "cash_balance",
    "current_assets", "current_liabilities", "total_debt", "total_equity",
    "inventory_value", "inventory_sold", "customers_count",
]

# Fixed conversion rates to USD for the demo; swap for a live FX API in production.
CURRENCY_TO_USD = {"USD": 1.0, "EUR": 1.08, "GBP": 1.27, "INR": 0.012, "JPY": 0.0067}


def _clean_numeric(value) -> float:
    if pd.isna(value):
        return np.nan
    if isinstance(value, (int, float)):
        return float(value)
    text = re.sub(r"[^0-9.\-]", "", str(value))
    if text in ("", "-", "."):
        return np.nan
    try:
        return float(text)
    except ValueError:
        return np.nan


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean an uploaded financial dataset: parse dates, coerce numerics, drop duplicate
    periods, convert currency to USD, and fill small gaps via forward/back fill."""
    df = df.copy()

    if "period" not in df.columns:
        raise ValueError("Uploaded file must contain a date/period column")

    df["period"] = pd.to_datetime(df["period"], errors="coerce")
    df = df.dropna(subset=["period"])
    df["period"] = df["period"].dt.to_period("M").dt.to_timestamp()

    for field in NUMERIC_FIELDS:
        if field in df.columns:
            df[field] = df[field].apply(_clean_numeric)

    if "currency" in df.columns:
        df["currency"] = df["currency"].fillna("USD").str.upper()
        rate = df["currency"].map(CURRENCY_TO_USD).fillna(1.0)
        for field in NUMERIC_FIELDS:
            if field in df.columns:
                df[field] = df[field] * rate
        df["currency"] = "USD"
    else:
        df["currency"] = "USD"

    df = df.drop_duplicates(subset=["period"], keep="last")
    df = df.sort_values("period")

    present_numeric = [f for f in NUMERIC_FIELDS if f in df.columns]
    df[present_numeric] = df[present_numeric].ffill().bfill().fillna(0)

    return df.reset_index(drop=True)
