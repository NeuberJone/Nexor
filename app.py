from pathlib import Path

from logs.service import import_job_from_log
from storage.database import init_database
from storage.repository import ProductionRepository


LOG_FOLDER = Path("logs_import")


def format_meters(value: float) -> str:
    """
    Formata metros com 2 casas decimais e vírgula.
    Exemplo: 9.9905 -> 9,99
    """
    return f"{value:.2f}".replace(".", ",")


def format_duration(seconds: int) -> str:
    """
    Converte segundos para HHhMMmin.
    Exemplo: 1027 -> 00h17min
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours:02d}h{minutes:02d}min"


def format_datetime(dt) -> str:
    """
    Formata datetime no padrão brasileiro.
    """
    return dt.strftime("%d/%m/%Y %H:%M:%S")


def main():
    print("\nNEXOR LOG IMPORT\n")

    init_database()
    repo = ProductionRepository()

    if not LOG_FOLDER.exists():
        print(f"Pasta de logs não encontrada: {LOG_FOLDER.resolve()}")
        return

    files = sorted(LOG_FOLDER.rglob("*.txt"))

    if not files:
        print(f"Nenhum arquivo .txt encontrado em: {LOG_FOLDER.resolve()}")
        return

    total = len(files)
    imported = 0
    duplicates = 0
    errors = 0

    total_length = 0.0
    total_gap = 0.0

    for file in files:
        try:
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

            saved = repo.save(job)

            if saved:
                imported += 1
                total_length += job.length_m
                total_gap += job.gap_before_m
                print("Status: IMPORTADO")
            else:
                duplicates += 1
                print("Status: DUPLICADO")

            print()

        except Exception as e:
            errors += 1
            print(f"Arquivo: {file.name}")
            print("Status: ERRO")
            print(f"Motivo: {e}\n")

    print("=" * 40)
    print("RESUMO FINAL")
    print("=" * 40)
    print(f"Logs encontrados: {total}")
    print(f"Importados: {imported}")
    print(f"Duplicados: {duplicates}")
    print(f"Erros: {errors}")

    print("\nProdução importada nesta execução:")
    print(f"Comprimento impresso: {format_meters(total_length)} m")
    print(f"Espaço técnico: {format_meters(total_gap)} m")
    print(f"Consumo operacional total: {format_meters(total_length + total_gap)} m")


if __name__ == "__main__":
    main()