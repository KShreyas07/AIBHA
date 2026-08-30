"""Offline training script for the production Business Health classifier.

Trains LightGBM (the validated winner of research/train_full_comparison.py, Study A/B)
on real company financial data — the Taiwanese Bankruptcy Prediction dataset (UCI 572),
mapped onto this app's 7 computable canonical features — replacing the previous
synthetic, rule-labeled training approach.

This is NOT run at app startup: it's a one-off (re-run only when the training data or
methodology changes) that produces a versioned artifact loaded by classification.py at
import time. Run it manually:

    cd backend
    source .venv/bin/activate
    python3 -m app.ml.train_bankruptcy_classifier

Outputs:
  - app/ml/artifacts/bankruptcy_classifier.joblib
  - app/ml/artifacts/bankruptcy_classifier_meta.json (metrics, thresholds, provenance)
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.metrics import (
    accuracy_score, average_precision_score, f1_score, precision_score,
    recall_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
TRAINING_DATA_PATH = ARTIFACTS_DIR / "bankruptcy_training_data.csv"
MODEL_PATH = ARTIFACTS_DIR / "bankruptcy_classifier.joblib"
META_PATH = ARTIFACTS_DIR / "bankruptcy_classifier_meta.json"

TARGET_COL = "Bankrupt?"

# Percentile thresholds on predicted bankruptcy probability, calibrated against this
# model's own training-set prediction distribution (heavily right-skewed: real
# financial distress is rare — p50 ~ 0.00003, p90 ~ 0.008, p95 ~ 0.05, p97 ~ 0.63,
# p99 ~ 0.998). Using fixed probability cutoffs like "> 10%" would classify nearly
# every company as Healthy. p97 was tried as the Critical cutoff first and rejected:
# it requires ~99.5% predicted probability, which even a clearly distressed synthetic
# test case (negative margins, near-zero cash ratio, 85% debt ratio) never reached —
# it only got flagged as "Warning". p95 (~5% probability, already well above the 3.23%
# base rate) gives "Critical" room to actually trigger for realistic distressed cases.
WARNING_PERCENTILE = 90
CRITICAL_PERCENTILE = 95


def main() -> None:
    df = pd.read_csv(TRAINING_DATA_PATH)
    X, y = df.drop(columns=[TARGET_COL]), df[TARGET_COL]
    feature_order = list(X.columns)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )

    model = LGBMClassifier(
        n_estimators=400, learning_rate=0.05, class_weight="balanced",
        random_state=42, n_jobs=-1, verbose=-1,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba_test = model.predict_proba(X_test)[:, 1]
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, y_proba_test),
        "pr_auc": average_precision_score(y_test, y_proba_test),
    }
    print("Held-out test metrics:", {k: round(v, 4) for k, v in metrics.items()})

    # Thresholds computed from TRAIN-set predictions only, keeping test metrics above
    # uncontaminated by anything used to calibrate the deployed thresholds.
    y_proba_train = model.predict_proba(X_train)[:, 1]
    warning_threshold = float(np.percentile(y_proba_train, WARNING_PERCENTILE))
    critical_threshold = float(np.percentile(y_proba_train, CRITICAL_PERCENTILE))
    print(f"Warning threshold (p{WARNING_PERCENTILE}): {warning_threshold:.5f}")
    print(f"Critical threshold (p{CRITICAL_PERCENTILE}): {critical_threshold:.5f}")

    ARTIFACTS_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    meta = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "algorithm": "LightGBM",
        "feature_order": feature_order,
        "source_dataset": "Taiwanese Bankruptcy Prediction (UCI ML Repository, ID 572), "
                           "DOI 10.24432/C5004D, CC BY 4.0",
        "n_training_rows": len(X_train),
        "n_test_rows": len(X_test),
        "test_metrics": metrics,
        "warning_threshold": warning_threshold,
        "critical_threshold": critical_threshold,
        "threshold_percentiles": {"warning": WARNING_PERCENTILE, "critical": CRITICAL_PERCENTILE},
        "notes": "customer_growth_rate is accepted by the classifier interface for "
                 "backward compatibility but is NOT used by this model — no equivalent "
                 "exists in the source dataset (see backend/research/DATASET.md).",
    }
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\nWrote {MODEL_PATH}")
    print(f"Wrote {META_PATH}")


if __name__ == "__main__":
    main()
