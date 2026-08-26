import re
import pandas as pd


def normalize_year(value):
    if isinstance(value, str) and value.strip().lower().startswith("june "):
        return None
    if pd.isna(value):
        return None

    value = str(value).strip()

    if not value:
        return None

    # FY 2023 / FY2020
    match = re.fullmatch(r"FY\s*(\d{4})", value, re.IGNORECASE)
    if match:
        return f"{match.group(1)}-03"

    # 2024-25
    match = re.fullmatch(r"(\d{4})-\d{2}", value)
    if match:
        return f"{match.group(1)}-03"

    # Month + year
    match = re.fullmatch(
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s/-]*(\d{2,4})",
        value,
        re.IGNORECASE,
    )

    if match:
        month = match.group(1).lower()[:3]
        year = match.group(2)

        if len(year) == 2:
            year = "20" + year

        months = {
            "jan": "01",
            "feb": "02",
            "mar": "03",
            "apr": "04",
            "may": "05",
            "jun": "06",
            "jul": "07",
            "aug": "08",
            "sep": "09",
            "oct": "10",
            "nov": "11",
            "dec": "12",
        }

        return f"{year}-{months[month]}"

    # Four-digit year
    match = re.fullmatch(r"\d{4}", value)
    if match:
        return f"{value}-03"

    return None


def normalize_ticker(value):
    if pd.isna(value):
        return None

    value = str(value).strip().upper()

    if not value:
        return None

    return value


def normalize_dataframe(df):
    df = df.copy()

    if "company_id" in df.columns:
        df["company_id"] = df["company_id"].apply(normalize_ticker)

    if "year" in df.columns:
        df["year"] = df["year"].apply(normalize_year)

    # DQ-02
    if "company_id" in df.columns and "year" in df.columns:
        df = df.dropna(subset=["company_id", "year"])

        df = df.drop_duplicates(
            subset=["company_id", "year"],
            keep="last"
        )

    return df