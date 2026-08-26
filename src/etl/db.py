from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).resolve().parents[2]
DB_DIR = BASE_DIR / "data" / "database"
DB_PATH = DB_DIR / "nifty100.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def get_connection():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def create_database():
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema not found: {SCHEMA_PATH}")

    conn = get_connection()

    try:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()

    print(f"Database created: {DB_PATH}")


if __name__ == "__main__":
    create_database()