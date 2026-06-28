from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils.io import save_json

TARGET_LABELS = {"person", "backpack", "laptop", "book", "bottle", "cup"}


def mock_detections(image_path: str) -> dict[str, Any]:
    return {
        "image": image_path,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": "mock",
        "detections": [
            {
                "id": "det-001",
                "label": "laptop",
                "category": "object",
                "confidence": 0.91,
                "bbox": [78, 118, 154, 166]
            },
            {
                "id": "det-002",
                "label": "book",
                "category": "object",
                "confidence": 0.86,
                "bbox": [118, 162, 184, 204]
            },
            {
                "id": "det-003",
                "label": "person",
                "category": "person",
                "confidence": 0.94,
                "bbox": [268, 68, 392, 232]
            },
            {
                "id": "det-004",
                "label": "bottle",
                "category": "object",
                "confidence": 0.79,
                "bbox": [496, 128, 532, 190]
            }
        ]
    }


def run_yolo(image_path: str, model_name: str = "yolov8n.pt", conf: float = 0.25) -> dict[str, Any]:
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError(
            "ultralytics is not installed. Run `pip install -r requirements.txt` "
            "or use `--mock` for the built-in sample detections."
        ) from exc

    image_file = Path(image_path)
    if not image_file.exists():
        raise FileNotFoundError(f"Image not found: {image_file}")

    model = YOLO(model_name)
    results = model.predict(source=str(image_file), conf=conf, verbose=False)
    detections: list[dict[str, Any]] = []

    for result in results:
        names = result.names
        for idx, box in enumerate(result.boxes):
            class_id = int(box.cls[0])
            label = str(names[class_id])
            if label not in TARGET_LABELS:
                continue
            x1, y1, x2, y2 = [round(float(v), 2) for v in box.xyxy[0].tolist()]
            detections.append({
                "id": f"det-{idx + 1:03d}",
                "label": label,
                "category": "person" if label == "person" else "object",
                "confidence": round(float(box.conf[0]), 4),
                "bbox": [x1, y1, x2, y2]
            })

    return {
        "image": str(image_file),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": "yolov8",
        "model": model_name,
        "detections": detections
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Step 1: run YOLOv8 detection or mock detections.")
    parser.add_argument("--image", default="src/data/sample_library.jpg", help="Input image path.")
    parser.add_argument("--output", default="output/detections.json", help="Output JSON path.")
    parser.add_argument("--model", default="yolov8n.pt", help="Ultralytics model name or path.")
    parser.add_argument("--conf", type=float, default=0.25, help="Detection confidence threshold.")
    parser.add_argument("--mock", action="store_true", help="Use built-in detections without a real image/model.")
    args = parser.parse_args()

    result = mock_detections(args.image) if args.mock else run_yolo(args.image, args.model, args.conf)
    save_json(args.output, result)
    print(f"saved {len(result['detections'])} detections to {args.output}")


if __name__ == "__main__":
    main()

