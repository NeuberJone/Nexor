from dataclasses import dataclass
from datetime import datetime


@dataclass
class Machine:
    machine_id: str
    name: str
    computer_name: str
    model: str | None = None


@dataclass
class ProductionJob:
    job_id: str
    machine: str
    computer_name: str
    document: str
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    fabric: str | None
    length_m: float
    gap_before_m: float
    driver: str | None = None
    source_path: str | None = None

    @property
    def total_consumption_m(self) -> float:
        """
        Operational metric: printed length + technical gap.
        """
        return self.length_m + self.gap_before_m