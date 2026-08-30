"""Downloads a panel of real monthly business-revenue-style time series from FRED
(Federal Reserve Economic Data) for the forecast model comparison study.

The Taiwan bankruptcy dataset (used in Studies A-D) is cross-sectional — one snapshot
per company, no repeated time periods — so it cannot validate forecasting models at all
(documented in DATASET.md's limitations). This is a genuinely different data need: real,
long-history monthly series to backtest against.

Series chosen: six distinct US Census retail-trade sub-sectors, each published monthly
by FRED since the early 1990s (30+ years of history). Each acts as a stand-in for a
different SME industry vertical (general retail, food service, clothing, fuel,
furniture, electronics) — real seasonal, trending revenue-like data, not synthetic.

All series are public, no API key required, sourced directly from
https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES_ID>

Outputs: research/datasets/forecast_timeseries/<series_id>.csv
"""
from pathlib import Path

import pandas as pd

OUT_DIR = Path(__file__).parent / "datasets" / "forecast_timeseries"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SERIES = {
    "RSXFS": "Retail Trade (ex. Food Services) — general retail proxy",
    "RSFSDP": "Food Services & Drinking Places — restaurant/hospitality proxy",
    "RSCCAS": "Clothing & Clothing Accessory Stores",
    "RSGASS": "Gasoline Stations",
    "RSFHFS": "Furniture & Home Furnishings Stores",
    "RSEAS": "Electronics & Appliance Stores",
}

FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"


def download_series(series_id: str) -> pd.DataFrame:
    df = pd.read_csv(FRED_URL.format(series_id=series_id))
    df.columns = ["period", "value"]
    df["period"] = pd.to_datetime(df["period"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"]).reset_index(drop=True)
    return df


def main() -> None:
    manifest = []
    for series_id, description in SERIES.items():
        df = download_series(series_id)
        out_path = OUT_DIR / f"{series_id}.csv"
        df.to_csv(out_path, index=False)
        manifest.append({
            "series_id": series_id,
            "description": description,
            "n_months": len(df),
            "start": df["period"].min().strftime("%Y-%m"),
            "end": df["period"].max().strftime("%Y-%m"),
        })
        print(f"{series_id:10s} {description:55s} {len(df)} months "
              f"({df['period'].min().strftime('%Y-%m')} to {df['period'].max().strftime('%Y-%m')})")

    pd.DataFrame(manifest).to_csv(OUT_DIR / "manifest.csv", index=False)
    print(f"\nWrote manifest to {OUT_DIR / 'manifest.csv'}")


if __name__ == "__main__":
    main()
