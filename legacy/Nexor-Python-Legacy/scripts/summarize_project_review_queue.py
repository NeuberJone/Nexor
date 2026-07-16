from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mostra um resumo executivo da fila de revisão operacional."
    )
    parser.add_argument(
        "--input",
        default=str(PROJECT_ROOT / "exports" / "project_review_queue.csv"),
        help="CSV gerado por build_project_review_queue.py",
    )
    parser.add_argument(
        "--show-top",
        type=int,
        default=15,
        help="Quantidade máxima de itens prioritários exibidos. Padrão: 15",
    )
    return parser.parse_args()


def safe_text(value, default: str = "-") -> str:
    text = str(value or "").strip()
    return text or default


def safe_int(value, default: int = 999) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default


def load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        print("Status: ERRO")
        print(f"Motivo: arquivo não encontrado: {path}")
        raise SystemExit(1)

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sort_key(row: dict[str, str]) -> tuple[int, str, str, str]:
    return (
        safe_int(row.get("priority")),
        safe_text(row.get("machine")),
        safe_text(row.get("fabric")),
        safe_text(row.get("file_name")),
    )


def print_counter_block(title: str, counter: Counter) -> None:
    print(title)
    if not counter:
        print("  - -")
        print()
        return

    for key, value in counter.most_common():
        print(f"  - {key}: {value}")
    print()


def print_top_items(rows: list[dict[str, str]], limit: int) -> None:
    print("Itens prioritários:")
    if not rows:
        print("  - Nenhum")
        print()
        return

    shown = rows[: max(limit, 1)]
    for row in shown:
        print(
            f"  - P{safe_text(row.get('priority'))} | "
            f"{safe_text(row.get('queue_status'))} | "
            f"job={safe_text(row.get('job_id'))} | "
            f"machine={safe_text(row.get('machine'))} | "
            f"fabric={safe_text(row.get('fabric'))} | "
            f"file={safe_text(row.get('file_name'))}"
        )
        print(
            f"    motivo={safe_text(row.get('review_reason'))} | "
            f"review={safe_text(row.get('review_status'))} | "
            f"print={safe_text(row.get('print_status'))} | "
            f"classification={safe_text(row.get('classification'))}"
        )

    if len(rows) > len(shown):
        print(f"  ... e mais {len(rows) - len(shown)} item(ns).")
    print()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()

    rows = load_rows(input_path)
    rows.sort(key=sort_key)

    print("\nNEXOR PROJECT REVIEW QUEUE SUMMARY\n")
    print(f"Arquivo: {input_path}")
    print(f"Itens na fila: {len(rows)}")
    print()

    status_counter = Counter(safe_text(row.get("queue_status")) for row in rows)
    machine_counter = Counter(safe_text(row.get("machine")) for row in rows)
    fabric_counter = Counter(safe_text(row.get("fabric")) for row in rows)
    reason_counter = Counter(safe_text(row.get("review_reason")) for row in rows)
    priority_counter = Counter(safe_text(row.get("priority")) for row in rows)

    print_counter_block("Por prioridade:", priority_counter)
    print_counter_block("Por status da fila:", status_counter)
    print_counter_block("Por máquina:", machine_counter)
    print_counter_block("Por tecido:", fabric_counter)
    print_counter_block("Principais motivos:", reason_counter)

    print_top_items(rows, args.show_top)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())