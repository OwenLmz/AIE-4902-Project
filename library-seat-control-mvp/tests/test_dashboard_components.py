from __future__ import annotations

import unittest

from src.dashboard.components import ADMIN_SECTION_TABS, STUDENT_SECTION_TABS, build_area_summary, build_crowd_trend_frame
from src.dashboard.components import _build_static_crowd_trend_chart
from src.dashboard.components import build_crowd_range_coverage_note
from src.dashboard.components import build_crowd_trend_frame_for_range, build_crowd_trend_summary, filter_crowd_history_by_range
from src.dashboard.components import build_anomaly_display_rows
from src.dashboard.components import build_admin_summary, build_anomaly_rows, _same_layout_group
from src.dashboard.seat_layout import build_svg_seat_layout


class DashboardComponentsTest(unittest.TestCase):
    def test_structured_tab_labels_are_fixed(self) -> None:
        self.assertEqual(STUDENT_SECTION_TABS, ["总览", "区域推荐", "座位地图", "人流趋势"])
        self.assertEqual(ADMIN_SECTION_TABS, ["管理概览", "异常座位", "异常定位"])

    def test_build_area_summary_groups_by_floor_zone(self) -> None:
        summary = build_area_summary([
            {"seat_id": "A01", "floor": "3", "zone": "A", "status": "FREE"},
            {"seat_id": "A02", "floor": "3", "zone": "A", "status": "OCCUPIED"},
            {"seat_id": "B01", "floor": "3", "zone": "B", "status": "FREE"},
        ])

        self.assertEqual(len(summary), 2)
        self.assertEqual(
            {(row["floor"], row["zone"]) for row in summary},
            {("3", "A"), ("3", "B")},
        )

    def test_build_area_summary_counts_all_statuses(self) -> None:
        summary = build_area_summary([
            {"seat_id": "A01", "floor": "3", "zone": "A", "status": "FREE"},
            {"seat_id": "A02", "floor": "3", "zone": "A", "status": "OCCUPIED"},
            {"seat_id": "A03", "floor": "3", "zone": "A", "status": "POSSIBLY_OCCUPIED"},
            {"seat_id": "A04", "floor": "3", "zone": "A", "status": "SUSPICIOUS"},
            {"seat_id": "A05", "floor": "3", "zone": "A", "status": "UNAVAILABLE"},
        ])[0]

        self.assertEqual(summary["total_seats"], 5)
        self.assertEqual(summary["free_seats"], 1)
        self.assertEqual(summary["occupied_seats"], 1)
        self.assertEqual(summary["temporarily_unavailable_seats"], 1)
        self.assertEqual(summary["suspicious_seats"], 1)
        self.assertEqual(summary["unavailable_seats"], 1)

    def test_available_ratio_excludes_unavailable(self) -> None:
        summary = build_area_summary([
            {"seat_id": "A01", "floor": "3", "zone": "A", "status": "FREE"},
            {"seat_id": "A02", "floor": "3", "zone": "A", "status": "UNAVAILABLE"},
        ])[0]

        self.assertEqual(summary["available_ratio"], 1.0)
        self.assertEqual(summary["available_ratio_label"], "100%")

    def test_no_usable_capacity_does_not_divide_by_zero(self) -> None:
        summary = build_area_summary([
            {"seat_id": "A01", "floor": "3", "zone": "A", "status": "UNAVAILABLE"}
        ])[0]

        self.assertIsNone(summary["available_ratio"])
        self.assertEqual(summary["area_status_label"], "暂无可用容量")

    def test_no_free_seats_label(self) -> None:
        summary = build_area_summary([
            {"seat_id": "A01", "floor": "3", "zone": "A", "status": "OCCUPIED"}
        ])[0]
        self.assertEqual(summary["area_status_label"], "暂无空位")

    def test_area_status_labels(self) -> None:
        high = build_area_summary([
            {"seat_id": "A01", "floor": "3", "zone": "A", "status": "FREE"},
            {"seat_id": "A02", "floor": "3", "zone": "A", "status": "OCCUPIED"},
        ])[0]
        medium = build_area_summary([
            {"seat_id": "A01", "floor": "3", "zone": "A", "status": "FREE"},
            {"seat_id": "A02", "floor": "3", "zone": "A", "status": "OCCUPIED"},
            {"seat_id": "A03", "floor": "3", "zone": "A", "status": "OCCUPIED"},
        ])[0]
        low = build_area_summary([
            {"seat_id": "A01", "floor": "3", "zone": "A", "status": "FREE"},
            *[
                {"seat_id": f"A{i:02d}", "floor": "3", "zone": "A", "status": "OCCUPIED"}
                for i in range(2, 12)
            ],
        ])[0]

        self.assertEqual(high["area_status_label"], "空闲较多")
        self.assertEqual(medium["area_status_label"], "座位紧张")
        self.assertEqual(low["area_status_label"], "接近满座")

    def test_area_recommendation_sorts_by_free_ratio_and_anomalies(self) -> None:
        summary = build_area_summary([
            {"seat_id": "A01", "floor": "3", "zone": "A", "status": "FREE"},
            {"seat_id": "A02", "floor": "3", "zone": "A", "status": "OCCUPIED"},
            {"seat_id": "B01", "floor": "3", "zone": "B", "status": "FREE"},
            {"seat_id": "B02", "floor": "3", "zone": "B", "status": "FREE"},
            {"seat_id": "B03", "floor": "3", "zone": "B", "status": "SUSPICIOUS"},
            {"seat_id": "C01", "floor": "3", "zone": "C", "status": "FREE"},
            {"seat_id": "C02", "floor": "3", "zone": "C", "status": "FREE"},
        ])

        self.assertEqual((summary[0]["floor"], summary[0]["zone"]), ("3", "C"))
        self.assertEqual(summary[0]["recommendation_label"], "推荐去")
        self.assertEqual((summary[1]["floor"], summary[1]["zone"]), ("3", "B"))
        self.assertEqual(summary[1]["recommendation_label"], "可考虑")

    def test_area_without_free_seats_is_not_recommended(self) -> None:
        summary = build_area_summary([
            {"seat_id": "A01", "floor": "3", "zone": "A", "status": "OCCUPIED"},
        ])[0]

        self.assertEqual(summary["recommendation_label"], "不建议")

    def test_empty_seats_returns_empty_summary(self) -> None:
        self.assertEqual(build_area_summary([]), [])

    def test_unknown_status_does_not_crash_summary(self) -> None:
        summary = build_area_summary([
            {"seat_id": "A01", "floor": "3", "zone": "A", "status": "BROKEN"}
        ])[0]

        self.assertEqual(summary["total_seats"], 1)
        self.assertEqual(summary["free_seats"], 0)
        self.assertEqual(summary["area_status_label"], "暂无空位")

    def test_empty_history_returns_empty_state(self) -> None:
        trend = build_crowd_trend_frame({"history": [], "capacity": 100})
        self.assertEqual(trend["rows"], [])
        self.assertEqual(trend["empty_reason"], "empty_history")

    def test_missing_capacity_does_not_add_capacity_line(self) -> None:
        trend = build_crowd_trend_frame({
            "history": [{"recorded_at": "2026-06-23 09:00:00", "total_in_library": 80}]
        })

        self.assertFalse(trend["has_capacity_line"])
        self.assertNotIn("容量参考线", trend["rows"][0])

    def test_missing_forecast_does_not_generate_prediction(self) -> None:
        trend = build_crowd_trend_frame({
            "capacity": 100,
            "history": [{"recorded_at": "2026-06-23 09:00:00", "total_in_library": 80}],
        })

        self.assertFalse(trend["forecast_available"])
        self.assertNotIn("未来预测人数", trend["rows"][0])

    def test_time_range_comes_from_history(self) -> None:
        trend = build_crowd_trend_frame({
            "capacity": 100,
            "history": [
                {"recorded_at": "2026-06-23 09:00:00", "total_in_library": 80},
                {"recorded_at": "2026-06-23 18:00:00", "total_in_library": 60},
            ],
        })

        self.assertEqual(
            trend["time_range"],
            "2026-06-23 09:00:00 至 2026-06-23 18:00:00",
        )
        self.assertTrue(trend["has_capacity_line"])
        self.assertIn("容量参考线", trend["rows"][0])

    def test_filter_crowd_history_near_3_hours_uses_latest_time(self) -> None:
        history = [
            {"recorded_at": "2026-06-23 07:59:59", "total_in_library": 30},
            {"recorded_at": "2026-06-23 08:00:00", "total_in_library": 40},
            {"recorded_at": "2026-06-23 10:00:00", "total_in_library": 80},
            {"recorded_at": "2026-06-23 11:00:00", "total_in_library": 100},
        ]

        filtered = filter_crowd_history_by_range(history, "近3小时")

        self.assertEqual([row["recorded_at"] for row in filtered], [
            "2026-06-23 08:00:00",
            "2026-06-23 10:00:00",
            "2026-06-23 11:00:00",
        ])

    def test_filter_crowd_history_today_uses_latest_date(self) -> None:
        history = [
            {"recorded_at": "2026-06-22 23:59:59", "total_in_library": 20},
            {"recorded_at": "2026-06-23 00:00:00", "total_in_library": 30},
            {"recorded_at": "2026-06-23 12:00:00", "total_in_library": 90},
        ]

        filtered = filter_crowd_history_by_range(history, "今日")

        self.assertEqual([row["recorded_at"] for row in filtered], [
            "2026-06-23 00:00:00",
            "2026-06-23 12:00:00",
        ])

    def test_filter_crowd_history_near_3_days(self) -> None:
        history = [
            {"recorded_at": "2026-06-19 23:59:59", "total_in_library": 20},
            {"recorded_at": "2026-06-20 12:00:00", "total_in_library": 40},
            {"recorded_at": "2026-06-23 12:00:00", "total_in_library": 100},
        ]

        filtered = filter_crowd_history_by_range(history, "近3天")

        self.assertEqual([row["recorded_at"] for row in filtered], [
            "2026-06-20 12:00:00",
            "2026-06-23 12:00:00",
        ])

    def test_range_filter_is_not_based_on_system_current_time(self) -> None:
        history = [
            {"recorded_at": "2024-01-01 08:00:00", "total_in_library": 10},
            {"recorded_at": "2024-01-01 10:00:00", "total_in_library": 20},
        ]

        filtered = filter_crowd_history_by_range(history, "近3小时")

        self.assertEqual(len(filtered), 2)

    def test_range_frame_returns_empty_when_data_is_insufficient(self) -> None:
        trend = build_crowd_trend_frame_for_range({
            "capacity": 100,
            "history": [{"recorded_at": "2026-06-23 09:00:00", "total_in_library": 80}],
        }, "近3小时")

        self.assertEqual(trend["rows"], [])
        self.assertEqual(trend["empty_reason"], "insufficient_range_data")

    def test_range_frame_missing_forecast_does_not_generate_prediction(self) -> None:
        trend = build_crowd_trend_frame_for_range({
            "capacity": 100,
            "history": [
                {"recorded_at": "2026-06-23 09:00:00", "total_in_library": 80},
                {"recorded_at": "2026-06-23 10:00:00", "total_in_library": 90},
            ],
        }, "近3小时")

        self.assertFalse(trend["forecast_available"])
        self.assertNotIn("未来预测人数", trend["rows"][0])

    def test_crowd_trend_summary_outputs_direction_labels(self) -> None:
        upward = build_crowd_trend_frame_for_range({
            "current_people": 90,
            "capacity": 100,
            "crowd_level": "medium",
            "history": [
                {"recorded_at": "2026-06-23 09:00:00", "total_in_library": 80},
                {"recorded_at": "2026-06-23 10:00:00", "total_in_library": 90},
            ],
        }, "近3小时")
        self.assertIn("整体上升", build_crowd_trend_summary({"current_people": 90, "capacity": 100, "crowd_level": "medium"}, upward))

        downward = build_crowd_trend_frame_for_range({
            "current_people": 70,
            "capacity": 100,
            "history": [
                {"recorded_at": "2026-06-23 09:00:00", "total_in_library": 90},
                {"recorded_at": "2026-06-23 10:00:00", "total_in_library": 70},
            ],
        }, "今日")
        self.assertIn("整体下降", build_crowd_trend_summary({"current_people": 70, "capacity": 100}, downward))

        stable = build_crowd_trend_frame_for_range({
            "current_people": 101,
            "capacity": 100,
            "crowd_level": "medium",
            "history": [
                {"recorded_at": "2026-06-23 09:00:00", "total_in_library": 100},
                {"recorded_at": "2026-06-23 10:00:00", "total_in_library": 101},
            ],
        }, "近3小时")
        self.assertIn("整体稳定", build_crowd_trend_summary({"current_people": 101, "capacity": 100, "crowd_level": "medium"}, stable))

    def test_crowd_trend_summary_outputs_insufficient_data(self) -> None:
        trend = build_crowd_trend_frame_for_range({
            "capacity": 100,
            "history": [{"recorded_at": "2026-06-23 09:00:00", "total_in_library": 80}],
        }, "近3小时")

        self.assertEqual(
            build_crowd_trend_summary({"capacity": 100}, trend),
            "当前数据量不足，暂无法判断趋势。",
        )

    def test_crowd_trend_chart_uses_intermediate_time_ticks(self) -> None:
        trend = build_crowd_trend_frame_for_range({
            "capacity": 120,
            "history": [
                {"recorded_at": "2026-06-23 09:00:00", "total_in_library": 60},
                {"recorded_at": "2026-06-23 10:00:00", "total_in_library": 80},
                {"recorded_at": "2026-06-23 11:00:00", "total_in_library": 100},
            ],
        }, "近3小时")

        chart = _build_static_crowd_trend_chart(trend)

        self.assertIn("class='crowd-x-grid'", chart)
        self.assertIn("class='crowd-x-label'", chart)
        self.assertIn(">09:30<", chart)
        self.assertIn(">10:30<", chart)

    def test_crowd_trend_chart_keeps_hover_tooltips_and_area_fill(self) -> None:
        trend = build_crowd_trend_frame_for_range({
            "capacity": 120,
            "history": [
                {"recorded_at": "2026-06-23 09:00:00", "total_in_library": 60},
                {"recorded_at": "2026-06-23 11:00:00", "total_in_library": 100},
            ],
        }, "近3小时")

        chart = _build_static_crowd_trend_chart(trend)

        self.assertIn("class='crowd-area-fill'", chart)
        self.assertIn("class='crowd-hover-region'", chart)
        self.assertIn("09:00 · 60 人", chart)
        self.assertIn("11:00 · 100 人", chart)
        self.assertIn("touch-action:pan-y", chart)

    def test_crowd_range_coverage_note_explains_identical_ranges(self) -> None:
        note = build_crowd_range_coverage_note({
            "history": [
                {"recorded_at": "2026-06-23 08:00:00", "total_in_library": 36},
                {"recorded_at": "2026-06-23 09:00:00", "total_in_library": 121},
                {"recorded_at": "2026-06-23 10:30:00", "total_in_library": 139},
            ]
        })

        self.assertEqual(
            note,
            "当前 mock 历史数据仅覆盖 2.5 小时，三个时间范围会显示相同折线。",
        )

    def test_crowd_range_coverage_note_hidden_when_ranges_differ(self) -> None:
        note = build_crowd_range_coverage_note({
            "history": [
                {"recorded_at": "2026-06-22 08:00:00", "total_in_library": 36},
                {"recorded_at": "2026-06-23 09:00:00", "total_in_library": 121},
                {"recorded_at": "2026-06-23 10:30:00", "total_in_library": 139},
            ]
        })

        self.assertIsNone(note)

    def test_admin_summary_counts_possibly_occupied(self) -> None:
        summary = build_admin_summary([
            {"seat_id": "A01", "status": "POSSIBLY_OCCUPIED"},
            {"seat_id": "A02", "status": "FREE"},
        ])
        self.assertEqual(summary["possibly_occupied_count"], 1)

    def test_admin_summary_counts_suspicious(self) -> None:
        summary = build_admin_summary([
            {"seat_id": "A01", "status": "SUSPICIOUS"},
            {"seat_id": "A02", "status": "FREE"},
        ])
        self.assertEqual(summary["suspicious_count"], 1)

    def test_admin_occupancy_rate_formula(self) -> None:
        summary = build_admin_summary([
            {"seat_id": "A01", "status": "OCCUPIED"},
            {"seat_id": "A02", "status": "FREE"},
            {"seat_id": "A03", "status": "UNAVAILABLE"},
        ])
        self.assertEqual(summary["occupancy_rate"], 0.5)

    def test_anomaly_statuses_do_not_count_as_occupied_numerator(self) -> None:
        summary = build_admin_summary([
            {"seat_id": "A01", "status": "OCCUPIED"},
            {"seat_id": "A02", "status": "POSSIBLY_OCCUPIED"},
            {"seat_id": "A03", "status": "SUSPICIOUS"},
        ])
        self.assertEqual(summary["occupancy_rate"], 1 / 3)

    def test_admin_summary_no_usable_capacity(self) -> None:
        summary = build_admin_summary([
            {"seat_id": "A01", "status": "UNAVAILABLE"},
        ])
        self.assertIsNone(summary["occupancy_rate"])
        self.assertEqual(summary["occupancy_rate_label"], "暂无数据")

    def test_admin_summary_busiest_anomaly_area(self) -> None:
        summary = build_admin_summary([
            {"seat_id": "A01", "floor": "3", "zone": "A", "status": "SUSPICIOUS"},
            {"seat_id": "A02", "floor": "3", "zone": "A", "status": "POSSIBLY_OCCUPIED"},
            {"seat_id": "B01", "floor": "3", "zone": "B", "status": "SUSPICIOUS"},
        ])
        self.assertEqual(summary["busiest_anomaly_area"], {"floor": "3", "zone": "A", "anomaly_count": 2})

    def test_admin_summary_no_anomaly_area(self) -> None:
        summary = build_admin_summary([
            {"seat_id": "A01", "floor": "3", "zone": "A", "status": "FREE"},
        ])
        self.assertIsNone(summary["busiest_anomaly_area"])
        self.assertEqual(summary["busiest_anomaly_area_label"], "暂无异常区域")

    def test_anomaly_rows_only_include_anomaly_statuses(self) -> None:
        rows = build_anomaly_rows([
            {"seat_id": "A01", "status": "FREE"},
            {"seat_id": "A02", "status": "OCCUPIED"},
            {"seat_id": "A03", "status": "POSSIBLY_OCCUPIED"},
            {"seat_id": "A04", "status": "SUSPICIOUS"},
            {"seat_id": "A05", "status": "BROKEN"},
        ])
        self.assertEqual([row["seat_id"] for row in rows], ["A04", "A03"])

    def test_suspicious_sorts_before_possibly_occupied(self) -> None:
        rows = build_anomaly_rows([
            {"seat_id": "A01", "status": "POSSIBLY_OCCUPIED", "unattended_minutes": 999},
            {"seat_id": "A02", "status": "SUSPICIOUS", "unattended_minutes": 1},
        ])
        self.assertEqual([row["seat_id"] for row in rows], ["A02", "A01"])

    def test_anomaly_rows_sort_by_minutes_then_updated_at(self) -> None:
        rows = build_anomaly_rows([
            {"seat_id": "A01", "status": "SUSPICIOUS", "unattended_minutes": 20, "updated_at": "2026-06-26T09:00:00"},
            {"seat_id": "A02", "status": "SUSPICIOUS", "unattended_minutes": 30, "updated_at": "2026-06-26T08:00:00"},
            {"seat_id": "A03", "status": "SUSPICIOUS", "unattended_minutes": 30, "updated_at": "2026-06-26T10:00:00"},
        ])
        self.assertEqual([row["seat_id"] for row in rows], ["A03", "A02", "A01"])

    def test_anomaly_rows_missing_fields_do_not_crash(self) -> None:
        rows = build_anomaly_rows([
            {"seat_id": "A01", "status": "SUSPICIOUS"},
        ])
        self.assertEqual(rows[0]["has_person"], None)
        self.assertEqual(rows[0]["has_object"], None)
        self.assertEqual(rows[0]["unattended_minutes"], None)

    def test_missing_polygon_does_not_affect_anomaly_row_generation(self) -> None:
        rows = build_anomaly_rows([
            {"seat_id": "A01", "status": "SUSPICIOUS"},
        ])
        self.assertEqual(rows[0]["seat_id"], "A01")
        self.assertIsNone(rows[0]["polygon"])

    def test_empty_seats_returns_empty_admin_summary_and_rows(self) -> None:
        summary = build_admin_summary([])
        rows = build_anomaly_rows([])
        self.assertEqual(summary["possibly_occupied_count"], 0)
        self.assertEqual(summary["suspicious_count"], 0)
        self.assertIsNone(summary["occupancy_rate"])
        self.assertEqual(rows, [])

    def test_selected_anomaly_can_find_floor_zone_camera_group(self) -> None:
        selected = {
            "seat_id": "A01",
            "floor": "3",
            "zone": "A",
            "camera_id": "CAM-1",
            "status": "SUSPICIOUS",
            "polygon": [[0, 0], [10, 0], [10, 10]],
        }
        group = _same_layout_group([
            selected,
            {"seat_id": "A02", "floor": "3", "zone": "A", "camera_id": "CAM-1", "polygon": [[20, 0], [30, 0], [30, 10]]},
            {"seat_id": "A03", "floor": "3", "zone": "A", "camera_id": "CAM-2", "polygon": [[20, 0], [30, 0], [30, 10]]},
        ], selected)
        self.assertEqual([seat["seat_id"] for seat in group], ["A01", "A02"])

    def test_selected_seat_id_passes_to_layout_highlight(self) -> None:
        svg = build_svg_seat_layout([
            {"seat_id": "A01", "status": "SUSPICIOUS", "polygon": [[0, 0], [10, 0], [10, 10]]}
        ], selected_seat_id="A01")
        self.assertIn("seat-selected", svg)

    def test_no_admin_action_fields_are_generated(self) -> None:
        rows = build_anomaly_rows([
            {"seat_id": "A01", "status": "SUSPICIOUS"},
        ])
        forbidden_keys = ["processing" + "_status", "action" + "_result", "admin" + "_note"]
        for key in forbidden_keys:
            self.assertNotIn(key, rows[0])

    def test_anomaly_display_rows_keep_only_required_fields(self) -> None:
        rows = build_anomaly_display_rows([
            {
                "seat_id": "A01",
                "floor": "3",
                "zone": "A",
                "status": "SUSPICIOUS",
                "unattended_minutes": 30,
                "updated_at": "2026-06-26T10:00:00",
                "has_person": False,
                "has_object": True,
                **{"processing" + "_status": "fake"},
            },
        ])
        self.assertEqual(
            set(rows[0]),
            {"seat_id", "floor", "zone", "status", "unattended_minutes", "updated_at"},
        )


if __name__ == "__main__":
    unittest.main()
