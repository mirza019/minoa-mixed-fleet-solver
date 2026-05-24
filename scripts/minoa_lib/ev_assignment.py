from __future__ import annotations

from .capacity import CapacityLedger
from .ev_battery import electric_spec
from .ev_charging import make_block_electric_with_charging
from .network import arc_by_code, trip_by_id
from .types import JsonDict


def fleet_type(data: JsonDict, name: str) -> JsonDict | None:
    for wrap in data["fleet"]["vehicleList"]:
        vt = wrap["vehicleType"]
        if vt["vehicleTypeName"].lower() == name.lower():
            return vt
    return None


def block_distance_and_service_time(data: JsonDict, block_wrap: JsonDict) -> tuple[float, int]:
    trips = trip_by_id(data)
    arcs = arc_by_code(data)
    distance = 0.0
    service_time = 0
    for activity in block_wrap["vehicleBlock"]["activityList"]:
        if "activityTrip" in activity:
            trip = trips[activity["activityTrip"]["tripId"]]
            distance += trip["lengthTrip"]
            service_time += trip["endTime"] - trip["startTime"]
        elif "deadhead" in activity:
            distance += arcs[activity["deadhead"]["deadheadArcCode"]]["arcLength"]
    return distance, service_time


def assign_no_charge_evs(data: JsonDict, vehicle_blocks: list[JsonDict]) -> int:
    electric = fleet_type(data, "electric")
    if not electric or "electricInfo" not in electric:
        return 0

    autonomy = electric["electricInfo"]["vehicleAutonomy"]
    available = electric["electricInfo"]["numberVehicle"]
    candidates = []
    for idx, block in enumerate(vehicle_blocks):
        distance, service_time = block_distance_and_service_time(data, block)
        if distance <= autonomy:
            candidates.append((service_time, idx, distance))

    assigned = 0
    for _, idx, _ in sorted(candidates, reverse=True)[:available]:
        vehicle_blocks[idx]["vehicleBlock"]["vehicleTypeName"] = "electric"
        assigned += 1
    return assigned


def assign_charging_aware_evs(data: JsonDict, vehicle_blocks: list[JsonDict]) -> int:
    """Assign EVs with charging insertion during existing breaks.

    Blocks are considered in descending service time, because converting long
    service blocks saves the most ICE emission cost while preserving vehicle
    count. Each accepted conversion is checked against a minute-level capacity
    ledger before it is committed.
    """
    spec = electric_spec(data)
    if spec is None:
        return 0

    scored = []
    for idx, block in enumerate(vehicle_blocks):
        distance, service_time = block_distance_and_service_time(data, block)
        scored.append((service_time, distance, idx))

    assigned = 0
    accepted: dict[int, JsonDict] = {}
    ledger = CapacityLedger(data)

    for _, _, idx in sorted(scored, reverse=True):
        if assigned >= spec.available_vehicles:
            break
        converted = make_block_electric_with_charging(data, vehicle_blocks[idx], spec, ledger)
        if converted is None:
            continue
        accepted[idx] = converted
        assigned += 1

    # Reserve and keep original breaks for blocks that were not converted.
    for idx, block in enumerate(vehicle_blocks):
        if idx in accepted:
            vehicle_blocks[idx] = accepted[idx]
        else:
            try:
                ledger.reserve_existing_breaks([block])
            except ValueError:
                # Some experimental builders can already violate parking
                # capacity. Keep the original block and let the official
                # validator report the infeasibility instead of aborting the
                # experiment run.
                pass

    return assigned
