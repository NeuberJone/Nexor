import sqlite3

from core.models import ProductionJob
from storage.database import get_connection


class ProductionRepository:
    def save(self, job: ProductionJob) -> bool:
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO production_jobs (
                    job_id,
                    machine,
                    computer_name,
                    document,
                    start_time,
                    end_time,
                    duration_seconds,
                    fabric,
                    length_m,
                    gap_before_m,
                    driver,
                    source_path
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.job_id,
                    job.machine,
                    job.computer_name,
                    job.document,
                    job.start_time.isoformat(),
                    job.end_time.isoformat(),
                    job.duration_seconds,
                    job.fabric,
                    job.length_m,
                    job.gap_before_m,
                    job.driver,
                    job.source_path,
                ),
            )

            conn.commit()
            return True

        except sqlite3.IntegrityError:
            return False

        finally:
            conn.close()

    def list_all(self):
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM production_jobs ORDER BY start_time"
        ).fetchall()
        conn.close()
        return rows

    def list_by_machine(self, computer_name: str):
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT *
            FROM production_jobs
            WHERE computer_name = ?
            ORDER BY start_time
            """,
            (computer_name,),
        ).fetchall()
        conn.close()
        return rows

    def list_by_day(self, day: str):
        """
        day no formato YYYY-MM-DD
        """
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT *
            FROM production_jobs
            WHERE date(start_time) = ?
            ORDER BY start_time
            """,
            (day,),
        ).fetchall()
        conn.close()
        return rows