import pandas as pd

from app.ml.feature_engineering import engineer_features, summarize_features
from app.ml.health_score import calculate_health_score
from app.ml.risk_detection import detect_risks


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "period": pd.date_range("2026-01-01", periods=6, freq="MS"),
        "revenue": [10000, 10500, 9800, 11000, 11500, 12000],
        "cogs": [4000, 4100, 4000, 4200, 4300, 4400],
        "operating_expenses": [3000, 3050, 3100, 3000, 3100, 3200],
        "net_profit": [3000, 3350, 2700, 3800, 4100, 4400],
        "cash_balance": [5000, 5200, 4800, 5500, 6000, 6500],
        "current_assets": [8000, 8200, 8100, 8500, 8700, 9000],
        "current_liabilities": [4000, 4100, 4200, 4000, 4100, 4200],
        "total_debt": [2000, 2000, 1900, 1900, 1800, 1800],
        "total_equity": [6000, 6200, 6300, 6500, 6700, 7000],
        "inventory_value": [3000, 3100, 3200, 3000, 2900, 2800],
        "inventory_sold": [1500, 1600, 1550, 1700, 1750, 1800],
        "customers_count": [100, 105, 103, 110, 115, 120],
    })


def test_engineer_features_computes_ratios():
    df = engineer_features(_sample_df())
    assert "profit_margin_pct" in df.columns
    assert df["profit_margin_pct"].iloc[-1] > 0


def test_health_score_within_bounds():
    features = summarize_features(engineer_features(_sample_df()))
    result = calculate_health_score(features)
    assert 0 <= result["score"] <= 100
    assert result["label"] in {"Excellent", "Good", "Average", "Poor", "Critical"}


def test_risk_detection_returns_list():
    df = engineer_features(_sample_df())
    features = summarize_features(df)
    risks = detect_risks(df, features)
    assert isinstance(risks, list)
