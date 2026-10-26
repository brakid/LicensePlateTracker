"""Violation detection and (mock) notification."""
import logging
from datetime import datetime
import sqlite3
from lpt.reg_api_mock import lookup_holder

log = logging.getLogger("violations")


def check_and_record(conn, session, max_stay_minutes, channel="log"):
    """If session duration exceeds threshold, record violation + notify. Returns violation dict or None."""
    duration = session["duration_min"]
    if duration is None or duration <= max_stay_minutes:
        return None
    holder = lookup_holder(session["plate"])
    now = datetime.utcnow().isoformat()
    cur = conn.execute(
        "INSERT INTO violations (session_id, plate, duration_min, holder_name, holder_contact, notified_at, channel) "
        "VALUES (?,?,?,?,?,?,?)",
        (
            session["id"],
            session["plate"],
            duration,
            holder["name"],
            holder["email"],
            now,
            channel,
        ),
    )
    # mark session violating
    conn.execute("UPDATE sessions SET status='violating' WHERE id=?", (session["id"],))
    conn.commit()
    msg = (
        f"VIOLATION: plate={session['plate']} stayed {duration:.1f} min "
        f"(limit {max_stay_minutes}); contact {holder['name']} {holder['email']} {holder['phone']}"
    )
    log.warning(msg)
    print(msg)
    return {
        "id": cur.lastrowid,
        "session_id": session["id"],
        "plate": session["plate"],
        "duration_min": duration,
        "holder": holder,
    }


def reconcile_open(conn, max_stay_minutes):
    """Return open sessions older than threshold (for end-of-day review)."""
    rows = conn.execute(
        "SELECT id, plate, entry_time FROM sessions WHERE status='open' ORDER BY entry_time"
    ).fetchall()
    now = datetime.utcnow()
    out = []
    for r in rows:
        entry = datetime.fromisoformat(r["entry_time"])
        dur = (now - entry).total_seconds() / 60.0
        if dur > max_stay_minutes:
            out.append({"id": r["id"], "plate": r["plate"], "entry_time": r["entry_time"], "duration_min": dur})
    return out
