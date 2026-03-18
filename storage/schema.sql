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

    job_type TEXT NOT NULL DEFAULT 'PRODUCTION',
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

CREATE TABLE IF NOT EXISTS rolls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_name TEXT NOT NULL UNIQUE,
    machine TEXT NOT NULL,
    fabric TEXT,
    status TEXT NOT NULL DEFAULT 'OPEN',
    note TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_at TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rolls_status
    ON rolls (status);

CREATE INDEX IF NOT EXISTS idx_rolls_machine
    ON rolls (machine);

CREATE INDEX IF NOT EXISTS idx_rolls_fabric
    ON rolls (fabric);

CREATE TRIGGER IF NOT EXISTS trg_rolls_updated_at
AFTER UPDATE ON rolls
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE rolls
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = OLD.id;
END;

CREATE TABLE IF NOT EXISTS roll_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_id INTEGER NOT NULL,
    job_row_id INTEGER NOT NULL,
    job_id TEXT NOT NULL,
    document TEXT NOT NULL,
    machine TEXT NOT NULL,
    fabric TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,

    planned_length_m REAL NOT NULL DEFAULT 0,
    effective_printed_length_m REAL NOT NULL DEFAULT 0,
    consumed_length_m REAL NOT NULL DEFAULT 0,
    gap_before_m REAL NOT NULL DEFAULT 0,

    metric_category TEXT,
    review_status TEXT,
    snapshot_print_status TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (roll_id) REFERENCES rolls(id) ON DELETE CASCADE,
    FOREIGN KEY (job_row_id) REFERENCES production_jobs(id) ON DELETE RESTRICT,
    UNIQUE(roll_id, job_row_id),
    UNIQUE(job_row_id)
);

CREATE INDEX IF NOT EXISTS idx_roll_items_roll_id
    ON roll_items (roll_id);

CREATE INDEX IF NOT EXISTS idx_roll_items_job_row_id
    ON roll_items (job_row_id);

CREATE INDEX IF NOT EXISTS idx_roll_items_sort_order
    ON roll_items (roll_id, sort_order);

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