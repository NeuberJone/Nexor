# app.py
from __future__ import annotations

import argparse

from cli.commands import (
    handle_add_job_to_roll,
    handle_close_roll,
    handle_create_roll,
    handle_export_roll,
    handle_import,
    handle_list_jobs,
    handle_list_rolls,
    handle_remove_job_from_roll,
    handle_show_roll,
)
from storage.database import init_database


UI_START_PAGES = ("home", "operations", "rolls")


def parse_args():
    parser = argparse.ArgumentParser(description="Nexor operational entrypoint")

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--ui",
        action="store_true",
        help="Abre a interface desktop do Nexor.",
    )
    mode_group.add_argument(
        "--force-rescan",
        action="store_true",
        help="Ignora o checkpoint das fontes e relê todos os logs.",
    )
    mode_group.add_argument(
        "--export-roll-id",
        type=int,
        help="Exporta um rolo fechado pelo ID.",
    )
    mode_group.add_argument(
        "--list-rolls",
        action="store_true",
        help="Lista os rolos cadastrados no banco.",
    )
    mode_group.add_argument(
        "--show-roll-id",
        type=int,
        help="Mostra o detalhe completo de um rolo pelo ID.",
    )
    mode_group.add_argument(
        "--list-jobs",
        action="store_true",
        help="Lista jobs disponíveis para montagem de rolo.",
    )
    mode_group.add_argument(
        "--create-roll",
        action="store_true",
        help="Cria um novo rolo em aberto.",
    )
    mode_group.add_argument(
        "--add-job-to-roll",
        action="store_true",
        help="Adiciona um job disponível a um rolo em aberto.",
    )
    mode_group.add_argument(
        "--remove-job-from-roll",
        action="store_true",
        help="Remove um job de um rolo em aberto.",
    )
    mode_group.add_argument(
        "--close-roll-id",
        type=int,
        help="Fecha um rolo pelo ID.",
    )

    parser.add_argument(
        "--page",
        choices=UI_START_PAGES,
        default="home",
        help="Página inicial da interface quando usado com --ui.",
    )

    parser.add_argument(
        "--export-output-dir",
        default="exports/out",
        help="Diretório de saída da exportação do rolo.",
    )

    parser.add_argument(
        "--roll-status",
        default="ALL",
        help="Filtro de status ao listar rolos. Ex.: ALL, OPEN, CLOSED, EXPORTED.",
    )

    parser.add_argument(
        "--machine",
        help="Filtro de máquina para listar jobs disponíveis.",
    )
    parser.add_argument(
        "--fabric",
        help="Filtro de tecido para listar jobs disponíveis.",
    )
    parser.add_argument(
        "--review-status",
        default=None,
        help="Filtro de review status para listar jobs. Ex.: PENDING_REVIEW, REVIEWED_OK.",
    )
    parser.add_argument(
        "--exclude-suspicious",
        action="store_true",
        help="Exclui jobs suspeitos da listagem de jobs disponíveis.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limite de resultados na listagem de jobs disponíveis.",
    )

    parser.add_argument(
        "--roll-machine",
        help="Máquina do rolo a ser criado. Ex.: M1, M2.",
    )
    parser.add_argument(
        "--roll-fabric",
        default=None,
        help="Tecido do rolo a ser criado.",
    )
    parser.add_argument(
        "--roll-note",
        default=None,
        help="Observação inicial do rolo a ser criado.",
    )
    parser.add_argument(
        "--roll-name",
        default=None,
        help="Nome manual do rolo. Se omitido, o Nexor gera automaticamente.",
    )

    parser.add_argument(
        "--target-roll-id",
        type=int,
        default=None,
        help="ID do rolo alvo para adicionar/remover job.",
    )
    parser.add_argument(
        "--job-row-id",
        type=int,
        default=None,
        help="ID interno do job (row id) para adicionar/remover do rolo.",
    )

    parser.add_argument(
        "--close-note",
        default=None,
        help="Observação adicional ao fechar o rolo.",
    )

    return parser.parse_args()


def run_ui(start_page: str = "home") -> int:
    from ui.app import main as ui_main

    argv: list[str] = []
    if start_page and start_page != "home":
        argv.extend(["--page", start_page])

    return int(ui_main(argv))


def main() -> int:
    args = parse_args()

    if args.ui:
        return run_ui(start_page=args.page)

    init_database()

    if args.export_roll_id is not None:
        return handle_export_roll(
            roll_id=args.export_roll_id,
            output_dir=args.export_output_dir,
        )

    if args.list_rolls:
        return handle_list_rolls(status=args.roll_status)

    if args.show_roll_id is not None:
        return handle_show_roll(roll_id=args.show_roll_id)

    if args.list_jobs:
        return handle_list_jobs(
            machine=args.machine,
            fabric=args.fabric,
            review_status=args.review_status,
            include_suspicious=not args.exclude_suspicious,
            limit=args.limit,
        )

    if args.create_roll:
        if not args.roll_machine:
            print("Status: ERRO")
            print("Motivo: --roll-machine é obrigatório para --create-roll")
            return 1

        return handle_create_roll(
            machine=args.roll_machine,
            fabric=args.roll_fabric,
            note=args.roll_note,
            roll_name=args.roll_name,
        )

    if args.add_job_to_roll:
        if args.target_roll_id is None:
            print("Status: ERRO")
            print("Motivo: --target-roll-id é obrigatório para --add-job-to-roll")
            return 1

        if args.job_row_id is None:
            print("Status: ERRO")
            print("Motivo: --job-row-id é obrigatório para --add-job-to-roll")
            return 1

        return handle_add_job_to_roll(
            roll_id=args.target_roll_id,
            job_row_id=args.job_row_id,
        )

    if args.remove_job_from_roll:
        if args.target_roll_id is None:
            print("Status: ERRO")
            print("Motivo: --target-roll-id é obrigatório para --remove-job-from-roll")
            return 1

        if args.job_row_id is None:
            print("Status: ERRO")
            print("Motivo: --job-row-id é obrigatório para --remove-job-from-roll")
            return 1

        return handle_remove_job_from_roll(
            roll_id=args.target_roll_id,
            job_row_id=args.job_row_id,
        )

    if args.close_roll_id is not None:
        return handle_close_roll(
            roll_id=args.close_roll_id,
            note=args.close_note,
        )

    return handle_import(force_rescan=args.force_rescan)


if __name__ == "__main__":
    raise SystemExit(main())