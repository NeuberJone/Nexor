from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

# ---------------------------------------------------------------------------
# Review status constants
# ---------------------------------------------------------------------------
REVIEW_PENDING = "PENDING_REVIEW"
REVIEWED_OK = "REVIEWED_OK"
REVIEWED_PARTIAL = "REVIEWED_PARTIAL"
REVIEWED_FAILED = "REVIEWED_FAILED"

# ---------------------------------------------------------------------------
# Log status constants
# ---------------------------------------------------------------------------
LOG_NEW = "NEW"
LOG_PARSED = "PARSED"
LOG_INVALID = "INVALID"
LOG_DUPLICATED = "DUPLICATED"
LOG_IGNORED = "IGNORED"
LOG_CONVERTED = "CONVERTED"

# ---------------------------------------------------------------------------
# Roll status constants
# ---------------------------------------------------------------------------
ROLL_OPEN = "OPEN"
ROLL_DRAFT = ROLL_OPEN
ROLL_CLOSED = "CLOSED"
ROLL_EXPORTED = "EXPORTED"
ROLL_REVIEWED = "REVIEWED"
ROLL_REOPENED = "REOPENED"

# ---------------------------------------------------------------------------
# Job workflow / review constants
# ---------------------------------------------------------------------------
JOB_PENDING_REVIEW = "PENDING_REVIEW"
JOB_READY = "READY"
JOB_SUSPICIOUS = "SUSPICIOUS"
JOB_ASSIGNED_TO_ROLL = "ASSIGNED_TO_ROLL"
JOB_IGNORED = "IGNORED"
JOB_CORRECTED = "CORRECTED"


@dataclass(slots=True)
class Machine:
    machine_id: str
    name: str
    computer_name: str
    model: str | None = None


@dataclass(slots=True)
class Log:
    """
    Raw imported production record.
    """

    id: int | None = None
    source_path: str | None = None
    source_name: str | None = None
    fingerprint: str | None = None
    machine_code_raw: str | None = None
    captured_at: datetime | None = None
    raw_payload: str | None = None
    status: str = LOG_NEW
    parse_error: str | None = None
    imported_at: datetime | None = None
    job_id: int | None = None

    @property
    def is_actionable(self) -> bool:
        return self.status in {LOG_NEW, LOG_PARSED}

    @property
    def is_terminal(self) -> bool:
        return self.status in {LOG_INVALID, LOG_DUPLICATED, LOG_IGNORED, LOG_CONVERTED}


@dataclass(slots=True)
class Job:
    """
    Normalized operational event derived from a parsed log.
    """

    id: int | None = None
    log_id: int | None = None
    job_id: str = ""
    machine: str = ""
    computer_name: str = ""
    document: str = ""
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration_seconds: int = 0
    fabric: str | None = None
    planned_length_m: float = 0.0
    actual_printed_length_m: float = 0.0
    gap_before_m: float = 0.0
    consumed_length_m: float = 0.0
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
    classification: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.duration_seconds = int(self.duration_seconds or 0)
        self.planned_length_m = float(self.planned_length_m or 0.0)
        self.actual_printed_length_m = float(self.actual_printed_length_m or 0.0)
        self.gap_before_m = float(self.gap_before_m or 0.0)
        self.consumed_length_m = float(self.consumed_length_m or 0.0)

        # Compatibility fix for older mappers:
        # if actual_printed_length_m is not explicitly provided, infer it.
        if self.actual_printed_length_m <= 0:
            if self.planned_length_m > 0:
                self.actual_printed_length_m = self.planned_length_m
            elif self.consumed_length_m > 0:
                inferred = self.consumed_length_m - self.gap_before_m
                self.actual_printed_length_m = max(inferred, 0.0)

        # Keep total consumption coherent.
        if self.consumed_length_m <= 0:
            self.consumed_length_m = self.actual_printed_length_m + self.gap_before_m

        # Normalize negative artifacts.
        if self.actual_printed_length_m < 0:
            self.actual_printed_length_m = 0.0
        if self.gap_before_m < 0:
            self.gap_before_m = 0.0
        if self.consumed_length_m < 0:
            self.consumed_length_m = 0.0

        if self.review_status is None:
            self.review_status = REVIEW_PENDING

    @property
    def printed_length_m(self) -> float:
        return self.actual_printed_length_m

    @property
    def total_consumption_m(self) -> float:
        return self.consumed_length_m

    @property
    def length_m(self) -> float:
        # Compatibility with older tests/flows.
        return self.actual_printed_length_m

    @property
    def is_suspicious(self) -> bool:
        return bool(self.suspicion_category or self.suspicion_reason)

    @property
    def is_reviewed(self) -> bool:
        return self.review_status in {REVIEWED_OK, REVIEWED_PARTIAL, REVIEWED_FAILED}

    @property
    def workflow_status(self) -> str:
        if self.print_status == "IGNORED":
            return JOB_IGNORED
        if self.roll_id is not None:
            return JOB_ASSIGNED_TO_ROLL
        if self.is_suspicious:
            return JOB_SUSPICIOUS
        if self.review_status in {REVIEWED_OK, REVIEWED_PARTIAL, REVIEWED_FAILED}:
            return JOB_CORRECTED if self.review_note else JOB_READY
        return JOB_PENDING_REVIEW

    @property
    def roll_id(self) -> int | None:
        """
        Compatibility placeholder.

        The current persisted relationship between jobs and rolls is stored via
        roll_items, not directly on the job row.
        """
        return None


# Transitional compatibility alias
ProductionJob = Job


@dataclass(slots=True)
class Roll:
    id: int | None = None
    roll_name: str = ""
    machine: str = ""
    fabric: str | None = None
    status: str = ROLL_OPEN
    note: str | None = None
    created_at: datetime | None = None
    closed_at: datetime | None = None
    updated_at: datetime | None = None
    exported_at: datetime | None = None
    reviewed_at: datetime | None = None
    reopened_at: datetime | None = None

    @property
    def roll_code(self) -> str:
        return self.roll_name

    @property
    def is_open(self) -> bool:
        return self.status == ROLL_OPEN

    @property
    def is_closed(self) -> bool:
        return self.status == ROLL_CLOSED

    @property
    def is_exported(self) -> bool:
        return self.status == ROLL_EXPORTED

    @property
    def is_reviewed(self) -> bool:
        return self.status == ROLL_REVIEWED

    @property
    def is_reopened(self) -> bool:
        return self.status == ROLL_REOPENED


@dataclass(slots=True)
class RollItem:
    id: int | None = None
    roll_id: int = 0
    job_row_id: int = 0
    job_id: str = ""
    document: str = ""
    machine: str = ""
    fabric: str | None = None
    sort_order: int = 0
    planned_length_m: float = 0.0
    effective_printed_length_m: float = 0.0
    consumed_length_m: float = 0.0
    gap_before_m: float = 0.0
    metric_category: str | None = None
    review_status: str | None = None
    snapshot_print_status: str | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        self.sort_order = int(self.sort_order or 0)
        self.planned_length_m = float(self.planned_length_m or 0.0)
        self.effective_printed_length_m = float(self.effective_printed_length_m or 0.0)
        self.consumed_length_m = float(self.consumed_length_m or 0.0)
        self.gap_before_m = float(self.gap_before_m or 0.0)


@dataclass(slots=True)
class LogSource:
    id: int | None = None
    name: str = ""
    path: str = ""
    recursive: bool = True
    enabled: bool = True
    machine_hint: str | None = None


@dataclass(slots=True)
class ImportRun:
    id: int | None = None
    source_id: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None
    total_found: int = 0
    imported_count: int = 0
    duplicate_count: int = 0
    error_count: int = 0
    notes: str | None = None


__all__ = [
    # Review statuses
    "REVIEW_PENDING",
    "REVIEWED_OK",
    "REVIEWED_PARTIAL",
    "REVIEWED_FAILED",
    # Log statuses
    "LOG_NEW",
    "LOG_PARSED",
    "LOG_INVALID",
    "LOG_DUPLICATED",
    "LOG_IGNORED",
    "LOG_CONVERTED",
    # Roll statuses
    "ROLL_OPEN",
    "ROLL_DRAFT",
    "ROLL_CLOSED",
    "ROLL_EXPORTED",
    "ROLL_REVIEWED",
    "ROLL_REOPENED",
    # Job workflow statuses
    "JOB_PENDING_REVIEW",
    "JOB_READY",
    "JOB_SUSPICIOUS",
    "JOB_ASSIGNED_TO_ROLL",
    "JOB_IGNORED",
    "JOB_CORRECTED",
    # Models
    "Machine",
    "Log",
    "Job",
    "ProductionJob",
    "Roll",
    "RollItem",
    "LogSource",
    "ImportRun",
]