"""Camera ingestion threads."""
import threading
import time
import cv2


class CameraStream:
    def __init__(self, url, name, on_frame, sample_every=5):
        self.url = url
        self.name = name
        self.on_frame = on_frame
        self.sample_every = sample_every
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self._stop.set()

    def _run(self):
        #cap = cv2.VideoCapture(self.url)
        cap = cv2.VideoCapture('auto2.avif') 
        frame_idx = 0
        while not self._stop.is_set():
            ok, frame = cap.read()
            if not ok:
                time.sleep(2)
                cap = cv2.VideoCapture(self.url)
                continue
            frame_idx += 1
            if frame_idx % self.sample_every == 0:
                self.on_frame(self.name, frame)
        cap.release()
