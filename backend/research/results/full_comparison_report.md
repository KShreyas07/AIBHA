# Study A: Full 95-Feature Model Comparison

Dataset: Taiwanese Bankruptcy Prediction (UCI 572), 6819 companies, 95 features, 220 bankrupt (3.23%).

Selection criterion: **PR-AUC** (average precision), since ROC-AUC can be optimistic under severe class imbalance while PR-AUC focuses on performance on the minority (bankrupt) class, which is the class that actually matters for this task.

## Results (sorted by PR-AUC)

| model        |   accuracy |   precision |   recall |     f1 |   roc_auc |   pr_auc |   true_positives |   false_positives |   true_negatives |   false_negatives |   train_seconds |
|:-------------|-----------:|------------:|---------:|-------:|----------:|---------:|-----------------:|------------------:|-----------------:|------------------:|----------------:|
| LightGBM     |     0.9758 |      0.7037 |   0.4318 | 0.5352 |    0.9582 |   0.5732 |               19 |                 8 |             1312 |                25 |          1.8100 |
| XGBoost      |     0.9685 |      0.5128 |   0.4545 | 0.4819 |    0.9526 |   0.5353 |               20 |                19 |             1301 |                24 |          0.9900 |
| RandomForest |     0.9707 |      0.5526 |   0.4773 | 0.5122 |    0.9469 |   0.5032 |               21 |                17 |             1303 |                23 |          0.6400 |
| CatBoost     |     0.9611 |      0.4151 |   0.5000 | 0.4536 |    0.9468 |   0.5021 |               22 |                31 |             1289 |                22 |          1.6200 |

## Winner: LightGBM

Selected model saved to `results/best_full_model.joblib`.
