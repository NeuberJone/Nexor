from __future__ import annotations

import argparse
from pathlib import Path

from analytics.production_metrics import (
    ClassifiedCandidate,
    collect_candidates,
    load_jobs_from_db,
    print_candidates_block,
    resolve_default_db_path,
)
from storage.repository import ProductionRepository


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Marca jobs suspeitos para revisão humana, sem alterar o print_status."
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
        help="Grava suspicion_* e review_status=PENDING_REVIEW no banco.",
    )
    parser.add_argument(
        "--keep-stale",
        action="store_true",
        help="Mantém suspeitas pendentes antigas que não apareceram nesta rodada.",
    )
    return parser.parse_args()


def _print_compact(title: str, items: list[ClassifiedCandidate], limit: int) -> None:
    print(f"\n{title}: {len(items)}")
    for candidate in items[:limit]:
        job = candidate.job
        print(
            f"- {job.job_id} | {job.document} | {job.start_time or '-'} | "
            f"{candidate.decision.category}"
        )


def main() -> int:
    args = parse_args()

    try:
        conn, resolved_table, jobs = load_jobs_from_db(args.db, args.table)
    except Exception as exc:
        print("=" * 70)
        print("MARK SUSPECTS")
        print("=" * 70)
        print(f"Erro ao ler o banco: {exc}")
        return 1

    try:
        aborted_candidates, partial_candidates = collect_candidates(jobs)

        print("=" * 70)
        print("MARK SUSPECTS")
        print("=" * 70)
        print(f"Banco: {args.db}")
        print(f"Tabela: {resolved_table}")

        if args.compact:
            _print_compact("Abortados candidatos", aborted_candidates, args.limit)
            _print_compact("Parciais candidatos", partial_candidates, args.limit)
        else:
            print_candidates_block("Abortados candidatos", aborted_candidates, args.limit)
            print_candidates_block("Parciais candidatos", partial_candidates, args.limit)
    finally:
        conn.close()

    if not args.apply:
        print("\nModo preview. Nada foi alterado no banco.")
        print("Use --apply para gravar suspicion_* e review_status=PENDING_REVIEW.")
        return 0

    repo = ProductionRepository(args.db, table_name=resolved_table)
    repo.ensure_review_fields()

    total_marked = 0
    active_row_ids: set[int] = set()

    for candidate in [*aborted_candidates, *partial_candidates]:
        row_id = candidate.job.rowid
        if row_id is None:
            continue

        active_row_ids.add(int(row_id))
        repo.mark_job_suspicion(
            row_id=int(row_id),
            category=candidate.decision.category or "UNKNOWN",
            reason=candidate.decision.reason,
            ratio=candidate.decision.ratio,
            missing_length_m=candidate.decision.missing_length_m,
        )
        total_marked += 1

    cleared = 0
    if not args.keep_stale:
        cleared = repo.clear_stale_pending_suspicions(active_row_ids)

    print(f"\nSuspeitas gravadas/atualizadas: {total_marked}")
    print(f"Pendências antigas limpas: {cleared}")
    print("Nenhum print_status foi alterado. Esta etapa apenas sinaliza para revisão humana.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
