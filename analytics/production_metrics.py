from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from core.suspicion_rules import (
    ABORTED_CANDIDATE,
    PARTIAL_CANDIDATE,
    DEFAULT_THRESHOLDS,
    SuspicionDecision,
    SuspicionThresholds,
    classify_suspicion,
)

DEFAULT_DB_CANDIDATES = (
    "nexor.db",
    "database.db",
)

DEFAULT_TABLE_CANDIDATES = (
    "production_jobs",
    "jobs",
    "print_jobs",
)

EXCLUDED_PRINT_STATUSES = {"FAILED", "CANCELED", "TEST"}
EXCLUDED_JOB_TYPES = {"TEST"}


@dataclass(frozen=True)
class JobSnapshot:
    rowid: int | None
    job_id: str
    document: str
    start_time: str | None
    machine: str | None
    computer_name: str | None
    fabric: str | None
    print_status: str
    error_reason: str | None
    job_type: str
    counts_as_valid_production: bool
    counts_for_fabric_summary: bool
    counts_for_roll_export: bool
    planned_length_m: float
    actual_printed_length_m: float
    gap_before_m: float
    consumed_length_m: float


@dataclass(frozen=True)
class ClassifiedCandidate:
    job: JobSnapshot
    decision: SuspicionDecision


def resolve_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_default_db_path() -> Path:
    root = resolve_project_root()

    candidates: list[Path] = []
    for db_name in DEFAULT_DB_CANDIDATES:
        candidates.append(root / db_name)
        candidates.append(root / "storage" / db_name)
        candidates.append(root / "data" / db_name)

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return root / DEFAULT_DB_CANDIDATES[0]


def validate_identifier(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"Nome inválido: {name!r}")
    return name


def connect_db(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(f"Banco não encontrado: {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def list_tables(conn: sqlite3.Connection) -> list[str]:
    cursor = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
        """
    )
    return [str(row["name"]) for row in cursor.fetchall()]


def table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    table_name = validate_identifier(table_name)
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    return {str(row["name"]) for row in cursor.fetchall()}


def discover_jobs_table(conn: sqlite3.Connection, requested_table: str | None = None) -> str:
    if requested_table:
        requested_table = validate_identifier(requested_table)
        existing_tables = set(list_tables(conn))
        if requested_table not in existing_tables:
            raise ValueError(f"Tabela não encontrada: {requested_table}")
        return requested_table

    all_tables = list_tables(conn)

    for candidate in DEFAULT_TABLE_CANDIDATES:
        if candidate in all_tables:
            return candidate

    for table_name in all_tables:
        cols = table_columns(conn, table_name)
        if "job_id" in cols and "planned_length_m" in cols and (
            "actual_printed_length_m" in cols or "printed_length_m" in cols
        ):
            return table_name

    raise ValueError("Não foi possível descobrir a tabela de jobs.")


def fetch_job_rows(conn: sqlite3.Connection, table_name: str) -> list[sqlite3.Row]:
    table_name = validate_identifier(table_name)

    cursor = conn.execute(f"SELECT rowid AS _rowid_, * FROM {table_name}")
    rows = cursor.fetchall()

    def sort_key(row: sqlite3.Row) -> tuple[str, str]:
        return (
            safe_text(row, "start_time"),
            safe_text(row, "job_id"),
        )

    return sorted(rows, key=sort_key)


def build_job_snapshots(rows: Iterable[sqlite3.Row]) -> list[JobSnapshot]:
    return [row_to_job_snapshot(row) for row in rows]


def row_to_job_snapshot(row: sqlite3.Row) -> JobSnapshot:
    planned_length_m = row_number(row, "planned_length_m", default=0.0)

    actual_printed_length_m = row_number(
        row,
        "actual_printed_length_m",
        "printed_length_m",
        default=0.0,
    )

    gap_before_m = row_number(row, "gap_before_m", default=0.0)

    consumed_length_m = row_number(
        row,
        "consumed_length_m",
        "total_consumption_m",
        default=actual_printed_length_m + gap_before_m,
    )

    return JobSnapshot(
        rowid=row_int(row, "_rowid_", default=None),
        job_id=safe_text(row, "job_id", fallback="?"),
        document=safe_text(row, "document", fallback="<SEM DOCUMENTO>"),
        start_time=row_value(row, "start_time"),
        machine=row_value(row, "machine"),
        computer_name=row_value(row, "computer_name"),
        fabric=row_value(row, "fabric"),
        print_status=safe_text(row, "print_status", fallback="OK").upper(),
        error_reason=row_value(row, "error_reason"),
        job_type=safe_text(row, "job_type", fallback="UNKNOWN").upper(),
        counts_as_valid_production=row_bool(row, "counts_as_valid_production", default=True),
        counts_for_fabric_summary=row_bool(row, "counts_for_fabric_summary", default=True),
        counts_for_roll_export=row_bool(row, "counts_for_roll_export", default=True),
        planned_length_m=planned_length_m,
        actual_printed_length_m=actual_printed_length_m,
        gap_before_m=gap_before_m,
        consumed_length_m=consumed_length_m,
    )


def row_value(row: sqlite3.Row, key: str, default: Any = None) -> Any:
    if key not in row.keys():
        return default
    value = row[key]
    return default if value is None else value


def safe_text(row: sqlite3.Row, key: str, fallback: str = "") -> str:
    value = row_value(row, key, fallback)
    if value is None:
        return fallback
    return str(value).strip() or fallback


def row_number(row: sqlite3.Row, *keys: str, default: float = 0.0) -> float:
    for key in keys:
        if key not in row.keys():
            continue

        value = row[key]
        if value in (None, ""):
            continue

        if isinstance(value, (int, float)):
            return float(value)

        try:
            return float(str(value).replace(",", ".").strip())
        except ValueError:
            continue

    return float(default)


def row_int(row: sqlite3.Row, key: str, default: int | None = None) -> int | None:
    if key not in row.keys():
        return default

    value = row[key]
    if value in (None, ""):
        return default

    try:
        return int(value)
    except Exception:
        return default


def row_bool(row: sqlite3.Row, key: str, default: bool = False) -> bool:
    if key not in row.keys():
        return default

    value = row[key]

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


def effective_printed_length_m(job: JobSnapshot) -> float:
    """
    Retorna o comprimento efetivamente impresso usado na análise.

    Regra:
    - se actual_printed_length_m vier preenchido (> 0), ele é a fonte de verdade
    - se vier zerado, usa fallback por consumed_length_m - gap_before_m

    Isso evita classificar como abortado um job que claramente consumiu
    quase tudo do planejado, mas cuja coluna actual ainda está zerada.
    """
    actual = max(float(job.actual_printed_length_m or 0.0), 0.0)
    if actual > 0:
        return actual

    estimated = max(
        float(job.consumed_length_m or 0.0) - float(job.gap_before_m or 0.0),
        0.0,
    )
    return estimated


def is_candidate_eligible(job: JobSnapshot) -> bool:
    if job.planned_length_m <= 0:
        return False

    if not job.counts_as_valid_production:
        return False

    if job.print_status in EXCLUDED_PRINT_STATUSES:
        return False

    if job.job_type in EXCLUDED_JOB_TYPES:
        return False

    return True


def classify_job(
    job: JobSnapshot,
    thresholds: SuspicionThresholds = DEFAULT_THRESHOLDS,
) -> SuspicionDecision:
    return classify_suspicion(
        planned_length_m=job.planned_length_m,
        effective_printed_length_m=effective_printed_length_m(job),
        thresholds=thresholds,
    )


def collect_candidates(
    jobs: Iterable[JobSnapshot],
    thresholds: SuspicionThresholds = DEFAULT_THRESHOLDS,
) -> tuple[list[ClassifiedCandidate], list[ClassifiedCandidate]]:
    aborted: list[ClassifiedCandidate] = []
    partial: list[ClassifiedCandidate] = []

    for job in jobs:
        if not is_candidate_eligible(job):
            continue

        decision = classify_job(job, thresholds=thresholds)

        if decision.category == ABORTED_CANDIDATE:
            aborted.append(ClassifiedCandidate(job=job, decision=decision))
        elif decision.category == PARTIAL_CANDIDATE:
            partial.append(ClassifiedCandidate(job=job, decision=decision))

    aborted.sort(key=_candidate_sort_key)
    partial.sort(key=_candidate_sort_key)

    return aborted, partial


def _candidate_sort_key(item: ClassifiedCandidate) -> tuple[float, float, str, str]:
    ratio = item.decision.ratio if item.decision.ratio is not None else 999.0
    return (
        ratio,
        -item.decision.missing_length_m,
        item.job.start_time or "",
        item.job.job_id,
    )


def format_m(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.3f}"


def format_ratio(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.1%}"


def print_candidates_block(
    title: str,
    items: list[ClassifiedCandidate],
    limit: int,
) -> None:
    print(f"\n{title}: {len(items)}")

    if not items:
        return

    for candidate in items[:limit]:
        job = candidate.job
        decision = candidate.decision
        effective = effective_printed_length_m(job)

        print(
            f"- {job.job_id} | {job.document} | {job.start_time or '-'} | "
            f"planned={format_m(job.planned_length_m)} | "
            f"actual={format_m(job.actual_printed_length_m)} | "
            f"effective={format_m(effective)} | "
            f"gap={format_m(job.gap_before_m)} | "
            f"consumed={format_m(job.consumed_length_m)} | "
            f"ratio={format_ratio(decision.ratio)} | "
            f"missing={format_m(decision.missing_length_m)} | "
            f"{decision.category}"
        )

    remaining = len(items) - limit
    if remaining > 0:
        print(f"... e mais {remaining} item(ns).")


def load_jobs_from_db(
    db_path: Path | None = None,
    table_name: str | None = None,
) -> tuple[sqlite3.Connection, str, list[JobSnapshot]]:
    db_path = db_path or resolve_default_db_path()
    conn = connect_db(db_path)
    resolved_table = discover_jobs_table(conn, table_name)
    rows = fetch_job_rows(conn, resolved_table)
    jobs = build_job_snapshots(rows)
    return conn, resolved_table, jobs


def apply_failed_status_to_aborted_candidates(
    conn: sqlite3.Connection,
    table_name: str,
    candidates: Iterable[ClassifiedCandidate],
) -> int:
    table_name = validate_identifier(table_name)
    columns = table_columns(conn, table_name)
    applied = 0

    for candidate in candidates:
        job = candidate.job

        updates: dict[str, Any] = {}

        if "print_status" in columns:
            updates["print_status"] = "FAILED"

        if "counts_as_valid_production" in columns:
            updates["counts_as_valid_production"] = 0

        if "counts_for_fabric_summary" in columns:
            updates["counts_for_fabric_summary"] = 0

        if "counts_for_roll_export" in columns:
            updates["counts_for_roll_export"] = 0

        if "error_reason" in columns and not (job.error_reason or "").strip():
            updates["error_reason"] = "AUTO_ABORTED_CANDIDATE"

        if not updates:
            continue

        set_clause = ", ".join(f"{column} = ?" for column in updates.keys())
        params = list(updates.values())

        if job.rowid is not None:
            sql = f"UPDATE {table_name} SET {set_clause} WHERE rowid = ?"
            params.append(job.rowid)
        else:
            sql = f"UPDATE {table_name} SET {set_clause} WHERE job_id = ?"
            params.append(job.job_id)

        cursor = conn.execute(sql, params)
        if cursor.rowcount > 0:
            applied += 1

    conn.commit()
    return applied
