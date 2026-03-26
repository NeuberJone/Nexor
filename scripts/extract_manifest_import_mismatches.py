from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extrai os casos divergentes do comparativo entre manifesto e import."
    )
    parser.add_argument(
        "--input",
        default=str(PROJECT_ROOT / "exports" / "manifest_vs_imported_cases.csv"),
        help="CSV gerado por compare_manifest_to_imported_cases.py",
    )
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "exports" / "manifest_import_mismatches.csv"),
        help="CSV de saída com apenas os casos divergentes.",
    )
    parser.add_argument(
        "--result",
        default=None,
        help="Filtra por resultado específico. Ex.: MISMATCH, MISSING_IN_IMPORT",
    )
    parser.add_argument(
        "--contains",
        default=None,
        help="Texto que deve aparecer em file_name, issues, document ou suspicion_reason.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limite máximo de linhas exportadas.",
    )
    return parser.parse_args()


def safe_text(value, default: str = "") -> str:
    text = str(value or "").strip()
    return text if text else default


def safe_upper(value) -> str:
    return safe_text(value).upper()


def load_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        print("Status: ERRO")
        print(f"Motivo: arquivo não encontrado: {path}")
        raise SystemExit(1)

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    return fieldnames, rows


def row_matches(row: dict[str, str], args: argparse.Namespace) -> bool:
    result = safe_upper(row.get("result"))

    if args.result and result != safe_upper(args.result):
        return False

    if not args.result and result == "OK":
        return False

    if args.contains:
        needle = args.contains.strip().lower()
        haystack = " ".join(
            [
                safe_text(row.get("file_name")),
                safe_text(row.get("issues")),
                safe_text(row.get("manifest_document")),
                safe_text(row.get("import_document")),
                safe_text(row.get("import_suspicion_reason")),
                safe_text(row.get("manifest_error_message")),
                safe_text(row.get("import_error_message")),
            ]
        ).lower()
        if needle not in haystack:
            return False

    return True


def sort_key(row: dict[str, str]) -> tuple[int, str, str]:
    result = safe_upper(row.get("result"))

    priority = {
        "MISSING_IN_IMPORT": 0,
        "MISMATCH": 1,
        "OK": 9,
    }.get(result, 5)

    return (
        priority,
        safe_text(row.get("issues")),
        safe_text(row.get("file_name")),
    )


def main() -> int:
    args = parse_args()

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    fieldnames, rows = load_rows(input_path)

    filtered = [row for row in rows if row_matches(row, args)]
    filtered.sort(key=sort_key)

    if args.limit is not None and args.limit > 0:
        filtered = filtered[: args.limit]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filtered)

    print("Status: OK")
    print(f"Entrada: {input_path}")
    print(f"Saída: {output_path}")
    print(f"Linhas exportadas: {len(filtered)}")

    result_counts: dict[str, int] = {}
    for row in filtered:
        key = safe_upper(row.get("result")) or "-"
        result_counts[key] = result_counts.get(key, 0) + 1

    print("Resumo:")
    for key in sorted(result_counts.keys()):
        print(f"- {key}: {result_counts[key]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())