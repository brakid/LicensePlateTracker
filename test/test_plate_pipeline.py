from lpt.plate_pipeline import normalize_plate


def test_normalize_plate():
    assert normalize_plate("ab c-123") == "ABC123"
