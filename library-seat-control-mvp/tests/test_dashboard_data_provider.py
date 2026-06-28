from __future__ import annotations

import unittest
from pathlib import Path

from src.dashboard.data_provider import (
    abnormal_seats,
    calculate_crowd_status,
    load_dashboard_data,
)
from src.dashboard.styles import crowd_level_from_ratio, status_label


FIXTURES = Path(__file__).parent / "fixtures"


class DashboardDataProviderTest(unittest.TestCase):
    def load_fixture_data(
        self,
        seat_status: str = "seat_status_valid.json",
        crowd_status: str = "crowd_status_valid.json",
        seat_layout: str = "seat_layout_valid.json",
    ) -> dict:
        return load_dashboard_data(
            base_dir=FIXTURES,
            seat_status_path=seat_status,
            crowd_status_path=crowd_status,
            seat_layout_path=seat_layout,
        )

    def test_seat_unattended_field_compatibility(self) -> None:
        data = self.load_fixture_data()
        seats = {seat["seat_id"]: seat for seat in data["seats"]}

        self.assertEqual(seats["F3-A01"]["unattended_minutes"], 25)
        self.assertEqual(seats["F3-A02"]["unattended_minutes"], 12)
        self.assertEqual(seats["F3-A03"]["unattended_minutes"], 0)

    def test_crowd_field_compatibility(self) -> None:
        warnings: list[dict] = []
        crowd, error = calculate_crowd_status(
            {
                "capacity": 200,
                "latest": {"total_in_library": 100},
                "history": [{"recorded_at": "2026-06-25T15:00:00", "total_in_library": 100}],
            },
            warnings,
        )
        self.assertIsNone(error)
        self.assertEqual(crowd["current_people"], 100)

        crowd_from_api, _ = calculate_crowd_status(
            {
                "capacity": 200,
                "current_num": 88,
                "history": [{"recorded_at": "2026-06-25T15:00:00", "total_in_library": 88}],
            },
            warnings,
        )
        self.assertEqual(crowd_from_api["current_people"], 88)

    def test_crowd_level_boundaries(self) -> None:
        cases = [
            (0.49, "LOW"),
            (0.50, "MEDIUM"),
            (0.74, "MEDIUM"),
            (0.75, "HIGH"),
            (0.89, "HIGH"),
            (0.90, "FULL"),
        ]
        for ratio, expected in cases:
            with self.subTest(ratio=ratio):
                self.assertEqual(crowd_level_from_ratio(ratio), expected)

    def test_invalid_capacity(self) -> None:
        for capacity in (None, 0, -1):
            with self.subTest(capacity=capacity):
                payload = {
                    "current_num": 20,
                    "history": [{"recorded_at": "2026-06-25T15:00:00", "total_in_library": 20}],
                }
                if capacity is not None:
                    payload["capacity"] = capacity
                crowd, error = calculate_crowd_status(payload, [])
                self.assertEqual(error, "invalid_capacity")
                self.assertIsNone(crowd["crowd_level"])

    def test_data_errors(self) -> None:
        missing = self.load_fixture_data(seat_status="missing.json")
        self.assertEqual(missing["errors"]["seat"], "missing_file")

        invalid = self.load_fixture_data(seat_status="invalid_json.json")
        self.assertEqual(invalid["errors"]["seat"], "invalid_json")

        empty_seats = self.load_fixture_data(seat_status="seat_status_empty.json")
        self.assertEqual(empty_seats["errors"]["seat"], "empty_seats")

        empty_history = self.load_fixture_data(crowd_status="crowd_status_empty_history.json")
        self.assertEqual(empty_history["errors"]["crowd"], "empty_history")

        duplicate = self.load_fixture_data(seat_status="seat_status_duplicate.json")
        self.assertEqual(duplicate["errors"]["seat"], "duplicate_seat_id")

    def test_crowd_quality_validation(self) -> None:
        crowd, error = calculate_crowd_status(
            {
                "capacity": 100,
                "current_num": -1,
                "history": [{"recorded_at": "2026-06-25T15:00:00", "total_in_library": 0}],
            },
            [],
        )
        self.assertEqual(error, "invalid_current_people")
        self.assertIsNone(crowd["current_people"])

        warnings: list[dict] = []
        crowd, error = calculate_crowd_status(
            {
                "capacity": 100,
                "current_num": 120,
                "history": [{"recorded_at": "2026-06-25T15:00:00", "total_in_library": 120}],
            },
            warnings,
        )
        self.assertIsNone(error)
        self.assertEqual(crowd["current_people"], 120)
        self.assertTrue(any(w["code"] == "current_people_exceeds_capacity" for w in warnings))

    def test_polygon_merge_and_camera_grouping(self) -> None:
        data = self.load_fixture_data()
        seats = {seat["seat_id"]: seat for seat in data["seats"]}
        groups = data["layout_groups"]

        self.assertEqual(seats["F3-A01"]["camera_id"], "CAM-1")
        self.assertEqual(seats["F3-A02"]["camera_id"], "CAM-2")
        self.assertIsNotNone(seats["F3-A01"]["polygon"])

        self.assertIn("3|A|CAM-1", groups)
        self.assertIn("3|A|CAM-2", groups)
        self.assertEqual({seat["camera_id"] for seat in groups["3|A|CAM-1"]}, {"CAM-1"})
        self.assertEqual({seat["camera_id"] for seat in groups["3|A|CAM-2"]}, {"CAM-2"})

    def test_missing_polygon_returns_clear_status(self) -> None:
        data = self.load_fixture_data(
            seat_status="seat_status_unknown.json",
            seat_layout="seat_layout_missing_polygon.json",
        )
        self.assertEqual(data["errors"]["layout"], "missing_polygon")
        self.assertEqual(data["layout_groups"], {})

    def test_abnormal_seat_sorting(self) -> None:
        seats = [
            {"seat_id": "A", "status": "POSSIBLY_OCCUPIED", "unattended_minutes": 99, "updated_at": "2026-06-25T15:30:00"},
            {"seat_id": "B", "status": "SUSPICIOUS", "unattended_minutes": 20, "updated_at": "2026-06-25T15:30:00"},
            {"seat_id": "C", "status": "SUSPICIOUS", "unattended_minutes": 30, "updated_at": "2026-06-25T15:00:00"},
            {"seat_id": "D", "status": "SUSPICIOUS", "unattended_minutes": 30, "updated_at": "2026-06-25T15:40:00"},
        ]

        ordered = abnormal_seats(seats)
        self.assertEqual([seat["seat_id"] for seat in ordered], ["D", "C", "B", "A"])

    def test_unknown_status_is_not_defaulted_to_free(self) -> None:
        data = self.load_fixture_data(seat_status="seat_status_unknown.json")
        self.assertEqual(data["seats"][0]["status"], "BROKEN_STATE")
        self.assertFalse(data["seats"][0]["status_known"])
        self.assertEqual(status_label(data["seats"][0]["status"]), "未知状态")
        self.assertNotEqual(data["seats"][0]["status"], "FREE")
        self.assertTrue(any(warning["code"] == "unknown_status" for warning in data["warnings"]))


if __name__ == "__main__":
    unittest.main()
