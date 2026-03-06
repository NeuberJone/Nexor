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

    length_m REAL,
    gap_before_m REAL,

    driver TEXT,
    source_path TEXT,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(job_id, computer_name, start_time)
);