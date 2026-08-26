from pathlib import Path
import sqlite3
import pandas as pd

from src.etl.loader import load_all
from src.etl.db import DB_PATH, create_database


OUTPUT_DIR = Path("output")
AUDIT_FILE = OUTPUT_DIR / "load_audit.csv"


def load_to_database():
    print("=" * 60)
    print("LOADING NIFTY 100 DATA INTO SQLITE")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Ensure database/schema exists
    create_database()

    # Load Excel datasets
    data = load_all()

    conn = sqlite3.connect(DB_PATH)

    audit_rows = []

    try:
        for table_name, df in data.items():
            row_count = len(df)

            print(
                f"Loading {table_name:20} "
                f"{row_count:>6} rows...",
                end=" "
            )

            try:
                df.to_sql(
                    table_name,
                    conn,
                    if_exists="replace",
                    index=False
                )

                audit_rows.append({
                    "table_name": table_name,
                    "source_rows": row_count,
                    "loaded_rows": row_count,
                    "rejected_rows": 0,
                    "status": "OK"
                })

                print("OK")

            except Exception as e:
                audit_rows.append({
                    "table_name": table_name,
                    "source_rows": row_count,
                    "loaded_rows": 0,
                    "rejected_rows": row_count,
                    "status": f"FAILED: {e}"
                })

                print("FAILED")

                raise

        conn.commit()

    finally:
        conn.close()

    # Create load audit
    audit_df = pd.DataFrame(audit_rows)
    audit_df.to_csv(AUDIT_FILE, index=False)

    print("\nDatabase loading completed.")
    print(f"Database: {DB_PATH}")
    print(f"Load audit: {AUDIT_FILE}")


if __name__ == "__main__":
    load_to_database()