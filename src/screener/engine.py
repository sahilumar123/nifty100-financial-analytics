from pathlib import Path
import sqlite3
import yaml
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "database" / "nifty100.db"
CONFIG_PATH = ROOT / "config" / "screener_config.yaml"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_data():
    conn = sqlite3.connect(DB_PATH)

    ratios = pd.read_sql("SELECT * FROM financial_ratios", conn)

    try:
        companies = pd.read_sql(
            "SELECT company_id, company_name, broad_sector FROM companies",
            conn,
        )
    except Exception:
        companies = pd.read_sql(
            "SELECT * FROM companies",
            conn,
        )

    conn.close()

    df = ratios.merge(
    companies,
    left_on="company_id",
    right_on="id",
    how="left"
     )

    df = df.drop(columns=["id"], errors="ignore")

    return df


def _find_column(df, candidates):
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _apply_threshold(df, column, threshold, mode):
    if column not in df.columns:
        return df

    values = pd.to_numeric(df[column], errors="coerce")

    if mode == "min":
        return df[values >= threshold]

    return df[values <= threshold]


def apply_filters(df, filters):
    result = df.copy()

    for key, threshold in filters.items():

        if key == "debt_declining":
            if threshold:
                de_col = _find_column(
                    result,
                    ["debt_to_equity", "debt_equity"]
                )

                if de_col:
                    result = result.sort_values(
                        ["company_id", "year"]
                    )

                    result["_previous_de"] = (
                        result.groupby("company_id")[de_col].shift(1)
                    )

                    result = result[
                        result["_previous_de"].notna()
                        & (
                            result[de_col]
                            < result["_previous_de"]
                        )
                    ]

                    result = result.drop(columns=["_previous_de"])

            continue

        metric_map = load_config()["metrics"]

        column = metric_map.get(key)

        if not column or column not in result.columns:
            continue

        # Financials are excluded from D/E screening.
        if key == "debt_to_equity_max":
            non_financial = (
                result["broad_sector"]
                .fillna("")
                .str.lower()
                != "financials"
            )

            financials = result[
                result["broad_sector"]
                .fillna("")
                .str.lower()
                == "financials"
            ]

            filtered = _apply_threshold(
                result[non_financial],
                column,
                threshold,
                "max",
            )

            result = pd.concat(
                [filtered, financials],
                ignore_index=True,
            )

        elif key.endswith("_min"):
            result = _apply_threshold(
                result,
                column,
                threshold,
                "min",
            )

        elif key.endswith("_max"):
            result = _apply_threshold(
                result,
                column,
                threshold,
                "max",
            )

    return result


def winsorize_score(series):
    values = pd.to_numeric(series, errors="coerce")

    if values.notna().sum() < 2:
        return pd.Series(50.0, index=series.index)

    p10 = values.quantile(0.10)
    p90 = values.quantile(0.90)

    if p90 == p10:
        return pd.Series(50.0, index=series.index)

    clipped = values.clip(p10, p90)

    return ((clipped - p10) / (p90 - p10) * 100).fillna(50)


def calculate_composite_score(df):
    result = df.copy()

    components = []

    for column, weight in [
        ("return_on_equity_pct", 15),
        ("return_on_capital_employed_pct", 10),
        ("net_profit_margin_pct", 10),
        ("free_cash_flow_cr", 15),
        ("cfo_quality_score", 10),
        ("revenue_cagr_5yr", 10),
        ("pat_cagr_5yr", 10),
        ("debt_to_equity", 10),
        ("interest_coverage", 5),
    ]:

        if column not in result.columns:
            score = pd.Series(50.0, index=result.index)
        else:
            score = winsorize_score(result[column])

            if column == "debt_to_equity":
                score = 100 - score

        components.append(score * weight / 100)

    result["composite_quality_score"] = sum(components)

    if "broad_sector" in result.columns:
        result["composite_quality_score"] = (
            result.groupby("broad_sector")[
                "composite_quality_score"
            ]
            .transform(
                lambda x: winsorize_score(x)
            )
        )

    return result


def run_preset(preset_name):
    config = load_config()
    df = load_data()

    filters = config["presets"][preset_name]

    result = apply_filters(df, filters)

    result = calculate_composite_score(result)

    result = result.sort_values(
        "composite_quality_score",
        ascending=False,
    )

    return result.reset_index(drop=True)


def run_all_presets():
    config = load_config()

    return {
        name: run_preset(name)
        for name in config["presets"]
    }


if __name__ == "__main__":
    results = run_all_presets()

    for name, df in results.items():
        print(f"\n{name}: {len(df)} companies")
        print(
            df[
                [
                    "company_id",
                    "composite_quality_score",
                ]
            ].head(10).to_string(index=False)
        )