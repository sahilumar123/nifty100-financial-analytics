import sqlite3
from pathlib import Path

DB_PATH = Path("data/database/nifty100.db")
SQL_PATH = Path("sql/analysis_queries.sql")


def main():
    conn = sqlite3.connect(DB_PATH)

    sql = SQL_PATH.read_text(encoding="utf-8")

    queries = [
        q.strip()
        for q in sql.split(";")
        if q.strip()
    ]

    print("=" * 70)
    print("NIFTY 100 SQL ANALYSIS")
    print("=" * 70)

    for i, query in enumerate(queries, start=1):
        try:
            cursor = conn.execute(query)
            rows = cursor.fetchall()

            print(f"\n--- QUERY {i} ---")
            print(f"Rows returned: {len(rows)}")

            for row in rows[:10]:
                print(row)

        except Exception as e:
            print(f"\n--- QUERY {i} FAILED ---")
            print(e)

    conn.close()

    print("\n" + "=" * 70)
    print("SQL ANALYSIS COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()