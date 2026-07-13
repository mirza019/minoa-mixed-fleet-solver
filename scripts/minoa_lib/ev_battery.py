from __future__ import annotations

from dataclasses import dataclass

from .capacity import normalize_spot
from .network import arc_by_code, trip_by_id
from .types import JsonDict


@dataclass(frozen=True)
class ElectricSpec:
    autonomy: float
    max_charging_time: int
    min_charging_time: int
    fast_coefficient: float
    available_vehicles: int


@dataclass(frozen=True)
class BatteryEvent:
    """Battery state around one activity in an electric vehicle block."""

    position: int
    activity_kind: str
    node: str | None
    start_time: int | None
    end_time: int | None
    distance_km: float
    charge_gain_km: float
    residual_pre_km: float
    residual_post_km: float


@dataclass(frozen=True)
class BatteryTrace:
    """Full residual-autonomy trace for one candidate EV block."""

    events: tuple[BatteryEvent, ...]
    feasible: bool
    min_residual_km: float
    final_residual_km: float


def electric_spec(data: JsonDict) -> ElectricSpec | None:
    for wrap in data["fleet"]["vehicleList"]:
        vehicle_type = wrap["vehicleType"]
        if "electricInfo" not in vehicle_type:
            continue
        info = vehicle_type["electricInfo"]
        return ElectricSpec(
            autonomy=float(info["vehicleAutonomy"]),
            max_charging_time=int(info["maxChargingTime"]),
            min_charging_time=int(info["minChargingTime"]),
            fast_coefficient=float(data["fleet"]["phi"]),
            available_vehicles=int(info["numberVehicle"]),
        )
    return None


def activity_distance(data: JsonDict, activity: JsonDict) -> float:
    if "activityTrip" in activity:
        return float(trip_by_id(data)[activity["activityTrip"]["tripId"]]["lengthTrip"])
    if "deadhead" in activity:
        return float(arc_by_code(data)[activity["deadhead"]["deadheadArcCode"]]["arcLength"])
    return 0.0


def charge_gain(spec: ElectricSpec, duration: int, spot: str) -> float:
    if duration <= 0:
        return 0.0
    full_time = spec.max_charging_time
    if spot.lower() in {"fastcharging", "fastcharge"}:
        full_time = spec.fast_coefficient * spec.max_charging_time
    return spec.autonomy * (duration / full_time)


def required_charge_seconds(spec: ElectricSpec, missing_km: float, spot: str) -> int:
    if missing_km <= 0:
        return 0
    full_time = spec.max_charging_time
    if spot.lower() in {"fastcharging", "fastcharge"}:
        full_time = spec.fast_coefficient * spec.max_charging_time
    seconds = int((missing_km / spec.autonomy) * full_time)
    if seconds % 60:
        seconds += 60 - (seconds % 60)
    return seconds


def charging_gain_for_break(spec: ElectricSpec, activity: JsonDict) -> float:
    """Return the autonomy gain of active charging windows in one break."""
    if "break" not in activity:
        return 0.0
    gain = 0.0
    for window_wrap in activity["break"]["breakTimeWindows"]:
        window = window_wrap["breakTimeWindow"]
        if not window.get("isCharging", False):
            continue
        duration = int(window["endTime"]) - int(window["startTime"])
        gain += charge_gain(spec, duration, normalize_spot(window["typeSpot"]))
    return gain


def activity_time_bounds(activity: JsonDict) -> tuple[int | None, int | None]:
    if "activityTrip" in activity:
        trip = activity["activityTrip"]
        # The activity only stores tripId in generated outputs. Exact trip
        # times are available through the input data and are filled by the
        # trace function for trip activities.
        return None, None
    if "deadhead" in activity:
        deadhead = activity["deadhead"]
        return int(deadhead["startingTime"]), int(deadhead["endingTime"])
    if "break" in activity:
        windows = activity["break"]["breakTimeWindows"]
        return (
            int(windows[0]["breakTimeWindow"]["startTime"]),
            int(windows[-1]["breakTimeWindow"]["endTime"]),
        )
    return None, None


def battery_trace(data: JsonDict, block_wrap: JsonDict, spec: ElectricSpec) -> BatteryTrace:
    """Propagate residual autonomy before and after every block activity.

    Distances and residual autonomy are measured in kilometres. Activity times
    remain in seconds, matching the MINOA input/output format.
    """
    trips = trip_by_id(data)
    residual = spec.autonomy
    min_residual = spec.autonomy
    feasible = True
    events: list[BatteryEvent] = []

    for position, activity in enumerate(block_wrap["vehicleBlock"]["activityList"]):
        pre = residual
        distance = activity_distance(data, activity)
        gain = 0.0
        node: str | None = None
        start, end = activity_time_bounds(activity)
        if "activityTrip" in activity:
            kind = "trip"
            trip = trips[activity["activityTrip"]["tripId"]]
            start = int(trip["startTime"])
            end = int(trip["endTime"])
        elif "deadhead" in activity:
            kind = "deadhead"
        elif "break" in activity:
            kind = "break"
            node = activity["break"]["nameNode"]
            gain = charging_gain_for_break(spec, activity)
        else:
            kind = "other"

        residual = min(spec.autonomy, residual - distance + gain)
        min_residual = min(min_residual, residual)
        if residual < -1e-6:
            feasible = False

        events.append(
            BatteryEvent(
                position=position,
                activity_kind=kind,
                node=node,
                start_time=start,
                end_time=end,
                distance_km=distance,
                charge_gain_km=gain,
                residual_pre_km=pre,
                residual_post_km=residual,
            )
        )

    return BatteryTrace(
        events=tuple(events),
        feasible=feasible,
        min_residual_km=min_residual,
        final_residual_km=residual,
    )


def block_drive_distance(data: JsonDict, block_wrap: JsonDict) -> float:
    return sum(
        activity_distance(data, activity)
        for activity in block_wrap["vehicleBlock"]["activityList"]
        if "activityTrip" in activity or "deadhead" in activity
    )
