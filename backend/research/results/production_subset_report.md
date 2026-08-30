# Study B: Production 7-Feature Subset vs. Full 95-Feature Panel

Algorithm: **LightGBM** (winner of Study A), retrained on only the 7 features this app can compute from a company's monthly financial uploads: `current_ratio, debt_ratio, cash_ratio, inventory_turnover, operating_margin_pct, profit_margin_pct, revenue_growth_pct`.

| Metric | Full 95-feature (Study A) | Production 7-feature (Study B) | Gap |
|---|---|---|---|
| PR-AUC | 0.5732 | 0.4213 | +0.1519 (+26.5%) |
| ROC-AUC | 0.9582 | 0.8777 | -0.0805 |
| F1 | 0.5352 | 0.4304 | -0.1048 |

**Interpretation**: reducing from 95 accounting ratios to 7 lightweight monthly-aggregate-derived features costs 26.5% relative PR-AUC. This quantifies the practical accuracy/data-collection-burden trade-off made by this app's design (users upload monthly summaries, not full accounting statements).

## Full metrics

| model    |   accuracy |   precision |   recall |     f1 |   roc_auc |   pr_auc |   true_positives |   false_positives |   true_negatives |   false_negatives |
|:---------|-----------:|------------:|---------:|-------:|----------:|---------:|-----------------:|------------------:|-----------------:|------------------:|
| LightGBM |     0.9670 |      0.4857 |   0.3864 | 0.4304 |    0.8777 |   0.4213 |               17 |                18 |             1302 |                27 |