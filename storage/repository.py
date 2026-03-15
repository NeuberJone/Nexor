from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from core.models import ProductionJob, REVIEW_PENDING


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _to_bool(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)

    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "sim", "y"}:
        return True
    if text in {"0", "false", "no", "nao", "não", "n"}:
            return False
    return default


def _default_db_path() -> Path:
    root = Path(__file__).resolve().parent.parent

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


class ProductionRepository:
    def __init__(
        self,
        db_path: str | Path | None = None,
        table_name: str = "production_jobs",
    ) -> None:
        self.db_path = Path(db_path) if db_path is not None else _default_db_path()
        self.table_name = table_name

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def table_columns(self, conn: sqlite3.Connection) -> set[str]:
        cursor = conn.execute(f"PRAGMA table_info({self.table_name})")
        return {str(row["name"]) for row in cursor.fetchall()}

    def _pk_column(self, conn: sqlite3.Connection) -> str:
        columns = self.table_columns(conn)
        return "id" if "id" in columns else "rowid"

    def _updated_at_trigger_name(self) -> str:
        return f"trg_{self.table_name}_updated_at"

    def ensure_runtime_fields(self, conn: sqlite3.Connection | None = None) -> None:
        """
        Garante que o banco atual tenha todos os campos necessários para:
        - created_at / updated_at
        - suspicion_*
        - review_*
        - trigger de updated_at
        """
        owns_connection = conn is None
        conn = conn or self.connect()

        try:
            existing = self.table_columns(conn)

            desired_columns = {
                "created_at": "TEXT",
                "updated_at": "TEXT",
                "suspicion_category": "TEXT",
                "suspicion_reason": "TEXT",
                "suspicion_ratio": "REAL",
                "suspicion_missing_length_m": "REAL",
                "suspicion_marked_at": "TEXT",
                "review_status": "TEXT",
                "review_note": "TEXT",
                "reviewed_by": "TEXT",
                "reviewed_at": "TEXT",
            }

            applied_any = False

            for column_name, column_type in desired_columns.items():
                if column_name in existing:
                    continue
                conn.execute(
                    f"ALTER TABLE {self.table_name} ADD COLUMN {column_name} {column_type}"
                )
                applied_any = True

            existing = self.table_columns(conn)

            if "created_at" in existing:
                conn.execute(
                    f"""
                    UPDATE {self.table_name}
                    SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP)
                    WHERE created_at IS NULL
                    """
                )

            if "updated_at" in existing:
                conn.execute(
                    f"""
                    UPDATE {self.table_name}
                    SET updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)
                    WHERE updated_at IS NULL
                    """
                )

            self._ensure_updated_at_trigger(conn)
            conn.commit()
        finally:
            if owns_connection:
                conn.close()

    def ensure_review_fields(self, conn: sqlite3.Connection | None = None) -> None:
        """
        Mantido por compatibilidade com chamadas antigas.
        """
        self.ensure_runtime_fields(conn)

    def _ensure_updated_at_trigger(self, conn: sqlite3.Connection) -> None:
        columns = self.table_columns(conn)
        trigger_name = self._updated_at_trigger_name()

        conn.execute(f"DROP TRIGGER IF EXISTS {trigger_name}")

        if "updated_at" not in columns:
            return

        conn.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS {trigger_name}
            AFTER UPDATE ON {self.table_name}
            FOR EACH ROW
            WHEN NEW.updated_at = OLD.updated_at
            BEGIN
                UPDATE {self.table_name}
                SET updated_at = CURRENT_TIMESTAMP
                WHERE rowid = OLD.rowid;
            END;
            """
        )

    def row_to_job(self, row: sqlite3.Row) -> ProductionJob:
        actual_printed = None
        for key in ("actual_printed_length_m", "printed_length_m"):
            if key in row.keys() and row[key] not in (None, ""):
                actual_printed = float(row[key])
                break
        if actual_printed is None:
            actual_printed = 0.0

        gap_before = float(row["gap_before_m"] or 0.0) if "gap_before_m" in row.keys() else 0.0

        consumed = None
        for key in ("consumed_length_m", "total_consumption_m"):
            if key in row.keys() and row[key] not in (None, ""):
                consumed = float(row[key])
                break
        if consumed is None:
            consumed = actual_printed + gap_before

        pk_value = row["id"] if "id" in row.keys() else None

        return ProductionJob(
            id=pk_value,
            job_id=row["job_id"],
            machine=row["machine"],
            computer_name=row["computer_name"],
            document=row["document"],
            start_time=_parse_datetime(row["start_time"]) or datetime.min,
            end_time=_parse_datetime(row["end_time"]) or datetime.min,
            duration_seconds=int(row["duration_seconds"] or 0),
            fabric=row["fabric"] if "fabric" in row.keys() else None,
            planned_length_m=float(row["planned_length_m"] or 0.0),
            actual_printed_length_m=actual_printed,
            gap_before_m=gap_before,
            consumed_length_m=consumed,
            driver=row["driver"] if "driver" in row.keys() else None,
            source_path=row["source_path"] if "source_path" in row.keys() else None,
            job_type=(row["job_type"] or "UNKNOWN") if "job_type" in row.keys() else "UNKNOWN",
            is_rework=_to_bool(row["is_rework"], default=False) if "is_rework" in row.keys() else False,
            notes=row["notes"] if "notes" in row.keys() else None,
            print_status=(row["print_status"] or "OK") if "print_status" in row.keys() else "OK",
            counts_as_valid_production=_to_bool(row["counts_as_valid_production"], default=True)
            if "counts_as_valid_production" in row.keys() else True,
            counts_for_fabric_summary=_to_bool(row["counts_for_fabric_summary"], default=True)
            if "counts_for_fabric_summary" in row.keys() else True,
            counts_for_roll_export=_to_bool(row["counts_for_roll_export"], default=True)
            if "counts_for_roll_export" in row.keys() else True,
            error_reason=row["error_reason"] if "error_reason" in row.keys() else None,
            operator_code=row["operator_code"] if "operator_code" in row.keys() else None,
            operator_name=row["operator_name"] if "operator_name" in row.keys() else None,
            replacement_index=row["replacement_index"] if "replacement_index" in row.keys() else None,
            suspicion_category=row["suspicion_category"] if "suspicion_category" in row.keys() else None,
            suspicion_reason=row["suspicion_reason"] if "suspicion_reason" in row.keys() else None,
            suspicion_ratio=row["suspicion_ratio"] if "suspicion_ratio" in row.keys() else None,
            suspicion_missing_length_m=(
                row["suspicion_missing_length_m"]
                if "suspicion_missing_length_m" in row.keys() else None
            ),
            suspicion_marked_at=_parse_datetime(row["suspicion_marked_at"])
            if "suspicion_marked_at" in row.keys() else None,
            review_status=row["review_status"] if "review_status" in row.keys() else None,
            review_note=row["review_note"] if "review_note" in row.keys() else None,
            reviewed_by=row["reviewed_by"] if "reviewed_by" in row.keys() else None,
            reviewed_at=_parse_datetime(row["reviewed_at"]) if "reviewed_at" in row.keys() else None,
            created_at=_parse_datetime(row["created_at"]) if "created_at" in row.keys() else None,
            updated_at=_parse_datetime(row["updated_at"]) if "updated_at" in row.keys() else None,
        )

    def list_jobs(self, limit: int | None = None) -> list[ProductionJob]:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)

            sql = f"SELECT * FROM {self.table_name} ORDER BY start_time, job_id"
            params: tuple[object, ...] = ()

            if limit is not None:
                sql += " LIMIT ?"
                params = (limit,)

            rows = conn.execute(sql, params).fetchall()
            return [self.row_to_job(row) for row in rows]

    def save_job(self, job: ProductionJob) -> int:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            columns = self.table_columns(conn)
            now_iso = _now_iso()

            payload = {
                "job_id": job.job_id,
                "machine": job.machine,
                "computer_name": job.computer_name,
                "document": job.document,
                "start_time": job.start_time.isoformat(timespec="seconds"),
                "end_time": job.end_time.isoformat(timespec="seconds"),
                "duration_seconds": int(job.duration_seconds),
                "fabric": job.fabric,
                "planned_length_m": float(job.planned_length_m),
                "actual_printed_length_m": float(job.actual_printed_length_m),
                "gap_before_m": float(job.gap_before_m),
                "consumed_length_m": float(job.consumed_length_m),
                "driver": job.driver,
                "source_path": job.source_path,
                "job_type": job.job_type,
                "is_rework": int(job.is_rework),
                "notes": job.notes,
                "print_status": job.print_status,
                "counts_as_valid_production": int(job.counts_as_valid_production),
                "counts_for_fabric_summary": int(job.counts_for_fabric_summary),
                "counts_for_roll_export": int(job.counts_for_roll_export),
                "error_reason": job.error_reason,
                "operator_code": job.operator_code,
                "operator_name": job.operator_name,
                "replacement_index": job.replacement_index,
                "suspicion_category": job.suspicion_category,
                "suspicion_reason": job.suspicion_reason,
                "suspicion_ratio": job.suspicion_ratio,
                "suspicion_missing_length_m": job.suspicion_missing_length_m,
                "suspicion_marked_at": job.suspicion_marked_at.isoformat(timespec="seconds")
                if job.suspicion_marked_at else None,
                "review_status": job.review_status,
                "review_note": job.review_note,
                "reviewed_by": job.reviewed_by,
                "reviewed_at": job.reviewed_at.isoformat(timespec="seconds")
                if job.reviewed_at else None,
            }

            if "created_at" in columns and job.id is None:
                payload["created_at"] = now_iso
            if "updated_at" in columns:
                payload["updated_at"] = now_iso

            insert_columns = [name for name in payload.keys() if name in columns]
            placeholders = ", ".join("?" for _ in insert_columns)
            column_sql = ", ".join(insert_columns)
            update_sql = ", ".join(
                f"{name}=excluded.{name}" for name in insert_columns if name != "created_at"
            )

            sql = f"""
                INSERT INTO {self.table_name} ({column_sql})
                VALUES ({placeholders})
                ON CONFLICT(job_id, start_time, machine, document)
                DO UPDATE SET {update_sql}
            """

            params = [payload[name] for name in insert_columns]
            cursor = conn.execute(sql, params)
            conn.commit()
            return int(cursor.lastrowid or 0)

    def mark_job_suspicion(
        self,
        row_id: int,
        category: str,
        reason: str | None,
        ratio: float | None,
        missing_length_m: float | None,
        preserve_reviewed: bool = True,
    ) -> None:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            columns = self.table_columns(conn)
            pk_column = self._pk_column(conn)

            row = conn.execute(
                f"SELECT review_status FROM {self.table_name} WHERE {pk_column} = ?",
                (row_id,),
            ).fetchone()

            current_review_status = row["review_status"] if row else None
            next_review_status = current_review_status

            if not current_review_status:
                next_review_status = REVIEW_PENDING
            elif not preserve_reviewed and current_review_status != REVIEW_PENDING:
                next_review_status = REVIEW_PENDING

            fields: dict[str, object] = {
                "suspicion_category": category,
                "suspicion_reason": reason,
                "suspicion_ratio": ratio,
                "suspicion_missing_length_m": missing_length_m,
                "suspicion_marked_at": _now_iso(),
            }

            if "review_status" in columns and next_review_status is not None:
                fields["review_status"] = next_review_status

            if "updated_at" in columns:
                fields["updated_at"] = _now_iso()

            set_clause = ", ".join(f"{name} = ?" for name in fields.keys())
            params = [fields[name] for name in fields.keys()]
            params.append(row_id)

            conn.execute(
                f"UPDATE {self.table_name} SET {set_clause} WHERE {pk_column} = ?",
                params,
            )
            conn.commit()

    def clear_stale_pending_suspicions(self, active_row_ids: set[int]) -> int:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            columns = self.table_columns(conn)
            pk_column = self._pk_column(conn)

            rows = conn.execute(
                f"""
                SELECT {pk_column} AS pk_id
                FROM {self.table_name}
                WHERE suspicion_category IS NOT NULL
                  AND (review_status IS NULL OR review_status = ?)
                """,
                (REVIEW_PENDING,),
            ).fetchall()

            stale_ids = [
                int(row["pk_id"])
                for row in rows
                if int(row["pk_id"]) not in active_row_ids
            ]

            if not stale_ids:
                return 0

            fields: dict[str, object] = {
                "suspicion_category": None,
                "suspicion_reason": None,
                "suspicion_ratio": None,
                "suspicion_missing_length_m": None,
                "suspicion_marked_at": None,
            }

            if "review_status" in columns:
                fields["review_status"] = None
            if "updated_at" in columns:
                fields["updated_at"] = _now_iso()

            set_clause = ", ".join(f"{name} = ?" for name in fields.keys())
            placeholders = ", ".join("?" for _ in stale_ids)
            params = [fields[name] for name in fields.keys()] + stale_ids

            conn.execute(
                f"""
                UPDATE {self.table_name}
                SET {set_clause}
                WHERE {pk_column} IN ({placeholders})
                """,
                params,
            )
            conn.commit()
            return len(stale_ids)

    def update_review(
        self,
        row_id: int,
        review_status: str,
        review_note: str | None = None,
        reviewed_by: str | None = None,
    ) -> None:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            columns = self.table_columns(conn)
            pk_column = self._pk_column(conn)

            fields: dict[str, object] = {
                "review_status": review_status,
                "review_note": review_note,
                "reviewed_by": reviewed_by,
                "reviewed_at": _now_iso(),
            }

            if "updated_at" in columns:
                fields["updated_at"] = _now_iso()

            set_clause = ", ".join(f"{name} = ?" for name in fields.keys())
            params = [fields[name] for name in fields.keys()]
            params.append(row_id)

            conn.execute(
                f"UPDATE {self.table_name} SET {set_clause} WHERE {pk_column} = ?",
                params,
            )
            conn.commit()

    def list_pending_reviews(self) -> list[ProductionJob]:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)

            rows = conn.execute(
                f"""
                SELECT *
                FROM {self.table_name}
                WHERE review_status = ?
                ORDER BY suspicion_marked_at, start_time, job_id
                """,
                (REVIEW_PENDING,),
            ).fetchall()

            return [self.row_to_job(row) for row in rows]