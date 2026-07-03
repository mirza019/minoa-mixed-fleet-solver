from __future__ import annotations

from .capacity import CapacityLedger, preferred_charging_spots, node_capacity
from .costs import vehicle_cost_specs
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


def block_ev_priority(data: JsonDict, block_wrap: JsonDict, strategy: str = "legacy") -> float:
    """Score one block for EV conversion.

    The legacy order uses service time only.  The risk-aware order is still a
    heuristic, but it uses whole-block information before attempting the actual
    battery and capacity simulation: expected CO2 saving, distance pressure,
    available charging breaks, and scarcity of chargers on those breaks.
    """
    distance, service_time = block_distance_and_service_time(data, block_wrap)
    if strategy not in {"risk", "risk-lookahead"}:
        return float(service_time)

    spec = electric_spec(data)
    if spec is None:
        return float("-inf")

    co2_saving = _ice_service_co2_cost(data, block_wrap)
    charging_seconds = _charging_opportunity_seconds(data, block_wrap, spec.min_charging_time)
    charger_pressure = _charger_pressure(data, block_wrap, spec.min_charging_time)
    autonomy_pressure = distance / max(spec.autonomy, 1.0)
    hard_risk_penalty = 0.0
    if distance > spec.autonomy and charging_seconds <= 0:
        hard_risk_penalty = 10_000.0

    return (
        20.0 * co2_saving
        + 0.01 * service_time
        + 0.005 * charging_seconds
        - 80.0 * autonomy_pressure
        - 30.0 * charger_pressure
        - hard_risk_penalty
    )


def _ice_service_co2_cost(data: JsonDict, block_wrap: JsonDict) -> float:
    specs = vehicle_cost_specs(data)
    ice = next((spec for name, spec in specs.items() if "electric" not in name), None)
    if ice is None:
        return 0.0
    trips = trip_by_id(data)
    service_seconds = 0
    for activity in block_wrap["vehicleBlock"]["activityList"]:
        if "activityTrip" not in activity:
            continue
        trip = trips[activity["activityTrip"]["tripId"]]
        service_seconds += int(trip["endTime"]) - int(trip["startTime"])
    return ice.emission_coefficient * service_seconds


def _charging_opportunity_seconds(data: JsonDict, block_wrap: JsonDict, min_duration: int) -> int:
    total = 0
    for activity in block_wrap["vehicleBlock"]["activityList"]:
        if "break" not in activity:
            continue
        node = activity["break"]["nameNode"]
        if not preferred_charging_spots(data, node):
            continue
        windows = activity["break"]["breakTimeWindows"]
        start = int(windows[0]["breakTimeWindow"]["startTime"])
        end = int(windows[-1]["breakTimeWindow"]["endTime"])
        if end - start >= min_duration:
            total += end - start
    return total


def _charger_pressure(data: JsonDict, block_wrap: JsonDict, min_duration: int) -> float:
    pressure = 0.0
    for activity in block_wrap["vehicleBlock"]["activityList"]:
        if "break" not in activity:
            continue
        node = activity["break"]["nameNode"]
        spots = preferred_charging_spots(data, node)
        if not spots:
            continue
        windows = activity["break"]["breakTimeWindows"]
        start = int(windows[0]["breakTimeWindow"]["startTime"])
        end = int(windows[-1]["breakTimeWindow"]["endTime"])
        duration = end - start
        if duration < min_duration:
            continue
        capacity = sum(node_capacity(data, node, spot) for spot in spots)
        pressure += duration / max(capacity, 1)
    return pressure / 3600.0


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


def assign_charging_aware_evs(
    data: JsonDict,
    vehicle_blocks: list[JsonDict],
    *,
    strategy: str = "legacy",
) -> int:
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
        priority = block_ev_priority(data, block, strategy=strategy)
        scored.append((priority, service_time, -distance, idx))

    assigned = 0
    accepted: dict[int, JsonDict] = {}
    ledger = CapacityLedger(data)

    charging_strategy = "lookahead" if strategy in {"lookahead", "risk", "risk-lookahead"} else "legacy"

    for *_score, idx in sorted(scored, reverse=True):
        if assigned >= spec.available_vehicles:
            break
        converted = make_block_electric_with_charging(
            data,
            vehicle_blocks[idx],
            spec,
            ledger,
            strategy=charging_strategy,
        )
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
