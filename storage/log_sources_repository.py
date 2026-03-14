from storage.database import get_connection


class LogSourceRepository:

    def __init__(self):
        pass

    # ============================================================
    # LISTAR FONTES ATIVAS
    # ============================================================

    def list_enabled(self):

        conn = get_connection()

        rows = conn.execute(
            """
            SELECT *
            FROM log_sources
            WHERE enabled = 1
            ORDER BY name
            """
        ).fetchall()

        conn.close()

        return rows

    # ============================================================
    # INSERIR FONTE
    # ============================================================

    def insert(
        self,
        name,
        path,
        recursive=True,
        machine_hint=None,
    ):

        conn = get_connection()

        conn.execute(
            """
            INSERT INTO log_sources (
                name,
                path,
                recursive,
                machine_hint,
                enabled
            )
            VALUES (?, ?, ?, ?, 1)
            """,
            (
                name,
                path,
                int(recursive),
                machine_hint,
            ),
        )

        conn.commit()
        conn.close()

    # ============================================================
    # ATUALIZAR MOMENTO DO SCAN
    # ============================================================

    def update_last_scan_at(self, source_id):

        conn = get_connection()

        conn.execute(
            """
            UPDATE log_sources
            SET last_scan_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (source_id,),
        )

        conn.commit()
        conn.close()

    # ============================================================
    # ATUALIZAR CHECKPOINT DE MTIME
    # ============================================================

    def update_last_successful_mtime(self, source_id, mtime):

        conn = get_connection()

        conn.execute(
            """
            UPDATE log_sources
            SET last_successful_mtime = ?
            WHERE id = ?
            """,
            (
                mtime,
                source_id,
            ),
        )

        conn.commit()
        conn.close()
