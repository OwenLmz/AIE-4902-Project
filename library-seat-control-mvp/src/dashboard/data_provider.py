from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from src.dashboard.adapters.csv_adapter import read_csv_dashboard_payloads
from src.dashboard.styles import KNOWN_STATUSES, crowding_level_from_ratio, normalize_status

DEFAULT_SEAT_STATUS_PATH = Path("output/seat_status.json")
DEFAULT_CROWD_STATUS_PATH = Path("output/crowd_status.json")
DEFAULT_SEAT_LAYOUT_PATH = Path("src/data/seats.json")

ABNORMAL_STATUSES = {"suspected"}


def _empty_result() -> dict[str, Any]:
    return {
        "data_source": "mock",
        "seat_updated_at": None,
        "crowd_updated_at": None,
        "seats": [],
        "layout_groups": {},
        "crowd": {
            "total_in_library": None,
            "capacity": None,
            "crowd_ratio": None,
            "crowding_level": None,
            "recorded_at": None,
            "history": [],
            "forecast_30m": None,
            "data_source": "mock",
        },
        "errors": {"seat": None, "crowd": None, "layout": None},
        "warnings": [],
    }


def _resolve_path(path: str | Path, base_dir: str | Path | None) -> Path:
    file_path = Path(path)
    if file_path.is_absolute() or base_dir is None:
        return file_path
    return Path(base_dir) / file_path


def _read_json(path: Path) -> tuple[Any | None, str | None]:
    if not path.exists():
        return None, "missing_file"
    try:
        with path.open("r", encoding="utf-8-sig") as f:
            return json.load(f), None
    except json.JSONDecodeError:
        return None, "invalid_json"


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _env_int(name: str) -> int | None:
    return _to_int(os.getenv(name))


def _to_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value in (0, "0", "false", "False", "FALSE"):
        return False
    if value in (1, "1", "true", "True", "TRUE"):
        return True
    if value is None:
        return None
    return bool(value)


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _warn_timestamp(value: Any, context: str, warnings: list[dict[str, Any]]) -> None:
    if value and _parse_timestamp(value) is None:
        warnings.append({"code": "invalid_timestamp", "context": context, "value": value})


def _suspect_duration(row: dict[str, Any]) -> int | None:
    for key in ("suspect_duration", "suspect_min", "unattended_minutes", "object_unattended_minutes"):
        if key in row:
            return _to_int(row.get(key))
    return None


def _roi_from_polygon(polygon: Any) -> dict[str, float] | None:
    polygon_points, error = validate_polygon(polygon)
    if error or not polygon_points:
        return None
    xs = [point[0] for point in polygon_points]
    ys = [point[1] for point in polygon_points]
    return {
        "roi_x1": min(xs),
        "roi_y1": min(ys),
        "roi_x2": max(xs),
        "roi_y2": max(ys),
    }


def _roi_from_row(row: dict[str, Any], layout: dict[str, Any]) -> tuple[dict[str, float] | None, str | None]:
    values = {
        key: _to_float(row.get(key, layout.get(key)))
        for key in ("roi_x1", "roi_y1", "roi_x2", "roi_y2")
    }
    if all(value is not None for value in values.values()):
        if values["roi_x2"] <= values["roi_x1"] or values["roi_y2"] <= values["roi_y1"]:
            return None, "invalid_roi"
        return values, None

    polygon_roi = _roi_from_polygon(row.get("polygon", layout.get("polygon")))
    if polygon_roi:
        return polygon_roi, None
    return None, "missing_roi"


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _layout_index(layout_payload: Any) -> dict[str, dict[str, Any]]:
    rows = layout_payload if isinstance(layout_payload, list) else []
    return {
        str(row.get("seat_id")): row
        for row in rows
        if isinstance(row, dict) and row.get("seat_id")
    }


def validate_polygon(polygon: Any) -> tuple[list[list[float]] | None, str | None]:
    if not isinstance(polygon, list) or len(polygon) < 3:
        return None, "missing_polygon"

    points: list[list[float]] = []
    for point in polygon:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            return None, "invalid_polygon"
        x, y = point[0], point[1]
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            return None, "invalid_polygon"
        points.append([float(x), float(y)])

    return points, None


def normalize_seats(
    seat_payload: Any,
    layout_payload: Any,
    warnings: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], str | None, str | None]:
    seat_rows = seat_payload.get("seats") if isinstance(seat_payload, dict) else None
    if not isinstance(seat_rows, list):
        return [], "missing_field", None
    if not seat_rows:
        return [], "empty_seats", None

    layout_by_id = _layout_index(layout_payload)
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    layout_error: str | None = None
    seat_detected_at = (
        seat_payload.get("detected_at") or seat_payload.get("updated_at")
        if isinstance(seat_payload, dict)
        else None
    )
    _warn_timestamp(seat_detected_at, "seat_detected_at", warnings)

    for row in seat_rows:
        if not isinstance(row, dict) or not row.get("seat_id"):
            warnings.append({"code": "missing_seat_id", "row": row})
            continue

        seat_id = str(row["seat_id"])
        if seat_id in seen:
            return [], "duplicate_seat_id", None
        seen.add(seat_id)

        layout = layout_by_id.get(seat_id, {})
        raw_status = row.get("status")
        status, status_warning = normalize_status(raw_status)
        if status_warning:
            warnings.append({"code": status_warning, "seat_id": seat_id, "value": raw_status})

        roi, roi_error = _roi_from_row(row, layout)
        if roi_error:
            layout_error = layout_error or roi_error
            warnings.append({"code": roi_error, "seat_id": seat_id})

        detected_at = row.get("detected_at") or row.get("updated_at") or seat_detected_at
        _warn_timestamp(detected_at, f"seat:{seat_id}", warnings)

        normalized_row = {
            "seat_id": seat_id,
            "floor": "" if row.get("floor", layout.get("floor")) is None else str(row.get("floor", layout.get("floor"))),
            "zone": "" if row.get("zone", layout.get("zone")) is None else str(row.get("zone", layout.get("zone"))),
            "camera_id": row.get("camera_id") or layout.get("camera_id"),
            "status": status,
            "status_known": status in KNOWN_STATUSES,
            "has_person": _to_bool(row.get("has_person")),
            "has_object": _to_bool(row.get("has_object")),
            "suspect_duration": _suspect_duration(row),
            "detected_at": detected_at,
        }
        if roi:
            normalized_row.update(roi)
        normalized.append(normalized_row)

    if not normalized:
        return [], "empty_seats", layout_error
    return normalized, None, layout_error


def calculate_crowd_status(
    crowd_payload: Any,
    warnings: list[dict[str, Any]],
) -> tuple[dict[str, Any], str | None]:
    crowd = {
        "total_in_library": None,
        "capacity": None,
        "crowd_ratio": None,
        "crowding_level": None,
        "recorded_at": None,
        "history": [],
        "forecast_30m": None,
        "data_source": "mock",
    }

    if not isinstance(crowd_payload, dict):
        return crowd, "missing_field"

    latest = crowd_payload.get("latest") if isinstance(crowd_payload.get("latest"), dict) else {}
    total_in_library = _to_int(latest.get("total_in_library"))
    if total_in_library is None:
        total_in_library = _to_int(crowd_payload.get("total_in_library"))
    if total_in_library is None:
        total_in_library = _to_int(crowd_payload.get("current_num"))
    if total_in_library is None:
        total_in_library = _to_int(crowd_payload.get("current_people"))
    if total_in_library is None:
        return crowd, "missing_field"
    if total_in_library < 0:
        return crowd, "invalid_total_in_library"

    capacity = _to_int(crowd_payload.get("capacity"))
    if capacity is None or capacity <= 0:
        crowd["total_in_library"] = total_in_library
        return crowd, "invalid_capacity"

    ratio = total_in_library / capacity
    if total_in_library > capacity:
        warnings.append({
            "code": "total_in_library_exceeds_capacity",
            "total_in_library": total_in_library,
            "capacity": capacity,
        })

    recorded_at = latest.get("recorded_at") or crowd_payload.get("recorded_at") or crowd_payload.get("updated_at")
    _warn_timestamp(recorded_at, "crowd_recorded_at", warnings)

    history = crowd_payload.get("history")
    if not isinstance(history, list) or not history:
        history = []
        error = "empty_history"
    else:
        error = None

    if crowd_payload.get("forecast_30m") is None:
        warnings.append({"code": "missing_forecast"})

    crowding_level = str(
        crowd_payload.get("crowding_level")
        or crowd_payload.get("crowd_level")
        or crowding_level_from_ratio(ratio)
    ).lower()
    crowd.update({
        "total_in_library": total_in_library,
        "capacity": capacity,
        "crowd_ratio": ratio,
        "crowding_level": crowding_level,
        "recorded_at": recorded_at,
        "history": history,
        "forecast_30m": crowd_payload.get("forecast_30m"),
    })
    return crowd, error


def group_seats_by_layout(seats: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for seat in seats:
        if not all(seat.get(key) is not None for key in ("roi_x1", "roi_y1", "roi_x2", "roi_y2")):
            continue
        key = f"{seat.get('floor', '')}|{seat.get('zone', '')}|{seat.get('camera_id') or ''}"
        groups.setdefault(key, []).append(seat)
    return groups


def abnormal_seats(seats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def sort_key(seat: dict[str, Any]) -> tuple[int, int, float]:
        priority = 0 if seat.get("status") == "suspected" else 1
        minutes = _to_int(seat.get("suspect_duration")) or 0
        parsed = _parse_timestamp(seat.get("detected_at"))
        timestamp = parsed.timestamp() if parsed else 0.0
        return priority, -minutes, -timestamp

    rows = [seat for seat in seats if seat.get("status") in ABNORMAL_STATUSES]
    return sorted(rows, key=sort_key)


def load_dashboard_data(
    base_dir: str | Path | None = None,
    seat_status_path: str | Path = DEFAULT_SEAT_STATUS_PATH,
    crowd_status_path: str | Path = DEFAULT_CROWD_STATUS_PATH,
    seat_layout_path: str | Path = DEFAULT_SEAT_LAYOUT_PATH,
    data_source: str | None = None,
    csv_capacity: int | None = None,
) -> dict[str, Any]:
    result = _empty_result()
    source = (data_source or os.getenv("DASHBOARD_DATA_SOURCE") or "json").strip().lower()
    if source == "csv":
        result["data_source"] = "csv"
        result["crowd"]["data_source"] = "csv"
        seat_payload, crowd_payload, csv_errors = read_csv_dashboard_payloads(
            base_dir=base_dir,
            seat_status_path=(
                os.getenv("DASHBOARD_SEAT_STATUS_CSV")
                if seat_status_path == DEFAULT_SEAT_STATUS_PATH
                else seat_status_path
            ),
            crowd_status_path=(
                os.getenv("DASHBOARD_CROWD_STATUS_CSV")
                if crowd_status_path == DEFAULT_CROWD_STATUS_PATH
                else crowd_status_path
            ),
            capacity=csv_capacity if csv_capacity is not None else _env_int("DASHBOARD_CAPACITY"),
        )
        layout_payload, layout_file_error = _read_json(_resolve_path(seat_layout_path, base_dir))

        if csv_errors.get("seat"):
            result["errors"]["seat"] = csv_errors["seat"]
        if csv_errors.get("crowd"):
            result["errors"]["crowd"] = csv_errors["crowd"]
        if layout_file_error:
            result["errors"]["layout"] = layout_file_error

        if seat_payload is not None:
            seats, seat_data_error, layout_data_error = normalize_seats(
                seat_payload,
                layout_payload if not layout_file_error else [],
                result["warnings"],
            )
            result["seats"] = seats
            result["seat_updated_at"] = seat_payload.get("detected_at")
            if seat_data_error:
                result["errors"]["seat"] = seat_data_error
            if layout_data_error and not result["errors"]["layout"]:
                result["errors"]["layout"] = layout_data_error
            result["layout_groups"] = group_seats_by_layout(seats)

        if crowd_payload is not None:
            crowd, crowd_data_error = calculate_crowd_status(crowd_payload, result["warnings"])
            crowd["data_source"] = "csv"
            result["crowd"] = crowd
            result["crowd_updated_at"] = crowd_payload.get("recorded_at")
            if crowd_data_error:
                result["errors"]["crowd"] = crowd_data_error

        return result

    seat_payload, seat_error = _read_json(_resolve_path(seat_status_path, base_dir))
    layout_payload, layout_file_error = _read_json(_resolve_path(seat_layout_path, base_dir))
    crowd_payload, crowd_file_error = _read_json(_resolve_path(crowd_status_path, base_dir))

    if seat_error:
        result["errors"]["seat"] = seat_error
    if layout_file_error:
        result["errors"]["layout"] = layout_file_error
    if crowd_file_error:
        result["errors"]["crowd"] = crowd_file_error

    if not seat_error:
        seats, seat_data_error, layout_data_error = normalize_seats(
            seat_payload,
            layout_payload if not layout_file_error else [],
            result["warnings"],
        )
        result["seats"] = seats
        result["seat_updated_at"] = (
            seat_payload.get("detected_at") or seat_payload.get("updated_at")
            if isinstance(seat_payload, dict)
            else None
        )
        if seat_data_error:
            result["errors"]["seat"] = seat_data_error
        if layout_data_error and not result["errors"]["layout"]:
            result["errors"]["layout"] = layout_data_error
        result["layout_groups"] = group_seats_by_layout(seats)

    if not crowd_file_error:
        crowd, crowd_data_error = calculate_crowd_status(crowd_payload, result["warnings"])
        result["crowd"] = crowd
        result["crowd_updated_at"] = (
            crowd_payload.get("recorded_at") or crowd_payload.get("updated_at")
            if isinstance(crowd_payload, dict)
            else None
        )
        if crowd_data_error:
            result["errors"]["crowd"] = crowd_data_error

    return result
