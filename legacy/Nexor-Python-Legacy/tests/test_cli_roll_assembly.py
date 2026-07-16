from __future__ import annotations

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import app as nexor_app
import cli.commands as cli_commands
import pytest
import storage.database as storage_database
from core.models import ProductionJob, ROLL_CLOSED, ROLL_OPEN
from storage.repository import ProductionRepository


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_test_repository(tmp_path: Path) -> tuple[Path, ProductionRepository]:
    db_path = tmp_path / "test_cli_roll_assembly.db"
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
    job_a = make_job(
        job_id="ASSEMBLY_JOB_001",
        actual_printed_length_m=1.20,
        gap_before_m=0.10,
        start_time=datetime(2026, 3, 22, 8, 0, 0),
        end_time=datetime(2026, 3, 22, 8, 5, 0),
    )
    job_b = make_job(
        job_id="ASSEMBLY_JOB_002",
        actual_printed_length_m=0.95,
        gap_before_m=0.12,
        start_time=datetime(2026, 3, 22, 8, 10, 0),
        end_time=datetime(2026, 3, 22, 8, 14, 0),
    )
    return [repo.save_job(job_a), repo.save_job(job_b)]


def test_cli_list_jobs_outputs_available_jobs(tmp_path: Path, monkeypatch, capsys) -> None:
    db_path, repo = create_test_repository(tmp_path)
    job_ids = create_available_jobs(repo)
    patch_app_to_use_temp_db(monkeypatch, db_path)

    monkeypatch.setattr(sys, "argv", ["app.py", "--list-jobs"])

    exit_code = nexor_app.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "NEXOR AVAILABLE JOBS" in output
    assert "Jobs disponíveis: 2" in output
    assert f"ID={job_ids[0]}" in output
    assert f"ID={job_ids[1]}" in output
    assert "ASSEMBLY_JOB_001" in output
    assert "ASSEMBLY_JOB_002" in output


def test_cli_create_roll_creates_open_roll(tmp_path: Path, monkeypatch, capsys) -> None:
    db_path, repo = create_test_repository(tmp_path)
    patch_app_to_use_temp_db(monkeypatch, db_path)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "app.py",
            "--create-roll",
            "--roll-machine",
            "M1",
            "--roll-fabric",
            "DRYFIT",
            "--roll-note",
            "Rolo criado por teste",
        ],
    )

    exit_code = nexor_app.main()
    output = capsys.readouterr().out

    rolls = repo.list_rolls(status="ALL")

    assert exit_code == 0
    assert "NEXOR CREATE ROLL" in output
    assert "Status: CRIADO" in output
    assert len(rolls) == 1
    assert rolls[0].machine == "M1"
    assert rolls[0].fabric == "DRYFIT"
    assert rolls[0].status == ROLL_OPEN
    assert "Rolo criado por teste" in (rolls[0].note or "")


def test_cli_add_job_to_roll_updates_roll_summary(tmp_path: Path, monkeypatch, capsys) -> None:
    db_path, repo = create_test_repository(tmp_path)
    [job_row_id, _] = create_available_jobs(repo)
    roll_id = repo.create_roll(machine="M1", fabric="DRYFIT", note="Teste add")
    patch_app_to_use_temp_db(monkeypatch, db_path)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "app.py",
            "--add-job-to-roll",
            "--target-roll-id",
            str(roll_id),
            "--job-row-id",
            str(job_row_id),
        ],
    )

    exit_code = nexor_app.main()
    output = capsys.readouterr().out
    summary = repo.get_roll_summary(roll_id)

    assert exit_code == 0
    assert "NEXOR ADD JOB TO ROLL" in output
    assert "Status: ADICIONADO" in output
    assert summary["jobs_count"] == 1
    assert summary["total_effective_m"] == pytest.approx(1.20, rel=1e-6)
    assert summary["total_gap_m"] == pytest.approx(0.10, rel=1e-6)
    assert summary["total_consumed_m"] == pytest.approx(1.30, rel=1e-6)


def test_cli_remove_job_from_roll_removes_item(tmp_path: Path, monkeypatch, capsys) -> None:
    db_path, repo = create_test_repository(tmp_path)
    [job_row_id, _] = create_available_jobs(repo)
    roll_id = repo.create_roll(machine="M1", fabric="DRYFIT", note="Teste remove")
    repo.add_job_to_roll(roll_id=roll_id, job_row_id=job_row_id)
    patch_app_to_use_temp_db(monkeypatch, db_path)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "app.py",
            "--remove-job-from-roll",
            "--target-roll-id",
            str(roll_id),
            "--job-row-id",
            str(job_row_id),
        ],
    )

    exit_code = nexor_app.main()
    output = capsys.readouterr().out
    summary = repo.get_roll_summary(roll_id)

    assert exit_code == 0
    assert "NEXOR REMOVE JOB FROM ROLL" in output
    assert "Status: REMOVIDO" in output
    assert summary["jobs_count"] == 0


def test_cli_close_roll_changes_status_to_closed(tmp_path: Path, monkeypatch, capsys) -> None:
    db_path, repo = create_test_repository(tmp_path)
    [job_row_id, _] = create_available_jobs(repo)
    roll_id = repo.create_roll(machine="M1", fabric="DRYFIT", note="Teste close")
    repo.add_job_to_roll(roll_id=roll_id, job_row_id=job_row_id)
    patch_app_to_use_temp_db(monkeypatch, db_path)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "app.py",
            "--close-roll-id",
            str(roll_id),
            "--close-note",
            "Fechado no teste",
        ],
    )

    exit_code = nexor_app.main()
    output = capsys.readouterr().out
    roll = repo.get_roll(roll_id=roll_id)

    assert exit_code == 0
    assert "NEXOR CLOSE ROLL" in output
    assert "Status: FECHADO" in output
    assert roll is not None
    assert roll.status == ROLL_CLOSED
    assert "Fechado no teste" in (roll.note or "")


def test_cli_close_empty_roll_returns_error(tmp_path: Path, monkeypatch, capsys) -> None:
    db_path, repo = create_test_repository(tmp_path)
    roll_id = repo.create_roll(machine="M1", fabric="DRYFIT", note="Vazio")
    patch_app_to_use_temp_db(monkeypatch, db_path)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "app.py",
            "--close-roll-id",
            str(roll_id),
        ],
    )

    exit_code = nexor_app.main()
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "NEXOR CLOSE ROLL" in output
    assert "Status: ERRO" in output
    assert "rolo vazio" in output.lower()


def test_cli_add_assigned_job_to_another_roll_returns_error(tmp_path: Path, monkeypatch, capsys) -> None:
    db_path, repo = create_test_repository(tmp_path)
    [job_row_id, _] = create_available_jobs(repo)

    roll_a = repo.create_roll(machine="M1", fabric="DRYFIT", note="Rolo A")
    roll_b = repo.create_roll(machine="M1", fabric="DRYFIT", note="Rolo B")
    repo.add_job_to_roll(roll_id=roll_a, job_row_id=job_row_id)

    patch_app_to_use_temp_db(monkeypatch, db_path)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "app.py",
            "--add-job-to-roll",
            "--target-roll-id",
            str(roll_b),
            "--job-row-id",
            str(job_row_id),
        ],
    )

    exit_code = nexor_app.main()
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "NEXOR ADD JOB TO ROLL" in output
    assert "Status: ERRO" in output
    assert "já está atribuído a um rolo" in output