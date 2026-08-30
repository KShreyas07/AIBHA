# Study C: Explainability — SHAP, Cross-Checked

## Methodological note: reconciling SHAP, permutation importance, and raw correlation

SHAP ranks features by their contribution to individual predictions; permutation importance measures the actual drop in held-out PR-AUC when a feature is shuffled (repeated 20x per feature to get a stable mean ± std); raw point-biserial correlation measures only *linear* association with the target. Comparing all three, rather than reporting SHAP alone, surfaces features where the measures disagree in informative ways:

- **`profit_margin_pct`** (SHAP rank #1) has near-zero linear correlation with the target (r = -0.0090) — which, taken alone, looks like noise, and was flagged as a risk in `DATASET.md` (it's a weak proxy column with low raw variance). But its permutation importance is 0.2975 ± 0.0202 — tight and clearly nonzero, on par with `debt_ratio`'s 0.2940 ± 0.0210. That combination (no linear correlation, but stable, substantial permutation importance) means the model has found genuine **non-linear or threshold-based signal** within this feature's narrow value range that a linear correlation coefficient cannot detect. This is corroborated, not just a SHAP artifact — though given the small positive class (220 companies), it should still be re-validated with k-fold cross-validation before being treated as fully reliable.
- **`inventory_turnover`** (SHAP rank #6), by contrast, has permutation importance of **-0.0083 ± 0.0237** — shuffling it does not hurt performance (the interval straddles, or falls past, zero). This is the case that genuinely looks like a SHAP overstatement: even after correcting the sentinel-value data-quality issue in this column (see `sentinel_correction_report.csv` — 43.20% of raw values were corrupted placeholders), the feature still shows no real predictive value. It should not be reported as a reliable risk driver.
- **`current_ratio`** (SHAP rank #5) shows a different mismatch: a real raw correlation (r = -0.0643, financially sensible — higher current ratio, lower bankruptcy risk) but modest permutation importance (+0.0314 ± 0.0145). The likely explanation is redundancy with `debt_ratio` — both are balance-sheet solvency measures, so once `debt_ratio` is in the model, `current_ratio` adds comparatively little marginal information, even though its unconditional relationship with the target is real.

**Practical takeaway for the deployed classifier**: `debt_ratio` (perm. importance 0.2940) is the single most robust, corroborated driver across all three measures. `profit_margin_pct` shows real but non-linear signal worth keeping, pending cross-validation. `inventory_turnover`'s importance should be treated with caution — it does not survive the permutation-importance check even on cleaned data. See `shap_global_importance.csv` for the full comparison table.

## Worked examples

Demonstrates the target output style — instead of a bare risk label, surface the specific factors driving the prediction.

## Correctly flagged high-risk company

**Risk Score**: 91.8%  
**Actual outcome**: Bankrupt

**Reasons (top SHAP-contributing factors):**

- **Profit Margin** = 0.8089 (increases risk, SHAP contribution = +5.1103)
- **Debt Ratio** = 0.2132 (increases risk, SHAP contribution = +4.0242)
- **Cash Ratio** = 0.0048 (increases risk, SHAP contribution = +2.7461)

## False alarm (flagged, actually healthy)

**Risk Score**: 60.6%  
**Actual outcome**: Not Bankrupt

**Reasons (top SHAP-contributing factors):**

- **Profit Margin** = 0.8084 (increases risk, SHAP contribution = +5.1015)
- **Operating Margin** = 0.9987 (increases risk, SHAP contribution = +2.7378)
- **Current Ratio** = 0.0042 (increases risk, SHAP contribution = +1.0595)

## Correctly flagged healthy company

**Risk Score**: 0.0%  
**Actual outcome**: Not Bankrupt

**Reasons (top SHAP-contributing factors):**

- **Operating Margin** = 0.9990 (increases risk, SHAP contribution = +1.4238)
- **Debt Ratio** = 0.1580 (increases risk, SHAP contribution = +0.7098)
- **Inventory Turnover** = 0.0002 (increases risk, SHAP contribution = +0.3476)

