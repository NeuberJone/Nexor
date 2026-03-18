from __future__ import annotations

import argparse
from pathlib import Path

from analytics.production_metrics import format_m, format_ratio, resolve_default_db_path
from core.models import ROLL_CLOSED, ROLL_OPEN
from storage.repository import ProductionRepository


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Operações básicas de rolo no Nexor."
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=resolve_default_db_path(),
        help="Caminho do banco SQLite.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    p_open = subparsers.add_parser("open", help="Abre um novo rolo.")
    p_open.add_argument("--machine", required=True, help="Máquina do rolo.")
    p_open.add_argument("--fabric", default=None, help="Tecido do rolo.")
    p_open.add_argument("--note", default=None, help="Observação inicial.")
    p_open.add_argument(
        "--name",
        default=None,
        help="Nome manual do rolo. Se omitido, o Nexor gera automaticamente.",
    )

    p_list = subparsers.add_parser("list", help="Lista rolos.")
    p_list.add_argument(
        "--status",
        default="ALL",
        choices=["ALL", ROLL_OPEN, ROLL_CLOSED],
        help="Filtra por status.",
    )

    p_show = subparsers.add_parser("show", help="Mostra detalhes de um rolo.")
    p_show.add_argument("--id", type=int, default=None, help="ID do rolo.")
    p_show.add_argument("--name", default=None, help="Nome do rolo.")

    p_add = subparsers.add_parser("add-job", help="Adiciona um job ao rolo.")
    p_add.add_argument("--roll-id", type=int, default=None, help="ID do rolo.")
    p_add.add_argument("--roll-name", default=None, help="Nome do rolo.")
    p_add.add_argument("--job-row-id", type=int, default=None, help="ID interno do job.")
    p_add.add_argument("--job-id", default=None, help="JobID do job.")

    p_remove = subparsers.add_parser("remove-job", help="Remove um job do rolo.")
    p_remove.add_argument("--roll-id", type=int, default=None, help="ID do rolo.")
    p_remove.add_argument("--roll-name", default=None, help="Nome do rolo.")
    p_remove.add_argument("--job-row-id", type=int, default=None, help="ID interno do job.")
    p_remove.add_argument("--job-id", default=None, help="JobID do job.")

    p_add_note = subparsers.add_parser("add-note", help="Adiciona uma observação ao rolo.")
    p_add_note.add_argument("--id", type=int, default=None, help="ID do rolo.")
    p_add_note.add_argument("--name", default=None, help="Nome do rolo.")
    p_add_note.add_argument("--note", required=True, help="Observação a acrescentar.")
    p_add_note.add_argument(
        "--operator",
        default=None,
        help="Operador responsável pela anotação.",
    )

    p_close = subparsers.add_parser("close", help="Fecha um rolo.")
    p_close.add_argument("--id", type=int, default=None, help="ID do rolo.")
    p_close.add_argument("--name", default=None, help="Nome do rolo.")
    p_close.add_argument("--note", default=None, help="Observação de fechamento.")

    return parser.parse_args()


def _resolve_roll(repo: ProductionRepository, roll_id: int | None, roll_name: str | None):
    if roll_id is None and roll_name is None:
        raise ValueError("Informe --id/--roll-id ou --name/--roll-name.")

    roll = repo.get_roll(roll_id=roll_id, roll_name=roll_name)
    if not roll:
        raise ValueError("Rolo não encontrado.")
    return roll


def _print_roll_list(rolls: list) -> None:
    print("=" * 70)
    print("ROLLOS")
    print("=" * 70)

    if not rolls:
        print("Nenhum rolo encontrado.")
        return

    for roll in rolls:
        print(
            f"id={roll.id} | name={roll.roll_name} | machine={roll.machine} | "
            f"fabric={roll.fabric or '-'} | status={roll.status} | "
            f"created_at={roll.created_at.isoformat(timespec='seconds') if roll.created_at else '-'} | "
            f"closed_at={roll.closed_at.isoformat(timespec='seconds') if roll.closed_at else '-'}"
        )


def _print_roll_summary(summary: dict) -> None:
    roll = summary["roll"]
    items = summary["items"]

    print("=" * 70)
    print("ROLL DETAIL")
    print("=" * 70)
    print(f"ID: {roll.id}")
    print(f"Nome: {roll.roll_name}")
    print(f"Máquina: {roll.machine}")
    print(f"Tecido: {roll.fabric or '-'}")
    print(f"Status: {roll.status}")
    print(f"Criado em: {roll.created_at.isoformat(timespec='seconds') if roll.created_at else '-'}")
    print(f"Fechado em: {roll.closed_at.isoformat(timespec='seconds') if roll.closed_at else '-'}")
    print("Nota:")
    print(roll.note or "-")

    print("\n" + "-" * 70)
    print("RESUMO")
    print("-" * 70)
    print(f"Jobs no rolo: {summary['jobs_count']}")
    print(f"Planejado total: {format_m(summary['total_planned_m'])} m")
    print(f"Impresso efetivo total: {format_m(summary['total_effective_m'])} m")
    print(f"Consumido total: {format_m(summary['total_consumed_m'])} m")
    print(f"Gap total: {format_m(summary['total_gap_m'])} m")
    print(f"Eficiência: {format_ratio(summary['efficiency_ratio'])}")

    print("\nClassificação dos itens:")
    metric_counts = summary["metric_counts"]
    if metric_counts:
        for key, value in sorted(metric_counts.items()):
            print(f"- {key}: {value}")
    else:
        print("- Nenhuma")

    print("\nTecido por metragem efetiva:")
    fabric_totals = summary["fabric_totals"]
    if fabric_totals:
        for fabric, total_m in sorted(fabric_totals.items()):
            print(f"- {fabric}: {format_m(total_m)} m")
    else:
        print("- Nenhuma")

    print("\n" + "-" * 70)
    print("ITENS")
    print("-" * 70)

    if not items:
        print("Rolo vazio.")
        return

    for item in items:
        print(
            f"sort={item.sort_order} | job_row_id={item.job_row_id} | job_id={item.job_id} | "
            f"{item.document} | machine={item.machine} | fabric={item.fabric or '-'} | "
            f"planned={format_m(item.planned_length_m)} m | "
            f"effective={format_m(item.effective_printed_length_m)} m | "
            f"consumed={format_m(item.consumed_length_m)} m | "
            f"gap={format_m(item.gap_before_m)} m | "
            f"metric={item.metric_category or '-'} | "
            f"review={item.review_status or '-'} | "
            f"status={item.snapshot_print_status or '-'}"
        )


def main() -> int:
    args = parse_args()
    repo = ProductionRepository(args.db)

    try:
        repo.ensure_roll_tables()

        if args.command == "open":
            roll_id = repo.create_roll(
                machine=args.machine,
                fabric=args.fabric,
                note=args.note,
                roll_name=args.name,
            )
            roll = repo.get_roll(roll_id=roll_id)
            print("=" * 70)
            print("ROLL OPENED")
            print("=" * 70)
            print(
                f"id={roll.id} | name={roll.roll_name} | machine={roll.machine} | "
                f"fabric={roll.fabric or '-'}"
            )
            return 0

        if args.command == "list":
            rolls = repo.list_rolls(status=args.status)
            _print_roll_list(rolls)
            return 0

        if args.command == "show":
            roll = _resolve_roll(repo, args.id, args.name)
            summary = repo.get_roll_summary(int(roll.id))
            _print_roll_summary(summary)
            return 0

        if args.command == "add-job":
            roll = _resolve_roll(repo, args.roll_id, args.roll_name)
            item_id = repo.add_job_to_roll(
                roll_id=int(roll.id),
                job_row_id=args.job_row_id,
                job_id=args.job_id,
            )
            print("=" * 70)
            print("JOB ADDED TO ROLL")
            print("=" * 70)
            print(f"roll_id={roll.id} | roll_name={roll.roll_name} | item_id={item_id}")
            return 0

        if args.command == "remove-job":
            roll = _resolve_roll(repo, args.roll_id, args.roll_name)
            removed = repo.remove_job_from_roll(
                roll_id=int(roll.id),
                job_row_id=args.job_row_id,
                job_id=args.job_id,
            )
            print("=" * 70)
            print("JOB REMOVED FROM ROLL")
            print("=" * 70)
            print(f"roll_id={roll.id} | roll_name={roll.roll_name} | removed={removed}")
            return 0

        if args.command == "add-note":
            roll = _resolve_roll(repo, args.id, args.name)
            repo.append_roll_note(
                roll_id=int(roll.id),
                note=args.note,
                operator=args.operator,
            )
            updated = repo.get_roll(roll_id=int(roll.id))
            print("=" * 70)
            print("ROLL NOTE ADDED")
            print("=" * 70)
            print(f"id={updated.id} | name={updated.roll_name}")
            print("Nota atual:")
            print(updated.note or "-")
            return 0

        if args.command == "close":
            roll = _resolve_roll(repo, args.id, args.name)
            repo.close_roll(int(roll.id), note=args.note)
            closed = repo.get_roll(roll_id=int(roll.id))
            print("=" * 70)
            print("ROLL CLOSED")
            print("=" * 70)
            print(
                f"id={closed.id} | name={closed.roll_name} | status={closed.status} | "
                f"closed_at={closed.closed_at.isoformat(timespec='seconds') if closed.closed_at else '-'}"
            )
            return 0

        print("Comando inválido.")
        return 1

    except Exception as exc:
        print("=" * 70)
        print("ROLL OPERATIONS")
        print("=" * 70)
        print(f"Erro: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())