"""
Módulo de Planejamento de Produção

Implementa lógica de agendamento de jobs, alocação de máquinas,
cálculo de previsão de conclusão e otimização de sequência.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import json


@dataclass
class Job:
    """Representa um job de produção"""
    id: int
    document: str
    fabric: str
    planned_length_m: float
    machine_code: str
    priority: int = 0
    created_at: str = ""


@dataclass
class MachineCapacity:
    """Capacidade de uma máquina"""
    code: str
    name: str
    speed_m_per_hour: float = 100.0  # metros por hora
    setup_time_minutes: int = 30  # tempo de setup entre jobs
    available_from: datetime = None
    current_load: float = 0.0  # metros já alocados


@dataclass
class ScheduledJob:
    """Job agendado em uma máquina"""
    job_id: int
    machine_code: str
    start_time: datetime
    end_time: datetime
    setup_time_minutes: int
    processing_time_minutes: float
    total_time_minutes: float
    fabric: str
    planned_length_m: float


class ProductionPlanner:
    """Planejador de produção com otimização"""

    def __init__(self):
        self.machines: Dict[str, MachineCapacity] = {}
        self.jobs: List[Job] = []
        self.schedule: List[ScheduledJob] = []

    def add_machine(self, code: str, name: str, speed_m_per_hour: float = 100.0):
        """Adiciona uma máquina ao planejador"""
        self.machines[code] = MachineCapacity(
            code=code,
            name=name,
            speed_m_per_hour=speed_m_per_hour,
            available_from=datetime.now(),
        )

    def add_job(self, job: Job):
        """Adiciona um job ao planejador"""
        self.jobs.append(job)

    def add_jobs(self, jobs: List[Job]):
        """Adiciona múltiplos jobs"""
        self.jobs.extend(jobs)

    def calculate_processing_time(
        self, length_m: float, machine_code: str
    ) -> float:
        """Calcula tempo de processamento em minutos"""
        if machine_code not in self.machines:
            return 0.0

        machine = self.machines[machine_code]
        hours = length_m / machine.speed_m_per_hour
        return hours * 60  # converter para minutos

    def allocate_job_to_machine(
        self, job: Job, machine_code: str, max_capacity_m: float = 1000.0
    ) -> Optional[ScheduledJob]:
        """Aloca um job a uma máquina com validação de capacidade"""
        if machine_code not in self.machines:
            return None

        machine = self.machines[machine_code]
        
        # Validar capacidade
        if machine.current_load + job.planned_length_m > max_capacity_m:
            return None  # Máquina está no limite de capacidade

        # Calcular tempos
        setup_time = machine.setup_time_minutes
        processing_time = self.calculate_processing_time(
            job.planned_length_m, machine_code
        )
        total_time = setup_time + processing_time

        # Determinar horário de início
        start_time = machine.available_from
        end_time = start_time + timedelta(minutes=total_time)

        # Criar job agendado
        scheduled = ScheduledJob(
            job_id=job.id,
            machine_code=machine_code,
            start_time=start_time,
            end_time=end_time,
            setup_time_minutes=setup_time,
            processing_time_minutes=processing_time,
            total_time_minutes=total_time,
            fabric=job.fabric,
            planned_length_m=job.planned_length_m,
        )

        # Atualizar disponibilidade da máquina
        machine.available_from = end_time
        machine.current_load += job.planned_length_m

        self.schedule.append(scheduled)
        return scheduled

    def plan_jobs(self, jobs: List[Job]) -> List[ScheduledJob]:
        """Planeja múltiplos jobs usando estratégia greedy"""
        self.schedule = []

        # Resetar máquinas
        for machine in self.machines.values():
            machine.available_from = datetime.now()
            machine.current_load = 0.0

        # Ordenar jobs por prioridade e tamanho
        sorted_jobs = sorted(
            jobs, key=lambda j: (-j.priority, -j.planned_length_m)
        )

        # Alocar cada job à máquina mais disponível
        for job in sorted_jobs:
            # Encontrar máquina com menor tempo de disponibilidade
            best_machine = min(
                self.machines.values(),
                key=lambda m: m.available_from,
            )

            self.allocate_job_to_machine(job, best_machine.code)

        return self.schedule

    def optimize_sequence(self, jobs: List[Job]) -> List[Job]:
        """Otimiza sequência de jobs para minimizar tempo total"""
        # Estratégia: agrupar por tecido para minimizar setups
        fabric_groups = {}

        for job in jobs:
            if job.fabric not in fabric_groups:
                fabric_groups[job.fabric] = []
            fabric_groups[job.fabric].append(job)

        # Ordenar grupos por tamanho total (maior primeiro)
        sorted_groups = sorted(
            fabric_groups.values(),
            key=lambda group: sum(j.planned_length_m for j in group),
            reverse=True,
        )

        # Flatten grupos mantendo ordem
        optimized = []
        for group in sorted_groups:
            # Ordenar jobs dentro do grupo por tamanho (maior primeiro)
            sorted_group = sorted(group, key=lambda j: -j.planned_length_m)
            optimized.extend(sorted_group)

        return optimized

    def get_schedule_summary(self) -> Dict[str, Any]:
        """Retorna resumo do planejamento"""
        if not self.schedule:
            return {
                "total_jobs": 0,
                "total_length_m": 0,
                "total_time_hours": 0,
                "estimated_completion": None,
                "machines_utilized": 0,
            }

        total_length = sum(s.planned_length_m for s in self.schedule)
        total_time = max(s.end_time for s in self.schedule) - min(
            s.start_time for s in self.schedule
        )
        machines_used = len(set(s.machine_code for s in self.schedule))

        return {
            "total_jobs": len(self.schedule),
            "total_length_m": round(total_length, 2),
            "total_time_hours": round(total_time.total_seconds() / 3600, 2),
            "estimated_completion": max(
                s.end_time for s in self.schedule
            ).isoformat(),
            "machines_utilized": machines_used,
        }

    def get_machine_timeline(self, machine_code: str) -> List[Dict[str, Any]]:
        """Retorna timeline de uma máquina"""
        machine_jobs = [s for s in self.schedule if s.machine_code == machine_code]
        machine_jobs.sort(key=lambda j: j.start_time)

        timeline = []
        for job in machine_jobs:
            timeline.append(
                {
                    "job_id": job.job_id,
                    "fabric": job.fabric,
                    "start_time": job.start_time.isoformat(),
                    "end_time": job.end_time.isoformat(),
                    "setup_time_minutes": job.setup_time_minutes,
                    "processing_time_minutes": round(job.processing_time_minutes, 2),
                    "total_time_minutes": round(job.total_time_minutes, 2),
                    "planned_length_m": job.planned_length_m,
                }
            )

        return timeline

    def get_all_timelines(self) -> Dict[str, List[Dict[str, Any]]]:
        """Retorna timelines de todas as máquinas"""
        result = {}
        for machine_code in self.machines.keys():
            result[machine_code] = self.get_machine_timeline(machine_code)
        return result

    def export_schedule(self) -> List[Dict[str, Any]]:
        """Exporta schedule em formato JSON"""
        return [
            {
                "job_id": s.job_id,
                "machine_code": s.machine_code,
                "start_time": s.start_time.isoformat(),
                "end_time": s.end_time.isoformat(),
                "setup_time_minutes": s.setup_time_minutes,
                "processing_time_minutes": round(s.processing_time_minutes, 2),
                "total_time_minutes": round(s.total_time_minutes, 2),
                "fabric": s.fabric,
                "planned_length_m": s.planned_length_m,
            }
            for s in self.schedule
        ]

    def get_utilization_report(self) -> Dict[str, Any]:
        """Retorna relatório de utilização de máquinas"""
        if not self.schedule:
            return {}

        total_time = max(s.end_time for s in self.schedule) - min(
            s.start_time for s in self.schedule
        )
        total_minutes = total_time.total_seconds() / 60

        report = {}
        for machine_code, machine in self.machines.items():
            machine_jobs = [s for s in self.schedule if s.machine_code == machine_code]

            if not machine_jobs:
                report[machine_code] = {
                    "name": machine.name,
                    "jobs_count": 0,
                    "total_length_m": 0,
                    "total_processing_time_minutes": 0,
                    "utilization_percent": 0,
                }
                continue

            total_processing = sum(s.processing_time_minutes for s in machine_jobs)
            utilization = (total_processing / total_minutes * 100) if total_minutes > 0 else 0

            report[machine_code] = {
                "name": machine.name,
                "jobs_count": len(machine_jobs),
                "total_length_m": round(machine.current_load, 2),
                "total_processing_time_minutes": round(total_processing, 2),
                "utilization_percent": round(utilization, 2),
            }

        return report

    def calculate_gaps(self) -> Dict[str, Any]:
        """Calcula gaps (lacunas) entre jobs em cada máquina"""
        gaps_report = {}
        
        for machine_code, machine in self.machines.items():
            machine_jobs = sorted(
                [s for s in self.schedule if s.machine_code == machine_code],
                key=lambda j: j.start_time
            )
            
            if len(machine_jobs) < 2:
                gaps_report[machine_code] = {
                    "name": machine.name,
                    "gaps": [],
                    "total_gap_minutes": 0,
                }
                continue
            
            gaps = []
            total_gap = 0
            
            for i in range(len(machine_jobs) - 1):
                current_job = machine_jobs[i]
                next_job = machine_jobs[i + 1]
                
                gap_duration = (next_job.start_time - current_job.end_time).total_seconds() / 60
                
                if gap_duration > 0:
                    gaps.append({
                        "from_job_id": current_job.job_id,
                        "to_job_id": next_job.job_id,
                        "gap_minutes": round(gap_duration, 2),
                        "from_time": current_job.end_time.isoformat(),
                        "to_time": next_job.start_time.isoformat(),
                    })
                    total_gap += gap_duration
            
            gaps_report[machine_code] = {
                "name": machine.name,
                "gaps": gaps,
                "total_gap_minutes": round(total_gap, 2),
            }
        
        return gaps_report

    def get_gantt_data(self) -> List[Dict[str, Any]]:
        """Retorna dados formatados para visualização Gantt"""
        gantt_data = []
        
        for scheduled_job in sorted(self.schedule, key=lambda j: j.start_time):
            start_minutes = (scheduled_job.start_time - min(s.start_time for s in self.schedule)).total_seconds() / 60
            duration_minutes = scheduled_job.total_time_minutes
            
            gantt_data.append({
                "job_id": scheduled_job.job_id,
                "machine": scheduled_job.machine_code,
                "fabric": scheduled_job.fabric,
                "start_minutes": round(start_minutes, 2),
                "duration_minutes": round(duration_minutes, 2),
                "start_time": scheduled_job.start_time.isoformat(),
                "end_time": scheduled_job.end_time.isoformat(),
                "processing_time": round(scheduled_job.processing_time_minutes, 2),
                "setup_time": scheduled_job.setup_time_minutes,
            })
        
        return gantt_data
