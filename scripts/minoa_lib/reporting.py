from __future__ import annotations

import json
import platform
import subprocess
from pathlib import Path

from .lower_bounds import selected_timetable_fixed_cost_lower_bound
from .types import JsonDict


def cpu_report() -> JsonDict:
    processor = _processor_name()
    machine = platform.machine()
    system = platform.system()
    description = f"{processor} ({machine}), {system}; NBench performance indices not reproduced"
    return {
        "cpuType": {
            "description": description,
            "numberCpu": 1,
            "cpuIntegerIndex": 0.0,
            "cpuFloatIndex": 0.0,
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
    """Backward-compatible wrapper for the selected-timetable fixed-cost bound."""
    return selected_timetable_fixed_cost_lower_bound(data, output).fixed_cost_lb


def update_report_sol(
    output_path: Path,
    *,
    upper_bound: float | None = None,
    execution_time: float | None = None,
    global_lower_bound: float | None = None,
) -> None:
    data = json.loads(output_path.read_text())
    report = data.setdefault("reportSol", {})
    if upper_bound is not None:
        report["upperBound"] = round(float(upper_bound), 3)
    if execution_time is not None:
        report["executionTime"] = round(float(execution_time), 3)
    if global_lower_bound is not None:
        report["lowerBound"] = round(float(global_lower_bound), 3)
    elif "lowerBound" not in report:
        report["lowerBound"] = 0.0
    output_path.write_text(json.dumps(data, indent=2))
