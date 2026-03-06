from __future__ import annotations

from datetime import datetime

from core.exceptions import LogValidationError
from core.models import Machine, ProductionJob


def _parse_datetime(value: str, field_name: str) -> datetime:
    value = (value or "").strip()

    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    raise LogValidationError(f"Data inválida em '{field_name}': {value!r}")


def _parse_float(value: str | None) -> float:
    if value is None:
        return 0.0

    normalized = value.strip().replace(",", ".")
    if not normalized:
        return 0.0

    try:
        return float(normalized)
    except ValueError as exc:
        raise LogValidationError(f"Valor numérico inválido: {value!r}") from exc


def _extract_fabric(document: str) -> str | None:
    """
    Regra inicial simples:
    tenta extrair tecido do padrão 'Pedido - Tecido - ...'
    """
    parts = [part.strip() for part in (document or "").split(" - ")]
    if len(parts) >= 2 and parts[1]:
        return parts[1].upper()
    return None


def _resolve_machine(
    computer_name: str,
    driver: str | None,
    machine_registry: dict[str, Machine] | None,
) -> tuple[str, str]:
    """
    Retorna:
    - machine_name
    - normalized_computer_name
    """
    normalized_computer_name = (computer_name or "").strip()
    if not normalized_computer_name:
        raise LogValidationError("Campo obrigatório ausente: ComputerName")

    if machine_registry and normalized_computer_name in machine_registry:
        machine = machine_registry[normalized_computer_name]
        return machine.name, normalized_computer_name

    fallback_name = (driver or "UNKNOWN_MACHINE").strip()
    return fallback_name, normalized_computer_name


def map_sections_to_job(
    sections: dict[str, dict[str, str]],
    *,
    machine_registry: dict[str, Machine] | None = None,
    source_path: str | None = None,
) -> ProductionJob:
    general = sections.get("General", {})
    item1 = sections.get("1", {})

    job_id = (general.get("JobID") or "").strip()
    if not job_id:
        raise LogValidationError("Campo obrigatório ausente: JobID")

    document = (
        general.get("Document")
        or item1.get("Name")
        or ""
    ).strip()
    if not document:
        raise LogValidationError("Campo obrigatório ausente: Document")

    start_time = _parse_datetime(general.get("StartTime", ""), "StartTime")
    end_time = _parse_datetime(general.get("EndTime", ""), "EndTime")

    duration_seconds = int((end_time - start_time).total_seconds())
    if duration_seconds < 0:
        raise LogValidationError("EndTime anterior a StartTime.")

    computer_name = general.get("ComputerName", "")
    driver = (general.get("Driver") or "").strip() or None
    machine_name, normalized_computer_name = _resolve_machine(
        computer_name=computer_name,
        driver=driver,
        machine_registry=machine_registry,
    )

    height_mm = _parse_float(item1.get("HeightMM"))
    vpos_mm = _parse_float(item1.get("VPosMM") or item1.get("VPositionMM"))

    # Regra crítica:
    # length_m = somente o comprimento real do arquivo
    # gap_before_m = avanço técnico anterior
    length_m = height_mm / 1000.0
    gap_before_m = vpos_mm / 1000.0

    return ProductionJob(
        job_id=job_id,
        machine=machine_name,
        computer_name=normalized_computer_name,
        document=document,
        start_time=start_time,
        end_time=end_time,
        duration_seconds=duration_seconds,
        fabric=_extract_fabric(document),
        length_m=length_m,
        gap_before_m=gap_before_m,
        driver=driver,
        source_path=source_path,
        raw_fields={
            "general": general,
            "item1": item1,
            "height_mm": height_mm,
            "vpos_mm": vpos_mm,
        },
    )