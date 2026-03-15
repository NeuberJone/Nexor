from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


REVIEW_PENDING = "PENDING_REVIEW"
REVIEWED_OK = "REVIEWED_OK"
REVIEWED_PARTIAL = "REVIEWED_PARTIAL"
REVIEWED_FAILED = "REVIEWED_FAILED"


@dataclass
class Machine:
    machine_id: str
    name: str
    computer_name: str
    model: str | None = None


@dataclass
class ProductionJob:
    id: int | None
    job_id: str
    machine: str
    computer_name: str
    document: str
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    fabric: str | None
    planned_length_m: float
    actual_printed_length_m: float
    gap_before_m: float
    consumed_length_m: float

    driver: str | None = None
    source_path: str | None = None

    # Classificação operacional
    job_type: str = "PRODUCTION"
    is_rework: bool = False
    notes: str | None = None

    # Status do job
    print_status: str = "OK"
    counts_as_valid_production: bool = True
    counts_for_fabric_summary: bool = True
    counts_for_roll_export: bool = True
    error_reason: str | None = None

    # Campos operacionais opcionais
    operator_code: str | None = None
    operator_name: str | None = None
    replacement_index: int | None = None

    # Suspeita automática
    suspicion_category: str | None = None
    suspicion_reason: str | None = None
    suspicion_ratio: float | None = None
    suspicion_missing_length_m: float | None = None
    suspicion_marked_at: datetime | None = None

    # Revisão humana
    review_status: str | None = None
    review_note: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def printed_length_m(self) -> float:
        return self.actual_printed_length_m

    @property
    def total_consumption_m(self) -> float:
        return self.consumed_length_m


@dataclass
class LogSource:
    id: int | None
    name: str
    path: str
    recursive: bool = True
    enabled: bool = True
    machine_hint: str | None = None


@dataclass
class ImportRun:
    id: int | None
    source_id: int
    started_at: datetime
    finished_at: datetime | None = None
    total_found: int = 0
    imported_count: int = 0
    duplicate_count: int = 0
    error_count: int = 0
    notes: str | None = None
