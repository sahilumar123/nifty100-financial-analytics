from pathlib import Path
import sqlite3
import math

import pandas as pd

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    roe,
    roce,
    roa,
    debt_to_equity,
    high_leverage_flag,
    interest_coverage,
    icr_label,
    icr_warning,
    net_debt,
    asset_turnover,
)

from src.analytics.cagr import calculate_cagr

from src.analytics.cashflow_kpis import (
    free_cash_flow,
    cfo_quality_score,
    cfo_quality_label,
    capex_intensity,
    capex_intensity_label,
    fcf_conversion_rate,
    capital_allocation_pattern,
)


DB_PATH = Path("data/database/nifty100.db")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def clean_columns(df):
    df.columns = [
        str(c).strip().lower().replace(" ", "_")
        for c in df.columns
    ]
    return df


def find_column(df, candidates):
    for col in candidates:
        if col in df.columns:
            return col
    return None


def numeric(df, column):
    if column and column in df.columns:
        return pd.to_numeric(df[column], errors="coerce")
    return pd.Series([0.0] * len(df), index=df.index)


def load_tables(conn):
    tables = {}

    for table in [
        "companies",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "financial_ratios",
        "sectors",
    ]:
        tables[table] = pd.read_sql(
            f'SELECT * FROM "{table}"',
            conn
        )
        tables[table] = clean_columns(tables[table])

    return tables


def prepare_data(tables):

    pnl = tables["profitandloss"]
    bs = tables["balancesheet"]
    cf = tables["cashflow"]
    companies = tables["companies"]
    sectors = tables["sectors"]

    key = ["company_id", "year"]

    # Rename possible column variations
    def rename_if_exists(df, mapping):
        existing = {}
        for new_name, candidates in mapping.items():
            found = find_column(df, candidates)
            if found:
                existing[found] = new_name

        return df.rename(columns=existing)

    pnl = rename_if_exists(
        pnl,
        {
            "sales": ["sales", "revenue", "revenue_cr"],
            "net_profit": ["net_profit", "pat"],
            "eps": ["eps", "earnings_per_share"],
            "operating_profit": [
                "operating_profit",
                "op_profit",
            ],
        },
    )

    bs = rename_if_exists(
        bs,
        {
            "equity_capital": [
                "equity_capital",
                "equity",
            ],
            "reserves": [
                "reserves",
                "reserves_surplus",
            ],
            "borrowings": [
                "borrowings",
                "total_borrowings",
                "debt",
            ],
            "total_assets": [
                "total_assets",
                "assets",
            ],
            "investments": [
                "investments",
            ],
            "book_value_per_share": [
                "book_value_per_share",
                "book_value",
            ],
            "dividend_payout_ratio_pct": [
                "dividend_payout_ratio_pct",
                "dividend_payout",
            ],
        },
    )

    cf = rename_if_exists(
        cf,
        {
            "operating_activity": [
                "operating_activity",
                "cash_from_operating_activity",
                "cash_from_operations",
                "cfo",
            ],
            "investing_activity": [
                "investing_activity",
                "cash_from_investing_activity",
                "cfi",
            ],
            "financing_activity": [
                "financing_activity",
                "cash_from_financing_activity",
                "cff",
            ],
        },
    )

    companies = rename_if_exists(
        companies,
        {
            "roce_percentage": [
                "roce_percentage",
                "roce_pct",
            ],
            "roe_percentage": [
                "roe_percentage",
                "roe_pct",
            ],
        },
    )

    sectors = rename_if_exists(
        sectors,
        {
            "broad_sector": [
                "broad_sector",
                "sector",
            ],
        },
    )

    # Ensure keys exist
    for df in [pnl, bs, cf]:
        for k in key:
            if k not in df.columns:
                raise ValueError(
                    f"Required column {k} missing"
                )

    # Keep one record per company/year
    pnl = pnl.drop_duplicates(key)
    bs = bs.drop_duplicates(key)
    cf = cf.drop_duplicates(key)

    base = pnl.copy()

    bs_cols = key + [
        c for c in [
            "equity_capital",
            "reserves",
            "borrowings",
            "total_assets",
            "investments",
            "book_value_per_share",
            "dividend_payout_ratio_pct",
        ]
        if c in bs.columns
    ]

    cf_cols = key + [
        c for c in [
            "operating_activity",
            "investing_activity",
            "financing_activity",
        ]
        if c in cf.columns
    ]

    base = base.merge(
        bs[bs_cols],
        on=key,
        how="left",
        suffixes=("", "_bs"),
    )

    base = base.merge(
        cf[cf_cols],
        on=key,
        how="left",
        suffixes=("", "_cf"),
    )

    if "broad_sector" in sectors.columns:
        sector_cols = ["company_id", "broad_sector"]
        sector_df = sectors[sector_cols].drop_duplicates(
            "company_id"
        )
        base = base.merge(
            sector_df,
            on="company_id",
            how="left",
        )
    else:
        base["broad_sector"] = None

    return base


def calculate_ratios(df):

    results = []

    for company_id, group in df.groupby("company_id"):
        group = group.copy()

        group["_year_sort"] = group["year"].astype(str)
        group = group.sort_values("_year_sort")

        for _, row in group.iterrows():

            sales = row.get("sales")
            net_profit = row.get("net_profit")
            operating_profit = row.get("operating_profit")

            equity = row.get("equity_capital")
            reserves = row.get("reserves")
            borrowings = row.get("borrowings")
            assets = row.get("total_assets")
            investments = row.get("investments")

            cfo = row.get("operating_activity")
            cfi = row.get("investing_activity")
            cff = row.get("financing_activity")

            sales = 0 if pd.isna(sales) else sales
            net_profit = 0 if pd.isna(net_profit) else net_profit
            operating_profit = (
                0 if pd.isna(operating_profit)
                else operating_profit
            )

            equity = 0 if pd.isna(equity) else equity
            reserves = 0 if pd.isna(reserves) else reserves
            borrowings = 0 if pd.isna(borrowings) else borrowings
            assets = 0 if pd.isna(assets) else assets
            investments = 0 if pd.isna(investments) else investments

            cfo = 0 if pd.isna(cfo) else cfo
            cfi = 0 if pd.isna(cfi) else cfi
            cff = 0 if pd.isna(cff) else cff

            npm = net_profit_margin(net_profit, sales)
            opm = operating_profit_margin(
                operating_profit,
                sales
            )

            roe_value = roe(
                net_profit,
                equity,
                reserves
            )

            roce_value = roce(
                operating_profit,
                equity,
                reserves,
                borrowings
            )

            roa_value = roa(
                net_profit,
                assets
            )

            de = debt_to_equity(
                borrowings,
                equity,
                reserves
            )

            leverage_flag = high_leverage_flag(
                de,
                row.get("broad_sector")
            )

            # Interest is not guaranteed to exist in every source
            interest = row.get("interest", 0)
            other_income = row.get("other_income", 0)

            if pd.isna(interest):
                interest = 0

            if pd.isna(other_income):
                other_income = 0

            icr = interest_coverage(
                operating_profit,
                other_income,
                interest
            )

            fcf = free_cash_flow(cfo, cfi)

            cfo_score = cfo_quality_score(
                cfo,
                net_profit
            )

            capex = capex_intensity(
                cfi,
                sales
            )

            conversion = fcf_conversion_rate(
                fcf,
                operating_profit
            )

            pattern = capital_allocation_pattern(
                cfo,
                cfi,
                cff,
                cfo_score
            )

            record = row.to_dict()

            record.update({
                "net_profit_margin_pct": npm,
                "operating_profit_margin_pct": opm,
                "return_on_equity_pct": roe_value,
                "return_on_capital_employed_pct": roce_value,
                "return_on_assets_pct": roa_value,
                "debt_to_equity": de,
                "high_leverage_flag": leverage_flag,
                "interest_coverage": icr,
                "icr_label": icr_label(icr),
                "icr_warning_flag": icr_warning(icr),
                "net_debt_cr": net_debt(
                    borrowings,
                    investments
                ),
                "asset_turnover": asset_turnover(
                    sales,
                    assets
                ),
                "free_cash_flow_cr": fcf,
                "cash_from_operations_cr": cfo,
                "capex_cr": abs(cfi),
                "capex_intensity_pct": capex,
                "capex_intensity_label":
                    capex_intensity_label(capex),
                "fcf_conversion_rate_pct": conversion,
                "cfo_quality_score": cfo_score,
                "cfo_quality_label":
                    cfo_quality_label(cfo_score),
                "capital_allocation_pattern": pattern,
                "earnings_per_share": row.get("eps"),
                "book_value_per_share":
                    row.get("book_value_per_share"),
                "dividend_payout_ratio_pct":
                    row.get("dividend_payout_ratio_pct"),
                "total_debt_cr": borrowings,
            })

            results.append(record)

    return pd.DataFrame(results)


def add_cagrs(df):

    df["revenue_cagr_3yr"] = None
    df["revenue_cagr_3yr_flag"] = None

    df["revenue_cagr_5yr"] = None
    df["revenue_cagr_5yr_flag"] = None

    df["revenue_cagr_10yr"] = None
    df["revenue_cagr_10yr_flag"] = None

    df["pat_cagr_3yr"] = None
    df["pat_cagr_3yr_flag"] = None

    df["pat_cagr_5yr"] = None
    df["pat_cagr_5yr_flag"] = None

    df["pat_cagr_10yr"] = None
    df["pat_cagr_10yr_flag"] = None

    df["eps_cagr_3yr"] = None
    df["eps_cagr_3yr_flag"] = None

    df["eps_cagr_5yr"] = None
    df["eps_cagr_5yr_flag"] = None

    df["eps_cagr_10yr"] = None
    df["eps_cagr_10yr_flag"] = None

    for company_id, idx in df.groupby(
        "company_id"
    ).groups.items():

        group = df.loc[idx].copy()
        group = group.sort_values("year")

        for metric, prefix in [
            ("sales", "revenue"),
            ("net_profit", "pat"),
            ("eps", "eps"),
        ]:

            if metric not in group.columns:
                continue

            values = pd.to_numeric(
                group[metric],
                errors="coerce"
            )

            for years in [3, 5, 10]:

                if len(values) < years + 1:
                    value, flag = (
                        None,
                        "INSUFFICIENT"
                    )
                else:
                    start = values.iloc[-(years + 1)]
                    end = values.iloc[-1]

                    value, flag = calculate_cagr(
                        start,
                        end,
                        years
                    )

                value_col = f"{prefix}_cagr_{years}yr"
                flag_col = f"{prefix}_cagr_{years}yr_flag"

                df.loc[
                    group.index,
                    value_col
                ] = value

                df.loc[
                    group.index,
                    flag_col
                ] = flag

    return df


def create_capital_allocation(df):

    columns = [
        "company_id",
        "year",
        "cfo_sign",
        "cfi_sign",
        "cff_sign",
        "pattern_label",
    ]

    output = []

    for _, row in df.iterrows():

        cfo = row.get(
            "operating_activity", 0
        )
        cfi = row.get(
            "investing_activity", 0
        )
        cff = row.get(
            "financing_activity", 0
        )

        cfo = 0 if pd.isna(cfo) else cfo
        cfi = 0 if pd.isna(cfi) else cfi
        cff = 0 if pd.isna(cff) else cff

        cfo_score = row.get(
            "cfo_quality_score"
        )

        cfo_sign = "+" if cfo > 0 else "-"
        cfi_sign = "+" if cfi > 0 else "-"
        cff_sign = "+" if cff > 0 else "-"

        label = capital_allocation_pattern(
            cfo,
            cfi,
            cff,
            cfo_score
        )

        output.append({
            "company_id": row["company_id"],
            "year": row["year"],
            "cfo_sign": cfo_sign,
            "cfi_sign": cfi_sign,
            "cff_sign": cff_sign,
            "pattern_label": label,
        })

    pd.DataFrame(output, columns=columns).to_csv(
        OUTPUT_DIR / "capital_allocation.csv",
        index=False
    )


def create_edge_case_log(df):

    path = OUTPUT_DIR / "ratio_edge_cases.log"

    with open(path, "w", encoding="utf-8") as f:

        f.write(
            "NIFTY 100 RATIO ENGINE EDGE CASE LOG\n"
        )
        f.write("=" * 60 + "\n")

        # CAGR flags
        for column in df.columns:
            if column.endswith("_flag"):
                counts = (
                    df[column]
                    .dropna()
                    .value_counts()
                )

                if len(counts):
                    f.write(
                        f"\n{column}\n"
                    )

                    for flag, count in counts.items():
                        f.write(
                            f"  {flag}: {count}\n"
                        )

        f.write(
            "\nClassification:\n"
            "INSUFFICIENT = insufficient historical data\n"
            "ZERO_BASE = zero starting value\n"
            "TURNAROUND = negative to positive\n"
            "DECLINE_TO_LOSS = positive to negative\n"
            "BOTH_NEGATIVE = negative to negative\n"
        )


def save_database(df, conn):

    # Remove helper-only columns
    drop_columns = [
        "_year_sort",
    ]

    df = df.drop(
        columns=[
            c for c in drop_columns
            if c in df.columns
        ],
        errors="ignore"
    )

    # Avoid pandas object issues with infinity
    df = df.replace(
        [float("inf"), float("-inf")],
        pd.NA
    )

    df.to_sql(
        "financial_ratios",
        conn,
        if_exists="replace",
        index=False
    )

    return len(df)


def main():

    print("=" * 70)
    print("NIFTY 100 SPRINT 2 — FINANCIAL RATIO ENGINE")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)

    try:

        print("\nLoading source tables...")
        tables = load_tables(conn)

        print("Preparing data...")
        df = prepare_data(tables)

        print(
            f"P&L base rows: {len(df)}"
        )

        print("Calculating profitability ratios...")
        df = calculate_ratios(df)

        print("Calculating CAGR metrics...")
        df = add_cagrs(df)

        print("Creating capital allocation output...")
        create_capital_allocation(df)

        print("Creating edge-case log...")
        create_edge_case_log(df)

        print("Writing financial_ratios table...")
        rows = save_database(df, conn)

        conn.commit()

        print("\n" + "=" * 70)
        print("SPRINT 2 RATIO ENGINE COMPLETED")
        print("=" * 70)

        print(
            f"financial_ratios rows: {rows}"
        )

        print(
            "capital_allocation.csv: CREATED"
        )

        print(
            "ratio_edge_cases.log: CREATED"
        )

    finally:
        conn.close()


if __name__ == "__main__":
    main()