# Study E: Forecast Model Comparison (Rolling-Origin Backtest)

Data: 6 real monthly business-revenue series from FRED (US Census retail trade sub-sectors), 414+ months each (1992-01 to 2026-06). 432 total (series x history-length x fold x model x horizon) evaluations across history lengths [6, 12, 24, 60] months and horizons [6, 12] months.

## Bug found and fixed during this study

The first backtest run found Prophet's 12-month-horizon MAPE spiking to **97% on average (max 324%)** specifically and only at `history_length=12` months, while performing normally at 6, 24, and 60 months. This pointed to `app/ml/forecasting.py`'s `yearly_seasonality=len(series) >= 12` toggle: with exactly one year of data, Prophet attempts to fit a yearly seasonal curve from a single cycle, which is a known-unstable estimation problem. Reproduced directly: on one series, `yearly_seasonality=True` at 12 months of history predicted 946,770 against an actual of 152,329 (a >6x error, with some predictions going negative); `yearly_seasonality=False` on the identical data gave 0.61% MAPE. **Fixed in production** (`app/ml/forecasting.py`) by raising the threshold to 24 months (two full cycles, the minimum needed to estimate a seasonal pattern reliably) — not just noted here. The numbers below are post-fix.

## Overall ranking (lower is better)

| model            |   horizon |     mae |    rmse |   mape |
|:-----------------|----------:|--------:|--------:|-------:|
| ARIMA            |         6 | 1558.76 | 1686.76 |  2.364 |
| ARIMA            |        12 | 2900.93 | 3413.14 |  3.765 |
| LinearRegression |         6 | 3209.6  | 3432.42 |  5.086 |
| LinearRegression |        12 | 5089.19 | 5743.17 |  7.681 |
| Prophet          |         6 | 3249.84 | 3503.64 |  5.061 |
| Prophet          |        12 | 5266.82 | 6006.68 |  7.538 |

## By regime — short history (this app's linear-fallback territory) vs. long history (Prophet territory)

| regime        | model            |   horizon |     mae |     rmse |   mape |
|:--------------|:-----------------|----------:|--------:|---------:|-------:|
| long (>=12mo) | ARIMA            |         6 | 1596.81 |  1723.84 |  2.269 |
| long (>=12mo) | ARIMA            |        12 | 2929.64 |  3436.3  |  3.583 |
| long (>=12mo) | LinearRegression |         6 | 3026.15 |  3190.36 |  4.748 |
| long (>=12mo) | LinearRegression |        12 | 4339.45 |  4826.12 |  6.612 |
| long (>=12mo) | Prophet          |         6 | 2790.67 |  2986.26 |  4.79  |
| long (>=12mo) | Prophet          |        12 | 4089.75 |  4649.62 |  6.46  |
| short (<12mo) | ARIMA            |         6 | 1444.61 |  1575.52 |  2.651 |
| short (<12mo) | ARIMA            |        12 | 2814.8  |  3343.64 |  4.311 |
| short (<12mo) | LinearRegression |         6 | 3759.95 |  4158.6  |  6.101 |
| short (<12mo) | LinearRegression |        12 | 7338.4  |  8494.32 | 10.885 |
| short (<12mo) | Prophet          |         6 | 4627.33 |  5055.78 |  5.873 |
| short (<12mo) | Prophet          |        12 | 8798.03 | 10077.9  | 10.773 |

## Auto-select validation

If we could always pick the best-performing model per origin (oracle / upper bound), mean MAPE at 12-month horizon would be **2.82%**. How often each model was the actual best choice:

| model            |   times_best |
|:-----------------|-------------:|
| ARIMA            |           28 |
| Prophet          |           23 |
| LinearRegression |           21 |

Best single fixed model at 12-month horizon: **ARIMA** (MAPE=3.77%). The gap between always using this one model and the oracle (2.82%) is 0.95 percentage points — this is the headroom a genuine data-driven per-company model-selection strategy could capture over the app's current fixed Prophet-if-enough-history-else-linear rule.
