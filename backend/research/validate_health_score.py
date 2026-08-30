"""Phase 2, Study D: validate the app's actual weighted Business Health Score
(app/ml/health_score.py::calculate_health_score — imported directly, not reimplemented)
against real bankruptcy outcomes in the Taiwan dataset.

This is a deterministic rule-based formula, not a trained model, so there's no
train/test leakage concern — the full dataset is used for maximum statistical power.

Scale reconciliation (important): calculate_health_score()'s _scale() bounds assume
real-world percentage inputs (e.g. worst=-20/best=20 for revenue_growth_pct,
worst=-10/best=25 for profit_margin_pct). The Taiwan dataset's proxy columns for these
two are pre-normalized by the original authors into a razor-thin band (see DATASET.md —
e.g. profit_margin_pct's middle 98% spans only 0.807-0.810) using an undocumented
method, and are NOT expressed in real percentage units. Feeding them in directly would
make every company clamp to nearly the same score component. To fix this without
fabricating data, these two columns are rank-quantile-mapped onto the score function's
own [worst, best] bounds (i.e. a company at the Nth percentile of the Taiwan
population's revenue_growth_pct gets mapped to the Nth percentile of [-20, 20]) — this
preserves each company's relative standing while giving the score formula's thresholds
something to actually discriminate on.
`debt_ratio`, `cash_ratio`, and `inventory_turnover` are NOT rescaled: their raw values
are already dimensionally compatible with the function's bounds (debt_ratio is a true
0-1 fraction matching worst=1/best=0; cash_ratio and inventory_turnover are real ratios
within [0,2] and [0,4] respectively, even if — per Study C — inventory_turnover carries
little real signal).

Caveat: `customer_growth_rate` (10 of the score's 100 points) has no equivalent in this
dataset (see DATASET.md) and is omitted, so every company gets the same fixed
contribution for that component — identical to how the real app behaves today for a
company that hasn't uploaded customer-count data. This means only 90 of 100 points are
doing discriminative work in this validation; that's reported explicitly, not hidden.

Outputs:
  - research/results/health_score_validation.md
  - research/results/health_score_by_company.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.ml.health_score import calculate_health_score  # noqa: E402

DATA_DIR = Path(__file__).parent / "datasets"
RESULTS_DIR = Path(__file__).parent / "results"
TARGET_COL = "Bankrupt?"

# Only columns confirmed scale-incompatible with calculate_health_score()'s assumed
# percentage bounds get rank-quantile-mapped; see module docstring for why the other
# three mapped features are used as-is.
QUANTILE_MAP_BOUNDS = {
    "revenue_growth_pct": (-20, 20),
    "profit_margin_pct": (-10, 25),
}


def rank_quantile_map(series: pd.Series, worst: float, best: float) -> pd.Series:
    rank = series.rank(pct=True)  # 0..1, preserves each company's relative standing
    return worst + rank * (best - worst)


def main() -> None:
    df = pd.read_csv(DATA_DIR / "production_subset_clean.csv")
    print(f"Scoring {len(df)} companies with the production calculate_health_score()...")

    for col, (worst, best) in QUANTILE_MAP_BOUNDS.items():
        df[f"{col}_mapped"] = rank_quantile_map(df[col], worst, best)

    scores, labels = [], []
    for _, row in df.iterrows():
        features = {
            "revenue_growth_pct": row["revenue_growth_pct_mapped"],
            "profit_margin_pct": row["profit_margin_pct_mapped"],
            "cash_ratio": row["cash_ratio"],
            "inventory_turnover": row["inventory_turnover"],
            "debt_ratio": row["debt_ratio"],
            # customer_growth_rate intentionally omitted — no equivalent in this dataset;
            # calculate_health_score() defaults it to 0, same as the real app would.
        }
        result = calculate_health_score(features)
        scores.append(result["score"])
        labels.append(result["label"])

    df["health_score"] = scores
    df["health_label"] = labels
    df.to_csv(RESULTS_DIR / "health_score_by_company.csv", index=False)

    bankrupt = df[df[TARGET_COL] == 1]["health_score"]
    solvent = df[df[TARGET_COL] == 0]["health_score"]

    # AUC: does a LOWER health score predict bankruptcy? Use -score as the "risk" signal.
    auc = roc_auc_score(df[TARGET_COL], -df["health_score"])
    point_biserial_r, p_value = stats.pointbiserialr(df[TARGET_COL], df["health_score"])
    t_stat, t_pvalue = stats.ttest_ind(solvent, bankrupt, equal_var=False)

    label_breakdown = (
        df.groupby("health_label")[TARGET_COL]
        .agg(["mean", "count"])
        .rename(columns={"mean": "bankruptcy_rate", "count": "n_companies"})
        .sort_values("bankruptcy_rate", ascending=False)
    )

    print(f"\nMean health score — bankrupt companies:  {bankrupt.mean():.2f}")
    print(f"Mean health score — solvent companies:    {solvent.mean():.2f}")
    print(f"Welch's t-test: t={t_stat:.3f}, p={t_pvalue:.2e}")
    print(f"Point-biserial correlation: r={point_biserial_r:.4f}, p={p_value:.2e}")
    print(f"ROC-AUC (health score predicting bankruptcy): {auc:.4f}")
    print()
    print("Bankruptcy rate by health score label:")
    print(label_breakdown)

    with open(RESULTS_DIR / "health_score_validation.md", "w") as f:
        f.write("# Study D: Business Health Score Validation\n\n")
        f.write("Validates `app/ml/health_score.py::calculate_health_score()` — the "
                "actual production function, imported directly — against real "
                "bankruptcy outcomes in the Taiwan dataset (n=6819).\n\n")
        f.write("**Caveat**: `customer_growth_rate` (10 of 100 points) has no "
                "equivalent in this dataset and defaults to a fixed value for every "
                "company (see `DATASET.md`), so this validates the 90 real points "
                "the other 5 components contribute, not the full 100-point formula.\n\n")
        f.write("## Summary statistics\n\n")
        f.write(f"| Group | Mean health score | N |\n|---|---|---|\n")
        f.write(f"| Bankrupt | {bankrupt.mean():.2f} | {len(bankrupt)} |\n")
        f.write(f"| Solvent | {solvent.mean():.2f} | {len(solvent)} |\n\n")
        f.write(f"- Welch's t-test (solvent vs. bankrupt mean score): "
                f"t={t_stat:.3f}, **p={t_pvalue:.2e}**\n")
        f.write(f"- Point-biserial correlation (score vs. bankruptcy): "
                f"r={point_biserial_r:.4f}, p={p_value:.2e}\n")
        f.write(f"- **ROC-AUC** (health score, inverted, as a bankruptcy-risk predictor): "
                f"**{auc:.4f}**\n\n")
        f.write("## Bankruptcy rate by health score label\n\n")
        f.write(label_breakdown.to_markdown(floatfmt=".4f"))
        f.write("\n\n")
        f.write("## Interpretation\n\n")
        if auc > 0.7:
            f.write(f"An AUC of {auc:.3f} indicates the health score has genuine, "
                    f"meaningful discriminative power for predicting real bankruptcy "
                    f"outcomes — well above the 0.5 no-skill baseline, using a "
                    f"transparent, interpretable weighted-rubric formula rather than "
                    f"a black-box model.\n")
        elif auc > 0.6:
            f.write(f"An AUC of {auc:.3f} indicates modest but real discriminative "
                    f"power — better than chance, but weaker than the dedicated ML "
                    f"classifier (Study A/B). This is expected: the health score is a "
                    f"fixed, interpretable linear rubric, while the classifier can "
                    f"learn non-linear interactions between features.\n")
        else:
            f.write(f"An AUC of {auc:.3f} is close to the 0.5 no-skill baseline, "
                    f"indicating the current weight distribution does not track real "
                    f"bankruptcy outcomes well on this dataset. This is a genuine "
                    f"negative result worth reporting as-is — it motivates either "
                    f"re-weighting the score's components or being explicit in the "
                    f"paper that the score is designed for early operational "
                    f"warning signals rather than bankruptcy prediction specifically.\n")

    print(f"\nWrote {RESULTS_DIR / 'health_score_validation.md'}")
    print(f"Wrote {RESULTS_DIR / 'health_score_by_company.csv'}")


if __name__ == "__main__":
    main()
