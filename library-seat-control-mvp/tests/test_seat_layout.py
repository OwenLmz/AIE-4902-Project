from __future__ import annotations

import unittest

from src.dashboard.seat_layout import build_svg_seat_layout, group_seats_by_layout, validate_polygon


class SeatLayoutTest(unittest.TestCase):
    def test_valid_polygon_returns_true(self) -> None:
        self.assertTrue(validate_polygon([[0, 0], [10, 0], [10, 10]]))

    def test_polygon_with_less_than_three_points_returns_false(self) -> None:
        self.assertFalse(validate_polygon([[0, 0], [10, 0]]))

    def test_polygon_with_non_numeric_coordinates_returns_false(self) -> None:
        self.assertFalse(validate_polygon([[0, 0], ["x", 0], [10, 10]]))

    def test_missing_polygon_does_not_crash(self) -> None:
        svg = build_svg_seat_layout([{"seat_id": "A01", "status": "FREE"}])
        self.assertIn("暂无座位布局数据", svg)

    def test_unknown_status_does_not_crash_and_shows_unknown_label(self) -> None:
        svg = build_svg_seat_layout([
            {"seat_id": "A01", "status": "BROKEN", "polygon": [[0, 0], [10, 0], [10, 10]]}
        ])
        self.assertIn("未知状态", svg)

    def test_seat_id_is_html_escaped(self) -> None:
        svg = build_svg_seat_layout([
            {"seat_id": "<A&1>", "status": "FREE", "polygon": [[0, 0], [10, 0], [10, 10]]}
        ])
        self.assertIn("&lt;A&amp;1&gt;", svg)
        self.assertNotIn("<A&1>", svg)

    def test_different_camera_ids_are_not_in_same_group(self) -> None:
        groups = group_seats_by_layout([
            {"seat_id": "A01", "floor": "3", "zone": "A", "camera_id": "CAM-1", "polygon": [[0, 0], [10, 0], [10, 10]]},
            {"seat_id": "A02", "floor": "3", "zone": "A", "camera_id": "CAM-2", "polygon": [[0, 0], [10, 0], [10, 10]]},
        ])
        self.assertIn("3|A|CAM-1", groups)
        self.assertIn("3|A|CAM-2", groups)
        self.assertEqual(len(groups["3|A|CAM-1"]["seats"]), 1)
        self.assertEqual(len(groups["3|A|CAM-2"]["seats"]), 1)

    def test_same_floor_zone_camera_are_in_same_group(self) -> None:
        groups = group_seats_by_layout([
            {"seat_id": "A01", "floor": "3", "zone": "A", "camera_id": "CAM-1", "polygon": [[0, 0], [10, 0], [10, 10]]},
            {"seat_id": "A02", "floor": "3", "zone": "A", "camera_id": "CAM-1", "polygon": [[20, 0], [30, 0], [30, 10]]},
        ])
        self.assertEqual(len(groups["3|A|CAM-1"]["seats"]), 2)

    def test_selected_seat_id_creates_highlight_style(self) -> None:
        svg = build_svg_seat_layout([
            {"seat_id": "A01", "status": "FREE", "polygon": [[0, 0], [10, 0], [10, 10]]}
        ], selected_seat_id="A01")
        self.assertIn("seat-selected", svg)

    def test_free_seat_has_stronger_visual_weight(self) -> None:
        svg = build_svg_seat_layout([
            {"seat_id": "A01", "status": "FREE", "polygon": [[0, 0], [10, 0], [10, 10]]},
            {"seat_id": "A02", "status": "OCCUPIED", "polygon": [[20, 0], [30, 0], [30, 10]]},
        ])
        self.assertIn("cinema-seat-map", svg)
        self.assertIn("seat-free-strong", svg)
        self.assertIn("seat-occupied-muted", svg)

    def test_layout_uses_cinema_seat_map_container(self) -> None:
        svg = build_svg_seat_layout([
            {"seat_id": "A01", "status": "FREE", "polygon": [[0, 0], [10, 0], [10, 10]]}
        ])
        self.assertIn("<style>", svg)
        self.assertIn("cinema-seat-map", svg)
        self.assertIn("seat-chip", svg)

    def test_recommended_seat_has_star_marker_class(self) -> None:
        svg = build_svg_seat_layout([
            {"seat_id": "F3-A04", "status": "FREE", "polygon": [[0, 0], [10, 0], [10, 10]]}
        ], recommended_seat_id="F3-A04")
        self.assertIn("seat-recommended", svg)
        self.assertIn(">A04<", svg)

    def test_admin_mode_emphasizes_suspicious_seat(self) -> None:
        svg = build_svg_seat_layout([
            {"seat_id": "A01", "status": "SUSPICIOUS", "polygon": [[0, 0], [10, 0], [10, 10]]}
        ], mode="admin")
        self.assertIn("seat-suspected-strong", svg)

    def test_svg_contains_no_script_or_external_image(self) -> None:
        svg = build_svg_seat_layout([
            {"seat_id": "A01", "status": "FREE", "polygon": [[0, 0], [10, 0], [10, 10]]}
        ])
        lowered = svg.lower()
        self.assertNotIn("<script", lowered)
        self.assertNotIn("<img", lowered)
        self.assertNotIn("http://", lowered)
        self.assertNotIn("https://", lowered)

    def test_empty_seats_returns_clear_empty_state(self) -> None:
        svg = build_svg_seat_layout([])
        self.assertIn("暂无座位布局数据", svg)


if __name__ == "__main__":
    unittest.main()
