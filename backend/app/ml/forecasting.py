"""Forecasting for revenue / profit / expenses / cash flow, 6 or 12 months ahead.

Model selection is backed by a rolling-origin backtest against six real monthly
business-revenue time series (research/train_forecast_comparison.py, Study E): ARIMA
outperformed both Prophet and linear-regression trend at every horizon and every
history-length regime tested (12-month-horizon MAPE: ARIMA 3.8% vs. Prophet 7.5% vs.
Linear 7.7%), but no single model won on every series — an oracle that picked the best
model per case reached 2.8% MAPE, meaningfully better than always using the single best
fixed model. So instead of a fixed model per history-length bucket, we auto-select: hold
out the last few months of the company's own data, fit every viable candidate on the
rest, and use whichever model predicts the holdout best — then refit that winner on the
full history for the real forecast.

For very short histories there isn't enough data to hold out a validation slice, so we
skip straight to ARIMA (the study's strongest performer even in the short-history
regime), falling back to a linear trend only if ARIMA fails to fit.
"""
import warnings

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from app.core.logging import get_logger

logger = get_logger(__name__)

METRIC_COLUMNS = {
    "revenue": "revenue",
    "profit": "net_profit",
    "expenses": "operating_expenses",
    "cash_flow": "cash_balance",
}

# Candidate ARIMA orders to try; keep best by AIC. Matches Study E's methodology.
ARIMA_ORDER_CANDIDATES = [(1, 1, 1), (2, 1, 1), (1, 1, 0), (0, 1, 1)]

MIN_MONTHS_FOR_AUTO_SELECT = 9  # enough history to hold out a meaningful validation slice
VALIDATION_HOLDOUT_MONTHS = 3


def _forecast_linear(series: pd.DataFrame, horizon_months: int) -> pd.DataFrame:
    series = series.reset_index(drop=True)
    X = np.arange(len(series)).reshape(-1, 1)
    y = series["y"].values
    model = LinearRegression().fit(X, y)

    residual_std = float(np.std(y - model.predict(X))) if len(y) > 1 else abs(y[-1]) * 0.1

    future_idx = np.arange(len(series), len(series) + horizon_months).reshape(-1, 1)
    preds = model.predict(future_idx)
    last_date = series["ds"].max()
    future_dates = pd.date_range(last_date, periods=horizon_months + 1, freq="MS")[1:]

    return pd.DataFrame({
        "ds": future_dates,
        "yhat": preds,
        "yhat_lower": preds - 1.96 * residual_std,
        "yhat_upper": preds + 1.96 * residual_std,
    })


def _forecast_prophet(series: pd.DataFrame, horizon_months: int) -> pd.DataFrame:
    from prophet import Prophet

    # Yearly seasonality needs at least two full cycles to estimate reliably. Enabling
    # it with exactly one year of data (the old `>= 12` threshold) is actively harmful:
    # a rolling-origin backtest against real monthly retail-sales data (Study E) showed
    # MAPE jumping from 0.6% to 100%+ at exactly 12 months of history, because Prophet
    # tries to fit a seasonal curve to a single cycle and extrapolates wildly.
    model = Prophet(yearly_seasonality=len(series) >= 24, weekly_seasonality=False, daily_seasonality=False)
    model.fit(series)
    future = model.make_future_dataframe(periods=horizon_months, freq="MS")
    forecast = model.predict(future)
    return forecast.tail(horizon_months)[["ds", "yhat", "yhat_lower", "yhat_upper"]]


def _forecast_arima(series: pd.DataFrame, horizon_months: int) -> pd.DataFrame:
    from statsmodels.tsa.arima.model import ARIMA

    y = series["y"].values
    best_aic, best_fit = np.inf, None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for order in ARIMA_ORDER_CANDIDATES:
            try:
                fit = ARIMA(y, order=order).fit()
            except Exception:  # noqa: BLE001 - some orders are inestimable on short/degenerate series
                continue
            if fit.aic < best_aic:
                best_aic, best_fit = fit.aic, fit

    if best_fit is None:
        raise ValueError("No ARIMA order could be fit to this series")

    result = best_fit.get_forecast(steps=horizon_months)
    preds = result.predicted_mean
    conf_int = result.conf_int(alpha=0.05)
    last_date = series["ds"].max()
    future_dates = pd.date_range(last_date, periods=horizon_months + 1, freq="MS")[1:]

    return pd.DataFrame({
        "ds": future_dates,
        "yhat": preds,
        "yhat_lower": conf_int[:, 0],
        "yhat_upper": conf_int[:, 1],
    })


MODEL_FUNCS = {
    "arima": _forecast_arima,
    "prophet": _forecast_prophet,
    "linear": _forecast_linear,
}


def _mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    denom = np.where(actual == 0, np.finfo(float).eps, actual)
    return float(np.mean(np.abs((actual - predicted) / denom)) * 100)


def _auto_select_model(series: pd.DataFrame) -> str:
    """Hold out the last few months, fit every viable candidate on the rest, and return
    the name of whichever model predicts the holdout best (lowest MAPE)."""
    holdout = min(VALIDATION_HOLDOUT_MONTHS, len(series) // 3)
    train, actual_holdout = series.iloc[:-holdout], series.iloc[-holdout:]

    candidates = ["arima", "linear"]
    if len(train) >= 6:
        candidates.append("prophet")

    scores = {}
    for name in candidates:
        try:
            forecast = MODEL_FUNCS[name](train, holdout)
            scores[name] = _mape(actual_holdout["y"].values, forecast["yhat"].values[:holdout])
        except Exception:  # noqa: BLE001 - a candidate failing validation just drops out of the race
            logger.info("Forecast candidate '%s' failed during auto-select validation", name)

    if not scores:
        return "linear"
    return min(scores, key=scores.get)


def forecast_metric(df: pd.DataFrame, metric: str, horizon_months: int = 6) -> list[dict]:
    if metric not in METRIC_COLUMNS:
        raise ValueError(f"Unsupported metric '{metric}'. Choose from {list(METRIC_COLUMNS)}")

    column = METRIC_COLUMNS[metric]
    series = df[["period", column]].rename(columns={"period": "ds", column: "y"}).dropna()
    series["ds"] = pd.to_datetime(series["ds"])

    if len(series) < 3:
        raise ValueError("At least 3 months of data are required to generate a forecast")

    if len(series) >= MIN_MONTHS_FOR_AUTO_SELECT:
        selected = _auto_select_model(series)
    else:
        # Not enough history to hold out a meaningful validation slice — go straight to
        # ARIMA, the strongest performer even in the short-history regime in Study E.
        selected = "arima"

    try:
        forecast = MODEL_FUNCS[selected](series, horizon_months)
    except Exception:  # noqa: BLE001 - degrade gracefully on any single-model failure
        logger.exception("Forecast model '%s' failed for metric=%s, falling back to linear trend",
                          selected, metric)
        selected = "linear"
        forecast = _forecast_linear(series, horizon_months)

    points = [
        {
            "period": row.ds.strftime("%Y-%m-%d"),
            "predicted_value": round(float(row.yhat), 2),
            "lower_bound": round(float(row.yhat_lower), 2),
            "upper_bound": round(float(row.yhat_upper), 2),
        }
        for row in forecast.itertuples()
    ]
    for point in points:
        point["model_used"] = selected
    return points
