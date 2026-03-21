from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

from exports.roll_export_service import export_closed_roll
from logs.service import import_and_persist_log
from storage.database import init_database
from storage.import_audit_repository import ImportAuditRepository
from storage.log_sources_repository import LogSourceRepository
from storage.repository import ProductionRepository


def format_meters(value: float) -> str:
    return f"{float(value or 0.0):.2f}".replace(".", ",")


def format_duration(seconds: int) -> str:
    seconds = int(seconds or 0)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours == 0 and minutes == 0:
        return f"{secs:02d}s"

    return f"{hours:02d}h{minutes:02d}min"


def format_datetime(dt) -> str:
    if dt is None:
        return "-"
    return dt.strftime("%d/%m/%Y %H:%M:%S")


def compute_file_hash(path: Path) -> str:
    sha = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)

    return sha.hexdigest()


def row_get(row: Any, key: str, default=None):
    try:
        if row is None:
            return default
        if hasattr(row, "keys") and key in row.keys():
            value = row[key]
            return default if value is None else value
        return row.get(key, default)
    except Exception:
        return default


def safe_call(label: str, fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        print(f"[WARN] {label}: {exc}")
        return None


def safe_audit_register(audit_repo: ImportAuditRepository, **kwargs) -> None:
    safe_call("audit register_file failed", audit_repo.register_file, **kwargs)


def safe_audit_start_run(audit_repo: ImportAuditRepository, source_id: int) -> int | None:
    return safe_call("audit start_run failed", audit_repo.start_run, source_id)


def safe_audit_finish_run(
    audit_repo: ImportAuditRepository,
    run_id: int | None,
    *,
    total_found: int,
    imported_count: int,
    duplicate_count: int,
    error_count: int,
    notes: str | None = None,
) -> None:
    if run_id is None:
        return

    safe_call(
        "audit finish_run failed",
        audit_repo.finish_run,
        run_id,
        total_found=total_found,
        imported_count=imported_count,
        duplicate_count=duplicate_count,
        error_count=error_count,
        notes=notes,
    )


def iter_source_files(source_row, force_rescan: bool = False):
    base_path = Path(str(row_get(source_row, "path", "")))

    if not str(base_path):
        return []

    if not base_path.exists():
        return []

    recursive = bool(row_get(source_row, "recursive", True))

    if recursive:
        candidates = sorted(base_path.rglob("*.txt"))
    else:
        candidates = sorted(base_path.glob("*.txt"))

    if force_rescan:
        return candidates

    last_mtime = row_get(source_row, "last_successful_mtime", None)

    if last_mtime is None:
        return candidates

    try:
        last_mtime = float(last_mtime)
    except Exception:
        return candidates

    new_files = []

    for file in candidates:
        try:
            mtime = file.stat().st_mtime
        except Exception:
            continue

        if mtime > last_mtime:
            new_files.append(file)

    return new_files


def parse_args():
    parser = argparse.ArgumentParser(description="Nexor operational CLI")

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--force-rescan",
        action="store_true",
        help="Ignora o checkpoint das fontes e relê todos os logs.",
    )
    mode_group.add_argument(
        "--export-roll-id",
        type=int,
        help="Exporta um rolo fechado pelo ID.",
    )
    mode_group.add_argument(
        "--list-rolls",
        action="store_true",
        help="Lista os rolos cadastrados no banco.",
    )
    mode_group.add_argument(
        "--show-roll-id",
        type=int,
        help="Mostra o detalhe completo de um rolo pelo ID.",
    )

    parser.add_argument(
        "--export-output-dir",
        default="exports/out",
        help="Diretório de saída da exportação do rolo.",
    )

    parser.add_argument(
        "--roll-status",
        default="ALL",
        help="Filtro de status ao listar rolos. Ex.: ALL, OPEN, CLOSED, EXPORTED.",
    )

    return parser.parse_args()


def print_job_details(job) -> None:
    print(f"Job ID: {job.job_id}")
    print(f"Máquina: {job.machine}")
    print(f"ComputerName: {job.computer_name}")
    print(f"Documento: {job.document}")
    print(f"Início: {format_datetime(job.start_time)}")
    print(f"Fim: {format_datetime(job.end_time)}")
    print(f"Duração: {format_duration(job.duration_seconds)}")
    print(f"Tecido: {job.fabric or '-'}")
    print(f"Tamanho do arquivo: {format_meters(job.planned_length_m)} m")
    print(f"Consumo medido no log: {format_meters(job.consumed_length_m)} m")
    print(f"Espaço técnico antes: {format_meters(job.gap_before_m)} m")
    print(f"Impresso real da arte: {format_meters(job.actual_printed_length_m)} m")
    print(f"Consumo operacional total: {format_meters(job.total_consumption_m)} m")


def print_roll_summary_block(summary: dict) -> None:
    roll = summary["roll"]

    print(f"ID: {roll.id}")
    print(f"Roll: {roll.roll_name}")
    print(f"Machine: {roll.machine}")
    print(f"Fabric: {roll.fabric or '-'}")
    print(f"Status: {roll.status}")
    print(f"Created: {format_datetime(roll.created_at)}")
    print(f"Closed: {format_datetime(roll.closed_at)}")
    print(f"Exported: {format_datetime(roll.exported_at)}")
    print(f"Reviewed: {format_datetime(roll.reviewed_at)}")
    print(f"Reopened: {format_datetime(roll.reopened_at)}")
    print(f"Jobs: {summary['jobs_count']}")
    print(f"Total planned (m): {format_meters(summary['total_planned_m'])}")
    print(f"Total effective (m): {format_meters(summary['total_effective_m'])}")
    print(f"Total gap (m): {format_meters(summary['total_gap_m'])}")
    print(f"Total consumed (m): {format_meters(summary['total_consumed_m'])}")
    print(f"Efficiency ratio: {summary['efficiency_ratio'] if summary['efficiency_ratio'] is not None else '-'}")
    print(f"Note: {roll.note or '-'}")


def handle_export_roll(roll_id: int, output_dir: str | Path) -> int:
    print("\nNEXOR ROLL EXPORT\n")
    print(f"Rolo ID: {roll_id}")
    print(f"Diretório de saída: {Path(output_dir)}\n")

    try:
        result = export_closed_roll(
            roll_id=roll_id,
            output_dir=output_dir,
        )
    except Exception as exc:
        print("Status: ERRO")
        print(f"Motivo: {exc}")
        return 1

    print("Status: EXPORTADO")
    print(f"Rolo: {result['roll_name']}")
    print(f"Jobs: {result['jobs_count']}")
    print(f"Total planejado: {format_meters(result['total_planned_m'])} m")
    print(f"Impresso efetivo: {format_meters(result['total_effective_m'])} m")
    print(f"Gap total: {format_meters(result['total_gap_m'])} m")
    print(f"Consumo total: {format_meters(result['total_consumed_m'])} m")
    print(f"PDF: {result['pdf_path']}")
    print(f"JPG: {result['jpg_path']}")
    return 0


def handle_list_rolls(status: str = "ALL") -> int:
    print("\nNEXOR ROLLS\n")

    repo = ProductionRepository()
    normalized_status = (status or "ALL").strip().upper()
    rolls = repo.list_rolls(status=normalized_status)

    if not rolls:
        print(f"Nenhum rolo encontrado para status={normalized_status}.")
        return 0

    for roll in rolls:
        summary = repo.get_roll_summary(roll.id)
        print("=" * 72)
        print_roll_summary_block(summary)

        items = summary["items"]
        if items:
            print("\nItems:")
            for item in items:
                print(
                    f"  - {item.job_id} | {item.document} | "
                    f"eff={format_meters(item.effective_printed_length_m)}m | "
                    f"gap={format_meters(item.gap_before_m)}m | "
                    f"cons={format_meters(item.consumed_length_m)}m"
                )
        print()

    return 0


def handle_show_roll(roll_id: int) -> int:
    print("\nNEXOR ROLL DETAIL\n")

    repo = ProductionRepository()
    roll = repo.get_roll(roll_id=roll_id)

    if not roll:
        print("Status: ERRO")
        print(f"Motivo: Rolo não encontrado: id={roll_id}")
        return 1

    summary = repo.get_roll_summary(roll_id)

    print_roll_summary_block(summary)

    metric_counts = summary.get("metric_counts") or {}
    fabric_totals = summary.get("fabric_totals") or {}

    print("\nMetric counts:")
    if metric_counts:
        for key, value in metric_counts.items():
            print(f"  - {key}: {value}")
    else:
        print("  - -")

    print("\nFabric totals:")
    if fabric_totals:
        for key, value in fabric_totals.items():
            print(f"  - {key}: {format_meters(value)} m")
    else:
        print("  - -")

    print("\nItems:")
    items = summary["items"]
    if not items:
        print("  - Nenhum item.")
    else:
        for item in items:
            print(
                f"  - Job={item.job_id} | Doc={item.document} | Machine={item.machine} | "
                f"Fabric={item.fabric or '-'} | Planned={format_meters(item.planned_length_m)}m | "
                f"Effective={format_meters(item.effective_printed_length_m)}m | "
                f"Gap={format_meters(item.gap_before_m)}m | "
                f"Consumed={format_meters(item.consumed_length_m)}m | "
                f"Metric={item.metric_category or '-'} | "
                f"Review={item.review_status or '-'} | "
                f"PrintStatus={item.snapshot_print_status or '-'}"
            )

    return 0


def handle_import(force_rescan: bool) -> int:
    print("\nNEXOR LOG IMPORT\n")

    if force_rescan:
        print("Modo: FORCE RESCAN (releitura completa das fontes)\n")

    source_repo = LogSourceRepository()
    audit_repo = ImportAuditRepository()

    sources = source_repo.list_enabled()

    if not sources:
        print("Nenhuma fonte de logs ativa cadastrada.")
        print("Cadastre pelo menos uma fonte em 'log_sources'.")
        return 0

    grand_total_found = 0
    grand_imported = 0
    grand_duplicates = 0
    grand_errors = 0

    grand_planned_length = 0.0
    grand_consumed_length = 0.0
    grand_gap = 0.0
    grand_actual_printed = 0.0

    for source in sources:
        source_id = row_get(source, "id")
        source_name = row_get(source, "name", "<SEM NOME>")
        source_path = row_get(source, "path", "<SEM CAMINHO>")

        print("=" * 60)
        print(f"FONTE: {source_name}")
        print(f"Caminho: {source_path}")
        print("=" * 60)

        if source_id is not None:
            safe_call("update_last_scan_at failed", source_repo.update_last_scan_at, source_id)

        files = iter_source_files(source, force_rescan=force_rescan)
        total = len(files)

        if not files:
            if force_rescan:
                print("Nenhum arquivo encontrado nesta fonte.\n")
            else:
                print("Nenhum arquivo novo encontrado nesta fonte.\n")
            continue

        run_id = safe_audit_start_run(audit_repo, int(source_id)) if source_id is not None else None

        imported = 0
        duplicates = 0
        errors = 0

        total_planned_length = 0.0
        total_consumed_length = 0.0
        total_gap = 0.0
        total_actual_printed = 0.0

        max_successful_mtime = row_get(source, "last_successful_mtime", None)

        for file in files:
            try:
                file_mtime = file.stat().st_mtime
                file_hash = compute_file_hash(file)
                file_size = file.stat().st_size

                result = import_and_persist_log(
                    path=file,
                    raise_on_invalid=False,
                )

                log_record = result.get("log")
                job = result.get("job")
                is_duplicate = bool(result.get("is_duplicate"))
                created_job = bool(result.get("created_job"))
                error_message = result.get("error")

                print(f"Arquivo: {file.name}")

                if job is not None:
                    print_job_details(job)

                if is_duplicate:
                    duplicates += 1
                    status = "DUPLICATE"
                    print("Status: DUPLICADO")

                    if max_successful_mtime is None or file_mtime > float(max_successful_mtime):
                        max_successful_mtime = file_mtime

                elif created_job and job is not None:
                    imported += 1
                    status = "IMPORTED"

                    total_planned_length += float(job.planned_length_m or 0.0)
                    total_consumed_length += float(job.consumed_length_m or 0.0)
                    total_gap += float(job.gap_before_m or 0.0)
                    total_actual_printed += float(job.actual_printed_length_m or 0.0)

                    if max_successful_mtime is None or file_mtime > float(max_successful_mtime):
                        max_successful_mtime = file_mtime

                    print("Status: IMPORTADO")

                else:
                    errors += 1
                    status = "ERROR"
                    print("Status: ERRO")
                    print(f"Motivo: {error_message or 'Falha na importação/normalização do log'}")

                safe_audit_register(
                    audit_repo,
                    run_id=run_id or 0,
                    source_id=source_id or 0,
                    file_name=file.name,
                    file_path=str(file),
                    file_size=file_size,
                    file_hash=file_hash,
                    status=status,
                    error_message=error_message,
                    detected_job_id=(job.job_id if job else None),
                    detected_computer_name=(job.computer_name if job else None),
                    detected_machine=(job.machine if job else None),
                )

                if log_record is not None:
                    print(f"Log ID: {log_record.id}")
                    print(f"Log status: {log_record.status}")

                print()

            except Exception as e:
                errors += 1

                try:
                    file_hash = compute_file_hash(file)
                    file_size = file.stat().st_size
                except Exception:
                    file_hash = None
                    file_size = None

                safe_audit_register(
                    audit_repo,
                    run_id=run_id or 0,
                    source_id=source_id or 0,
                    file_name=file.name,
                    file_path=str(file),
                    file_size=file_size,
                    file_hash=file_hash,
                    status="ERROR",
                    error_message=str(e),
                )

                print(f"Arquivo: {file.name}")
                print("Status: ERRO")
                print(f"Motivo: {e}\n")

        if source_id is not None and max_successful_mtime is not None:
            safe_call(
                "update_last_successful_mtime failed",
                source_repo.update_last_successful_mtime,
                source_id,
                max_successful_mtime,
            )

        safe_audit_finish_run(
            audit_repo,
            run_id,
            total_found=total,
            imported_count=imported,
            duplicate_count=duplicates,
            error_count=errors,
        )

        print("-" * 40)
        print(f"Resumo da fonte: {source_name}")
        print(f"Logs encontrados: {total}")
        print(f"Importados: {imported}")
        print(f"Duplicados: {duplicates}")
        print(f"Erros: {errors}")
        print(f"Tamanho total dos arquivos: {format_meters(total_planned_length)} m")
        print(f"Consumo medido no log: {format_meters(total_consumed_length)} m")
        print(f"Espaço técnico: {format_meters(total_gap)} m")
        print(f"Impresso real da arte: {format_meters(total_actual_printed)} m")
        print(f"Consumo operacional total: {format_meters(total_consumed_length)} m")
        print()

        grand_total_found += total
        grand_imported += imported
        grand_duplicates += duplicates
        grand_errors += errors

        grand_planned_length += total_planned_length
        grand_consumed_length += total_consumed_length
        grand_gap += total_gap
        grand_actual_printed += total_actual_printed

    print("=" * 60)
    print("RESUMO GERAL")
    print("=" * 60)
    print(f"Logs encontrados: {grand_total_found}")
    print(f"Importados: {grand_imported}")
    print(f"Duplicados: {grand_duplicates}")
    print(f"Erros: {grand_errors}")
    print(f"Tamanho total dos arquivos: {format_meters(grand_planned_length)} m")
    print(f"Consumo medido no log: {format_meters(grand_consumed_length)} m")
    print(f"Espaço técnico: {format_meters(grand_gap)} m")
    print(f"Impresso real da arte: {format_meters(grand_actual_printed)} m")
    print(f"Consumo operacional total: {format_meters(grand_consumed_length)} m")

    return 0


def main() -> int:
    args = parse_args()
    init_database()

    if args.export_roll_id is not None:
        return handle_export_roll(
            roll_id=args.export_roll_id,
            output_dir=args.export_output_dir,
        )

    if args.list_rolls:
        return handle_list_rolls(status=args.roll_status)

    if args.show_roll_id is not None:
        return handle_show_roll(roll_id=args.show_roll_id)

    return handle_import(force_rescan=args.force_rescan)


if __name__ == "__main__":
    raise SystemExit(main())