from datetime import datetime
from core.models import ProductionJob
from core.exceptions import LogValidationError


def parse_datetime(value: str):

    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    raise LogValidationError(f"Invalid datetime: {value}")


def parse_float(value: str | None):

    if not value:
        return 0.0

    value = value.replace(",", ".")

    return float(value)


def extract_fabric(document: str):

    parts = document.split(" - ")

    if len(parts) >= 2:
        return parts[1].upper()

    return None


def map_sections_to_job(sections: dict) -> ProductionJob:

    general = sections.get("General", {})
    item = sections.get("1", {})

    job_id = general.get("JobID")

    if not job_id:
        raise LogValidationError("Missing JobID")

    document = general.get("Document") or item.get("Name")

    if not document:
        raise LogValidationError("Missing document")

    start_time = parse_datetime(general.get("StartTime"))
    end_time = parse_datetime(general.get("EndTime"))

    duration = int((end_time - start_time).total_seconds())

    if duration < 0:
        raise LogValidationError("EndTime before StartTime")

    computer_name = general.get("ComputerName")

    height_mm = parse_float(item.get("HeightMM"))
    vpos_mm = parse_float(item.get("VPosMM") or item.get("VPositionMM"))

    length_m = height_mm / 1000
    gap_before_m = vpos_mm / 1000

    return ProductionJob(
        job_id=job_id,
        machine=general.get("Driver"),
        computer_name=computer_name,
        document=document,
        start_time=start_time,
        end_time=end_time,
        duration_seconds=duration,
        fabric=extract_fabric(document),
        length_m=length_m,
        gap_before_m=gap_before_m,
        driver=general.get("Driver"),
    )