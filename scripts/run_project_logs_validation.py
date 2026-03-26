from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cli.commands import handle_import
from storage.database import get_connection, init_database
from storage.import_audit_repository import ImportAuditRepository
from storage.log_sources_repository import LogSourceRepository


DEFAULT_SOURCE_NAME = "PROJECT_LOGS_IMPORT"
SQLITE_MAX_VARS = 900


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Executa validação ponta a ponta usando a pasta logs_import do projeto."
    )
    parser.add_argument(
        "--source-name",
        default=DEFAULT_SOURCE_NAME,
        help=f"Nome do source no banco. Padrão: {DEFAULT_SOURCE_NAME}",
    )
    parser.add_argument(
        "--path",
        default=str(PROJECT_ROOT / "logs_import"),
        help="Caminho da pasta de logs. Padrão: <project>/logs_import",
    )
    parser.add_argument(
        "--disable-others",
        action="store_true",
        help="Desabilita todos os outros sources para isolar o teste nesta pasta.",
    )
    parser.add_argument(
        "--reset-checkpoint",
        action="store_true",
        help="Reseta checkpoint antes do import.",
    )
    parser.add_argument(
        "--non-recursive",
        action="store_true",
        help="Registra o source como não recursivo.",
    )
    parser.add_argument(
        "--force-rescan",
        action="store_true",
        help="Força releitura completa no import.",
    )
    parser.add_argument(
        "--show-errors",
        type=int,
        default=10,
        help="Máximo de arquivos com erro para exibir. Padrão: 10",
    )
    parser.add_argument(
        "--show-suspicious",
        type=int,
        default=10,
        help="Máximo de jobs suspeitos para exibir. Padrão: 10",
    )
    parser.add_argument(
        "--show-pending",
        type=int,
        default=10,
        help="Máximo de jobs pendentes para exibir. Padrão: 10",
    )
    return parser.parse_args()


def safe_text(value, default: str = "-") -> str:
    text = str(value or "").strip()
    return text or default


def fmt_dt(value) -> str:
    if not value:
        return "-"
    text = str(value).strip()
    if not text:
        return "-"
    return text.replace("T", " ")


def fmt_m(value) -> str:
    try:
        return f"{float(value or 0.0):.2f} m"
    except Exception:
        return "0.00 m"


def chunked(values: list[str], size: int) -> Iterable[list[str]]:
    for index in range(0, len(values), size):
        yield values[index:index + size]


def fetch_jobs_for_file_paths(file_paths: list[str]) -> list:
    if not file_paths:
        return []

    conn = get_connection()
    rows = []

    try:
        for part in chunked(file_paths, SQLITE_MAX_VARS):
            placeholders = ",".join("?" for _ in part)
            sql = f"""
                SELECT
                    id,
                    job_id,
                    machine,
                    computer_name,
                    document,
                    fabric,
                    start_time,
                    end_time,
                    planned_length_m,
                    actual_printed_length_m,
                    gap_before_m,
                    consumed_length_m,
                    print_status,
                    review_status,
                    classification,
                    suspicion_category,
                    suspicion_reason,
                    source_path
                FROM production_jobs
                WHERE source_path IN ({placeholders})
                ORDER BY start_time DESC, id DESC
            """
            rows.extend(conn.execute(sql, tuple(part)).fetchall())
        return rows
    finally:
        conn.close()


def build_counter(rows: list, field_name: str) -> Counter:
    counter: Counter = Counter()
    for row in rows:
        counter[safe_text(row[field_name])] += 1
    return counter


def print_counter_block(title: str, counter: Counter) -> None:
    print(title)
    if not counter:
        print("  - -")
        print()
        return

    for key, value in counter.most_common():
        print(f"  - {key}: {value}")
    print()


def print_error_files(rows: list, limit: int) -> None:
    print("Arquivos com erro:")
    error_rows = [row for row in rows if safe_text(row["status"]) == "ERROR"]

    if not error_rows:
        print("  - Nenhum")
        print()
        return

    for row in error_rows[:limit]:
        print(
            f"  - {safe_text(row['file_name'])} | "
            f"status={safe_text(row['status'])} | "
            f"job={safe_text(row['detected_job_id'])} | "
            f"motivo={safe_text(row['error_message'])}"
        )

    if len(error_rows) > limit:
        print(f"  ... e mais {len(error_rows) - limit} arquivo(s) com erro.")
    print()


def print_suspicious_jobs(rows: list, limit: int) -> None:
    print("Jobs suspeitos:")
    suspicious = [
        row for row in rows
        if safe_text(row["suspicion_category"]) != "-" or safe_text(row["suspicion_reason"]) != "-"
    ]

    if not suspicious:
        print("  - Nenhum")
        print()
        return

    for row in suspicious[:limit]:
        file_name = "-"
        src = safe_text(row["source_path"], default="")
        if src:
            file_name = Path(src).name

        print(
            f"  - row_id={row['id']} | "
            f"job={safe_text(row['job_id'])} | "
            f"machine={safe_text(row['machine'])} | "
            f"fabric={safe_text(row['fabric'])} | "
            f"print_status={safe_text(row['print_status'])} | "
            f"review={safe_text(row['review_status'])} | "
            f"classification={safe_text(row['classification'])} | "
            f"suspicion={safe_text(row['suspicion_category'])} | "
            f"motivo={safe_text(row['suspicion_reason'])} | "
            f"consumed={fmt_m(row['consumed_length_m'])} | "
            f"file={file_name}"
        )

    if len(suspicious) > limit:
        print(f"  ... e mais {len(suspicious) - limit} job(s) suspeito(s).")
    print()


def print_pending_jobs(rows: list, limit: int) -> None:
    print("Jobs pendentes de review:")
    pending = [row for row in rows if safe_text(row["review_status"]) == "PENDING_REVIEW"]

    if not pending:
        print("  - Nenhum")
        print()
        return

    for row in pending[:limit]:
        print(
            f"  - row_id={row['id']} | "
            f"job={safe_text(row['job_id'])} | "
            f"machine={safe_text(row['machine'])} | "
            f"fabric={safe_text(row['fabric'])} | "
            f"print_status={safe_text(row['print_status'])} | "
            f"classification={safe_text(row['classification'])} | "
            f"effective={fmt_m(row['actual_printed_length_m'])} | "
            f"gap={fmt_m(row['gap_before_m'])} | "
            f"consumed={fmt_m(row['consumed_length_m'])}"
        )

    if len(pending) > limit:
        print(f"  ... e mais {len(pending) - limit} job(s) pendente(s).")
    print()


def configure_source(
    *,
    source_name: str,
    path: str,
    disable_others: bool,
    reset_checkpoint: bool,
    recursive: bool,
) -> int:
    repo = LogSourceRepository()
    target_path = Path(path).resolve()

    if not target_path.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {target_path}")

    if not target_path.is_dir():
        raise NotADirectoryError(f"O caminho informado não é uma pasta: {target_path}")

    source_id = repo.upsert(
        name=source_name,
        path=str(target_path),
        recursive=recursive,
        machine_hint=None,
        enabled=True,
    )

    if disable_others:
        for row in repo.list_all():
            row_id = int(row["id"])
            if row_id != source_id and int(row["enabled"] or 0) == 1:
                repo.disable(row_id)

    if reset_checkpoint:
        repo.reset_checkpoint(source_id)

    return source_id


def resolve_latest_run_for_source(source_id: int):
    audit_repo = ImportAuditRepository()
    runs = audit_repo.list_runs(source_id=source_id, limit=1)
    if not runs:
        return None
    return runs[0]


def main() -> int:
    args = parse_args()

    try:
        init_database()

        source_id = configure_source(
            source_name=args.source_name,
            path=args.path,
            disable_others=args.disable_others,
            reset_checkpoint=args.reset_checkpoint,
            recursive=not args.non_recursive,
        )
    except Exception as exc:
        print("Status: ERRO")
        print(f"Motivo ao preparar source: {exc}")
        return 1

    source_repo = LogSourceRepository()
    source = source_repo.get_by_id(source_id)

    print("\nNEXOR PROJECT LOGS VALIDATION\n")
    print("Etapa 1: source preparado")
    print(f"- Source ID: {source_id}")
    print(f"- Nome: {safe_text(source['name'])}")
    print(f"- Caminho: {safe_text(source['path'])}")
    print(f"- Recursivo: {'SIM' if int(source['recursive'] or 0) == 1 else 'NÃO'}")
    print(f"- Habilitado: {'SIM' if int(source['enabled'] or 0) == 1 else 'NÃO'}")
    print()

    print("Etapa 2: executando import real")
    import_exit = handle_import(force_rescan=args.force_rescan)
    print()

    if import_exit != 0:
        print("Status: ERRO")
        print("Motivo: o import retornou falha.")
        return int(import_exit)

    run = resolve_latest_run_for_source(source_id)
    if run is None:
        print("Status: ERRO")
        print("Motivo: nenhum import run encontrado após a execução.")
        return 1

    audit_repo = ImportAuditRepository()
    run_files = list(audit_repo.list_run_files(int(run["id"])))

    file_paths: list[str] = []
    for row in run_files:
        text = safe_text(row["file_path"], default="")
        if text:
            file_paths.append(text)

    jobs = fetch_jobs_for_file_paths(file_paths)

    print("Etapa 3: resumo do último run")
    print(f"- Run ID: {run['id']}")
    print(f"- Iniciado em: {fmt_dt(run['started_at'])}")
    print(f"- Finalizado em: {fmt_dt(run['finished_at'])}")
    print(f"- total_found: {int(run['total_found'] or 0)}")
    print(f"- imported_count: {int(run['imported_count'] or 0)}")
    print(f"- duplicate_count: {int(run['duplicate_count'] or 0)}")
    print(f"- error_count: {int(run['error_count'] or 0)}")
    print(f"- arquivos auditados: {len(run_files)}")
    print(f"- jobs localizados: {len(jobs)}")
    print()

    print_counter_block(
        "Status dos arquivos auditados:",
        build_counter(run_files, "status"),
    )
    print_counter_block(
        "Review status dos jobs:",
        build_counter(jobs, "review_status"),
    )
    print_counter_block(
        "Print status dos jobs:",
        build_counter(jobs, "print_status"),
    )
    print_counter_block(
        "Classification dos jobs:",
        build_counter(jobs, "classification"),
    )
    print_counter_block(
        "Suspicion category dos jobs:",
        build_counter(jobs, "suspicion_category"),
    )
    print_counter_block(
        "Máquinas detectadas:",
        build_counter(jobs, "machine"),
    )
    print_counter_block(
        "Tecidos detectados:",
        build_counter(jobs, "fabric"),
    )

    print_error_files(run_files, args.show_errors)
    print_suspicious_jobs(jobs, args.show_suspicious)
    print_pending_jobs(jobs, args.show_pending)

    print("Próximo passo sugerido:")
    print("- comparar esse resultado com o comportamento esperado dos logs reais")
    print("- identificar onde o parser/classificação acertou")
    print("- listar os casos que precisam ajuste de regra")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())