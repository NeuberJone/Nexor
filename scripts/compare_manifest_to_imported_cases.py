from __future__ import annotations

import argparse
import csv
import sys
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
        description="Compara o manifesto bruto dos logs com os casos importados no banco."
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
        "--manifest",
        default=str(PROJECT_ROOT / "exports" / "project_log_manifest.csv"),
        help="CSV gerado por build_project_log_manifest.py",
    )
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "exports" / "manifest_vs_imported_cases.csv"),
        help="CSV de saída da comparação.",
    )
    return parser.parse_args()


def safe_text(value, default: str = "") -> str:
    text = str(value or "").strip()
    return text if text else default


def safe_upper(value) -> str:
    return safe_text(value).upper()


def safe_float(value) -> float | None:
    try:
        text = safe_text(value)
        if not text:
            return None
        return float(text.replace(",", "."))
    except Exception:
        return None


def fmt_bool(value: bool) -> str:
    return "YES" if value else "NO"


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


def load_manifest_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        print("Status: ERRO")
        print(f"Motivo: manifesto não encontrado: {path}")
        raise SystemExit(1)

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fetch_run_rows(run_id: int) -> list:
    conn = get_connection()
    try:
        sql = """
            SELECT
                il.id AS audit_id,
                il.run_id,
                il.file_name,
                il.file_path,
                il.status AS audit_status,
                il.error_message,

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
                pj.planned_length_m,
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


def build_imported_index(rows: list) -> dict[str, object]:
    index: dict[str, object] = {}
    for row in rows:
        file_path = safe_text(row["file_path"])
        if file_path and file_path not in index:
            index[file_path] = row
    return index


def compare_text(manifest_value, imported_value) -> bool:
    return safe_upper(manifest_value) == safe_upper(imported_value)


def compare_float(manifest_value, imported_value, tolerance: float = 0.0001) -> bool:
    left = safe_float(manifest_value)
    right = safe_float(imported_value)

    if left is None and right is None:
        return True
    if left is None or right is None:
        return False
    return abs(left - right) <= tolerance


def classify_row(manifest_row: dict[str, str], imported_row) -> tuple[str, list[str]]:
    issues: list[str] = []

    parse_status = safe_upper(manifest_row.get("parse_status"))
    map_status = safe_upper(manifest_row.get("map_status"))

    if imported_row is None:
        return "MISSING_IN_IMPORT", ["arquivo do manifesto não apareceu no import run"]

    audit_status = safe_upper(imported_row["audit_status"])
    job_exists = imported_row["job_row_id"] is not None

    if parse_status == "PARSE_ERROR":
        if audit_status != "ERROR":
            issues.append("manifesto indica parse_error, mas audit_status não é ERROR")
        return ("MISMATCH" if issues else "OK"), issues

    if map_status == "MAP_ERROR":
        if audit_status != "ERROR":
            issues.append("manifesto indica map_error, mas audit_status não é ERROR")
        return ("MISMATCH" if issues else "OK"), issues

    if map_status == "MAP_OK" and not job_exists and audit_status != "DUPLICATE":
        issues.append("manifesto mapeou job, mas o run não trouxe job persistido")

    if not compare_text(manifest_row.get("mapped_job_id"), imported_row["job_id"]):
        issues.append("job_id divergente")

    if not compare_text(manifest_row.get("mapped_machine"), imported_row["machine"]):
        issues.append("machine divergente")

    if not compare_text(manifest_row.get("mapped_document"), imported_row["document"]):
        issues.append("document divergente")

    if not compare_text(manifest_row.get("mapped_fabric"), imported_row["fabric"]):
        issues.append("fabric divergente")

    if not compare_float(manifest_row.get("planned_length_m"), imported_row["planned_length_m"]):
        issues.append("planned_length_m divergente")

    if not compare_float(
        manifest_row.get("actual_printed_length_m"),
        imported_row["actual_printed_length_m"],
    ):
        issues.append("actual_printed_length_m divergente")

    if not compare_float(manifest_row.get("gap_before_m"), imported_row["gap_before_m"]):
        issues.append("gap_before_m divergente")

    if not compare_float(manifest_row.get("consumed_length_m"), imported_row["consumed_length_m"]):
        issues.append("consumed_length_m divergente")

    return ("MISMATCH" if issues else "OK"), issues


def build_export_row(manifest_row: dict[str, str], imported_row, result: str, issues: list[str]) -> dict[str, str]:
    return {
        "result": result,
        "issues": " | ".join(issues),
        "file_name": safe_text(manifest_row.get("file_name")),
        "file_path": safe_text(manifest_row.get("file_path")),
        "manifest_parse_status": safe_text(manifest_row.get("parse_status")),
        "manifest_map_status": safe_text(manifest_row.get("map_status")),
        "manifest_error_type": safe_text(manifest_row.get("error_type")),
        "manifest_error_message": safe_text(manifest_row.get("error_message")),
        "manifest_expected_bucket": safe_text(manifest_row.get("expected_bucket")),
        "manifest_expected_ratio": safe_text(manifest_row.get("expected_ratio")),
        "manifest_job_id": safe_text(manifest_row.get("mapped_job_id")),
        "manifest_machine": safe_text(manifest_row.get("mapped_machine")),
        "manifest_document": safe_text(manifest_row.get("mapped_document")),
        "manifest_fabric": safe_text(manifest_row.get("mapped_fabric")),
        "manifest_planned_length_m": safe_text(manifest_row.get("planned_length_m")),
        "manifest_actual_printed_length_m": safe_text(manifest_row.get("actual_printed_length_m")),
        "manifest_gap_before_m": safe_text(manifest_row.get("gap_before_m")),
        "manifest_consumed_length_m": safe_text(manifest_row.get("consumed_length_m")),
        "import_audit_id": safe_text(imported_row["audit_id"] if imported_row is not None else ""),
        "import_audit_status": safe_text(imported_row["audit_status"] if imported_row is not None else ""),
        "import_error_message": safe_text(imported_row["error_message"] if imported_row is not None else ""),
        "import_job_row_id": safe_text(imported_row["job_row_id"] if imported_row is not None else ""),
        "import_job_id": safe_text(imported_row["job_id"] if imported_row is not None else ""),
        "import_machine": safe_text(imported_row["machine"] if imported_row is not None else ""),
        "import_document": safe_text(imported_row["document"] if imported_row is not None else ""),
        "import_fabric": safe_text(imported_row["fabric"] if imported_row is not None else ""),
        "import_print_status": safe_text(imported_row["print_status"] if imported_row is not None else ""),
        "import_review_status": safe_text(imported_row["review_status"] if imported_row is not None else ""),
        "import_classification": safe_text(imported_row["classification"] if imported_row is not None else ""),
        "import_suspicion_category": safe_text(imported_row["suspicion_category"] if imported_row is not None else ""),
        "import_suspicion_reason": safe_text(imported_row["suspicion_reason"] if imported_row is not None else ""),
        "import_planned_length_m": safe_text(imported_row["planned_length_m"] if imported_row is not None else ""),
        "import_actual_printed_length_m": safe_text(imported_row["actual_printed_length_m"] if imported_row is not None else ""),
        "import_gap_before_m": safe_text(imported_row["gap_before_m"] if imported_row is not None else ""),
        "import_consumed_length_m": safe_text(imported_row["consumed_length_m"] if imported_row is not None else ""),
        "job_persisted": fmt_bool(imported_row is not None and imported_row["job_row_id"] is not None),
    }


def main() -> int:
    args = parse_args()
    init_database()

    manifest_path = Path(args.manifest).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    source, run = resolve_target_run(args.source_name, args.run_id)
    manifest_rows = load_manifest_rows(manifest_path)
    imported_rows = fetch_run_rows(int(run["id"]))
    imported_index = build_imported_index(imported_rows)

    export_rows: list[dict[str, str]] = []
    result_counter: dict[str, int] = {}

    for manifest_row in manifest_rows:
        file_path = safe_text(manifest_row.get("file_path"))
        imported_row = imported_index.get(file_path)
        result, issues = classify_row(manifest_row, imported_row)
        export_rows.append(build_export_row(manifest_row, imported_row, result, issues))
        result_counter[result] = result_counter.get(result, 0) + 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "result",
        "issues",
        "file_name",
        "file_path",
        "manifest_parse_status",
        "manifest_map_status",
        "manifest_error_type",
        "manifest_error_message",
        "manifest_expected_bucket",
        "manifest_expected_ratio",
        "manifest_job_id",
        "manifest_machine",
        "manifest_document",
        "manifest_fabric",
        "manifest_planned_length_m",
        "manifest_actual_printed_length_m",
        "manifest_gap_before_m",
        "manifest_consumed_length_m",
        "import_audit_id",
        "import_audit_status",
        "import_error_message",
        "import_job_row_id",
        "import_job_id",
        "import_machine",
        "import_document",
        "import_fabric",
        "import_print_status",
        "import_review_status",
        "import_classification",
        "import_suspicion_category",
        "import_suspicion_reason",
        "import_planned_length_m",
        "import_actual_printed_length_m",
        "import_gap_before_m",
        "import_consumed_length_m",
        "job_persisted",
    ]

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(export_rows)

    print("Status: OK")
    print(f"Source: {safe_text(source['name'])}")
    print(f"Run ID: {run['id']}")
    print(f"Manifesto: {manifest_path}")
    print(f"CSV comparação: {output_path}")
    print(f"Linhas comparadas: {len(export_rows)}")
    for key in sorted(result_counter.keys()):
        print(f"- {key}: {result_counter[key]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())