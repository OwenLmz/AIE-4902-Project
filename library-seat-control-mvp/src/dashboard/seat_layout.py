from __future__ import annotations

import html
from typing import Any

from src.dashboard.i18n import status_text, t

SEAT_LAYOUT_STYLE = """
<style>
* {
    box-sizing: border-box;
}
body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    color: #101828;
}
.cinema-seat-map {
    width: 100%;
    border: 1px solid #eaecf0;
    border-radius: 8px;
    padding: 22px 20px;
    background:
        linear-gradient(#f8fafc 1px, transparent 1px),
        linear-gradient(90deg, #f8fafc 1px, transparent 1px),
        #ffffff;
    background-size: 30px 30px;
    box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
}
.cinema-screen {
    text-align: center;
    color: #667085;
    font-size: 12px;
    margin-bottom: 18px;
    padding-bottom: 10px;
    border-bottom: 2px solid #d0d5dd;
}
.seat-row {
    display: flex;
    justify-content: center;
    gap: 12px;
    margin-bottom: 12px;
}
.seat-chip {
    min-width: 54px;
    height: 42px;
    padding: 0 8px;
    border-radius: 10px;
    font-size: 13px;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border: 1px solid transparent;
    position: relative;
    line-height: 1;
}
.seat-free {
    background: #d1fadf;
    color: #027a48;
    border-color: #a6f4c5;
}
.seat-free-strong {
    background: #12b76a;
    color: #ffffff;
    border-color: #039855;
}
.seat-occupied {
    background: #d1e9ff;
    color: #175cd3;
    border-color: #84caff;
}
.seat-occupied-muted {
    background: #e0e7f2;
    color: #475467;
    border-color: #cbd5e1;
}
.seat-suspected {
    background: #fedf89;
    color: #93370d;
    border-color: #fdb022;
}
.seat-suspected-strong {
    background: #d92d20;
    color: #ffffff;
    border-color: #b42318;
}
.seat-unavailable {
    background: #f2f4f7;
    color: #667085;
    border-color: #d0d5dd;
}
.seat-selected {
    outline: 3px solid #101828;
    outline-offset: 2px;
}
.seat-recommended {
    box-shadow: 0 0 0 3px rgba(18, 183, 106, 0.24);
}
.seat-recommended::after {
    content: "★";
    position: absolute;
    top: -10px;
    right: -6px;
    font-size: 12px;
    color: #f79009;
}
.legend {
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
    align-items: center;
    justify-content: center;
    margin-top: 16px;
    font-size: 13px;
    color: #475467;
}
.legend-item {
    display: inline-flex;
    align-items: center;
    gap: 6px;
}
.legend-dot {
    width: 10px;
    height: 10px;
    border-radius: 999px;
    display: inline-block;
}
.legend-dot.free {
    background: #12b76a;
}
.legend-dot.occupied {
    background: #84caff;
}
.legend-dot.suspected {
    background: #f79009;
}
.legend-dot.selected {
    border: 2px solid #101828;
    background: #ffffff;
}
</style>
"""


def _as_number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def validate_polygon(polygon: Any) -> bool:
    if not isinstance(polygon, list) or len(polygon) < 3:
        return False
    for point in polygon:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            return False
        if _as_number(point[0]) is None or _as_number(point[1]) is None:
            return False
    return True


def _normalize_polygon(polygon: Any) -> list[tuple[float, float]] | None:
    if not validate_polygon(polygon):
        return None
    return [(float(point[0]), float(point[1])) for point in polygon]


def layout_key(seat: dict[str, Any]) -> str:
    floor = str(seat.get("floor", ""))
    zone = str(seat.get("zone", ""))
    camera_id = str(seat.get("camera_id") or "")
    return f"{floor}|{zone}|{camera_id}"


def group_seats_by_layout(seats: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for seat in seats:
        if not isinstance(seat, dict) or not seat.get("seat_id"):
            continue

        key = layout_key(seat)
        group = groups.setdefault(
            key,
            {
                "key": key,
                "floor": str(seat.get("floor", "")),
                "zone": str(seat.get("zone", "")),
                "camera_id": str(seat.get("camera_id") or ""),
                "seats": [],
                "warnings": [],
            },
        )
        if validate_polygon(seat.get("polygon")):
            group["seats"].append(seat)
        else:
            group["warnings"].append({
                "code": "invalid_polygon",
                "seat_id": str(seat.get("seat_id", "")),
            })
    return groups


def _polygon_center(points: list[tuple[float, float]]) -> tuple[float, float]:
    x = sum(point[0] for point in points) / len(points)
    y = sum(point[1] for point in points) / len(points)
    return x, y


def get_short_seat_label(seat_id: str) -> str:
    if not seat_id:
        return ""
    parts = seat_id.split("-")
    return parts[-1] if parts else seat_id


def _status_class(status: str, mode: str) -> str:
    if status == "FREE":
        return "seat-free-strong" if mode == "student" else "seat-free"
    if status == "OCCUPIED":
        return "seat-occupied-muted" if mode == "student" else "seat-occupied"
    if status in {"SUSPICIOUS", "POSSIBLY_OCCUPIED"}:
        return "seat-suspected-strong" if mode == "admin" else "seat-suspected"
    if status == "UNAVAILABLE":
        return "seat-unavailable"
    return "seat-occupied-muted"


def _empty_layout_html(language: str = "zh") -> str:
    return (
        "<div style='padding:16px;border:1px solid #ddd;border-radius:8px;"
        f"background:#fafafa;color:#555'>{html.escape(t('empty.no_layout_data', language))}</div>"
    )


def _legend(mode: str = "student", language: str = "zh") -> str:
    suspected_label = (
        "疑似占座 / 暂不可用"
        if language == "zh" and mode == "admin"
        else "疑似占座"
        if language == "zh"
        else "Suspicious / Temporary"
        if mode == "admin"
        else "Suspicious"
    )
    return (
        "<div class='legend'>"
        f"<span class='legend-item'><span class='legend-dot free'></span>{html.escape(status_text('FREE', language=language))}</span>"
        f"<span class='legend-item'><span class='legend-dot occupied'></span>{html.escape(status_text('OCCUPIED', language=language))}</span>"
        f"<span class='legend-item'><span class='legend-dot suspected'></span>{html.escape(suspected_label)}</span>"
        f"<span class='legend-item'><span class='legend-dot selected'></span>{html.escape('当前选中' if language == 'zh' else 'Selected')}</span>"
        f"<span class='legend-item'>★ {html.escape('推荐座位' if language == 'zh' else 'Recommended')}</span>"
        "</div>"
    )


def _seat_chip(
    seat: dict[str, Any],
    selected_seat_id: str,
    recommended_seat_id: str,
    mode: str,
    language: str,
) -> str:
    seat_id = str(seat.get("seat_id", ""))
    status = str(seat.get("status") or "UNKNOWN").upper()
    classes = ["seat-chip", _status_class(status, mode)]
    if seat_id == selected_seat_id:
        classes.append("seat-selected")
    if recommended_seat_id and seat_id == recommended_seat_id:
        classes.append("seat-recommended")
    safe_classes = html.escape(" ".join(classes))
    safe_title = html.escape(f"{seat_id} {status_text(status, audience='admin' if mode == 'admin' else 'student', language=language)}")
    safe_label = html.escape(get_short_seat_label(seat_id))
    return f"<div class='{safe_classes}' title='{safe_title}'>{safe_label}</div>"


def _seat_rows(
    normalized: list[tuple[dict[str, Any], list[tuple[float, float]]]],
    seats_per_row: int,
) -> list[list[dict[str, Any]]]:
    ordered = [
        seat for seat, _polygon in sorted(
            normalized,
            key=lambda item: (_polygon_center(item[1])[1], _polygon_center(item[1])[0], str(item[0].get("seat_id", ""))),
        )
    ]
    return [ordered[index:index + seats_per_row] for index in range(0, len(ordered), seats_per_row)]


def build_svg_seat_layout(
    seats: list[dict[str, Any]],
    selected_seat_id: str | None = None,
    mode: str = "student",
    recommended_seat_id: str | None = None,
    floor_label: str | None = None,
    area_label: str | None = None,
    seats_per_row: int = 2,
    language: str = "zh",
) -> str:
    normalized: list[tuple[dict[str, Any], list[tuple[float, float]]]] = []
    for seat in seats:
        if not isinstance(seat, dict) or not seat.get("seat_id"):
            continue
        polygon = _normalize_polygon(seat.get("polygon"))
        if polygon is None:
            continue
        normalized.append((seat, polygon))

    if not normalized:
        return _empty_layout_html(language)

    selected = str(selected_seat_id or "")
    recommended = str(recommended_seat_id or "")
    rows = _seat_rows(normalized, max(seats_per_row, 1))
    floor = html.escape(str(floor_label or ("未标注楼层" if language == "zh" else "Unlabeled floor")))
    area = html.escape(str(area_label or ("未标注区域" if language == "zh" else "Unlabeled area")))
    direction_label = "入口 / 通道方向" if language == "zh" else "Entrance / Aisle"
    rendered_rows = []
    for row in rows:
        rendered_rows.append(
            "<div class='seat-row'>"
            + "".join(_seat_chip(seat, selected, recommended, mode, language) for seat in row)
            + "</div>"
        )
    return (
        SEAT_LAYOUT_STYLE
        + "<div class='cinema-seat-map'>"
        f"<div class='cinema-screen'>{floor} {area} · {html.escape(direction_label)}</div>"
        + "".join(rendered_rows)
        + _legend(mode, language)
        + "</div>"
    )
