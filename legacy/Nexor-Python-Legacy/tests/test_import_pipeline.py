from __future__ import annotations

import sqlite3
from pathlib import Path
from textwrap import dedent

import pytest

from logs.service import import_and_persist_log
from storage.repository import ProductionRepository


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_test_repository(tmp_path: Path) -> ProductionRepository:
    db_path = tmp_path / "test_nexor.db"
    schema_path = PROJECT_ROOT / "storage" / "schema.sql"

    conn = sqlite3.connect(str(db_path))
    try:
        schema = schema_path.read_text(encoding="utf-8")
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()

    repo = ProductionRepository(db_path=db_path)
    repo.ensure_runtime_fields()
    return repo


def write_log_file(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def count_rows(repo: ProductionRepository, table_name: str) -> int:
    with repo.connect() as conn:
        row = conn.execute(f"SELECT COUNT(*) AS n FROM {table_name}").fetchone()
        return int(row["n"])


def make_valid_log_text(
    *,
    job_id: str = "11077",
    document: str = "23-03 - dryfit - manchester chelsea (4).jpeg",
    start_time: str = "09/03/2026 19:45:54",
    end_time: str = "09/03/2026 19:50:54",
    computer_name: str = "DESKTOP-36UB5C9",
    driver: str = "MIMAKI",
    height_mm: str = "1101",
    vpos_mm: str = "1054.5",
    print_height_mm: str = "1101",
) -> str:
    return dedent(
        f"""
        [General]
        JobID={job_id}
        Document={document}
        StartTime={start_time}
        EndTime={end_time}
        ComputerName={computer_name}
        Driver={driver}

        [1]
        Name={document}
        HeightMM={height_mm}
        VPosMM={vpos_mm}

        [Costs]
        PrintHeightMM={print_height_mm}
        """
    ).strip()


def make_invalid_log_text_missing_job_id() -> str:
    return dedent(
        """
        [General]
        Document=23-03 - dryfit - manchester chelsea (4).jpeg
        StartTime=09/03/2026 19:45:54
        EndTime=09/03/2026 19:50:54
        ComputerName=DESKTOP-36UB5C9
        Driver=MIMAKI

        [1]
        Name=23-03 - dryfit - manchester chelsea (4).jpeg
        HeightMM=1101
        VPosMM=1054.5

        [Costs]
        PrintHeightMM=1101
        """
    ).strip()


def test_valid_import_creates_log_and_job(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)
    log_path = write_log_file(tmp_path, "valid_log.txt", make_valid_log_text())

    result = import_and_persist_log(
        path=log_path,
        repository=repo,
        raise_on_invalid=False,
    )

    assert result["is_duplicate"] is False
    assert result["created_log"] is True
    assert result["created_job"] is True

    log_record = result["log"]
    job = result["job"]

    assert log_record is not None
    assert job is not None

    assert log_record.status == "CONVERTED"
    assert log_record.job_id == job.id

    assert job.job_id == "11077"
    assert job.machine == "M1"
    assert job.fabric == "DRYFIT"

    assert job.actual_printed_length_m == pytest.approx(1.101, rel=1e-6)
    assert job.gap_before_m == pytest.approx(1.0545, rel=1e-6)
    assert job.consumed_length_m == pytest.approx(2.1555, rel=1e-6)

    assert count_rows(repo, "logs") == 1
    assert count_rows(repo, "production_jobs") == 1


def test_duplicate_import_does_not_create_second_log_or_job(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)
    log_path = write_log_file(tmp_path, "duplicate_log.txt", make_valid_log_text())

    first_result = import_and_persist_log(
        path=log_path,
        repository=repo,
        raise_on_invalid=False,
    )
    second_result = import_and_persist_log(
        path=log_path,
        repository=repo,
        raise_on_invalid=False,
    )

    assert first_result["is_duplicate"] is False
    assert second_result["is_duplicate"] is True
    assert second_result["created_log"] is False
    assert second_result["created_job"] is False

    assert count_rows(repo, "logs") == 1
    assert count_rows(repo, "production_jobs") == 1


def test_invalid_import_marks_log_as_invalid_and_keeps_raw_record(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)
    log_path = write_log_file(
        tmp_path,
        "invalid_log.txt",
        make_invalid_log_text_missing_job_id(),
    )

    result = import_and_persist_log(
        path=log_path,
        repository=repo,
        raise_on_invalid=False,
    )

    assert result["is_duplicate"] is False
    assert result["created_log"] is True
    assert result["created_job"] is False
    assert result["job"] is None
    assert "Missing JobID" in result["error"]

    log_record = result["log"]
    assert log_record is not None
    assert log_record.status == "INVALID"
    assert log_record.raw_payload is not None
    assert "JobID" not in log_record.raw_payload

    assert count_rows(repo, "logs") == 1
    assert count_rows(repo, "production_jobs") == 0


def test_heightmm_is_real_printed_length_and_vpos_is_only_gap(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)

    # This test specifically protects the rule that VPosMM must not be added
    # to actual_printed_length_m.
    log_path = write_log_file(
        tmp_path,
        "metric_rule_log.txt",
        make_valid_log_text(
            job_id="36005",
            height_mm="1101",
            vpos_mm="1054.5",
            print_height_mm="1101",
        ),
    )

    result = import_and_persist_log(
        path=log_path,
        repository=repo,
        raise_on_invalid=False,
    )

    job = result["job"]
    assert job is not None

    # Real printed length comes only from HeightMM
    assert job.actual_printed_length_m == pytest.approx(1.101, rel=1e-6)

    # Gap comes from VPosMM
    assert job.gap_before_m == pytest.approx(1.0545, rel=1e-6)

    # Total consumption can include both
    assert job.consumed_length_m == pytest.approx(2.1555, rel=1e-6)

    # Guard against the exact regression we want to avoid:
    assert job.actual_printed_length_m != pytest.approx(2.1555, rel=1e-6)