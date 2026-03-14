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


def _actual_printed(job):
    consumed = _safe_float(job.get("consumed_length_m"))
    gap = _safe_float(job.get("gap_before_m"))
    value = consumed - gap
    return value if value > 0 else 0.0


def _consumption(job):
    return _safe_float(job.get("consumed_length_m"))


def _is_valid(job):
    return int(job.get("counts_as_valid_production", 0)) == 1


def _is_error(job):
    return (job.get("print_status") or "OK") != "OK"


# ============================================================
# VELOCIDADE
# ============================================================

def compute_job_speed_m_per_min(job):
    actual_printed = _actual_printed(job)
    duration_s = _safe_int(job.get("duration_seconds"))

    if duration_s <= 0:
        return 0.0

    minutes = duration_s / 60.0
    if minutes <= 0:
        return 0.0

    return actual_printed / minutes


# ============================================================
# RESUMO GERAL
# ============================================================

def summarize_jobs(rows):
    jobs = [_normalize_row(r) for r in rows]

    total_jobs = len(jobs)

    planned = sum(_safe_float(j.get("planned_length_m")) for j in jobs)
    consumed = sum(_safe_float(j.get("consumed_length_m")) for j in jobs)
    gap = sum(_safe_float(j.get("gap_before_m")) for j in jobs)
    actual_printed = sum(_actual_printed(j) for j in jobs)

    duration = sum(_safe_int(j.get("duration_seconds")) for j in jobs)
    avg_duration = int(mean(_safe_int(j.get("duration_seconds")) for j in jobs)) if jobs else 0

    speeds = [
        compute_job_speed_m_per_min(j)
        for j in jobs
        if _safe_int(j.get("duration_seconds")) > 0
    ]
    avg_speed = mean(speeds) if speeds else 0.0

    valid_jobs = [j for j in jobs if _is_valid(j)]
    valid_production = sum(_actual_printed(j) for j in valid_jobs)

    error_jobs = [j for j in jobs if _is_error(j)]
    error_actual_printed = sum(_actual_printed(j) for j in error_jobs)
    error_consumed = sum(_consumption(j) for j in error_jobs)

    mechanical_efficiency = 0.0
    useful_efficiency = 0.0

    if consumed > 0:
        mechanical_efficiency = (actual_printed / consumed) * 100
        useful_efficiency = (valid_production / consumed) * 100

    waste_m = consumed - valid_production
    waste_percent = 0.0
    if consumed > 0:
        waste_percent = (waste_m / consumed) * 100

    return {
        "total_jobs": total_jobs,
        "total_planned_length_m": planned,
        "total_consumed_length_m": consumed,
        "total_gap_m": gap,
        "total_actual_printed_m": actual_printed,
        "total_consumption_m": consumed,
        "total_duration_s": duration,
        "avg_duration_s": avg_duration,
        "avg_speed_m_per_min": avg_speed,
        "valid_production_m": valid_production,
        "error_jobs_count": len(error_jobs),
        "error_actual_printed_m": error_actual_printed,
        "error_consumed_m": error_consumed,
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
        groups[job.get("machine") or "UNKNOWN_MACHINE"].append(job)

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
        groups[job.get("fabric") or "UNKNOWN_FABRIC"].append(job)

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
        start_time = job.get("start_time") or ""
        day = start_time[:10] if len(start_time) >= 10 else "UNKNOWN_DAY"
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

        planned = _safe_float(job.get("planned_length_m"))
        actual = _actual_printed(job)

        if planned <= 0:
            continue

        ratio = actual / planned

        if ratio < ratio_threshold:
            flagged = dict(job)
            flagged["ratio"] = ratio
            flagged["speed_m_per_min"] = compute_job_speed_m_per_min(job)
            flagged["actual_printed_length_m"] = actual
            flagged["suspect_reasons"] = [
                f"actual/planned abaixo do limite ({ratio:.2%})"
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