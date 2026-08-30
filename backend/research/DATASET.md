# Dataset Card — Taiwanese Bankruptcy Prediction

## Source
- **Name**: Taiwanese Bankruptcy Prediction
- **Repository**: UCI Machine Learning Repository, dataset ID 572
- **URL**: https://archive.ics.uci.edu/dataset/572/taiwanese+bankruptcy+prediction
- **DOI**: 10.24432/C5004D (cite this in the paper's dataset section)
- **License**: CC BY 4.0
- **Origin**: Collected from the Taiwan Economic Journal, 1999–2009. Bankruptcy status
  defined per Taiwan Stock Exchange business regulations.

## Shape
- 6,819 companies, 95 financial-ratio features, 1 binary target (`Bankrupt?`)
- 0 missing values, 0 duplicate rows (verified)
- **Severe class imbalance**: 6,599 non-bankrupt (96.77%) vs. 220 bankrupt (3.23%)
  — must be handled explicitly in modeling (class weighting, and evaluation via
  Precision/Recall/F1/ROC-AUC/PR-AUC rather than raw accuracy, which would be
  misleading at this base rate).

## Preprocessing decisions (`prepare_dataset.py`)

**Sentinel-value correction, not simple outlier winsorization.** A systematic scan of
all 95 columns (not just visual inspection of a handful) found **24 columns** contain a
small number of extreme, round-number values in the billions (e.g. 9.99e9) — almost
certainly a sentinel placeholder the original compilers used for undefined ratios (e.g.
division-by-zero when a denominator like inventory or receivables is zero), not real
financial figures.

This matters because the corruption rate varies wildly by column — from 0.01% up to
**88.24%** (`Total Asset Growth Rate`) and **62.16%** (`Cash Turnover Rate`). Simple
percentile winsorization (clip to 1st/99th percentile), the initial approach, silently
fails whenever more than ~1% of a column is corrupted, because the percentile itself is
still in the billions. The corrected approach:

1. Any value > 1000 is treated as missing (a real financial ratio should never
   plausibly reach this range in a properly-scaled, already-normalized dataset).
2. Missing values are imputed with the column's median, computed from the
   non-corrupted values only.
3. Applied uniformly across all 95 feature columns via automated detection, not a
   hand-picked list — an earlier pass manually found only 6 affected columns and
   missed 18 others. See `sentinel_correction_report.csv` for the full per-column
   breakdown (rows affected, % affected, imputed value).
4. **3 columns are >50% sentinel** even after correction (`Total Asset Growth Rate`,
   `Cash Turnover Rate`, `Research and development expense rate`) — these are now
   mostly their own median and carry little real information. They remain in the
   95-feature set for completeness (Study A has 94 other features to draw signal
   from) but should not be treated as reliable individually. None of them are used
   in the production subset.
5. Of the 7 production-subset features, only `inventory_turnover` was affected
   (43.20% sentinel-corrupted) — this is the same feature Study C's
   permutation-importance check independently flagged as not actually predictive,
   which is a reassuring cross-validation of both fixes.

## Two derived files
| File | Purpose |
|---|---|
| `full_95_features_clean.csv` | All 95 features, winsorized. For the rigorous RandomForest / XGBoost / LightGBM / CatBoost comparison study — the paper's core evaluation (Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC + SHAP explainability on the winning model). |
| `production_subset_clean.csv` | 7 features mapped onto this app's canonical feature set, for retraining the deployed `classify_health()` model on real outcomes instead of synthetic rule-based labels. |

Both have `_train.csv` / `_test.csv` stratified 80/20 splits (`random_state=42`,
stratified on `Bankrupt?` to preserve the 3.23% positive rate in both splits).

## Feature mapping — production subset

| App canonical feature | Taiwan dataset column | Match quality |
|---|---|---|
| `current_ratio` | Current Ratio | Direct |
| `debt_ratio` | Debt ratio % | Direct |
| `cash_ratio` | Cash/Current Liability | Direct (sentinel-corrected, 0.67% of rows) |
| `inventory_turnover` | Inventory Turnover Rate (times) | Direct (sentinel-corrected, 43.20% of rows) — **caveat: even after correction, Study C found this feature has negative permutation importance (does not help held-out performance). SHAP still ranks it non-trivially; do not trust that ranking.** |
| `operating_margin_pct` | Operating Profit Rate | Reasonable proxy |
| `profit_margin_pct` | After-tax net Interest Rate | Approximate proxy — low raw variance (25th–75th percentile ≈ 0.809), near-zero *linear* correlation with the target (r=-0.009). **Update after Study C**: despite this, permutation importance is stable and substantial (0.298 ± 0.020) — genuine non-linear/threshold signal invisible to a correlation coefficient, not noise. See `results/shap_example_explanations.md`. |
| `revenue_growth_pct` | Realized Sales Gross Profit Growth Rate | Approximate proxy — low raw variance, modest but real permutation importance (~0.05) per Study C. Weakest of the seven features but not negligible. |
| `customer_growth_rate` | *No equivalent exists* | This is a pure financial-statement dataset — no customer/CRM data. Documented and intentionally excluded from the production-subset retraining rather than faked. |

## Known limitations (for the paper's Limitations section)
- Single-country, single-decade source (Taiwan, 1999–2009) — cross-market
  generalization to modern SMEs in other economies is untested.
- Company-year snapshots, not the monthly time-series format this app collects
  from users — this dataset validates the *classification* model, not the
  time-series forecasting models (those still need a separate time-series
  dataset or evaluation approach).
- `customer_growth_rate` has no real-data validation at all in this study.
- `inventory_turnover` does not survive the permutation-importance check (Study C)
  even after sentinel-value correction — its apparent SHAP importance should not be
  reported as reliable.

## Reproduce
```bash
cd backend
source .venv/bin/activate
python3 research/prepare_dataset.py
```
