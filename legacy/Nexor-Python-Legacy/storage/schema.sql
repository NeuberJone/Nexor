PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- Raw imported logs
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_path TEXT,
    source_name TEXT,
    fingerprint TEXT UNIQUE,
    machine_code_raw TEXT,
    captured_at TEXT,
    raw_payload TEXT,
    status TEXT NOT NULL DEFAULT 'NEW',
    parse_error TEXT,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    job_id INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_logs_status
    ON logs (status);

CREATE INDEX IF NOT EXISTS idx_logs_captured_at
    ON logs (captured_at);

CREATE INDEX IF NOT EXISTS idx_logs_source_path
    ON logs (source_path);

CREATE INDEX IF NOT EXISTS idx_logs_machine_code_raw
    ON logs (machine_code_raw);

CREATE TRIGGER IF NOT EXISTS trg_logs_updated_at
AFTER UPDATE ON logs
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE logs
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = OLD.id;
END;

-- ---------------------------------------------------------------------------
-- Normalized production jobs
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS production_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_id INTEGER,
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

    classification TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (log_id) REFERENCES logs(id) ON DELETE SET NULL,
    UNIQUE(job_id, start_time, machine, document)
);

CREATE INDEX IF NOT EXISTS idx_production_jobs_log_id
    ON production_jobs (log_id);

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

-- ---------------------------------------------------------------------------
-- Roll headers
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rolls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_name TEXT NOT NULL UNIQUE,
    machine TEXT NOT NULL,
    fabric TEXT,
    status TEXT NOT NULL DEFAULT 'OPEN',
    note TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_at TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    exported_at TEXT,
    reviewed_at TEXT,
    reopened_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_rolls_status
    ON rolls (status);

CREATE INDEX IF NOT EXISTS idx_rolls_machine
    ON rolls (machine);

CREATE INDEX IF NOT EXISTS idx_rolls_fabric
    ON rolls (fabric);

CREATE INDEX IF NOT EXISTS idx_rolls_created_at
    ON rolls (created_at);

CREATE TRIGGER IF NOT EXISTS trg_rolls_updated_at
AFTER UPDATE ON rolls
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE rolls
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = OLD.id;
END;

-- ---------------------------------------------------------------------------
-- Roll item snapshots
-- ---------------------------------------------------------------------------
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

-- ---------------------------------------------------------------------------
-- Configured log sources
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS log_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    path TEXT NOT NULL UNIQUE,
    recursive INTEGER NOT NULL DEFAULT 1,
    enabled INTEGER NOT NULL DEFAULT 1,
    machine_hint TEXT,
    last_scan_at TEXT,
    last_successful_mtime REAL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_log_sources_enabled
    ON log_sources (enabled);

CREATE TRIGGER IF NOT EXISTS trg_log_sources_updated_at
AFTER UPDATE ON log_sources
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE log_sources
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = OLD.id;
END;

-- ---------------------------------------------------------------------------
-- Import runs
-- ---------------------------------------------------------------------------
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
    FOREIGN KEY (source_id) REFERENCES log_sources(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_import_runs_source_id
    ON import_runs (source_id);

CREATE INDEX IF NOT EXISTS idx_import_runs_started_at
    ON import_runs (started_at);

-- ---------------------------------------------------------------------------
-- File-level import audit
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS imported_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    file_hash TEXT,
    status TEXT NOT NULL,
    error_message TEXT,
    detected_job_id TEXT,
    detected_computer_name TEXT,
    detected_machine TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (run_id) REFERENCES import_runs(id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES log_sources(id) ON DELETE RESTRICT,
    UNIQUE(run_id, file_path, file_hash)
);

CREATE INDEX IF NOT EXISTS idx_imported_logs_run_id
    ON imported_logs (run_id);

CREATE INDEX IF NOT EXISTS idx_imported_logs_source_id
    ON imported_logs (source_id);

CREATE INDEX IF NOT EXISTS idx_imported_logs_status
    ON imported_logs (status);

CREATE INDEX IF NOT EXISTS idx_imported_logs_file_hash
    ON imported_logs (file_hash);