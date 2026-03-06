from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True, frozen=True)
class Machine:
    machine_id: str
    name: str
    computer_name: str
    model: str | None = None


@dataclass(slots=True, frozen=True)
class ProductionJob:
    job_id: str
    machine: str
    computer_name: str
    document: str
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    fabric: str | None
    length_m: float
    gap_before_m: float
    driver: str | None = None
    source_path: str | None = None
    raw_fields: dict[str, Any] = field(default_factory=dict)

    @property
    def total_consumption_m(self) -> float:
        """
        Medida operacional opcional:
        comprimento do arquivo + gap técnico anterior.
        Não substitui length_m.
        """
        return self.length_m + self.gap_before_m