from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .detector import YoloDetector
from .geometry import detection_overlaps_seat
from .state import build_seat_result
from .storage import MySQLStorage, RedisStorage, StorageError, seats_from_fallback
from .types import Detection, SeatConfig, SeatResult


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def list_images(images_dir: str | Path, single_image: str | Path | None = None) -> list[Path]:
    if single_image:
        path = Path(single_image)
        return [path] if path.exists() else []

    directory = Path(images_dir)
    if not directory.exists():
        return []
    return sorted(path for path in directory.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS)


def choose_seats_for_image(image_path: Path, seats: list[SeatConfig]) -> list[SeatConfig]:
    camera_ids = sorted({seat.camera_id for seat in seats})
    if len(camera_ids) <= 1:
        return seats

    stem = image_path.stem.lower()
    matched = [seat for seat in seats if seat.camera_id.lower() in stem]
    return matched or seats


def classify_seat(
    seat: SeatConfig,
    detections: Iterable[Detection],
    person_classes: set[str],
    object_classes: set[str],
    overlap_threshold: float,
) -> tuple[bool, bool]:
    has_person = False
    has_object = False
    for detection in detections:
        if not detection_overlaps_seat(detection, seat, overlap_threshold):
            continue
        class_name = detection.class_name.lower()
        if class_name in person_classes:
            has_person = True
        if class_name in object_classes:
            has_object = True
    return has_person, has_object


def write_csv(results: list[SeatResult], outputs_dir: str | Path) -> Path:
    out_dir = Path(outputs_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "latest_seat_status.csv"
    fieldnames = [
        "seat_id",
        "floor",
        "zone",
        "detected_at",
        "has_person",
        "has_object",
        "status",
        "suspect_duration",
        "image_name",
    ]
    with out_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result.csv_row())
    return out_path


def write_detections_json(detections_by_image: dict[str, list[Detection]], outputs_dir: str | Path) -> Path:
    out_dir = Path(outputs_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "latest_detections.json"
    payload = {
        image_name: [
            {
                "class_name": detection.class_name,
                "confidence": round(detection.confidence, 4),
                "box": [round(v, 2) for v in detection.box],
            }
            for detection in detections
        ]
        for image_name, detections in detections_by_image.items()
    }
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    return out_path


def load_seats(config: dict, mysql: MySQLStorage | None, allow_fallback: bool = True) -> list[SeatConfig]:
    if mysql is not None:
        try:
            seats = mysql.fetch_seats()
            if seats:
                print(f"Loaded {len(seats)} seats from MySQL seat_config.")
                return seats
        except Exception as exc:
            print(f"[WARN] MySQL seat_config read failed: {exc}")

    if allow_fallback:
        seats = seats_from_fallback(config)
        if seats:
            print(f"Using {len(seats)} fallback seats from config.yaml.")
            return seats

    return []


def initial_suspect_cache(seats: list[SeatConfig], redis_store: RedisStorage | None) -> dict[str, int]:
    cache: dict[str, int] = {}
    for seat in seats:
        value = 0
        if redis_store is not None:
            try:
                value = redis_store.get_suspect_min(seat.seat_id)
            except StorageError as exc:
                print(f"[WARN] {exc}")
        cache[seat.seat_id] = value
    return cache


def run_pipeline(
    config: dict,
    dry_run: bool = False,
    skip_mysql: bool = False,
    skip_redis: bool = False,
    single_image: str | Path | None = None,
) -> list[SeatResult]:
    runtime = config["runtime"]
    model_cfg = config["model"]
    paths = config["paths"]

    mysql = None if skip_mysql else MySQLStorage(config["mysql"])
    redis_store = None if skip_redis else RedisStorage(config["redis"], runtime["redis_ttl_sec"])

    seats = load_seats(config, mysql)
    if not seats:
        print("[ERROR] No seat_config records found and no fallback seats configured.")
        return []

    images = list_images(paths["images_dir"], single_image=single_image)
    if not images:
        print(f"[ERROR] No images found. Put jpg/png files in {paths['images_dir']}.")
        write_csv([], paths["outputs_dir"])
        return []

    detector = YoloDetector(
        model_path=paths["model"],
        confidence=runtime["confidence"],
        image_size=runtime["image_size"],
        device=runtime.get("device", "cpu"),
        auto_download=bool(model_cfg.get("auto_download", True)),
    )

    person_classes = {name.lower() for name in model_cfg.get("person_classes", ["person"])}
    object_classes = {name.lower() for name in model_cfg.get("object_classes", [])}
    overlap_threshold = float(config.get("roi", {}).get("overlap_threshold", 0.3))

    suspect_cache = initial_suspect_cache(seats, redis_store)
    all_results: list[SeatResult] = []
    detections_by_image: dict[str, list[Detection]] = {}

    for image_path in images:
        print(f"Running YOLO on {image_path.name} ...")
        detections = detector.detect(image_path)
        detections_by_image[image_path.name] = detections
        seats_for_image = choose_seats_for_image(image_path, seats)
        detected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        image_results: list[SeatResult] = []
        for seat in seats_for_image:
            has_person, has_object = classify_seat(
                seat=seat,
                detections=detections,
                person_classes=person_classes,
                object_classes=object_classes,
                overlap_threshold=overlap_threshold,
            )
            result = build_seat_result(
                seat=seat,
                detected_at=detected_at,
                has_person=has_person,
                has_object=has_object,
                previous_suspect_min=suspect_cache.get(seat.seat_id, 0),
                sample_interval_min=runtime["sample_interval_min"],
                suspect_threshold_min=runtime["suspect_threshold_min"],
                image_name=image_path.name,
            )
            suspect_cache[seat.seat_id] = result.suspect_duration
            image_results.append(result)

        all_results.extend(image_results)

        if not dry_run and redis_store is not None:
            try:
                redis_store.write_results(image_results)
                print(f"Wrote {len(image_results)} seat states to Redis.")
            except StorageError as exc:
                print(f"[WARN] {exc}")

        if not dry_run and mysql is not None:
            try:
                mysql.write_status_log(image_results)
                print(f"Wrote {len(image_results)} rows to MySQL seat_status_log.")
            except Exception as exc:
                print(f"[WARN] MySQL write failed: {exc}")

    csv_path = write_csv(all_results, paths["outputs_dir"])
    json_path = write_detections_json(detections_by_image, paths["outputs_dir"])
    print(f"Saved CSV output: {csv_path}")
    print(f"Saved detection debug JSON: {json_path}")
    return all_results

