from __future__ import annotations

import argparse
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


DEFAULT_TABLE_NAME = "production_jobs"
EXCLUDED_PRINT_STATUSES = {"FAILED", "CANCELED", "TEST"}
EXCLUDED_JOB_TYPES = {"TEST"}


@dataclass(frozen=True)
class SuspicionThresholds:
    min_planned_length_m: float = 0.30
    aborted_max_ratio: float = 0.15
    aborted_max_actual_m: float = 0.05
    partial_max_ratio: float = 0.90
    partial_min_missing_m: float = 0.20


@dataclass(frozen=True)
class SuspicionDecision:
    is_suspect: bool
    category: str | None
    ratio: float | None
    missing_length_m: float
    reason: str | None


@dataclass(frozen=True)
class JobSnapshot:
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
    planned_length_m: float
    actual_printed_length_m: float
    gap_before_m: float
    consumed_length_m: float


DEFAULT_THRESHOLDS = SuspicionThresholds()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Confere métricas do banco do Nexor e aponta jobs suspeitos."
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=resolve_default_db_path(),
        help="Caminho do banco SQLite. Padrão: tenta localizar nexor.db automaticamente.",
    )
    parser.add_argument(
        "--table",
        default=DEFAULT_TABLE_NAME,
        help=f"Nome da tabela de jobs. Padrão: {DEFAULT_TABLE_NAME}",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Quantidade máxima de itens exibidos por seção. Padrão: 20.",
    )
    return parser.parse_args()


def resolve_default_db_path() -> Path:
    base_dir = Path(__file__).resolve().parent

    candidates = [
        base_dir / "nexor.db",
        base_dir / "storage" / "nexor.db",
        base_dir / "data" / "nexor.db",
        base_dir / "database.db",
        base_dir / "storage" / "database.db",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


def validate_identifier(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"Nome de tabela inválido: {name!r}")
    return name


def connect_db(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(f"Banco não encontrado: {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def fetch_job_rows(conn: sqlite3.Connection, table_name: str) -> list[sqlite3.Row]:
    table_name = validate_identifier(table_name)
    cursor = conn.execute(f"SELECT * FROM {table_name}")
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
        default=actual_printed_length_m + gap_before_m,
    )

    return JobSnapshot(
        job_id=safe_text(row, "job_id", fallback="?"),
        document=safe_text(row, "document", fallback="<SEM DOCUMENTO>"),
        start_time=row_value(row, "start_time"),
        machine=row_value(row, "machine"),
        computer_name=row_value(row, "computer_name"),
        fabric=row_value(row, "fabric"),
        print_status=safe_text(row, "print_status", fallback="OK").upper(),
        error_reason=row_value(row, "error_reason"),
        job_type=safe_text(row, "job_type", fallback="UNKNOWN").upper(),
        counts_as_valid_production=row_bool(
            row,
            "counts_as_valid_production",
            default=True,
        ),
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


def classify_suspicion(
    planned_length_m: float | None,
    actual_printed_length_m: float | None,
    thresholds: SuspicionThresholds = DEFAULT_THRESHOLDS,
) -> SuspicionDecision:
    planned = max(float(planned_length_m or 0.0), 0.0)
    actual = max(float(actual_printed_length_m or 0.0), 0.0)

    if planned <= 0:
        return SuspicionDecision(
            is_suspect=False,
            category=None,
            ratio=None,
            missing_length_m=0.0,
            reason="NO_PLANNED_LENGTH",
        )

    missing_length_m = max(planned - actual, 0.0)
    ratio = actual / planned if planned > 0 else None

    if planned < thresholds.min_planned_length_m:
        return SuspicionDecision(
            is_suspect=False,
            category=None,
            ratio=ratio,
            missing_length_m=missing_length_m,
            reason="BELOW_MIN_PLANNED_LENGTH",
        )

    if actual <= thresholds.aborted_max_actual_m or (ratio is not None and ratio <= thresholds.aborted_max_ratio):
        return SuspicionDecision(
            is_suspect=True,
            category="ABORTED_CANDIDATE",
            ratio=ratio,
            missing_length_m=missing_length_m,
            reason="VERY_LOW_ACTUAL_PRINTED",
        )

    if (
        ratio is not None
        and ratio < thresholds.partial_max_ratio
        and missing_length_m >= thresholds.partial_min_missing_m
    ):
        return SuspicionDecision(
            is_suspect=True,
            category="PARTIAL_CANDIDATE",
            ratio=ratio,
            missing_length_m=missing_length_m,
            reason="PRINTED_BELOW_EXPECTED",
        )

    return SuspicionDecision(
        is_suspect=False,
        category=None,
        ratio=ratio,
        missing_length_m=missing_length_m,
        reason=None,
    )


def split_candidates(
    jobs: Iterable[JobSnapshot],
    thresholds: SuspicionThresholds = DEFAULT_THRESHOLDS,
) -> tuple[list[tuple[JobSnapshot, SuspicionDecision]], list[tuple[JobSnapshot, SuspicionDecision]]]:
    aborted: list[tuple[JobSnapshot, SuspicionDecision]] = []
    partial: list[tuple[JobSnapshot, SuspicionDecision]] = []

    for job in jobs:
        if not is_candidate_eligible(job):
            continue

        decision = classify_suspicion(
            planned_length_m=job.planned_length_m,
            actual_printed_length_m=job.actual_printed_length_m,
            thresholds=thresholds,
        )

        if decision.category == "ABORTED_CANDIDATE":
            aborted.append((job, decision))
        elif decision.category == "PARTIAL_CANDIDATE":
            partial.append((job, decision))

    aborted.sort(
        key=lambda item: (
            item[1].ratio if item[1].ratio is not None else 999.0,
            -item[1].missing_length_m,
            item[0].start_time or "",
            item[0].job_id,
        )
    )
    partial.sort(
        key=lambda item: (
            item[1].ratio if item[1].ratio is not None else 999.0,
            -item[1].missing_length_m,
            item[0].start_time or "",
            item[0].job_id,
        )
    )

    return aborted, partial


def format_m(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.3f} m"


def format_ratio(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.1%}"


def print_header(title: str) -> None:
    print("=" * 70)
    print(title)
    print("=" * 70)


def print_candidates(
    title: str,
    items: list[tuple[JobSnapshot, SuspicionDecision]],
    limit: int,
) -> None:
    print(f"\n{title}: {len(items)}")

    if not items:
        return

    for job, decision in items[:limit]:
        print(
            f"- {job.job_id} | {job.document} | {job.start_time or '-'} | "
            f"planned={format_m(job.planned_length_m)} | "
            f"actual={format_m(job.actual_printed_length_m)} | "
            f"gap={format_m(job.gap_before_m)} | "
            f"consumed={format_m(job.consumed_length_m)} | "
            f"ratio={format_ratio(decision.ratio)} | "
            f"missing={format_m(decision.missing_length_m)} | "
            f"{decision.category}"
        )

    remaining = len(items) - limit
    if remaining > 0:
        print(f"... e mais {remaining} item(ns).")


def main() -> int:
    args = parse_args()

    try:
        with connect_db(args.db) as conn:
            rows = fetch_job_rows(conn, args.table)
    except Exception as exc:
        print_header("CHECK METRICS")
        print(f"Erro ao ler o banco: {exc}")
        return 1

    jobs = build_job_snapshots(rows)
    eligible_jobs = [job for job in jobs if is_candidate_eligible(job)]
    aborted_candidates, partial_candidates = split_candidates(eligible_jobs)

    total_planned = sum(job.planned_length_m for job in jobs)
    total_actual = sum(job.actual_printed_length_m for job in jobs)
    total_gap = sum(job.gap_before_m for job in jobs)
    total_consumed = sum(job.consumed_length_m for job in jobs)

    global_ratio = (total_actual / total_planned) if total_planned > 0 else None

    print_header("CHECK METRICS")
    print(f"Banco: {args.db}")
    print(f"Tabela: {args.table}")
    print(f"Jobs lidos: {len(jobs)}")
    print(f"Jobs elegíveis para revisão: {len(eligible_jobs)}")
    print(f"Planejado total: {format_m(total_planned)}")
    print(f"Impresso real total: {format_m(total_actual)}")
    print(f"Gap total: {format_m(total_gap)}")
    print(f"Consumido total: {format_m(total_consumed)}")
    print(f"Eficiência global (real/planejado): {format_ratio(global_ratio)}")

    print_candidates("Abortados candidatos", aborted_candidates, args.limit)
    print_candidates("Parciais candidatos", partial_candidates, args.limit)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
