from __future__ import annotations

import copy
import json
import time
from pathlib import Path

from .blocks import build_chained_ice_blocks, build_path_cover_blocks, build_weighted_path_cover_blocks
from .ev_assignment import assign_charging_aware_evs, assign_no_charge_evs
from .timetable import select_direction_trips
from .types import CPU_REPORT, JsonDict, SelectedTrip


def solve(
    input_path: Path,
    builder: str = "greedy",
    ev_mode: str = "charging",
    tt_variant: int = 0,
    tt_variants: list[int] | None = None,
) -> tuple[JsonDict, JsonDict]:
    start = time.perf_counter()
    data = json.loads(input_path.read_text())
    output = copy.deepcopy(data)
    output["directions"] = []
    selected_items: list[SelectedTrip] = []

    stats: JsonDict = {
        "builder": builder,
        "ev_mode": ev_mode,
        "tt_variant": tt_variant,
        "tt_variants": tt_variants,
        "selected_trips": 0,
        "directions": [],
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

    if builder == "pathcover":
        output["vehicleBlockList"] = build_path_cover_blocks(data, selected_items)
    elif builder == "pathcover-cost":
        output["vehicleBlockList"] = build_weighted_path_cover_blocks(data, selected_items)
    else:
        output["vehicleBlockList"] = build_chained_ice_blocks(data, selected_items)
    if ev_mode == "none":
        stats["evs"] = 0
    elif ev_mode == "no-charge":
        stats["evs"] = assign_no_charge_evs(data, output["vehicleBlockList"])
    else:
        stats["evs"] = assign_charging_aware_evs(data, output["vehicleBlockList"])

    output["reportSol"] = {
        "listCpuType": [CPU_REPORT],
        "lowerBound": 0,
        "executionTime": round(time.perf_counter() - start, 3),
    }
    stats["blocks"] = len(output["vehicleBlockList"])
    return output, stats
