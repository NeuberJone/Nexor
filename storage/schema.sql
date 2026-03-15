PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS production_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    machine TEXT NOT NULL,
    computer_name TEXT NOT NULL,
    document TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL DEFAULT 0,
    fabric TEXT,

    planned_length_m REAL NOT NULL DEFAULT 0,
    actual_printed_length_m REAL NOT NULL DEFAULT 0,
    gap_before_m REAL NOT NULL DEFAULT 0,
    consumed_length_m REAL NOT NULL DEFAULT 0,

    driver TEXT,
    source_path TEXT,

    job_type TEXT NOT NULL DEFAULT 'UNKNOWN',
    is_rework INTEGER NOT NULL DEFAULT 0,
    notes TEXT,

    print_status TEXT NOT NULL DEFAULT 'OK',
    counts_as_valid_production INTEGER NOT NULL DEFAULT 1,
    counts_for_fabric_summary INTEGER NOT NULL DEFAULT 1,
    counts_for_roll_export INTEGER NOT NULL DEFAULT 1,
    error_reason TEXT,

    operator_code TEXT,
    operator_name TEXT,
    replacement_index INTEGER,

    suspicion_category TEXT,
    suspicion_reason TEXT,
    suspicion_ratio REAL,
    suspicion_missing_length_m REAL,
    suspicion_marked_at TEXT,

    review_status TEXT,
    review_note TEXT,
    reviewed_by TEXT,
    reviewed_at TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(job_id, start_time, machine, document)
);

CREATE INDEX IF NOT EXISTS idx_production_jobs_start_time
    ON production_jobs (start_time);

CREATE INDEX IF NOT EXISTS idx_production_jobs_machine
    ON production_jobs (machine);

CREATE INDEX IF NOT EXISTS idx_production_jobs_fabric
    ON production_jobs (fabric);

CREATE INDEX IF NOT EXISTS idx_production_jobs_print_status
    ON production_jobs (print_status);

CREATE INDEX IF NOT EXISTS idx_production_jobs_suspicion_category
    ON production_jobs (suspicion_category);

CREATE INDEX IF NOT EXISTS idx_production_jobs_review_status
    ON production_jobs (review_status);

CREATE INDEX IF NOT EXISTS idx_production_jobs_source_path
    ON production_jobs (source_path);

CREATE TRIGGER IF NOT EXISTS trg_production_jobs_updated_at
AFTER UPDATE ON production_jobs
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE production_jobs
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = OLD.id;
END;

CREATE TABLE IF NOT EXISTS log_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    path TEXT NOT NULL UNIQUE,
    recursive INTEGER NOT NULL DEFAULT 1,
    enabled INTEGER NOT NULL DEFAULT 1,
    machine_hint TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS import_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    total_found INTEGER NOT NULL DEFAULT 0,
    imported_count INTEGER NOT NULL DEFAULT 0,
    duplicate_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (source_id) REFERENCES log_sources(id)
);
