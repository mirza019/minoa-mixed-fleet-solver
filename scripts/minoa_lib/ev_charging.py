from __future__ import annotations

import copy

from .capacity import CapacityLedger, preferred_charging_spots
from .ev_battery import ElectricSpec, activity_distance, charge_gain
from .types import JsonDict


def _break_bounds(activity: JsonDict) -> tuple[str, int, int]:
    node = activity["break"]["nameNode"]
    windows = activity["break"]["breakTimeWindows"]
    start = int(windows[0]["breakTimeWindow"]["startTime"])
    end = int(windows[-1]["breakTimeWindow"]["endTime"])
    return node, start, end


def _set_break_windows(
    activity: JsonDict,
    node: str,
    start: int,
    charge_end: int,
    end: int,
    spot: str,
) -> None:
    windows = []
    if charge_end > start:
        windows.append(
            {
                "breakTimeWindow": {
                    "startTime": start,
                    "endTime": charge_end,
                    "typeSpot": spot,
                    "isCharging": True,
                }
            }
        )
    if charge_end < end:
        windows.append(
            {
                "breakTimeWindow": {
                    "startTime": charge_end,
                    "endTime": end,
                    "typeSpot": "parking",
                    "isCharging": False,
                }
            }
        )
    activity["break"]["nameNode"] = node
    activity["break"]["breakTimeWindows"] = windows


def make_block_electric_with_charging(
    data: JsonDict,
    block_wrap: JsonDict,
    spec: ElectricSpec,
    ledger: CapacityLedger,
) -> JsonDict | None:
    """Try converting one block to EV by charging greedily during existing breaks.

    The method is intentionally conservative: it never creates new activities,
    only rewrites existing break windows into at most one charging segment plus
    one parking segment. This keeps trip chaining unchanged and lets the
    official validator remain the final feasibility authority.
    """
    candidate = copy.deepcopy(block_wrap)
    block = candidate["vehicleBlock"]
    residual = spec.autonomy

    reservations: list[tuple[str, str, int, int]] = []
    rewritten_breaks: list[tuple[JsonDict, str, int, int, int, str]] = []

    activities = block["activityList"]

    for pos, activity in enumerate(activities):
        if "activityTrip" in activity or "deadhead" in activity:
            residual -= activity_distance(data, activity)
            if residual < -1e-6:
                return None
            continue

        if "break" not in activity:
            continue

        node, start, end = _break_bounds(activity)
        duration = end - start
        if duration < spec.min_charging_time:
            for window_wrap in activity["break"]["breakTimeWindows"]:
                window = window_wrap["breakTimeWindow"]
                reservations.append(
                    (
                        node,
                        window["typeSpot"],
                        int(window["startTime"]),
                        int(window["endTime"]),
                    )
                )
            continue

        missing = spec.autonomy - residual
        if missing <= 1e-6:
            for window_wrap in activity["break"]["breakTimeWindows"]:
                window = window_wrap["breakTimeWindow"]
                reservations.append(
                    (
                        node,
                        window["typeSpot"],
                        int(window["startTime"]),
                        int(window["endTime"]),
                    )
                )
            continue

        if node.lower() == "dep" and _can_reach_later_terminal_charger(
            data,
            activities,
            pos + 1,
            residual,
        ):
            for window_wrap in activity["break"]["breakTimeWindows"]:
                window = window_wrap["breakTimeWindow"]
                reservations.append(
                    (
                        node,
                        window["typeSpot"],
                        int(window["startTime"]),
                        int(window["endTime"]),
                    )
                )
            continue

        charged = False
        for spot in preferred_charging_spots(data, node):
            # Charge as much as this break can usefully accept. The validator
            # rejects charging beyond full battery, so cap by missing autonomy.
            full_time = spec.max_charging_time
            if spot == "fastCharging":
                full_time = spec.fast_coefficient * spec.max_charging_time
            needed = int((missing / spec.autonomy) * full_time)
            if needed % 60:
                needed += 60 - (needed % 60)
            charge_duration = min(duration, needed)
            if charge_duration < spec.min_charging_time:
                continue
            charge_end = start + charge_duration
            if not ledger.can_reserve(node, spot, start, charge_end):
                continue
            if charge_end < end and not ledger.can_reserve(node, "parking", charge_end, end):
                continue
            residual = min(spec.autonomy, residual + charge_gain(spec, charge_duration, spot))
            reservations.append((node, spot, start, charge_end))
            if charge_end < end:
                reservations.append((node, "parking", charge_end, end))
            rewritten_breaks.append((activity, node, start, charge_end, end, spot))
            charged = True
            break

        if not charged:
            # Keep the original break reservation if it was not rewritten.
            for window_wrap in activity["break"]["breakTimeWindows"]:
                window = window_wrap["breakTimeWindow"]
                reservations.append(
                    (
                        node,
                        window["typeSpot"],
                        int(window["startTime"]),
                        int(window["endTime"]),
                    )
                )

    for activity, node, start, charge_end, end, spot in rewritten_breaks:
        _set_break_windows(activity, node, start, charge_end, end, spot)

    try:
        for node, spot, start, end in reservations:
            ledger.reserve(node, spot, start, end)
    except ValueError:
        return None

    block["vehicleTypeName"] = "electric"
    return candidate


def _can_reach_later_terminal_charger(
    data: JsonDict,
    activities: list[JsonDict],
    start_pos: int,
    residual: float,
) -> bool:
    """Return true if the block can defer depot charging safely.

    We only skip depot charging when the current battery can cover all driving
    until a future non-depot break with charging infrastructure. That shifts
    useful charging time from unpaid depot waiting to paid terminal waiting.
    """
    remaining = residual
    for future in activities[start_pos:]:
        if "activityTrip" in future or "deadhead" in future:
            remaining -= activity_distance(data, future)
            if remaining < -1e-6:
                return False
        elif "break" in future:
            node, break_start, break_end = _break_bounds(future)
            if node.lower() == "dep":
                continue
            if break_end - break_start < 60:
                continue
            if preferred_charging_spots(data, node):
                return True
    return True
