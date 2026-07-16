# application/log_sources_service.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from storage.import_audit_repository import ImportAuditRepository
from storage.log_sources_repository import LogSourceRepository


@dataclass(slots=True)
class LogSourceFormData:
    name: str
    path: str
    machine_hint: str | None = None
    recursive: bool = True
    enabled: bool = True


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
    Application service das fontes de logs.

    Responsabilidades:
    - servir dados prontos para a UI
    - combinar cadastro de fontes com auditoria de importação
    - manter a lógica de validação fora da camada visual
    """

    def __init__(
        self,
        repository: LogSourceRepository | None = None,
        audit_repository: ImportAuditRepository | None = None,
        db_path: str | Path | None = None,
    ) -> None:
        self.repository = repository or LogSourceRepository(db_path=db_path)
        self.audit_repository = audit_repository or ImportAuditRepository(db_path=db_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_sources(self, include_disabled: bool = True) -> list[LogSourceRow]:
        raw_rows = (
            self.repository.list_all()
            if include_disabled
            else self.repository.list_enabled()
        )

        rows: list[LogSourceRow] = []
        for raw in raw_rows:
            rows.append(self._map_source_row(raw))

        return rows

    def get_source(self, source_id: int) -> LogSourceRow:
        raw = self.repository.get_by_id(int(source_id))
        if raw is None:
            raise ValueError("Fonte de logs não encontrada.")
        return self._map_source_row(raw)

    def get_snapshot(self) -> LogSourceSnapshot:
        rows = self.list_sources(include_disabled=True)

        total_sources = len(rows)
        enabled_sources = sum(1 for row in rows if row.enabled)
        disabled_sources = total_sources - enabled_sources
        sources_with_checkpoint = sum(1 for row in rows if row.last_successful_mtime is not None)
        sources_with_runs = sum(1 for row in rows if row.last_run_started_at is not None)
        sources_with_errors = sum(
            1
            for row in rows
            if row.last_run_error_count > 0
        )

        return LogSourceSnapshot(
            total_sources=total_sources,
            enabled_sources=enabled_sources,
            disabled_sources=disabled_sources,
            sources_with_checkpoint=sources_with_checkpoint,
            sources_with_runs=sources_with_runs,
            sources_with_errors=sources_with_errors,
            rows=rows,
        )

    def create_source(self, form: LogSourceFormData) -> LogSourceRow:
        normalized = self._normalize_form(form)

        source_id = self.repository.upsert(
            name=normalized.name,
            path=normalized.path,
            recursive=normalized.recursive,
            machine_hint=normalized.machine_hint,
            enabled=normalized.enabled,
        )
        return self.get_source(source_id)

    def enable_source(self, source_id: int) -> LogSourceRow:
        self.repository.enable(int(source_id))
        return self.get_source(source_id)

    def disable_source(self, source_id: int) -> LogSourceRow:
        self.repository.disable(int(source_id))
        return self.get_source(source_id)

    def reset_checkpoint(self, source_id: int) -> LogSourceRow:
        self.repository.reset_checkpoint(int(source_id))
        return self.get_source(source_id)

    def delete_source(self, source_id: int) -> None:
        self.repository.delete(int(source_id))

    # ------------------------------------------------------------------
    # Optional helpers for future flows
    # ------------------------------------------------------------------

    def mark_scan_started(self, source_id: int) -> LogSourceRow:
        self.repository.touch_scan_started(int(source_id))
        return self.get_source(source_id)

    def mark_last_scan(self, source_id: int) -> LogSourceRow:
        self.repository.update_last_scan_at(int(source_id))
        return self.get_source(source_id)

    def update_checkpoint(self, source_id: int, mtime: float) -> LogSourceRow:
        self.repository.update_last_successful_mtime(int(source_id), float(mtime))
        return self.get_source(source_id)

    # ------------------------------------------------------------------
    # Internal mapping
    # ------------------------------------------------------------------

    def _map_source_row(self, raw: Any) -> LogSourceRow:
        latest_run = self._get_latest_run(int(raw["id"]))

        return LogSourceRow(
            source_id=int(raw["id"]),
            name=str(raw["name"] or ""),
            path=str(raw["path"] or ""),
            recursive=bool(raw["recursive"]),
            enabled=bool(raw["enabled"]),
            machine_hint=_blank_to_none(raw["machine_hint"]),
            last_scan_at=_parse_dt(raw["last_scan_at"]),
            last_successful_mtime=_to_float_or_none(raw["last_successful_mtime"]),
            created_at=_parse_dt(raw["created_at"]),
            updated_at=_parse_dt(raw["updated_at"]),
            last_run_started_at=_parse_dt(_safe_get(latest_run, "started_at")),
            last_run_finished_at=_parse_dt(_safe_get(latest_run, "finished_at")),
            last_run_total_found=_to_int(_safe_get(latest_run, "total_found")),
            last_run_imported_count=_to_int(_safe_get(latest_run, "imported_count")),
            last_run_duplicate_count=_to_int(_safe_get(latest_run, "duplicate_count")),
            last_run_error_count=_to_int(_safe_get(latest_run, "error_count")),
            last_run_notes=_blank_to_none(_safe_get(latest_run, "notes")),
        )

    def _get_latest_run(self, source_id: int):
        runs = self.audit_repository.list_runs(source_id=source_id, limit=1)
        if not runs:
            return None
        return runs[0]

    def _normalize_form(self, form: LogSourceFormData) -> LogSourceFormData:
        name = (form.name or "").strip()
        if not name:
            raise ValueError("Informe o nome da fonte.")

        raw_path = (form.path or "").strip()
        if not raw_path:
            raise ValueError("Informe a pasta da fonte.")

        path_obj = Path(raw_path).expanduser()

        # Mantém comportamento amigável no Windows e normaliza o caminho.
        try:
            normalized_path = str(path_obj.resolve(strict=False))
        except Exception:
            normalized_path = str(path_obj)

        if not Path(normalized_path).exists():
            raise ValueError("A pasta informada não existe.")

        if not Path(normalized_path).is_dir():
            raise ValueError("O caminho informado não é uma pasta.")

        machine_hint = (form.machine_hint or "").strip().upper() or None

        return LogSourceFormData(
            name=name,
            path=normalized_path,
            machine_hint=machine_hint,
            recursive=bool(form.recursive),
            enabled=bool(form.enabled),
        )


def _safe_get(row: Any, key: str):
    if row is None:
        return None
    try:
        return row[key]
    except Exception:
        return None


def _blank_to_none(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _to_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _to_float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None

    if isinstance(value, datetime):
        return value

    text = str(value).strip()
    if not text:
        return None

    try:
        return datetime.fromisoformat(text)
    except Exception:
        pass

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
    ):
        try:
            return datetime.strptime(text, fmt)
        except Exception:
            continue

    return None