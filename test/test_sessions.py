import sqlite3
from lpt.db import connect
from lpt.sessions import open_session, close_session, normalize_plate
from lpt.exemptions import add_exemption


def test_normalize():
    assert normalize_plate("abc 123") == "ABC123"


def test_open_and_close(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    sid = open_session(conn, "abc 123", "entry")
    assert sid is not None
    res = close_session(conn, "ABC123", "exit")
    assert res is not None
    assert res["duration_min"] >= 0


def test_exempt_skips(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    add_exemption(conn, "SVC1", reason="service")
    assert open_session(conn, "SVC1", "entry") is None


def test_debounce(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    s1 = open_session(conn, "P1", "entry", debounce_seconds=60)
    s2 = open_session(conn, "P1", "entry", debounce_seconds=60)
    assert s1 is not None
    assert s2 is None
