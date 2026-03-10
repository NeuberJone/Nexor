from collections import defaultdict
from statistics import mean


# ============================================================
# UTILITÁRIOS
# ============================================================

def _safe_float(value):
    if value is None:
        return 0.0
    return float(value)


def _safe_int(value):
    if value is None:
        return 0
    return int(value)


def _normalize_row(row):
    return dict(row)


def _job_total_consumption(job):
    return _safe_float(job["printed_length_m"]) + _safe_float(job["gap_before_m"])


def _is_valid(job):
    return int(job["counts_as_valid_production"]) == 1


def _is_error(job):
    return (job["print_status"] or "OK") != "OK"


# ============================================================
# VELOCIDADE
# ============================================================

def compute_job_speed_m_per_min(job):

    printed = _safe_float(job["printed_length_m"])
    duration_s = _safe_int(job["duration_seconds"])

    if duration_s <= 0:
        return 0.0

    minutes = duration_s / 60.0

    if minutes <= 0:
        return 0.0

    return printed / minutes


# ============================================================
# RESUMO GERAL
# ============================================================

def summarize_jobs(rows):

    jobs = [_normalize_row(r) for r in rows]

    total_jobs = len(jobs)

    planned = sum(_safe_float(j["planned_length_m"]) for j in jobs)
    printed = sum(_safe_float(j["printed_length_m"]) for j in jobs)
    gap = sum(_safe_float(j["gap_before_m"]) for j in jobs)

    consumption = printed + gap

    duration = sum(_safe_int(j["duration_seconds"]) for j in jobs)

    avg_duration = int(mean(_safe_int(j["duration_seconds"]) for j in jobs)) if jobs else 0

    speeds = [
        compute_job_speed_m_per_min(j)
        for j in jobs
        if _safe_int(j["duration_seconds"]) > 0
    ]

    avg_speed = mean(speeds) if speeds else 0.0

    # ============================================================
    # PRODUÇÃO VÁLIDA
    # ============================================================

    valid_jobs = [j for j in jobs if _is_valid(j)]

    valid_production = sum(
        _safe_float(j["printed_length_m"]) for j in valid_jobs
    )

    # ============================================================
    # JOBS COM ERRO
    # ============================================================

    error_jobs = [j for j in jobs if _is_error(j)]

    error_printed = sum(
        _safe_float(j["printed_length_m"]) for j in error_jobs
    )

    # ============================================================
    # EFICIÊNCIAS
    # ============================================================

    mechanical_efficiency = 0.0
    useful_efficiency = 0.0

    if consumption > 0:
        mechanical_efficiency = (printed / consumption) * 100
        useful_efficiency = (valid_production / consumption) * 100

    # ============================================================
    # PERDAS
    # ============================================================

    waste_m = consumption - valid_production

    waste_percent = 0.0
    if consumption > 0:
        waste_percent = (waste_m / consumption) * 100

    return {

        "total_jobs": total_jobs,

        "total_planned_length_m": planned,
        "total_printed_length_m": printed,
        "total_gap_m": gap,
        "total_consumption_m": consumption,

        "total_duration_s": duration,
        "avg_duration_s": avg_duration,
        "avg_speed_m_per_min": avg_speed,

        "valid_production_m": valid_production,

        "error_jobs_count": len(error_jobs),
        "error_printed_m": error_printed,

        "mechanical_efficiency_percent": mechanical_efficiency,
        "useful_efficiency_percent": useful_efficiency,

        "waste_m": waste_m,
        "waste_percent": waste_percent,
    }


# ============================================================
# AGRUPAMENTO
# ============================================================

def summarize_by_machine(rows):

    groups = defaultdict(list)

    for row in rows:
        job = _normalize_row(row)
        groups[job["machine"]].append(job)

    result = []

    for machine, jobs in groups.items():

        summary = summarize_jobs(jobs)
        summary["machine"] = machine

        result.append(summary)

    return result


def summarize_by_fabric(rows):

    groups = defaultdict(list)

    for row in rows:
        job = _normalize_row(row)
        groups[job["fabric"]].append(job)

    result = []

    for fabric, jobs in groups.items():

        summary = summarize_jobs(jobs)
        summary["fabric"] = fabric

        result.append(summary)

    return result


def summarize_by_day(rows):

    groups = defaultdict(list)

    for row in rows:

        job = _normalize_row(row)

        day = job["start_time"][:10]

        groups[day].append(job)

    result = []

    for day, jobs in groups.items():

        summary = summarize_jobs(jobs)
        summary["day"] = day

        result.append(summary)

    return result


# ============================================================
# JOBS SUSPEITOS
# ============================================================

def detect_suspect_jobs(rows, ratio_threshold=0.2):

    suspects = []

    for row in rows:

        job = _normalize_row(row)

        planned = _safe_float(job["planned_length_m"])
        printed = _safe_float(job["printed_length_m"])

        if planned <= 0:
            continue

        ratio = printed / planned

        if ratio < ratio_threshold:

            flagged = dict(job)

            flagged["ratio"] = ratio
            flagged["speed_m_per_min"] = compute_job_speed_m_per_min(job)

            flagged["suspect_reasons"] = [
                f"printed/planned abaixo do limite ({ratio:.2%})"
            ]

            suspects.append(flagged)

    return suspects


# ============================================================
# VISÕES OPERACIONAIS
# ============================================================

def split_operational_views(rows):

    jobs = [_normalize_row(r) for r in rows]

    valid_jobs = [j for j in jobs if _is_valid(j)]
    error_jobs = [j for j in jobs if _is_error(j)]

    suspects = detect_suspect_jobs(jobs)

    return {

        "all": summarize_jobs(jobs),

        "valid_production": summarize_jobs(valid_jobs),

        "error_jobs": summarize_jobs(error_jobs),

        "suspect_jobs_count": len(suspects),
        "suspect_jobs": suspects,
    }