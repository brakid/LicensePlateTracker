"""Statistics helpers."""
import sqlite3


def anomaly_counts(conn: sqlite3.Connection) -> dict:
    rows = conn.execute(
        "SELECT reason, COUNT(*) AS n FROM anomalies GROUP BY reason"
    ).fetchall()
    return {r["reason"]: r["n"] for r in rows}


def discard_open_session(conn: sqlite3.Connection, session_id: int) -> None:
    conn.execute("UPDATE sessions SET status='discarded' WHERE id=?", (session_id,))
    conn.commit()
