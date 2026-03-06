from core.models import LogSource
from storage.database import get_connection


class LogSourceRepository:
    def add(self, source: LogSource) -> int:
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO log_sources (
                    name,
                    path,
                    recursive,
                    enabled,
                    machine_hint
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    source.name,
                    source.path,
                    int(source.recursive),
                    int(source.enabled),
                    source.machine_hint,
                ),
            )

            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def list_enabled(self):
        conn = get_connection()

        try:
            rows = conn.execute(
                """
                SELECT *
                FROM log_sources
                WHERE enabled = 1
                ORDER BY id
                """
            ).fetchall()
            return rows
        finally:
            conn.close()

    def list_all(self):
        conn = get_connection()

        try:
            rows = conn.execute(
                """
                SELECT *
                FROM log_sources
                ORDER BY id
                """
            ).fetchall()
            return rows
        finally:
            conn.close()

    def update_path(self, source_id: int, new_path: str):
        conn = get_connection()

        try:
            conn.execute(
                """
                UPDATE log_sources
                SET path = ?
                WHERE id = ?
                """,
                (new_path, source_id),
            )
            conn.commit()
        finally:
            conn.close()

    def set_enabled(self, source_id: int, enabled: bool):
        conn = get_connection()

        try:
            conn.execute(
                """
                UPDATE log_sources
                SET enabled = ?
                WHERE id = ?
                """,
                (int(enabled), source_id),
            )
            conn.commit()
        finally:
            conn.close()