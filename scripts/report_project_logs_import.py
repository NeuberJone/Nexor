from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from storage.database import get_connection, init_database
from storage.import_audit_repository import ImportAuditRepository
from storage.log_sources_repository import LogSourceRepository


DEFAULT_SOURCE_NAME = "PROJECT_LOGS_IMPORT"
SQLITE_MAX_VARS = 900


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera relatório de validação do import usando logs reais do projeto."
    )
    parser.add_argument(
        "--source-name",
        default=DEFAULT_SOURCE_NAME,
        help=f"Nome do source de teste. Padrão: {DEFAULT_SOURCE_NAME}",
    )
    parser.add_argument(
        "--run-id",
        type=int,
        default=None,
        help="ID específico do import run a ser analisado. Se omitido, usa o mais recente.",
    )
    parser.add_argument(
        "--show-errors",
        type=int,
        default=15,
        help="Quantidade máxima de arquivos com erro a exibir. Padrão: 15",
    )
    parser.add_argument(
        "--show-suspicious",
        type=int,
        default=15,
        help="Quantidade máxima de jobs suspeitos a exibir. Padrão: 15",
    )
    parser.add_argument(
        "--show-pending",
        type=int,
        default=15,
        help="Quantidade máxima de jobs pendentes de review a exibir. Padrão: 15",
    )
    return parser.parse_args()


def chunked(values: list[str], size: int) -> Iterable[list[str]]:
    for index in range(0, len(values), size):
        yield values[index:index + size]


def fmt_dt(value) -> str:
    if not value:
        return "-"
    text = str(value).strip()
    if not text:
        return "-"
    if "T" in text:
        return text.replace("T", " ")
    return text


def fmt_m(value) -> str:
    try:
        return f"{float(value or 0.0):.2f} m"
    except Exception:
        return "0.00 m"


def safe_text(value, default: str = "-") -> str:
    text = str(value or "").strip()
    return text or default


def fetch_jobs_for_file_paths(file_paths: list[str]) -> list:
    if not file_paths:
        return []

    conn = get_connection()
    rows = []

    try:
        for part in chunked(file_paths, SQLITE_MAX_VARS):
            placeholders = ",".join("?" for _ in part)
            sql = f"""
                SELECT
                    id,
                    job_id,
                    machine,
                    computer_name,
                    document,
                    fabric,
                    start_time,
                    end_time,
                    planned_length_m,
                    actual_printed_length_m,
                    gap_before_m,
                    consumed_length_m,
                    print_status,
                    review_status,
                    classification,
                    suspicion_category,
                    suspicion_reason,
                    source_path
                FROM production_jobs
                WHERE source_path IN ({placeholders})
                ORDER BY start_time DESC, id DESC
            """
            rows.extend(conn.execute(sql, tuple(part)).fetchall())
        return rows
    finally:
        conn.close()


def print_counter_block(title: str, counter: Counter) -> None:
    print(title)
    if not counter:
        print("  - -")
        print()
        return

    for key, value in counter.most_common():
        print(f"  - {safe_text(key)}: {value}")
    print()


def resolve_target_run(
    *,
    source_name: str,
    run_id: int | None,
):
    source_repo = LogSourceRepository()
    audit_repo = ImportAuditRepository()

    source = source_repo.get_by_name(source_name)
    if not source:
        print("Status: ERRO")
        print(f"Motivo: source não encontrado: {source_name}")
        print()
        print("Dica:")
        print("  python scripts/bootstrap_project_logs_source.py --disable-others --reset-checkpoint")
        raise SystemExit(1)

    source_id = int(source["id"])

    if run_id is not None:
        run = audit_repo.get_run(run_id)
        if not run:
            print("Status: ERRO")
            print(f"Motivo: import run não encontrado: id={run_id}")
            raise SystemExit(1)

        if int(run["source_id"]) != source_id:
            print("Status: ERRO")
            print(
                f"Motivo: o run {run_id} não pertence ao source '{source_name}'."
            )
            raise SystemExit(1)

        return source, run

    runs = audit_repo.list_runs(source_id=source_id, limit=1)
    if not runs:
        print("Status: ERRO")
        print(f"Motivo: nenhum import run encontrado para o source '{source_name}'.")
        print()
        print("Dica:")
        print("  python app.py --force-rescan")
        raise SystemExit(1)

    return source, runs[0]


def build_file_status_counter(run_files: list) -> Counter:
    counter: Counter = Counter()
    for row in run_files:
        counter[safe_text(row["status"])] += 1
    return counter


def build_counter(rows: list, field_name: str) -> Counter:
    counter: Counter = Counter()
    for row in rows:
        counter[safe_text(row[field_name])] += 1
    return counter


def print_error_files(rows: list, limit: int) -> None:
    print("Arquivos com erro:")
    error_rows = [row for row in rows if safe_text(row["status"]) == "ERROR"]

    if not error_rows:
        print("  - Nenhum")
        print()
        return

    for row in error_rows[:limit]:
        print(
            f"  - {safe_text(row['file_name'])} | "
            f"status={safe_text(row['status'])} | "
            f"job={safe_text(row['detected_job_id'])} | "
            f"motivo={safe_text(row['error_message'])}"
        )

    if len(error_rows) > limit:
        print(f"  ... e mais {len(error_rows) - limit} arquivo(s) com erro.")
    print()


def print_suspicious_jobs(rows: list, limit: int) -> None:
    print("Jobs suspeitos:")
    suspicious = [
        row for row in rows
        if safe_text(row["suspicion_category"]) != "-" or safe_text(row["suspicion_reason"]) != "-"
    ]

    if not suspicious:
        print("  - Nenhum")
        print()
        return

    for row in suspicious[:limit]:
        print(
            f"  - row_id={row['id']} | "
            f"job={safe_text(row['job_id'])} | "
            f"machine={safe_text(row['machine'])} | "
            f"fabric={safe_text(row['fabric'])} | "
            f"print_status={safe_text(row['print_status'])} | "
            f"review={safe_text(row['review_status'])} | "
            f"classification={safe_text(row['classification'])} | "
            f"suspicion={safe_text(row['suspicion_category'])} | "
            f"motivo={safe_text(row['suspicion_reason'])} | "
            f"consumed={fmt_m(row['consumed_length_m'])} | "
            f"file={Path(safe_text(row['source_path'], '')).name if safe_text(row['source_path'], '') != '-' else '-'}"
        )

    if len(suspicious) > limit:
        print(f"  ... e mais {len(suspicious) - limit} job(s) suspeito(s).")
    print()


def print_pending_jobs(rows: list, limit: int) -> None:
    print("Jobs pendentes de review:")
    pending = [row for row in rows if safe_text(row["review_status"]) == "PENDING_REVIEW"]

    if not pending:
        print("  - Nenhum")
        print()
        return

    for row in pending[:limit]:
        print(
            f"  - row_id={row['id']} | "
            f"job={safe_text(row['job_id'])} | "
            f"machine={safe_text(row['machine'])} | "
            f"fabric={safe_text(row['fabric'])} | "
            f"print_status={safe_text(row['print_status'])} | "
            f"classification={safe_text(row['classification'])} | "
            f"effective={fmt_m(row['actual_printed_length_m'])} | "
            f"gap={fmt_m(row['gap_before_m'])} | "
            f"consumed={fmt_m(row['consumed_length_m'])}"
        )

    if len(pending) > limit:
        print(f"  ... e mais {len(pending) - limit} job(s) pendente(s).")
    print()


def print_overview(
    *,
    source,
    run,
    run_files: list,
    jobs: list,
) -> None:
    print("\nNEXOR PROJECT LOGS REPORT\n")
    print(f"Source: {safe_text(source['name'])}")
    print(f"Path: {safe_text(source['path'])}")
    print(f"Run ID: {run['id']}")
    print(f"Iniciado em: {fmt_dt(run['started_at'])}")
    print(f"Finalizado em: {fmt_dt(run['finished_at'])}")
    print()

    print("Resumo do run:")
    print(f"  - total_found: {int(run['total_found'] or 0)}")
    print(f"  - imported_count: {int(run['imported_count'] or 0)}")
    print(f"  - duplicate_count: {int(run['duplicate_count'] or 0)}")
    print(f"  - error_count: {int(run['error_count'] or 0)}")
    print(f"  - arquivos auditados no run: {len(run_files)}")
    print(f"  - jobs localizados a partir desses arquivos: {len(jobs)}")
    print()


def main() -> int:
    args = parse_args()
    init_database()

    source, run = resolve_target_run(
        source_name=args.source_name,
        run_id=args.run_id,
    )

    audit_repo = ImportAuditRepository()
    run_files = list(audit_repo.list_run_files(int(run["id"])))

    file_paths = []
    for row in run_files:
        path = safe_text(row["file_path"], default="")
        if path:
            file_paths.append(path)

    jobs = fetch_jobs_for_file_paths(file_paths)

    print_overview(
        source=source,
        run=run,
        run_files=run_files,
        jobs=jobs,
    )

    print_counter_block("Status dos arquivos auditados:", build_file_status_counter(run_files))
    print_counter_block("Review status dos jobs:", build_counter(jobs, "review_status"))
    print_counter_block("Print status dos jobs:", build_counter(jobs, "print_status"))
    print_counter_block("Classification dos jobs:", build_counter(jobs, "classification"))
    print_counter_block("Suspicion category dos jobs:", build_counter(jobs, "suspicion_category"))
    print_counter_block("Máquinas detectadas:", build_counter(jobs, "machine"))
    print_counter_block("Tecidos detectados:", build_counter(jobs, "fabric"))

    print_error_files(run_files, args.show_errors)
    print_suspicious_jobs(jobs, args.show_suspicious)
    print_pending_jobs(jobs, args.show_pending)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())