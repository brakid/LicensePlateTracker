from lpt.reg_api_mock import lookup_holder


def test_lookup_known():
    h = lookup_holder("ABC123")
    assert h["name"] == "Alice Example"


def test_lookup_unknown_synthetic():
    h = lookup_holder("ZZZ999")
    assert "email" in h and h["email"].endswith("@example.com")
