"""Parking session state machine."""
from datetime import datetime, timedelta
import sqlite3


def _now() -> str:
    return datetime.utcnow().isoformat()


def is_exempt(conn: sqlite3.Connection, plate: str) -> bool:
    row = conn.execute(
        "SELECT expires_at FROM exemptions WHERE plate=?", (plate,)
    ).fetchone()
    if not row:
        return False
    expires = row["expires_at"]
    if expires and datetime.fromisoformat(expires) < datetime.utcnow():
        return False
    return True


def normalize_plate(text: str) -> str:
    return "".join(ch for ch in text.upper() if ch.isalnum())


def open_session(
    conn: sqlite3.Connection,
    plate: str,
    camera: str,
    debounce_seconds: int = 60,
) -> int | None:
    """Create an entry session if not exempt and no recent open session. Returns session id or None."""
    plate = normalize_plate(plate)
    if is_exempt(conn, plate):
        return None
    recent = conn.execute(
        "SELECT id, entry_time FROM sessions WHERE plate=? AND status='open' ORDER BY entry_time DESC LIMIT 1",
        (plate,),
    ).fetchone()
    if recent:
        # prevent duplicate open sessions across runs: skip if any open session exists
        return None
    cur = conn.execute(
        "INSERT INTO sessions (plate, entry_time, status, camera_entry) VALUES (?,?,?,?)",
        (plate, _now(), "open", camera),
    )
    conn.commit()
    return cur.lastrowid


def close_session(
    conn: sqlite3.Connection, plate: str, camera: str
) -> dict | None:
    """Close the latest open session for plate. Returns session dict or None."""
    plate = normalize_plate(plate)
    row = conn.execute(
        "SELECT id, entry_time FROM sessions WHERE plate=? AND status='open' ORDER BY entry_time DESC LIMIT 1",
        (plate,),
    ).fetchone()
    if not row:
        # exit without entry: log anomaly, ignore
        conn.execute(
            "INSERT INTO anomalies (camera, plate, reason, ts) VALUES (?,?,?,?)",
            (camera, plate, "exit_without_entry", _now()),
        )
        conn.commit()
        return None
    entry = datetime.fromisoformat(row["entry_time"])
    exit_time = datetime.utcnow()
    duration = (exit_time - entry).total_seconds() / 60.0
    conn.execute(
        "UPDATE sessions SET exit_time=?, duration_min=?, status=?, camera_exit=? WHERE id=?",
        (exit_time.isoformat(), duration, "closed", camera, row["id"]),
    )
    conn.commit()
    return {
        "id": row["id"],
        "plate": plate,
        "entry_time": row["entry_time"],
        "exit_time": exit_time.isoformat(),
        "duration_min": duration,
    }


def list_open_sessions(conn: sqlite3.Connection) -> list:
    rows = conn.execute(
        "SELECT id, plate, entry_time FROM sessions WHERE status='open' ORDER BY entry_time"
    ).fetchall()
    return [dict(r) for r in rows]
