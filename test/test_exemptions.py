from lpt.db import connect
from lpt.exemptions import add_exemption, remove_exemption, list_exemptions


def test_exemption_crud(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    add_exemption(conn, "X1", reason="vip")
    assert any(e["plate"] == "X1" for e in list_exemptions(conn))
    remove_exemption(conn, "X1")
    assert not any(e["plate"] == "X1" for e in list_exemptions(conn))
