from datetime import datetime

from storage.database import get_connection


class ImportAuditRepository:
    def start_run(self, source_id: int) -> int:
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO import_runs (
                    source_id,
                    started_at
                )
                VALUES (?, ?)
                """,
                (source_id, datetime.now().isoformat()),
            )

            conn.commit()
            return cursor.lastrowid
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
    ):
        conn = get_connection()

        try:
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
                    datetime.now().isoformat(),
                    total_found,
                    imported_count,
                    duplicate_count,
                    error_count,
                    notes,
                    run_id,
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
    ):
        conn = get_connection()

        try:
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
                    detected_machine
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
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
                ),
            )
            conn.commit()
        finally:
            conn.close()