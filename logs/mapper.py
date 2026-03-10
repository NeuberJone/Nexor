from datetime import datetime

from core.models import ProductionJob
from core.exceptions import LogValidationError
from machines.registry import resolve_machine


def parse_datetime(value: str):

    if not value:
        raise LogValidationError("Missing datetime")

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

    try:
        return float(value)
    except ValueError:
        raise LogValidationError(f"Invalid numeric value: {value}")


def extract_fabric(document: str):

    parts = document.split(" - ")

    if len(parts) >= 2:
        return parts[1].upper()

    return None


def map_sections_to_job(
    sections: dict,
    source_path: str | None = None
) -> ProductionJob:

    general = sections.get("General", {})
    item = sections.get("1", {})
    costs = sections.get("Costs", {})

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

    computer_name = (general.get("ComputerName") or "").strip()

    if not computer_name:
        raise LogValidationError("Missing ComputerName")

    driver = (general.get("Driver") or "").strip() or None

    machine = resolve_machine(
        computer_name=computer_name,
        driver=driver
    )

    # tamanho original do arquivo enviado
    planned_height_mm = parse_float(item.get("HeightMM"))

    # metragem realmente impressa
    printed_height_mm = parse_float(costs.get("PrintHeightMM"))

    # fallback caso alguns logs não tenham [Costs]
    if printed_height_mm == 0 and planned_height_mm > 0:
        printed_height_mm = planned_height_mm

    vpos_mm = parse_float(item.get("VPosMM") or item.get("VPositionMM"))

    planned_length_m = planned_height_mm / 1000
    printed_length_m = printed_height_mm / 1000
    gap_before_m = vpos_mm / 1000

    return ProductionJob(
        job_id=job_id,
        machine=machine,
        computer_name=computer_name,
        document=document,
        start_time=start_time,
        end_time=end_time,
        duration_seconds=duration,
        fabric=extract_fabric(document),
        planned_length_m=planned_length_m,
        printed_length_m=printed_length_m,
        gap_before_m=gap_before_m,
        driver=driver,
        source_path=source_path,
    )