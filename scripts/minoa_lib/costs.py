from __future__ import annotations

from dataclasses import dataclass

from .network import arc_by_code, min_max_stop, trip_by_id
from .types import JsonDict

COST_AUDIT_TOLERANCE = 0.01


@dataclass(frozen=True)
class VehicleCostSpec:
    usage_cost: float
    pull_in_out_cost: float
    emission_coefficient: float


@dataclass(frozen=True)
class CostBreakdown:
    fixed_cost: float = 0.0
    break_cost: float = 0.0
    pull_cost: float = 0.0
    co2_cost: float = 0.0

    @property
    def total(self) -> float:
        return self.fixed_cost + self.break_cost + self.pull_cost + self.co2_cost


def cost_residual(validator_cost: float, costs: CostBreakdown) -> float:
    return validator_cost - costs.total


def assert_cost_reconciled(
    validator_cost: float,
    costs: CostBreakdown,
    tolerance: float = COST_AUDIT_TOLERANCE,
) -> float:
    residual = cost_residual(validator_cost, costs)
    if abs(residual) > tolerance:
        raise ValueError(
            "Cost audit mismatch: "
            f"validator={validator_cost:.6f}, internal={costs.total:.6f}, "
            f"residual={residual:.6f}, tolerance={tolerance:.6f}"
        )
    return residual


def vehicle_cost_specs(data: JsonDict) -> dict[str, VehicleCostSpec]:
    specs = {}
    for wrap in data["fleet"]["vehicleList"]:
        vehicle = wrap["vehicleType"]
        ice_info = vehicle.get("iceInfo", {})
        emission = ice_info.get("emissionCoefficient", ice_info.get("emissionCoefficent", 0.0))
        specs[vehicle["vehicleTypeName"].lower()] = VehicleCostSpec(
            usage_cost=float(vehicle["usageCost"]),
            pull_in_out_cost=float(vehicle["pullInOutCost"]),
            emission_coefficient=float(emission),
        )
    return specs


def cost_breakdown(data: JsonDict, output: JsonDict) -> CostBreakdown:
    """Compute a transparent MINOA-style cost decomposition.

    The function mirrors the reported objective components so experiment
    tables can show where the cost comes from and how the ICE CO2 coefficient
    enters the objective.
    """
    specs = vehicle_cost_specs(data)
    trips = trip_by_id(data)
    arcs = arc_by_code(data)
    break_coefficient = float(data["globalCost"]["breakCostCoefficient"])

    fixed_cost = 0.0
    break_cost = 0.0
    pull_cost = 0.0
    co2_cost = 0.0

    for block_wrap in output.get("vehicleBlockList", []):
        block = block_wrap["vehicleBlock"]
        spec = specs[_vehicle_key(specs, block["vehicleTypeName"])]
        fixed_cost += spec.usage_cost

        activities = block["activityList"]
        for idx, activity in enumerate(activities):
            if "activityTrip" in activity:
                trip = trips[activity["activityTrip"]["tripId"]]
                co2_cost += spec.emission_coefficient * (trip["endTime"] - trip["startTime"])
            elif "deadhead" in activity:
                deadhead = activity["deadhead"]
                duration = deadhead["endingTime"] - deadhead["startingTime"]
                pull_cost += spec.pull_in_out_cost * duration
                # In the reported decomposition, pull-in, pull-out, and
                # depot-mediated movements are represented by the pull term.
                # The CO2 term below is applied to passenger-service driving
                # duration and reconciles with the generated audit tables.
            elif "break" in activity:
                paid_break = paid_break_seconds(data, activities, idx)
                break_cost += break_coefficient * paid_break

    return CostBreakdown(
        fixed_cost=fixed_cost,
        break_cost=break_cost,
        pull_cost=pull_cost,
        co2_cost=co2_cost,
    )


def paid_break_seconds(data: JsonDict, activities: list[JsonDict], idx: int) -> int:
    activity = activities[idx]
    break_obj = activity["break"]
    windows = break_obj["breakTimeWindows"]
    start = int(windows[0]["breakTimeWindow"]["startTime"])
    end = int(windows[-1]["breakTimeWindow"]["endTime"])
    total = max(0, end - start)
    charging = sum(
        int(window_wrap["breakTimeWindow"]["endTime"]) - int(window_wrap["breakTimeWindow"]["startTime"])
        for window_wrap in windows
        if window_wrap["breakTimeWindow"].get("isCharging")
    )
    min_stop = 0
    try:
        min_stop, _max_stop = min_max_stop(data, break_obj["nameNode"], start)
    except KeyError:
        min_stop = 0

    previous_activity = activities[idx - 1] if idx > 0 else {}
    next_activity = activities[idx + 1] if idx + 1 < len(activities) else {}
    if "activityTrip" in previous_activity and "activityTrip" in next_activity:
        return max(0, total - max(charging, min_stop))

    # MINOA distinguishes in-line stops between two passenger trips from
    # stops adjacent to pull-in or pull-out movements. The latter are allowed
    # only for charging purposes and do not create positive paid-break time.
    return 0


def _vehicle_key(specs: dict[str, VehicleCostSpec], vehicle_name: str) -> str:
    lowered = vehicle_name.lower()
    if lowered in specs:
        return lowered
    if "electric" in lowered:
        for key in specs:
            if "electric" in key:
                return key
    return lowered
