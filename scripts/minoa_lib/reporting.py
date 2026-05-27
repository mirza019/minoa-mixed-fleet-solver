from __future__ import annotations

import platform
import subprocess

from .costs import vehicle_cost_specs
from .types import JsonDict


def cpu_report() -> JsonDict:
    processor = _processor_name()
    machine = platform.machine()
    system = platform.system()
    description = f"{processor} ({machine}), {system}; benchmark not measured"
    return {
        "cpuType": {
            "description": description,
            "numberCpu": 1,
            "cpuIntegerIndex": 1.0,
            "cpuFloatIndex": 1.0,
        }
    }


def _processor_name() -> str:
    if platform.system() == "Darwin":
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if result.stdout.strip():
                return result.stdout.strip()
        except OSError:
            pass
    return platform.processor() or platform.machine() or "unknown processor"


def fixed_vehicle_lower_bound(data: JsonDict, output: JsonDict) -> float:
    """Conservative objective lower bound based on simultaneous selected trips.

    At any time, each active passenger trip requires a different vehicle. The
    maximum number of simultaneously active selected trips is therefore a lower
    bound on the number of used vehicle blocks. Multiplying it by the cheapest
    fixed vehicle usage cost gives a valid, simple lower bound on the full
    MINOA vehicle-scheduling objective.
    """
    events: list[tuple[int, int]] = []
    for direction_wrap in output.get("directions", []):
        for trip_wrap in direction_wrap["direction"].get("trips", []):
            trip = trip_wrap["trip"]
            events.append((int(trip["startTime"]), 1))
            events.append((int(trip["endTime"]), -1))

    active = 0
    max_active = 0
    for _time, delta in sorted(events, key=lambda item: (item[0], item[1])):
        active += delta
        max_active = max(max_active, active)

    min_fixed_cost = min(spec.usage_cost for spec in vehicle_cost_specs(data).values())
    return round(max_active * min_fixed_cost, 3)
