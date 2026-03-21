from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from core.models import ProductionJob, ROLL_CLOSED, ROLL_EXPORTED, ROLL_OPEN
from storage.repository import ProductionRepository

# O serviço ainda vai ser criado no próximo passo.
# Este teste define o contrato esperado.
from exports.roll_export_service import export_closed_roll


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_test_repository(tmp_path: Path) -> ProductionRepository:
    db_path = tmp_path / "test_roll_export.db"
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


def create_closed_roll_with_one_job(repo: ProductionRepository) -> int:
    job_row_id = persist_job(repo, make_job(job_id="JOB_EXPORT_001"))
    roll_id = repo.create_roll(machine="M1", fabric="DRYFIT", note="Rolo para exportação")
    repo.add_job_to_roll(roll_id=roll_id, job_row_id=job_row_id)
    repo.close_roll(roll_id, note="Fechado para exportação")
    return roll_id


def test_export_closed_roll_creates_pdf_and_jpg_and_marks_exported(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)
    output_dir = tmp_path / "exports"
    roll_id = create_closed_roll_with_one_job(repo)

    roll_before = repo.get_roll(roll_id=roll_id)
    assert roll_before is not None
    assert roll_before.status == ROLL_CLOSED

    result = export_closed_roll(
        roll_id=roll_id,
        output_dir=output_dir,
        repository=repo,
    )

    assert isinstance(result, dict)
    assert result["roll_id"] == roll_id
    assert result["roll_name"]
    assert result["pdf_path"]
    assert result["jpg_path"]

    pdf_path = Path(result["pdf_path"])
    jpg_path = Path(result["jpg_path"])

    assert pdf_path.exists()
    assert jpg_path.exists()
    assert pdf_path.suffix.lower() == ".pdf"
    assert jpg_path.suffix.lower() in {".jpg", ".jpeg"}

    assert pdf_path.parent == output_dir
    assert jpg_path.parent == output_dir

    roll_after = repo.get_roll(roll_id=roll_id)
    assert roll_after is not None
    assert roll_after.status == ROLL_EXPORTED
    assert roll_after.exported_at is not None


def test_export_nonexistent_roll_raises_value_error(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)
    output_dir = tmp_path / "exports"

    with pytest.raises(ValueError, match="Rolo não encontrado|Roll not found"):
        export_closed_roll(
            roll_id=9999,
            output_dir=output_dir,
            repository=repo,
        )


def test_export_open_roll_is_blocked(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)
    output_dir = tmp_path / "exports"

    roll_id = repo.create_roll(machine="M1", fabric="DRYFIT")

    roll = repo.get_roll(roll_id=roll_id)
    assert roll is not None
    assert roll.status == ROLL_OPEN

    with pytest.raises(ValueError, match="fechado|closed"):
        export_closed_roll(
            roll_id=roll_id,
            output_dir=output_dir,
            repository=repo,
        )


def test_export_empty_roll_is_blocked_even_if_status_is_forced_closed(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)
    output_dir = tmp_path / "exports"

    roll_id = repo.create_roll(machine="M1", fabric="DRYFIT")

    # Força o estado fechado diretamente no banco para validar que o serviço
    # não deve confiar apenas no status visual/persistido do cabeçalho.
    with repo.connect() as conn:
        conn.execute(
            """
            UPDATE rolls
            SET status = ?, closed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (ROLL_CLOSED, roll_id),
        )
        conn.commit()

    with pytest.raises(ValueError, match="vazio|empty|sem itens|no items"):
        export_closed_roll(
            roll_id=roll_id,
            output_dir=output_dir,
            repository=repo,
        )


def test_export_uses_persisted_roll_data_and_returns_summary_totals(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)
    output_dir = tmp_path / "exports"

    job_a = make_job(
        job_id="JOB_EXPORT_A",
        actual_printed_length_m=1.20,
        gap_before_m=0.10,
        start_time=datetime(2026, 3, 20, 8, 0, 0),
        end_time=datetime(2026, 3, 20, 8, 4, 0),
    )
    job_b = make_job(
        job_id="JOB_EXPORT_B",
        actual_printed_length_m=0.80,
        gap_before_m=0.20,
        start_time=datetime(2026, 3, 20, 9, 0, 0),
        end_time=datetime(2026, 3, 20, 9, 3, 0),
    )

    job_a_row_id = persist_job(repo, job_a)
    job_b_row_id = persist_job(repo, job_b)

    roll_id = repo.create_roll(machine="M1", fabric="DRYFIT")
    repo.add_job_to_roll(roll_id=roll_id, job_row_id=job_a_row_id)
    repo.add_job_to_roll(roll_id=roll_id, job_row_id=job_b_row_id)
    repo.close_roll(roll_id)

    result = export_closed_roll(
        roll_id=roll_id,
        output_dir=output_dir,
        repository=repo,
    )

    assert result["jobs_count"] == 2
    assert result["total_effective_m"] == pytest.approx(2.0, rel=1e-6)
    assert result["total_gap_m"] == pytest.approx(0.3, rel=1e-6)
    assert result["total_consumed_m"] == pytest.approx(2.3, rel=1e-6)