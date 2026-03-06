from __future__ import annotations

from pathlib import Path

from core.models import Machine, ProductionJob
from logs.mapper import map_sections_to_job
from logs.parser import parse_log_file


def import_job_from_log(
    path: str | Path,
    *,
    machine_registry: dict[str, Machine] | None = None,
) -> ProductionJob:
    sections = parse_log_file(path)
    return map_sections_to_job(
        sections,
        machine_registry=machine_registry,
        source_path=str(path),
    )