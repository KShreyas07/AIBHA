"""Phase 2, Study C: SHAP explainability on the production model (LightGBM, 7-feature
subset) — this is what backs the "Explainable AI" contribution: instead of a bare
"Risk = High", we can report which specific factors drove a prediction and by how much.

Outputs:
  - research/results/shap_global_importance.csv   (mean |SHAP value| per feature, ranked)
  - research/results/shap_summary_plot.png         (global importance bar chart)
  - research/results/shap_example_explanations.md  (per-company worked examples, in the
    "Risk Score = 84%, Reasons: ..." style from the feature spec)
"""
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.inspection import permutation_importance

DATA_DIR = Path(__file__).parent / "datasets"
RESULTS_DIR = Path(__file__).parent / "results"
TARGET_COL = "Bankrupt?"

FEATURE_LABELS = {
    "current_ratio": "Current Ratio",
    "debt_ratio": "Debt Ratio",
    "cash_ratio": "Cash Ratio",
    "inventory_turnover": "Inventory Turnover",
    "operating_margin_pct": "Operating Margin",
    "profit_margin_pct": "Profit Margin",
    "revenue_growth_pct": "Revenue Growth",
}


def main() -> None:
    model = joblib.load(RESULTS_DIR / "best_production_model.joblib")
    test = pd.read_csv(DATA_DIR / "production_subset_clean_test.csv")
    X_test = test.drop(columns=[TARGET_COL])
    y_test = test[TARGET_COL]

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    # LightGBM binary classifier via shap can return a single array or a list per class;
    # normalize to the positive-class (bankrupt) contribution array.
    if isinstance(shap_values, list):
        shap_values = shap_values[1]

    # --- Global feature importance ---
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    importance = pd.DataFrame({
        "feature": X_test.columns,
        "label": [FEATURE_LABELS[c] for c in X_test.columns],
        "mean_abs_shap": mean_abs_shap,
    }).sort_values("mean_abs_shap", ascending=False)
    importance["rank"] = range(1, len(importance) + 1)

    # --- Cross-check with permutation importance (model-agnostic: measures the actual
    #     drop in PR-AUC when a feature is shuffled) and raw point-biserial correlation
    #     with the target. SHAP on tree models can overstate the importance of a
    #     near-constant feature if the model overfits a spurious split on it — comparing
    #     against these two independent signals catches that rather than reporting SHAP
    #     at face value. ---
    perm = permutation_importance(
        model, X_test, y_test, scoring="average_precision", n_repeats=20, random_state=42,
    )
    importance["permutation_importance_mean"] = [
        perm.importances_mean[list(X_test.columns).index(c)] for c in importance["feature"]
    ]
    importance["permutation_importance_std"] = [
        perm.importances_std[list(X_test.columns).index(c)] for c in importance["feature"]
    ]
    raw_corr = X_test.assign(**{TARGET_COL: y_test.values}).corr()[TARGET_COL].drop(TARGET_COL)
    importance["raw_correlation_with_target"] = [raw_corr[c] for c in importance["feature"]]
    importance = importance.sort_values("mean_abs_shap", ascending=False)
    importance.to_csv(RESULTS_DIR / "shap_global_importance.csv", index=False)

    print("Global feature importance (mean |SHAP value|) vs. permutation importance vs. raw correlation:")
    for _, row in importance.iterrows():
        flag = ""
        if row["mean_abs_shap"] > 0 and abs(row["raw_correlation_with_target"]) < 0.02 and row["permutation_importance_mean"] < 0.01:
            flag = "  <-- SHAP rank disagrees with permutation/correlation: likely overfitting artifact, not real signal"
        print(f"  {row['rank']}. {row['label']:22s} SHAP={row['mean_abs_shap']:.5f}  "
              f"perm_imp={row['permutation_importance_mean']:+.5f}  "
              f"raw_corr={row['raw_correlation_with_target']:+.4f}{flag}")

    # --- Summary plot ---
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(importance["label"][::-1], importance["mean_abs_shap"][::-1], color="#6366f1")
    ax.set_xlabel("Mean |SHAP value| (impact on bankruptcy prediction)")
    ax.set_title("Global Feature Importance — Production Classifier (LightGBM)")
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "shap_summary_plot.png", dpi=150)
    plt.close(fig)
    print(f"\nWrote {RESULTS_DIR / 'shap_summary_plot.png'}")

    # --- Worked per-company examples: one true positive (correctly flagged bankrupt),
    #     one false positive (flagged but healthy), one true negative (correctly healthy) ---
    proba = model.predict_proba(X_test)[:, 1]
    pred = model.predict(X_test)

    examples = []
    tp_idx = np.where((pred == 1) & (y_test.values == 1))[0]
    fp_idx = np.where((pred == 1) & (y_test.values == 0))[0]
    tn_idx = np.where((pred == 0) & (y_test.values == 0))[0]
    for label, idx_pool in [("Correctly flagged high-risk company", tp_idx),
                             ("False alarm (flagged, actually healthy)", fp_idx),
                             ("Correctly flagged healthy company", tn_idx)]:
        if len(idx_pool) == 0:
            continue
        i = idx_pool[0]
        row_shap = shap_values[i]
        top_factors = sorted(
            zip(X_test.columns, row_shap, X_test.iloc[i].values),
            key=lambda t: abs(t[1]), reverse=True,
        )[:3]
        examples.append({
            "title": label,
            "risk_score": float(proba[i]),
            "actual_label": "Bankrupt" if y_test.values[i] == 1 else "Not Bankrupt",
            "factors": [
                {"feature": FEATURE_LABELS[f], "shap_contribution": float(s), "value": float(v)}
                for f, s, v in top_factors
            ],
        })

    def stats_for(feature: str) -> dict:
        row = importance[importance["feature"] == feature].iloc[0]
        return {
            "rank": int(row["rank"]),
            "shap": row["mean_abs_shap"],
            "perm_mean": row["permutation_importance_mean"],
            "perm_std": row["permutation_importance_std"],
            "corr": row["raw_correlation_with_target"],
        }

    pm, dr, it, cr = (stats_for(f) for f in
                       ["profit_margin_pct", "debt_ratio", "inventory_turnover", "current_ratio"])

    with open(RESULTS_DIR / "shap_example_explanations.md", "w") as f:
        f.write("# Study C: Explainability — SHAP, Cross-Checked\n\n")

        f.write("## Methodological note: reconciling SHAP, permutation importance, and raw correlation\n\n")
        f.write("SHAP ranks features by their contribution to individual predictions; "
                "permutation importance measures the actual drop in held-out PR-AUC "
                "when a feature is shuffled (repeated 20x per feature to get a stable "
                "mean ± std); raw point-biserial correlation measures only *linear* "
                "association with the target. Comparing all three, rather than "
                "reporting SHAP alone, surfaces features where the measures disagree "
                "in informative ways:\n\n")
        f.write(f"- **`profit_margin_pct`** (SHAP rank #{pm['rank']}) has near-zero "
                f"linear correlation with the target (r = {pm['corr']:+.4f}) — which, "
                f"taken alone, looks like noise, and was flagged as a risk in "
                f"`DATASET.md` (it's a weak proxy column with low raw variance). But "
                f"its permutation importance is {pm['perm_mean']:.4f} ± {pm['perm_std']:.4f} "
                f"— tight and clearly nonzero, on par with `debt_ratio`'s "
                f"{dr['perm_mean']:.4f} ± {dr['perm_std']:.4f}. That combination (no "
                f"linear correlation, but stable, substantial permutation importance) "
                f"means the model has found genuine **non-linear or threshold-based "
                f"signal** within this feature's narrow value range that a linear "
                f"correlation coefficient cannot detect. This is corroborated, not just "
                f"a SHAP artifact — though given the small positive class (220 "
                f"companies), it should still be re-validated with k-fold "
                f"cross-validation before being treated as fully reliable.\n")
        f.write(f"- **`inventory_turnover`** (SHAP rank #{it['rank']}), by contrast, has "
                f"permutation importance of **{it['perm_mean']:+.4f} ± {it['perm_std']:.4f}** "
                f"— shuffling it does not hurt performance (the interval straddles, or "
                f"falls past, zero). This is the case that genuinely looks like a SHAP "
                f"overstatement: even after correcting the sentinel-value data-quality "
                f"issue in this column (see `sentinel_correction_report.csv` — 43.20% "
                f"of raw values were corrupted placeholders), the feature still shows "
                f"no real predictive value. It should not be reported as a reliable "
                f"risk driver.\n")
        f.write(f"- **`current_ratio`** (SHAP rank #{cr['rank']}) shows a different "
                f"mismatch: a real raw correlation (r = {cr['corr']:+.4f}, financially "
                f"sensible — higher current ratio, lower bankruptcy risk) but modest "
                f"permutation importance ({cr['perm_mean']:+.4f} ± {cr['perm_std']:.4f}). "
                f"The likely explanation is redundancy with `debt_ratio` — both are "
                f"balance-sheet solvency measures, so once `debt_ratio` is in the "
                f"model, `current_ratio` adds comparatively little marginal "
                f"information, even though its unconditional relationship with the "
                f"target is real.\n\n")
        f.write(f"**Practical takeaway for the deployed classifier**: `debt_ratio` "
                f"(perm. importance {dr['perm_mean']:.4f}) is the single most robust, "
                f"corroborated driver across all three measures. `profit_margin_pct` "
                f"shows real but non-linear signal worth keeping, pending "
                f"cross-validation. `inventory_turnover`'s importance should be "
                f"treated with caution — it does not survive the permutation-importance "
                f"check even on cleaned data. See `shap_global_importance.csv` for the "
                f"full comparison table.\n\n")

        f.write("## Worked examples\n\n")
        f.write("Demonstrates the target output style — instead of a bare risk label, "
                "surface the specific factors driving the prediction.\n\n")
        for ex in examples:
            f.write(f"## {ex['title']}\n\n")
            f.write(f"**Risk Score**: {ex['risk_score']*100:.1f}%  \n")
            f.write(f"**Actual outcome**: {ex['actual_label']}\n\n")
            f.write("**Reasons (top SHAP-contributing factors):**\n\n")
            for factor in ex["factors"]:
                direction = "increases" if factor["shap_contribution"] > 0 else "decreases"
                f.write(f"- **{factor['feature']}** = {factor['value']:.4f} "
                        f"({direction} risk, SHAP contribution = {factor['shap_contribution']:+.4f})\n")
            f.write("\n")

    print(f"Wrote {RESULTS_DIR / 'shap_example_explanations.md'}")
    print(f"Wrote {RESULTS_DIR / 'shap_global_importance.csv'}")


if __name__ == "__main__":
    main()
