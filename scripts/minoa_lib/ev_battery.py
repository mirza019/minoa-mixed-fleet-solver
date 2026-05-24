from __future__ import annotations

from dataclasses import dataclass

from .network import arc_by_code, trip_by_id
from .types import JsonDict


@dataclass(frozen=True)
class ElectricSpec:
    autonomy: float
    max_charging_time: int
    min_charging_time: int
    fast_coefficient: float
    available_vehicles: int


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
    if spot.lower() == "fastcharging":
        full_time = spec.fast_coefficient * spec.max_charging_time
    return spec.autonomy * (duration / full_time)


def required_charge_seconds(spec: ElectricSpec, missing_km: float, spot: str) -> int:
    if missing_km <= 0:
        return 0
    full_time = spec.max_charging_time
    if spot.lower() == "fastcharging":
        full_time = spec.fast_coefficient * spec.max_charging_time
    seconds = int((missing_km / spec.autonomy) * full_time)
    if seconds % 60:
        seconds += 60 - (seconds % 60)
    return seconds

