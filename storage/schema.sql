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