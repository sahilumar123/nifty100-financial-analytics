from pathlib import Path
import sqlite3
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "database" / "nifty100.db"
PEER_FILE = ROOT / "data" / "raw" / "peer_groups.xlsx"


METRICS = {
    "ROE": ("return_on_equity_pct", False),
    "ROCE": ("return_on_capital_employed_pct", False),
    "Net Profit Margin": ("net_profit_margin_pct", False),
    "D/E": ("debt_to_equity", True),
    "FCF": ("free_cash_flow_cr", False),
    "PAT CAGR 5yr": ("pat_cagr_5yr", False),
    "Revenue CAGR 5yr": ("revenue_cagr_5yr", False),
    "EPS CAGR 5yr": ("eps_cagr_5yr", False),
    "Interest Coverage": ("interest_coverage", False),
    "Asset Turnover": ("asset_turnover", False),
}


def load_peer_groups():

    df = pd.read_excel(PEER_FILE)

    df.columns = [
        str(c).strip().lower().replace(" ", "_")
        for c in df.columns
    ]

    return df


def find_column(df, names):

    for name in names:
        if name in df.columns:
            return name

    return None


def calculate_peer_percentiles():

    conn = sqlite3.connect(DB_PATH)

    ratios = pd.read_sql(
        "SELECT * FROM financial_ratios",
        conn,
    )

    companies = pd.read_sql(
        "SELECT * FROM companies",
        conn,
    )

    peers = load_peer_groups()

    conn.close()

    company_col = find_column(
        peers,
        ["company_id", "ticker", "symbol"],
    )

    peer_col = find_column(
        peers,
        ["peer_group_name", "peer_group", "group"],
    )

    if not company_col or not peer_col:
        raise ValueError(
            "Could not identify company ID / peer group columns "
            "in peer_groups.xlsx"
        )

    peers = peers[[company_col, peer_col]].copy()

    peers.columns = [
        "company_id",
        "peer_group_name",
    ]

    data = ratios.merge(
        peers,
        on="company_id",
        how="left",
    )

    data["peer_group_name"] = data[
        "peer_group_name"
    ].fillna("No peer group assigned")

    records = []

    for group, group_df in data.groupby(
        "peer_group_name"
    ):

        for metric_name, (
            column,
            inverse,
        ) in METRICS.items():

            if column not in group_df.columns:
                continue

            values = pd.to_numeric(
                group_df[column],
                errors="coerce",
            )

            percentile = values.rank(
                pct=True,
                method="average",
            )

            if inverse:
                percentile = 1 - percentile

            temp = pd.DataFrame({
                "company_id": group_df["company_id"],
                "peer_group_name": group,
                "metric": metric_name,
                "value": values,
                "percentile_rank": percentile,
                "year": group_df["year"],
            })

            records.append(temp)

    result = pd.concat(
        records,
        ignore_index=True,
    )

    conn = sqlite3.connect(DB_PATH)

    result.to_sql(
        "peer_percentiles",
        conn,
        if_exists="replace",
        index=False,
    )

    conn.close()

    print(
        f"peer_percentiles created: {len(result)} rows"
    )

    return result


if __name__ == "__main__":
    calculate_peer_percentiles()