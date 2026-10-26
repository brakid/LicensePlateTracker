"""Entry point: start camera threads."""
import logging
from lpt.config import load_config
from lpt.camera import CameraStream
from lpt.db import connect

logging.basicConfig(level=logging.INFO)

cfg = load_config()
conn = connect(cfg.db_path)


def on_frame(camera_name, frame):
    # placeholder: detect + OCR + session handling wired here
    pass


entry_cam = CameraStream(cfg.entry_camera_url, "entry", on_frame, cfg.frame_sample_every_n)
exit_cam = CameraStream(cfg.exit_camera_url, "exit", on_frame, cfg.frame_sample_every_n)

if __name__ == "__main__":
    entry_cam.start()
    exit_cam.start()
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        entry_cam.stop()
        exit_cam.stop()
