from __future__ import annotations

import argparse
from pathlib import Path

from analytics.production_metrics import format_m, format_ratio, resolve_default_db_path
from core.suspicion_rules import classify_suspicion
from storage.repository import ProductionRepository


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lista jobs com review_status=PENDING_REVIEW."
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=resolve_default_db_path(),
        help="Caminho do banco SQLite.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limita a quantidade de jobs exibidos.",
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
        help="Exibe uma linha por job.",
    )
    return parser.parse_args()


def display_job_type(job_type: str | None) -> str:
    value = (job_type or "").strip().upper()

    if value == "PRODUCTION":
        return "Produção"

    if value == "REPLACEMENT":
        return "Reposição"

    return job_type or "-"


def effective_printed_length(job) -> float:
    actual = max(float(job.actual_printed_length_m or 0.0), 0.0)
    if actual > 0:
        return actual

    return max(float(job.consumed_length_m or 0.0) - float(job.gap_before_m or 0.0), 0.0)


def live_metric_snapshot(job) -> tuple[str, str | None, float | None, float]:
    effective = effective_printed_length(job)
    decision = classify_suspicion(
        planned_length_m=job.planned_length_m,
        effective_printed_length_m=effective,
    )

    if decision.category:
        return (
            decision.category,
            decision.reason,
            decision.ratio,
            decision.missing_length_m,
        )

    if float(job.planned_length_m or 0.0) <= 0:
        return ("NO_PLANNED_LENGTH", decision.reason, decision.ratio, decision.missing_length_m)

    return ("OK", decision.reason, decision.ratio, decision.missing_length_m)


def apply_filters(jobs: list, args: argparse.Namespace) -> list:
    filtered = jobs

    if args.job_id:
        filtered = [job for job in filtered if str(job.job_id) == str(args.job_id)]

    if args.document_contains:
        needle = args.document_contains.strip().lower()
        filtered = [job for job in filtered if needle in (job.document or "").lower()]

    if args.limit is not None:
        filtered = filtered[: args.limit]

    return filtered


def render_block(job) -> str:
    effective = effective_printed_length(job)

    stored_category = job.suspicion_category
    stored_reason = job.suspicion_reason
    stored_ratio = job.suspicion_ratio
    stored_missing = job.suspicion_missing_length_m

    live_category, live_reason, live_ratio, live_missing = live_metric_snapshot(job)

    lines = [
        "-" * 60,
        f"ID: {job.id}",
        f"JOB: {job.job_id}",
        f"Documento: {job.document}",
        f"Início: {job.start_time.isoformat(timespec='seconds') if job.start_time else '-'}",
        f"Máquina: {job.machine or '-'}",
        f"Computador: {job.computer_name or '-'}",
        f"Tecido: {job.fabric or '-'}",
        f"Status atual: {job.print_status or '-'}",
        f"Tipo: {display_job_type(job.job_type)}",
        "",
        f"Planejado: {format_m(job.planned_length_m)} m",
        f"Impresso bruto: {format_m(job.actual_printed_length_m)} m",
        f"Impresso efetivo: {format_m(effective)} m",
        f"Gap: {format_m(job.gap_before_m)} m",
        f"Consumido: {format_m(job.consumed_length_m)} m",
        "",
        f"Suspeita gravada: {stored_category or '-'}",
        f"Motivo gravado: {stored_reason or '-'}",
        f"Ratio gravado: {format_ratio(stored_ratio)}",
        f"Missing gravado: {format_m(stored_missing)} m" if stored_missing is not None else "Missing gravado: -",
        "",
        f"Classificação ao vivo: {live_category}",
        f"Motivo ao vivo: {live_reason or '-'}",
        f"Ratio ao vivo: {format_ratio(live_ratio)}",
        f"Missing ao vivo: {format_m(live_missing)} m",
        "",
        f"Review status: {job.review_status or '-'}",
        f"Review note: {job.review_note or '-'}",
        f"Reviewed by: {job.reviewed_by or '-'}",
        f"Reviewed at: {job.reviewed_at.isoformat(timespec='seconds') if job.reviewed_at else '-'}",
    ]

    return "\n".join(lines)


def render_compact(job) -> str:
    effective = effective_printed_length(job)
    category = job.suspicion_category or live_metric_snapshot(job)[0]
    ratio = job.suspicion_ratio
    if ratio is None:
        _, _, ratio, _ = live_metric_snapshot(job)

    return (
        f"id={job.id} | job={job.job_id} | {job.document} | "
        f"effective={format_m(effective)} m | "
        f"ratio={format_ratio(ratio)} | "
        f"suspect={category or '-'} | "
        f"review={job.review_status or '-'}"
    )


def main() -> int:
    args = parse_args()
    repo = ProductionRepository(args.db)

    try:
        jobs = repo.list_pending_reviews()
    except Exception as exc:
        print("=" * 70)
        print("LIST PENDING REVIEWS")
        print("=" * 70)
        print(f"Erro ao listar pendências: {exc}")
        return 1

    jobs = apply_filters(jobs, args)

    print("=" * 70)
    print("LIST PENDING REVIEWS")
    print("=" * 70)
    print(f"Banco: {args.db}")

    if not jobs:
        print("\nNenhum job pendente de revisão.")
        return 0

    for job in jobs:
        print(render_compact(job) if args.compact else render_block(job))

    print("\n" + "=" * 70)
    print("RESUMO")
    print("=" * 70)
    print(f"Pendências encontradas: {len(jobs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())