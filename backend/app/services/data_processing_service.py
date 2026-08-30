import uuid

import pandas as pd
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.database.session import SessionLocal
from app.ml.feature_engineering import engineer_features
from app.ml.preprocessing import clean_dataframe
from app.models.company import Company
from app.models.financial_data import FinancialData
from app.models.upload import Upload
from app.utils.file_parser import parse_tabular_file
from app.utils.pdf_extractor import extract_tables_from_pdf

logger = get_logger(__name__)

UPSERT_FIELDS = [
    "revenue", "cogs", "operating_expenses", "net_profit", "cash_balance",
    "current_assets", "current_liabilities", "total_debt", "total_equity",
    "inventory_value", "inventory_sold", "customers_count",
]


def _parse_upload_file(upload: Upload) -> pd.DataFrame:
    if upload.file_type == "pdf":
        return extract_tables_from_pdf(upload.file_path)
    return parse_tabular_file(upload.file_path)


def process_upload(db: Session, upload: Upload) -> None:
    """Parse one uploaded file, clean it, and merge its columns into the company's
    monthly FinancialData rows (only overwriting fields the file actually provided)."""
    upload.status = "processing"
    db.commit()

    try:
        raw_df = _parse_upload_file(upload)
        clean_df = clean_dataframe(raw_df)

        for _, row in clean_df.iterrows():
            period = row["period"].date()
            record = (
                db.query(FinancialData)
                .filter(FinancialData.company_id == upload.company_id, FinancialData.period == period)
                .first()
            )
            if record is None:
                record = FinancialData(company_id=upload.company_id, upload_id=upload.id, period=period)
                db.add(record)

            for field in UPSERT_FIELDS:
                if field in row and pd.notna(row[field]):
                    setattr(record, field, float(row[field]))

        upload.status = "processed"
        upload.error_message = None
        db.commit()
        recompute_engineered_features(db, upload.company_id)
        logger.info("Processed upload %s (%s rows)", upload.id, len(clean_df))
    except Exception as exc:  # noqa: BLE001 - surface any parsing/cleaning failure to the user
        db.rollback()
        upload.status = "failed"
        upload.error_message = str(exc)[:1000]
        db.commit()
        logger.exception("Failed to process upload %s", upload.id)


def process_upload_by_id(upload_id: uuid.UUID) -> None:
    """Entry point for background tasks: request-scoped sessions are closed by the time
    BackgroundTasks run, so this opens its own session rather than reusing a detached one."""
    db = SessionLocal()
    try:
        upload = db.get(Upload, upload_id)
        if upload is None:
            logger.error("Upload %s not found for background processing", upload_id)
            return
        process_upload(db, upload)
    finally:
        db.close()


def recompute_engineered_features(db: Session, company_id) -> pd.DataFrame:
    """Recompute revenue growth / margins / ratios across a company's full financial
    history whenever new data lands, since growth-rate features depend on prior periods."""
    records = (
        db.query(FinancialData)
        .filter(FinancialData.company_id == company_id)
        .order_by(FinancialData.period)
        .all()
    )
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame([
        {"period": r.period, **{f: float(getattr(r, f)) for f in UPSERT_FIELDS}}
        for r in records
    ])
    df["period"] = pd.to_datetime(df["period"])
    featured = engineer_features(df)

    ratio_fields = [
        "revenue_growth_pct", "profit_margin_pct", "operating_margin_pct", "cash_ratio",
        "current_ratio", "debt_ratio", "inventory_turnover", "customer_growth_rate",
    ]
    for record, (_, row) in zip(records, featured.iterrows()):
        for field in ratio_fields:
            value = row[field]
            setattr(record, field, float(value) if pd.notna(value) else None)

    db.commit()
    return featured


def get_company_financial_dataframe(db: Session, company_id) -> pd.DataFrame:
    records = (
        db.query(FinancialData)
        .filter(FinancialData.company_id == company_id)
        .order_by(FinancialData.period)
        .all()
    )
    if not records:
        return pd.DataFrame()

    all_fields = UPSERT_FIELDS + [
        "revenue_growth_pct", "profit_margin_pct", "operating_margin_pct", "cash_ratio",
        "current_ratio", "debt_ratio", "inventory_turnover", "customer_growth_rate",
    ]
    return pd.DataFrame([
        {"period": r.period, **{f: (float(v) if (v := getattr(r, f)) is not None else None) for f in all_fields}}
        for r in records
    ])
