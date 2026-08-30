# Study D: Business Health Score Validation

Validates `app/ml/health_score.py::calculate_health_score()` — the actual production function, imported directly — against real bankruptcy outcomes in the Taiwan dataset (n=6819).

**Caveat**: `customer_growth_rate` (10 of 100 points) has no equivalent in this dataset and defaults to a fixed value for every company (see `DATASET.md`), so this validates the 90 real points the other 5 components contribute, not the full 100-point formula.

## Summary statistics

| Group | Mean health score | N |
|---|---|---|
| Bankrupt | 26.37 | 220 |
| Solvent | 37.81 | 6599 |

- Welch's t-test (solvent vs. bankrupt mean score): t=19.430, **p=5.74e-51**
- Point-biserial correlation (score vs. bankruptcy): r=-0.2088, p=4.63e-68
- **ROC-AUC** (health score, inverted, as a bankruptcy-risk predictor): **0.8121**

## Bankruptcy rate by health score label

| health_label   |   bankruptcy_rate |   n_companies |
|:---------------|------------------:|--------------:|
| Critical       |            0.0908 |     1641.0000 |
| Poor           |            0.0153 |     4511.0000 |
| Average        |            0.0030 |      667.0000 |

## Interpretation

An AUC of 0.812 indicates the health score has genuine, meaningful discriminative power for predicting real bankruptcy outcomes — well above the 0.5 no-skill baseline, using a transparent, interpretable weighted-rubric formula rather than a black-box model.
