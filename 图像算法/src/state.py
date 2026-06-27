from __future__ import annotations

from .types import SeatConfig, SeatResult


VALID_STATUS = {"free", "occupied", "suspected", "unavailable"}


def build_seat_result(
    seat: SeatConfig,
    detected_at: str,
    has_person: bool,
    has_object: bool,
    previous_suspect_min: int,
    sample_interval_min: int,
    suspect_threshold_min: int,
    image_name: str = "",
) -> SeatResult:
    if not seat.is_active:
        status = "unavailable"
        suspect_duration = 0
        has_person = False
        has_object = False
    elif has_person:
        status = "occupied"
        suspect_duration = 0
    elif has_object:
        suspect_duration = max(0, int(previous_suspect_min)) + sample_interval_min
        status = "suspected" if suspect_duration >= suspect_threshold_min else "occupied"
    else:
        status = "free"
        suspect_duration = 0

    return SeatResult(
        seat_id=seat.seat_id,
        floor=seat.floor,
        zone=seat.zone,
        detected_at=detected_at,
        has_person=has_person,
        has_object=has_object,
        status=status,
        suspect_duration=suspect_duration,
        image_name=image_name,
    )

