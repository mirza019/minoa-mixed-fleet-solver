from __future__ import annotations

from typing import Any


JsonDict = dict[str, Any]
Trip = JsonDict
TripWrap = JsonDict
SelectedTrip = JsonDict


CPU_REPORT: JsonDict = {
    "cpuType": {
        "description": "Local development CPU, benchmark not measured",
        "numberCpu": 1,
        "cpuIntegerIndex": 1.0,
        "cpuFloatIndex": 1.0,
    }
}

