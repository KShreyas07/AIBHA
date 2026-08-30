"""Phase 2, Study B: retrain the winning algorithm from Study A (whichever model scored
highest PR-AUC in full_comparison_metrics.csv) on the practical 7-feature production
subset — the features this app can actually compute from a company's monthly uploads.

This answers a question Study A can't: what performance do we actually get when
deployed, using only lightweight monthly aggregates instead of a full 95-ratio
accounting panel? The gap between Study A and Study B is itself a reportable, honest
empirical result — not something to hide.

Outputs:
  - research/results/production_subset_metrics.csv
  - research/results/production_subset_report.md
  - research/results/best_production_model.joblib   (used by shap_analysis.py next)
"""
from pathlib import Path

import joblib
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
TARGET_COL = "Bankrupt?"

MODEL_BUILDERS = {
    "RandomForest": lambda pw: RandomForestClassifier(
        n_estimators=400, class_weight="balanced", random_state=42, n_jobs=-1),
    "XGBoost": lambda pw: XGBClassifier(
        n_estimators=400, max_depth=6, learning_rate=0.05, scale_pos_weight=pw,
        eval_metric="logloss", random_state=42, n_jobs=-1),
    "LightGBM": lambda pw: LGBMClassifier(
        n_estimators=400, learning_rate=0.05, class_weight="balanced",
        random_state=42, n_jobs=-1, verbose=-1),
    "CatBoost": lambda pw: CatBoostClassifier(
        iterations=400, depth=6, learning_rate=0.05, auto_class_weights="Balanced",
        random_state=42, verbose=False),
}


def load_split():
    train = pd.read_csv(DATA_DIR / "production_subset_clean_train.csv")
    test = pd.read_csv(DATA_DIR / "production_subset_clean_test.csv")
    X_train, y_train = train.drop(columns=[TARGET_COL]), train[TARGET_COL]
    X_test, y_test = test.drop(columns=[TARGET_COL]), test[TARGET_COL]
    return X_train, y_train, X_test, y_test


def evaluate(name, model, X_test, y_test) -> dict:
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
        "true_positives": int(tp), "false_positives": int(fp),
        "true_negatives": int(tn), "false_negatives": int(fn),
    }


def main() -> None:
    full_results = pd.read_csv(RESULTS_DIR / "full_comparison_metrics.csv")
    winner_name = full_results.sort_values("pr_auc", ascending=False).iloc[0]["model"]
    full_winner_pr_auc = full_results.sort_values("pr_auc", ascending=False).iloc[0]["pr_auc"]
    print(f"Study A winner was: {winner_name} (full 95-feature PR-AUC={full_winner_pr_auc:.4f})")
    print(f"Retraining {winner_name} on the 7-feature production subset...\n")

    X_train, y_train, X_test, y_test = load_split()
    print(f"Train: {len(X_train)} rows ({y_train.sum()} positive)")
    print(f"Test:  {len(X_test)} rows ({y_test.sum()} positive)")
    print(f"Features used: {list(X_train.columns)}\n")

    pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    model = MODEL_BUILDERS[winner_name](pos_weight)
    model.fit(X_train, y_train)
    metrics = evaluate(winner_name, model, X_test, y_test)

    joblib.dump(model, RESULTS_DIR / "best_production_model.joblib")
    pd.DataFrame([metrics]).to_csv(RESULTS_DIR / "production_subset_metrics.csv", index=False)

    gap = full_winner_pr_auc - metrics["pr_auc"]
    gap_pct = (gap / full_winner_pr_auc) * 100

    with open(RESULTS_DIR / "production_subset_report.md", "w") as f:
        f.write("# Study B: Production 7-Feature Subset vs. Full 95-Feature Panel\n\n")
        f.write(f"Algorithm: **{winner_name}** (winner of Study A), retrained on only the "
                f"7 features this app can compute from a company's monthly financial "
                f"uploads: `{', '.join(X_train.columns)}`.\n\n")
        f.write("| Metric | Full 95-feature (Study A) | Production 7-feature (Study B) | Gap |\n")
        f.write("|---|---|---|---|\n")
        f.write(f"| PR-AUC | {full_winner_pr_auc:.4f} | {metrics['pr_auc']:.4f} | "
                f"{gap:+.4f} ({gap_pct:+.1f}%) |\n")
        f.write(f"| ROC-AUC | {full_results.sort_values('pr_auc', ascending=False).iloc[0]['roc_auc']:.4f} "
                f"| {metrics['roc_auc']:.4f} | "
                f"{metrics['roc_auc'] - full_results.sort_values('pr_auc', ascending=False).iloc[0]['roc_auc']:+.4f} |\n")
        f.write(f"| F1 | {full_results.sort_values('pr_auc', ascending=False).iloc[0]['f1']:.4f} "
                f"| {metrics['f1']:.4f} | "
                f"{metrics['f1'] - full_results.sort_values('pr_auc', ascending=False).iloc[0]['f1']:+.4f} |\n\n")
        f.write(f"**Interpretation**: reducing from 95 accounting ratios to 7 lightweight "
                f"monthly-aggregate-derived features costs {gap_pct:.1f}% relative PR-AUC. "
                f"This quantifies the practical accuracy/data-collection-burden trade-off "
                f"made by this app's design (users upload monthly summaries, not full "
                f"accounting statements).\n\n")
        f.write("## Full metrics\n\n")
        f.write(pd.DataFrame([metrics]).to_markdown(index=False, floatfmt=".4f"))

    print(f"Production subset: PR-AUC={metrics['pr_auc']:.4f}  ROC-AUC={metrics['roc_auc']:.4f}  "
          f"F1={metrics['f1']:.4f}")
    print(f"Gap vs full feature set: {gap:+.4f} PR-AUC ({gap_pct:+.1f}%)")
    print(f"\nWrote {RESULTS_DIR / 'production_subset_metrics.csv'}")
    print(f"Wrote {RESULTS_DIR / 'production_subset_report.md'}")
    print(f"Wrote {RESULTS_DIR / 'best_production_model.joblib'}")


if __name__ == "__main__":
    main()
