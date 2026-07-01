from __future__ import annotations

import unittest
from pathlib import Path

from src.dashboard.data_provider import (
    abnormal_seats,
    calculate_crowd_status,
    load_dashboard_data,
    normalize_seats,
)
from src.dashboard.styles import crowding_level_from_ratio, status_label


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

        self.assertEqual(seats["F3-A01"]["suspect_duration"], 25)
        self.assertEqual(seats["F3-A02"]["suspect_duration"], 12)
        self.assertEqual(seats["F3-A03"]["suspect_duration"], 0)

    def test_backend_seat_fields_are_primary(self) -> None:
        warnings: list[dict] = []
        seats, error, layout_error = normalize_seats(
            {
                "seats": [
                    {
                        "seat_id": "F3-A01",
                        "floor": "3",
                        "zone": "A",
                        "camera_id": "CAM-1",
                        "detected_at": "2026-06-25T15:30:00",
                        "has_person": False,
                        "has_object": True,
                        "status": "suspected",
                        "suspect_duration": 22,
                        "roi_x1": 10,
                        "roi_y1": 20,
                        "roi_x2": 110,
                        "roi_y2": 120,
                    }
                ]
            },
            [],
            warnings,
        )

        self.assertIsNone(error)
        self.assertIsNone(layout_error)
        self.assertEqual(seats[0]["status"], "suspected")
        self.assertEqual(seats[0]["detected_at"], "2026-06-25T15:30:00")
        self.assertEqual(seats[0]["suspect_duration"], 22)
        self.assertEqual(seats[0]["roi_x1"], 10.0)
        self.assertNotIn("updated_at", seats[0])
        self.assertNotIn("unattended_minutes", seats[0])
        self.assertNotIn("polygon", seats[0])

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
        self.assertEqual(crowd["total_in_library"], 100)

        crowd_from_api, _ = calculate_crowd_status(
            {
                "capacity": 200,
                "current_num": 88,
                "history": [{"recorded_at": "2026-06-25T15:00:00", "total_in_library": 88}],
            },
            warnings,
        )
        self.assertEqual(crowd_from_api["total_in_library"], 88)

    def test_backend_crowd_fields_are_primary(self) -> None:
        crowd, error = calculate_crowd_status(
            {
                "recorded_at": "2026-06-25T15:30:00",
                "total_in_library": 145,
                "capacity": 220,
                "crowding_level": "medium",
                "history": [{"recorded_at": "2026-06-25T15:00:00", "total_in_library": 140}],
            },
            [],
        )

        self.assertIsNone(error)
        self.assertEqual(crowd["recorded_at"], "2026-06-25T15:30:00")
        self.assertEqual(crowd["total_in_library"], 145)
        self.assertEqual(crowd["crowding_level"], "medium")

    def test_csv_adapter_loads_backend_csv_fields(self) -> None:
        data = load_dashboard_data(
            base_dir=FIXTURES,
            seat_status_path="seat_status_backend.csv",
            crowd_status_path="gate_log_backend.csv",
            seat_layout_path="seat_layout_valid.json",
            data_source="csv",
            csv_capacity=220,
        )
        seats = {seat["seat_id"]: seat for seat in data["seats"]}

        self.assertEqual(data["data_source"], "csv")
        self.assertIsNone(data["errors"]["seat"])
        self.assertIsNone(data["errors"]["crowd"])
        self.assertEqual(data["seat_updated_at"], "2026-06-25 15:30:00")
        self.assertEqual(data["crowd_updated_at"], "2026-06-25 15:30:00")
        self.assertEqual(seats["F3-A01"]["detected_at"], "2026-06-25 15:30:00")
        self.assertEqual(seats["F3-A01"]["suspect_duration"], 28)
        self.assertEqual(seats["F3-A01"]["status"], "suspected")
        self.assertEqual(seats["F3-A03"]["status"], "free")
        self.assertEqual(data["crowd"]["total_in_library"], 125)
        self.assertEqual(data["crowd"]["capacity"], 220)
        self.assertEqual(data["crowd"]["crowding_level"], "medium")
        self.assertEqual(len(data["crowd"]["history"]), 3)

    def test_csv_adapter_does_not_invent_capacity(self) -> None:
        data = load_dashboard_data(
            base_dir=FIXTURES,
            seat_status_path="seat_status_backend.csv",
            crowd_status_path="gate_log_backend.csv",
            seat_layout_path="seat_layout_valid.json",
            data_source="csv",
        )

        self.assertEqual(data["errors"]["crowd"], "invalid_capacity")
        self.assertEqual(data["crowd"]["total_in_library"], 125)
        self.assertIsNone(data["crowd"]["capacity"])

    def test_crowding_level_boundaries(self) -> None:
        cases = [
            (0.49, "low"),
            (0.50, "medium"),
            (0.74, "medium"),
            (0.75, "high"),
            (0.89, "high"),
            (0.90, "full"),
        ]
        for ratio, expected in cases:
            with self.subTest(ratio=ratio):
                self.assertEqual(crowding_level_from_ratio(ratio), expected)

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
                self.assertIsNone(crowd["crowding_level"])

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
        self.assertEqual(error, "invalid_total_in_library")
        self.assertIsNone(crowd["total_in_library"])

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
        self.assertEqual(crowd["total_in_library"], 120)
        self.assertTrue(any(w["code"] == "total_in_library_exceeds_capacity" for w in warnings))

    def test_roi_merge_and_camera_grouping(self) -> None:
        data = self.load_fixture_data()
        seats = {seat["seat_id"]: seat for seat in data["seats"]}
        groups = data["layout_groups"]

        self.assertEqual(seats["F3-A01"]["camera_id"], "CAM-1")
        self.assertEqual(seats["F3-A02"]["camera_id"], "CAM-2")
        self.assertEqual(seats["F3-A01"]["roi_x1"], 50)
        self.assertEqual(seats["F3-A01"]["roi_y1"], 80)
        self.assertEqual(seats["F3-A01"]["roi_x2"], 210)
        self.assertEqual(seats["F3-A01"]["roi_y2"], 220)

        self.assertIn("3|A|CAM-1", groups)
        self.assertIn("3|A|CAM-2", groups)
        self.assertEqual({seat["camera_id"] for seat in groups["3|A|CAM-1"]}, {"CAM-1"})
        self.assertEqual({seat["camera_id"] for seat in groups["3|A|CAM-2"]}, {"CAM-2"})

    def test_missing_roi_returns_clear_status(self) -> None:
        data = self.load_fixture_data(
            seat_status="seat_status_unknown.json",
            seat_layout="seat_layout_missing_polygon.json",
        )
        self.assertEqual(data["errors"]["layout"], "missing_roi")
        self.assertEqual(data["layout_groups"], {})

    def test_abnormal_seat_sorting(self) -> None:
        seats = [
            {"seat_id": "A", "status": "occupied", "suspect_duration": 99, "detected_at": "2026-06-25T15:30:00"},
            {"seat_id": "B", "status": "suspected", "suspect_duration": 20, "detected_at": "2026-06-25T15:30:00"},
            {"seat_id": "C", "status": "suspected", "suspect_duration": 30, "detected_at": "2026-06-25T15:00:00"},
            {"seat_id": "D", "status": "suspected", "suspect_duration": 30, "detected_at": "2026-06-25T15:40:00"},
        ]

        ordered = abnormal_seats(seats)
        self.assertEqual([seat["seat_id"] for seat in ordered], ["D", "C", "B"])

    def test_unknown_status_is_not_defaulted_to_free(self) -> None:
        data = self.load_fixture_data(seat_status="seat_status_unknown.json")
        self.assertEqual(data["seats"][0]["status"], "broken_state")
        self.assertFalse(data["seats"][0]["status_known"])
        self.assertEqual(status_label(data["seats"][0]["status"]), "未知状态")
        self.assertNotEqual(data["seats"][0]["status"], "free")
        self.assertTrue(any(warning["code"] == "unknown_status" for warning in data["warnings"]))


if __name__ == "__main__":
    unittest.main()
