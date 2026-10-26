# License Plate Tracker — Design

## Overview

A single Python service tracking cars through a parking lot using two cameras (entry + exit). Each camera detects and reads license plates (YOLOv8 + OCR). The system records entry/exit times, computes stay duration, flags violations when a car stays longer than a configurable threshold, and contacts the car holder via a mocked registration API. Service cars and other exempt vehicles are excluded from tracking. Cars that never leave are reconciled manually by an operator at end of day.

## Models (from LicensePlateRecognition.ipynb)

- **Detection**: YOLOv8 model `best.pt` (custom license-plate detector). Confidence threshold 0.75.
  - Reference: https://www.kaggle.com/code/ztrollk/license-plate-detection-with-yolov8/notebook
- **OCR (primary)**: fast-plate-ocr `cct-s-v2-global-model` (`LicensePlateRecognizer`).
  - Reference: https://github.com/ankandrew/fast-plate-ocr
- **OCR (fallback)**: Tesseract with char whitelist `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ`, PSM 3, Otsu thresholding + morphological opening.
  - Reference: https://stackoverflow.com/questions/53797130/empty-string-with-tesseract

## High-Level Architecture

```
┌──────────────┐        ┌──────────────┐
│ Entry Camera │        │ Exit Camera  │  (RTSP streams)
└──────┬───────┘        └──────┬───────┘
       │                       │
       ▼                       ▼
┌──────────────────────────────────────┐
│        Camera Ingestion Threads      │  (cv2.VideoCapture, reconnect, frame sampling)
└──────────────┬───────────────────────┘
               │ frames
               ▼
┌──────────────────────────────────────┐
│   Plate Detection + OCR Pipeline     │  YOLOv8 best.pt → crop → fast-plate-ocr
│   (confidence threshold, normalize,  │  (or Tesseract fallback)
│    debounce across K frames)         │
└──────────────┬───────────────────────┘
               │ (camera, plate, ts)
               ▼
┌──────────────────────────────────────┐
│        Session State Machine         │  SQLite: create on entry, close on exit
│        + Exemption Check             │  exempt plates logged, not tracked
└──────────────┬───────────────────────┘
               │ closed session
               ▼
┌──────────────────────────────────────┐
│        Violation Checker             │  duration > MAX_STAY_MINUTES ?
│   (on exit) + end-of-day reconcile   │
└──────────────┬───────────────────────┘
               │ violation
               ▼
┌──────────────────────────────────────┐
│   Mock Registration API + Logger     │  plate → holder contact info; log contact action
└──────────────────────────────────────┘
```

## Components

| Component | File | Responsibility |
|---|---|---|
| Config | `config.py` / `config.yaml` | RTSP URLs, thresholds, DB path |
| Camera ingestion | `camera.py` | RTSP capture threads, reconnect, frame sampling |
| Plate pipeline | `plate_pipeline.py` | YOLOv8 detection + OCR, normalization, debounce |
| Sessions | `sessions.py` | Create/close parking sessions in SQLite |
| Exemptions | `exemptions.py` | Exempt plate registry (DB-backed) |
| Violations | `violations.py` | Threshold check, notify via mock reg API |
| Reg API mock | `reg_api_mock.py` | In-memory plate → holder lookup |
| DB | `db.py` | Schema, migrations, WAL mode |
| CLI | `cli.py` | Exemption mgmt, sessions, reconcile, violations |
| Main | `main.py` | Start camera threads + violation sweeper |

## Design Decisions

1. **Plate matching**: exact normalized string match for v1 (uppercase, strip spaces). No fuzzy matching to avoid merging distinct plates.
2. **Session identity**: keyed by normalized plate only; no vehicle re-ID.
3. **Duplicate entry handling**: if an open session exists for a plate and the entry camera sees it again within `entry_debounce_seconds`, ignore.
4. **Exit without entry**: log as anomaly, no session created.
5. **Violation timing**: checked on exit (post-hoc). No real-time alert while parked.
6. **Never-leaves cars**: operator runs `cli reconcile` at end of day; lists open sessions older than threshold; operator confirms each → triggers violation + contact path.
7. **Concurrency**: SQLite in WAL mode; writes serialized through a single writer thread/queue.
8. **Exemptions**: DB table with optional expiry; checked before session creation; exempt plates are still logged in `detections` for audit.
9. **Notifications**: log only for now (no email/webhook). Contact action recorded in `violations` table.
10. **OCR backend**: fast-plate-ocr primary, Tesseract as fallback (notebook showed onnxruntime must be installed).

## DB Schema (SQLite)

```sql
CREATE TABLE sessions (
  id INTEGER PRIMARY KEY,
  plate TEXT NOT NULL,
  entry_time TIMESTAMP NOT NULL,
  exit_time TIMESTAMP,
  duration_min REAL,
  status TEXT NOT NULL,        -- open | closed | violating
  camera_entry TEXT,
  camera_exit TEXT
);

CREATE TABLE exemptions (
  plate TEXT PRIMARY KEY,
  reason TEXT,
  created_at TIMESTAMP NOT NULL,
  expires_at TIMESTAMP
);

CREATE TABLE violations (
  id INTEGER PRIMARY KEY,
  session_id INTEGER REFERENCES sessions(id),
  plate TEXT NOT NULL,
  duration_min REAL NOT NULL,
  holder_name TEXT,
  holder_contact TEXT,
  notified_at TIMESTAMP NOT NULL,
  channel TEXT NOT NULL        -- log
);

CREATE TABLE detections (
  id INTEGER PRIMARY KEY,
  camera TEXT NOT NULL,       -- entry | exit
  plate TEXT NOT NULL,
  confidence REAL NOT NULL,
  frame_ts TIMESTAMP NOT NULL
);
```

## CLI Commands

- `python -m lpt exempt add <plate> --reason "..." [--expires YYYY-MM-DD]`
- `python -m lpt exempt list | remove <plate>`
- `python -m lpt sessions list [--open]`
- `python -m lpt reconcile` — interactive end-of-day review of open sessions
- `python -m lpt violations list`

## Querying the DB

```sql
-- Current occupancy
SELECT plate, entry_time FROM sessions WHERE status='open' ORDER BY entry_time;

-- Today's violations
SELECT plate, duration_min, notified_at FROM violations
WHERE date(notified_at)=date('now') ORDER BY notified_at DESC;

-- Average stay (closed sessions)
SELECT AVG(duration_min) AS avg_min, COUNT(*) AS n
FROM sessions WHERE status IN ('closed','violating');

-- Top offenders
SELECT plate, COUNT(*) AS v FROM violations GROUP BY plate ORDER BY v DESC LIMIT 10;
```

## End-of-Day Reconciliation Flow

```
operator runs `cli reconcile`
  → SELECT open sessions with entry_time older than threshold
  → for each: print plate + duration so far
  → operator confirms (y/n) whether it's a violation
  → confirmed → mark session violating, call mock reg API, log contact
  → declined → leave open (car still legitimately parked; re-check tomorrow)
```

## Anomalies & Statistics

- If the exit camera detects a plate with no matching open session, it is logged to `anomalies` (reason `exit_without_entry`) and ignored.
- Operators can discard stale open sessions via `discard_open_session` / CLI.
- `stats.anomaly_counts()` reports how often these cases happen, for monitoring detection quality.

## Next Items (Roadmap)

1. Multiple entry/exit gates: support N cameras, each registered as a gate (type entry/exit) in a `gates` table; sessions track entry/exit gate.
2. Fuzzy plate matching / re-ID: edit-distance matching against recent detections to merge misread sessions.
3. Real-time dashboard: FastAPI + WebSocket for live occupancy, detections, violations; admin UI for exemptions.
4. Notifications: email/SMS/webhook on violation with retry queue.
5. Analytics: peak-hour heatmaps, avg stay by day, repeat offenders.
6. ALPR improvements: multi-frame voting, confidence aggregation, per-country plate format validation.
7. Compliance: GDPR retention/anonymization, audit logs.

## Recent Changes

- Detection model sourced from Hugging Face: `morsetechlab/yolov11-license-plate-detection` (`license-plate-finetune-v1x.pt`) via `hf_hub_download`.
- When multiple plates are detected, the largest (closest) confident plate is selected for processing.
- `CameraStream` supports single image paths (`.jpg/.png/.avif/...`) for mocking streams: shows the image once then stops.
- Code reorganized into `src/lpt/` with tests in `test/`; hatch-based build (`pyproject.toml`).

## Tech Stack

Python 3.11+, ultralytics, fast-plate-ocr (+ onnxruntime), opencv-python, pyyaml, click, pytest, black, huggingface_hub. SQLite via stdlib.
