"""Entry point: start camera threads."""
import logging
from huggingface_hub import hf_hub_download
from ultralytics import YOLO
from fast_plate_ocr import LicensePlateRecognizer
from lpt.config import load_config
from lpt.camera import CameraStream
from lpt.db import connect
from lpt.plate_pipeline import detect_plates, recognize_plate
from lpt.sessions import open_session, close_session
from lpt.violations import check_and_record

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("main")

cfg = load_config()
conn = connect(cfg.db_path)
weights = hf_hub_download("morsetechlab/yolov11-license-plate-detection", "license-plate-finetune-v1x.pt")
model = YOLO(weights)
recognizer = LicensePlateRecognizer("cct-s-v2-global-model")


def on_frame(camera_name, frame):
    plates = detect_plates(frame, model, cfg.confidence_threshold)
    if not plates:
        return
    # choose largest (closest) plate among confident detections
    plates = [p for p in plates if p[4] >= cfg.confidence_threshold]
    if not plates:
        return
    primary = max(plates, key=lambda p: (p[2]-p[0])*(p[3]-p[1]))
    plates = [primary]
    for (x1, y1, x2, y2, conf) in plates:
        crop = frame[y1:y2, x1:x2]
        try:
            text = recognize_plate(crop, recognizer)
        except Exception as e:
            log.warning("OCR failed: %s", e)
            continue
        if not text:
            continue
        conn.execute(
            "INSERT INTO detections (camera, plate, confidence, frame_ts) VALUES (?,?,?,datetime('now'))",
            (camera_name, text, conf),
        )
        conn.commit()
        log.info("Detected plate %s on %s (conf %.2f)", text, camera_name, conf)
        if camera_name == "entry":
            open_session(conn, text, camera_name, cfg.entry_debounce_seconds)
        else:
            sess = close_session(conn, text, camera_name)
            if sess:
                check_and_record(conn, sess, cfg.max_stay_minutes)


entry_cam = CameraStream(cfg.entry_camera_url, "entry", on_frame, cfg.frame_sample_every_n)
exit_cam = CameraStream(cfg.exit_camera_url, "exit", on_frame, cfg.frame_sample_every_n)

if __name__ == "__main__":
    entry_cam.start()
    exit_cam.start()
    entry_cam.thread.join()
    exit_cam.thread.join()
