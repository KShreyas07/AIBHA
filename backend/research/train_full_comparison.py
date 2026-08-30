"""Phase 2, Study A: compare RandomForest, XGBoost, LightGBM, and CatBoost for bankruptcy
classification on the full 95-feature Taiwanese Bankruptcy Prediction dataset.

The dataset is severely imbalanced (3.23% positive class), so:
  - Every model is trained with class-balanced weighting (no synthetic oversampling —
    SMOTE would fabricate data, which is undesirable for a dataset this sensitive).
  - Evaluation reports Accuracy, Precision, Recall, F1, ROC-AUC, and PR-AUC (average
    precision). Accuracy alone would be misleading at a 96.77% base rate — a model that
    predicts "not bankrupt" for everyone scores 96.77% accuracy while being useless.

Outputs:
  - research/results/full_comparison_metrics.csv  (all models, all metrics)
  - research/results/full_comparison_report.md     (formatted report for the paper)
  - research/results/best_full_model.joblib        (winning model, for reference)
"""
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
)
from xgboost import XGBClassifier

DATA_DIR = Path(__file__).parent / "datasets"
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

TARGET_COL = "Bankrupt?"


def load_split():
    train = pd.read_csv(DATA_DIR / "full_95_features_clean_train.csv")
    test = pd.read_csv(DATA_DIR / "full_95_features_clean_test.csv")
    X_train, y_train = train.drop(columns=[TARGET_COL]), train[TARGET_COL]
    X_test, y_test = test.drop(columns=[TARGET_COL]), test[TARGET_COL]
    return X_train, y_train, X_test, y_test


def build_models(pos_weight: float) -> dict:
    return {
        "RandomForest": RandomForestClassifier(
            n_estimators=400, max_depth=None, class_weight="balanced",
            random_state=42, n_jobs=-1,
        ),
        "XGBoost": XGBClassifier(
            n_estimators=400, max_depth=6, learning_rate=0.05,
            scale_pos_weight=pos_weight, eval_metric="logloss",
            random_state=42, n_jobs=-1,
        ),
        "LightGBM": LGBMClassifier(
            n_estimators=400, max_depth=-1, learning_rate=0.05,
            class_weight="balanced", random_state=42, n_jobs=-1, verbose=-1,
        ),
        "CatBoost": CatBoostClassifier(
            iterations=400, depth=6, learning_rate=0.05,
            auto_class_weights="Balanced", random_state=42, verbose=False,
        ),
    }


def evaluate(name: str, model, X_test, y_test, train_seconds: float) -> dict:
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

    return {
        "model": name,
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, y_proba),
        "pr_auc": average_precision_score(y_test, y_proba),
        "true_positives": int(tp),
        "false_positives": int(fp),
        "true_negatives": int(tn),
        "false_negatives": int(fn),
        "train_seconds": round(train_seconds, 2),
    }


def main() -> None:
    X_train, y_train, X_test, y_test = load_split()
    pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    print(f"Train: {len(X_train)} rows ({y_train.sum()} positive)")
    print(f"Test:  {len(X_test)} rows ({y_test.sum()} positive)")
    print(f"scale_pos_weight (for XGBoost): {pos_weight:.2f}")
    print()

    models = build_models(pos_weight)
    results = []
    trained_models = {}

    for name, model in models.items():
        print(f"Training {name}...")
        start = time.time()
        model.fit(X_train, y_train)
        elapsed = time.time() - start
        metrics = evaluate(name, model, X_test, y_test, elapsed)
        results.append(metrics)
        trained_models[name] = model
        print(f"  Accuracy={metrics['accuracy']:.4f}  F1={metrics['f1']:.4f}  "
              f"ROC-AUC={metrics['roc_auc']:.4f}  PR-AUC={metrics['pr_auc']:.4f}  "
              f"({elapsed:.1f}s)")

    results_df = pd.DataFrame(results).sort_values("pr_auc", ascending=False)
    results_df.to_csv(RESULTS_DIR / "full_comparison_metrics.csv", index=False)

    winner_name = results_df.iloc[0]["model"]
    winner_model = trained_models[winner_name]
    joblib.dump(winner_model, RESULTS_DIR / "best_full_model.joblib")

    with open(RESULTS_DIR / "full_comparison_report.md", "w") as f:
        f.write("# Study A: Full 95-Feature Model Comparison\n\n")
        f.write(f"Dataset: Taiwanese Bankruptcy Prediction (UCI 572), "
                f"{len(X_train) + len(X_test)} companies, 95 features, "
                f"{(y_train.sum() + y_test.sum())} bankrupt "
                f"({(y_train.sum() + y_test.sum()) / (len(y_train) + len(y_test)) * 100:.2f}%).\n\n")
        f.write("Selection criterion: **PR-AUC** (average precision), since ROC-AUC can "
                "be optimistic under severe class imbalance while PR-AUC focuses on "
                "performance on the minority (bankrupt) class, which is the class that "
                "actually matters for this task.\n\n")
        f.write("## Results (sorted by PR-AUC)\n\n")
        f.write(results_df.to_markdown(index=False, floatfmt=".4f"))
        f.write(f"\n\n## Winner: {winner_name}\n\n")
        f.write(f"Selected model saved to `results/best_full_model.joblib`.\n")

    print()
    print(f"Winner: {winner_name} (PR-AUC={results_df.iloc[0]['pr_auc']:.4f})")
    print(f"Wrote {RESULTS_DIR / 'full_comparison_metrics.csv'}")
    print(f"Wrote {RESULTS_DIR / 'full_comparison_report.md'}")


if __name__ == "__main__":
    main()
