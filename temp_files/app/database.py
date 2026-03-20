"""
Módulo de gerenciamento de banco de dados SQLite
Armazena jobs, rolos e eventos
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from app.parsers import Job, Block


# ============================================================
# Database Setup
# ============================================================

DB_PATH = Path(__file__).parent.parent / "nexor.db"


def init_db():
    """Inicializa banco de dados com tabelas"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Tabela de rolos
    c.execute("""
        CREATE TABLE IF NOT EXISTS rolls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_name TEXT UNIQUE NOT NULL,
            machine TEXT,
            fabric TEXT,
            total_m REAL,
            job_count INTEGER,
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP,
            notes TEXT
        )
    """)
    
    # Tabela de jobs
    c.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_id INTEGER,
            document TEXT NOT NULL,
            fabric TEXT NOT NULL,
            height_mm REAL,
            vpos_mm REAL,
            real_m REAL,
            end_time TIMESTAMP,
            src_file TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (roll_id) REFERENCES rolls(id)
        )
    """)
    
    # Tabela de eventos
    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_id INTEGER,
            event_type TEXT,
            payload TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (roll_id) REFERENCES rolls(id)
        )
    """)
    
    # Tabela de estoque de rolos de tecido
    c.execute("""
        CREATE TABLE IF NOT EXISTS stock_rolls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fabric TEXT NOT NULL,
            quantity_m REAL NOT NULL,
            supplier TEXT,
            batch_code TEXT,
            received_date TIMESTAMP,
            expiry_date TIMESTAMP,
            status TEXT DEFAULT 'available',
            location TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela de consumo de estoque
    c.execute("""
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_roll_id INTEGER NOT NULL,
            roll_id INTEGER,
            movement_type TEXT NOT NULL,
            quantity_m REAL NOT NULL,
            reason TEXT,
            operator TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_roll_id) REFERENCES stock_rolls(id),
            FOREIGN KEY (roll_id) REFERENCES rolls(id)
        )
    """)
    
    # Tabela de alertas de estoque
    c.execute("""
        CREATE TABLE IF NOT EXISTS stock_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_roll_id INTEGER NOT NULL,
            alert_type TEXT NOT NULL,
            threshold_m REAL,
            current_quantity_m REAL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            FOREIGN KEY (stock_roll_id) REFERENCES stock_rolls(id)
        )
    """)
    
    # Índices
    c.execute("CREATE INDEX IF NOT EXISTS idx_rolls_status ON rolls(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_rolls_machine ON rolls(machine)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_jobs_roll_id ON jobs(roll_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_jobs_fabric ON jobs(fabric)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_events_roll_id ON events(roll_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_stock_fabric ON stock_rolls(fabric)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_stock_status ON stock_rolls(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_movements_stock ON stock_movements(stock_roll_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_alerts_stock ON stock_alerts(stock_roll_id)")
    
    conn.commit()
    conn.close()


# ============================================================
# Jobs
# ============================================================

def insert_job(
    document: str,
    fabric: str,
    height_mm: float,
    vpos_mm: float,
    real_m: float,
    end_time: datetime,
    src_file: str,
    roll_id: Optional[int] = None,
) -> int:
    """Insere um job no banco de dados"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO jobs (roll_id, document, fabric, height_mm, vpos_mm, real_m, end_time, src_file)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (roll_id, document, fabric, height_mm, vpos_mm, real_m, end_time, src_file))
    
    job_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return job_id


def get_jobs(roll_id: Optional[int] = None, limit: int = 1000) -> List[Dict[str, Any]]:
    """Obtém lista de jobs"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    if roll_id is not None:
        c.execute("""
            SELECT * FROM jobs WHERE roll_id = ? ORDER BY end_time DESC LIMIT ?
        """, (roll_id, limit))
    else:
        c.execute("""
            SELECT * FROM jobs ORDER BY end_time DESC LIMIT ?
        """, (limit,))
    
    rows = c.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_unassigned_jobs(limit: int = 1000) -> List[Dict[str, Any]]:
    """Obtém jobs não atribuídos a nenhum rolo"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("""
        SELECT * FROM jobs WHERE roll_id IS NULL ORDER BY end_time DESC LIMIT ?
    """, (limit,))
    
    rows = c.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


# ============================================================
# Rolls
# ============================================================

def insert_roll(
    roll_name: str,
    machine: str,
    fabric: str,
    total_m: float,
    job_count: int,
    notes: str = "",
) -> int:
    """Insere um rolo no banco de dados"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO rolls (roll_name, machine, fabric, total_m, job_count, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (roll_name, machine, fabric, total_m, job_count, notes))
    
    roll_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return roll_id


def get_rolls(
    status: Optional[str] = None,
    machine: Optional[str] = None,
    fabric: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 300,
) -> List[Dict[str, Any]]:
    """Obtém lista de rolos com filtros avançados"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = "SELECT * FROM rolls WHERE 1=1"
    params = []
    
    if status:
        query += " AND status = ?"
        params.append(status)
    
    if machine:
        query += " AND machine = ?"
        params.append(machine)
    
    if fabric:
        query += " AND fabric = ?"
        params.append(fabric)
    
    if date_from:
        query += " AND DATE(created_at) >= DATE(?)"
        params.append(date_from)
    
    if date_to:
        query += " AND DATE(created_at) <= DATE(?)"
        params.append(date_to)
    
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_roll(roll_id: int) -> Optional[Dict[str, Any]]:
    """Obtém detalhes de um rolo específico"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM rolls WHERE id = ?", (roll_id,))
    row = c.fetchone()
    conn.close()
    
    return dict(row) if row else None


def close_roll(roll_id: int) -> bool:
    """Fecha um rolo (muda status para 'closed')"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("""
        UPDATE rolls SET status = 'closed', closed_at = CURRENT_TIMESTAMP WHERE id = ?
    """, (roll_id,))
    
    conn.commit()
    conn.close()
    
    return c.rowcount > 0


def update_roll(roll_id: int, **kwargs) -> bool:
    """Atualiza campos de um rolo"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    allowed_fields = {'machine', 'fabric', 'total_m', 'job_count', 'notes', 'status'}
    fields_to_update = {k: v for k, v in kwargs.items() if k in allowed_fields}
    
    if not fields_to_update:
        conn.close()
        return False
    
    set_clause = ", ".join([f"{k} = ?" for k in fields_to_update.keys()])
    values = list(fields_to_update.values()) + [roll_id]
    
    c.execute(f"UPDATE rolls SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()
    
    return c.rowcount > 0


def assign_jobs_to_roll(job_ids: List[int], roll_id: int) -> bool:
    """Atribui jobs a um rolo"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    placeholders = ",".join("?" * len(job_ids))
    c.execute(f"""
        UPDATE jobs SET roll_id = ? WHERE id IN ({placeholders})
    """, [roll_id] + job_ids)
    
    conn.commit()
    conn.close()
    
    return c.rowcount > 0


# ============================================================
# Events
# ============================================================

def insert_event(
    roll_id: int,
    event_type: str,
    payload: Dict[str, Any],
) -> int:
    """Insere um evento"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    payload_json = json.dumps(payload, ensure_ascii=False, default=str)
    
    c.execute("""
        INSERT INTO events (roll_id, event_type, payload)
        VALUES (?, ?, ?)
    """, (roll_id, event_type, payload_json))
    
    event_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return event_id


def get_events(roll_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    """Obtém eventos de um rolo"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("""
        SELECT * FROM events WHERE roll_id = ? ORDER BY created_at DESC LIMIT ?
    """, (roll_id, limit))
    
    rows = c.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        d = dict(row)
        try:
            d['payload'] = json.loads(d['payload'])
        except:
            pass
        result.append(d)
    
    return result


# ============================================================
# Statistics
# ============================================================

def get_statistics() -> Dict[str, Any]:
    """Obtém estatísticas gerais"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Total de jobs
    c.execute("SELECT COUNT(*) as count FROM jobs")
    total_jobs = c.fetchone()[0]
    
    # Total de rolos
    c.execute("SELECT COUNT(*) as count FROM rolls")
    total_rolls = c.fetchone()[0]
    
    # Rolos abertos
    c.execute("SELECT COUNT(*) as count FROM rolls WHERE status = 'open'")
    open_rolls = c.fetchone()[0]
    
    # Total de metros
    c.execute("SELECT SUM(total_m) as total FROM rolls WHERE status = 'closed'")
    total_m = c.fetchone()[0] or 0
    
    # Tecidos únicos
    c.execute("SELECT COUNT(DISTINCT fabric) as count FROM jobs")
    unique_fabrics = c.fetchone()[0]
    
    conn.close()
    
    return {
        'total_jobs': total_jobs,
        'total_rolls': total_rolls,
        'open_rolls': open_rolls,
        'total_m': round(total_m, 2),
        'unique_fabrics': unique_fabrics,
    }


# ============================================================
# Audit & Inconsistencies
# ============================================================

def get_roll_audit_trail(roll_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    """Obtém trilha de auditoria de um rolo"""
    return get_events(roll_id, limit)


def get_inconsistencies() -> List[Dict[str, Any]]:
    """Obtém lista de inconsistências detectadas"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    inconsistencies = []
    
    # Rolos sem jobs
    c.execute("""
        SELECT id, roll_name, total_m, job_count FROM rolls 
        WHERE job_count = 0 OR job_count IS NULL
    """)
    for row in c.fetchall():
        inconsistencies.append({
            'type': 'empty_roll',
            'severity': 'high',
            'roll_id': row['id'],
            'roll_name': row['roll_name'],
            'message': f"Rolo vazio: {row['roll_name']}",
        })
    
    # Jobs com tecido desconhecido
    c.execute("""
        SELECT COUNT(*) as count FROM jobs WHERE fabric = 'DESCONHECIDO'
    """)
    unknown_count = c.fetchone()[0]
    if unknown_count > 0:
        inconsistencies.append({
            'type': 'unknown_fabric',
            'severity': 'medium',
            'count': unknown_count,
            'message': f"{unknown_count} jobs com tecido desconhecido",
        })
    
    # Rolos com data de fechamento mas status aberto
    c.execute("""
        SELECT id, roll_name FROM rolls 
        WHERE status = 'open' AND closed_at IS NOT NULL
    """)
    for row in c.fetchall():
        inconsistencies.append({
            'type': 'status_mismatch',
            'severity': 'high',
            'roll_id': row['id'],
            'roll_name': row['roll_name'],
            'message': f"Status inconsistente: {row['roll_name']}",
        })
    
    conn.close()
    return inconsistencies


# ============================================================
# Stock Management
# ============================================================

def add_stock_roll(fabric: str, quantity_m: float, supplier: str = None, batch_code: str = None, location: str = None) -> int:
    """Adiciona um novo rolo de estoque"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO stock_rolls (fabric, quantity_m, supplier, batch_code, location, status)
        VALUES (?, ?, ?, ?, ?, 'available')
    """, (fabric, quantity_m, supplier, batch_code, location))
    
    stock_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return stock_id


def get_stock_rolls(fabric: str = None, status: str = None) -> List[Dict[str, Any]]:
    """Obtém rolos de estoque com filtros opcionais"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = "SELECT * FROM stock_rolls WHERE 1=1"
    params = []
    
    if fabric:
        query += " AND fabric LIKE ?"
        params.append(f"%{fabric}%")
    
    if status:
        query += " AND status = ?"
        params.append(status)
    
    query += " ORDER BY created_at DESC"
    
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def consume_stock(stock_roll_id: int, quantity_m: float, roll_id: int = None, operator: str = None) -> bool:
    """Consome estoque de um rolo"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Verificar disponibilidade
        c.execute("SELECT quantity_m FROM stock_rolls WHERE id = ?", (stock_roll_id,))
        row = c.fetchone()
        if not row or row[0] < quantity_m:
            conn.close()
            return False
        
        # Atualizar quantidade
        c.execute("""
            UPDATE stock_rolls SET quantity_m = quantity_m - ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (quantity_m, stock_roll_id))
        
        # Registrar movimento
        c.execute("""
            INSERT INTO stock_movements (stock_roll_id, roll_id, movement_type, quantity_m, operator)
            VALUES (?, ?, 'consume', ?, ?)
        """, (stock_roll_id, roll_id, quantity_m, operator))
        
        # Verificar se precisa de alerta
        c.execute("SELECT quantity_m FROM stock_rolls WHERE id = ?", (stock_roll_id,))
        remaining = c.fetchone()[0]
        if remaining < 50:  # Alerta se menos de 50m
            c.execute("""
                INSERT INTO stock_alerts (stock_roll_id, alert_type, threshold_m, current_quantity_m)
                VALUES (?, 'low_stock', 50, ?)
            """, (stock_roll_id, remaining))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao consumir estoque: {e}")
        conn.close()
        return False


def get_stock_movements(stock_roll_id: int = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Obtém movimentações de estoque"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    if stock_roll_id:
        c.execute("""
            SELECT * FROM stock_movements WHERE stock_roll_id = ?
            ORDER BY created_at DESC LIMIT ?
        """, (stock_roll_id, limit))
    else:
        c.execute("""
            SELECT * FROM stock_movements
            ORDER BY created_at DESC LIMIT ?
        """, (limit,))
    
    rows = c.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_stock_alerts(status: str = 'active') -> List[Dict[str, Any]]:
    """Obtém alertas de estoque"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("""
        SELECT a.*, s.fabric, s.quantity_m FROM stock_alerts a
        JOIN stock_rolls s ON a.stock_roll_id = s.id
        WHERE a.status = ?
        ORDER BY a.created_at DESC
    """, (status,))
    
    rows = c.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_stock_summary() -> Dict[str, Any]:
    """Obtém resumo de estoque"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Total de metros em estoque
    c.execute("SELECT SUM(quantity_m) as total FROM stock_rolls WHERE status = 'available'")
    total_m = c.fetchone()[0] or 0
    
    # Quantidade de rolos
    c.execute("SELECT COUNT(*) as count FROM stock_rolls WHERE status = 'available'")
    roll_count = c.fetchone()[0]
    
    # Tecidos únicos
    c.execute("SELECT COUNT(DISTINCT fabric) as count FROM stock_rolls WHERE status = 'available'")
    fabric_count = c.fetchone()[0]
    
    # Alertas ativos
    c.execute("SELECT COUNT(*) as count FROM stock_alerts WHERE status = 'active'")
    alert_count = c.fetchone()[0]
    
    conn.close()
    
    return {
        'total_m': round(total_m, 2),
        'roll_count': roll_count,
        'fabric_count': fabric_count,
        'active_alerts': alert_count,
    }


# ============================================================
# Initialization
# ============================================================

# Inicializar banco de dados ao importar
init_db()
