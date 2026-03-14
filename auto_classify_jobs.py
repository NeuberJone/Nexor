from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from check_metrics import (
    DEFAULT_TABLE_NAME,
    DEFAULT_THRESHOLDS,
    JobSnapshot,
    SuspicionDecision,
    build_job_snapshots,
    classify_suspicion,
    connect_db,
    fetch_job_rows,
    format_m,
    format_ratio,
    is_candidate_eligible,
    resolve_default_db_path,
)


@dataclass(frozen=True)
class ClassifiedCandidate:
    job: JobSnapshot
    decision: SuspicionDecision


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classifica automaticamente jobs suspeitos sem aplicar mudanças no banco."
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=resolve_default_db_path(),
        help="Caminho do banco SQLite. Padrão: tenta localizar nexor.db automaticamente.",
    )
    parser.add_argument(
        "--table",
        default=DEFAULT_TABLE_NAME,
        help=f"Nome da tabela de jobs. Padrão: {DEFAULT_TABLE_NAME}",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Quantidade máxima de itens exibidos por categoria. Padrão: 50.",
    )
    return parser.parse_args()


def collect_candidates(
    jobs: list[JobSnapshot],
) -> tuple[list[ClassifiedCandidate], list[ClassifiedCandidate]]:
    aborted: list[ClassifiedCandidate] = []
    partial: list[ClassifiedCandidate] = []

    for job in jobs:
        if not is_candidate_eligible(job):
            continue

        decision = classify_suspicion(
            planned_length_m=job.planned_length_m,
            actual_printed_length_m=job.actual_printed_length_m,
            thresholds=DEFAULT_THRESHOLDS,
        )

        if decision.category == "ABORTED_CANDIDATE":
            aborted.append(ClassifiedCandidate(job=job, decision=decision))
        elif decision.category == "PARTIAL_CANDIDATE":
            partial.append(ClassifiedCandidate(job=job, decision=decision))

    aborted.sort(
        key=lambda item: (
            item.decision.ratio if item.decision.ratio is not None else 999.0,
            -item.decision.missing_length_m,
            item.job.start_time or "",
            item.job.job_id,
        )
    )
    partial.sort(
        key=lambda item: (
            item.decision.ratio if item.decision.ratio is not None else 999.0,
            -item.decision.missing_length_m,
            item.job.start_time or "",
            item.job.job_id,
        )
    )

    return aborted, partial


def print_header(title: str) -> None:
    print("=" * 70)
    print(title)
    print("=" * 70)


def print_group(
    title: str,
    items: list[ClassifiedCandidate],
    limit: int,
) -> None:
    print(f"\n{title}: {len(items)}")

    if not items:
        return

    for candidate in items[:limit]:
        job = candidate.job
        decision = candidate.decision

        print(
            f"- {job.job_id} | {job.document} | {job.start_time or '-'} | "
            f"planned={format_m(job.planned_length_m)} | "
            f"actual={format_m(job.actual_printed_length_m)} | "
            f"gap={format_m(job.gap_before_m)} | "
            f"consumed={format_m(job.consumed_length_m)} | "
            f"ratio={format_ratio(decision.ratio)} | "
            f"missing={format_m(decision.missing_length_m)} | "
            f"{decision.category}"
        )

    remaining = len(items) - limit
    if remaining > 0:
        print(f"... e mais {remaining} item(ns).")


def main() -> int:
    args = parse_args()

    try:
        with connect_db(args.db) as conn:
            rows = fetch_job_rows(conn, args.table)
    except Exception as exc:
        print_header("AUTO CLASSIFICATION")
        print(f"Erro ao ler o banco: {exc}")
        return 1

    jobs = build_job_snapshots(rows)
    aborted_candidates, partial_candidates = collect_candidates(jobs)

    print_header("AUTO CLASSIFICATION")
    print(f"Banco: {args.db}")
    print(f"Tabela: {args.table}")
    print(
        "Regra unificada: suspeita baseada em planned_length_m x actual_printed_length_m "
        f"(min_planned={DEFAULT_THRESHOLDS.min_planned_length_m:.2f} m, "
        f"aborted_ratio<={DEFAULT_THRESHOLDS.aborted_max_ratio:.0%}, "
        f"partial_ratio<{DEFAULT_THRESHOLDS.partial_max_ratio:.0%})"
    )

    print_group("Abortados candidatos", aborted_candidates, args.limit)
    print_group("Parciais candidatos", partial_candidates, args.limit)

    print("\nModo preview. Nada foi alterado no banco.")
    print("Use apply_auto_classification.py --apply para marcar apenas os ABORTED_CANDIDATE como FAILED.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
