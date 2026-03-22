from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.models import ProductionJob
from storage.database import init_database
from storage.repository import ProductionRepository


def make_available_job(
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

    base_time = datetime.now().replace(microsecond=0, second=0)
    suffix = base_time.strftime("%Y%m%d%H%M")

    jobs = [
        make_available_job(
            job_id=f"AVAILABLE_JOB_{suffix}_001",
            machine="M1",
            fabric="DRYFIT",
            document=f"25-03 - dryfit - available team a {suffix}.jpeg",
            start_time=base_time,
            end_time=base_time + timedelta(minutes=5),
            actual_printed_length_m=1.10,
            gap_before_m=0.10,
            source_path=f"C:/bootstrap/AVAILABLE_JOB_{suffix}_001.txt",
        ),
        make_available_job(
            job_id=f"AVAILABLE_JOB_{suffix}_002",
            machine="M1",
            fabric="DRYFIT",
            document=f"25-03 - dryfit - available team b {suffix}.jpeg",
            start_time=base_time + timedelta(minutes=10),
            end_time=base_time + timedelta(minutes=14),
            actual_printed_length_m=0.95,
            gap_before_m=0.12,
            source_path=f"C:/bootstrap/AVAILABLE_JOB_{suffix}_002.txt",
        ),
        make_available_job(
            job_id=f"AVAILABLE_JOB_{suffix}_003",
            machine="M1",
            fabric="DRYFIT",
            document=f"25-03 - dryfit - available team c {suffix}.jpeg",
            start_time=base_time + timedelta(minutes=20),
            end_time=base_time + timedelta(minutes=25),
            actual_printed_length_m=1.35,
            gap_before_m=0.08,
            source_path=f"C:/bootstrap/AVAILABLE_JOB_{suffix}_003.txt",
        ),
    ]

    created_ids: list[int] = []
    for job in jobs:
        row_id = repo.save_job(job)
        created_ids.append(row_id)

    available_jobs = repo.list_available_jobs(machine="M1", fabric="DRYFIT")

    print("\nBOOTSTRAP AVAILABLE JOBS\n")
    print(f"Database: {db_path}")
    print(f"Jobs criados nesta execução: {len(created_ids)}\n")

    for row_id, job in zip(created_ids, jobs, strict=True):
        print(
            f"ID interno: {row_id} | "
            f"Job ID: {job.job_id} | "
            f"Machine: {job.machine} | "
            f"Fabric: {job.fabric} | "
            f"Effective: {job.actual_printed_length_m:.3f} m | "
            f"Gap: {job.gap_before_m:.3f} m | "
            f"Consumed: {job.consumed_length_m:.3f} m | "
            f"Doc: {job.document}"
        )

    print("\nJobs disponíveis atualmente para montagem:")
    if not available_jobs:
        print("Nenhum job disponível.")
    else:
        for job in available_jobs:
            print(
                f"ID={job.id} | Job={job.job_id} | Machine={job.machine} | "
                f"Fabric={job.fabric or '-'} | Review={job.review_status or '-'} | "
                f"PrintStatus={job.print_status or '-'} | "
                f"Effective={job.actual_printed_length_m:.3f}m | "
                f"Gap={job.gap_before_m:.3f}m | "
                f"Consumed={job.consumed_length_m:.3f}m | "
                f"Doc={job.document}"
            )

    print("\nBootstrap de jobs disponíveis concluído.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())