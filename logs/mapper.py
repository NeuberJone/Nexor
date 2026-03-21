from __future__ import annotations

import re
from datetime import datetime

from core.exceptions import LogValidationError
from core.models import Machine, ProductionJob
from machines.registry import resolve_machine


def parse_datetime(value: str | None) -> datetime:
    if not value:
        raise LogValidationError("Missing datetime")

    value = str(value).strip()

    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    raise LogValidationError(f"Invalid datetime: {value}")


def parse_float(value: str | None) -> float:
    if value is None:
        return 0.0

    text = str(value).strip()
    if not text:
        return 0.0

    text = text.replace(",", ".")

    try:
        return float(text)
    except ValueError as exc:
        raise LogValidationError(f"Invalid numeric value: {value}") from exc


def normalize_fabric_name(value: str | None) -> str | None:
    if not value:
        return None

    text = str(value).strip().upper()
    text = re.sub(r"\s+", " ", text)

    return text or None


def extract_fabric(document: str) -> str | None:
    parts = document.split(" - ")

    if len(parts) >= 2:
        return normalize_fabric_name(parts[1])

    return None


def safe_section(sections: dict, key: str) -> dict:
    value = sections.get(key, {})
    return value if isinstance(value, dict) else {}


def resolve_document(general: dict, item: dict) -> str:
    document = (general.get("Document") or item.get("Name") or "").strip()
    if not document:
        raise LogValidationError("Missing document")
    return document


def resolve_job_id(general: dict) -> str:
    job_id = str(general.get("JobID") or "").strip()
    if not job_id:
        raise LogValidationError("Missing JobID")
    return job_id


def resolve_computer_name(general: dict) -> str:
    computer_name = str(general.get("ComputerName") or "").strip()
    if not computer_name:
        raise LogValidationError("Missing ComputerName")
    return computer_name


def resolve_machine_with_optional_registry(
    *,
    computer_name: str,
    driver: str | None,
    machine_registry: dict | None = None,
) -> str:
    if machine_registry:
        found = machine_registry.get(computer_name)
        if found is not None:
            if isinstance(found, Machine):
                return found.machine_id
            return str(found).strip() or "UNKNOWN_MACHINE"

    return resolve_machine(computer_name=computer_name, driver=driver)


def map_sections_to_job(
    sections: dict,
    source_path: str | None = None,
    machine_registry: dict | None = None,
) -> ProductionJob:
    general = safe_section(sections, "General")
    item = safe_section(sections, "1")
    costs = safe_section(sections, "Costs")

    job_id = resolve_job_id(general)
    document = resolve_document(general, item)

    start_time = parse_datetime(general.get("StartTime"))
    end_time = parse_datetime(general.get("EndTime"))

    duration = int((end_time - start_time).total_seconds())
    if duration < 0:
        raise LogValidationError("EndTime anterior ao StartTime")

    computer_name = resolve_computer_name(general)
    driver = (str(general.get("Driver") or "").strip() or None)

    machine = resolve_machine_with_optional_registry(
        computer_name=computer_name,
        driver=driver,
        machine_registry=machine_registry,
    )

    height_mm = parse_float(item.get("HeightMM"))
    costs_print_height_mm = parse_float(costs.get("PrintHeightMM"))

    if height_mm <= 0 and costs_print_height_mm > 0:
        height_mm = costs_print_height_mm

    if height_mm <= 0:
        raise LogValidationError("Missing or invalid HeightMM")

    vpos_mm = parse_float(item.get("VPosMM") or item.get("VPositionMM"))
    if vpos_mm < 0:
        vpos_mm = 0.0

    actual_printed_length_m = height_mm / 1000.0
    gap_before_m = vpos_mm / 1000.0

    consumed_height_mm = max(costs_print_height_mm, height_mm + vpos_mm)
    consumed_length_m = consumed_height_mm / 1000.0

    planned_length_m = actual_printed_length_m

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
        actual_printed_length_m=actual_printed_length_m,
        gap_before_m=gap_before_m,
        consumed_length_m=consumed_length_m,
        driver=driver,
        source_path=source_path,
    )