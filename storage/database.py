from __future__ import annotations

import sqlite3
from pathlib import Path


def resolve_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_default_db_path() -> Path:
    root = resolve_project_root()

    candidates = [
        root / "nexor.db",
        root / "storage" / "nexor.db",
        root / "data" / "nexor.db",
        root / "database.db",
        root / "storage" / "database.db",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return root / "nexor.db"


DB_PATH = resolve_default_db_path()


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    target = Path(db_path) if db_path is not None else DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(target))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database(db_path: str | Path | None = None) -> Path:
    """
    Initialize the database from schema.sql and apply runtime compatibility
    safeguards used by the repositories.

    Returns the final database path in use.
    """
    target = Path(db_path) if db_path is not None else DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)

    conn = get_connection(target)

    try:
        schema_path = Path(__file__).parent / "schema.sql"
        schema = schema_path.read_text(encoding="utf-8")
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()

    # Runtime compatibility / migration layer for existing databases
    # Import locally to avoid unnecessary import coupling at module load time.
    from storage.repository import ProductionRepository
    from storage.log_sources_repository import LogSourceRepository
    from storage.import_audit_repository import ImportAuditRepository

    ProductionRepository(db_path=target).ensure_runtime_fields()
    LogSourceRepository().ensure_runtime_fields()
    ImportAuditRepository().ensure_runtime_tables()

    return target