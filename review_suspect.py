from __future__ import annotations

import argparse
from pathlib import Path

from analytics.production_metrics import format_m, format_ratio, resolve_default_db_path
from core.models import REVIEWED_FAILED, REVIEWED_OK, REVIEWED_PARTIAL
from core.suspicion_rules import classify_suspicion
from storage.repository import ProductionRepository


ALLOWED_REVIEW_STATUSES = {
    REVIEWED_FAILED,
    REVIEWED_OK,
    REVIEWED_PARTIAL,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Revisa manualmente um job suspeito do Nexor."
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=resolve_default_db_path(),
        help="Caminho do banco SQLite.",
    )
    parser.add_argument(
        "--id",
        type=int,
        default=None,
        help="ID interno do registro.",
    )
    parser.add_argument(
        "--job-id",
        default=None,
        help="Job ID do registro.",
    )
    parser.add_argument(
        "--status",
        required=True,
        choices=sorted(ALLOWED_REVIEW_STATUSES),
        help="Novo status de revisão.",
    )
    parser.add_argument(
        "--note",
        default=None,
        help="Observação da revisão.",
    )
    parser.add_argument(
        "--reviewed-by",
        default=None,
        help="Nome ou código de quem revisou.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica a revisão no banco. Sem isso, roda só em preview.",
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


def find_target_job(repo: ProductionRepository, job_row_id: int | None, job_id: str | None):
    jobs = repo.list_jobs()

    if job_row_id is not None:
        for job in jobs:
            if job.id == job_row_id:
                return job

    if job_id is not None:
        matches = [job for job in jobs if str(job.job_id) == str(job_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ValueError(
                f"Mais de um registro encontrado para job_id={job_id}. Use --id para desambiguar."
            )

    raise ValueError("Job não encontrado.")


def render_preview(job, next_status: str, note: str | None, reviewed_by: str | None) -> str:
    effective = effective_printed_length(job)
    live_category, live_reason, live_ratio, live_missing = live_metric_snapshot(job)

    lines = [
        "=" * 70,
        "REVIEW SUSPECT",
        "=" * 70,
        f"ID: {job.id}",
        f"JOB: {job.job_id}",
        f"Documento: {job.document}",
        f"Início: {job.start_time.isoformat(timespec='seconds') if job.start_time else '-'}",
        f"Máquina: {job.machine or '-'}",
        f"Tecido: {job.fabric or '-'}",
        f"Status atual do job: {job.print_status or '-'}",
        f"Tipo: {display_job_type(job.job_type)}",
        "",
        f"Planejado: {format_m(job.planned_length_m)} m",
        f"Impresso bruto: {format_m(job.actual_printed_length_m)} m",
        f"Impresso efetivo: {format_m(effective)} m",
        f"Gap: {format_m(job.gap_before_m)} m",
        f"Consumido: {format_m(job.consumed_length_m)} m",
        "",
        f"Suspeita gravada: {job.suspicion_category or '-'}",
        f"Motivo gravado: {job.suspicion_reason or '-'}",
        f"Review status atual: {job.review_status or '-'}",
        f"Review note atual: {job.review_note or '-'}",
        f"Reviewed by atual: {job.reviewed_by or '-'}",
        "",
        f"Classificação ao vivo: {live_category}",
        f"Motivo ao vivo: {live_reason or '-'}",
        f"Ratio ao vivo: {format_ratio(live_ratio)}",
        f"Missing ao vivo: {format_m(live_missing)} m",
        "",
        f"Novo review_status: {next_status}",
        f"Nova note: {note or '-'}",
        f"Novo reviewed_by: {reviewed_by or '-'}",
    ]

    return "\n".join(lines)


def main() -> int:
    args = parse_args()

    if args.id is None and args.job_id is None:
        print("Informe --id ou --job-id.")
        return 1

    repo = ProductionRepository(args.db)

    try:
        target = find_target_job(repo, args.id, args.job_id)
    except Exception as exc:
        print("=" * 70)
        print("REVIEW SUSPECT")
        print("=" * 70)
        print(f"Erro ao localizar job: {exc}")
        return 1

    print(render_preview(target, args.status, args.note, args.reviewed_by))

    if not args.apply:
        print("\nModo preview. Nada foi alterado no banco.")
        print("Use --apply para gravar a revisão.")
        return 0

    try:
        if target.id is None:
            raise ValueError("O job encontrado não possui ID persistido para atualização.")

        repo.update_review(
            row_id=int(target.id),
            review_status=args.status,
            review_note=args.note,
            reviewed_by=args.reviewed_by,
        )
    except Exception as exc:
        print(f"\nErro ao gravar revisão: {exc}")
        return 1

    print("\nRevisão gravada com sucesso.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())