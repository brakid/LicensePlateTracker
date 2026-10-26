"""Mocked vehicle registration API: plate -> holder contact info."""
import random

_MOCK_DB = {
    "ABC123": {"name": "Alice Example", "email": "alice@example.com", "phone": "+1-555-0100"},
    "XYZ789": {"name": "Bob Sample", "email": "bob@example.com", "phone": "+1-555-0101"},
}


def lookup_holder(plate: str) -> dict:
    plate = plate.upper().replace(" ", "")
    if plate in _MOCK_DB:
        return _MOCK_DB[plate]
    # synthetic fallback for unknown plates
    rng = random.Random(plate)
    return {
        "name": f"Holder-{plate}",
        "email": f"{plate.lower()}@example.com",
        "phone": f"+1-555-{rng.randint(1000,9999)}",
    }
