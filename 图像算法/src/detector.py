from __future__ import annotations

import shutil
import urllib.request
from pathlib import Path

from .types import Detection


YOLOV8N_URL = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt"


class DetectorError(RuntimeError):
    pass


def ensure_model(model_path: str | Path, auto_download: bool = True) -> Path:
    path = Path(model_path)
    if path.exists():
        return path

    if not auto_download:
        raise DetectorError(f"Model file not found: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        print(f"Model not found. Downloading YOLOv8n to {path} ...")
        urllib.request.urlretrieve(YOLOV8N_URL, path)
        return path
    except Exception as direct_error:
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise DetectorError(
                "Cannot download model because ultralytics is not installed. "
                "Run setup.ps1 or pip install -r requirements.txt."
            ) from exc

        try:
            model = YOLO("yolov8n.pt")
            candidate = Path("yolov8n.pt")
            if candidate.exists():
                shutil.copy2(candidate, path)
                return path
            if getattr(model, "ckpt_path", None):
                ckpt = Path(model.ckpt_path)
                if ckpt.exists():
                    shutil.copy2(ckpt, path)
                    return path
        except Exception as ultralytics_error:
            raise DetectorError(
                f"Failed to download YOLOv8n model. Direct error: {direct_error}; "
                f"Ultralytics error: {ultralytics_error}"
            ) from ultralytics_error

    if not path.exists():
        raise DetectorError(f"Model download finished but file is still missing: {path}")
    return path


class YoloDetector:
    def __init__(
        self,
        model_path: str | Path,
        confidence: float,
        image_size: int,
        device: str = "cpu",
        auto_download: bool = True,
    ) -> None:
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise DetectorError("Missing dependency ultralytics. Run setup.ps1 first.") from exc

        resolved = ensure_model(model_path, auto_download=auto_download)
        self.model = YOLO(str(resolved))
        self.confidence = confidence
        self.image_size = image_size
        self.device = device

    def detect(self, image_path: str | Path) -> list[Detection]:
        result = self.model.predict(
            source=str(image_path),
            imgsz=self.image_size,
            conf=self.confidence,
            device=self.device,
            verbose=False,
        )[0]

        names = result.names
        detections: list[Detection] = []
        if result.boxes is None:
            return detections

        for box in result.boxes:
            xyxy = box.xyxy[0].tolist()
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            detections.append(
                Detection(
                    class_name=str(names.get(cls_id, cls_id)),
                    confidence=conf,
                    x1=float(xyxy[0]),
                    y1=float(xyxy[1]),
                    x2=float(xyxy[2]),
                    y2=float(xyxy[3]),
                )
            )
        return detections

