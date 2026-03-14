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

    planned_length_m:
        Tamanho planejado/original do arquivo enviado.

    consumed_length_m:
        Quanto a máquina efetivamente consumiu segundo o log de custo.
        Em muitos casos isso já inclui o avanço técnico anterior.

    gap_before_m:
        Avanço técnico antes da impressão.

    actual_printed_length_m:
        Quanto realmente corresponde à arte impressa.
        Regra:
            actual_printed_length_m = max(consumed_length_m - gap_before_m, 0)
    """

    job_id: str
    machine: str
    computer_name: str
    document: str

    start_time: datetime
    end_time: datetime
    duration_seconds: int

    fabric: str | None

    planned_length_m: float
    consumed_length_m: float
    gap_before_m: float

    driver: str | None = None
    source_path: str | None = None

    job_type: str = "UNKNOWN"
    is_rework: bool = False
    notes: str | None = None

    print_status: str = "OK"

    counts_as_valid_production: bool = True
    counts_for_fabric_summary: bool = True
    counts_for_roll_export: bool = True

    error_reason: str | None = None

    @property
    def actual_printed_length_m(self) -> float:
        value = self.consumed_length_m - self.gap_before_m
        return value if value > 0 else 0.0

    @property
    def total_consumption_m(self) -> float:
        return self.consumed_length_m


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