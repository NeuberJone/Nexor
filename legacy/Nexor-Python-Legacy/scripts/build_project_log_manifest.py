from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.exceptions import LogParseError, LogValidationError
from logs.service import parse_sections_from_log
from logs.mapper import map_sections_to_job


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera um CSV manifesto dos logs reais da pasta logs_import sem persistir no banco."
    )
    parser.add_argument(
        "--path",
        default=str(PROJECT_ROOT / "logs_import"),
        help="Pasta raiz dos logs reais. Padrão: <project>/logs_import",
    )
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "exports" / "project_log_manifest.csv"),
        help="Caminho do CSV de saída.",
    )
    parser.add_argument(
        "--non-recursive",
        action="store_true",
        help="Lê apenas a pasta informada, sem subpastas.",
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
    return parser.parse_args()


def safe_text(value, default: str = "") -> str:
    text = str(value or "").strip()
    return text if text else default


def safe_float(value) -> float | None:
    try:
        if value is None:
            return None
        text = str(value).strip().replace(",", ".")
        if not text:
            return None
        return float(text)
    except Exception:
        return None


def fmt_float(value) -> str:
    if value is None:
        return ""
    return f"{float(value):.6f}"


def section_dict(sections: dict, key: str) -> dict:
    value = sections.get(key, {})
    return value if isinstance(value, dict) else {}


def resolve_expected_bucket(
    *,
    planned_length_m: float | None,
    actual_printed_length_m: float | None,
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
        return "ABORTED", ratio
    if ratio < complete_threshold:
        return "PARTIAL", ratio
    return "COMPLETE", ratio


def iter_log_files(root: Path, recursive: bool):
    if recursive:
        return sorted(root.rglob("*.txt"))
    return sorted(root.glob("*.txt"))


def build_row_from_file(
    file_path: Path,
    *,
    partial_threshold: float,
    complete_threshold: float,
) -> dict[str, str]:
    row: dict[str, str] = {
        "file_name": file_path.name,
        "file_path": str(file_path),
        "parse_status": "",
        "map_status": "",
        "error_type": "",
        "error_message": "",
        "section_keys": "",
        "general_job_id": "",
        "general_document": "",
        "general_computer_name": "",
        "general_driver": "",
        "general_start_time": "",
        "general_end_time": "",
        "item_height_mm": "",
        "item_vpos_mm": "",
        "item_vposition_mm": "",
        "item_name": "",
        "costs_print_height_mm": "",
        "mapped_job_id": "",
        "mapped_machine": "",
        "mapped_computer_name": "",
        "mapped_document": "",
        "mapped_fabric": "",
        "mapped_start_time": "",
        "mapped_end_time": "",
        "mapped_duration_seconds": "",
        "planned_length_m": "",
        "actual_printed_length_m": "",
        "gap_before_m": "",
        "consumed_length_m": "",
        "expected_ratio": "",
        "expected_bucket": "",
        "print_status": "",
        "review_status": "",
        "classification": "",
        "suspicion_category": "",
        "suspicion_reason": "",
    }

    try:
        sections = parse_sections_from_log(file_path)
        row["parse_status"] = "PARSE_OK"
        row["section_keys"] = ",".join(sorted(str(key) for key in sections.keys()))
    except LogParseError as exc:
        row["parse_status"] = "PARSE_ERROR"
        row["error_type"] = "LogParseError"
        row["error_message"] = str(exc)
        return row
    except Exception as exc:
        row["parse_status"] = "PARSE_ERROR"
        row["error_type"] = type(exc).__name__
        row["error_message"] = str(exc)
        return row

    general = section_dict(sections, "General")
    item = section_dict(sections, "1")
    costs = section_dict(sections, "Costs")

    row["general_job_id"] = safe_text(general.get("JobID"))
    row["general_document"] = safe_text(general.get("Document"))
    row["general_computer_name"] = safe_text(general.get("ComputerName"))
    row["general_driver"] = safe_text(general.get("Driver"))
    row["general_start_time"] = safe_text(general.get("StartTime"))
    row["general_end_time"] = safe_text(general.get("EndTime"))

    row["item_height_mm"] = safe_text(item.get("HeightMM"))
    row["item_vpos_mm"] = safe_text(item.get("VPosMM"))
    row["item_vposition_mm"] = safe_text(item.get("VPositionMM"))
    row["item_name"] = safe_text(item.get("Name"))

    row["costs_print_height_mm"] = safe_text(costs.get("PrintHeightMM"))

    try:
        job = map_sections_to_job(sections, source_path=str(file_path))
        row["map_status"] = "MAP_OK"
    except LogValidationError as exc:
        row["map_status"] = "MAP_ERROR"
        row["error_type"] = "LogValidationError"
        row["error_message"] = str(exc)
        return row
    except Exception as exc:
        row["map_status"] = "MAP_ERROR"
        row["error_type"] = type(exc).__name__
        row["error_message"] = str(exc)
        return row

    row["mapped_job_id"] = safe_text(job.job_id)
    row["mapped_machine"] = safe_text(job.machine)
    row["mapped_computer_name"] = safe_text(job.computer_name)
    row["mapped_document"] = safe_text(job.document)
    row["mapped_fabric"] = safe_text(job.fabric)
    row["mapped_start_time"] = safe_text(job.start_time)
    row["mapped_end_time"] = safe_text(job.end_time)
    row["mapped_duration_seconds"] = str(int(job.duration_seconds or 0))

    row["planned_length_m"] = fmt_float(job.planned_length_m)
    row["actual_printed_length_m"] = fmt_float(job.actual_printed_length_m)
    row["gap_before_m"] = fmt_float(job.gap_before_m)
    row["consumed_length_m"] = fmt_float(job.consumed_length_m)

    expected_bucket, ratio = resolve_expected_bucket(
        planned_length_m=job.planned_length_m,
        actual_printed_length_m=job.actual_printed_length_m,
        partial_threshold=partial_threshold,
        complete_threshold=complete_threshold,
    )
    row["expected_bucket"] = expected_bucket
    row["expected_ratio"] = fmt_float(ratio)

    row["print_status"] = safe_text(job.print_status)
    row["review_status"] = safe_text(job.review_status)
    row["classification"] = safe_text(job.classification)
    row["suspicion_category"] = safe_text(job.suspicion_category)
    row["suspicion_reason"] = safe_text(job.suspicion_reason)

    return row


def main() -> int:
    args = parse_args()

    target_path = Path(args.path).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not target_path.exists():
        print("Status: ERRO")
        print(f"Motivo: pasta não encontrada: {target_path}")
        return 1

    if not target_path.is_dir():
        print("Status: ERRO")
        print(f"Motivo: o caminho informado não é uma pasta: {target_path}")
        return 1

    if args.partial_threshold < 0:
        print("Status: ERRO")
        print("Motivo: --partial-threshold não pode ser negativo.")
        return 1

    if args.complete_threshold <= args.partial_threshold:
        print("Status: ERRO")
        print("Motivo: --complete-threshold deve ser maior que --partial-threshold.")
        return 1

    files = list(iter_log_files(target_path, recursive=not args.non_recursive))
    if not files:
        print("Status: ERRO")
        print("Motivo: nenhum arquivo .txt encontrado.")
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "file_name",
        "file_path",
        "parse_status",
        "map_status",
        "error_type",
        "error_message",
        "section_keys",
        "general_job_id",
        "general_document",
        "general_computer_name",
        "general_driver",
        "general_start_time",
        "general_end_time",
        "item_height_mm",
        "item_vpos_mm",
        "item_vposition_mm",
        "item_name",
        "costs_print_height_mm",
        "mapped_job_id",
        "mapped_machine",
        "mapped_computer_name",
        "mapped_document",
        "mapped_fabric",
        "mapped_start_time",
        "mapped_end_time",
        "mapped_duration_seconds",
        "planned_length_m",
        "actual_printed_length_m",
        "gap_before_m",
        "consumed_length_m",
        "expected_ratio",
        "expected_bucket",
        "print_status",
        "review_status",
        "classification",
        "suspicion_category",
        "suspicion_reason",
    ]

    rows = [
        build_row_from_file(
            file_path,
            partial_threshold=float(args.partial_threshold),
            complete_threshold=float(args.complete_threshold),
        )
        for file_path in files
    ]

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    parse_ok = sum(1 for row in rows if row["parse_status"] == "PARSE_OK")
    map_ok = sum(1 for row in rows if row["map_status"] == "MAP_OK")
    parse_error = sum(1 for row in rows if row["parse_status"] == "PARSE_ERROR")
    map_error = sum(1 for row in rows if row["map_status"] == "MAP_ERROR")
    expected_counter = Counter(row["expected_bucket"] for row in rows if row["expected_bucket"])

    print("Status: OK")
    print(f"Arquivos lidos: {len(rows)}")
    print(f"PARSE_OK: {parse_ok}")
    print(f"MAP_OK: {map_ok}")
    print(f"PARSE_ERROR: {parse_error}")
    print(f"MAP_ERROR: {map_error}")
    print("Buckets esperados:")
    for key, value in expected_counter.most_common():
        print(f"- {key}: {value}")
    print(f"CSV: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())