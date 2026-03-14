from analytics.production_metrics import detect_suspect_jobs
from storage.repository import ProductionRepository


def fmt_m(value):
    return f"{value:.2f}".replace(".", ",") + " m"


def fmt_pct(value):
    return f"{value * 100:.2f}".replace(".", ",") + "%"


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
    repo = ProductionRepository()
    rows = repo.list_all()

    suspects = detect_suspect_jobs(rows, ratio_threshold=0.95)

    if not suspects:
        print("Nenhum job classificado como suspeito/parcial.")
        return

    print("=" * 70)
    print("CLASSIFICAÇÃO AUTOMÁTICA DE JOBS")
    print("=" * 70)
    print()

    for job in suspects:
        classification, reason = classify_job(job)

        planned = float(job.get("planned_length_m") or 0)
        consumed = float(job.get("consumed_length_m") or 0)
        gap = float(job.get("gap_before_m") or 0)
        actual = float(job.get("actual_printed_length_m") or 0)
        ratio = (actual / planned) if planned > 0 else 0.0

        print(f"Job ID: {job['job_id']}")
        print(f"Máquina: {job['machine']}")
        print(f"ComputerName: {job['computer_name']}")
        print(f"Documento: {job['document']}")
        print(f"Start: {job['start_time']}")
        print(f"Planejado: {fmt_m(planned)}")
        print(f"Consumido: {fmt_m(consumed)}")
        print(f"Gap: {fmt_m(gap)}")
        print(f"Impresso real: {fmt_m(actual)}")
        print(f"Relação actual/planned: {fmt_pct(ratio)}")
        print(f"Classificação sugerida: {classification}")
        print(f"Motivo: {reason}")
        print("-" * 70)


if __name__ == "__main__":
    main()
