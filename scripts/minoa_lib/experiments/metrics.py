from __future__ import annotations

import json
import re
from pathlib import Path

from ..network import arc_by_code, trip_by_id
from ..types import JsonDict
from ..validation import validate


VS_COST_RE = re.compile(r"vsCost:\s*([0-9]+(?:\.[0-9]+)?)")


def parse_vs_cost(validator_output: str) -> float | None:
    match = VS_COST_RE.search(validator_output)
    if not match:
        return None
    return float(match.group(1))


def instance_name(input_path: Path) -> str:
    name = input_path.name
    for suffix in ("_Input_S.json", "_input_S.json", "_Input.json", "_input.json", ".json"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    return name.replace("_", " ")


def approach_name(output_path: Path) -> str:
    stem = output_path.stem
    parts = stem.split("_")
    if "Output" in parts:
        parts = parts[parts.index("Output") + 1 :]
    elif "output" in parts:
        parts = parts[parts.index("output") + 1 :]
    return " ".join(parts) if parts else stem


def block_metrics(data: JsonDict) -> JsonDict:
    blocks = data.get("vehicleBlockList", [])
    trips = trip_by_id(data)
    arcs = arc_by_code(data)

    ev_blocks = 0
    ice_blocks = 0
    selected_trip_ids: set[int] = set()
    deadhead_time = 0
    deadhead_km = 0.0
    service_time = 0
    service_km = 0.0
    break_time = 0
    charging_time = 0

    for block_wrap in blocks:
        block = block_wrap["vehicleBlock"]
        vehicle_type = block["vehicleTypeName"].lower()
        if "electric" in vehicle_type:
            ev_blocks += 1
        else:
            ice_blocks += 1

        for activity in block["activityList"]:
            if "activityTrip" in activity:
                trip = trips[activity["activityTrip"]["tripId"]]
                selected_trip_ids.add(trip["tripId"])
                service_time += trip["endTime"] - trip["startTime"]
                service_km += trip["lengthTrip"]
            elif "deadhead" in activity:
                deadhead = activity["deadhead"]
                deadhead_time += deadhead["endingTime"] - deadhead["startingTime"]
                deadhead_km += arcs[deadhead["deadheadArcCode"]]["arcLength"]
            elif "break" in activity:
                for break_wrap in activity["break"]["breakTimeWindows"]:
                    bw = break_wrap["breakTimeWindow"]
                    duration = bw["endTime"] - bw["startTime"]
                    break_time += duration
                    if bw.get("isCharging"):
                        charging_time += duration

    total_blocks = len(blocks)
    return {
        "total_blocks": total_blocks,
        "ev_blocks": ev_blocks,
        "ice_blocks": ice_blocks,
        "ev_share": 100.0 * ev_blocks / total_blocks if total_blocks else 0.0,
        "selected_trips": len(selected_trip_ids),
        "deadhead_min": deadhead_time / 60.0,
        "deadhead_km": deadhead_km,
        "service_min": service_time / 60.0,
        "service_km": service_km,
        "break_min": break_time / 60.0,
        "charging_min": charging_time / 60.0,
    }


def evaluate_solution(input_path: Path, output_path: Path, validator_path: Path) -> JsonDict:
    data = json.loads(output_path.read_text())
    result = validate(validator_path, input_path, output_path)
    objective = parse_vs_cost(result.stdout)
    valid = result.returncode == 0 and objective is not None
    return {
        "instance": instance_name(input_path),
        "approach": approach_name(output_path),
        "input": str(input_path),
        "output": str(output_path),
        "valid": valid,
        "objective": objective,
        "validator_output": result.stdout,
        **block_metrics(data),
    }

