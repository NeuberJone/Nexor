from storage.database import get_connection
from core.models import ProductionJob


class ProductionRepository:

    def save(self, job: ProductionJob):

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

        except Exception:

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