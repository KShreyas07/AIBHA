from pathlib import Path

import pandas as pd

# Canonical field -> accepted header synonyms (lowercased, stripped).
COLUMN_SYNONYMS: dict[str, list[str]] = {
    "period": ["date", "period", "month", "reporting_date", "reporting period", "date/period", "period/date"],
    "revenue": ["revenue", "total revenue", "sales", "net sales", "total sales", "income"],
    "cogs": ["cogs", "cost of goods sold", "cost of sales"],
    "operating_expenses": ["operating_expenses", "operating expenses", "opex", "total expenses", "expenses"],
    "net_profit": ["net_profit", "net profit", "net income", "profit"],
    "cash_balance": ["cash_balance", "cash", "closing cash", "ending cash balance", "cash and cash equivalents"],
    "current_assets": ["current_assets", "current assets", "total current assets"],
    "current_liabilities": ["current_liabilities", "current liabilities", "total current liabilities"],
    "total_debt": ["total_debt", "total debt", "total liabilities", "debt"],
    "total_equity": ["total_equity", "total equity", "shareholders equity", "owner's equity"],
    "inventory_value": ["inventory_value", "inventory", "closing inventory", "ending inventory"],
    "inventory_sold": ["inventory_sold", "cogs (units)", "units sold", "inventory sold"],
    "customers_count": ["customers_count", "customers", "total customers", "active customers", "customer count"],
    "currency": ["currency", "curr"],
}

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".pdf"}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename arbitrary source headers to canonical field names using the synonym table.
    Unrecognized columns are dropped since the ML pipeline only understands canonical fields."""
    lookup: dict[str, str] = {}
    for canonical, synonyms in COLUMN_SYNONYMS.items():
        for s in synonyms:
            lookup[s.lower().strip()] = canonical

    rename_map = {}
    for col in df.columns:
        key = str(col).lower().strip()
        if key in lookup:
            rename_map[col] = lookup[key]

    df = df.rename(columns=rename_map)
    keep = [c for c in df.columns if c in COLUMN_SYNONYMS]
    return df[keep]


def parse_tabular_file(file_path: str) -> pd.DataFrame:
    ext = Path(file_path).suffix.lower()
    if ext == ".csv":
        df = pd.read_csv(file_path)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported tabular file extension: {ext}")

    if df.empty:
        raise ValueError("Uploaded file contains no rows")

    return normalize_columns(df)


def validate_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
    return ext
