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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspeciona um arquivo de log real sem persistir nada no banco."
    )
    parser.add_argument(
        "path",
        help="Caminho do arquivo de log a inspecionar.",
    )
    parser.add_argument(
        "--show-sections",
        action="store_true",
        help="Mostra o dicionário completo de sections parseadas.",
    )
    parser.add_argument(
        "--show-raw-keys",
        action="store_true",
        help="Mostra apenas as chaves principais e subchaves detectadas.",
    )
    return parser.parse_args()


def safe_text(value, default: str = "-") -> str:
    text = str(value or "").strip()
    return text or default


def fmt_m(value) -> str:
    try:
        return f"{float(value or 0.0):.3f} m"
    except Exception:
        return "0.000 m"


def fmt_dt(value) -> str:
    if value is None:
        return "-"
    return getattr(value, "strftime", lambda _: str(value))("%d/%m/%Y %H:%M:%S")


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
    print("Job mapeado:")
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
    target = Path(args.path).expanduser().resolve()

    if not target.exists():
        print("Status: ERRO")
        print(f"Motivo: arquivo não encontrado: {target}")
        return 1

    if not target.is_file():
        print("Status: ERRO")
        print(f"Motivo: o caminho informado não é um arquivo: {target}")
        return 1

    print("\nNEXOR LOG FILE INSPECTION\n")
    print(f"Arquivo: {target}")
    print()

    try:
        log_record = build_log_record(target)
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
        sections = parse_sections_from_log(target)
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

    if args.show_raw_keys:
        pass

    if args.show_sections:
        print("Sections completas:")
        print(pformat(sections, width=120, sort_dicts=True))
        print()

    try:
        job = import_job_from_log(target)
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

    print("Leitura rápida:")
    if job.actual_printed_length_m <= 0:
        print("  - A arte saiu com comprimento efetivo zerado.")
    if job.gap_before_m > 0:
        print("  - Existe gap técnico antes da arte.")
    if job.consumed_length_m < job.actual_printed_length_m:
        print("  - ALERTA: consumo menor que impresso efetivo, isso parece incoerente.")
    if job.end_time and job.start_time and job.duration_seconds <= 0:
        print("  - ALERTA: duração não positiva.")
    if not job.fabric:
        print("  - ALERTA: tecido não foi extraído do documento.")
    print()

    print("Próximo uso sugerido:")
    print("  - rodar esse script em um arquivo completo")
    print("  - rodar em um parcial")
    print("  - rodar em um abortado")
    print("  - comparar onde os campos começam a divergir")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())