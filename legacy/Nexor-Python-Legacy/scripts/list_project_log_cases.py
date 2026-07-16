from __future__ import annotations

import argparse
import sys
from pathlib import Path

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
        description="Lista casos importados da pasta logs_import para investigação manual."
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
        help="ID específico do import run. Se omitido, usa o mais recente.",
    )
    parser.add_argument(
        "--status",
        default=None,
        help="Filtro por status do arquivo auditado. Ex.: IMPORTED, DUPLICATE, ERROR",
    )
    parser.add_argument(
        "--review-status",
        default=None,
        help="Filtro por review_status do job. Ex.: PENDING_REVIEW, REVIEWED_OK",
    )
    parser.add_argument(
        "--classification",
        default=None,
        help="Filtro por classification do job.",
    )
    parser.add_argument(
        "--print-status",
        default=None,
        help="Filtro por print_status do job.",
    )
    parser.add_argument(
        "--only-suspicious",
        action="store_true",
        help="Mostra apenas jobs suspeitos.",
    )
    parser.add_argument(
        "--machine",
        default=None,
        help="Filtro por máquina do job.",
    )
    parser.add_argument(
        "--fabric",
        default=None,
        help="Filtro por tecido do job.",
    )
    parser.add_argument(
        "--contains",
        default=None,
        help="Texto que deve aparecer no nome do arquivo, documento, job_id ou motivo.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=30,
        help="Máximo de linhas exibidas. Padrão: 30",
    )
    return parser.parse_args()


def safe_text(value, default: str = "-") -> str:
    text = str(value or "").strip()
    return text or default


def safe_upper(value) -> str | None:
    text = str(value or "").strip()
    return text.upper() if text else None


def fmt_m(value) -> str:
    try:
        return f"{float(value or 0.0):.2f} m"
    except Exception:
        return "0.00 m"


def resolve_target_run(source_name: str, run_id: int | None):
    source_repo = LogSourceRepository()
    audit_repo = ImportAuditRepository()

    source = source_repo.get_by_name(source_name)
    if not source:
        print("Status: ERRO")
        print(f"Motivo: source não encontrado: {source_name}")
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
            print(f"Motivo: o run {run_id} não pertence ao source '{source_name}'.")
            raise SystemExit(1)

        return source, run

    runs = audit_repo.list_runs(source_id=source_id, limit=1)
    if not runs:
        print("Status: ERRO")
        print(f"Motivo: nenhum import run encontrado para o source '{source_name}'.")
        raise SystemExit(1)

    return source, runs[0]


def fetch_case_rows(run_id: int) -> list:
    conn = get_connection()

    try:
        sql = """
            SELECT
                il.id AS audit_id,
                il.run_id,
                il.source_id,
                il.file_name,
                il.file_path,
                il.file_hash,
                il.status AS audit_status,
                il.error_message,
                il.detected_job_id,
                il.detected_computer_name,
                il.detected_machine,

                pj.id AS job_row_id,
                pj.job_id,
                pj.machine,
                pj.computer_name,
                pj.document,
                pj.fabric,
                pj.print_status,
                pj.review_status,
                pj.classification,
                pj.suspicion_category,
                pj.suspicion_reason,
                pj.actual_printed_length_m,
                pj.gap_before_m,
                pj.consumed_length_m,
                pj.source_path

            FROM imported_logs il
            LEFT JOIN production_jobs pj
                ON pj.source_path = il.file_path
            WHERE il.run_id = ?
            ORDER BY il.id DESC
        """
        return conn.execute(sql, (int(run_id),)).fetchall()
    finally:
        conn.close()


def row_matches(row, args: argparse.Namespace) -> bool:
    if args.status and safe_upper(row["audit_status"]) != safe_upper(args.status):
        return False

    if args.review_status and safe_upper(row["review_status"]) != safe_upper(args.review_status):
        return False

    if args.classification and safe_upper(row["classification"]) != safe_upper(args.classification):
        return False

    if args.print_status and safe_upper(row["print_status"]) != safe_upper(args.print_status):
        return False

    if args.machine and safe_upper(row["machine"]) != safe_upper(args.machine):
        return False

    if args.fabric and safe_upper(row["fabric"]) != safe_upper(args.fabric):
        return False

    if args.only_suspicious:
        if safe_text(row["suspicion_category"]) == "-" and safe_text(row["suspicion_reason"]) == "-":
            return False

    if args.contains:
        needle = args.contains.strip().lower()
        haystack = " ".join(
            [
                safe_text(row["file_name"], ""),
                safe_text(row["document"], ""),
                safe_text(row["job_id"], ""),
                safe_text(row["error_message"], ""),
                safe_text(row["suspicion_reason"], ""),
                safe_text(row["classification"], ""),
            ]
        ).lower()
        if needle not in haystack:
            return False

    return True


def print_row(row) -> None:
    print(
        f"audit_id={row['audit_id']} | "
        f"job_row_id={safe_text(row['job_row_id'])} | "
        f"file_status={safe_text(row['audit_status'])} | "
        f"job={safe_text(row['job_id'])} | "
        f"machine={safe_text(row['machine'])} | "
        f"fabric={safe_text(row['fabric'])} | "
        f"review={safe_text(row['review_status'])} | "
        f"print={safe_text(row['print_status'])} | "
        f"classification={safe_text(row['classification'])} | "
        f"suspicion={safe_text(row['suspicion_category'])} | "
        f"effective={fmt_m(row['actual_printed_length_m'])} | "
        f"gap={fmt_m(row['gap_before_m'])} | "
        f"consumed={fmt_m(row['consumed_length_m'])} | "
        f"file={safe_text(row['file_name'])}"
    )

    extra = []
    if safe_text(row["document"]) != "-":
        extra.append(f"doc={safe_text(row['document'])}")
    if safe_text(row["error_message"]) != "-":
        extra.append(f"erro={safe_text(row['error_message'])}")
    if safe_text(row["suspicion_reason"]) != "-":
        extra.append(f"motivo={safe_text(row['suspicion_reason'])}")

    if extra:
        print("  " + " | ".join(extra))


def main() -> int:
    args = parse_args()
    init_database()

    source, run = resolve_target_run(args.source_name, args.run_id)
    rows = fetch_case_rows(int(run["id"]))

    matched = [row for row in rows if row_matches(row, args)]

    print("\nNEXOR PROJECT LOG CASES\n")
    print(f"Source: {safe_text(source['name'])}")
    print(f"Run ID: {run['id']}")
    print(f"Total de casos no run: {len(rows)}")
    print(f"Total após filtros: {len(matched)}")
    print()

    if not matched:
        print("Nenhum caso encontrado com esses filtros.")
        return 0

    shown = matched[: max(int(args.limit), 1)]
    for row in shown:
        print_row(row)
        print()

    if len(matched) > len(shown):
        print(f"... e mais {len(matched) - len(shown)} caso(s).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())