from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from core.exceptions import LogParseError, LogValidationError
from core.models import LOG_NEW, Log, ProductionJob
from logs.mapper import map_sections_to_job
from logs.parser import parse_log_text
from storage.repository import ProductionRepository


def normalize_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def read_log_text(path: str | Path) -> str:
    file_path = normalize_path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Log file not found: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    return file_path.read_text(encoding="utf-8", errors="ignore")


def compute_log_fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def parse_sections_from_log(path: str | Path) -> dict[str, Any]:
    text = read_log_text(path)
    return parse_log_text(text)


def build_log_record(path: str | Path) -> Log:
    file_path = normalize_path(path)
    text = read_log_text(file_path)

    return Log(
        source_path=str(file_path),
        source_name=file_path.name,
        fingerprint=compute_log_fingerprint(text),
        raw_payload=text,
        status=LOG_NEW,
    )


def import_job_from_log(path: str | Path) -> ProductionJob:
    """
    Backward-compatible helper.

    Reads a log file, parses it, maps it into a ProductionJob and returns it
    without persisting anything.
    """
    file_path = normalize_path(path)
    text = read_log_text(file_path)
    sections = parse_log_text(text)
    return map_sections_to_job(sections, source_path=str(file_path))


def import_and_persist_log(
    path: str | Path,
    repository: ProductionRepository | None = None,
    raise_on_invalid: bool = True,
) -> dict[str, Any]:
    """
    Full import flow for a single log file.

    Returns a dictionary with:
    - log: persisted or existing Log
    - job: persisted ProductionJob when conversion succeeds
    - is_duplicate: whether the log had already been imported
    - created_log: whether a new log row was created now
    - created_job: whether a new/updated job row was created now
    """
    repo = repository or ProductionRepository()
    file_path = normalize_path(path)

    log_record = build_log_record(file_path)
    existing_log = repo.get_log_by_fingerprint(log_record.fingerprint or "")

    if existing_log:
        existing_job = (
            repo.get_job_by_row_id(existing_log.job_id)
            if existing_log.job_id is not None
            else None
        )
        return {
            "log": existing_log,
            "job": existing_job,
            "is_duplicate": True,
            "created_log": False,
            "created_job": False,
        }

    persisted_log_id = repo.save_log(log_record)
    persisted_log = repo.get_log_by_id(persisted_log_id)

    try:
        sections = parse_log_text(log_record.raw_payload or "")
        repo.mark_log_parsed(persisted_log_id)

        job = map_sections_to_job(
            sections,
            source_path=str(file_path),
        )
        job.log_id = persisted_log_id

        job_row_id = repo.save_job(job)
        repo.mark_log_converted(persisted_log_id, job_row_id)

        saved_log = repo.get_log_by_id(persisted_log_id)
        saved_job = repo.get_job_by_row_id(job_row_id)

        return {
            "log": saved_log,
            "job": saved_job,
            "is_duplicate": False,
            "created_log": True,
            "created_job": True,
        }

    except (LogParseError, LogValidationError) as exc:
        repo.mark_log_invalid(persisted_log_id, parse_error=str(exc))

        if raise_on_invalid:
            raise

        return {
            "log": repo.get_log_by_id(persisted_log_id),
            "job": None,
            "is_duplicate": False,
            "created_log": True,
            "created_job": False,
            "error": str(exc),
        }


def import_many_logs(
    paths: list[str | Path],
    repository: ProductionRepository | None = None,
    raise_on_invalid: bool = False,
) -> list[dict[str, Any]]:
    repo = repository or ProductionRepository()
    results: list[dict[str, Any]] = []

    for path in paths:
        try:
            result = import_and_persist_log(
                path=path,
                repository=repo,
                raise_on_invalid=raise_on_invalid,
            )
        except (LogParseError, LogValidationError, FileNotFoundError, ValueError) as exc:
            if raise_on_invalid:
                raise

            result = {
                "path": str(path),
                "log": None,
                "job": None,
                "is_duplicate": False,
                "created_log": False,
                "created_job": False,
                "error": str(exc),
            }

        results.append(result)

    return results