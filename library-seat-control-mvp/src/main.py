from __future__ import annotations

import argparse

from src.detection.yolo_detector import mock_detections, run_yolo
from src.seat_mapping.mapper import map_detections_to_seats
from src.state_machine.rules import evaluate_all
from src.utils.crowding import calculate_crowding
from src.utils.io import load_json, save_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the complete library seat-control MVP pipeline.")
    parser.add_argument("--image", default="src/data/sample_library.jpg", help="Input image path.")
    parser.add_argument("--seats", default="src/data/seats.json", help="Seat polygon JSON path.")
    parser.add_argument("--gate-flow", default="src/data/gate_flow.csv", help="Gate flow CSV path.")
    parser.add_argument("--mock", action="store_true", help="Use built-in mock detections.")
    parser.add_argument("--model", default="yolov8n.pt", help="YOLOv8 model name or path.")
    parser.add_argument("--conf", type=float, default=0.25, help="Detection confidence threshold.")
    parser.add_argument("--interval-minutes", type=int, default=5, help="Sampling interval in minutes.")
    parser.add_argument("--threshold-minutes", type=int, default=20, help="Suspicious threshold in minutes.")
    parser.add_argument("--capacity", type=int, default=220, help="Library crowding capacity baseline.")
    args = parser.parse_args()

    detections = mock_detections(args.image) if args.mock else run_yolo(args.image, args.model, args.conf)
    save_json("output/detections.json", detections)

    seats = load_json(args.seats)
    mapped = map_detections_to_seats(seats, detections)
    save_json("output/mapped_seats.json", mapped)

    previous = load_json("output/seat_status.json", default={})
    seat_status = evaluate_all(mapped, previous, args.interval_minutes, args.threshold_minutes)
    save_json("output/seat_status.json", seat_status)

    crowd = calculate_crowding(args.gate_flow, args.capacity)
    save_json("output/crowd_status.json", crowd)

    print("MVP pipeline finished")
    print(f"seat summary: {seat_status['summary']}")
    print(
        "crowding: "
        f"{crowd['latest']['crowd_level']} "
        f"({crowd['latest']['total_in_library']}/{crowd['capacity']})"
    )


if __name__ == "__main__":
    main()

