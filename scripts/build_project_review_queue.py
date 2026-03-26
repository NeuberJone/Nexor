from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera uma fila priorizada de revisão operacional a partir dos CSVs de análise."
    )
    parser.add_argument(
        "--cases-csv",
        default=str(PROJECT_ROOT / "exports" / "project_log_cases.csv"),
        help="CSV gerado por export_project_log_cases_csv.py",
    )
    parser.add_argument(
        "--compare-csv",
        default=str(PROJECT_ROOT / "exports" / "manifest_vs_imported_cases.csv"),
        help="CSV gerado por compare_manifest_to_imported_cases.py",
    )
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "exports" / "project_review_queue.csv"),
        help="CSV de saída com a fila priorizada.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limite máximo de linhas exportadas.",
    )
    return parser.parse_args()


def safe_text(value, default: str = "") -> str:
    text = str(value or "").strip()
    return text if text else default


def safe_upper(value) -> str:
    return safe_text(value).upper()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        print("Status: ERRO")
        print(f"Motivo: arquivo não encontrado: {path}")
        raise SystemExit(1)

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build_compare_index(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for row in rows:
        file_path = safe_text(row.get("file_path"))
        if file_path and file_path not in index:
            index[file_path] = row
    return index


def classify_priority(case_row: dict[str, str], compare_row: dict[str, str] | None) -> tuple[int, str, str]:
    audit_status = safe_upper(case_row.get("audit_status"))
    review_status = safe_upper(case_row.get("review_status"))
    classification = safe_upper(case_row.get("classification"))
    print_status = safe_upper(case_row.get("print_status"))
    suspicion_category = safe_upper(case_row.get("suspicion_category"))
    compare_result = safe_upper(compare_row.get("result")) if compare_row else ""
    compare_issues = safe_text(compare_row.get("issues")) if compare_row else ""

    if audit_status == "ERROR":
        return 10, "IMPORT_ERROR", "Falha de importação ou persistência do arquivo"

    if compare_result == "MISSING_IN_IMPORT":
        return 20, "MISSING_IN_IMPORT", "Arquivo apareceu no manifesto mas não entrou no import"

    if compare_result == "MISMATCH":
        return 30, "MANIFEST_IMPORT_MISMATCH", compare_issues or "Divergência entre manifesto e banco"

    if suspicion_category:
        return 40, "SUSPICIOUS_JOB", suspicion_category or "Job marcado como suspeito"

    if review_status == "PENDING_REVIEW":
        return 50, "PENDING_REVIEW", "Job ainda pendente de revisão"

    if classification and classification not in {"OK", "COMPLETE"}:
        return 60, "CLASSIFICATION_ATTENTION", f"Classification={classification}"

    if print_status and print_status not in {"OK", "COMPLETE", "COMPLETED"}:
        return 70, "PRINT_STATUS_ATTENTION", f"PrintStatus={print_status}"

    return 90, "OK", "Sem ação imediata"


def build_output_row(
    case_row: dict[str, str],
    compare_row: dict[str, str] | None,
    priority: int,
    queue_status: str,
    review_reason: str,
) -> dict[str, str]:
    return {
        "priority": str(priority),
        "queue_status": queue_status,
        "review_reason": review_reason,
        "audit_id": safe_text(case_row.get("audit_id")),
        "job_row_id": safe_text(case_row.get("job_row_id")),
        "file_status": safe_text(case_row.get("audit_status")),
        "job_id": safe_text(case_row.get("job_id")),
        "machine": safe_text(case_row.get("machine")),
        "fabric": safe_text(case_row.get("fabric")),
        "review_status": safe_text(case_row.get("review_status")),
        "print_status": safe_text(case_row.get("print_status")),
        "classification": safe_text(case_row.get("classification")),
        "suspicion_category": safe_text(case_row.get("suspicion_category")),
        "suspicion_reason": safe_text(case_row.get("suspicion_reason")),
        "effective_m": safe_text(case_row.get("actual_printed_length_m")),
        "gap_m": safe_text(case_row.get("gap_before_m")),
        "consumed_m": safe_text(case_row.get("consumed_length_m")),
        "file_name": safe_text(case_row.get("file_name")),
        "file_path": safe_text(case_row.get("file_path")),
        "document": safe_text(case_row.get("document")),
        "error_message": safe_text(case_row.get("error_message")),
        "compare_result": safe_text(compare_row.get("result") if compare_row else ""),
        "compare_issues": safe_text(compare_row.get("issues") if compare_row else ""),
    }


def sort_key(row: dict[str, str]) -> tuple[int, str, str, str]:
    try:
        priority = int(row.get("priority", "999"))
    except Exception:
        priority = 999

    return (
        priority,
        safe_text(row.get("machine")),
        safe_text(row.get("fabric")),
        safe_text(row.get("file_name")),
    )


def main() -> int:
    args = parse_args()

    cases_path = Path(args.cases_csv).expanduser().resolve()
    compare_path = Path(args.compare_csv).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    cases_rows = load_csv_rows(cases_path)
    compare_rows = load_csv_rows(compare_path)
    compare_index = build_compare_index(compare_rows)

    queue_rows: list[dict[str, str]] = []

    for case_row in cases_rows:
        file_path = safe_text(case_row.get("file_path"))
        compare_row = compare_index.get(file_path)

        priority, queue_status, review_reason = classify_priority(case_row, compare_row)

        if queue_status == "OK":
            continue

        queue_rows.append(
            build_output_row(
                case_row,
                compare_row,
                priority,
                queue_status,
                review_reason,
            )
        )

    queue_rows.sort(key=sort_key)

    if args.limit is not None and args.limit > 0:
        queue_rows = queue_rows[: args.limit]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "priority",
        "queue_status",
        "review_reason",
        "audit_id",
        "job_row_id",
        "file_status",
        "job_id",
        "machine",
        "fabric",
        "review_status",
        "print_status",
        "classification",
        "suspicion_category",
        "suspicion_reason",
        "effective_m",
        "gap_m",
        "consumed_m",
        "file_name",
        "file_path",
        "document",
        "error_message",
        "compare_result",
        "compare_issues",
    ]

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(queue_rows)

    print("Status: OK")
    print(f"Cases CSV: {cases_path}")
    print(f"Compare CSV: {compare_path}")
    print(f"Fila gerada: {output_path}")
    print(f"Itens na fila: {len(queue_rows)}")

    counts: dict[str, int] = {}
    for row in queue_rows:
        key = safe_text(row.get("queue_status"), "-")
        counts[key] = counts.get(key, 0) + 1

    print("Resumo:")
    for key in sorted(counts.keys()):
        print(f"- {key}: {counts[key]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())