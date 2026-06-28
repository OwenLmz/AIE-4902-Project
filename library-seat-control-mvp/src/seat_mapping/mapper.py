from __future__ import annotations

import argparse
from typing import Any

from src.utils.io import load_json, save_json

OBJECT_LABELS = {"backpack", "laptop", "book", "bottle", "cup"}


def bbox_center(bbox: list[float]) -> tuple[float, float]:
    x1, y1, x2, y2 = bbox
    return (x1 + x2) / 2, (y1 + y2) / 2


def point_in_polygon(point: tuple[float, float], polygon: list[list[float]]) -> bool:
    x, y = point
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        crosses = (yi > y) != (yj > y)
        if crosses:
            x_at_y = (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi
            if x < x_at_y:
                inside = not inside
        j = i
    return inside


def polygon_bbox(polygon: list[list[float]]) -> list[float]:
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    return [min(xs), min(ys), max(xs), max(ys)]


def bbox_iou(a: list[float], b: list[float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter == 0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    return inter / (area_a + area_b - inter)


def belongs_to_seat(detection: dict[str, Any], polygon: list[list[float]], iou_threshold: float) -> bool:
    bbox = detection["bbox"]
    center_hit = point_in_polygon(bbox_center(bbox), polygon)
    overlap_hit = bbox_iou(bbox, polygon_bbox(polygon)) >= iou_threshold
    return center_hit or overlap_hit


def map_detections_to_seats(
    seats: list[dict[str, Any]],
    detection_payload: dict[str, Any],
    iou_threshold: float = 0.1
) -> dict[str, Any]:
    detections = detection_payload.get("detections", [])
    mapped: list[dict[str, Any]] = []

    for seat in seats:
        polygon = seat["polygon"]
        seat_detections = [
            det for det in detections
            if det.get("label") in {"person", *OBJECT_LABELS}
            and belongs_to_seat(det, polygon, iou_threshold)
        ]
        labels = [det["label"] for det in seat_detections]
        mapped.append({
            "seat_id": seat["seat_id"],
            "floor": seat.get("floor"),
            "zone": seat.get("zone"),
            "camera_id": seat.get("camera_id"),
            "polygon": polygon,
            "has_person": "person" in labels,
            "has_object": any(label in OBJECT_LABELS for label in labels),
            "detections": seat_detections
        })

    return {
        "image": detection_payload.get("image"),
        "generated_at": detection_payload.get("generated_at"),
        "source": detection_payload.get("source"),
        "seats": mapped
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Step 2: map detections to seat polygons.")
    parser.add_argument("--seats", default="src/data/seats.json", help="Seat polygon JSON path.")
    parser.add_argument("--detections", default="output/detections.json", help="Detection JSON path.")
    parser.add_argument("--output", default="output/mapped_seats.json", help="Mapped seats JSON path.")
    parser.add_argument("--iou-threshold", type=float, default=0.1, help="BBox-to-seat IoU threshold.")
    args = parser.parse_args()

    seats = load_json(args.seats)
    detections = load_json(args.detections)
    result = map_detections_to_seats(seats, detections, args.iou_threshold)
    save_json(args.output, result)
    print(f"mapped {len(result['seats'])} seats to {args.output}")


if __name__ == "__main__":
    main()

