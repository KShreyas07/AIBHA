import pandas as pd
import pdfplumber

from app.utils.file_parser import normalize_columns


def extract_tables_from_pdf(file_path: str) -> pd.DataFrame:
    """Extract every table found across all pages of a PDF financial statement and
    concatenate rows that share a header row shape into one normalized DataFrame."""
    frames: list[pd.DataFrame] = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                if not table or len(table) < 2:
                    continue
                header, *rows = table
                header = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(header)]
                df = pd.DataFrame(rows, columns=header)
                frames.append(df)

    if not frames:
        raise ValueError("No tables could be extracted from the PDF. Please upload a text-based (non-scanned) PDF.")

    combined = pd.concat(frames, ignore_index=True, sort=False)
    return normalize_columns(combined)
