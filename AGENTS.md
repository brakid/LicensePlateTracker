# AGENTS.md

## Project

License Plate Tracker — Python service tracking cars via two cameras (entry/exit), detecting license plates, computing parking duration, flagging violations, contacting holders via a mocked registration API, with an exemption registry and end-of-day reconciliation.

## Code Standards

- **Language**: Python 3.11+
- **Formatting**: Use `black` for all Python code. Run `black .` before committing. Line length default 88.
- **Style**: Follow PEP 8; type hints on public functions; docstrings on modules and public functions.
- **Imports**: stdlib first, then third-party, then local; black/isort-compatible grouping.

## Testing

- **Framework**: pytest.
- **Location**: `tests/` directory mirroring source modules (e.g. `tests/test_sessions.py`).
- **Rules**: Every new feature/fix must include unit tests. Mock external dependencies (cameras, OCR, reg API) in tests. Use `tmp_path` for SQLite DB in tests (never the real DB).
- **Run**: `pytest -q` must pass before merging.

## Development Workflow

1. Create a feature branch.
2. Implement change + unit tests.
3. Run `black .` then `pytest -q`.
4. Commit with a clear message.

## Key Modules

- `plate_pipeline.py` — detection + OCR; keep pure (no DB/camera side effects) for testability.
- `sessions.py` — state machine; all DB writes go through `db.py`.
- `reg_api_mock.py` — mock only; never call real external services in tests.

## Notes

- Never commit `best.pt` changes or large binary artifacts.
- Config values (thresholds, RTSP URLs) live in `config.yaml`, not hardcoded.
