# Import every mapped model so Base.metadata is fully populated (for Alembic
# autogenerate, Base.metadata.create_all, and SQLAlchemy relationship resolution)
# whenever `app.models` is imported, without risking a circular import with
# app.database.base (which each model module imports Base from).
from app.models.user import User
from app.models.company import Company
from app.models.upload import Upload
from app.models.financial_data import FinancialData
from app.models.forecast import Forecast
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation
from app.models.report import Report

__all__ = [
    "User",
    "Company",
    "Upload",
    "FinancialData",
    "Forecast",
    "Prediction",
    "Recommendation",
    "Report",
]
