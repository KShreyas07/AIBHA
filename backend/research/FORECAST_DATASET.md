# Dataset Card — FRED Retail Trade Monthly Sales (Forecast Comparison)

## Source
- **Provider**: FRED (Federal Reserve Economic Data), Federal Reserve Bank of St. Louis
- **Underlying source**: US Census Bureau, Advance Monthly Retail Trade Survey
- **Access**: public CSV export, no API key required —
  `https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES_ID>`
- **License**: FRED data is public domain (US government statistical data)

## Why a different dataset from Studies A-D
The Taiwanese Bankruptcy Prediction dataset (`DATASET.md`) is cross-sectional — one row
per company, no repeated time periods — so it cannot be used to validate forecasting
models at all. This is a genuinely separate data need: long-history, real monthly
time series to backtest against.

## Series used
Six distinct US Census retail-trade sub-sectors, each a stand-in for a different SME
industry vertical:

| Series ID | Description | Industry analogy |
|---|---|---|
| RSXFS | Retail Trade (ex. Food Services) | General retail |
| RSFSDP | Food Services & Drinking Places | Restaurant/hospitality |
| RSCCAS | Clothing & Clothing Accessory Stores | Apparel retail |
| RSGASS | Gasoline Stations | Fuel/convenience retail |
| RSFHFS | Furniture & Home Furnishings Stores | Home goods retail |
| RSEAS | Electronics & Appliance Stores | Electronics retail |

All six: 414 months, 1992-01 to 2026-06 (34.5 years) — real, seasonal, trending
monthly sales figures (USD millions), not synthetic.

## Methodology (`train_forecast_comparison.py`)
Rolling-origin (walk-forward) backtest: for each series, at multiple combinations of
training-window length (6, 12, 24, 60 months — spanning both "new company, short
history" and "established company, long history" scenarios) and start offset (3 folds
per length), fit each model on the training window only and forecast 12 months ahead.
Compare against actual observed values at 6-month and 12-month horizons using MAE,
RMSE, and MAPE. 432 total evaluations.

Models compared:
- **Prophet** and **Linear Regression** — imported directly from
  `app/ml/forecasting.py` (the actual deployed functions, not reimplementations)
- **ARIMA** (auto order selection by AIC over a small candidate grid) — not currently
  in the app; added here to evaluate whether it's worth adopting

## Key outcome
This study found and fixed a real production bug (Prophet's yearly-seasonality
threshold was unstable at exactly 12 months of history) — see
`results/forecast_comparison_report.md` for the full writeup — and found that ARIMA
outperforms both currently-deployed models on this data (MAPE 3.77% vs. 7.5-7.7% at
the 12-month horizon), a concrete, evidence-based recommendation for the app's model
selection logic.

## Known limitations
- US national retail-sector aggregates, not individual SME company data — real
  individual businesses will have more idiosyncratic, noisier patterns than a
  national sub-sector aggregate. This validates *relative* model performance
  (which forecasting approach handles trend/seasonality better), not the *absolute*
  accuracy this app would achieve on a specific uploaded company's data.
- Only one country's retail sector is represented; no international generalization
  claim can be made from this study alone.

## Reproduce
```bash
cd backend
source .venv/bin/activate
python3 research/prepare_forecast_dataset.py
python3 research/train_forecast_comparison.py
```
