from datetime import datetime
from machines.registry import resolve_machine

from core.exceptions import LogValidationError
from core.models import ProductionJob


def parse_datetime(value: str):
    if not value:
        raise LogValidationError("Missing datetime value")

    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    raise LogValidationError(f"Invalid datetime: {value}")


def parse_float(value: str | None):
    if not value:
        return 0.0

    value = value.strip().replace(",", ".")

    try:
        return float(value)
    except ValueError as exc:
        raise LogValidationError(f"Invalid numeric value: {value}") from exc

def extract_fabric(document: str):
    parts = document.split(" - ")

    if len(parts) >= 2:
        fabric = parts[1].strip().upper()
        return fabric or None

    return None


def map_sections_to_job(sections: dict, source_path: str | None = None) -> ProductionJob:
    general = sections.get("General", {})
    item = sections.get("1", {})

    job_id = (general.get("JobID") or "").strip()
    if not job_id:
        raise LogValidationError("Missing JobID")

    document = (general.get("Document") or item.get("Name") or "").strip()
    if not document:
        raise LogValidationError("Missing document")

    start_time = parse_datetime(general.get("StartTime"))
    end_time = parse_datetime(general.get("EndTime"))

    duration = int((end_time - start_time).total_seconds())
    if duration < 0:
        raise LogValidationError("EndTime before StartTime")

    computer_name = (general.get("ComputerName") or "").strip()
    if not computer_name:
        raise LogValidationError("Missing ComputerName")

    driver = (general.get("Driver") or "").strip() or None
    machine = resolve_machine(
        computer_name=computer_name,
        driver=driver,
    )

    height_mm = parse_float(item.get("HeightMM"))

    vpos_value = (
        item.get("VPosMM")
        or item.get("VPositionMM")
    )

    vpos_mm = parse_float(vpos_value)

    length_m = height_mm / 1000.0
    gap_before_m = vpos_mm / 1000.0

    return ProductionJob(
        job_id=job_id,
        machine=machine,
        computer_name=computer_name,
        document=document,
        start_time=start_time,
        end_time=end_time,
        duration_seconds=duration,
        fabric=extract_fabric(document),
        length_m=length_m,
        gap_before_m=gap_before_m,
        driver=driver,
        source_path=source_path,
    )