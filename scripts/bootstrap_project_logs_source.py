from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from storage.database import init_database
from storage.log_sources_repository import LogSourceRepository


DEFAULT_SOURCE_NAME = "PROJECT_LOGS_IMPORT"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap do source local logs_import para testes reais do Nexor."
    )
    parser.add_argument(
        "--source-name",
        default=DEFAULT_SOURCE_NAME,
        help=f"Nome do source no banco. Padrão: {DEFAULT_SOURCE_NAME}",
    )
    parser.add_argument(
        "--path",
        default=str(PROJECT_ROOT / "logs_import"),
        help="Caminho da pasta de logs a registrar. Padrão: <project>/logs_import",
    )
    parser.add_argument(
        "--disable-others",
        action="store_true",
        help="Desabilita todos os outros sources para isolar o teste nesta pasta.",
    )
    parser.add_argument(
        "--reset-checkpoint",
        action="store_true",
        help="Reseta o checkpoint do source após registrar, para permitir releitura completa.",
    )
    parser.add_argument(
        "--non-recursive",
        action="store_true",
        help="Registra o source como não recursivo.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    target_path = Path(args.path).resolve()
    recursive = not args.non_recursive

    if not target_path.exists():
        print("Status: ERRO")
        print(f"Motivo: pasta não encontrada: {target_path}")
        return 1

    if not target_path.is_dir():
        print("Status: ERRO")
        print(f"Motivo: o caminho informado não é uma pasta: {target_path}")
        return 1

    init_database()
    repo = LogSourceRepository()

    source_id = repo.upsert(
        name=args.source_name,
        path=str(target_path),
        recursive=recursive,
        machine_hint=None,
        enabled=True,
    )

    if args.disable_others:
        for row in repo.list_all():
            row_id = int(row["id"])
            if row_id != source_id and int(row["enabled"] or 0) == 1:
                repo.disable(row_id)

    if args.reset_checkpoint:
        repo.reset_checkpoint(source_id)

    source = repo.get_by_id(source_id)
    all_sources = repo.list_all()
    enabled_sources = repo.list_enabled()

    print("Status: OK")
    print(f"Source ID: {source_id}")
    print(f"Nome: {source['name']}")
    print(f"Caminho: {source['path']}")
    print(f"Recursivo: {'SIM' if int(source['recursive'] or 0) == 1 else 'NÃO'}")
    print(f"Habilitado: {'SIM' if int(source['enabled'] or 0) == 1 else 'NÃO'}")
    print()

    print("Resumo dos sources:")
    print(f"- Total cadastrados: {len(all_sources)}")
    print(f"- Total habilitados: {len(enabled_sources)}")

    if args.disable_others:
        print("- Modo isolado: apenas este source deve permanecer habilitado.")
    else:
        print("- Atenção: outros sources habilitados também serão lidos no import.")

    if args.reset_checkpoint:
        print("- Checkpoint resetado: o próximo import poderá reler todos os logs desta pasta.")

    print()
    print("Próximos comandos sugeridos:")
    print("1) Rodar import completo:")
    print("   python app.py --force-rescan")
    print()
    print("2) Conferir jobs disponíveis depois do import:")
    print("   python app.py --list-jobs")
    print()
    print("3) Conferir rolos existentes, se necessário:")
    print("   python app.py --list-rolls")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())