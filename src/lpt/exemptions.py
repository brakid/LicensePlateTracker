"""Exemption registry helpers."""
from datetime import datetime
import sqlite3
from lpt.sessions import normalize_plate


def add_exemption(conn, plate, reason=None, expires_at=None):
    plate = normalize_plate(plate)
    conn.execute(
        "INSERT OR REPLACE INTO exemptions (plate, reason, created_at, expires_at) VALUES (?,?,?,?)",
        (plate, reason, datetime.utcnow().isoformat(), expires_at),
    )
    conn.commit()


def remove_exemption(conn, plate):
    plate = normalize_plate(plate)
    conn.execute("DELETE FROM exemptions WHERE plate=?", (plate,))
    conn.commit()


def list_exemptions(conn):
    rows = conn.execute(
        "SELECT plate, reason, created_at, expires_at FROM exemptions ORDER BY plate"
    ).fetchall()
    return [dict(r) for r in rows]
