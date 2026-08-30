import uuid

from scipy.stats import norm
from sqlalchemy.orm import Session

from app.ml.feature_engineering import summarize_features
from app.models.company import Company
from app.services.data_processing_service import get_company_financial_dataframe

# Approximate industry-average benchmarks (mean, std) for demo purposes.
# Replace with a live benchmarking data source/API in production.
INDUSTRY_BENCHMARKS: dict[str, dict[str, tuple[float, float]]] = {
    "retail": {"profit_margin_pct": (6.0, 4.0), "revenue_growth_pct": (4.0, 8.0), "cash_ratio": (0.5, 0.3), "operating_margin_pct": (7.0, 5.0), "inventory_turnover": (1.5, 0.8)},
    "technology": {"profit_margin_pct": (15.0, 8.0), "revenue_growth_pct": (12.0, 15.0), "cash_ratio": (1.2, 0.6), "operating_margin_pct": (18.0, 10.0), "inventory_turnover": (3.0, 1.5)},
    "manufacturing": {"profit_margin_pct": (8.0, 5.0), "revenue_growth_pct": (3.0, 6.0), "cash_ratio": (0.6, 0.3), "operating_margin_pct": (9.0, 5.0), "inventory_turnover": (2.0, 1.0)},
    "food & beverage": {"profit_margin_pct": (5.0, 4.0), "revenue_growth_pct": (5.0, 7.0), "cash_ratio": (0.4, 0.25), "operating_margin_pct": (6.0, 4.0), "inventory_turnover": (4.0, 2.0)},
    "services": {"profit_margin_pct": (12.0, 7.0), "revenue_growth_pct": (6.0, 8.0), "cash_ratio": (0.8, 0.4), "operating_margin_pct": (14.0, 8.0), "inventory_turnover": (0.5, 0.4)},
    "default": {"profit_margin_pct": (8.0, 6.0), "revenue_growth_pct": (5.0, 8.0), "cash_ratio": (0.6, 0.35), "operating_margin_pct": (9.0, 6.0), "inventory_turnover": (1.5, 1.0)},
}


def get_benchmark(db: Session, company: Company) -> dict:
    df = get_company_financial_dataframe(db, company.id)
    if df.empty:
        raise ValueError("No processed financial data available for this company yet")

    features = summarize_features(df)
    industry_key = company.industry.strip().lower()
    benchmarks = INDUSTRY_BENCHMARKS.get(industry_key, INDUSTRY_BENCHMARKS["default"])

    results = {}
    for metric, (mean, std) in benchmarks.items():
        company_value = features.get(metric, 0) or 0
        percentile = round(float(norm.cdf((company_value - mean) / std)) * 100, 1)
        results[metric] = {
            "company_value": round(company_value, 2),
            "industry_average": mean,
            "percentile": percentile,
        }

    return {"industry": company.industry, "metrics": results}
