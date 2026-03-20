from __future__ import annotations

import sqlite3
from datetime import datetime

from storage.database import get_connection


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


class ImportAuditRepository:
    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def connect(self) -> sqlite3.Connection:
        conn = get_connection()
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def table_columns(self, conn: sqlite3.Connection, table_name: str) -> set[str]:
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        return {str(row["name"]) for row in cursor.fetchall()}

    def ensure_runtime_tables(self, conn: sqlite3.Connection | None = None) -> None:
        owns_connection = conn is None
        conn = conn or self.connect()

        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS import_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id INTEGER NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    total_found INTEGER NOT NULL DEFAULT 0,
                    imported_count INTEGER NOT NULL DEFAULT 0,
                    duplicate_count INTEGER NOT NULL DEFAULT 0,
                    error_count INTEGER NOT NULL DEFAULT 0,
                    notes TEXT,
                    FOREIGN KEY (source_id) REFERENCES log_sources(id) ON DELETE RESTRICT
                )
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_import_runs_source_id
                    ON import_runs (source_id)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_import_runs_started_at
                    ON import_runs (started_at)
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS imported_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    source_id INTEGER NOT NULL,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    file_hash TEXT,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    detected_job_id TEXT,
                    detected_computer_name TEXT,
                    detected_machine TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES import_runs(id) ON DELETE CASCADE,
                    FOREIGN KEY (source_id) REFERENCES log_sources(id) ON DELETE RESTRICT,
                    UNIQUE(run_id, file_path, file_hash)
                )
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_imported_logs_run_id
                    ON imported_logs (run_id)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_imported_logs_source_id
                    ON imported_logs (source_id)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_imported_logs_status
                    ON imported_logs (status)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_imported_logs_file_hash
                    ON imported_logs (file_hash)
                """
            )

            # Runtime backfill / compatibility for old databases
            import_runs_cols = self.table_columns(conn, "import_runs")
            desired_import_runs = {
                "source_id": "INTEGER",
                "started_at": "TEXT",
                "finished_at": "TEXT",
                "total_found": "INTEGER NOT NULL DEFAULT 0",
                "imported_count": "INTEGER NOT NULL DEFAULT 0",
                "duplicate_count": "INTEGER NOT NULL DEFAULT 0",
                "error_count": "INTEGER NOT NULL DEFAULT 0",
                "notes": "TEXT",
            }

            for column_name, column_type in desired_import_runs.items():
                if column_name in import_runs_cols:
                    continue
                conn.execute(
                    f"ALTER TABLE import_runs ADD COLUMN {column_name} {column_type}"
                )

            imported_logs_cols = self.table_columns(conn, "imported_logs")
            desired_imported_logs = {
                "run_id": "INTEGER",
                "source_id": "INTEGER",
                "file_name": "TEXT",
                "file_path": "TEXT",
                "file_size": "INTEGER",
                "file_hash": "TEXT",
                "status": "TEXT",
                "error_message": "TEXT",
                "detected_job_id": "TEXT",
                "detected_computer_name": "TEXT",
                "detected_machine": "TEXT",
                "created_at": "TEXT",
            }

            for column_name, column_type in desired_imported_logs.items():
                if column_name in imported_logs_cols:
                    continue
                conn.execute(
                    f"ALTER TABLE imported_logs ADD COLUMN {column_name} {column_type}"
                )

            conn.commit()
        finally:
            if owns_connection:
                conn.close()

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def start_run(self, source_id: int) -> int:
        if int(source_id) <= 0:
            raise ValueError("source_id inválido para iniciar import run.")

        conn = self.connect()
        cursor = conn.cursor()

        try:
            self.ensure_runtime_tables(conn)

            cursor.execute(
                """
                INSERT INTO import_runs (
                    source_id,
                    started_at
                )
                VALUES (?, ?)
                """,
                (
                    int(source_id),
                    _now_iso(),
                ),
            )

            conn.commit()
            return int(cursor.lastrowid)
        finally:
            conn.close()

    def finish_run(
        self,
        run_id: int,
        *,
        total_found: int,
        imported_count: int,
        duplicate_count: int,
        error_count: int,
        notes: str | None = None,
    ) -> None:
        if int(run_id) <= 0:
            return

        conn = self.connect()

        try:
            self.ensure_runtime_tables(conn)

            conn.execute(
                """
                UPDATE import_runs
                SET finished_at = ?,
                    total_found = ?,
                    imported_count = ?,
                    duplicate_count = ?,
                    error_count = ?,
                    notes = ?
                WHERE id = ?
                """,
                (
                    _now_iso(),
                    int(total_found or 0),
                    int(imported_count or 0),
                    int(duplicate_count or 0),
                    int(error_count or 0),
                    notes,
                    int(run_id),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def register_file(
        self,
        *,
        run_id: int,
        source_id: int,
        file_name: str,
        file_path: str,
        file_size: int | None,
        file_hash: str | None,
        status: str,
        error_message: str | None = None,
        detected_job_id: str | None = None,
        detected_computer_name: str | None = None,
        detected_machine: str | None = None,
    ) -> None:
        if int(run_id or 0) <= 0:
            return

        if int(source_id or 0) <= 0:
            return

        conn = self.connect()

        try:
            self.ensure_runtime_tables(conn)

            conn.execute(
                """
                INSERT OR IGNORE INTO imported_logs (
                    run_id,
                    source_id,
                    file_name,
                    file_path,
                    file_size,
                    file_hash,
                    status,
                    error_message,
                    detected_job_id,
                    detected_computer_name,
                    detected_machine,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(run_id),
                    int(source_id),
                    file_name,
                    file_path,
                    file_size,
                    file_hash,
                    status,
                    error_message,
                    detected_job_id,
                    detected_computer_name,
                    detected_machine,
                    _now_iso(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def list_runs(self, source_id: int | None = None, limit: int | None = None):
        conn = self.connect()

        try:
            self.ensure_runtime_tables(conn)

            sql = """
                SELECT *
                FROM import_runs
            """
            params: list[object] = []

            if source_id is not None:
                sql += " WHERE source_id = ?"
                params.append(int(source_id))

            sql += " ORDER BY started_at DESC, id DESC"

            if limit is not None:
                sql += " LIMIT ?"
                params.append(int(limit))

            return conn.execute(sql, tuple(params)).fetchall()
        finally:
            conn.close()

    def get_run(self, run_id: int):
        conn = self.connect()

        try:
            self.ensure_runtime_tables(conn)

            return conn.execute(
                """
                SELECT *
                FROM import_runs
                WHERE id = ?
                """,
                (int(run_id),),
            ).fetchone()
        finally:
            conn.close()

    def list_run_files(self, run_id: int):
        conn = self.connect()

        try:
            self.ensure_runtime_tables(conn)

            return conn.execute(
                """
                SELECT *
                FROM imported_logs
                WHERE run_id = ?
                ORDER BY id
                """,
                (int(run_id),),
            ).fetchall()
        finally:
            conn.close()

    def list_source_files(self, source_id: int, limit: int | None = None):
        conn = self.connect()

        try:
            self.ensure_runtime_tables(conn)

            sql = """
                SELECT *
                FROM imported_logs
                WHERE source_id = ?
                ORDER BY created_at DESC, id DESC
            """
            params: list[object] = [int(source_id)]

            if limit is not None:
                sql += " LIMIT ?"
                params.append(int(limit))

            return conn.execute(sql, tuple(params)).fetchall()
        finally:
            conn.close()