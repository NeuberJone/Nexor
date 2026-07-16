from __future__ import annotations

import argparse
from pathlib import Path

from analytics.production_metrics import (
    JobSnapshot,
    classify_job,
    effective_printed_length_m,
    format_m,
    format_ratio,
    load_jobs_from_db,
    resolve_default_db_path,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera relatório detalhado de auditoria dos jobs do Nexor."
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
        default=None,
        help="Limita a quantidade de jobs exibidos.",
    )
    parser.add_argument(
        "--only-suspects",
        action="store_true",
        help="Mostra apenas jobs classificados como ABORTED_CANDIDATE ou PARTIAL_CANDIDATE.",
    )
    parser.add_argument(
        "--job-id",
        default=None,
        help="Filtra por um job_id específico.",
    )
    parser.add_argument(
        "--document-contains",
        default=None,
        help="Filtra jobs cujo documento contenha este texto.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Exibe uma linha por job, em vez do bloco detalhado.",
    )
    return parser.parse_args()


def display_job_type(job_type: str | None) -> str:
    value = (job_type or "").strip().upper()

    if value == "PRODUCTION":
        return "Produção"

    if value == "REPLACEMENT":
        return "Reposição"

    return job_type or "-"


def review_state(job: JobSnapshot) -> str:
    """
    Situação operacional do job para fins de revisão.
    Isso é separado da classificação por metragem.
    """

    if job.planned_length_m <= 0:
        return "SKIPPED_NO_PLANNED_LENGTH"

    if job.print_status == "FAILED":
        return "SKIPPED_ALREADY_FAILED"

    if job.print_status == "CANCELED":
        return "SKIPPED_CANCELED"

    if job.print_status == "TEST" or job.job_type == "TEST":
        return "SKIPPED_TEST"

    if not job.counts_as_valid_production:
        return "SKIPPED_INVALID_PRODUCTION"

    return "ELIGIBLE_FOR_REVIEW"


def metric_classification(job: JobSnapshot) -> tuple[str, str | None, float | None, float]:
    """
    Classificação do Nexor baseada na metragem/efetivo.
    Essa classificação existe mesmo para jobs já FAILED.
    """
    decision = classify_job(job)

    if decision.category:
        return (
            decision.category,
            decision.reason,
            decision.ratio,
            decision.missing_length_m,
        )

    if job.planned_length_m <= 0:
        return ("NO_PLANNED_LENGTH", decision.reason, decision.ratio, decision.missing_length_m)

    return ("OK", decision.reason, decision.ratio, decision.missing_length_m)


def filter_jobs(jobs: list[JobSnapshot], args: argparse.Namespace) -> list[JobSnapshot]:
    filtered = jobs

    if args.job_id:
        filtered = [job for job in filtered if str(job.job_id) == str(args.job_id)]

    if args.document_contains:
        needle = args.document_contains.strip().lower()
        filtered = [job for job in filtered if needle in (job.document or "").lower()]

    if args.only_suspects:
        suspect_jobs: list[JobSnapshot] = []
        for job in filtered:
            label, _, _, _ = metric_classification(job)
            if label in {"ABORTED_CANDIDATE", "PARTIAL_CANDIDATE"}:
                suspect_jobs.append(job)
        filtered = suspect_jobs

    if args.limit is not None:
        filtered = filtered[: args.limit]

    return filtered


def print_job_block(job: JobSnapshot) -> str:
    label, reason, ratio, missing = metric_classification(job)
    effective = effective_printed_length_m(job)
    state = review_state(job)

    lines = [
        "-" * 60,
        f"JOB: {job.job_id}",
        f"Documento: {job.document}",
        f"Início: {job.start_time or '-'}",
        f"Máquina: {job.machine or '-'}",
        f"Computador: {job.computer_name or '-'}",
        f"Tecido: {job.fabric or '-'}",
        f"Status: {job.print_status or '-'}",
        f"Tipo: {display_job_type(job.job_type)}",
        "",
        f"Planejado: {format_m(job.planned_length_m)} m",
        f"Impresso bruto: {format_m(job.actual_printed_length_m)} m",
        f"Impresso efetivo: {format_m(effective)} m",
        f"Gap: {format_m(job.gap_before_m)} m",
        f"Consumido: {format_m(job.consumed_length_m)} m",
        "",
        f"Percentual impresso: {format_ratio(ratio)}",
        f"Faltante: {format_m(missing)} m",
        f"Classificação Nexor: {label}",
        f"Motivo: {reason or '-'}",
        f"Situação da revisão: {state}",
    ]

    if getattr(job, "suspicion_category", None):
        lines.append("")
        lines.append(f"Suspeita gravada: {job.suspicion_category}")
        lines.append(f"Review status: {job.review_status or '-'}")
        lines.append(f"Review note: {job.review_note or '-'}")
        lines.append(f"Reviewed by: {job.reviewed_by or '-'}")

    return "\n".join(lines)


def print_job_compact(job: JobSnapshot) -> str:
    label, reason, ratio, missing = metric_classification(job)
    effective = effective_printed_length_m(job)
    state = review_state(job)

    return (
        f"{job.job_id} | {job.document} | {job.start_time or '-'} | "
        f"planned={format_m(job.planned_length_m)} m | "
        f"actual={format_m(job.actual_printed_length_m)} m | "
        f"effective={format_m(effective)} m | "
        f"gap={format_m(job.gap_before_m)} m | "
        f"consumed={format_m(job.consumed_length_m)} m | "
        f"ratio={format_ratio(ratio)} | "
        f"missing={format_m(missing)} m | "
        f"class={label} | "
        f"reason={reason or '-'} | "
        f"review={state}"
    )


def print_summary(jobs: list[JobSnapshot]) -> None:
    total_jobs = len(jobs)

    metric_ok = 0
    metric_aborted = 0
    metric_partial = 0
    metric_no_planned = 0

    review_eligible = 0
    review_skipped_failed = 0
    review_skipped_canceled = 0
    review_skipped_test = 0
    review_skipped_invalid = 0
    review_skipped_no_planned = 0

    total_planned = 0.0
    total_actual = 0.0
    total_effective = 0.0
    total_gap = 0.0
    total_consumed = 0.0

    for job in jobs:
        label, _, _, _ = metric_classification(job)
        state = review_state(job)

        total_planned += job.planned_length_m
        total_actual += job.actual_printed_length_m
        total_effective += effective_printed_length_m(job)
        total_gap += job.gap_before_m
        total_consumed += job.consumed_length_m

        if label == "OK":
            metric_ok += 1
        elif label == "ABORTED_CANDIDATE":
            metric_aborted += 1
        elif label == "PARTIAL_CANDIDATE":
            metric_partial += 1
        elif label == "NO_PLANNED_LENGTH":
            metric_no_planned += 1

        if state == "ELIGIBLE_FOR_REVIEW":
            review_eligible += 1
        elif state == "SKIPPED_ALREADY_FAILED":
            review_skipped_failed += 1
        elif state == "SKIPPED_CANCELED":
            review_skipped_canceled += 1
        elif state == "SKIPPED_TEST":
            review_skipped_test += 1
        elif state == "SKIPPED_INVALID_PRODUCTION":
            review_skipped_invalid += 1
        elif state == "SKIPPED_NO_PLANNED_LENGTH":
            review_skipped_no_planned += 1

    global_ratio = (total_effective / total_planned) if total_planned > 0 else None

    print("\n" + "=" * 70)
    print("RESUMO DA AUDITORIA")
    print("=" * 70)
    print(f"Jobs considerados no relatório: {total_jobs}")
    print("")
    print("Classificação por metragem:")
    print(f"OK: {metric_ok}")
    print(f"ABORTED_CANDIDATE: {metric_aborted}")
    print(f"PARTIAL_CANDIDATE: {metric_partial}")
    print(f"NO_PLANNED_LENGTH: {metric_no_planned}")
    print("")
    print("Situação da revisão:")
    print(f"ELIGIBLE_FOR_REVIEW: {review_eligible}")
    print(f"SKIPPED_ALREADY_FAILED: {review_skipped_failed}")
    print(f"SKIPPED_CANCELED: {review_skipped_canceled}")
    print(f"SKIPPED_TEST: {review_skipped_test}")
    print(f"SKIPPED_INVALID_PRODUCTION: {review_skipped_invalid}")
    print(f"SKIPPED_NO_PLANNED_LENGTH: {review_skipped_no_planned}")
    print("")
    print(f"Planejado total: {format_m(total_planned)} m")
    print(f"Impresso bruto total: {format_m(total_actual)} m")
    print(f"Impresso efetivo total: {format_m(total_effective)} m")
    print(f"Gap total: {format_m(total_gap)} m")
    print(f"Consumido total: {format_m(total_consumed)} m")
    print(f"Eficiência global (efetivo/planejado): {format_ratio(global_ratio)}")


def main() -> int:
    args = parse_args()

    try:
        conn, resolved_table, jobs = load_jobs_from_db(args.db, args.table)
    except Exception as exc:
        print("=" * 70)
        print("REPORT JOB AUDIT")
        print("=" * 70)
        print(f"Erro ao ler o banco: {exc}")
        return 1

    try:
        jobs = filter_jobs(jobs, args)

        print("=" * 70)
        print("REPORT JOB AUDIT")
        print("=" * 70)
        print(f"Banco: {args.db}")
        print(f"Tabela: {resolved_table}")

        if not jobs:
            print("\nNenhum job encontrado com os filtros informados.")
            return 0

        for job in jobs:
            if args.compact:
                print(print_job_compact(job))
            else:
                print(print_job_block(job))

        print_summary(jobs)
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())