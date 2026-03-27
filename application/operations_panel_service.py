from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from core.models import (
    LOG_CONVERTED,
    LOG_NEW,
    LOG_NORMALIZATION_CONVERTED,
    LOG_NORMALIZATION_PENDING,
    LOG_NORMALIZATION_READY,
    LOG_PARSE_DUPLICATED,
    LOG_PARSE_IGNORED,
    LOG_PARSE_INVALID,
    LOG_PARSE_NEW,
    LOG_PARSE_PARSED,
    REVIEW_PENDING,
    REVIEWED_OK,
    ROLL_OPEN,
)
from exports.roll_export_service import export_closed_roll
from storage.repository import ProductionRepository


@dataclass(slots=True)
class AvailableJobsFilters:
    machine: str | None = None
    fabric: str | None = None
    review_status: str | None = None
    exclude_suspicious: bool = False
    limit: int | None = None


@dataclass(slots=True)
class RollListFilters:
    status: str | None = None
    machine: str | None = None
    search: str | None = None
    limit: int | None = None


@dataclass(slots=True)
class LogQueueFilters:
    status: str | None = None
    parse_status: str | None = None
    normalized_status: str | None = None
    search: str | None = None
    limit: int | None = None


@dataclass(slots=True)
class AvailableJobRow:
    row_id: int
    job_id: str
    machine: str
    fabric: str | None
    review_status: str | None
    print_status: str | None
    document: str
    planned_length_m: float
    effective_printed_length_m: float
    gap_before_m: float
    consumed_length_m: float
    is_suspicious: bool
    suspicion_reason: str | None
    start_time: datetime | None
    end_time: datetime | None


@dataclass(slots=True)
class RollItemRow:
    row_id: int | None
    job_id: str
    document: str
    machine: str
    fabric: str | None
    review_status: str | None
    metric_category: str | None
    planned_length_m: float
    effective_printed_length_m: float
    gap_before_m: float
    consumed_length_m: float


@dataclass(slots=True)
class OpenRollRow:
    roll_id: int
    roll_name: str
    machine: str
    fabric: str | None
    status: str
    created_at: datetime | None
    jobs_count: int
    total_effective_m: float
    total_gap_m: float
    total_consumed_m: float
    note: str | None


@dataclass(slots=True)
class LogQueueRow:
    log_id: int
    source_name: str | None
    source_path: str | None
    machine_code_raw: str | None
    captured_at: datetime | None
    imported_at: datetime | None
    status: str
    parse_status: str
    normalized_status: str
    parse_error: str | None
    job_id: int | None
    is_actionable: bool
    is_terminal: bool


@dataclass(slots=True)
class RollSummaryDTO:
    roll_id: int
    roll_name: str
    machine: str
    fabric: str | None
    status: str
    created_at: datetime | None
    closed_at: datetime | None
    exported_at: datetime | None
    note: str | None
    jobs_count: int
    total_planned_m: float
    total_effective_m: float
    total_gap_m: float
    total_consumed_m: float
    efficiency_ratio: float | None
    metric_counts: dict[str, int]
    fabric_totals: dict[str, float]
    pending_review_count: int
    reviewed_ok_count: int
    suspicious_count: int
    items: list[RollItemRow]


@dataclass(slots=True)
class OperationsSnapshotDTO:
    available_jobs_count: int
    suspicious_jobs_count: int
    open_rolls_count: int
    pending_logs_count: int
    parsed_logs_count: int
    ready_logs_count: int
    converted_logs_count: int
    invalid_logs_count: int
    duplicated_logs_count: int
    ignored_logs_count: int


class OperationsPanelService:
    """
    Application service para o painel operacional local.

    Responsabilidades:
    - servir dados já prontos para a UI
    - reaproveitar o núcleo validado
    - evitar que a UI conheça detalhes do repository/export service
    """

    def __init__(self, repository: ProductionRepository | None = None) -> None:
        self.repository = repository or ProductionRepository()

    # ------------------------------------------------------------------
    # Available jobs
    # ------------------------------------------------------------------

    def list_available_jobs(
        self,
        filters: AvailableJobsFilters | None = None,
    ) -> list[AvailableJobRow]:
        filters = filters or AvailableJobsFilters()

        jobs = self.repository.list_available_jobs(
            machine=_norm(filters.machine),
            fabric=_norm(filters.fabric),
            review_status=_norm(filters.review_status),
            include_suspicious=not filters.exclude_suspicious,
            limit=filters.limit,
        )
        return [self._map_available_job(job) for job in jobs]

    def get_filter_values(self) -> dict[str, list[str]]:
        jobs = self.list_available_jobs(AvailableJobsFilters(limit=None))

        machines = sorted({row.machine for row in jobs if row.machine})
        fabrics = sorted({row.fabric for row in jobs if row.fabric})
        review_statuses = sorted({row.review_status for row in jobs if row.review_status})

        return {
            "machines": machines,
            "fabrics": fabrics,
            "review_statuses": review_statuses,
        }

    # ------------------------------------------------------------------
    # Logs / operational queue
    # ------------------------------------------------------------------

    def list_log_queue(
        self,
        filters: LogQueueFilters | None = None,
    ) -> list[LogQueueRow]:
        filters = filters or LogQueueFilters()

        logs = self.repository.list_logs(
            status=_norm(filters.status),
            parse_status=_norm(filters.parse_status),
            normalized_status=_norm(filters.normalized_status),
            limit=filters.limit,
        )

        rows = [self._map_log_queue_row(log) for log in logs]

        if filters.search:
            term = filters.search.strip().lower()
            rows = [
                row for row in rows
                if _contains_search(
                    term,
                    row.log_id,
                    row.source_name,
                    row.source_path,
                    row.machine_code_raw,
                    row.status,
                    row.parse_status,
                    row.normalized_status,
                    row.parse_error,
                    row.job_id,
                )
            ]

        return rows

    def get_log_filter_values(self) -> dict[str, list[str]]:
        rows = self.list_log_queue(LogQueueFilters(limit=None))

        return {
            "statuses": sorted({row.status for row in rows if row.status}),
            "parse_statuses": sorted({row.parse_status for row in rows if row.parse_status}),
            "normalized_statuses": sorted(
                {row.normalized_status for row in rows if row.normalized_status}
            ),
            "machines": sorted({row.machine_code_raw for row in rows if row.machine_code_raw}),
        }

    # ------------------------------------------------------------------
    # Rolls
    # ------------------------------------------------------------------

    def list_rolls(
        self,
        filters: RollListFilters | None = None,
    ) -> list[OpenRollRow]:
        filters = filters or RollListFilters()

        rows: list[OpenRollRow] = []
        rolls = self.repository.list_rolls(status=_norm(filters.status))

        for roll in rolls:
            summary = self.repository.get_roll_summary(int(roll.id))
            row = self._map_open_roll(summary)

            if filters.machine and row.machine.strip().upper() != filters.machine.strip().upper():
                continue

            if filters.search and not _contains_search(
                filters.search.strip().lower(),
                row.roll_id,
                row.roll_name,
                row.machine,
                row.fabric,
                row.status,
                row.note,
            ):
                continue

            rows.append(row)

            if filters.limit is not None and len(rows) >= filters.limit:
                break

        return rows

    def list_open_rolls(self) -> list[OpenRollRow]:
        return self.list_rolls(RollListFilters(status=ROLL_OPEN))

    def get_roll_filter_values(self) -> dict[str, list[str]]:
        rows = self.list_rolls(RollListFilters(limit=None))

        statuses = sorted({row.status for row in rows if row.status})
        machines = sorted({row.machine for row in rows if row.machine})

        return {
            "statuses": statuses,
            "machines": machines,
        }

    def create_roll(
        self,
        *,
        machine: str,
        fabric: str | None = None,
        note: str | None = None,
        roll_name: str | None = None,
    ) -> RollSummaryDTO:
        roll_id = self.repository.create_roll(
            machine=machine,
            fabric=fabric,
            note=note,
            roll_name=roll_name,
        )
        return self.get_roll_summary(roll_id)

    def get_roll_summary(self, roll_id: int) -> RollSummaryDTO:
        summary = self.repository.get_roll_summary(roll_id)
        return self._map_roll_summary(summary)

    def get_roll_detail(self, roll_id: int) -> RollSummaryDTO:
        return self.get_roll_summary(roll_id)

    def add_job_to_roll(self, *, roll_id: int, job_row_id: int) -> RollSummaryDTO:
        self.repository.add_job_to_roll(
            roll_id=roll_id,
            job_row_id=job_row_id,
        )
        return self.get_roll_summary(roll_id)

    def remove_job_from_roll(self, *, roll_id: int, job_row_id: int) -> RollSummaryDTO:
        removed = self.repository.remove_job_from_roll(
            roll_id=roll_id,
            job_row_id=job_row_id,
        )
        if removed <= 0:
            raise ValueError("Nenhum item removido do rolo.")
        return self.get_roll_summary(roll_id)

    def close_roll(self, *, roll_id: int, note: str | None = None) -> RollSummaryDTO:
        self.repository.close_roll(roll_id=roll_id, note=note)
        return self.get_roll_summary(roll_id)

    def export_roll(self, *, roll_id: int, output_dir: str | Path) -> dict[str, Any]:
        return export_closed_roll(
            roll_id=roll_id,
            output_dir=output_dir,
            repository=self.repository,
        )

    # ------------------------------------------------------------------
    # Dashboard / overview
    # ------------------------------------------------------------------

    def get_operations_snapshot(self) -> OperationsSnapshotDTO:
        available_jobs = self.repository.list_available_jobs(limit=None)
        open_rolls = self.repository.list_rolls(status=ROLL_OPEN)
        logs = self.repository.list_logs(limit=None)

        suspicious_jobs_count = sum(
            1 for job in available_jobs
            if bool(getattr(job, "suspicion_category", None) or getattr(job, "suspicion_reason", None))
        )

        pending_logs_count = sum(
            1 for log in logs if (getattr(log, "parse_status", "") or "").upper() == LOG_PARSE_NEW
        )
        parsed_logs_count = sum(
            1 for log in logs if (getattr(log, "parse_status", "") or "").upper() == LOG_PARSE_PARSED
        )
        ready_logs_count = sum(
            1 for log in logs
            if (getattr(log, "normalized_status", "") or "").upper() == LOG_NORMALIZATION_READY
        )
        converted_logs_count = sum(
            1 for log in logs
            if (getattr(log, "normalized_status", "") or "").upper() == LOG_NORMALIZATION_CONVERTED
            or (getattr(log, "status", "") or "").upper() == LOG_CONVERTED
        )
        invalid_logs_count = sum(
            1 for log in logs if (getattr(log, "parse_status", "") or "").upper() == LOG_PARSE_INVALID
        )
        duplicated_logs_count = sum(
            1 for log in logs if (getattr(log, "parse_status", "") or "").upper() == LOG_PARSE_DUPLICATED
        )
        ignored_logs_count = sum(
            1 for log in logs if (getattr(log, "parse_status", "") or "").upper() == LOG_PARSE_IGNORED
        )

        return OperationsSnapshotDTO(
            available_jobs_count=len(available_jobs),
            suspicious_jobs_count=suspicious_jobs_count,
            open_rolls_count=len(open_rolls),
            pending_logs_count=pending_logs_count,
            parsed_logs_count=parsed_logs_count,
            ready_logs_count=ready_logs_count,
            converted_logs_count=converted_logs_count,
            invalid_logs_count=invalid_logs_count,
            duplicated_logs_count=duplicated_logs_count,
            ignored_logs_count=ignored_logs_count,
        )

    # ------------------------------------------------------------------
    # Mapping
    # ------------------------------------------------------------------

    def _map_available_job(self, job: Any) -> AvailableJobRow:
        return AvailableJobRow(
            row_id=int(job.id),
            job_id=str(job.job_id),
            machine=str(job.machine or ""),
            fabric=_blank_to_none(getattr(job, "fabric", None)),
            review_status=_blank_to_none(getattr(job, "review_status", None)),
            print_status=_blank_to_none(getattr(job, "print_status", None)),
            document=str(getattr(job, "document", "") or ""),
            planned_length_m=float(getattr(job, "planned_length_m", 0.0) or 0.0),
            effective_printed_length_m=float(getattr(job, "actual_printed_length_m", 0.0) or 0.0),
            gap_before_m=float(getattr(job, "gap_before_m", 0.0) or 0.0),
            consumed_length_m=float(getattr(job, "consumed_length_m", 0.0) or 0.0),
            is_suspicious=bool(
                getattr(job, "suspicion_category", None) or getattr(job, "suspicion_reason", None)
            ),
            suspicion_reason=_blank_to_none(getattr(job, "suspicion_reason", None)),
            start_time=getattr(job, "start_time", None),
            end_time=getattr(job, "end_time", None),
        )

    def _map_open_roll(self, summary: dict[str, Any]) -> OpenRollRow:
        roll = summary["roll"]
        return OpenRollRow(
            roll_id=int(roll.id),
            roll_name=str(roll.roll_name),
            machine=str(roll.machine),
            fabric=_blank_to_none(getattr(roll, "fabric", None)),
            status=str(roll.status),
            created_at=getattr(roll, "created_at", None),
            jobs_count=int(summary.get("jobs_count") or 0),
            total_effective_m=float(summary.get("total_effective_m") or 0.0),
            total_gap_m=float(summary.get("total_gap_m") or 0.0),
            total_consumed_m=float(summary.get("total_consumed_m") or 0.0),
            note=_blank_to_none(getattr(roll, "note", None)),
        )

    def _map_roll_summary(self, summary: dict[str, Any]) -> RollSummaryDTO:
        roll = summary["roll"]
        items = [self._map_roll_item(item) for item in summary.get("items", [])]

        pending_review_count = sum(1 for item in items if item.review_status == REVIEW_PENDING)
        reviewed_ok_count = sum(1 for item in items if item.review_status == REVIEWED_OK)
        suspicious_count = sum(1 for item in items if (item.metric_category or "").upper() != "OK")

        return RollSummaryDTO(
            roll_id=int(roll.id),
            roll_name=str(roll.roll_name),
            machine=str(roll.machine),
            fabric=_blank_to_none(getattr(roll, "fabric", None)),
            status=str(roll.status),
            created_at=getattr(roll, "created_at", None),
            closed_at=getattr(roll, "closed_at", None),
            exported_at=getattr(roll, "exported_at", None),
            note=_blank_to_none(getattr(roll, "note", None)),
            jobs_count=int(summary.get("jobs_count") or 0),
            total_planned_m=float(summary.get("total_planned_m") or 0.0),
            total_effective_m=float(summary.get("total_effective_m") or 0.0),
            total_gap_m=float(summary.get("total_gap_m") or 0.0),
            total_consumed_m=float(summary.get("total_consumed_m") or 0.0),
            efficiency_ratio=_to_float_or_none(summary.get("efficiency_ratio")),
            metric_counts=dict(summary.get("metric_counts") or {}),
            fabric_totals=dict(summary.get("fabric_totals") or {}),
            pending_review_count=pending_review_count,
            reviewed_ok_count=reviewed_ok_count,
            suspicious_count=suspicious_count,
            items=items,
        )

    def _map_roll_item(self, item: Any) -> RollItemRow:
        return RollItemRow(
            row_id=getattr(item, "job_row_id", None),
            job_id=str(item.job_id),
            document=str(getattr(item, "document", "") or ""),
            machine=str(getattr(item, "machine", "") or ""),
            fabric=_blank_to_none(getattr(item, "fabric", None)),
            review_status=_blank_to_none(getattr(item, "review_status", None)),
            metric_category=_blank_to_none(getattr(item, "metric_category", None)),
            planned_length_m=float(getattr(item, "planned_length_m", 0.0) or 0.0),
            effective_printed_length_m=float(getattr(item, "effective_printed_length_m", 0.0) or 0.0),
            gap_before_m=float(getattr(item, "gap_before_m", 0.0) or 0.0),
            consumed_length_m=float(getattr(item, "consumed_length_m", 0.0) or 0.0),
        )

    def _map_log_queue_row(self, log: Any) -> LogQueueRow:
        status = str(getattr(log, "status", "") or LOG_NEW)
        parse_status = str(getattr(log, "parse_status", "") or LOG_PARSE_NEW)
        normalized_status = str(
            getattr(log, "normalized_status", "") or LOG_NORMALIZATION_PENDING
        )

        return LogQueueRow(
            log_id=int(getattr(log, "id")),
            source_name=_blank_to_none(getattr(log, "source_name", None)),
            source_path=_blank_to_none(getattr(log, "source_path", None)),
            machine_code_raw=_blank_to_none(getattr(log, "machine_code_raw", None)),
            captured_at=getattr(log, "captured_at", None),
            imported_at=getattr(log, "imported_at", None),
            status=status,
            parse_status=parse_status,
            normalized_status=normalized_status,
            parse_error=_blank_to_none(getattr(log, "parse_error", None)),
            job_id=getattr(log, "job_id", None),
            is_actionable=bool(getattr(log, "is_actionable", False)),
            is_terminal=bool(getattr(log, "is_terminal", False)),
        )


def _norm(value: str | None) -> str | None:
    text = (value or "").strip()
    return text or None


def _blank_to_none(value: str | None) -> str | None:
    text = (value or "").strip()
    return text or None


def _to_float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _contains_search(term: str, *values: object) -> bool:
    haystack = " ".join(str(value or "") for value in values).lower()
    return term in haystack