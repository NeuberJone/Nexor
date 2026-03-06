CREATE TABLE IF NOT EXISTS production_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    job_id TEXT NOT NULL,
    machine TEXT,
    computer_name TEXT NOT NULL,
    document TEXT NOT NULL,

    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL,

    fabric TEXT,

    length_m REAL NOT NULL,
    gap_before_m REAL NOT NULL,

    driver TEXT,
    source_path TEXT,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(job_id, computer_name, start_time)
);

CREATE TABLE IF NOT EXISTS log_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL,
    path TEXT NOT NULL,
    recursive INTEGER NOT NULL DEFAULT 1,
    enabled INTEGER NOT NULL DEFAULT 1,
    machine_hint TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
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

    imported_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (run_id) REFERENCES import_runs(id),
    FOREIGN KEY (source_id) REFERENCES log_sources(id),

    UNIQUE(file_path, file_hash)
);