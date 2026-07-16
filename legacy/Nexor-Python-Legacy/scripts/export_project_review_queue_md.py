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
        description="Exporta a fila de revisão operacional para um relatório Markdown."
    )
    parser.add_argument(
        "--input",
        default=str(PROJECT_ROOT / "exports" / "project_review_queue.csv"),
        help="CSV gerado por build_project_review_queue.py",
    )
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "exports" / "project_review_queue.md"),
        help="Arquivo Markdown de saída.",
    )
    parser.add_argument(
        "--show-top",
        type=int,
        default=20,
        help="Quantidade de itens prioritários no relatório. Padrão: 20",
    )
    parser.add_argument(
        "--show-table",
        type=int,
        default=30,
        help="Quantidade de linhas na tabela principal. Padrão: 30",
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


def md_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def build_counter(rows: list[dict[str, str]], field_name: str) -> Counter:
    return Counter(safe_text(row.get(field_name)) for row in rows)


def render_counter_section(title: str, counter: Counter) -> list[str]:
    lines = [f"## {title}", ""]
    if not counter:
        lines.append("- -")
        lines.append("")
        return lines

    for key, value in counter.most_common():
        lines.append(f"- **{md_escape(key)}**: {value}")
    lines.append("")
    return lines


def render_top_items(rows: list[dict[str, str]], limit: int) -> list[str]:
    lines = ["## Itens prioritários", ""]
    if not rows:
        lines.append("- Nenhum")
        lines.append("")
        return lines

    shown = rows[: max(limit, 1)]
    for row in shown:
        priority = md_escape(safe_text(row.get("priority")))
        queue_status = md_escape(safe_text(row.get("queue_status")))
        job_id = md_escape(safe_text(row.get("job_id")))
        machine = md_escape(safe_text(row.get("machine")))
        fabric = md_escape(safe_text(row.get("fabric")))
        file_name = md_escape(safe_text(row.get("file_name")))
        review_reason = md_escape(safe_text(row.get("review_reason")))

        line = (
            f"- **P{priority} · {queue_status}** "
            f"· job `{job_id}`\n"
            f"  · máquina `{machine}`\n"
            f"  · tecido `{fabric}`\n"
            f"  · arquivo `{file_name}`\n"
            f"  · motivo: {review_reason}"
        )
        lines.append(line)
        lines.append("")

    return lines


def render_table(rows: list[dict[str, str]], limit: int) -> list[str]:
    lines = ["## Tabela dos primeiros casos", ""]
    if not rows:
        lines.append("Sem itens na fila.")
        lines.append("")
        return lines

    shown = rows[: max(limit, 1)]

    header = "| Prioridade | Status | Job | Máquina | Tecido | Classification | Arquivo |"
    sep = "|---|---|---|---|---|---|---|"

    lines.append(header)
    lines.append(sep)

    for row in shown:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(safe_text(row.get("priority"))),
                    md_escape(safe_text(row.get("queue_status"))),
                    md_escape(safe_text(row.get("job_id"))),
                    md_escape(safe_text(row.get("machine"))),
                    md_escape(safe_text(row.get("fabric"))),
                    md_escape(safe_text(row.get("classification"))),
                    md_escape(safe_text(row.get("file_name"))),
                ]
            )
            + " |"
        )

    lines.append("")
    return lines


def render_footer(total_rows: int, shown_top: int, shown_table: int) -> list[str]:
    return [
        "## Observações",
        "",
        f"- Total de itens na fila: **{total_rows}**",
        f"- Itens exibidos na seção prioritária: **{shown_top}**",
        f"- Itens exibidos na tabela: **{shown_table}**",
        "",
    ]


def main() -> int:
    args = parse_args()

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    rows = load_rows(input_path)
    rows.sort(key=sort_key)

    priority_counter = build_counter(rows, "priority")
    status_counter = build_counter(rows, "queue_status")
    machine_counter = build_counter(rows, "machine")
    fabric_counter = build_counter(rows, "fabric")
    reason_counter = build_counter(rows, "review_reason")

    lines: list[str] = [
        "# Nexor · Project Review Queue",
        "",
        f"Arquivo de origem: `{input_path}`",
        "",
        f"Total de itens na fila: **{len(rows)}**",
        "",
    ]

    lines.extend(render_counter_section("Por prioridade", priority_counter))
    lines.extend(render_counter_section("Por status da fila", status_counter))
    lines.extend(render_counter_section("Por máquina", machine_counter))
    lines.extend(render_counter_section("Por tecido", fabric_counter))
    lines.extend(render_counter_section("Principais motivos", reason_counter))
    lines.extend(render_top_items(rows, args.show_top))
    lines.extend(render_table(rows, args.show_table))
    lines.extend(
        render_footer(
            total_rows=len(rows),
            shown_top=min(len(rows), max(args.show_top, 1)),
            shown_table=min(len(rows), max(args.show_table, 1)),
        )
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")

    print("Status: OK")
    print(f"Entrada: {input_path}")
    print(f"Markdown: {output_path}")
    print(f"Itens na fila: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())