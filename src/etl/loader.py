from pathlib import Path
import pandas as pd

from src.etl.normaliser import normalize_dataframe


RAW_DIR = Path("data/raw")

CORE_FILES = {
    "companies": "companies.xlsx",
    "profitandloss": "profitandloss.xlsx",
    "balancesheet": "balancesheet.xlsx",
    "cashflow": "cashflow.xlsx",
    "analysis": "analysis.xlsx",
    "documents": "documents.xlsx",
    "prosandcons": "prosandcons.xlsx",
}

SUPPLEMENTARY_FILES = {
    "sectors": "sectors.xlsx",
    "peer_groups": "peer_groups.xlsx",
    "financial_ratios": "financial_ratios.xlsx",
    "stock_prices": "stock_prices.xlsx",
    "market_cap": "market_cap.xlsx",
}


def load_excel(filename, header=0):
    path = RAW_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    df = pd.read_excel(path, header=header)
    return normalize_dataframe(df)


def load_all():
    datasets = {}

    for table_name, filename in CORE_FILES.items():
        if table_name in ["companies", "cashflow"]:
            datasets[table_name] = load_excel(filename, header=0)
        else:
            datasets[table_name] = load_excel(filename, header=1)

    for table_name, filename in SUPPLEMENTARY_FILES.items():
        datasets[table_name] = load_excel(filename, header=0)

    return datasets


if __name__ == "__main__":
    data = load_all()

    print("\n=== DATASET SUMMARY ===")

    for name, df in data.items():
        print(f"{name:20} {len(df):>6} rows x {len(df.columns):>3} columns")

    print("\nLoader completed successfully.")