from __future__ import annotations

import argparse
from pathlib import Path

from analytics.production_metrics import (
    collect_candidates,
    effective_printed_length_m,
    format_m,
    format_ratio,
    load_jobs_from_db,
    resolve_default_db_path,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Confere métricas do banco do Nexor e aponta jobs suspeitos."
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
        default=20,
        help="Quantidade máxima de itens exibidos por seção.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Exibe versão compacta do relatório.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        conn, resolved_table, jobs = load_jobs_from_db(args.db, args.table)
    except Exception as exc:
        print("=" * 70)
        print("CHECK METRICS")
        print("=" * 70)
        print(f"Erro ao ler o banco: {exc}")
        return 1

    try:
        aborted_candidates, partial_candidates = collect_candidates(jobs)

        eligible_jobs = [
            job
            for job in jobs
            if job.planned_length_m > 0
            and job.counts_as_valid_production
            and job.print_status not in {"FAILED", "CANCELED", "TEST"}
            and job.job_type not in {"TEST"}
        ]

        total_planned = sum(job.planned_length_m for job in jobs)
        total_actual_raw = sum(job.actual_printed_length_m for job in jobs)
        total_effective = sum(effective_printed_length_m(job) for job in jobs)
        total_gap = sum(job.gap_before_m for job in jobs)
        total_consumed = sum(job.consumed_length_m for job in jobs)

        global_ratio = (total_effective / total_planned) if total_planned > 0 else None

        print("=" * 70)
        print("CHECK METRICS")
        print("=" * 70)
        print(f"Banco: {args.db}")
        print(f"Tabela: {resolved_table}")
        print(f"Jobs lidos: {len(jobs)}")
        print(f"Jobs elegíveis para revisão: {len(eligible_jobs)}")
        print(f"Planejado total: {format_m(total_planned)} m")
        print(f"Impresso real bruto: {format_m(total_actual_raw)} m")
        print(f"Impresso efetivo usado na análise: {format_m(total_effective)} m")
        print(f"Gap total: {format_m(total_gap)} m")
        print(f"Consumido total: {format_m(total_consumed)} m")
        print(f"Eficiência global (efetivo/planejado): {format_ratio(global_ratio)}")

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
            from analytics.production_metrics import print_candidates_block

            print_candidates_block("Abortados candidatos", aborted_candidates, args.limit)
            print_candidates_block("Parciais candidatos", partial_candidates, args.limit)

        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
