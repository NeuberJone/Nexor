from storage.database import get_connection


class ProductionRepository:

    def __init__(self):
        pass

    # ============================================================
    # SALVAR JOB
    # ============================================================

    def save(self, job):

        conn = get_connection()

        cursor = conn.execute(
            """
            SELECT 1
            FROM production_jobs
            WHERE job_id = ?
            AND computer_name = ?
            AND start_time = ?
            """,
            (
                job.job_id,
                job.computer_name,
                job.start_time.isoformat(),
            ),
        )

        if cursor.fetchone():
            conn.close()
            return False

        conn.execute(
            """
            INSERT INTO production_jobs (
                job_id,
                machine,
                computer_name,
                document,
                fabric,
                start_time,
                end_time,
                duration_seconds,
                planned_length_m,
                printed_length_m,
                gap_before_m,
                driver,
                source_path,
                job_type,
                print_status,
                error_reason,
                counts_as_valid_production,
                counts_for_fabric_summary,
                counts_for_roll_export,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job.job_id,
                job.machine,
                job.computer_name,
                job.document,
                job.fabric,
                job.start_time.isoformat(),
                job.end_time.isoformat(),
                job.duration_seconds,
                job.planned_length_m,
                job.printed_length_m,
                job.gap_before_m,
                job.driver,
                job.source_path,
                job.job_type,
                job.print_status,
                job.error_reason,
                job.counts_as_valid_production,
                job.counts_for_fabric_summary,
                job.counts_for_roll_export,
                job.notes,
            ),
        )

        conn.commit()
        conn.close()

        return True

    # ============================================================
    # LISTAR TODOS OS JOBS
    # ============================================================

    def list_all(self):

        conn = get_connection()

        rows = conn.execute(
            """
            SELECT *
            FROM production_jobs
            ORDER BY start_time
            """
        ).fetchall()

        conn.close()

        return rows

    # ============================================================
    # BUSCAR POR JOB ID
    # ============================================================

    def get_by_job_id(self, job_id):

        conn = get_connection()

        rows = conn.execute(
            """
            SELECT *
            FROM production_jobs
            WHERE job_id = ?
            ORDER BY start_time
            """,
            (job_id,),
        ).fetchall()

        conn.close()

        return rows

    # ============================================================
    # MARCAR JOB COMO FALHA
    # ============================================================

    def mark_as_failed(
        self,
        job_id,
        computer_name,
        start_time_iso,
        reason="FAILED",
        notes=None,
    ):

        conn = get_connection()

        cursor = conn.execute(
            """
            UPDATE production_jobs
            SET
                print_status = ?,
                error_reason = ?,
                counts_as_valid_production = 0,
                counts_for_fabric_summary = 0,
                counts_for_roll_export = 0,
                notes = ?
            WHERE job_id = ?
            AND computer_name = ?
            AND start_time = ?
            """,
            (
                "FAILED",
                reason,
                notes,
                job_id,
                computer_name,
                start_time_iso,
            ),
        )

        conn.commit()
        conn.close()

        return cursor.rowcount

    # ============================================================
    # MARCAR JOB COMO MANCHADO
    # ============================================================

    def mark_as_stained(
        self,
        job_id,
        computer_name,
        start_time_iso,
        notes=None,
    ):

        conn = get_connection()

        cursor = conn.execute(
            """
            UPDATE production_jobs
            SET
                print_status = 'STAINED',
                error_reason = 'STAINED',
                counts_for_fabric_summary = 0,
                counts_for_roll_export = 0,
                notes = ?
            WHERE job_id = ?
            AND computer_name = ?
            AND start_time = ?
            """,
            (
                notes,
                job_id,
                computer_name,
                start_time_iso,
            ),
        )

        conn.commit()
        conn.close()

        return cursor.rowcount

    # ============================================================
    # MARCAR COMO REIMPRESSÃO
    # ============================================================

    def mark_as_reprint(
        self,
        job_id,
        computer_name,
        start_time_iso,
        notes=None,
    ):

        conn = get_connection()

        cursor = conn.execute(
            """
            UPDATE production_jobs
            SET
                job_type = 'REPRINT',
                notes = ?
            WHERE job_id = ?
            AND computer_name = ?
            AND start_time = ?
            """,
            (
                notes,
                job_id,
                computer_name,
                start_time_iso,
            ),
        )

        conn.commit()
        conn.close()

        return cursor.rowcount

    # ============================================================
    # EXCLUIR JOB
    # ============================================================

    def delete_job(
        self,
        job_id,
        computer_name,
        start_time_iso,
    ):

        conn = get_connection()

        cursor = conn.execute(
            """
            DELETE FROM production_jobs
            WHERE job_id = ?
            AND computer_name = ?
            AND start_time = ?
            """,
            (
                job_id,
                computer_name,
                start_time_iso,
            ),
        )

        conn.commit()
        conn.close()

        return cursor.rowcount