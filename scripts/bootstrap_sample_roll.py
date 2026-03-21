from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

# Garante que a raiz do projeto entre no sys.path quando o script for executado
# diretamente via: python scripts/bootstrap_sample_roll.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.models import ProductionJob
from storage.database import init_database
from storage.repository import ProductionRepository


def make_sample_job(
    *,
    job_id: str,
    machine: str,
    fabric: str,
    document: str,
    start_time: datetime,
    end_time: datetime,
    actual_printed_length_m: float,
    gap_before_m: float,
    source_path: str,
) -> ProductionJob:
    return ProductionJob(
        job_id=job_id,
        machine=machine,
        computer_name="DESKTOP-36UB5C9" if machine == "M1" else "DESKTOP-2GGH09O",
        document=document,
        start_time=start_time,
        end_time=end_time,
        duration_seconds=int((end_time - start_time).total_seconds()),
        fabric=fabric,
        planned_length_m=actual_printed_length_m,
        actual_printed_length_m=actual_printed_length_m,
        gap_before_m=gap_before_m,
        consumed_length_m=actual_printed_length_m + gap_before_m,
        source_path=source_path,
    )


def main() -> int:
    db_path = init_database()
    repo = ProductionRepository(db_path=db_path)

    job_a = make_sample_job(
        job_id="BOOTSTRAP_JOB_001",
        machine="M1",
        fabric="DRYFIT",
        document="24-03 - dryfit - sample team a.jpeg",
        start_time=datetime(2026, 3, 21, 8, 0, 0),
        end_time=datetime(2026, 3, 21, 8, 5, 0),
        actual_printed_length_m=1.20,
        gap_before_m=0.10,
        source_path="C:/bootstrap/BOOTSTRAP_JOB_001.txt",
    )

    job_b = make_sample_job(
        job_id="BOOTSTRAP_JOB_002",
        machine="M1",
        fabric="DRYFIT",
        document="24-03 - dryfit - sample team b.jpeg",
        start_time=datetime(2026, 3, 21, 8, 10, 0),
        end_time=datetime(2026, 3, 21, 8, 14, 0),
        actual_printed_length_m=0.85,
        gap_before_m=0.15,
        source_path="C:/bootstrap/BOOTSTRAP_JOB_002.txt",
    )

    job_a_row_id = repo.save_job(job_a)
    job_b_row_id = repo.save_job(job_b)

    roll_id = repo.create_roll(
        machine="M1",
        fabric="DRYFIT",
        note="Bootstrap sample roll",
    )

    repo.add_job_to_roll(roll_id=roll_id, job_row_id=job_a_row_id)
    repo.add_job_to_roll(roll_id=roll_id, job_row_id=job_b_row_id)
    repo.close_roll(roll_id, note="Closed by bootstrap script")

    roll = repo.get_roll(roll_id=roll_id)
    summary = repo.get_roll_summary(roll_id)

    print("\nBOOTSTRAP SAMPLE ROLL\n")
    print(f"Database: {db_path}")
    print(f"Roll ID: {roll_id}")
    print(f"Roll Name: {roll.roll_name if roll else '-'}")
    print(f"Machine: {roll.machine if roll else '-'}")
    print(f"Fabric: {roll.fabric if roll else '-'}")
    print(f"Status: {roll.status if roll else '-'}")
    print(f"Jobs: {summary['jobs_count']}")
    print(f"Total planned (m): {summary['total_planned_m']:.3f}")
    print(f"Total effective (m): {summary['total_effective_m']:.3f}")
    print(f"Total gap (m): {summary['total_gap_m']:.3f}")
    print(f"Total consumed (m): {summary['total_consumed_m']:.3f}")
    print("\nSample roll created successfully.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())