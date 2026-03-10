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
        Tamanho planejado/original do arquivo enviado para impressão.

    printed_length_m:
        Quanto realmente saiu da máquina.

    gap_before_m:
        Avanço técnico antes da impressão.

    Regras importantes:
    - planned_length_m representa o tamanho do job/arquivo.
    - printed_length_m representa a metragem efetivamente impressa.
    - um job pode existir no histórico e ainda assim não contar como produção válida.
    - um job pode ser excluído do resumo de tecido e do roll export sem ser apagado.
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
    printed_length_m: float
    gap_before_m: float

    driver: str | None = None
    source_path: str | None = None

    # Classificação operacional
    job_type: str = "UNKNOWN"   # PRODUCTION | REPRINT | TEST | UNKNOWN
    is_rework: bool = False
    notes: str | None = None

    # Status de impressão / qualidade do job
    print_status: str = "OK"    # OK | STAINED | FAILED | CANCELED | TEST

    # Regras de contagem operacional
    counts_as_valid_production: bool = True
    counts_for_fabric_summary: bool = True
    counts_for_roll_export: bool = True

    # Motivo operacional do problema, se houver
    error_reason: str | None = None

    @property
    def total_consumption_m(self) -> float:
        """
        Consumo operacional total do job.
        Metragem realmente impressa + espaço técnico antes.
        """
        return self.printed_length_m + self.gap_before_m


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