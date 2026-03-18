from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


REVIEW_PENDING = "PENDING_REVIEW"
REVIEWED_OK = "REVIEWED_OK"
REVIEWED_PARTIAL = "REVIEWED_PARTIAL"
REVIEWED_FAILED = "REVIEWED_FAILED"

ROLL_OPEN = "OPEN"
ROLL_CLOSED = "CLOSED"


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

    job_type: str = "PRODUCTION"
    is_rework: bool = False
    notes: str | None = None

    print_status: str = "OK"
    counts_as_valid_production: bool = True
    counts_for_fabric_summary: bool = True
    counts_for_roll_export: bool = True
    error_reason: str | None = None

    operator_code: str | None = None
    operator_name: str | None = None
    replacement_index: int | None = None

    suspicion_category: str | None = None
    suspicion_reason: str | None = None
    suspicion_ratio: float | None = None
    suspicion_missing_length_m: float | None = None
    suspicion_marked_at: datetime | None = None

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
class Roll:
    id: int | None
    roll_name: str
    machine: str
    fabric: str | None
    status: str = ROLL_OPEN
    note: str | None = None
    created_at: datetime | None = None
    closed_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class RollItem:
    id: int | None
    roll_id: int
    job_row_id: int
    job_id: str
    document: str
    machine: str
    fabric: str | None
    sort_order: int
    planned_length_m: float
    effective_printed_length_m: float
    consumed_length_m: float
    gap_before_m: float
    metric_category: str | None = None
    review_status: str | None = None
    snapshot_print_status: str | None = None
    created_at: datetime | None = None


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