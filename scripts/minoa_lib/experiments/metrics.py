from __future__ import annotations

import json
import re
from pathlib import Path

from ..costs import assert_cost_reconciled, cost_breakdown, cost_residual
from ..lower_bounds import selected_timetable_fixed_cost_lower_bound
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
    input_data = json.loads(input_path.read_text())
    data = json.loads(output_path.read_text())
    result = validate(validator_path, input_path, output_path)
    objective = parse_vs_cost(result.stdout)
    valid = result.returncode == 0 and objective is not None
    costs = cost_breakdown(input_data, data)
    selected_lb = selected_timetable_fixed_cost_lower_bound(input_data, data)
    global_lb = float(data.get("reportSol", {}).get("lowerBound", 0.0) or 0.0)
    fixed_cost = costs.fixed_cost
    pull_cost = costs.pull_cost
    co2_cost = costs.co2_cost
    break_cost = costs.break_cost
    estimated_cost = costs.total
    official_residual = None
    if objective is not None:
        official_residual = cost_residual(objective, costs)
        if valid:
            assert_cost_reconciled(objective, costs)
    return {
        "instance": instance_name(input_path),
        "approach": approach_name(output_path),
        "input": str(input_path),
        "output": str(output_path),
        "valid": valid,
        "objective": objective,
        "fixed_cost": fixed_cost,
        "break_cost": break_cost,
        "pull_cost": pull_cost,
        "co2_cost": co2_cost,
        "estimated_cost": estimated_cost,
        "official_residual": official_residual,
        "validator_cost_delta": official_residual,
        "global_lower_bound": global_lb,
        "global_bound_gap_ub": 100.0 * (objective - global_lb) / objective if objective else None,
        "selected_tt_lower_bound": selected_lb.fixed_cost_lb,
        "selected_tt_vehicle_count_lb": selected_lb.vehicle_count_lb,
        "selected_tt_overlap_vehicle_count_lb": selected_lb.overlap_vehicle_lb,
        "selected_tt_path_cover_vehicle_count_lb": selected_lb.path_cover_vehicle_lb,
        "selected_tt_bound_scope": selected_lb.scope,
        "selected_tt_bound_gap_ub": selected_lb.gap_ub_percent(objective),
        "validator_output": result.stdout,
        **block_metrics(data),
    }
