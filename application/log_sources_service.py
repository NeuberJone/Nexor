# application/log_sources_service.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from storage.import_audit_repository import ImportAuditRepository
from storage.log_sources_repository import LogSourceRepository


@dataclass(slots=True)
class LogSourceRow:
    source_id: int
    name: str
    path: str
    recursive: bool
    enabled: bool
    machine_hint: str | None
    last_scan_at: datetime | None
    last_successful_mtime: float | None
    created_at: datetime | None
    updated_at: datetime | None
    last_run_started_at: datetime | None
    last_run_finished_at: datetime | None
    last_run_total_found: int
    last_run_imported_count: int
    last_run_duplicate_count: int
    last_run_error_count: int
    last_run_notes: str | None


@dataclass(slots=True)
class LogSourceFormData:
    name: str
    path: str
    recursive: bool = True
    enabled: bool = True
    machine_hint: str | None = None


@dataclass(slots=True)
class LogSourceSnapshot:
    total_sources: int
    enabled_sources: int
    disabled_sources: int
    sources_with_checkpoint: int
    sources_with_runs: int
    sources_with_errors: int
    rows: list[LogSourceRow]


class LogSourcesService:
    """
    Application service para gestão das fontes de logs.

    Objetivos:
    - entregar DTOs prontos para a UI
    - centralizar validação básica de cadastro
    - evitar que a interface conheça sqlite.Row ou regras de persistência
    """

    def __init__(
        self,
        repository: LogSourceRepository | None = None,
        audit_repository: ImportAuditRepository | None = None,
        db_path: str | Path | None = None,
    ) -> None:
        self.repository = repository or _build_log_source_repository(db_path)
        self.audit_repository = audit_repository or _build_import_audit_repository(db_path)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def list_sources(self, include_disabled: bool = True) -> list[LogSourceRow]:
        rows = self.repository.list_all() if include_disabled else self.repository.list_enabled()
        mapped = [self._map_row(row) for row in rows]
        mapped.sort(key=lambda item: (not item.enabled, item.name.lower(), item.source_id))
        return mapped

    def get_source(self, source_id: int) -> LogSourceRow | None:
        row = self.repository.get_by_id(int(source_id))
        if row is None:
            return None
        return self._map_row(row)

    def get_snapshot(self) -> LogSourceSnapshot:
        rows = self.list_sources(include_disabled=True)

        enabled_sources = sum(1 for row in rows if row.enabled)
        disabled_sources = sum(1 for row in rows if not row.enabled)
        sources_with_checkpoint = sum(1 for row in rows if row.last_successful_mtime is not None)
        sources_with_runs = sum(1 for row in rows if row.last_run_started_at is not None)
        sources_with_errors = sum(1 for row in rows if row.last_run_error_count > 0)

        return LogSourceSnapshot(
            total_sources=len(rows),
            enabled_sources=enabled_sources,
            disabled_sources=disabled_sources,
            sources_with_checkpoint=sources_with_checkpoint,
            sources_with_runs=sources_with_runs,
            sources_with_errors=sources_with_errors,
            rows=rows,
        )

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def create_source(self, data: LogSourceFormData) -> LogSourceRow:
        normalized = self._normalize_form_data(data)
        self._validate_new_source(normalized)

        source_id = self.repository.upsert(
            name=normalized.name,
            path=normalized.path,
            recursive=normalized.recursive,
            machine_hint=normalized.machine_hint,
            enabled=normalized.enabled,
        )
        return self.get_source_or_raise(source_id)

    def enable_source(self, source_id: int) -> LogSourceRow:
        self.get_source_or_raise(source_id)
        self.repository.enable(int(source_id))
        return self.get_source_or_raise(source_id)

    def disable_source(self, source_id: int) -> LogSourceRow:
        self.get_source_or_raise(source_id)
        self.repository.disable(int(source_id))
        return self.get_source_or_raise(source_id)

    def set_enabled(self, source_id: int, enabled: bool) -> LogSourceRow:
        self.get_source_or_raise(source_id)
        self.repository.set_enabled(int(source_id), bool(enabled))
        return self.get_source_or_raise(source_id)

    def reset_checkpoint(self, source_id: int) -> LogSourceRow:
        self.get_source_or_raise(source_id)
        self.repository.reset_checkpoint(int(source_id))
        return self.get_source_or_raise(source_id)

    def delete_source(self, source_id: int) -> None:
        self.get_source_or_raise(source_id)
        self.repository.delete(int(source_id))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def get_source_or_raise(self, source_id: int) -> LogSourceRow:
        row = self.get_source(source_id)
        if row is None:
            raise ValueError(f"Fonte de log não encontrada: id={source_id}")
        return row

    def _validate_new_source(self, data: LogSourceFormData) -> None:
        existing_name = self.repository.get_by_name(data.name)
        if existing_name is not None:
            raise ValueError(f"Já existe uma fonte com o nome '{data.name}'.")

        existing_path = self.repository.get_by_path(data.path)
        if existing_path is not None:
            raise ValueError(f"Já existe uma fonte cadastrada para o caminho '{data.path}'.")

    def _normalize_form_data(self, data: LogSourceFormData) -> LogSourceFormData:
        name = (data.name or "").strip()
        path_text = (data.path or "").strip()
        machine_hint = _blank_to_none(data.machine_hint)

        if not name:
            raise ValueError("Informe o nome da fonte.")
        if not path_text:
            raise ValueError("Informe o caminho da fonte.")

        normalized_path = str(Path(path_text))

        return LogSourceFormData(
            name=name,
            path=normalized_path,
            recursive=bool(data.recursive),
            enabled=bool(data.enabled),
            machine_hint=machine_hint,
        )

    def _map_row(self, row: Any) -> LogSourceRow:
        source_id = int(row["id"])
        last_run = self._get_last_run_for_source(source_id)

        return LogSourceRow(
            source_id=source_id,
            name=str(row["name"] or ""),
            path=str(row["path"] or ""),
            recursive=bool(int(row["recursive"] or 0)),
            enabled=bool(int(row["enabled"] or 0)),
            machine_hint=_blank_to_none(row["machine_hint"]),
            last_scan_at=_parse_dt(row["last_scan_at"]),
            last_successful_mtime=_to_float_or_none(row["last_successful_mtime"]),
            created_at=_parse_dt(row["created_at"]),
            updated_at=_parse_dt(row["updated_at"]),
            last_run_started_at=_parse_dt(last_run["started_at"]) if last_run is not None else None,
            last_run_finished_at=_parse_dt(last_run["finished_at"]) if last_run is not None else None,
            last_run_total_found=int(last_run["total_found"] or 0) if last_run is not None else 0,
            last_run_imported_count=int(last_run["imported_count"] or 0) if last_run is not None else 0,
            last_run_duplicate_count=int(last_run["duplicate_count"] or 0) if last_run is not None else 0,
            last_run_error_count=int(last_run["error_count"] or 0) if last_run is not None else 0,
            last_run_notes=_blank_to_none(last_run["notes"]) if last_run is not None else None,
        )

    def _get_last_run_for_source(self, source_id: int) -> Any | None:
        runs = self.audit_repository.list_runs(source_id=source_id, limit=1)
        if not runs:
            return None
        return runs[0]


def _build_log_source_repository(db_path: str | Path | None) -> LogSourceRepository:
    if db_path is None:
        return LogSourceRepository()

    try:
        return LogSourceRepository(db_path=db_path)
    except TypeError:
        return LogSourceRepository()


def _build_import_audit_repository(db_path: str | Path | None) -> ImportAuditRepository:
    if db_path is None:
        return ImportAuditRepository()

    try:
        return ImportAuditRepository(db_path=db_path)
    except TypeError:
        return ImportAuditRepository()


def _parse_dt(value: Any) -> datetime | None:
    text = (str(value).strip() if value is not None else "")
    if not text:
        return None

    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _blank_to_none(value: Any) -> str | None:
    text = (str(value).strip() if value is not None else "")
    return text or None


def _to_float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None