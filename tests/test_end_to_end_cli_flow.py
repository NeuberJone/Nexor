from __future__ import annotations

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import app as nexor_app
import cli.commands as cli_commands
import exports.roll_export_service as roll_export_service
import pytest
import storage.database as storage_database
from core.models import ProductionJob
from storage.repository import ProductionRepository


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_test_repository(tmp_path: Path) -> tuple[Path, ProductionRepository]:
    db_path = tmp_path / "test_end_to_end_cli_flow.db"
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
    monkeypatch.setattr(cli_commands, "ProductionRepository", FixedRepo)
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
    start_time = start_time or datetime(2026, 3, 22, 8, 0, 0)
    end_time = end_time or datetime(2026, 3, 22, 8, 5, 0)
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


def create_available_jobs(repo: ProductionRepository) -> list[int]:
    jobs = [
        make_job(
            job_id="E2E_JOB_001",
            actual_printed_length_m=1.20,
            gap_before_m=0.10,
            start_time=datetime(2026, 3, 22, 8, 0, 0),
            end_time=datetime(2026, 3, 22, 8, 5, 0),
        ),
        make_job(
            job_id="E2E_JOB_002",
            actual_printed_length_m=0.95,
            gap_before_m=0.12,
            start_time=datetime(2026, 3, 22, 8, 10, 0),
            end_time=datetime(2026, 3, 22, 8, 14, 0),
        ),
    ]
    return [repo.save_job(job) for job in jobs]


def run_app(monkeypatch, capsys, argv: list[str]) -> tuple[int, str]:
    monkeypatch.setattr(sys, "argv", argv)
    exit_code = nexor_app.main()
    output = capsys.readouterr().out
    return exit_code, output


def test_end_to_end_cli_flow(tmp_path: Path, monkeypatch, capsys) -> None:
    db_path, repo = create_test_repository(tmp_path)
    job_row_ids = create_available_jobs(repo)
    patch_app_to_use_temp_db(monkeypatch, db_path)

    # 1. List available jobs
    exit_code, output = run_app(monkeypatch, capsys, ["app.py", "--list-jobs"])
    assert exit_code == 0
    assert "NEXOR AVAILABLE JOBS" in output
    assert "E2E_JOB_001" in output
    assert "E2E_JOB_002" in output

    # 2. Create roll
    exit_code, output = run_app(
        monkeypatch,
        capsys,
        [
            "app.py",
            "--create-roll",
            "--roll-machine",
            "M1",
            "--roll-fabric",
            "DRYFIT",
            "--roll-note",
            "Rolo E2E",
        ],
    )
    assert exit_code == 0
    assert "NEXOR CREATE ROLL" in output
    assert "Status: CRIADO" in output

    rolls = repo.list_rolls(status="ALL")
    assert len(rolls) == 1
    roll_id = rolls[0].id
    assert roll_id is not None

    # 3. Add first job
    exit_code, output = run_app(
        monkeypatch,
        capsys,
        [
            "app.py",
            "--add-job-to-roll",
            "--target-roll-id",
            str(roll_id),
            "--job-row-id",
            str(job_row_ids[0]),
        ],
    )
    assert exit_code == 0
    assert "NEXOR ADD JOB TO ROLL" in output
    assert "Status: ADICIONADO" in output
    assert "E2E_JOB_001" in output

    # 4. Add second job
    exit_code, output = run_app(
        monkeypatch,
        capsys,
        [
            "app.py",
            "--add-job-to-roll",
            "--target-roll-id",
            str(roll_id),
            "--job-row-id",
            str(job_row_ids[1]),
        ],
    )
    assert exit_code == 0
    assert "Status: ADICIONADO" in output
    assert "E2E_JOB_002" in output

    # 5. Show roll detail while open
    exit_code, output = run_app(
        monkeypatch,
        capsys,
        ["app.py", "--show-roll-id", str(roll_id)],
    )
    assert exit_code == 0
    assert "NEXOR ROLL DETAIL" in output
    assert f"ID: {roll_id}" in output
    assert "Jobs: 2" in output
    assert "E2E_JOB_001" in output
    assert "E2E_JOB_002" in output
    assert "Status: OPEN" in output

    # 6. Close roll
    exit_code, output = run_app(
        monkeypatch,
        capsys,
        [
            "app.py",
            "--close-roll-id",
            str(roll_id),
            "--close-note",
            "Fechado E2E",
        ],
    )
    assert exit_code == 0
    assert "NEXOR CLOSE ROLL" in output
    assert "Status: FECHADO" in output
    assert "Status: CLOSED" in output

    # 7. Export roll
    output_dir = tmp_path / "exports_out"
    exit_code, output = run_app(
        monkeypatch,
        capsys,
        [
            "app.py",
            "--export-roll-id",
            str(roll_id),
            "--export-output-dir",
            str(output_dir),
        ],
    )
    assert exit_code == 0
    assert "NEXOR ROLL EXPORT" in output
    assert "Status: EXPORTADO" in output
    assert "PDF:" in output
    assert "JPG:" in output

    # 8. Final repository assertions
    final_roll = repo.get_roll(roll_id=roll_id)
    assert final_roll is not None
    assert final_roll.status == "EXPORTED"
    assert final_roll.closed_at is not None
    assert final_roll.exported_at is not None
    assert "Fechado E2E" in (final_roll.note or "")

    summary = repo.get_roll_summary(roll_id)
    assert summary["jobs_count"] == 2
    assert summary["total_effective_m"] == pytest.approx(2.15, rel=1e-6)
    assert summary["total_gap_m"] == pytest.approx(0.22, rel=1e-6)
    assert summary["total_consumed_m"] == pytest.approx(2.37, rel=1e-6)

    expected_pdf = output_dir / f"{final_roll.roll_name}.pdf"
    expected_jpg = output_dir / f"{final_roll.roll_name}.jpg"
    assert expected_pdf.exists()
    assert expected_jpg.exists()

    # 9. No jobs should remain available after assignment
    exit_code, output = run_app(monkeypatch, capsys, ["app.py", "--list-jobs"])
    assert exit_code == 0
    assert "Nenhum job disponível para montagem de rolo." in output