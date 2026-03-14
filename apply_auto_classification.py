import argparse

from analytics.production_metrics import detect_suspect_jobs
from storage.repository import ProductionRepository


def classify_job(job):
    planned = float(job.get("planned_length_m") or 0)
    actual = float(job.get("actual_printed_length_m") or 0)

    if planned <= 0:
        return "INVALID_PLANNED", "Planned length is zero or missing"

    ratio = actual / planned

    if ratio < 0.20:
        return "ABORTED_CANDIDATE", "Very low actual/planned ratio"
    if ratio < 0.95:
        return "PARTIAL_CANDIDATE", "Partial actual/planned ratio"
    return "COMPLETE_CANDIDATE", "Looks complete"


def main():
    parser = argparse.ArgumentParser(
        description="Apply automatic classification to Nexor jobs"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica no banco os candidatos a abortado.",
    )
    args = parser.parse_args()

    repo = ProductionRepository()
    rows = repo.list_all()

    suspects = detect_suspect_jobs(rows, ratio_threshold=0.95)

    if not suspects:
        print("Nenhum job suspeito encontrado.")
        return

    aborted = []
    partial = []

    for job in suspects:
        classification, reason = classify_job(job)

        record = {
            "job_id": job["job_id"],
            "computer_name": job["computer_name"],
            "start_time": job["start_time"],
            "document": job["document"],
            "classification": classification,
            "reason": reason,
        }

        if classification == "ABORTED_CANDIDATE":
            aborted.append(record)
        elif classification == "PARTIAL_CANDIDATE":
            partial.append(record)

    print("=" * 70)
    print("AUTO CLASSIFICATION")
    print("=" * 70)
    print()

    print(f"Abortados candidatos: {len(aborted)}")
    for item in aborted:
        print(
            f"- {item['job_id']} | {item['document']} | "
            f"{item['start_time']} | {item['classification']}"
        )

    print()
    print(f"Parciais candidatos: {len(partial)}")
    for item in partial:
        print(
            f"- {item['job_id']} | {item['document']} | "
            f"{item['start_time']} | {item['classification']}"
        )

    if not args.apply:
        print()
        print("Modo preview. Nada foi alterado no banco.")
        print("Use --apply para marcar apenas os ABORTED_CANDIDATE como FAILED.")
        return

    print()
    print("Aplicando marcação automática nos ABORTED_CANDIDATE...")
    print()

    updated = 0

    for item in aborted:
        count = repo.mark_as_failed(
            job_id=item["job_id"],
            computer_name=item["computer_name"],
            start_time_iso=item["start_time"],
            reason="AUTO_ABORTED_CANDIDATE",
            notes="Marcado automaticamente por baixa relação actual/planned",
        )
        updated += count
        print(f"- {item['job_id']} atualizado: {count}")

    print()
    print(f"Total de registros atualizados: {updated}")


if __name__ == "__main__":
    main()
