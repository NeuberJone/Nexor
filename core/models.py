from dataclasses import dataclass
from datetime import datetime


@dataclass
class Machine:
    """
    Representa uma máquina de impressão registrada no sistema.
    """
    machine_id: str
    name: str
    computer_name: str
    model: str | None = None


@dataclass
class ProductionJob:
    """
    Registro estruturado de um job de impressão.
    """

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
        Consumo operacional total do job.
        Comprimento impresso + espaço técnico antes.
        """
        return self.length_m + self.gap_before_m


@dataclass
class LogSource:
    """
    Fonte de logs cadastrada no Nexor.
    Pode ser uma pasta local ou de rede.
    """

    id: int | None
    name: str
    path: str

    recursive: bool = True
    enabled: bool = True

    machine_hint: str | None = None


@dataclass
class ImportRun:
    """
    Execução de importação de logs.
    """

    id: int | None
    source_id: int

    started_at: datetime
    finished_at: datetime | None = None

    total_found: int = 0
    imported_count: int = 0
    duplicate_count: int = 0
    error_count: int = 0

    notes: str | None = None