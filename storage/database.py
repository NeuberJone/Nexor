import sqlite3
from pathlib import Path


DB_PATH = Path("nexor.db")


def get_connection():

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    return conn


def init_database():

    conn = get_connection()

    schema_path = Path(__file__).parent / "schema.sql"

    schema = schema_path.read_text()

    conn.executescript(schema)

    conn.commit()

    conn.close()