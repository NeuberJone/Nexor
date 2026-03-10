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
    return f"{hours:02d}h{minutes:02d}min"


def format_datetime(dt) -> str:
    return dt.strftime("%d/%m/%Y %H:%M:%S")


def compute_file_hash(path: Path) -> str:
    sha = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)

    return sha.hexdigest()


def iter_source_files(source_row):
    base_path = Path(source_row["path"])

    if not base_path.exists():
        return []

    if source_row["recursive"]:
        return sorted(base_path.rglob("*.txt"))

    return sorted(base_path.glob("*.txt"))


def main():
    print("\nNEXOR LOG IMPORT\n")

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
    grand_length = 0.0
    grand_gap = 0.0

    for source in sources:
        print("=" * 60)
        print(f"FONTE: {source['name']}")
        print(f"Caminho: {source['path']}")
        print("=" * 60)

        files = iter_source_files(source)
        total = len(files)

        if not files:
            print("Nenhum arquivo encontrado nesta fonte.\n")
            continue

        run_id = audit_repo.start_run(source["id"])

        imported = 0
        duplicates = 0
        errors = 0
        total_length = 0.0
        total_gap = 0.0

        for file in files:
            try:
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
                print(f"Comprimento impresso: {format_meters(job.length_m)} m")
                print(f"Espaço técnico antes: {format_meters(job.gap_before_m)} m")
                print(f"Consumo operacional total: {format_meters(job.total_consumption_m)} m")

                saved = production_repo.save(job)

                if saved:
                    imported += 1
                    total_length += job.length_m
                    total_gap += job.gap_before_m
                    status = "IMPORTED"
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
        print(f"Comprimento impresso: {format_meters(total_length)} m")
        print(f"Espaço técnico: {format_meters(total_gap)} m")
        print(f"Consumo operacional total: {format_meters(total_length + total_gap)} m")
        print()

        grand_total_found += total
        grand_imported += imported
        grand_duplicates += duplicates
        grand_errors += errors
        grand_length += total_length
        grand_gap += total_gap

    print("=" * 60)
    print("RESUMO GERAL")
    print("=" * 60)
    print(f"Logs encontrados: {grand_total_found}")
    print(f"Importados: {grand_imported}")
    print(f"Duplicados: {grand_duplicates}")
    print(f"Erros: {grand_errors}")
    print(f"Comprimento impresso: {format_meters(grand_length)} m")
    print(f"Espaço técnico: {format_meters(grand_gap)} m")
    print(f"Consumo operacional total: {format_meters(grand_length + grand_gap)} m")


if __name__ == "__main__":
    main()