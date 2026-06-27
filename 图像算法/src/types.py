from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SeatConfig:
    seat_id: str
    floor: int
    zone: str
    camera_id: str
    roi_x1: int
    roi_y1: int
    roi_x2: int
    roi_y2: int
    is_active: bool = True

    @property
    def roi(self) -> tuple[float, float, float, float]:
        return (float(self.roi_x1), float(self.roi_y1), float(self.roi_x2), float(self.roi_y2))


@dataclass(frozen=True)
class Detection:
    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def box(self) -> tuple[float, float, float, float]:
        return (self.x1, self.y1, self.x2, self.y2)


@dataclass(frozen=True)
class SeatResult:
    seat_id: str
    floor: int
    zone: str
    detected_at: str
    has_person: bool
    has_object: bool
    status: str
    suspect_duration: int
    image_name: str = ""

    def redis_mapping(self) -> dict[str, str]:
        return {
            "status": self.status,
            "has_person": "1" if self.has_person else "0",
            "has_object": "1" if self.has_object else "0",
            "suspect_min": str(self.suspect_duration),
            "floor": str(self.floor),
            "zone": self.zone,
            "updated_at": self.detected_at,
        }

    def csv_row(self) -> dict[str, object]:
        return {
            "seat_id": self.seat_id,
            "floor": self.floor,
            "zone": self.zone,
            "detected_at": self.detected_at,
            "has_person": 1 if self.has_person else 0,
            "has_object": 1 if self.has_object else 0,
            "status": self.status,
            "suspect_duration": self.suspect_duration,
            "image_name": self.image_name,
        }

