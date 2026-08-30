"""Prepares the Taiwanese Bankruptcy Prediction dataset (UCI ID 572) for two downstream uses:

1. `full_95_features_clean.csv` — all 95 original financial ratios, for the rigorous
   RandomForest vs XGBoost vs LightGBM vs CatBoost comparison study (the paper's core
   evaluation: real data, standard metrics, SHAP explainability on the winning model).

2. `production_subset_clean.csv` — only the 7 features that map onto this app's existing
   canonical feature set (see FEATURE_MAPPING below), for retraining the deployed
   classify_health() model on real outcomes instead of synthetic rule-based labels.

Preprocessing — sentinel-value correction (not simple outlier winsorization):
A systematic scan of all 95 columns found 24 of them contain a small number of
extreme, round-number values in the billions (e.g. 9.99e9), almost always at the exact
values 9.99e9 / 9.98e9 / 1.0e10, etc. This is a well-documented characteristic of this
specific dataset: the original compilers appear to have used a large sentinel value for
undefined ratios (e.g. division-by-zero when a denominator, such as inventory or
receivables, is zero) rather than leaving them blank. Critically, this is NOT a rare
outlier in every affected column — some columns (e.g. "Total Asset Growth Rate") have
this sentinel value in 88% of rows, meaning percentile-based winsorization silently
fails for them (the 99th percentile itself is still in the billions). The correct fix
is sentinel detection + median imputation, not clipping:
  1. Any value > SENTINEL_THRESHOLD (1000) is treated as missing, regardless of what
     fraction of the column it represents.
  2. Missing values are imputed with the column's median computed from the remaining
     (non-sentinel) values.
This is applied uniformly to all 95 feature columns, not a hand-picked subset — an
earlier version of this script only handled 6 columns found by manual inspection and
missed 18 others; this version scans systematically instead.

Columns that are majority-sentinel after this fix (i.e. more than half their values
were imputed) are flagged in `SENTINEL_REPORT.md` as low-reliability, since imputing
>50% of a column with its own median makes it a near-constant, low-information feature
— an honest fact to report, not something to hide.

Source: Taiwan Economic Journal, 1999-2009. UCI ML Repository, DOI: 10.24432/C5004D.
License: CC BY 4.0.
"""
from pathlib import Path

import pandas as pd

RAW_PATH = Path(__file__).parent / "datasets" / "taiwan_bankruptcy_raw.csv"
OUT_DIR = Path(__file__).parent / "datasets"

TARGET_COL = "Bankrupt?"
SENTINEL_THRESHOLD = 1000.0

# Canonical app feature -> source column in the Taiwan dataset.
# `customer_growth_rate` has no equivalent in this dataset (no customer/CRM data exists
# in company financial statements) and is intentionally omitted here.
FEATURE_MAPPING = {
    "current_ratio": "Current Ratio",
    "debt_ratio": "Debt ratio %",
    "cash_ratio": "Cash/Current Liability",
    "inventory_turnover": "Inventory Turnover Rate (times)",
    "operating_margin_pct": "Operating Profit Rate",
    "profit_margin_pct": "After-tax net Interest Rate",
    "revenue_growth_pct": "Realized Sales Gross Profit Growth Rate",
}


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(RAW_PATH)
    df.columns = [c.strip() for c in df.columns]
    return df


def fix_sentinel_values(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Replace sentinel-scale values with the column's clean median. Returns the fixed
    dataframe plus a report of which columns were affected and how badly."""
    df = df.copy()
    report_rows = []
    feature_cols = [c for c in df.columns if c != TARGET_COL]

    for col in feature_cols:
        is_sentinel = df[col] > SENTINEL_THRESHOLD
        n_sentinel = int(is_sentinel.sum())
        if n_sentinel == 0:
            continue
        clean_median = df.loc[~is_sentinel, col].median()
        df.loc[is_sentinel, col] = clean_median
        report_rows.append({
            "column": col,
            "n_sentinel_values": n_sentinel,
            "pct_sentinel": round(n_sentinel / len(df) * 100, 2),
            "imputed_with_median": clean_median,
            "majority_imputed": n_sentinel / len(df) > 0.5,
        })

    report = pd.DataFrame(report_rows).sort_values("pct_sentinel", ascending=False)
    return df, report


def build_production_subset(df: pd.DataFrame) -> pd.DataFrame:
    cols = [TARGET_COL] + list(FEATURE_MAPPING.values())
    subset = df[cols].rename(columns={v: k for k, v in FEATURE_MAPPING.items()})
    return subset


def main() -> None:
    raw = load_raw()
    print(f"Loaded {len(raw)} rows, {len(raw.columns) - 1} features")
    print(f"Class balance: {raw[TARGET_COL].value_counts(normalize=True).round(4).to_dict()}")

    clean, report = fix_sentinel_values(raw)
    report.to_csv(OUT_DIR / "sentinel_correction_report.csv", index=False)
    print(f"\nSentinel values found and corrected in {len(report)} of "
          f"{len(raw.columns) - 1} columns:")
    print(report.to_string(index=False))

    majority_imputed = report[report["majority_imputed"]]
    if len(majority_imputed):
        print(f"\nWARNING: {len(majority_imputed)} column(s) were >50% sentinel and are "
              f"now mostly their own median (low information after correction): "
              f"{list(majority_imputed['column'])}")

    clean.to_csv(OUT_DIR / "full_95_features_clean.csv", index=False)
    print(f"\nWrote full_95_features_clean.csv ({clean.shape[0]} rows, {clean.shape[1]} cols)")

    subset = build_production_subset(clean)
    subset.to_csv(OUT_DIR / "production_subset_clean.csv", index=False)
    print(f"Wrote production_subset_clean.csv ({subset.shape[0]} rows, {subset.shape[1]} cols)")


if __name__ == "__main__":
    main()
