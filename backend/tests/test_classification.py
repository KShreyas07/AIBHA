from app.ml.classification import get_classifier, RealDataClassifier

HEALTHY_FEATURES = {
    "revenue_growth_pct": 8.0, "profit_margin_pct": 15.0, "operating_margin_pct": 12.0,
    "cash_ratio": 0.9, "current_ratio": 1.8, "debt_ratio": 0.2,
    "inventory_turnover": 2.0, "customer_growth_rate": 5.0,
}

DISTRESSED_FEATURES = {
    "revenue_growth_pct": -15.0, "profit_margin_pct": -5.0, "operating_margin_pct": -3.0,
    "cash_ratio": 0.05, "current_ratio": 0.6, "debt_ratio": 0.85,
    "inventory_turnover": 0.1, "customer_growth_rate": -10.0,
}


def test_classifier_loads_real_data_artifact():
    # If this is the synthetic fallback, the artifact wasn't trained — that's a setup
    # problem worth failing loudly on rather than silently testing the fallback.
    assert isinstance(get_classifier(), RealDataClassifier)


def test_predict_returns_expected_shape():
    result = get_classifier().predict(HEALTHY_FEATURES)
    assert result["health_class"] in {"Healthy", "Warning", "Critical"}
    assert 0 <= result["confidence"] <= 1
    assert 0 <= result["risk_probability"] <= 1
    assert result["model_used"] == "lightgbm"
    assert "model_comparison" in result


def test_healthy_profile_scores_lower_risk_than_distressed():
    healthy_result = get_classifier().predict(HEALTHY_FEATURES)
    distressed_result = get_classifier().predict(DISTRESSED_FEATURES)
    assert healthy_result["risk_probability"] < distressed_result["risk_probability"]
    assert healthy_result["health_class"] == "Healthy"
    assert distressed_result["health_class"] in {"Warning", "Critical"}


def test_predict_handles_missing_features_gracefully():
    # customer_growth_rate is deliberately unused by the real model but should still
    # be accepted without error for interface backward-compatibility.
    partial = {k: v for k, v in HEALTHY_FEATURES.items() if k != "customer_growth_rate"}
    result = get_classifier().predict(partial)
    assert result["health_class"] in {"Healthy", "Warning", "Critical"}


def test_explain_returns_ranked_factors_excluding_inventory_turnover():
    factors = get_classifier().explain(DISTRESSED_FEATURES, top_n=5)
    assert 1 <= len(factors) <= 5
    for factor in factors:
        assert factor["feature"] != "inventory_turnover"
        assert "label" in factor
        assert "shap_contribution" in factor
        assert isinstance(factor["increases_risk"], bool)
    # Ranked by absolute SHAP contribution, descending.
    magnitudes = [abs(f["shap_contribution"]) for f in factors]
    assert magnitudes == sorted(magnitudes, reverse=True)
