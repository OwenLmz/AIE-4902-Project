from __future__ import annotations

import unittest

from src.geometry import detection_overlaps_seat
from src.state import build_seat_result
from src.types import Detection, SeatConfig


class CoreLogicTest(unittest.TestCase):
    def setUp(self) -> None:
        self.seat = SeatConfig(
            seat_id="F3-A01",
            floor=3,
            zone="A",
            camera_id="CAM-3A",
            roi_x1=100,
            roi_y1=100,
            roi_x2=200,
            roi_y2=200,
            is_active=True,
        )

    def test_detection_center_inside_roi_matches(self) -> None:
        detection = Detection("person", 0.9, 120, 120, 180, 180)
        self.assertTrue(detection_overlaps_seat(detection, self.seat, 0.3))

    def test_detection_outside_roi_does_not_match(self) -> None:
        detection = Detection("person", 0.9, 220, 220, 280, 280)
        self.assertFalse(detection_overlaps_seat(detection, self.seat, 0.3))

    def test_person_resets_suspect_duration(self) -> None:
        result = build_seat_result(self.seat, "2025-04-01 09:00:00", True, True, 30, 30, 20)
        self.assertEqual(result.status, "occupied")
        self.assertEqual(result.suspect_duration, 0)

    def test_object_without_person_becomes_suspected(self) -> None:
        result = build_seat_result(self.seat, "2025-04-01 09:00:00", False, True, 0, 30, 20)
        self.assertEqual(result.status, "suspected")
        self.assertEqual(result.suspect_duration, 30)

    def test_free_resets_suspect_duration(self) -> None:
        result = build_seat_result(self.seat, "2025-04-01 09:00:00", False, False, 30, 30, 20)
        self.assertEqual(result.status, "free")
        self.assertEqual(result.suspect_duration, 0)


if __name__ == "__main__":
    unittest.main()

