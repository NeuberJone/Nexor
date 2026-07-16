from __future__ import annotations

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pytest

import app as nexor_app
import exports.roll_export_service as roll_export_service
import storage.database as storage_database
from core.models import ProductionJob
from storage.repository import ProductionRepository


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_test_repository(tmp_path: Path) -> tuple[Path, ProductionRepository]:
    db_path = tmp_path / "test_app_cli.db"
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
    return db_path, repo


def patch_app_to_use_temp_db(monkeypatch, db_path: Path) -> None:
    class FixedRepo(ProductionRepository):
        def __init__(self, *args, **kwargs):
            super().__init__(db_path=db_path)

    monkeypatch.setattr(storage_database, "DB_PATH", db_path)
    monkeypatch.setattr(nexor_app, "ProductionRepository", FixedRepo)
    monkeypatch.setattr(roll_export_service, "ProductionRepository", FixedRepo)


def make_job(
    *,
    job_id: str,
    machine: str = "M1",
    fabric: str | None = "DRYFIT",
    document: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    actual_printed_length_m: float = 1.10,
    gap_before_m: float = 0.10,
) -> ProductionJob:
    start_time = start_time or datetime(2026, 3, 21, 8, 0, 0)
    end_time = end_time or datetime(2026, 3, 21, 8, 5, 0)
    document = document or f"{job_id} - dryfit - teste.jpeg"

    return ProductionJob(
        job_id=job_id,
        machine=machine,
        computer_name="DESKTOP-36UB5C9",
        document=document,
        start_time=start_time,
        end_time=end_time,
        duration_seconds=int((end_time - start_time).total_seconds()),
        fabric=fabric,
        planned_length_m=actual_printed_length_m,
        actual_printed_length_m=actual_printed_length_m,
        gap_before_m=gap_before_m,
        consumed_length_m=actual_printed_length_m + gap_before_m,
        source_path=f"C:/logs/{job_id}.txt",
    )


def create_closed_roll(repo: ProductionRepository) -> int:
    job_a = make_job(
        job_id="CLI_JOB_001",
        actual_printed_length_m=1.20,
        gap_before_m=0.10,
        start_time=datetime(2026, 3, 21, 8, 0, 0),
        end_time=datetime(2026, 3, 21, 8, 5, 0),
    )
    job_b = make_job(
        job_id="CLI_JOB_002",
        actual_printed_length_m=0.85,
        gap_before_m=0.15,
        start_time=datetime(2026, 3, 21, 8, 10, 0),
        end_time=datetime(2026, 3, 21, 8, 14, 0),
    )

    job_a_row_id = repo.save_job(job_a)
    job_b_row_id = repo.save_job(job_b)

    roll_id = repo.create_roll(
        machine="M1",
        fabric="DRYFIT",
        note="CLI test roll",
    )
    repo.add_job_to_roll(roll_id=roll_id, job_row_id=job_a_row_id)
    repo.add_job_to_roll(roll_id=roll_id, job_row_id=job_b_row_id)
    repo.close_roll(roll_id, note="Closed by CLI test")
    return roll_id


def test_app_list_rolls_outputs_summary(tmp_path: Path, monkeypatch, capsys) -> None:
    db_path, repo = create_test_repository(tmp_path)
    roll_id = create_closed_roll(repo)
    patch_app_to_use_temp_db(monkeypatch, db_path)

    monkeypatch.setattr(sys, "argv", ["app.py", "--list-rolls"])

    exit_code = nexor_app.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "NEXOR ROLLS" in output
    assert f"ID: {roll_id}" in output
    assert "Machine: M1" in output
    assert "Fabric: DRYFIT" in output
    assert "Jobs: 2" in output
    assert "CLI_JOB_001" in output
    assert "CLI_JOB_002" in output


def test_app_show_roll_id_outputs_detail(tmp_path: Path, monkeypatch, capsys) -> None:
    db_path, repo = create_test_repository(tmp_path)
    roll_id = create_closed_roll(repo)
    patch_app_to_use_temp_db(monkeypatch, db_path)

    monkeypatch.setattr(sys, "argv", ["app.py", "--show-roll-id", str(roll_id)])

    exit_code = nexor_app.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "NEXOR ROLL DETAIL" in output
    assert f"ID: {roll_id}" in output
    assert "Metric counts:" in output
    assert "Fabric totals:" in output
    assert "CLI_JOB_001" in output
    assert "CLI_JOB_002" in output
    assert "Review=PENDING_REVIEW" in output


def test_app_export_roll_id_creates_files(tmp_path: Path, monkeypatch, capsys) -> None:
    db_path, repo = create_test_repository(tmp_path)
    roll_id = create_closed_roll(repo)
    patch_app_to_use_temp_db(monkeypatch, db_path)

    output_dir = tmp_path / "exports_out"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "app.py",
            "--export-roll-id",
            str(roll_id),
            "--export-output-dir",
            str(output_dir),
        ],
    )

    exit_code = nexor_app.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "NEXOR ROLL EXPORT" in output
    assert "Status: EXPORTADO" in output
    assert "PDF:" in output
    assert "JPG:" in output

    pdf_path = output_dir / "M1_20260321_001.pdf"
    jpg_path = output_dir / "M1_20260321_001.jpg"

    assert pdf_path.exists()
    assert jpg_path.exists()


def test_app_export_nonexistent_roll_returns_error(tmp_path: Path, monkeypatch, capsys) -> None:
    db_path, _repo = create_test_repository(tmp_path)
    patch_app_to_use_temp_db(monkeypatch, db_path)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "app.py",
            "--export-roll-id",
            "9999",
            "--export-output-dir",
            str(tmp_path / "exports_out"),
        ],
    )

    exit_code = nexor_app.main()
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Status: ERRO" in output
    assert "Rolo não encontrado" in output