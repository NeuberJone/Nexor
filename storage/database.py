# storage/database.py
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
    Inicializa o banco a partir do schema.sql e aplica a camada de
    compatibilidade/runtime usada pelos repositórios.

    Retorna o caminho final do banco em uso.
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

    # Import local para evitar acoplamento desnecessário no carregamento.
    from storage.import_audit_repository import ImportAuditRepository
    from storage.log_sources_repository import LogSourceRepository
    from storage.repository import ProductionRepository

    ProductionRepository(db_path=target).ensure_runtime_fields()
    LogSourceRepository(db_path=target).ensure_runtime_fields()
    ImportAuditRepository(db_path=target).ensure_runtime_tables()

    return target