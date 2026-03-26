from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from storage.database import get_connection, init_database
from storage.import_audit_repository import ImportAuditRepository
from storage.log_sources_repository import LogSourceRepository


DEFAULT_SOURCE_NAME = "PROJECT_LOGS_IMPORT"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compara o comportamento do Nexor com expectativas operacionais simples para logs reais."
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
        "--partial-threshold",
        type=float,
        default=0.05,
        help="Limite inferior para considerar parcial. Padrão: 0.05",
    )
    parser.add_argument(
        "--complete-threshold",
        type=float,
        default=0.95,
        help="Limite mínimo para considerar completo. Padrão: 0.95",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Máximo de divergências exibidas. Padrão: 25",
    )
    return parser.parse_args()


def safe_text(value, default: str = "-") -> str:
    text = str(value or "").strip()
    return text or default


def safe_upper(value) -> str:
    return safe_text(value, default="").upper()


def fmt_m(value) -> str:
    try:
        return f"{float(value or 0.0):.2f} m"
    except Exception:
        return "0.00 m"


def fmt_ratio(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value * 100:.1f}%"


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


def fetch_run_rows(run_id: int) -> list:
    conn = get_connection()
    try:
        sql = """
            SELECT
                il.id AS audit_id,
                il.file_name,
                il.file_path,
                il.status AS audit_status,
                il.error_message,

                pj.id AS job_row_id,
                pj.job_id,
                pj.machine,
                pj.document,
                pj.fabric,
                pj.print_status,
                pj.review_status,
                pj.classification,
                pj.suspicion_category,
                pj.suspicion_reason,
                pj.planned_length_m,
                pj.actual_printed_length_m,
                pj.gap_before_m,
                pj.consumed_length_m

            FROM imported_logs il
            LEFT JOIN production_jobs pj
                ON pj.source_path = il.file_path
            WHERE il.run_id = ?
            ORDER BY il.id DESC
        """
        return conn.execute(sql, (int(run_id),)).fetchall()
    finally:
        conn.close()


def expected_bucket(
    *,
    planned_length_m: float,
    actual_printed_length_m: float,
    partial_threshold: float,
    complete_threshold: float,
) -> tuple[str, float | None]:
    planned = float(planned_length_m or 0.0)
    actual = float(actual_printed_length_m or 0.0)

    if planned <= 0:
        return "UNKNOWN", None

    ratio = actual / planned if planned > 0 else None

    if ratio is None:
        return "UNKNOWN", None
    if ratio <= partial_threshold:
        return "ABORTED"
    if ratio < complete_threshold:
        return "PARTIAL"
    return "COMPLETE"


def infer_observed_bucket(row) -> str:
    audit_status = safe_upper(row["audit_status"])
    print_status = safe_upper(row["print_status"])
    suspicion = safe_upper(row["suspicion_category"])
    review_status = safe_upper(row["review_status"])
    classification = safe_upper(row["classification"])

    if audit_status == "ERROR":
        return "ERROR"
    if safe_text(row["job_row_id"]) == "-":
        return "NO_JOB"

    if print_status in {"ABORTED", "FAILED", "CANCELLED"}:
        return "ABORTED"
    if print_status in {"PARTIAL", "INCOMPLETE"}:
        return "PARTIAL"
    if print_status in {"OK", "COMPLETED", "COMPLETE"}:
        return "COMPLETE"

    if classification in {"ABORTED", "FAILED"}:
        return "ABORTED"
    if classification in {"PARTIAL", "INCOMPLETE"}:
        return "PARTIAL"
    if classification in {"COMPLETE", "OK"}:
        return "COMPLETE"

    if suspicion in {"ABORTED_CANDIDATE", "FAILED_CANDIDATE"}:
        return "ABORTED"
    if suspicion in {"PARTIAL_CANDIDATE", "INCOMPLETE_CANDIDATE"}:
        return "PARTIAL"

    if review_status == "REVIEWED_OK":
        return "COMPLETE"

    return "UNCLASSIFIED"


def is_mismatch(expected: str, observed: str) -> bool:
    if expected == "UNKNOWN":
        return False
    if observed in {"ERROR", "NO_JOB", "UNCLASSIFIED"}:
        return True
    return expected != observed


def print_counter_block(title: str, counter: Counter) -> None:
    print(title)
    if not counter:
        print("  - -")
        print()
        return

    for key, value in counter.most_common():
        print(f"  - {key}: {value}")
    print()


def print_mismatch(row, expected: str, observed: str, ratio: float | None) -> None:
    print(
        f"audit_id={row['audit_id']} | "
        f"job_row_id={safe_text(row['job_row_id'])} | "
        f"expected={expected} | "
        f"observed={observed} | "
        f"ratio={fmt_ratio(ratio)} | "
        f"planned={fmt_m(row['planned_length_m'])} | "
        f"actual={fmt_m(row['actual_printed_length_m'])} | "
        f"gap={fmt_m(row['gap_before_m'])} | "
        f"consumed={fmt_m(row['consumed_length_m'])} | "
        f"print={safe_text(row['print_status'])} | "
        f"review={safe_text(row['review_status'])} | "
        f"classification={safe_text(row['classification'])} | "
        f"suspicion={safe_text(row['suspicion_category'])} | "
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

    if args.partial_threshold < 0:
        print("Status: ERRO")
        print("Motivo: --partial-threshold não pode ser negativo.")
        return 1

    if args.complete_threshold <= args.partial_threshold:
        print("Status: ERRO")
        print("Motivo: --complete-threshold deve ser maior que --partial-threshold.")
        return 1

    source, run = resolve_target_run(args.source_name, args.run_id)
    rows = fetch_run_rows(int(run["id"]))

    expected_counter: Counter = Counter()
    observed_counter: Counter = Counter()
    mismatch_rows: list[tuple[object, str, str, float | None]] = []

    comparable_rows = 0

    for row in rows:
        expected, ratio = expected_bucket(
            planned_length_m=float(row["planned_length_m"] or 0.0),
            actual_printed_length_m=float(row["actual_printed_length_m"] or 0.0),
            partial_threshold=float(args.partial_threshold),
            complete_threshold=float(args.complete_threshold),
        )
        observed = infer_observed_bucket(row)

        expected_counter[expected] += 1
        observed_counter[observed] += 1

        if expected != "UNKNOWN":
            comparable_rows += 1

        if is_mismatch(expected, observed):
            mismatch_rows.append((row, expected, observed, ratio))

    print("\nNEXOR PROJECT LOG EXPECTATIONS CHECK\n")
    print(f"Source: {safe_text(source['name'])}")
    print(f"Run ID: {run['id']}")
    print(f"Partial threshold: {args.partial_threshold:.2f}")
    print(f"Complete threshold: {args.complete_threshold:.2f}")
    print(f"Linhas avaliadas: {len(rows)}")
    print(f"Linhas comparáveis: {comparable_rows}")
    print(f"Divergências: {len(mismatch_rows)}")
    print()

    print_counter_block("Buckets esperados pela régua de teste:", expected_counter)
    print_counter_block("Buckets observados no banco:", observed_counter)

    print("Divergências detectadas:")
    if not mismatch_rows:
        print("  - Nenhuma")
        print()
        return 0

    shown = mismatch_rows[: max(int(args.limit), 1)]
    for row, expected, observed, ratio in shown:
        print_mismatch(row, expected, observed, ratio)
        print()

    if len(mismatch_rows) > len(shown):
        print(f"... e mais {len(mismatch_rows) - len(shown)} divergência(s).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())