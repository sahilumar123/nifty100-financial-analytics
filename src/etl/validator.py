from pathlib import Path
import re
import pandas as pd

from src.etl.loader import load_all


OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def add_failure(
    failures,
    rule,
    severity,
    dataset,
    message,
    company_id=None,
    year=None,
):
    failures.append(
        {
            "rule_id": rule,
            "severity": severity,
            "dataset": dataset,
            "company_id": company_id,
            "year": year,
            "message": message,
        }
    )


# ============================================================
# DQ-01: Primary Key Uniqueness
# ============================================================

def validate_pk_uniqueness(data, failures):
    df = data["companies"]

    duplicates = df[df["id"].duplicated(keep=False)]

    for _, row in duplicates.iterrows():
        add_failure(
            failures,
            "DQ-01",
            "CRITICAL",
            "companies",
            "Duplicate company primary key",
            row["id"],
        )


# ============================================================
# DQ-02: (company_id, year) Uniqueness
# ============================================================

def validate_annual_pk(data, failures):
    tables = [
        "profitandloss",
        "balancesheet",
        "cashflow",
        "financial_ratios",
        "market_cap",
    ]

    for table in tables:
        df = data[table]

        if not {"company_id", "year"}.issubset(df.columns):
            continue

        valid_years = df[df["year"].notna()].copy()

        duplicates = valid_years[
        valid_years.duplicated(
        ["company_id", "year"],
        keep=False
          )
         ]        

        for _, row in duplicates.iterrows():
            add_failure(
                failures,
                "DQ-02",
                "CRITICAL",
                table,
                "Duplicate (company_id, year)",
                row["company_id"],
                row["year"],
            )


# ============================================================
# DQ-03: Foreign Key Integrity
# ============================================================

def validate_fk(data, failures):
    companies = set(
        data["companies"]["id"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
    )

    child_tables = [
        "profitandloss",
        "balancesheet",
        "cashflow",
        "analysis",
        "documents",
        "prosandcons",
        "sectors",
        "peer_groups",
        "financial_ratios",
        "stock_prices",
        "market_cap",
    ]

    for table in child_tables:
        df = data[table]

        if "company_id" not in df.columns:
            continue

        for _, row in df.iterrows():
            company_id = row["company_id"]

            if pd.isna(company_id):
                continue

            company_id = str(company_id).strip().upper()

            if company_id not in companies:
                add_failure(
                    failures,
                    "DQ-03",
                    "CRITICAL",
                    table,
                    "Orphan company_id",
                    company_id,
                    row.get("year"),
                )


# ============================================================
# DQ-04: Balance Sheet Balance
# ============================================================

def validate_balance_sheet(data, failures):
    df = data["balancesheet"]

    for _, row in df.iterrows():
        assets = row.get("total_assets")
        liabilities = row.get("total_liabilities")

        if (
            pd.notna(assets)
            and pd.notna(liabilities)
            and assets != 0
        ):
            difference = abs(assets - liabilities) / abs(assets)

            if difference >= 0.01:
                add_failure(
                    failures,
                    "DQ-04",
                    "WARNING",
                    "balancesheet",
                    f"Balance difference = {difference:.2%}",
                    row["company_id"],
                    row["year"],
                )


# ============================================================
# DQ-05: Operating Profit Margin Cross-check
# ============================================================

def validate_opm(data, failures):
    df = data["profitandloss"]

    for _, row in df.iterrows():
        sales = row.get("sales")
        operating_profit = row.get("operating_profit")
        source_opm = row.get("opm_percentage")

        if (
            pd.notna(sales)
            and sales != 0
            and pd.notna(operating_profit)
            and pd.notna(source_opm)
        ):
            calculated_opm = (
                operating_profit / sales
            ) * 100

            if abs(source_opm - calculated_opm) >= 1:
                add_failure(
                    failures,
                    "DQ-05",
                    "WARNING",
                    "profitandloss",
                    (
                        f"OPM mismatch: "
                        f"source={source_opm}, "
                        f"calculated={calculated_opm:.2f}"
                    ),
                    row["company_id"],
                    row["year"],
                )


# ============================================================
# DQ-06: Positive Sales
# ============================================================

def validate_sales(data, failures):
    df = data["profitandloss"]

    for _, row in df.iterrows():
        sales = row.get("sales")

        if pd.notna(sales) and sales <= 0:
            add_failure(
                failures,
                "DQ-06",
                "WARNING",
                "profitandloss",
                "Sales <= 0",
                row["company_id"],
                row["year"],
            )


# ============================================================
# DQ-07: Year Format YYYY-MM
# ============================================================

def validate_year_format(data, failures):
    tables = [
        "profitandloss",
        "balancesheet",
        "cashflow",
        "financial_ratios",
        "market_cap",
    ]

    pattern = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

    for table in tables:
        df = data[table]

        if "year" not in df.columns:
            continue

        for _, row in df.iterrows():
            value = row["year"]

            if pd.isna(value) or not pattern.fullmatch(str(value)):
                add_failure(
                    failures,
                    "DQ-07",
                    "CRITICAL",
                    table,
                    f"Invalid year format: {value}",
                    row.get("company_id"),
                    value,
                )


# ============================================================
# DQ-08: Ticker Format
# ============================================================

def validate_ticker_format(data, failures):
    for table, df in data.items():
        if "company_id" not in df.columns:
            continue

        for _, row in df.iterrows():
            ticker = row["company_id"]

            if pd.isna(ticker):
                add_failure(
                    failures,
                    "DQ-08",
                    "CRITICAL",
                    table,
                    "Missing company ticker",
                    ticker,
                    row.get("year"),
                )
                continue

            ticker = str(ticker).strip()

            if not 2 <= len(ticker) <= 12:
                add_failure(
                    failures,
                    "DQ-08",
                    "CRITICAL",
                    table,
                    "Ticker length outside 2-12 characters",
                    ticker,
                    row.get("year"),
                )


# ============================================================
# DQ-09: Net Cash Flow Check
# ============================================================

def validate_net_cash(data, failures):
    df = data["cashflow"]

    for _, row in df.iterrows():
        operating = row.get("operating_activity")
        investing = row.get("investing_activity")
        financing = row.get("financing_activity")
        net_cash = row.get("net_cash_flow")

        if all(
            pd.notna(value)
            for value in [
                operating,
                investing,
                financing,
                net_cash,
            ]
        ):
            calculated = (
                operating
                + investing
                + financing
            )

            if abs(net_cash - calculated) > 10:
                add_failure(
                    failures,
                    "DQ-09",
                    "WARNING",
                    "cashflow",
                    (
                        f"Net cash mismatch: "
                        f"source={net_cash}, "
                        f"calculated={calculated}"
                    ),
                    row["company_id"],
                    row["year"],
                )


# ============================================================
# DQ-10: Fixed Assets
# ============================================================

def validate_fixed_assets(data, failures):
    df = data["balancesheet"]

    for _, row in df.iterrows():
        fixed_assets = row.get("fixed_assets")

        if pd.notna(fixed_assets) and fixed_assets < 0:
            add_failure(
                failures,
                "DQ-10",
                "WARNING",
                "balancesheet",
                "Negative fixed assets",
                row["company_id"],
                row["year"],
            )


# ============================================================
# DQ-11: Tax Rate
# ============================================================

def validate_tax(data, failures):
    df = data["profitandloss"]

    for _, row in df.iterrows():
        tax = row.get("tax_percentage")

        if pd.notna(tax) and not 0 <= tax <= 60:
            add_failure(
                failures,
                "DQ-11",
                "WARNING",
                "profitandloss",
                f"Tax percentage outside 0-60: {tax}",
                row["company_id"],
                row["year"],
            )


# ============================================================
# DQ-12: Dividend Payout
# ============================================================

def validate_dividend(data, failures):
    df = data["profitandloss"]

    for _, row in df.iterrows():
        dividend = row.get("dividend_payout")

        if pd.notna(dividend) and dividend > 200:
            add_failure(
                failures,
                "DQ-12",
                "WARNING",
                "profitandloss",
                f"Dividend payout > 200%: {dividend}",
                row["company_id"],
                row["year"],
            )


# ============================================================
# DQ-13: URL Validation
# ============================================================

def validate_urls(data, failures):
    df = data["documents"]

    # Detect actual column name safely
    url_column = None

    for column in df.columns:
        if str(column).lower() in [
            "annual_report",
            "annual_report_url",
            "url",
        ]:
            url_column = column
            break

    if url_column is None:
        return

    for _, row in df.iterrows():
        url = row.get(url_column)

        if (
            pd.isna(url)
            or not str(url).startswith(
                ("http://", "https://")
            )
        ):
            add_failure(
                failures,
                "DQ-13",
                "WARNING",
                "documents",
                "Invalid or missing Annual Report URL",
                row.get("company_id"),
                row.get("year"),
            )


# ============================================================
# DQ-14: EPS Sign
# ============================================================

def validate_eps(data, failures):
    df = data["profitandloss"]

    for _, row in df.iterrows():
        net_profit = row.get("net_profit")
        eps = row.get("eps")

        if (
            pd.notna(net_profit)
            and pd.notna(eps)
            and net_profit > 0
            and eps <= 0
        ):
            add_failure(
                failures,
                "DQ-14",
                "WARNING",
                "profitandloss",
                "EPS <= 0 while net profit > 0",
                row["company_id"],
                row["year"],
            )


# ============================================================
# DQ-15: Balance Sheet Equality
# ============================================================

def validate_bse_balance(data, failures):
    df = data["balancesheet"]

    for _, row in df.iterrows():
        assets = row.get("total_assets")
        liabilities = row.get("total_liabilities")

        if (
            pd.notna(assets)
            and pd.notna(liabilities)
            and assets != liabilities
        ):
            add_failure(
                failures,
                "DQ-15",
                "INFO",
                "balancesheet",
                "Total assets != total liabilities",
                row["company_id"],
                row["year"],
            )


# ============================================================
# DQ-16: Year Coverage
# ============================================================

def validate_coverage(data, failures):
    companies = data["companies"]

    for company_id in companies["id"]:
        coverage = []

        for table in [
            "profitandloss",
            "balancesheet",
            "cashflow",
        ]:
            df = data[table]

            count = (
                df[df["company_id"] == company_id]["year"]
                .nunique()
            )

            coverage.append(count)

        if any(count < 5 for count in coverage):
            add_failure(
                failures,
                "DQ-16",
                "WARNING",
                "coverage",
                (
                    "Year coverage "
                    f"P&L/BS/CF = {coverage}"
                ),
                company_id,
            )


# ============================================================
# RUN ALL 16 RULES
# ============================================================

def validate_all(data):
    failures = []

    validate_pk_uniqueness(data, failures)
    validate_annual_pk(data, failures)
    validate_fk(data, failures)
    validate_balance_sheet(data, failures)
    validate_opm(data, failures)
    validate_sales(data, failures)
    validate_year_format(data, failures)
    validate_ticker_format(data, failures)
    validate_net_cash(data, failures)
    validate_fixed_assets(data, failures)
    validate_tax(data, failures)
    validate_dividend(data, failures)
    validate_urls(data, failures)
    validate_eps(data, failures)
    validate_bse_balance(data, failures)
    validate_coverage(data, failures)

    return pd.DataFrame(failures)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("NIFTY 100 DATA QUALITY VALIDATION")
    print("=" * 60)

    print("\nLoading datasets...")

    data = load_all()

    print("\nRunning DQ-01 to DQ-16...")

    failures = validate_all(data)

    output_file = (
        OUTPUT_DIR / "validation_failures.csv"
    )

    failures.to_csv(
        output_file,
        index=False,
    )

    print("\nValidation complete.")
    print(f"Total failures: {len(failures)}")
    print(f"Output file: {output_file}")

    if not failures.empty:

        print("\nFailures by rule:")

        print(
            failures
            .groupby(["rule_id", "severity"])
            .size()
            .to_string()
        )

        print("\nFailures by severity:")

        print(
            failures["severity"]
            .value_counts()
            .to_string()
        )

    else:
        print("\nNo validation failures found.")