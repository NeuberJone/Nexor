"""
Módulo de parsing de logs .txt baseado no ProjetoJocasta
Extrai dados de impressão e agrupa em blocos por tecido
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass


# ============================================================
# Domain Models
# ============================================================

@dataclass
class Job:
    """Representa um pedido individual de impressão"""
    end_time: datetime
    document: str          # Ex: "PED-001 - OXFORD 300g"
    fabric: str            # Ex: "OXFORD 300g" (extraído do document)
    height_mm: float       # Comprimento em mm
    vpos_mm: float         # Deslocamento vertical (offset)
    src_file: str          # Caminho do arquivo .txt
    
    @property
    def real_m(self) -> float:
        """Comprimento real em metros (HeightMM / 1000)"""
        return self.height_mm / 1000.0
    
    def to_dict(self) -> dict:
        return {
            'end_time': self.end_time.isoformat(),
            'document': self.document,
            'fabric': self.fabric,
            'height_mm': self.height_mm,
            'vpos_mm': self.vpos_mm,
            'real_m': self.real_m,
            'src_file': self.src_file,
        }


@dataclass
class Block:
    """Representa um bloco de jobs do mesmo tecido (rolo)"""
    fabric: str
    machine: str
    jobs: List[Job]
    
    @property
    def total_m(self) -> float:
        """Total de metros do bloco"""
        return sum(j.real_m for j in self.jobs)
    
    @property
    def job_count(self) -> int:
        """Quantidade de jobs no bloco"""
        return len(self.jobs)
    
    @property
    def newest_end(self) -> datetime:
        """Data/hora mais recente"""
        return max(j.end_time for j in self.jobs) if self.jobs else datetime.now()
    
    @property
    def oldest_end(self) -> datetime:
        """Data/hora mais antiga"""
        return min(j.end_time for j in self.jobs) if self.jobs else datetime.now()
    
    def to_dict(self) -> dict:
        return {
            'fabric': self.fabric,
            'machine': self.machine,
            'total_m': round(self.total_m, 2),
            'job_count': self.job_count,
            'newest_end': self.newest_end.isoformat(),
            'oldest_end': self.oldest_end.isoformat(),
            'jobs': [j.to_dict() for j in self.jobs],
        }


# ============================================================
# Parsing Helpers
# ============================================================

_RE_KV = re.compile(r"^\s*([A-Za-z0-9_]+)\s*=\s*(.*)\s*$")
_RE_SECTION = re.compile(r"^\s*\[(.+?)\]\s*$")


def _parse_datetime(s: str) -> Optional[datetime]:
    """Parse datetime em formatos: DD/MM/YYYY HH:MM:SS ou DD/MM/YYYY HH:MM"""
    s = (s or "").strip()
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    return None


def _fabric_from_document(doc: str) -> str:
    """
    Extrai tecido do document.
    Formato esperado: "PEDIDO - TECIDO"
    Ex: "PED-001 - OXFORD 300g" → "OXFORD 300g"
    """
    parts = [p.strip() for p in (doc or "").split(" - ")]
    if len(parts) >= 2 and parts[1].strip():
        return parts[1].strip().upper()
    return "DESCONHECIDO"


def _parse_float(x: str) -> float:
    """Parse float com suporte a vírgula como separador decimal"""
    x = (x or "").strip().replace(",", ".")
    try:
        return float(x)
    except Exception:
        return 0.0


# ============================================================
# Log Parsing
# ============================================================

def parse_log_txt(path: str) -> Optional[Job]:
    """
    Parse arquivo .txt de log de impressão.
    
    Formato esperado:
    [General]
    EndTime=20/03/2025 14:30:45
    Document=PED-001 - OXFORD 300g
    
    [1]
    HeightMM=150.5
    VPositionMM=10.2
    Name=Job001
    """
    try:
        txt = Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return None
    
    section = None
    general = {}
    item1 = {}
    
    # Parse seções [General] e [1]
    for line in txt:
        msec = _RE_SECTION.match(line)
        if msec:
            section = msec.group(1).strip()
            continue
        mkv = _RE_KV.match(line)
        if not mkv:
            continue
        k, v = mkv.group(1).strip(), mkv.group(2).strip()
        if section == "General":
            general[k] = v
        elif section == "1":
            item1[k] = v
    
    # Validar EndTime (obrigatório)
    end_dt = _parse_datetime(general.get("EndTime", ""))
    if not end_dt:
        return None
    
    # Document (obrigatório)
    document = general.get("Document") or item1.get("Name") or Path(path).stem
    
    # Extrair métricas
    height_mm = _parse_float(item1.get("HeightMM", "0"))
    vpos_mm = _parse_float(item1.get("VPositionMM", "0"))
    
    # Tecido extraído do document
    fabric = _fabric_from_document(document)
    
    return Job(
        end_time=end_dt,
        document=document,
        fabric=fabric,
        height_mm=height_mm,
        vpos_mm=vpos_mm,
        src_file=str(path),
    )


# ============================================================
# Block Grouping
# ============================================================

def group_jobs_into_blocks(jobs: List[Job], machine: str = "DESCONHECIDA") -> List[Block]:
    """
    Agrupa jobs em blocos por tecido consecutivo.
    
    Regra: Se tecido mudar, quebra o bloco.
    Ordem: EndTime descendente (último impresso primeiro)
    """
    if not jobs:
        return []
    
    # Ordenar por EndTime descendente
    sorted_jobs = sorted(jobs, key=lambda j: j.end_time, reverse=True)
    
    blocks = []
    current_block_jobs = []
    current_fabric = None
    
    for job in sorted_jobs:
        # Se tecido mudou, criar novo bloco
        if current_fabric is not None and job.fabric != current_fabric:
            if current_block_jobs:
                blocks.append(Block(
                    fabric=current_fabric,
                    machine=machine,
                    jobs=current_block_jobs,
                ))
            current_block_jobs = []
        
        current_fabric = job.fabric
        current_block_jobs.append(job)
    
    # Adicionar último bloco
    if current_block_jobs:
        blocks.append(Block(
            fabric=current_fabric,
            machine=machine,
            jobs=current_block_jobs,
        ))
    
    return blocks


# ============================================================
# Batch Import
# ============================================================

def import_logs_from_directory(directory: str) -> tuple[List[Job], List[str]]:
    """
    Importa todos os arquivos .txt de um diretório.
    
    Retorna: (lista de jobs, lista de erros)
    """
    jobs = []
    errors = []
    
    try:
        path = Path(directory)
        if not path.exists():
            return jobs, [f"Diretório não existe: {directory}"]
        
        for txt_file in path.glob("*.txt"):
            try:
                job = parse_log_txt(str(txt_file))
                if job:
                    jobs.append(job)
                else:
                    errors.append(f"Falha ao parsear: {txt_file.name}")
            except Exception as e:
                errors.append(f"Erro em {txt_file.name}: {str(e)}")
    
    except Exception as e:
        errors.append(f"Erro ao acessar diretório: {str(e)}")
    
    return jobs, errors
