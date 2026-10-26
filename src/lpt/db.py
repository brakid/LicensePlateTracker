"""SQLite database helpers and schema."""
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    plate TEXT NOT NULL,
    entry_time TEXT NOT NULL,
    exit_time TEXT,
    duration_min REAL,
    status TEXT NOT NULL,
    camera_entry TEXT,
    camera_exit TEXT
);
CREATE TABLE IF NOT EXISTS exemptions (
    plate TEXT PRIMARY KEY,
    reason TEXT,
    created_at TEXT NOT NULL,
    expires_at TEXT
);
CREATE TABLE IF NOT EXISTS violations (
    id INTEGER PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id),
    plate TEXT NOT NULL,
    duration_min REAL NOT NULL,
    holder_name TEXT,
    holder_contact TEXT,
    notified_at TEXT NOT NULL,
    channel TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS detections (
    id INTEGER PRIMARY KEY,
    camera TEXT NOT NULL,
    plate TEXT NOT NULL,
    confidence REAL NOT NULL,
    frame_ts TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS anomalies (
    id INTEGER PRIMARY KEY,
    camera TEXT NOT NULL,
    plate TEXT NOT NULL,
    reason TEXT NOT NULL,
    ts TEXT NOT NULL
);
"""


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.executescript(SCHEMA)
    conn.commit()
    return conn
