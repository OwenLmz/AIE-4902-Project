from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_IMAGE_SEAT_STATUS_CSV = Path("../图像算法/outputs/latest_seat_status.csv")
DEFAULT_DATA_SEAT_STATUS_CSV = Path("../数据建设/Data Generator/output/seat_status_simulation.csv")
DEFAULT_CROWD_STATUS_CSV = Path("../数据建设/Data Generator/output/gate_log_simulation.csv")


def _parse_timestamp(value: Any) -> datetime:
    if not value:
        return datetime.min
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return datetime.min


def _resolve_path(path: str | Path, base_dir: str | Path | None) -> Path:
    file_path = Path(path)
    if file_path.is_absolute() or base_dir is None:
        return file_path
    return Path(base_dir) / file_path


def _read_csv_rows(path: Path) -> tuple[list[dict[str, str]], str | None]:
    if not path.exists():
        return [], "missing_file"
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return [], "empty_csv"
            return [
                {str(key): "" if value is None else value for key, value in row.items()}
                for row in reader
                if any(value not in (None, "") for value in row.values())
            ], None
    except (csv.Error, OSError, UnicodeDecodeError):
        return [], "invalid_csv"


def _latest_row(rows: list[dict[str, str]], time_field: str) -> dict[str, str] | None:
    if not rows:
        return None
    return max(rows, key=lambda row: _parse_timestamp(row.get(time_field)))


def _latest_seat_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    latest_by_seat: dict[str, dict[str, str]] = {}
    for row in rows:
        seat_id = row.get("seat_id")
        if not seat_id:
            continue
        current = latest_by_seat.get(seat_id)
        if current is None or _parse_timestamp(row.get("detected_at")) >= _parse_timestamp(current.get("detected_at")):
            latest_by_seat[seat_id] = row
    return list(latest_by_seat.values())


def seat_status_csv_to_payload(rows: list[dict[str, str]]) -> dict[str, Any]:
    latest_rows = _latest_seat_rows(rows)
    latest = _latest_row(latest_rows, "detected_at")
    return {
        "detected_at": latest.get("detected_at") if latest else None,
        "seats": latest_rows,
    }


def crowd_csv_to_payload(rows: list[dict[str, str]], capacity: int | None = None) -> dict[str, Any]:
    latest = _latest_row(rows, "recorded_at") or {}
    payload: dict[str, Any] = {
        "recorded_at": latest.get("recorded_at"),
        "total_in_library": latest.get("total_in_library"),
        "crowding_level": latest.get("crowding_level"),
        "history": rows,
        "forecast_30m": None,
    }
    if capacity is not None:
        payload["capacity"] = capacity
    elif latest.get("capacity"):
        payload["capacity"] = latest.get("capacity")
    return payload


def read_csv_dashboard_payloads(
    base_dir: str | Path | None = None,
    seat_status_path: str | Path | None = None,
    crowd_status_path: str | Path | None = None,
    capacity: int | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, str | None]]:
    seat_path = _resolve_path(seat_status_path or DEFAULT_IMAGE_SEAT_STATUS_CSV, base_dir)
    seat_rows, seat_error = _read_csv_rows(seat_path)
    if seat_error == "missing_file" and seat_status_path is None:
        fallback_path = _resolve_path(DEFAULT_DATA_SEAT_STATUS_CSV, base_dir)
        seat_rows, seat_error = _read_csv_rows(fallback_path)

    crowd_path = _resolve_path(crowd_status_path or DEFAULT_CROWD_STATUS_CSV, base_dir)
    crowd_rows, crowd_error = _read_csv_rows(crowd_path)

    return (
        seat_status_csv_to_payload(seat_rows) if not seat_error else None,
        crowd_csv_to_payload(crowd_rows, capacity=capacity) if not crowd_error else None,
        {"seat": seat_error, "crowd": crowd_error},
    )

