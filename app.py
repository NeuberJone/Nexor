import argparse
import hashlib
from pathlib import Path

from logs.service import import_job_from_log
from storage.database import init_database
from storage.repository import ProductionRepository
from storage.log_sources_repository import LogSourceRepository
from storage.import_audit_repository import ImportAuditRepository


def format_meters(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


def format_duration(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours == 0 and minutes == 0:
        return f"{secs:02d}s"

    return f"{hours:02d}h{minutes:02d}min"


def format_datetime(dt) -> str:
    return dt.strftime("%d/%m/%Y %H:%M:%S")


def compute_file_hash(path: Path) -> str:
    sha = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)

    return sha.hexdigest()


def iter_source_files(source_row, force_rescan: bool = False):
    base_path = Path(source_row["path"])

    if not base_path.exists():
        return []

    if source_row["recursive"]:
        candidates = sorted(base_path.rglob("*.txt"))
    else:
        candidates = sorted(base_path.glob("*.txt"))

    if force_rescan:
        return candidates

    last_mtime = source_row["last_successful_mtime"]

    if last_mtime is None:
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
    parser = argparse.ArgumentParser(
        description="Nexor log import engine"
    )

    parser.add_argument(
        "--force-rescan",
        action="store_true",
        help="Ignora o checkpoint das fontes e relê todos os logs.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    print("\nNEXOR LOG IMPORT\n")

    if args.force_rescan:
        print("Modo: FORCE RESCAN (releitura completa das fontes)\n")

    init_database()

    production_repo = ProductionRepository()
    source_repo = LogSourceRepository()
    audit_repo = ImportAuditRepository()

    sources = source_repo.list_enabled()

    if not sources:
        print("Nenhuma fonte de logs ativa cadastrada.")
        print("Cadastre pelo menos uma fonte em 'log_sources'.")
        return

    grand_total_found = 0
    grand_imported = 0
    grand_duplicates = 0
    grand_errors = 0

    grand_planned_length = 0.0
    grand_consumed_length = 0.0
    grand_gap = 0.0
    grand_actual_printed = 0.0

    for source in sources:
        print("=" * 60)
        print(f"FONTE: {source['name']}")
        print(f"Caminho: {source['path']}")
        print("=" * 60)

        source_repo.update_last_scan_at(source["id"])

        files = iter_source_files(source, force_rescan=args.force_rescan)
        total = len(files)

        if not files:
            if args.force_rescan:
                print("Nenhum arquivo encontrado nesta fonte.\n")
            else:
                print("Nenhum arquivo novo encontrado nesta fonte.\n")
            continue

        run_id = audit_repo.start_run(source["id"])

        imported = 0
        duplicates = 0
        errors = 0

        total_planned_length = 0.0
        total_consumed_length = 0.0
        total_gap = 0.0
        total_actual_printed = 0.0

        max_successful_mtime = source["last_successful_mtime"]

        for file in files:
            try:
                file_mtime = file.stat().st_mtime
                file_hash = compute_file_hash(file)
                file_size = file.stat().st_size

                job = import_job_from_log(file)

                print(f"Arquivo: {file.name}")
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

                saved = production_repo.save(job)

                if saved:
                    imported += 1
                    total_planned_length += job.planned_length_m
                    total_consumed_length += job.consumed_length_m
                    total_gap += job.gap_before_m
                    total_actual_printed += job.actual_printed_length_m
                    status = "IMPORTED"

                    if max_successful_mtime is None or file_mtime > max_successful_mtime:
                        max_successful_mtime = file_mtime

                    print("Status: IMPORTADO")
                else:
                    duplicates += 1
                    status = "DUPLICATE"
                    print("Status: DUPLICADO")

                audit_repo.register_file(
                    run_id=run_id,
                    source_id=source["id"],
                    file_name=file.name,
                    file_path=str(file),
                    file_size=file_size,
                    file_hash=file_hash,
                    status=status,
                    detected_job_id=job.job_id,
                    detected_computer_name=job.computer_name,
                    detected_machine=job.machine,
                )

                print()

            except Exception as e:
                errors += 1

                try:
                    file_hash = compute_file_hash(file)
                    file_size = file.stat().st_size
                except Exception:
                    file_hash = None
                    file_size = None

                audit_repo.register_file(
                    run_id=run_id,
                    source_id=source["id"],
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

        if max_successful_mtime is not None:
            source_repo.update_last_successful_mtime(source["id"], max_successful_mtime)

        audit_repo.finish_run(
            run_id,
            total_found=total,
            imported_count=imported,
            duplicate_count=duplicates,
            error_count=errors,
        )

        print("-" * 40)
        print(f"Resumo da fonte: {source['name']}")
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


if __name__ == "__main__":
    main()
