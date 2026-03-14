import re

from storage.database import get_connection


def normalize_fabric_name(value: str | None):
    if not value:
        return None

    value = value.strip().upper()
    value = re.sub(r"\s+", " ", value)

    return value or None


def main():
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT id, fabric
        FROM production_jobs
        WHERE fabric IS NOT NULL
        """
    ).fetchall()

    updated = 0
    changes = {}

    for row in rows:
        row_id = row["id"]
        old_value = row["fabric"]
        new_value = normalize_fabric_name(old_value)

        if new_value != old_value:
            conn.execute(
                """
                UPDATE production_jobs
                SET fabric = ?
                WHERE id = ?
                """,
                (new_value, row_id),
            )

            updated += 1
            changes.setdefault((old_value, new_value), 0)
            changes[(old_value, new_value)] += 1

    conn.commit()
    conn.close()

    print(f"Registros atualizados: {updated}")

    if changes:
        print("\nAlterações feitas:")
        for (old, new), count in sorted(changes.items()):
            print(f"{old!r} -> {new!r} | {count} registro(s)")
    else:
        print("Nenhuma alteração necessária.")


if __name__ == "__main__":
    main()
