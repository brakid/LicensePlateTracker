"""License plate detection + OCR pipeline. Kept pure for testability."""
import cv2


def detect_plates(frame, model, threshold=0.75):
    """Run YOLO model; return list of (x1,y1,x2,y2,conf)."""
    results = model.predict(frame, verbose=False)
    plates = []
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0].item())
            if conf >= threshold:
                plates.append((x1, y1, x2, y2, conf))
    return plates


def crop_plate(frame, box):
    x1, y1, x2, y2, _ = box
    return frame[y1:y2, x1:x2]


def recognize_plate(crop, recognizer):
    """Run fast-plate-ocr recognizer on a cropped plate image."""
    preds = recognizer.run(crop)
    # preds may be list of strings or PlatePrediction
    if isinstance(preds, (list, tuple)):
        text = preds[0] if preds else ""
    else:
        text = str(preds)
    if hasattr(text, "plate"):
        text = text.plate
    return "".join(str(text).split()).upper()


def normalize_plate(text: str) -> str:
    return "".join(ch for ch in text.upper() if ch.isalnum())
