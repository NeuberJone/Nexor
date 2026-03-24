from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from core.models import ROLL_OPEN
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


class OperationsPanelService:
    def __init__(self, repository: ProductionRepository | None = None) -> None:
        self.repository = repository or ProductionRepository()

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

            if filters.search:
                haystack = " ".join(
                    [
                        str(row.roll_id),
                        str(row.roll_name or ""),
                        str(row.machine or ""),
                        str(row.fabric or ""),
                        str(row.status or ""),
                        str(row.note or ""),
                    ]
                ).lower()
                if filters.search.strip().lower() not in haystack:
                    continue

            rows.append(row)

            if filters.limit is not None and len(rows) >= filters.limit:
                break

        return rows

    def list_open_rolls(self) -> list[OpenRollRow]:
        return self.list_rolls(RollListFilters(status=ROLL_OPEN))

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

    def get_roll_filter_values(self) -> dict[str, list[str]]:
        rows = self.list_rolls(RollListFilters(limit=None))

        statuses = sorted({row.status for row in rows if row.status})
        machines = sorted({row.machine for row in rows if row.machine})

        return {
            "statuses": statuses,
            "machines": machines,
        }

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

        pending_review_count = sum(1 for item in items if item.review_status == "PENDING_REVIEW")
        reviewed_ok_count = sum(1 for item in items if item.review_status == "REVIEWED_OK")
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