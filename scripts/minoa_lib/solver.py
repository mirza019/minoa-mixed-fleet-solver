from __future__ import annotations

import copy
import json
import time
from pathlib import Path

from .blocks import (
    build_chained_ice_blocks,
    build_path_cover_blocks,
    build_weighted_path_cover_blocks,
)
from .ev_assignment import assign_charging_aware_evs, assign_no_charge_evs
from .lower_bounds import selected_timetable_fixed_cost_lower_bound, validate_trip_coverage, zero_global_lower_bound
from .reporting import cpu_report
from .timetable import select_direction_trips
from .types import JsonDict, SelectedTrip


def solve(
    input_path: Path,
    builder: str = "greedy",
    ev_mode: str = "charging",
    tt_variant: int = 0,
    tt_variants: list[int] | None = None,
    edge_mode: str = "time",
    ev_strategy: str = "legacy",
) -> tuple[JsonDict, JsonDict]:
    data = json.loads(input_path.read_text())
    algorithm_start = time.perf_counter()
    stage_start = algorithm_start
    timings: JsonDict = {}

    output = copy.deepcopy(data)
    output["directions"] = []
    selected_items: list[SelectedTrip] = []

    stats: JsonDict = {
        "builder": builder,
        "ev_mode": ev_mode,
        "tt_variant": tt_variant,
        "tt_variants": tt_variants,
        "edge_mode": edge_mode,
        "ev_strategy": ev_strategy,
        "selected_trips": 0,
        "directions": [],
        "timing_seconds": timings,
    }
    for direction_index, direction_wrap in enumerate(data["directions"]):
        direction = direction_wrap["direction"]
        variant = tt_variants[direction_index] if tt_variants else tt_variant
        selected = select_direction_trips(direction, data["timeHorizon"], variant=variant)
        out_direction = copy.deepcopy(direction)
        out_direction["trips"] = selected
        output["directions"].append({"direction": out_direction})
        stats["selected_trips"] += len(selected)
        stats["directions"].append(
            {
                "lineName": direction["lineName"],
                "directionType": direction["directionType"],
                "selected": len(selected),
                "tt_variant": variant,
            }
        )
        for tw in selected:
            selected_items.append({"direction": direction, "trip": tw["trip"]})

    timings["timetable_generation"] = round(time.perf_counter() - stage_start, 6)
    stage_start = time.perf_counter()

    if builder == "pathcover":
        output["vehicleBlockList"] = build_path_cover_blocks(data, selected_items)
    elif builder == "pathcover-cost":
        output["vehicleBlockList"] = build_weighted_path_cover_blocks(
            data,
            selected_items,
            edge_mode=edge_mode,
        )
    else:
        output["vehicleBlockList"] = build_chained_ice_blocks(data, selected_items)

    timings["block_construction"] = round(time.perf_counter() - stage_start, 6)
    stage_start = time.perf_counter()

    if ev_mode == "none":
        stats["evs"] = 0
    elif ev_mode == "no-charge":
        stats["evs"] = assign_no_charge_evs(data, output["vehicleBlockList"])
    else:
        stats["evs"] = assign_charging_aware_evs(
            data,
            output["vehicleBlockList"],
            strategy=ev_strategy,
        )

    timings["ev_assignment_and_charging"] = round(time.perf_counter() - stage_start, 6)
    stage_start = time.perf_counter()
    validate_trip_coverage(data, output)
    global_lb_report = zero_global_lower_bound(data)
    selected_lb_report = selected_timetable_fixed_cost_lower_bound(data, output)
    timings["coverage_and_lower_bound"] = round(time.perf_counter() - stage_start, 6)
    execution_time = round(time.perf_counter() - algorithm_start, 3)
    timings["algorithm_total"] = execution_time

    output["reportSol"] = {
        "listCpuType": [cpu_report()],
        "lowerBound": global_lb_report.fixed_cost_lb,
        "executionTime": execution_time,
    }
    stats["blocks"] = len(output["vehicleBlockList"])
    stats["global_lower_bound"] = global_lb_report.fixed_cost_lb
    stats["global_lower_bound_vehicle_count"] = global_lb_report.vehicle_count_lb
    stats["global_lower_bound_scope"] = global_lb_report.scope
    stats["global_lower_bound_status"] = global_lb_report.status
    stats["selected_timetable_lower_bound"] = selected_lb_report.fixed_cost_lb
    stats["selected_timetable_vehicle_lower_bound"] = selected_lb_report.vehicle_count_lb
    stats["selected_timetable_overlap_vehicle_lower_bound"] = selected_lb_report.overlap_vehicle_lb
    stats["selected_timetable_path_cover_vehicle_lower_bound"] = selected_lb_report.path_cover_vehicle_lb
    return output, stats
