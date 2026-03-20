from __future__ import annotations

import sqlite3
from datetime import datetime

from storage.database import get_connection


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


class LogSourceRepository:
    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def connect(self) -> sqlite3.Connection:
        conn = get_connection()
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def table_columns(self, conn: sqlite3.Connection) -> set[str]:
        cursor = conn.execute("PRAGMA table_info(log_sources)")
        return {str(row["name"]) for row in cursor.fetchall()}

    def ensure_runtime_fields(self, conn: sqlite3.Connection | None = None) -> None:
        owns_connection = conn is None
        conn = conn or self.connect()

        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS log_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    path TEXT NOT NULL UNIQUE,
                    recursive INTEGER NOT NULL DEFAULT 1,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    machine_hint TEXT,
                    last_scan_at TEXT,
                    last_successful_mtime REAL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            existing = self.table_columns(conn)

            desired_columns = {
                "name": "TEXT",
                "path": "TEXT",
                "recursive": "INTEGER NOT NULL DEFAULT 1",
                "enabled": "INTEGER NOT NULL DEFAULT 1",
                "machine_hint": "TEXT",
                "last_scan_at": "TEXT",
                "last_successful_mtime": "REAL",
                "created_at": "TEXT",
                "updated_at": "TEXT",
            }

            for column_name, column_type in desired_columns.items():
                if column_name in existing:
                    continue
                conn.execute(
                    f"ALTER TABLE log_sources ADD COLUMN {column_name} {column_type}"
                )

            conn.execute(
                """
                UPDATE log_sources
                SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP)
                WHERE created_at IS NULL
                """
            )
            conn.execute(
                """
                UPDATE log_sources
                SET updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)
                WHERE updated_at IS NULL
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_log_sources_enabled
                    ON log_sources (enabled)
                """
            )

            conn.execute("DROP TRIGGER IF EXISTS trg_log_sources_updated_at")
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS trg_log_sources_updated_at
                AFTER UPDATE ON log_sources
                FOR EACH ROW
                WHEN NEW.updated_at = OLD.updated_at
                BEGIN
                    UPDATE log_sources
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = OLD.id;
                END;
                """
            )

            conn.commit()
        finally:
            if owns_connection:
                conn.close()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def list_all(self):
        conn = self.connect()

        try:
            self.ensure_runtime_fields(conn)

            rows = conn.execute(
                """
                SELECT *
                FROM log_sources
                ORDER BY name
                """
            ).fetchall()

            return rows
        finally:
            conn.close()

    def list_enabled(self):
        conn = self.connect()

        try:
            self.ensure_runtime_fields(conn)

            rows = conn.execute(
                """
                SELECT *
                FROM log_sources
                WHERE enabled = 1
                ORDER BY name
                """
            ).fetchall()

            return rows
        finally:
            conn.close()

    def get_by_id(self, source_id: int):
        conn = self.connect()

        try:
            self.ensure_runtime_fields(conn)

            row = conn.execute(
                """
                SELECT *
                FROM log_sources
                WHERE id = ?
                """,
                (source_id,),
            ).fetchone()

            return row
        finally:
            conn.close()

    def get_by_name(self, name: str):
        conn = self.connect()

        try:
            self.ensure_runtime_fields(conn)

            row = conn.execute(
                """
                SELECT *
                FROM log_sources
                WHERE name = ?
                """,
                (name,),
            ).fetchone()

            return row
        finally:
            conn.close()

    def get_by_path(self, path: str):
        conn = self.connect()

        try:
            self.ensure_runtime_fields(conn)

            row = conn.execute(
                """
                SELECT *
                FROM log_sources
                WHERE path = ?
                """,
                (path,),
            ).fetchone()

            return row
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def insert(
        self,
        name,
        path,
        recursive=True,
        machine_hint=None,
    ):
        conn = self.connect()

        try:
            self.ensure_runtime_fields(conn)

            cursor = conn.execute(
                """
                INSERT INTO log_sources (
                    name,
                    path,
                    recursive,
                    machine_hint,
                    enabled,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (
                    name,
                    path,
                    int(bool(recursive)),
                    machine_hint,
                ),
            )

            conn.commit()
            return int(cursor.lastrowid)
        finally:
            conn.close()

    def upsert(
        self,
        name: str,
        path: str,
        recursive: bool = True,
        machine_hint: str | None = None,
        enabled: bool = True,
    ) -> int:
        conn = self.connect()

        try:
            self.ensure_runtime_fields(conn)

            existing = conn.execute(
                """
                SELECT id
                FROM log_sources
                WHERE name = ? OR path = ?
                ORDER BY id
                LIMIT 1
                """,
                (name, path),
            ).fetchone()

            if existing:
                source_id = int(existing["id"])
                conn.execute(
                    """
                    UPDATE log_sources
                    SET name = ?,
                        path = ?,
                        recursive = ?,
                        machine_hint = ?,
                        enabled = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        name,
                        path,
                        int(bool(recursive)),
                        machine_hint,
                        int(bool(enabled)),
                        source_id,
                    ),
                )
                conn.commit()
                return source_id

            cursor = conn.execute(
                """
                INSERT INTO log_sources (
                    name,
                    path,
                    recursive,
                    machine_hint,
                    enabled,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (
                    name,
                    path,
                    int(bool(recursive)),
                    machine_hint,
                    int(bool(enabled)),
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)
        finally:
            conn.close()

    def set_enabled(self, source_id: int, enabled: bool) -> None:
        conn = self.connect()

        try:
            self.ensure_runtime_fields(conn)

            conn.execute(
                """
                UPDATE log_sources
                SET enabled = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    int(bool(enabled)),
                    source_id,
                ),
            )

            conn.commit()
        finally:
            conn.close()

    def disable(self, source_id: int) -> None:
        self.set_enabled(source_id, False)

    def enable(self, source_id: int) -> None:
        self.set_enabled(source_id, True)

    def update_last_scan_at(self, source_id):
        conn = self.connect()

        try:
            self.ensure_runtime_fields(conn)

            conn.execute(
                """
                UPDATE log_sources
                SET last_scan_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (source_id,),
            )

            conn.commit()
        finally:
            conn.close()

    def update_last_successful_mtime(self, source_id, mtime):
        conn = self.connect()

        try:
            self.ensure_runtime_fields(conn)

            conn.execute(
                """
                UPDATE log_sources
                SET last_successful_mtime = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    float(mtime),
                    source_id,
                ),
            )

            conn.commit()
        finally:
            conn.close()

    def reset_checkpoint(self, source_id: int) -> None:
        conn = self.connect()

        try:
            self.ensure_runtime_fields(conn)

            conn.execute(
                """
                UPDATE log_sources
                SET last_scan_at = NULL,
                    last_successful_mtime = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (source_id,),
            )

            conn.commit()
        finally:
            conn.close()

    def delete(self, source_id: int) -> None:
        conn = self.connect()

        try:
            self.ensure_runtime_fields(conn)

            conn.execute(
                """
                DELETE FROM log_sources
                WHERE id = ?
                """,
                (source_id,),
            )

            conn.commit()
        finally:
            conn.close()