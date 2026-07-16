from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from core.models import ProductionJob, ROLL_CLOSED, ROLL_OPEN
from storage.repository import ProductionRepository


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_test_repository(tmp_path: Path) -> ProductionRepository:
    db_path = tmp_path / "test_rolls.db"
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
    start_time = start_time or datetime(2026, 3, 20, 8, 0, 0)
    end_time = end_time or datetime(2026, 3, 20, 8, 5, 0)
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


def persist_job(repo: ProductionRepository, job: ProductionJob) -> int:
    row_id = repo.save_job(job)
    assert row_id > 0
    return row_id


def test_create_roll_successfully(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)

    roll_id = repo.create_roll(machine="M1", fabric="DRYFIT", note="Primeiro rolo")
    roll = repo.get_roll(roll_id=roll_id)

    assert roll is not None
    assert roll.id == roll_id
    assert roll.machine == "M1"
    assert roll.fabric == "DRYFIT"
    assert roll.status == ROLL_OPEN
    assert roll.note == "Primeiro rolo"


def test_add_job_to_roll_successfully(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)

    job_row_id = persist_job(repo, make_job(job_id="JOB001"))
    roll_id = repo.create_roll(machine="M1", fabric="DRYFIT")

    item_id = repo.add_job_to_roll(roll_id=roll_id, job_row_id=job_row_id)
    items = repo.list_roll_items(roll_id)

    assert item_id > 0
    assert len(items) == 1
    assert items[0].job_row_id == job_row_id
    assert items[0].job_id == "JOB001"
    assert items[0].machine == "M1"
    assert items[0].fabric == "DRYFIT"


def test_prevent_same_job_in_two_rolls(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)

    job_row_id = persist_job(repo, make_job(job_id="JOB002"))
    roll_a = repo.create_roll(machine="M1", fabric="DRYFIT")
    roll_b = repo.create_roll(machine="M1", fabric="DRYFIT")

    repo.add_job_to_roll(roll_id=roll_a, job_row_id=job_row_id)

    with pytest.raises(ValueError, match="já pertence ao rolo"):
        repo.add_job_to_roll(roll_id=roll_b, job_row_id=job_row_id)


def test_block_job_with_incompatible_machine(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)

    job_row_id = persist_job(repo, make_job(job_id="JOB003", machine="M2"))
    roll_id = repo.create_roll(machine="M1", fabric="DRYFIT")

    with pytest.raises(ValueError, match="Máquina incompatível"):
        repo.add_job_to_roll(roll_id=roll_id, job_row_id=job_row_id)


def test_block_job_with_incompatible_fabric(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)

    job_row_id = persist_job(repo, make_job(job_id="JOB004", fabric="ELASTANO"))
    roll_id = repo.create_roll(machine="M1", fabric="DRYFIT")

    with pytest.raises(ValueError, match="Tecido incompatível"):
        repo.add_job_to_roll(roll_id=roll_id, job_row_id=job_row_id)


def test_prevent_closing_empty_roll(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)

    roll_id = repo.create_roll(machine="M1", fabric="DRYFIT")

    with pytest.raises(ValueError, match="rolo vazio"):
        repo.close_roll(roll_id)


def test_close_roll_with_valid_item(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)

    job_row_id = persist_job(repo, make_job(job_id="JOB005"))
    roll_id = repo.create_roll(machine="M1", fabric="DRYFIT")

    repo.add_job_to_roll(roll_id=roll_id, job_row_id=job_row_id)
    repo.close_roll(roll_id, note="Fechamento de teste")

    roll = repo.get_roll(roll_id=roll_id)
    assert roll is not None
    assert roll.status == ROLL_CLOSED
    assert roll.closed_at is not None
    assert "Fechamento de teste" in (roll.note or "")


def test_prevent_changes_after_roll_is_closed(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)

    job_a_row_id = persist_job(repo, make_job(job_id="JOB006"))
    job_b_row_id = persist_job(
        repo,
        make_job(
            job_id="JOB007",
            start_time=datetime(2026, 3, 20, 9, 0, 0),
            end_time=datetime(2026, 3, 20, 9, 5, 0),
        ),
    )

    roll_id = repo.create_roll(machine="M1", fabric="DRYFIT")
    repo.add_job_to_roll(roll_id=roll_id, job_row_id=job_a_row_id)
    repo.close_roll(roll_id)

    with pytest.raises(ValueError, match="não está em aberto"):
        repo.add_job_to_roll(roll_id=roll_id, job_row_id=job_b_row_id)

    with pytest.raises(ValueError, match="não está em aberto"):
        repo.remove_job_from_roll(roll_id=roll_id, job_row_id=job_a_row_id)