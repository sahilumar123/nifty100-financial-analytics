from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "database" / "nifty100.db"
OUTPUT = ROOT / "reports" / "radar_charts"


METRICS = [
    ("ROE", "return_on_equity_pct"),
    ("ROCE", "return_on_capital_employed_pct"),
    ("NPM", "net_profit_margin_pct"),
    ("D/E", "debt_to_equity"),
    ("FCF", "free_cash_flow_cr"),
    ("PAT CAGR", "pat_cagr_5yr"),
    ("Revenue CAGR", "revenue_cagr_5yr"),
    ("Composite", "composite_quality_score"),
]


def normalize(values):

    values = pd.to_numeric(
        values,
        errors="coerce",
    ).fillna(0)

    p10 = values.quantile(0.10)
    p90 = values.quantile(0.90)

    if p90 == p10:
        return np.ones(len(values)) * 50

    values = values.clip(p10, p90)

    return (
        (values - p10)
        / (p90 - p10)
        * 100
    )


def create_radar_charts():

    OUTPUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql(
        """
        SELECT
            f.*,
            c.company_name
        FROM financial_ratios f
        LEFT JOIN companies c
            ON f.company_id = c.id
        """,
        conn,
    )

    conn.close()

    if "peer_percentiles" not in []:
        pass

    for _, row in df.tail(100).iterrows():

        labels = []
        values = []

        for label, column in METRICS:

            if column in df.columns:
                labels.append(label)

                values.append(
                    float(
                        normalize(
                            df[column]
                        ).loc[row.name]
                    )
                )

        if not values:
            continue

        angles = np.linspace(
            0,
            2 * np.pi,
            len(values),
            endpoint=False,
        )

        values += values[:1]
        angles = np.concatenate(
            [angles, angles[:1]]
        )

        fig = plt.figure(
            figsize=(7, 7)
        )

        ax = fig.add_subplot(
            111,
            polar=True,
        )

        ax.plot(
            angles,
            values,
        )

        ax.fill(
            angles,
            values,
            alpha=0.20,
        )

        ax.set_xticks(
            angles[:-1]
        )

        ax.set_xticklabels(labels)

        title = row["company_id"]

        ax.set_title(
            f"{title} Radar"
        )

        safe_name = (
            str(title)
            .replace("/", "_")
            .replace("\\", "_")
        )

        plt.savefig(
            OUTPUT / f"{safe_name}_radar.png",
            dpi=150,
            bbox_inches="tight",
        )

        plt.close()


if __name__ == "__main__":
    create_radar_charts()