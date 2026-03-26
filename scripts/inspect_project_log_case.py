from __future__ import annotations

import argparse
import sys
from pathlib import Path
from pprint import pformat

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.exceptions import LogParseError, LogValidationError
from logs.service import build_log_record, import_job_from_log, parse_sections_from_log
from storage.database import get_connection, init_database
from storage.import_audit_repository import ImportAuditRepository
from storage.log_sources_repository import LogSourceRepository


DEFAULT_SOURCE_NAME = "PROJECT_LOGS_IMPORT"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspeciona um caso do import real sem precisar localizar manualmente o arquivo."
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

    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument(
        "--audit-id",
        type=int,
        help="ID da linha em imported_logs.",
    )
    selector.add_argument(
        "--job-row-id",
        type=int,
        help="ID da linha em production_jobs.",
    )
    selector.add_argument(
        "--contains",
        help="Texto que deve aparecer no nome do arquivo/documento/job_id.",
    )

    parser.add_argument(
        "--show-sections",
        action="store_true",
        help="Mostra o dicionário completo de sections parseadas.",
    )
    parser.add_argument(
        "--show-raw-keys",
        action="store_true",
        help="Mostra as chaves principais e subchaves detectadas.",
    )
    return parser.parse_args()


def safe_text(value, default: str = "-") -> str:
    text = str(value or "").strip()
    return text or default


def fmt_dt(value) -> str:
    if value is None:
        return "-"
    return getattr(value, "strftime", lambda _: str(value))("%d/%m/%Y %H:%M:%S")


def fmt_m(value) -> str:
    try:
        return f"{float(value or 0.0):.3f} m"
    except Exception:
        return "0.000 m"


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


def fetch_run_cases(run_id: int) -> list:
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


def select_case(rows: list, args: argparse.Namespace):
    if args.audit_id is not None:
        for row in rows:
            if int(row["audit_id"]) == int(args.audit_id):
                return row
        return None

    if args.job_row_id is not None:
        for row in rows:
            if row["job_row_id"] is not None and int(row["job_row_id"]) == int(args.job_row_id):
                return row
        return None

    if args.contains:
        needle = args.contains.strip().lower()
        matches = []
        for row in rows:
            haystack = " ".join(
                [
                    safe_text(row["file_name"], ""),
                    safe_text(row["document"], ""),
                    safe_text(row["job_id"], ""),
                    safe_text(row["error_message"], ""),
                    safe_text(row["suspicion_reason"], ""),
                ]
            ).lower()
            if needle in haystack:
                matches.append(row)

        if not matches:
            return None

        if len(matches) > 1:
            print("Status: ERRO")
            print(f"Motivo: mais de um caso encontrado para contains='{args.contains}'.")
            print("Refine o filtro ou use --audit-id / --job-row-id.")
            print()
            print("Primeiros matches:")
            for row in matches[:10]:
                print(
                    f"  - audit_id={row['audit_id']} | "
                    f"job_row_id={safe_text(row['job_row_id'])} | "
                    f"file={safe_text(row['file_name'])} | "
                    f"job={safe_text(row['job_id'])} | "
                    f"doc={safe_text(row['document'])}"
                )
            raise SystemExit(1)

        return matches[0]

    return None


def print_case_header(row) -> None:
    print("Caso selecionado:")
    print(f"  - audit_id: {row['audit_id']}")
    print(f"  - job_row_id: {safe_text(row['job_row_id'])}")
    print(f"  - file_status: {safe_text(row['audit_status'])}")
    print(f"  - file_name: {safe_text(row['file_name'])}")
    print(f"  - file_path: {safe_text(row['file_path'])}")
    print(f"  - job_id: {safe_text(row['job_id'])}")
    print(f"  - machine: {safe_text(row['machine'])}")
    print(f"  - fabric: {safe_text(row['fabric'])}")
    print(f"  - review_status: {safe_text(row['review_status'])}")
    print(f"  - print_status: {safe_text(row['print_status'])}")
    print(f"  - classification: {safe_text(row['classification'])}")
    print(f"  - suspicion_category: {safe_text(row['suspicion_category'])}")
    print(f"  - suspicion_reason: {safe_text(row['suspicion_reason'])}")
    print(f"  - error_message: {safe_text(row['error_message'])}")
    print()


def print_section_keys(sections: dict) -> None:
    print("Sections detectadas:")
    if not sections:
        print("  - Nenhuma")
        print()
        return

    for key, value in sections.items():
        if isinstance(value, dict):
            subkeys = ", ".join(sorted(str(k) for k in value.keys()))
            print(f"  - [{key}] -> {subkeys or '(sem chaves)'}")
        else:
            print(f"  - [{key}] -> tipo={type(value).__name__}")
    print()


def print_selected_raw_values(sections: dict) -> None:
    general = sections.get("General", {}) if isinstance(sections.get("General"), dict) else {}
    item = sections.get("1", {}) if isinstance(sections.get("1"), dict) else {}
    costs = sections.get("Costs", {}) if isinstance(sections.get("Costs"), dict) else {}

    print("Campos brutos relevantes:")
    print(f"  - General.JobID: {safe_text(general.get('JobID'))}")
    print(f"  - General.Document: {safe_text(general.get('Document'))}")
    print(f"  - General.ComputerName: {safe_text(general.get('ComputerName'))}")
    print(f"  - General.Driver: {safe_text(general.get('Driver'))}")
    print(f"  - General.StartTime: {safe_text(general.get('StartTime'))}")
    print(f"  - General.EndTime: {safe_text(general.get('EndTime'))}")
    print(f"  - [1].HeightMM: {safe_text(item.get('HeightMM'))}")
    print(f"  - [1].VPosMM: {safe_text(item.get('VPosMM'))}")
    print(f"  - [1].VPositionMM: {safe_text(item.get('VPositionMM'))}")
    print(f"  - [1].Name: {safe_text(item.get('Name'))}")
    print(f"  - Costs.PrintHeightMM: {safe_text(costs.get('PrintHeightMM'))}")
    print()


def print_job_summary(job) -> None:
    print("Job mapeado ao reinspecionar o arquivo:")
    print(f"  - job_id: {safe_text(job.job_id)}")
    print(f"  - machine: {safe_text(job.machine)}")
    print(f"  - computer_name: {safe_text(job.computer_name)}")
    print(f"  - document: {safe_text(job.document)}")
    print(f"  - fabric: {safe_text(job.fabric)}")
    print(f"  - start_time: {fmt_dt(job.start_time)}")
    print(f"  - end_time: {fmt_dt(job.end_time)}")
    print(f"  - duration_seconds: {int(job.duration_seconds or 0)}")
    print(f"  - planned_length_m: {fmt_m(job.planned_length_m)}")
    print(f"  - actual_printed_length_m: {fmt_m(job.actual_printed_length_m)}")
    print(f"  - gap_before_m: {fmt_m(job.gap_before_m)}")
    print(f"  - consumed_length_m: {fmt_m(job.consumed_length_m)}")
    print(f"  - total_consumption_m: {fmt_m(job.total_consumption_m)}")
    print(f"  - print_status: {safe_text(job.print_status)}")
    print(f"  - review_status: {safe_text(job.review_status)}")
    print(f"  - classification: {safe_text(job.classification)}")
    print(f"  - suspicion_category: {safe_text(job.suspicion_category)}")
    print(f"  - suspicion_reason: {safe_text(job.suspicion_reason)}")
    print(f"  - suspicion_ratio: {safe_text(job.suspicion_ratio)}")
    print(f"  - is_suspicious: {'SIM' if job.is_suspicious else 'NÃO'}")
    print()


def main() -> int:
    args = parse_args()
    init_database()

    source, run = resolve_target_run(args.source_name, args.run_id)
    rows = fetch_run_cases(int(run["id"]))
    target_row = select_case(rows, args)

    if target_row is None:
        print("Status: ERRO")
        print("Motivo: nenhum caso encontrado com o seletor informado.")
        return 1

    file_path = Path(str(target_row["file_path"])).expanduser().resolve()

    print("\nNEXOR PROJECT LOG CASE INSPECTION\n")
    print(f"Source: {safe_text(source['name'])}")
    print(f"Run ID: {run['id']}")
    print()
    print_case_header(target_row)

    if not file_path.exists():
        print("Status: ERRO")
        print(f"Motivo: arquivo do caso não existe mais no disco: {file_path}")
        return 1

    try:
        log_record = build_log_record(file_path)
    except Exception as exc:
        print("Status: ERRO")
        print(f"Motivo ao montar Log record: {exc}")
        return 1

    print("Log record:")
    print(f"  - source_name: {safe_text(log_record.source_name)}")
    print(f"  - source_path: {safe_text(log_record.source_path)}")
    print(f"  - fingerprint: {safe_text(log_record.fingerprint)}")
    print(f"  - payload_size_chars: {len(log_record.raw_payload or '')}")
    print()

    try:
        sections = parse_sections_from_log(file_path)
    except LogParseError as exc:
        print("Status: ERRO")
        print(f"Falha no parser: {exc}")
        return 1
    except Exception as exc:
        print("Status: ERRO")
        print(f"Falha inesperada no parser: {exc}")
        return 1

    print("Status: PARSE OK")
    print()
    print_section_keys(sections)
    print_selected_raw_values(sections)

    if args.show_sections:
        print("Sections completas:")
        print(pformat(sections, width=120, sort_dicts=True))
        print()

    try:
        job = import_job_from_log(file_path)
    except LogValidationError as exc:
        print("Status: ERRO")
        print(f"Falha na validação/mapeamento: {exc}")
        return 1
    except Exception as exc:
        print("Status: ERRO")
        print(f"Falha inesperada no mapeamento: {exc}")
        return 1

    print("Status: MAP OK")
    print()
    print_job_summary(job)

    print("Comparação rápida com o que já está no banco/auditoria:")
    print(f"  - job_id banco: {safe_text(target_row['job_id'])}")
    print(f"  - job_id reinspecionado: {safe_text(job.job_id)}")
    print(f"  - machine banco: {safe_text(target_row['machine'])}")
    print(f"  - machine reinspecionada: {safe_text(job.machine)}")
    print(f"  - fabric banco: {safe_text(target_row['fabric'])}")
    print(f"  - fabric reinspecionada: {safe_text(job.fabric)}")
    print(f"  - effective banco: {fmt_m(target_row['actual_printed_length_m'])}")
    print(f"  - effective reinspecionado: {fmt_m(job.actual_printed_length_m)}")
    print(f"  - gap banco: {fmt_m(target_row['gap_before_m'])}")
    print(f"  - gap reinspecionado: {fmt_m(job.gap_before_m)}")
    print(f"  - consumed banco: {fmt_m(target_row['consumed_length_m'])}")
    print(f"  - consumed reinspecionado: {fmt_m(job.consumed_length_m)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())