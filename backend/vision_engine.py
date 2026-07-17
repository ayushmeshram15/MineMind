from pathlib import Path
from tempfile import NamedTemporaryFile
from collections import Counter
import os

MODEL_NAME = os.getenv("MINEMIND_YOLO_MODEL", "yolo11n.pt")
SAMPLE_EVERY = int(os.getenv("MINEMIND_VISION_SAMPLE_EVERY", "8"))


def analyze_video_bytes(data: bytes, suffix: str = ".mp4"):
    try:
        import cv2
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError("Vision dependencies missing. Run: python3 -m pip install -r requirements.txt") from exc

    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
        video_path = tmp.name

    cap = None
    try:
        model = YOLO(MODEL_NAME)
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Could not open uploaded video")

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
        counts = Counter()
        confidences = {}
        sampled = 0
        frame_index = 0

        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if frame_index % SAMPLE_EVERY == 0:
                result = model.predict(frame, verbose=False, conf=0.30, imgsz=640)[0]
                sampled += 1
                for box in result.boxes:
                    cls_id = int(box.cls[0].item())
                    label = model.names[cls_id].upper().replace(" ", "_")
                    conf = float(box.conf[0].item())
                    counts[label] += 1
                    confidences[label] = max(confidences.get(label, 0.0), conf)
            frame_index += 1

        priority = ["TRUCK", "CAR", "BUS", "PERSON", "MOTORCYCLE", "BICYCLE"]
        detections = []
        for label in priority:
            if label in counts:
                detections.append({"label": label, "count": counts[label], "confidence": round(confidences[label] * 100, 1)})
        for label, count in counts.most_common():
            if label not in priority:
                detections.append({"label": label, "count": count, "confidence": round(confidences[label] * 100, 1)})
        detections = detections[:10]

        vehicle_hits = sum(counts[x] for x in ("TRUCK", "CAR", "BUS"))
        person_hits = counts["PERSON"]
        if vehicle_hits >= max(3, sampled // 2):
            classification = "VEHICLE_ACTIVITY_DETECTED"
            severity = "WARNING"
            description = f"YOLO detected sustained vehicle activity across {sampled} sampled frames. Review haul-road flow and dispatch spacing."
        elif person_hits:
            classification = "PERSON_PRESENCE_DETECTED"
            severity = "WARNING"
            description = f"YOLO detected person presence in {person_hits} sampled-frame detections. Review camera zone safety context."
        else:
            classification = "NO_OPERATIONAL_TARGET_DETECTED"
            severity = "INFO"
            description = f"YOLO completed real inference on {sampled} sampled frames; no configured operational target exceeded the alert threshold."

        return {
            "model": MODEL_NAME,
            "real_inference": True,
            "frames_total": frame_count,
            "frames_sampled": sampled,
            "fps": round(fps, 2),
            "classification": classification,
            "severity": severity,
            "description": description,
            "detections": detections,
        }
    finally:
        if cap is not None:
            cap.release()
        Path(video_path).unlink(missing_ok=True)
