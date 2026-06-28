from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils.io import save_json


def crowd_level(total_people: int, capacity: int) -> str:
    ratio = total_people / max(capacity, 1)
    if ratio < 0.4:
        return "low"
    if ratio < 0.75:
        return "medium"
    return "high"


def calculate_crowding(gate_flow_path: str | Path, capacity: int = 220) -> dict[str, Any]:
    total = 0
    rows: list[dict[str, Any]] = []
    with Path(gate_flow_path).open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            enter_count = int(row.get("enter_count", 0) or 0)
            exit_count = int(row.get("exit_count", 0) or 0)
            total = max(0, total + enter_count - exit_count)
            rows.append({
                "recorded_at": row.get("recorded_at"),
                "enter_count": enter_count,
                "exit_count": exit_count,
                "total_in_library": total,
                "crowd_level": crowd_level(total, capacity)
            })

    latest = rows[-1] if rows else {
        "recorded_at": None,
        "enter_count": 0,
        "exit_count": 0,
        "total_in_library": 0,
        "crowd_level": "low"
    }
    return {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "capacity": capacity,
        "latest": latest,
        "history": rows
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Step 5: calculate baseline crowding level.")
    parser.add_argument("--gate-flow", default="src/data/gate_flow.csv", help="Gate flow CSV path.")
    parser.add_argument("--capacity", type=int, default=220, help="Library capacity baseline.")
    parser.add_argument("--output", default="output/crowd_status.json", help="Crowding output JSON path.")
    args = parser.parse_args()

    result = calculate_crowding(args.gate_flow, args.capacity)
    save_json(args.output, result)
    print(
        f"crowd level={result['latest']['crowd_level']} "
        f"total={result['latest']['total_in_library']} saved to {args.output}"
    )


if __name__ == "__main__":
    main()

