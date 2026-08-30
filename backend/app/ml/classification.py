"""Business Health Classification: Healthy / Warning / Critical.

Loads a LightGBM model trained offline on real company outcomes — the Taiwanese
Bankruptcy Prediction dataset (UCI ML Repository 572, DOI 10.24432/C5004D) — selected
after comparing RandomForest, XGBoost, LightGBM, and CatBoost on that real data
(backend/research/train_full_comparison.py, Study A/B; LightGBM won on PR-AUC).
See backend/app/ml/train_bankruptcy_classifier.py to retrain, and
backend/research/DATASET.md for the full data provenance and feature-mapping caveats.

This replaces an earlier version that trained on a synthetically generated, rule-labeled
dataset (kept below as `_SyntheticFallbackClassifier`, used only if the real artifact is
missing, e.g. a fresh checkout before running the training script).
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from app.core.logging import get_logger

logger = get_logger(__name__)

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "bankruptcy_classifier.joblib"
META_PATH = ARTIFACTS_DIR / "bankruptcy_classifier_meta.json"

# Full interface accepted from callers (matches summarize_features() output);
# `customer_growth_rate` has no equivalent in the training dataset and is accepted for
# backward compatibility but not used by the real model — see DATASET.md.
FEATURE_ORDER = [
    "revenue_growth_pct", "profit_margin_pct", "operating_margin_pct",
    "cash_ratio", "current_ratio", "debt_ratio", "inventory_turnover",
    "customer_growth_rate",
]
CLASSES = ["Critical", "Warning", "Healthy"]

FEATURE_LABELS = {
    "current_ratio": "Current Ratio",
    "debt_ratio": "Debt Ratio",
    "cash_ratio": "Cash Ratio",
    "inventory_turnover": "Inventory Turnover",
    "operating_margin_pct": "Operating Margin",
    "profit_margin_pct": "Profit Margin",
    "revenue_growth_pct": "Revenue Growth",
}

# `inventory_turnover` is deliberately excluded from user-facing explanations: Study C
# (research/shap_analysis.py) found it has negative permutation importance — shuffling
# it doesn't hurt held-out performance, meaning the model isn't actually relying on real
# signal from it despite sometimes showing non-trivial SHAP values for a given
# prediction. The model still uses it internally (dropping it would mean retraining),
# but we don't present it to users as a trustworthy "reason".
EXPLANATION_EXCLUDED_FEATURES = {"inventory_turnover"}


class RealDataClassifier:
    """Wraps the LightGBM model trained on real bankruptcy outcomes."""

    def __init__(self) -> None:
        self._model = joblib.load(MODEL_PATH)
        with open(META_PATH) as f:
            self._meta = json.load(f)
        self._model_feature_order = self._meta["feature_order"]
        self._warning_threshold = self._meta["warning_threshold"]
        self._critical_threshold = self._meta["critical_threshold"]
        self._shap_explainer = None  # lazy — shap import/init is relatively expensive
        logger.info(
            "Loaded real-data bankruptcy classifier (LightGBM, trained %s, "
            "test ROC-AUC=%.4f, PR-AUC=%.4f)",
            self._meta["trained_at"], self._meta["test_metrics"]["roc_auc"],
            self._meta["test_metrics"]["pr_auc"],
        )

    def predict(self, features: dict) -> dict:
        row = pd.DataFrame(
            [[features.get(f, 0) or 0 for f in self._model_feature_order]],
            columns=self._model_feature_order,
        )
        risk_probability = float(self._model.predict_proba(row)[0][1])

        if risk_probability >= self._critical_threshold:
            health_class = "Critical"
            confidence = risk_probability
        elif risk_probability >= self._warning_threshold:
            health_class = "Warning"
            confidence = risk_probability
        else:
            health_class = "Healthy"
            confidence = 1 - risk_probability

        return {
            "health_class": health_class,
            "confidence": round(confidence, 4),
            "risk_probability": round(risk_probability, 5),
            "model_used": "lightgbm",
            "model_comparison": {
                "algorithm": self._meta["algorithm"],
                "validated_on": self._meta["source_dataset"],
                "test_roc_auc": self._meta["test_metrics"]["roc_auc"],
                "test_pr_auc": self._meta["test_metrics"]["pr_auc"],
                "note": "Selected by comparing RandomForest/XGBoost/LightGBM/CatBoost "
                        "on real outcomes — see research/results/full_comparison_report.md",
            },
        }

    def explain(self, features: dict, top_n: int = 3) -> list[dict]:
        """Top SHAP-contributing factors behind this company's risk prediction —
        "Risk Score = 84%, Reasons: ..." instead of a bare label. See
        research/shap_analysis.py (Study C) for the validation behind this."""
        import shap

        if self._shap_explainer is None:
            self._shap_explainer = shap.TreeExplainer(self._model)

        row = pd.DataFrame(
            [[features.get(f, 0) or 0 for f in self._model_feature_order]],
            columns=self._model_feature_order,
        )
        shap_values = self._shap_explainer.shap_values(row)
        if isinstance(shap_values, list):
            shap_values = shap_values[1]  # positive (at-risk) class contribution
        contributions = shap_values[0]

        ranked = sorted(
            zip(self._model_feature_order, contributions, row.iloc[0].values),
            key=lambda t: abs(t[1]),
            reverse=True,
        )
        factors = [
            {
                "feature": feature,
                "label": FEATURE_LABELS.get(feature, feature),
                "value": round(float(value), 4),
                "shap_contribution": round(float(contribution), 4),
                "increases_risk": bool(contribution > 0),
            }
            for feature, contribution, value in ranked
            if feature not in EXPLANATION_EXCLUDED_FEATURES
        ]
        return factors[:top_n]


# --- Fallback: only used if the real-data artifact hasn't been trained yet. ---

def _label_row(row: pd.Series) -> str:
    score = 0
    score += 1 if row["revenue_growth_pct"] > 0 else (-1 if row["revenue_growth_pct"] < -10 else 0)
    score += 1 if row["profit_margin_pct"] > 8 else (-1 if row["profit_margin_pct"] < 0 else 0)
    score += 1 if row["cash_ratio"] > 0.5 else (-1 if row["cash_ratio"] < 0.1 else 0)
    score += 1 if row["current_ratio"] > 1.2 else (-1 if row["current_ratio"] < 0.8 else 0)
    score += 1 if row["debt_ratio"] < 0.4 else (-1 if row["debt_ratio"] > 0.7 else 0)
    score += 1 if row["inventory_turnover"] > 1 else (-1 if row["inventory_turnover"] < 0.3 else 0)

    if score >= 3:
        return "Healthy"
    if score <= -2:
        return "Critical"
    return "Warning"


def generate_synthetic_dataset(n: int = 4000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "revenue_growth_pct": rng.normal(3, 12, n),
        "profit_margin_pct": rng.normal(7, 10, n),
        "operating_margin_pct": rng.normal(6, 9, n),
        "cash_ratio": np.abs(rng.normal(0.6, 0.5, n)),
        "current_ratio": np.abs(rng.normal(1.3, 0.6, n)),
        "debt_ratio": np.clip(rng.normal(0.4, 0.25, n), 0, 1.5),
        "inventory_turnover": np.abs(rng.normal(1.2, 0.9, n)),
        "customer_growth_rate": rng.normal(2, 8, n),
    })
    df["health_class"] = df.apply(_label_row, axis=1)
    return df


class _SyntheticFallbackClassifier:
    """Trains on synthetic, rule-labeled data. Only used if the real artifact
    (app/ml/artifacts/bankruptcy_classifier.joblib) hasn't been built yet — run
    `python3 -m app.ml.train_bankruptcy_classifier` to replace this with real data."""

    def __init__(self) -> None:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import accuracy_score
        from sklearn.model_selection import train_test_split
        from xgboost import XGBClassifier

        logger.warning(
            "Real-data classifier artifact not found at %s — falling back to a "
            "synthetic, rule-labeled classifier. Run "
            "`python3 -m app.ml.train_bankruptcy_classifier` to fix this.", MODEL_PATH,
        )

        data = generate_synthetic_dataset()
        X, y = data[FEATURE_ORDER], data["health_class"]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        rf = RandomForestClassifier(n_estimators=200, max_depth=8, random_state=42)
        rf.fit(X_train, y_train)
        rf_acc = accuracy_score(y_test, rf.predict(X_test))

        y_train_enc = y_train.map({c: i for i, c in enumerate(CLASSES)})
        y_test_enc = y_test.map({c: i for i, c in enumerate(CLASSES)})
        xgb = XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.1, eval_metric="mlogloss", random_state=42)
        xgb.fit(X_train, y_train_enc)
        xgb_acc = accuracy_score(y_test_enc, xgb.predict(X_test))

        self._metrics = {"random_forest_accuracy": round(rf_acc, 4), "xgboost_accuracy": round(xgb_acc, 4)}
        if xgb_acc >= rf_acc:
            self._model, self._model_name = xgb, "xgboost"
        else:
            self._model, self._model_name = rf, "random_forest"

    def predict(self, features: dict) -> dict:
        row = pd.DataFrame([[features.get(f, 0) or 0 for f in FEATURE_ORDER]], columns=FEATURE_ORDER)
        proba = self._model.predict_proba(row)[0]
        classes = CLASSES if self._model_name == "xgboost" else list(self._model.classes_)
        best_idx = int(np.argmax(proba))
        return {
            "health_class": classes[best_idx],
            "confidence": round(float(proba[best_idx]), 4),
            "model_used": self._model_name,
            "model_comparison": {**self._metrics, "note": "SYNTHETIC DATA FALLBACK — not real-data-validated"},
        }


_classifier = None


def get_classifier():
    global _classifier
    if _classifier is None:
        if MODEL_PATH.exists() and META_PATH.exists():
            _classifier = RealDataClassifier()
        else:
            _classifier = _SyntheticFallbackClassifier()
    return _classifier
