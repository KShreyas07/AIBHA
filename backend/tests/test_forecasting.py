import numpy as np
import pandas as pd
import pytest

from app.ml.forecasting import forecast_metric


def _financial_df(n_months: int, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    periods = pd.date_range("2024-01-01", periods=n_months, freq="MS")
    trend = np.linspace(50000, 50000 + 500 * n_months, n_months)
    noise = rng.normal(0, 500, n_months)
    revenue = trend + noise
    return pd.DataFrame({
        "period": periods,
        "revenue": revenue,
        "net_profit": revenue * 0.15,
        "operating_expenses": revenue * 0.5,
        "cash_balance": revenue * 0.3,
    })


@pytest.mark.parametrize("n_months,horizon", [(4, 6), (8, 6), (12, 6), (24, 12)])
def test_forecast_metric_returns_correct_horizon_length(n_months, horizon):
    df = _financial_df(n_months)
    points = forecast_metric(df, "revenue", horizon)
    assert len(points) == horizon
    for point in points:
        assert "predicted_value" in point
        assert "model_used" in point
        assert point["model_used"] in {"arima", "prophet", "linear"}


def test_forecast_metric_short_history_skips_auto_select():
    # Below MIN_MONTHS_FOR_AUTO_SELECT (9): should go straight to arima (or its
    # fallback, linear, if arima can't fit this particular tiny series).
    df = _financial_df(4)
    points = forecast_metric(df, "revenue", 6)
    assert points[0]["model_used"] in {"arima", "linear"}


def test_forecast_metric_requires_minimum_history():
    df = _financial_df(2)
    with pytest.raises(ValueError):
        forecast_metric(df, "revenue", 6)


def test_forecast_metric_rejects_unknown_metric():
    df = _financial_df(12)
    with pytest.raises(ValueError):
        forecast_metric(df, "not_a_real_metric", 6)


def test_forecast_metric_bounds_are_sane():
    df = _financial_df(12)
    points = forecast_metric(df, "revenue", 6)
    for point in points:
        assert point["lower_bound"] <= point["predicted_value"] <= point["upper_bound"]
