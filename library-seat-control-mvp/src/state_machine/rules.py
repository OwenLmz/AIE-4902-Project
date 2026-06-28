from __future__ import annotations

import argparse
from datetime import datetime
from typing import Any

from src.utils.io import load_json, save_json

FREE = "FREE"
OCCUPIED = "OCCUPIED"
POSSIBLY_OCCUPIED = "POSSIBLY_OCCUPIED"
SUSPICIOUS = "SUSPICIOUS"


def previous_minutes_by_seat(previous_payload: dict[str, Any] | None) -> dict[str, int]:
    if not previous_payload:
        return {}
    rows = previous_payload.get("seats", previous_payload if isinstance(previous_payload, list) else [])
    return {
        row["seat_id"]: int(row.get("object_unattended_minutes", row.get("suspect_duration", 0)) or 0)
        for row in rows
    }


def evaluate_seat(
    mapped_seat: dict[str, Any],
    previous_unattended_minutes: int,
    interval_minutes: int,
    suspicious_threshold_minutes: int
) -> dict[str, Any]:
    has_person = bool(mapped_seat.get("has_person"))
    has_object = bool(mapped_seat.get("has_object"))

    if has_person:
        status = OCCUPIED
        unattended_minutes = 0
    elif has_object:
        unattended_minutes = previous_unattended_minutes + interval_minutes
        status = SUSPICIOUS if unattended_minutes >= suspicious_threshold_minutes else POSSIBLY_OCCUPIED
    else:
        status = FREE
        unattended_minutes = 0

    return {
        "seat_id": mapped_seat["seat_id"],
        "floor": mapped_seat.get("floor"),
        "zone": mapped_seat.get("zone"),
        "has_person": has_person,
        "has_object": has_object,
        "status": status,
        "object_unattended_minutes": unattended_minutes,
        "suspect_duration": unattended_minutes,
        "detections": mapped_seat.get("detections", [])
    }


def evaluate_all(
    mapped_payload: dict[str, Any],
    previous_payload: dict[str, Any] | None = None,
    interval_minutes: int = 5,
    suspicious_threshold_minutes: int = 20
) -> dict[str, Any]:
    previous = previous_minutes_by_seat(previous_payload)
    seats = [
        evaluate_seat(
            row,
            previous.get(row["seat_id"], 0),
            interval_minutes,
            suspicious_threshold_minutes
        )
        for row in mapped_payload.get("seats", [])
    ]
    summary = {
        FREE: sum(1 for row in seats if row["status"] == FREE),
        OCCUPIED: sum(1 for row in seats if row["status"] == OCCUPIED),
        POSSIBLY_OCCUPIED: sum(1 for row in seats if row["status"] == POSSIBLY_OCCUPIED),
        SUSPICIOUS: sum(1 for row in seats if row["status"] == SUSPICIOUS)
    }
    return {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "interval_minutes": interval_minutes,
        "suspicious_threshold_minutes": suspicious_threshold_minutes,
        "summary": summary,
        "seats": seats
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Step 3: evaluate seat state machine.")
    parser.add_argument("--mapped", default="output/mapped_seats.json", help="Mapped seats JSON path.")
    parser.add_argument("--previous", default="", help="Previous seat status JSON path, optional.")
    parser.add_argument("--output", default="output/seat_status.json", help="Seat status JSON path.")
    parser.add_argument("--interval-minutes", type=int, default=5, help="Sampling interval in minutes.")
    parser.add_argument("--threshold-minutes", type=int, default=20, help="Suspicious threshold in minutes.")
    args = parser.parse_args()

    mapped = load_json(args.mapped)
    previous = load_json(args.previous, default={}) if args.previous else {}
    result = evaluate_all(mapped, previous, args.interval_minutes, args.threshold_minutes)
    save_json(args.output, result)
    print(f"evaluated {len(result['seats'])} seats to {args.output}")


if __name__ == "__main__":
    main()

