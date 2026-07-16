from __future__ import annotations

import argparse
from pathlib import Path

from analytics.production_metrics import (
    apply_failed_status_to_aborted_candidates,
    collect_candidates,
    load_jobs_from_db,
    print_candidates_block,
    resolve_default_db_path,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aplica classificação automática apenas para ABORTED_CANDIDATE."
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=resolve_default_db_path(),
        help="Caminho do banco SQLite.",
    )
    parser.add_argument(
        "--table",
        default=None,
        help="Nome da tabela de jobs. Se omitido, o script tenta descobrir automaticamente.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Quantidade máxima de itens exibidos por categoria.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Exibe versão compacta do preview.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica no banco apenas os ABORTED_CANDIDATE.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        conn, resolved_table, jobs = load_jobs_from_db(args.db, args.table)
    except Exception as exc:
        print("=" * 70)
        print("APPLY AUTO CLASSIFICATION")
        print("=" * 70)
        print(f"Erro ao ler o banco: {exc}")
        return 1

    try:
        aborted_candidates, partial_candidates = collect_candidates(jobs)

        print("=" * 70)
        print("APPLY AUTO CLASSIFICATION")
        print("=" * 70)
        print(f"Banco: {args.db}")
        print(f"Tabela: {resolved_table}")

        if args.compact:
            print(f"\nAbortados candidatos: {len(aborted_candidates)}")
            for candidate in aborted_candidates[: args.limit]:
                job = candidate.job
                print(f"- {job.job_id} | {job.document} | {job.start_time or '-'} | ABORTED_CANDIDATE")

            print(f"\nParciais candidatos: {len(partial_candidates)}")
            for candidate in partial_candidates[: args.limit]:
                job = candidate.job
                print(f"- {job.job_id} | {job.document} | {job.start_time or '-'} | PARTIAL_CANDIDATE")
        else:
            print_candidates_block("Abortados candidatos", aborted_candidates, args.limit)
            print_candidates_block("Parciais candidatos", partial_candidates, args.limit)

        if not args.apply:
            print("\nModo preview. Nada foi alterado no banco.")
            print("Use --apply para marcar apenas os ABORTED_CANDIDATE como FAILED.")
            return 0

        applied = apply_failed_status_to_aborted_candidates(
            conn=conn,
            table_name=resolved_table,
            candidates=aborted_candidates,
        )

        print(f"\nAplicação concluída. Jobs marcados como FAILED: {applied}")
        print("PARTIAL_CANDIDATE continua apenas como sugestão, sem autoaplicação.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
