PRAGMA foreign_keys = ON;


-- ============================================================
-- FONTES DE LOGS
-- ============================================================

CREATE TABLE IF NOT EXISTS log_sources (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL,
    path TEXT NOT NULL,

    recursive INTEGER DEFAULT 1,
    enabled INTEGER DEFAULT 1,

    machine_hint TEXT,

    last_scan_at TEXT,
    last_successful_mtime REAL,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- EXECUÇÕES DE IMPORTAÇÃO
-- ============================================================

CREATE TABLE IF NOT EXISTS import_runs (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    source_id INTEGER NOT NULL,

    started_at TEXT DEFAULT CURRENT_TIMESTAMP,
    finished_at TEXT,

    total_found INTEGER DEFAULT 0,
    imported_count INTEGER DEFAULT 0,
    duplicate_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,

    notes TEXT,

    FOREIGN KEY (source_id) REFERENCES log_sources(id)
);


-- ============================================================
-- ARQUIVOS PROCESSADOS
-- ============================================================

CREATE TABLE IF NOT EXISTS imported_logs (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    run_id INTEGER,
    source_id INTEGER,

    file_name TEXT,
    file_path TEXT,

    file_size INTEGER,
    file_hash TEXT,

    status TEXT,

    detected_job_id TEXT,
    detected_computer_name TEXT,
    detected_machine TEXT,

    error_message TEXT,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (run_id) REFERENCES import_runs(id),
    FOREIGN KEY (source_id) REFERENCES log_sources(id)
);


-- ============================================================
-- JOBS DE PRODUÇÃO
-- ============================================================

CREATE TABLE IF NOT EXISTS production_jobs (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    job_id TEXT NOT NULL,

    machine TEXT,
    computer_name TEXT,

    document TEXT,

    start_time TEXT,
    end_time TEXT,
    duration_seconds INTEGER,

    fabric TEXT,

    planned_length_m REAL,
    consumed_length_m REAL,
    gap_before_m REAL,

    driver TEXT,
    source_path TEXT,

    job_type TEXT DEFAULT 'UNKNOWN',
    print_status TEXT DEFAULT 'OK',

    counts_as_valid_production INTEGER DEFAULT 1,
    counts_for_fabric_summary INTEGER DEFAULT 1,
    counts_for_roll_export INTEGER DEFAULT 1,

    error_reason TEXT,
    notes TEXT,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(job_id, computer_name, start_time)
);


-- ============================================================
-- ÍNDICES IMPORTANTES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_jobs_start_time
ON production_jobs(start_time);

CREATE INDEX IF NOT EXISTS idx_jobs_machine
ON production_jobs(machine);

CREATE INDEX IF NOT EXISTS idx_jobs_fabric
ON production_jobs(fabric);

CREATE INDEX IF NOT EXISTS idx_imported_logs_source_id
ON imported_logs(source_id);

CREATE INDEX IF NOT EXISTS idx_log_sources_enabled
ON log_sources(enabled);
