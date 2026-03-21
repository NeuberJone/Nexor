from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from storage.database import init_database
from storage.repository import ProductionRepository


def format_m(value: float) -> str:
    return f"{float(value or 0.0):.3f}"


def main() -> int:
    db_path = init_database()
    repo = ProductionRepository(db_path=db_path)

    rolls = repo.list_rolls(status="ALL")

    print("\nNEXOR ROLLS\n")
    print(f"Database: {db_path}\n")

    if not rolls:
        print("Nenhum rolo encontrado.")
        return 0

    for roll in rolls:
        summary = repo.get_roll_summary(roll.id)

        print("=" * 72)
        print(f"ID: {roll.id}")
        print(f"Roll: {roll.roll_name}")
        print(f"Machine: {roll.machine}")
        print(f"Fabric: {roll.fabric or '-'}")
        print(f"Status: {roll.status}")
        print(f"Created: {roll.created_at or '-'}")
        print(f"Closed: {roll.closed_at or '-'}")
        print(f"Exported: {roll.exported_at or '-'}")
        print(f"Jobs: {summary['jobs_count']}")
        print(f"Total planned (m): {format_m(summary['total_planned_m'])}")
        print(f"Total effective (m): {format_m(summary['total_effective_m'])}")
        print(f"Total gap (m): {format_m(summary['total_gap_m'])}")
        print(f"Total consumed (m): {format_m(summary['total_consumed_m'])}")

        items = summary["items"]
        if items:
            print("\nItems:")
            for item in items:
                print(
                    f"  - {item.job_id} | {item.document} | "
                    f"eff={format_m(item.effective_printed_length_m)}m | "
                    f"gap={format_m(item.gap_before_m)}m | "
                    f"cons={format_m(item.consumed_length_m)}m"
                )
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())