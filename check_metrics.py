from analytics.production_metrics import (
    summarize_jobs,
    summarize_by_machine,
    summarize_by_fabric,
    summarize_by_day,
    split_operational_views,
)

from storage.repository import ProductionRepository


# ============================================================
# FORMATADORES
# ============================================================

def fmt_m(value):
    return f"{value:.2f}".replace(".", ",") + " m"


def fmt_pct(value):
    return f"{value:.2f}".replace(".", ",") + "%"


def fmt_speed(value):
    return f"{value:.2f}".replace(".", ",") + " m/min"


def fmt_duration(seconds):

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours == 0 and minutes == 0:
        return f"{secs}s"

    return f"{hours:02d}h{minutes:02d}min"


# ============================================================
# BLOCO DE RESUMO
# ============================================================

def print_summary_block(title, summary):

    print("=" * 60)
    print(title)
    print("=" * 60)

    print(f"Jobs: {summary['total_jobs']}")

    print(f"Tamanho total dos arquivos: {fmt_m(summary['total_planned_length_m'])}")
    print(f"Comprimento impresso: {fmt_m(summary['total_printed_length_m'])}")
    print(f"Espaço técnico: {fmt_m(summary['total_gap_m'])}")
    print(f"Consumo operacional total: {fmt_m(summary['total_consumption_m'])}")

    print()

    print(f"Duração total: {fmt_duration(summary['total_duration_s'])}")
    print(f"Duração média: {fmt_duration(summary['avg_duration_s'])}")
    print(f"Velocidade média: {fmt_speed(summary['avg_speed_m_per_min'])}")

    print()

    print(f"Produção válida: {fmt_m(summary['valid_production_m'])}")

    print()

    print(f"Eficiência mecânica: {fmt_pct(summary['mechanical_efficiency_percent'])}")
    print(f"Eficiência útil: {fmt_pct(summary['useful_efficiency_percent'])}")

    print()

    print(f"Perda operacional: {fmt_m(summary['waste_m'])}")
    print(f"Perda percentual: {fmt_pct(summary['waste_percent'])}")

    print()

    print(f"Jobs com erro: {summary['error_jobs_count']}")
    print(f"Metragem em jobs com erro: {fmt_m(summary['error_printed_m'])}")

    print()


# ============================================================
# MAIN
# ============================================================

def main():

    repo = ProductionRepository()

    rows = repo.list_all()

    if not rows:
        print("Nenhum job encontrado no banco.")
        return

    overall = summarize_jobs(rows)

    views = split_operational_views(rows)

    by_machine = summarize_by_machine(rows)

    by_fabric = summarize_by_fabric(rows)

    by_day = summarize_by_day(rows)

    # ============================================================
    # RESUMO GERAL
    # ============================================================

    print_summary_block("RESUMO GERAL", overall)

    # ============================================================
    # PRODUÇÃO VÁLIDA
    # ============================================================

    print_summary_block("VISÃO: PRODUÇÃO VÁLIDA", views["valid_production"])

    # ============================================================
    # JOBS COM ERRO
    # ============================================================

    print_summary_block("VISÃO: JOBS COM ERRO", views["error_jobs"])

    # ============================================================
    # POR MÁQUINA
    # ============================================================

    print("=" * 60)
    print("POR MÁQUINA")
    print("=" * 60)

    for item in by_machine:

        print(
            f"{item['machine']}: "
            f"jobs={item['total_jobs']} | "
            f"planejado={fmt_m(item['total_planned_length_m'])} | "
            f"impresso={fmt_m(item['total_printed_length_m'])} | "
            f"consumo={fmt_m(item['total_consumption_m'])} | "
            f"eficiência útil={fmt_pct(item['useful_efficiency_percent'])}"
        )

    print()

    # ============================================================
    # POR TECIDO
    # ============================================================

    print("=" * 60)
    print("POR TECIDO")
    print("=" * 60)

    for item in by_fabric:

        print(
            f"{item['fabric']}: "
            f"jobs={item['total_jobs']} | "
            f"planejado={fmt_m(item['total_planned_length_m'])} | "
            f"impresso={fmt_m(item['total_printed_length_m'])} | "
            f"consumo={fmt_m(item['total_consumption_m'])}"
        )

    print()

    # ============================================================
    # POR DIA
    # ============================================================

    print("=" * 60)
    print("POR DIA")
    print("=" * 60)

    for item in by_day:

        print(
            f"{item['day']}: "
            f"jobs={item['total_jobs']} | "
            f"planejado={fmt_m(item['total_planned_length_m'])} | "
            f"impresso={fmt_m(item['total_printed_length_m'])} | "
            f"consumo={fmt_m(item['total_consumption_m'])}"
        )

    print()

    # ============================================================
    # JOBS SUSPEITOS
    # ============================================================

    suspects = views["suspect_jobs"]

    print("=" * 60)
    print("JOBS SUSPEITOS")
    print("=" * 60)

    print(f"Quantidade: {views['suspect_jobs_count']}")
    print()

    for job in suspects:

        reasons = "; ".join(job["suspect_reasons"])

        print(
            f"Job {job['job_id']} | "
            f"Máquina: {job['machine']} | "
            f"Documento: {job['document']}"
        )

        print(
            f"Planejado: {fmt_m(job['planned_length_m'])} | "
            f"Impresso: {fmt_m(job['printed_length_m'])} | "
            f"Velocidade: {fmt_speed(job['speed_m_per_min'])}"
        )

        print(f"Motivos: {reasons}")

        print("-" * 60)


# ============================================================

if __name__ == "__main__":
    main()