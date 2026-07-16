# storage/repository.py
from __future__ import annotations

import re
import sqlite3
from datetime import datetime
from pathlib import Path

from analytics.production_metrics import classify_job, effective_printed_length_m
from core.models import (
    Job,
    Log,
    ProductionJob,
    REVIEW_PENDING,
    ROLL_CLOSED,
    ROLL_EXPORTED,
    ROLL_OPEN,
    ROLL_REOPENED,
    ROLL_REVIEWED,
    LOG_CONVERTED,
    LOG_DUPLICATED,
    LOG_IGNORED,
    LOG_INVALID,
    LOG_NEW,
    LOG_PARSED,
    LOG_NORMALIZATION_CONVERTED,
    LOG_NORMALIZATION_PENDING,
    LOG_NORMALIZATION_READY,
    LOG_PARSE_DUPLICATED,
    LOG_PARSE_IGNORED,
    LOG_PARSE_INVALID,
    LOG_PARSE_NEW,
    LOG_PARSE_PARSED,
    Roll,
    RollItem,
    resolve_log_status_parts,
)


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _now_display() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _dt_to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat(timespec="seconds")


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


def _validate_identifier(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return name


class ProductionRepository:
    def __init__(
        self,
        db_path: str | Path | None = None,
        table_name: str = "production_jobs",
    ) -> None:
        self.db_path = Path(db_path) if db_path is not None else _default_db_path()
        self.table_name = _validate_identifier(table_name)

    def connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def table_columns(self, conn: sqlite3.Connection, table_name: str | None = None) -> set[str]:
        target = _validate_identifier(table_name or self.table_name)
        cursor = conn.execute(f"PRAGMA table_info({target})")
        return {str(row["name"]) for row in cursor.fetchall()}

    def _pk_column(self, conn: sqlite3.Connection, table_name: str | None = None) -> str:
        columns = self.table_columns(conn, table_name)
        return "id" if "id" in columns else "rowid"

    def _updated_at_trigger_name(self, table_name: str | None = None) -> str:
        target = _validate_identifier(table_name or self.table_name)
        return f"trg_{target}_updated_at"

    def _ensure_updated_at_trigger(self, conn: sqlite3.Connection, table_name: str | None = None) -> None:
        target = _validate_identifier(table_name or self.table_name)
        columns = self.table_columns(conn, target)
        trigger_name = self._updated_at_trigger_name(target)

        conn.execute(f"DROP TRIGGER IF EXISTS {trigger_name}")

        if "updated_at" not in columns:
            return

        conn.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS {trigger_name}
            AFTER UPDATE ON {target}
            FOR EACH ROW
            WHEN NEW.updated_at = OLD.updated_at
            BEGIN
                UPDATE {target}
                SET updated_at = CURRENT_TIMESTAMP
                WHERE rowid = OLD.rowid;
            END;
            """
        )

    def _ensure_table_columns(
        self,
        conn: sqlite3.Connection,
        table_name: str,
        desired_columns: dict[str, str],
    ) -> None:
        target = _validate_identifier(table_name)
        existing = self.table_columns(conn, target)

        for column_name, column_type in desired_columns.items():
            if column_name in existing:
                continue
            conn.execute(f"ALTER TABLE {target} ADD COLUMN {column_name} {column_type}")

    # ------------------------------------------------------------------
    # Schema / runtime compatibility
    # ------------------------------------------------------------------

    def ensure_log_table(self, conn: sqlite3.Connection | None = None) -> None:
        owns_connection = conn is None
        conn = conn or self.connect()

        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_path TEXT,
                    source_name TEXT,
                    fingerprint TEXT,
                    machine_code_raw TEXT,
                    captured_at TEXT,
                    raw_payload TEXT,
                    status TEXT NOT NULL DEFAULT 'NEW',
                    parse_status TEXT NOT NULL DEFAULT 'NEW',
                    normalized_status TEXT NOT NULL DEFAULT 'PENDING',
                    parse_error TEXT,
                    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    job_id INTEGER,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            self._ensure_table_columns(
                conn,
                "logs",
                {
                    "source_path": "TEXT",
                    "source_name": "TEXT",
                    "fingerprint": "TEXT",
                    "machine_code_raw": "TEXT",
                    "captured_at": "TEXT",
                    "raw_payload": "TEXT",
                    "status": "TEXT",
                    "parse_status": "TEXT",
                    "normalized_status": "TEXT",
                    "parse_error": "TEXT",
                    "imported_at": "TEXT",
                    "job_id": "INTEGER",
                    "created_at": "TEXT",
                    "updated_at": "TEXT",
                },
            )

            conn.execute(
                """
                UPDATE logs
                SET parse_status = CASE
                    WHEN UPPER(COALESCE(status, '')) = 'PARSED' THEN 'PARSED'
                    WHEN UPPER(COALESCE(status, '')) = 'INVALID' THEN 'INVALID'
                    WHEN UPPER(COALESCE(status, '')) = 'DUPLICATED' THEN 'DUPLICATED'
                    WHEN UPPER(COALESCE(status, '')) = 'IGNORED' THEN 'IGNORED'
                    WHEN UPPER(COALESCE(status, '')) = 'CONVERTED' THEN 'PARSED'
                    ELSE 'NEW'
                END
                WHERE parse_status IS NULL OR TRIM(parse_status) = ''
                """
            )

            conn.execute(
                """
                UPDATE logs
                SET normalized_status = CASE
                    WHEN UPPER(COALESCE(status, '')) = 'CONVERTED' THEN 'CONVERTED'
                    WHEN UPPER(COALESCE(parse_status, '')) = 'PARSED' THEN 'READY'
                    ELSE 'PENDING'
                END
                WHERE normalized_status IS NULL OR TRIM(normalized_status) = ''
                """
            )

            conn.execute(
                """
                UPDATE logs
                SET status = CASE
                    WHEN UPPER(COALESCE(normalized_status, '')) = 'CONVERTED' THEN 'CONVERTED'
                    WHEN UPPER(COALESCE(parse_status, '')) = 'INVALID' THEN 'INVALID'
                    WHEN UPPER(COALESCE(parse_status, '')) = 'DUPLICATED' THEN 'DUPLICATED'
                    WHEN UPPER(COALESCE(parse_status, '')) = 'IGNORED' THEN 'IGNORED'
                    WHEN UPPER(COALESCE(parse_status, '')) = 'PARSED' THEN 'PARSED'
                    ELSE 'NEW'
                END
                WHERE status IS NULL OR TRIM(status) = ''
                """
            )

            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_logs_fingerprint ON logs (fingerprint)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_logs_status ON logs (status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_logs_parse_status ON logs (parse_status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_logs_normalized_status ON logs (normalized_status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_logs_captured_at ON logs (captured_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_logs_source_path ON logs (source_path)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_logs_machine_code_raw ON logs (machine_code_raw)"
            )

            conn.execute(
                """
                UPDATE logs
                SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP)
                WHERE created_at IS NULL
                """
            )
            conn.execute(
                """
                UPDATE logs
                SET updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)
                WHERE updated_at IS NULL
                """
            )

            self._ensure_updated_at_trigger(conn, "logs")
            conn.commit()
        finally:
            if owns_connection:
                conn.close()

    def ensure_roll_tables(self, conn: sqlite3.Connection | None = None) -> None:
        owns_connection = conn is None
        conn = conn or self.connect()

        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rolls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    roll_name TEXT NOT NULL UNIQUE,
                    machine TEXT NOT NULL,
                    fabric TEXT,
                    status TEXT NOT NULL DEFAULT 'OPEN',
                    note TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    closed_at TEXT,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    exported_at TEXT,
                    reviewed_at TEXT,
                    reopened_at TEXT
                )
                """
            )

            self._ensure_table_columns(
                conn,
                "rolls",
                {
                    "roll_name": "TEXT",
                    "machine": "TEXT",
                    "fabric": "TEXT",
                    "status": "TEXT",
                    "note": "TEXT",
                    "created_at": "TEXT",
                    "closed_at": "TEXT",
                    "updated_at": "TEXT",
                    "exported_at": "TEXT",
                    "reviewed_at": "TEXT",
                    "reopened_at": "TEXT",
                },
            )

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_rolls_status ON rolls (status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_rolls_machine ON rolls (machine)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_rolls_fabric ON rolls (fabric)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_rolls_created_at ON rolls (created_at)"
            )

            self._ensure_updated_at_trigger(conn, "rolls")

            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS roll_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    roll_id INTEGER NOT NULL,
                    job_row_id INTEGER NOT NULL,
                    job_id TEXT NOT NULL,
                    document TEXT NOT NULL,
                    machine TEXT NOT NULL,
                    fabric TEXT,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    planned_length_m REAL NOT NULL DEFAULT 0,
                    effective_printed_length_m REAL NOT NULL DEFAULT 0,
                    consumed_length_m REAL NOT NULL DEFAULT 0,
                    gap_before_m REAL NOT NULL DEFAULT 0,
                    metric_category TEXT,
                    review_status TEXT,
                    snapshot_print_status TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (roll_id) REFERENCES rolls(id) ON DELETE CASCADE,
                    FOREIGN KEY (job_row_id) REFERENCES {self.table_name}(id) ON DELETE RESTRICT,
                    UNIQUE(roll_id, job_row_id),
                    UNIQUE(job_row_id)
                )
                """
            )

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_roll_items_roll_id ON roll_items (roll_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_roll_items_job_row_id ON roll_items (job_row_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_roll_items_sort_order ON roll_items (roll_id, sort_order)"
            )
            conn.commit()
        finally:
            if owns_connection:
                conn.close()

    def ensure_runtime_fields(self, conn: sqlite3.Connection | None = None) -> None:
        owns_connection = conn is None
        conn = conn or self.connect()

        try:
            self._ensure_table_columns(
                conn,
                self.table_name,
                {
                    "log_id": "INTEGER",
                    "created_at": "TEXT",
                    "updated_at": "TEXT",
                    "actual_printed_length_m": "REAL",
                    "gap_before_m": "REAL",
                    "consumed_length_m": "REAL",
                    "job_type": "TEXT",
                    "is_rework": "INTEGER",
                    "notes": "TEXT",
                    "print_status": "TEXT",
                    "counts_as_valid_production": "INTEGER",
                    "counts_for_fabric_summary": "INTEGER",
                    "counts_for_roll_export": "INTEGER",
                    "error_reason": "TEXT",
                    "operator_code": "TEXT",
                    "operator_name": "TEXT",
                    "replacement_index": "INTEGER",
                    "suspicion_category": "TEXT",
                    "suspicion_reason": "TEXT",
                    "suspicion_ratio": "REAL",
                    "suspicion_missing_length_m": "REAL",
                    "suspicion_marked_at": "TEXT",
                    "review_status": "TEXT",
                    "review_note": "TEXT",
                    "reviewed_by": "TEXT",
                    "reviewed_at": "TEXT",
                    "classification": "TEXT",
                },
            )

            existing = self.table_columns(conn, self.table_name)

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

            if "review_status" in existing:
                conn.execute(
                    f"""
                    UPDATE {self.table_name}
                    SET review_status = COALESCE(review_status, ?)
                    WHERE review_status IS NULL
                    """,
                    (REVIEW_PENDING,),
                )

            if "print_status" in existing:
                conn.execute(
                    f"""
                    UPDATE {self.table_name}
                    SET print_status = COALESCE(print_status, 'OK')
                    WHERE print_status IS NULL
                    """
                )

            self._ensure_updated_at_trigger(conn, self.table_name)
            self.ensure_log_table(conn)
            self.ensure_roll_tables(conn)
            conn.commit()
        finally:
            if owns_connection:
                conn.close()

    def ensure_review_fields(self, conn: sqlite3.Connection | None = None) -> None:
        self.ensure_runtime_fields(conn)

    # ------------------------------------------------------------------
    # Logs
    # ------------------------------------------------------------------

    def row_to_log(self, row: sqlite3.Row) -> Log:
        status = row["status"] if "status" in row.keys() and row["status"] else LOG_NEW
        parse_status = (
            row["parse_status"]
            if "parse_status" in row.keys() and row["parse_status"]
            else None
        )
        normalized_status = (
            row["normalized_status"]
            if "normalized_status" in row.keys() and row["normalized_status"]
            else None
        )

        return Log(
            id=int(row["id"]) if row["id"] is not None else None,
            source_path=row["source_path"] if "source_path" in row.keys() else None,
            source_name=row["source_name"] if "source_name" in row.keys() else None,
            fingerprint=row["fingerprint"] if "fingerprint" in row.keys() else None,
            machine_code_raw=row["machine_code_raw"] if "machine_code_raw" in row.keys() else None,
            captured_at=_parse_datetime(row["captured_at"]) if "captured_at" in row.keys() else None,
            raw_payload=row["raw_payload"] if "raw_payload" in row.keys() else None,
            status=status,
            parse_status=parse_status,
            normalized_status=normalized_status,
            parse_error=row["parse_error"] if "parse_error" in row.keys() else None,
            imported_at=_parse_datetime(row["imported_at"]) if "imported_at" in row.keys() else None,
            job_id=int(row["job_id"]) if "job_id" in row.keys() and row["job_id"] is not None else None,
        )

    def list_logs(
        self,
        status: str | None = None,
        limit: int | None = None,
        *,
        parse_status: str | None = None,
        normalized_status: str | None = None,
    ) -> list[Log]:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            sql = "SELECT * FROM logs"
            params: list[object] = []
            where_clauses: list[str] = []

            if status:
                where_clauses.append("UPPER(status) = ?")
                params.append(status.strip().upper())

            if parse_status:
                where_clauses.append("UPPER(parse_status) = ?")
                params.append(parse_status.strip().upper())

            if normalized_status:
                where_clauses.append("UPPER(normalized_status) = ?")
                params.append(normalized_status.strip().upper())

            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)

            sql += " ORDER BY imported_at DESC, id DESC"

            if limit is not None:
                sql += " LIMIT ?"
                params.append(limit)

            rows = conn.execute(sql, tuple(params)).fetchall()
            return [self.row_to_log(row) for row in rows]

    def get_log_by_id(self, log_id: int) -> Log | None:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            row = conn.execute("SELECT * FROM logs WHERE id = ?", (log_id,)).fetchone()
            return self.row_to_log(row) if row else None

    def get_log_by_fingerprint(self, fingerprint: str) -> Log | None:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            row = conn.execute(
                "SELECT * FROM logs WHERE fingerprint = ?",
                (fingerprint,),
            ).fetchone()
            return self.row_to_log(row) if row else None

    def _get_log_row_id_by_fingerprint(self, conn: sqlite3.Connection, fingerprint: str) -> int | None:
        row = conn.execute(
            "SELECT id FROM logs WHERE fingerprint = ?",
            (fingerprint,),
        ).fetchone()
        return int(row["id"]) if row else None

    def save_log(self, log: Log) -> int:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)

            legacy_status, parse_status, normalized_status = resolve_log_status_parts(
                getattr(log, "status", None),
                getattr(log, "parse_status", None),
                getattr(log, "normalized_status", None),
            )

            payload = {
                "source_path": log.source_path,
                "source_name": log.source_name,
                "fingerprint": log.fingerprint,
                "machine_code_raw": log.machine_code_raw,
                "captured_at": _dt_to_iso(log.captured_at),
                "raw_payload": log.raw_payload,
                "status": legacy_status,
                "parse_status": parse_status,
                "normalized_status": normalized_status,
                "parse_error": log.parse_error,
                "imported_at": _dt_to_iso(log.imported_at) or _now_iso(),
                "job_id": log.job_id,
                "updated_at": _now_iso(),
            }

            if log.id is None:
                payload["created_at"] = _now_iso()

            columns = [name for name in payload.keys()]
            placeholders = ", ".join("?" for _ in columns)
            update_sql = ", ".join(
                f"{name}=excluded.{name}" for name in columns if name != "created_at"
            )

            conn.execute(
                f"""
                INSERT INTO logs ({", ".join(columns)})
                VALUES ({placeholders})
                ON CONFLICT(fingerprint)
                DO UPDATE SET {update_sql}
                """,
                [payload[name] for name in columns],
            )

            conn.commit()

            if log.fingerprint:
                row_id = self._get_log_row_id_by_fingerprint(conn, log.fingerprint)
                if row_id is not None:
                    return row_id

            row = conn.execute("SELECT last_insert_rowid() AS row_id").fetchone()
            return int(row["row_id"] or 0)

    def _update_log_status(
        self,
        conn: sqlite3.Connection,
        log_id: int,
        status: str | None = None,
        *,
        parse_status: str | None = None,
        normalized_status: str | None = None,
        parse_error: str | None = None,
        job_id: int | None = None,
    ) -> None:
        legacy_status, parse_value, normalized_value = resolve_log_status_parts(
            status,
            parse_status,
            normalized_status,
        )

        conn.execute(
            """
            UPDATE logs
            SET status = ?,
                parse_status = ?,
                normalized_status = ?,
                parse_error = ?,
                job_id = COALESCE(?, job_id),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                legacy_status,
                parse_value,
                normalized_value,
                parse_error,
                job_id,
                log_id,
            ),
        )

    def mark_log_parsed(self, log_id: int) -> None:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            self._update_log_status(
                conn,
                log_id,
                status=LOG_PARSED,
                parse_status=LOG_PARSE_PARSED,
                normalized_status=LOG_NORMALIZATION_READY,
            )
            conn.commit()

    def mark_log_invalid(self, log_id: int, parse_error: str | None = None) -> None:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            self._update_log_status(
                conn,
                log_id,
                status=LOG_INVALID,
                parse_status=LOG_PARSE_INVALID,
                normalized_status=LOG_NORMALIZATION_PENDING,
                parse_error=parse_error,
            )
            conn.commit()

    def mark_log_duplicated(self, log_id: int) -> None:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            self._update_log_status(
                conn,
                log_id,
                status=LOG_DUPLICATED,
                parse_status=LOG_PARSE_DUPLICATED,
                normalized_status=LOG_NORMALIZATION_PENDING,
            )
            conn.commit()

    def mark_log_ignored(self, log_id: int) -> None:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            self._update_log_status(
                conn,
                log_id,
                status=LOG_IGNORED,
                parse_status=LOG_PARSE_IGNORED,
                normalized_status=LOG_NORMALIZATION_PENDING,
            )
            conn.commit()

    def mark_log_converted(self, log_id: int, job_id: int) -> None:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            self._update_log_status(
                conn,
                log_id,
                status=LOG_CONVERTED,
                parse_status=LOG_PARSE_PARSED,
                normalized_status=LOG_NORMALIZATION_CONVERTED,
                job_id=job_id,
            )
            conn.commit()

    # ------------------------------------------------------------------
    # Jobs
    # ------------------------------------------------------------------

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
            log_id=row["log_id"] if "log_id" in row.keys() else None,
            job_id=row["job_id"],
            machine=row["machine"],
            computer_name=row["computer_name"],
            document=row["document"],
            start_time=_parse_datetime(row["start_time"]),
            end_time=_parse_datetime(row["end_time"]),
            duration_seconds=int(row["duration_seconds"] or 0),
            fabric=row["fabric"] if "fabric" in row.keys() else None,
            planned_length_m=float(row["planned_length_m"] or 0.0),
            actual_printed_length_m=actual_printed,
            gap_before_m=gap_before,
            consumed_length_m=consumed,
            driver=row["driver"] if "driver" in row.keys() else None,
            source_path=row["source_path"] if "source_path" in row.keys() else None,
            job_type=(row["job_type"] or "PRODUCTION") if "job_type" in row.keys() else "PRODUCTION",
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
                if "suspicion_missing_length_m" in row.keys()
                else None
            ),
            suspicion_marked_at=_parse_datetime(row["suspicion_marked_at"])
            if "suspicion_marked_at" in row.keys()
            else None,
            review_status=row["review_status"] if "review_status" in row.keys() else None,
            review_note=row["review_note"] if "review_note" in row.keys() else None,
            reviewed_by=row["reviewed_by"] if "reviewed_by" in row.keys() else None,
            reviewed_at=_parse_datetime(row["reviewed_at"]) if "reviewed_at" in row.keys() else None,
            classification=row["classification"] if "classification" in row.keys() else None,
            created_at=_parse_datetime(row["created_at"]) if "created_at" in row.keys() else None,
            updated_at=_parse_datetime(row["updated_at"]) if "updated_at" in row.keys() else None,
        )

    def _job_unique_lookup(
        self,
        conn: sqlite3.Connection,
        job: ProductionJob,
    ) -> int | None:
        row = conn.execute(
            f"""
            SELECT id
            FROM {self.table_name}
            WHERE job_id = ?
              AND start_time = ?
              AND machine = ?
              AND document = ?
            """,
            (
                job.job_id,
                _dt_to_iso(job.start_time),
                job.machine,
                job.document,
            ),
        ).fetchone()
        return int(row["id"]) if row else None

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

    def list_available_jobs(
        self,
        *,
        machine: str | None = None,
        fabric: str | None = None,
        review_status: str | None = None,
        include_suspicious: bool = True,
        limit: int | None = None,
    ) -> list[ProductionJob]:
        """
        Return jobs that are still eligible to be added to a roll.

        Eligibility rules:
        - not already present in roll_items
        - counts_for_roll_export = 1 when the column exists
        - print_status not in FAILED / CANCELED / TEST / IGNORED
        - optional machine / fabric / review filters
        - optional exclusion of suspicious jobs
        """
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            columns = self.table_columns(conn)

            where_clauses = [
                "ri.job_row_id IS NULL",
            ]
            params: list[object] = []

            if "counts_for_roll_export" in columns:
                where_clauses.append(
                    f"COALESCE(j.counts_for_roll_export, 1) = 1"
                )

            if "print_status" in columns:
                where_clauses.append(
                    "UPPER(COALESCE(j.print_status, 'OK')) NOT IN ('FAILED', 'CANCELED', 'TEST', 'IGNORED')"
                )

            if machine:
                where_clauses.append("UPPER(COALESCE(j.machine, '')) = ?")
                params.append(machine.strip().upper())

            if fabric:
                where_clauses.append("UPPER(COALESCE(j.fabric, '')) = ?")
                params.append(fabric.strip().upper())

            if review_status and review_status.strip().upper() != "ALL":
                where_clauses.append("UPPER(COALESCE(j.review_status, '')) = ?")
                params.append(review_status.strip().upper())

            if not include_suspicious:
                suspicion_checks = []
                if "suspicion_category" in columns:
                    suspicion_checks.append("j.suspicion_category IS NULL")
                if "suspicion_reason" in columns:
                    suspicion_checks.append("j.suspicion_reason IS NULL")

                if suspicion_checks:
                    where_clauses.append(" AND ".join(suspicion_checks))

            sql = f"""
                SELECT j.*
                FROM {self.table_name} j
                LEFT JOIN roll_items ri
                    ON ri.job_row_id = j.id
                WHERE {" AND ".join(where_clauses)}
                ORDER BY j.start_time, j.job_id, j.id
            """

            if limit is not None:
                sql += " LIMIT ?"
                params.append(int(limit))

            rows = conn.execute(sql, tuple(params)).fetchall()
            return [self.row_to_job(row) for row in rows]

    def get_job_by_row_id(self, row_id: int) -> ProductionJob | None:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            row = conn.execute(
                f"SELECT * FROM {self.table_name} WHERE id = ?",
                (row_id,),
            ).fetchone()
            return self.row_to_job(row) if row else None

    def get_available_job_by_row_id(self, row_id: int) -> ProductionJob | None:
        jobs = self.list_available_jobs(limit=None)
        for job in jobs:
            if int(job.id or 0) == int(row_id):
                return job
        return None

    def job_is_assigned_to_any_roll(self, job_row_id: int) -> bool:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            row = conn.execute(
                """
                SELECT 1
                FROM roll_items
                WHERE job_row_id = ?
                LIMIT 1
                """,
                (job_row_id,),
            ).fetchone()
            return row is not None

    def get_job_by_job_id(self, job_id: str) -> ProductionJob | None:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            rows = conn.execute(
                f"SELECT * FROM {self.table_name} WHERE job_id = ? ORDER BY start_time, id",
                (job_id,),
            ).fetchall()

            if not rows:
                return None

            if len(rows) > 1:
                raise ValueError(
                    f"Mais de um registro encontrado para job_id={job_id}. Use o ID interno."
                )

            return self.row_to_job(rows[0])

    def save_job(self, job: ProductionJob) -> int:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            columns = self.table_columns(conn)
            now_iso = _now_iso()

            payload = {
                "log_id": getattr(job, "log_id", None),
                "job_id": job.job_id,
                "machine": job.machine,
                "computer_name": job.computer_name,
                "document": job.document,
                "start_time": _dt_to_iso(job.start_time),
                "end_time": _dt_to_iso(job.end_time),
                "duration_seconds": int(job.duration_seconds or 0),
                "fabric": job.fabric,
                "planned_length_m": float(job.planned_length_m or 0.0),
                "actual_printed_length_m": float(job.actual_printed_length_m or 0.0),
                "gap_before_m": float(job.gap_before_m or 0.0),
                "consumed_length_m": float(job.consumed_length_m or 0.0),
                "driver": job.driver,
                "source_path": job.source_path,
                "job_type": job.job_type,
                "is_rework": int(bool(job.is_rework)),
                "notes": job.notes,
                "print_status": job.print_status,
                "counts_as_valid_production": int(bool(job.counts_as_valid_production)),
                "counts_for_fabric_summary": int(bool(job.counts_for_fabric_summary)),
                "counts_for_roll_export": int(bool(job.counts_for_roll_export)),
                "error_reason": job.error_reason,
                "operator_code": job.operator_code,
                "operator_name": job.operator_name,
                "replacement_index": job.replacement_index,
                "suspicion_category": job.suspicion_category,
                "suspicion_reason": job.suspicion_reason,
                "suspicion_ratio": job.suspicion_ratio,
                "suspicion_missing_length_m": job.suspicion_missing_length_m,
                "suspicion_marked_at": _dt_to_iso(job.suspicion_marked_at),
                "review_status": job.review_status,
                "review_note": job.review_note,
                "reviewed_by": job.reviewed_by,
                "reviewed_at": _dt_to_iso(job.reviewed_at),
                "classification": getattr(job, "classification", None),
            }

            if "created_at" in columns and job.id is None:
                payload["created_at"] = now_iso
            if "updated_at" in columns:
                payload["updated_at"] = now_iso

            insert_columns = [name for name in payload.keys() if name in columns]
            placeholders = ", ".join("?" for _ in insert_columns)
            update_sql = ", ".join(
                f"{name}=excluded.{name}" for name in insert_columns if name != "created_at"
            )

            conn.execute(
                f"""
                INSERT INTO {self.table_name} ({", ".join(insert_columns)})
                VALUES ({placeholders})
                ON CONFLICT(job_id, start_time, machine, document)
                DO UPDATE SET {update_sql}
                """,
                [payload[name] for name in insert_columns],
            )

            job_row_id = self._job_unique_lookup(conn, job)
            if job_row_id is None:
                row = conn.execute("SELECT last_insert_rowid() AS row_id").fetchone()
                job_row_id = int(row["row_id"] or 0)

            log_id = getattr(job, "log_id", None)
            if log_id is not None:
                self._update_log_status(
                    conn,
                    int(log_id),
                    status=LOG_CONVERTED,
                    parse_status=LOG_PARSE_PARSED,
                    normalized_status=LOG_NORMALIZATION_CONVERTED,
                    job_id=job_row_id,
                )

            conn.commit()
            return int(job_row_id)

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

    def apply_review_failed_operational_effects(
        self,
        row_id: int,
        error_reason: str | None = None,
    ) -> None:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            columns = self.table_columns(conn)
            pk_column = self._pk_column(conn)

            current_row = conn.execute(
                f"""
                SELECT error_reason
                FROM {self.table_name}
                WHERE {pk_column} = ?
                """,
                (row_id,),
            ).fetchone()

            current_error_reason = current_row["error_reason"] if current_row else None

            fields: dict[str, object] = {}

            if "print_status" in columns:
                fields["print_status"] = "FAILED"

            if "counts_as_valid_production" in columns:
                fields["counts_as_valid_production"] = 0

            if "counts_for_fabric_summary" in columns:
                fields["counts_for_fabric_summary"] = 0

            if "counts_for_roll_export" in columns:
                fields["counts_for_roll_export"] = 0

            if "error_reason" in columns:
                if error_reason is not None and str(error_reason).strip():
                    fields["error_reason"] = error_reason
                elif not (current_error_reason or "").strip():
                    fields["error_reason"] = "REVIEW_CONFIRMED_FAILED"

            if "updated_at" in columns:
                fields["updated_at"] = _now_iso()

            if not fields:
                return

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

    # ------------------------------------------------------------------
    # Rolls
    # ------------------------------------------------------------------

    def row_to_roll(self, row: sqlite3.Row) -> Roll:
        return Roll(
            id=int(row["id"]),
            roll_name=row["roll_name"],
            machine=row["machine"],
            fabric=row["fabric"],
            status=row["status"],
            note=row["note"],
            created_at=_parse_datetime(row["created_at"]),
            closed_at=_parse_datetime(row["closed_at"]),
            updated_at=_parse_datetime(row["updated_at"]),
            exported_at=_parse_datetime(row["exported_at"]) if "exported_at" in row.keys() else None,
            reviewed_at=_parse_datetime(row["reviewed_at"]) if "reviewed_at" in row.keys() else None,
            reopened_at=_parse_datetime(row["reopened_at"]) if "reopened_at" in row.keys() else None,
        )

    def row_to_roll_item(self, row: sqlite3.Row) -> RollItem:
        return RollItem(
            id=int(row["id"]),
            roll_id=int(row["roll_id"]),
            job_row_id=int(row["job_row_id"]),
            job_id=row["job_id"],
            document=row["document"],
            machine=row["machine"],
            fabric=row["fabric"],
            sort_order=int(row["sort_order"]),
            planned_length_m=float(row["planned_length_m"] or 0.0),
            effective_printed_length_m=float(row["effective_printed_length_m"] or 0.0),
            consumed_length_m=float(row["consumed_length_m"] or 0.0),
            gap_before_m=float(row["gap_before_m"] or 0.0),
            metric_category=row["metric_category"],
            review_status=row["review_status"],
            snapshot_print_status=row["snapshot_print_status"],
            created_at=_parse_datetime(row["created_at"]),
        )

    def generate_roll_name(
        self,
        machine: str,
        opened_at: datetime | None = None,
        conn: sqlite3.Connection | None = None,
    ) -> str:
        owns_connection = conn is None
        conn = conn or self.connect()

        try:
            self.ensure_runtime_fields(conn)
            self.ensure_roll_tables(conn)

            dt = opened_at or datetime.now()
            machine_code = machine.strip().upper()
            date_key = dt.strftime("%Y%m%d")
            prefix = f"{machine_code}_{date_key}_"

            rows = conn.execute(
                """
                SELECT roll_name
                FROM rolls
                WHERE machine = ?
                  AND roll_name LIKE ?
                ORDER BY roll_name
                """,
                (machine_code, f"{prefix}%"),
            ).fetchall()

            max_seq = 0
            for row in rows:
                name = str(row["roll_name"])
                suffix = name.rsplit("_", 1)[-1]
                if suffix.isdigit():
                    max_seq = max(max_seq, int(suffix))

            next_seq = max_seq + 1
            return f"{machine_code}_{date_key}_{next_seq:03d}"
        finally:
            if owns_connection:
                conn.close()

    def create_roll(
        self,
        machine: str,
        fabric: str | None = None,
        note: str | None = None,
        roll_name: str | None = None,
    ) -> int:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            self.ensure_roll_tables(conn)

            machine_code = machine.strip().upper()
            final_roll_name = (roll_name.strip().upper() if roll_name else None) or self.generate_roll_name(
                machine=machine_code,
                conn=conn,
            )

            try:
                cursor = conn.execute(
                    """
                    INSERT INTO rolls (
                        roll_name,
                        machine,
                        fabric,
                        status,
                        note,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    (final_roll_name, machine_code, fabric, ROLL_OPEN, note),
                )
                conn.commit()
                return int(cursor.lastrowid)
            except sqlite3.IntegrityError as exc:
                message = str(exc).lower()
                if "rolls.roll_name" in message or "unique constraint failed: rolls.roll_name" in message:
                    raise ValueError(
                        f"Já existe um rolo com o nome '{final_roll_name}'. "
                        "Use outro nome ou deixe o Nexor gerar automaticamente."
                    ) from exc
                raise

    def append_roll_note(
        self,
        roll_id: int,
        note: str,
        operator: str | None = None,
    ) -> None:
        if not note or not note.strip():
            raise ValueError("A observação não pode estar vazia.")

        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            self.ensure_roll_tables(conn)

            row = conn.execute(
                "SELECT note FROM rolls WHERE id = ?",
                (roll_id,),
            ).fetchone()

            if not row:
                raise ValueError(f"Rolo não encontrado: id={roll_id}")

            current_note = row["note"] or ""
            timestamp = _now_display()
            operator_label = f"[{operator.strip()}] " if operator and operator.strip() else ""
            new_entry = f"[{timestamp}] {operator_label}{note.strip()}"

            final_note = f"{current_note}\n{new_entry}".strip() if current_note.strip() else new_entry

            conn.execute(
                """
                UPDATE rolls
                SET note = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (final_note, roll_id),
            )
            conn.commit()

    def list_rolls(self, status: str | None = None) -> list[Roll]:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            self.ensure_roll_tables(conn)

            sql = "SELECT * FROM rolls"
            params: tuple[object, ...] = ()

            if status and status.upper() != "ALL":
                sql += " WHERE status = ?"
                params = (status.upper(),)

            sql += " ORDER BY created_at DESC, id DESC"

            rows = conn.execute(sql, params).fetchall()
            return [self.row_to_roll(row) for row in rows]

    def get_roll(self, roll_id: int | None = None, roll_name: str | None = None) -> Roll | None:
        if roll_id is None and roll_name is None:
            raise ValueError("Informe roll_id ou roll_name.")

        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            self.ensure_roll_tables(conn)

            if roll_id is not None:
                row = conn.execute(
                    "SELECT * FROM rolls WHERE id = ?",
                    (roll_id,),
                ).fetchone()
                return self.row_to_roll(row) if row else None

            row = conn.execute(
                "SELECT * FROM rolls WHERE roll_name = ?",
                (roll_name,),
            ).fetchone()
            return self.row_to_roll(row) if row else None

    def _get_job_for_roll(
        self,
        conn: sqlite3.Connection,
        job_row_id: int | None = None,
        job_id: str | None = None,
    ) -> ProductionJob:
        if job_row_id is None and job_id is None:
            raise ValueError("Informe job_row_id ou job_id.")

        if job_row_id is not None:
            row = conn.execute(
                f"SELECT * FROM {self.table_name} WHERE id = ?",
                (job_row_id,),
            ).fetchone()
            if not row:
                raise ValueError(f"Job não encontrado para id={job_row_id}.")
            return self.row_to_job(row)

        rows = conn.execute(
            f"SELECT * FROM {self.table_name} WHERE job_id = ? ORDER BY start_time, id",
            (job_id,),
        ).fetchall()

        if not rows:
            raise ValueError(f"Job não encontrado para job_id={job_id}.")
        if len(rows) > 1:
            raise ValueError(
                f"Mais de um registro encontrado para job_id={job_id}. Use o ID interno."
            )

        return self.row_to_job(rows[0])

    def list_roll_items(self, roll_id: int) -> list[RollItem]:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            self.ensure_roll_tables(conn)

            rows = conn.execute(
                """
                SELECT *
                FROM roll_items
                WHERE roll_id = ?
                ORDER BY sort_order, id
                """,
                (roll_id,),
            ).fetchall()

            return [self.row_to_roll_item(row) for row in rows]

    def add_job_to_roll(
        self,
        roll_id: int,
        job_row_id: int | None = None,
        job_id: str | None = None,
    ) -> int:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            self.ensure_roll_tables(conn)

            roll_row = conn.execute(
                "SELECT * FROM rolls WHERE id = ?",
                (roll_id,),
            ).fetchone()
            if not roll_row:
                raise ValueError(f"Rolo não encontrado: id={roll_id}")

            roll = self.row_to_roll(roll_row)
            if roll.status != ROLL_OPEN:
                raise ValueError(f"O rolo {roll.roll_name} não está em aberto.")

            job = self._get_job_for_roll(conn, job_row_id=job_row_id, job_id=job_id)
            if job.id is None:
                raise ValueError("Job sem ID persistido.")

            existing_any = conn.execute(
                """
                SELECT ri.id, ri.roll_id, r.roll_name
                FROM roll_items ri
                JOIN rolls r ON r.id = ri.roll_id
                WHERE ri.job_row_id = ?
                """,
                (int(job.id),),
            ).fetchone()

            if existing_any:
                raise ValueError(
                    f"Este job já pertence ao rolo {existing_any['roll_name']} (id={existing_any['roll_id']})."
                )

            if roll.machine.strip().upper() != (job.machine or "").strip().upper():
                raise ValueError(
                    f"Máquina incompatível. Rolo={roll.machine} | Job={job.machine}"
                )

            if roll.fabric and job.fabric:
                if roll.fabric.strip().upper() != job.fabric.strip().upper():
                    raise ValueError(
                        f"Tecido incompatível. Rolo={roll.fabric} | Job={job.fabric}"
                    )

            next_sort = conn.execute(
                "SELECT COALESCE(MAX(sort_order), 0) + 1 AS next_sort FROM roll_items WHERE roll_id = ?",
                (roll_id,),
            ).fetchone()["next_sort"]

            decision = classify_job(job)
            cursor = conn.execute(
                """
                INSERT INTO roll_items (
                    roll_id,
                    job_row_id,
                    job_id,
                    document,
                    machine,
                    fabric,
                    sort_order,
                    planned_length_m,
                    effective_printed_length_m,
                    consumed_length_m,
                    gap_before_m,
                    metric_category,
                    review_status,
                    snapshot_print_status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    roll_id,
                    int(job.id),
                    job.job_id,
                    job.document,
                    job.machine,
                    job.fabric,
                    int(next_sort),
                    float(job.planned_length_m),
                    float(effective_printed_length_m(job)),
                    float(job.consumed_length_m),
                    float(job.gap_before_m),
                    decision.category or "OK",
                    job.review_status,
                    job.print_status,
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def remove_job_from_roll(
        self,
        roll_id: int,
        job_row_id: int | None = None,
        job_id: str | None = None,
    ) -> int:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            self.ensure_roll_tables(conn)

            roll_row = conn.execute(
                "SELECT * FROM rolls WHERE id = ?",
                (roll_id,),
            ).fetchone()
            if not roll_row:
                raise ValueError(f"Rolo não encontrado: id={roll_id}")

            roll = self.row_to_roll(roll_row)
            if roll.status != ROLL_OPEN:
                raise ValueError(f"O rolo {roll.roll_name} não está em aberto.")

            if job_row_id is None and job_id is None:
                raise ValueError("Informe job_row_id ou job_id.")

            if job_row_id is not None:
                cursor = conn.execute(
                    """
                    DELETE FROM roll_items
                    WHERE roll_id = ? AND job_row_id = ?
                    """,
                    (roll_id, job_row_id),
                )
            else:
                cursor = conn.execute(
                    """
                    DELETE FROM roll_items
                    WHERE roll_id = ? AND job_id = ?
                    """,
                    (roll_id, job_id),
                )

            conn.commit()
            return int(cursor.rowcount)

    def close_roll(self, roll_id: int, note: str | None = None) -> None:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            self.ensure_roll_tables(conn)

            roll_row = conn.execute(
                "SELECT * FROM rolls WHERE id = ?",
                (roll_id,),
            ).fetchone()
            if not roll_row:
                raise ValueError(f"Rolo não encontrado: id={roll_id}")

            existing_items = conn.execute(
                "SELECT COUNT(*) AS n FROM roll_items WHERE roll_id = ?",
                (roll_id,),
            ).fetchone()["n"]
            if int(existing_items) <= 0:
                raise ValueError("Não é possível fechar um rolo vazio.")

            current_note = roll_row["note"]
            final_note = current_note
            if note:
                final_note = f"{current_note}\n{note}".strip() if current_note else note

            conn.execute(
                """
                UPDATE rolls
                SET status = ?,
                    note = ?,
                    closed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (ROLL_CLOSED, final_note, roll_id),
            )
            conn.commit()

    def mark_roll_exported(self, roll_id: int) -> None:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            self.ensure_roll_tables(conn)
            conn.execute(
                """
                UPDATE rolls
                SET status = ?,
                    exported_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (ROLL_EXPORTED, roll_id),
            )
            conn.commit()

    def mark_roll_reviewed(self, roll_id: int) -> None:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            self.ensure_roll_tables(conn)
            conn.execute(
                """
                UPDATE rolls
                SET status = ?,
                    reviewed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (ROLL_REVIEWED, roll_id),
            )
            conn.commit()

    def reopen_roll(self, roll_id: int, note: str | None = None) -> None:
        with self.connect() as conn:
            self.ensure_runtime_fields(conn)
            self.ensure_roll_tables(conn)

            row = conn.execute("SELECT note FROM rolls WHERE id = ?", (roll_id,)).fetchone()
            if not row:
                raise ValueError(f"Rolo não encontrado: id={roll_id}")

            current_note = row["note"] or ""
            final_note = current_note
            if note and note.strip():
                stamp = f"[{_now_display()}] REOPEN: {note.strip()}"
                final_note = f"{current_note}\n{stamp}".strip() if current_note else stamp

            conn.execute(
                """
                UPDATE rolls
                SET status = ?,
                    note = ?,
                    reopened_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (ROLL_REOPENED, final_note, roll_id),
            )
            conn.commit()

    def get_roll_summary(self, roll_id: int) -> dict:
        roll = self.get_roll(roll_id=roll_id)
        if not roll:
            raise ValueError(f"Rolo não encontrado: id={roll_id}")

        items = self.list_roll_items(roll_id)

        total_planned = sum(item.planned_length_m for item in items)
        total_effective = sum(item.effective_printed_length_m for item in items)
        total_consumed = sum(item.consumed_length_m for item in items)
        total_gap = sum(item.gap_before_m for item in items)

        metric_counts: dict[str, int] = {}
        fabric_counts: dict[str, float] = {}

        for item in items:
            key = item.metric_category or "OK"
            metric_counts[key] = metric_counts.get(key, 0) + 1

            fab = (item.fabric or "SEM TECIDO").strip() or "SEM TECIDO"
            fabric_counts[fab] = fabric_counts.get(fab, 0.0) + float(item.effective_printed_length_m)

        efficiency = (total_effective / total_planned) if total_planned > 0 else None

        return {
            "roll": roll,
            "items": items,
            "jobs_count": len(items),
            "total_planned_m": total_planned,
            "total_effective_m": total_effective,
            "total_consumed_m": total_consumed,
            "total_gap_m": total_gap,
            "efficiency_ratio": efficiency,
            "metric_counts": metric_counts,
            "fabric_totals": fabric_counts,
        }


__all__ = [
    "ProductionRepository",
]