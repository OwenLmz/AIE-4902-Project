from __future__ import annotations

from .types import Detection, SeatConfig


Box = tuple[float, float, float, float]


def box_area(box: Box) -> float:
    x1, y1, x2, y2 = box
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def intersection_area(a: Box, b: Box) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    x1 = max(ax1, bx1)
    y1 = max(ay1, by1)
    x2 = min(ax2, bx2)
    y2 = min(ay2, by2)
    return box_area((x1, y1, x2, y2))


def iou(a: Box, b: Box) -> float:
    inter = intersection_area(a, b)
    union = box_area(a) + box_area(b) - inter
    if union <= 0:
        return 0.0
    return inter / union


def center_inside(inner: Box, outer: Box) -> bool:
    x1, y1, x2, y2 = inner
    ox1, oy1, ox2, oy2 = outer
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    return ox1 <= cx <= ox2 and oy1 <= cy <= oy2


def detection_overlaps_seat(detection: Detection, seat: SeatConfig, threshold: float) -> bool:
    det_box = detection.box
    roi = seat.roi
    if center_inside(det_box, roi):
        return True

    det_area = box_area(det_box)
    if det_area <= 0:
        return False
    overlap_ratio = intersection_area(det_box, roi) / det_area
    return overlap_ratio >= threshold or iou(det_box, roi) >= threshold

