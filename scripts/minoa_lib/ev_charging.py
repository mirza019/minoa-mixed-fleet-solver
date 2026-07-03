from __future__ import annotations

import copy
from dataclasses import dataclass

from .capacity import CapacityLedger, preferred_charging_spots
from .activities import output_spot_name
from .ev_battery import ElectricSpec, activity_distance, battery_trace, charge_gain, required_charge_seconds
from .types import JsonDict


@dataclass(frozen=True)
class ChargingPlan:
    """One candidate rewrite for a single break activity."""

    activity: JsonDict
    node: str
    break_start: int
    break_end: int
    charge_start: int
    charge_end: int
    spot: str
    score: float
    expected_gain_km: float


@dataclass(frozen=True)
class BlockChargingResult:
    """Internal diagnostics for one EV conversion attempt."""

    block: JsonDict
    charging_events: int
    charging_seconds: int
    min_residual_km: float
    final_residual_km: float


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
    charge_start: int,
    charge_end: int,
    end: int,
    spot: str,
) -> None:
    windows = []
    if charge_start > start:
        windows.append(
            {
                "breakTimeWindow": {
                    "startTime": start,
                    "endTime": charge_start,
                    "typeSpot": "parking",
                    "isCharging": False,
                }
            }
        )
    if charge_end > charge_start:
        windows.append(
            {
                "breakTimeWindow": {
                    "startTime": charge_start,
                    "endTime": charge_end,
                    "typeSpot": output_spot_name(spot),
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
    strategy: str = "legacy",
) -> JsonDict | None:
    result = make_block_electric_with_charging_result(data, block_wrap, spec, ledger, strategy=strategy)
    return result.block if result is not None else None


def make_block_electric_with_charging_result(
    data: JsonDict,
    block_wrap: JsonDict,
    spec: ElectricSpec,
    ledger: CapacityLedger,
    strategy: str = "legacy",
) -> BlockChargingResult | None:
    if strategy == "lookahead":
        return _make_block_electric_lookahead_result(data, block_wrap, spec, ledger)
    return _make_block_electric_legacy_result(data, block_wrap, spec, ledger)


def _make_block_electric_legacy_result(
    data: JsonDict,
    block_wrap: JsonDict,
    spec: ElectricSpec,
    ledger: CapacityLedger,
) -> BlockChargingResult | None:
    """Try converting one block to EV by charging greedily during existing breaks.

    This is the validated default used by the main multistart experiments. It
    keeps the block structure fixed and rewrites only existing break windows.
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
        _set_break_windows(activity, node, start, start, charge_end, end, spot)

    trace = battery_trace(data, candidate, spec)
    if not trace.feasible:
        return None

    try:
        for node, spot, start, end in reservations:
            ledger.reserve(node, spot, start, end)
    except ValueError:
        return None

    block["vehicleTypeName"] = "electric"
    return BlockChargingResult(
        block=candidate,
        charging_events=len(rewritten_breaks),
        charging_seconds=sum(charge_end - start for _, _, start, charge_end, _, _ in rewritten_breaks),
        min_residual_km=trace.min_residual_km,
        final_residual_km=trace.final_residual_km,
    )


def _make_block_electric_lookahead_result(
    data: JsonDict,
    block_wrap: JsonDict,
    spec: ElectricSpec,
    ledger: CapacityLedger,
) -> BlockChargingResult | None:
    """Try converting one block to EV with local charging-plan selection.

    The method remains deliberately local: it never creates new activities and
    only rewrites existing break windows. For each break it evaluates feasible
    charging plans, including no charging, early charging, late charging, and
    slow/fast alternatives. This strengthens the EV layer while preserving the
    path-cover vehicle-block structure.
    """
    candidate = copy.deepcopy(block_wrap)
    block = candidate["vehicleBlock"]
    residual = spec.autonomy

    reservations: list[tuple[str, str, int, int]] = []
    rewritten_breaks: list[ChargingPlan] = []

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
        required = _required_autonomy_gain(data, activities, pos + 1, residual, spec)

        if required <= 1e-6 or duration < spec.min_charging_time:
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

        plan = _best_charging_plan(data, activities, pos, residual, required, spec, ledger)
        if plan is not None:
            residual = min(spec.autonomy, residual + plan.expected_gain_km)
            if plan.charge_start > start:
                reservations.append((node, "parking", start, plan.charge_start))
            reservations.append((node, plan.spot, plan.charge_start, plan.charge_end))
            if plan.charge_end < end:
                reservations.append((node, "parking", plan.charge_end, end))
            rewritten_breaks.append(plan)
            continue

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

    for plan in rewritten_breaks:
        _set_break_windows(
            plan.activity,
            plan.node,
            plan.break_start,
            plan.charge_start,
            plan.charge_end,
            plan.break_end,
            plan.spot,
        )

    trace = battery_trace(data, candidate, spec)
    if not trace.feasible:
        return None

    try:
        for node, spot, start, end in reservations:
            ledger.reserve(node, spot, start, end)
    except ValueError:
        return None

    block["vehicleTypeName"] = "electric"
    return BlockChargingResult(
        block=candidate,
        charging_events=len(rewritten_breaks),
        charging_seconds=sum(plan.charge_end - plan.charge_start for plan in rewritten_breaks),
        min_residual_km=trace.min_residual_km,
        final_residual_km=trace.final_residual_km,
    )


def _best_charging_plan(
    data: JsonDict,
    activities: list[JsonDict],
    pos: int,
    residual: float,
    required_gain: float,
    spec: ElectricSpec,
    ledger: CapacityLedger,
) -> ChargingPlan | None:
    activity = activities[pos]
    node, start, end = _break_bounds(activity)
    duration = end - start
    plans: list[ChargingPlan] = []

    for spot in preferred_charging_spots(data, node):
        max_gain = max(0.0, spec.autonomy - residual)
        gain_targets = {
            min(max_gain, required_gain),
            min(max_gain, required_gain + 0.10 * spec.autonomy),
            max_gain,
        }
        for gain in gain_targets:
            charge_duration = required_charge_seconds(spec, gain, spot)
            if charge_duration <= 0:
                continue
            if charge_duration < spec.min_charging_time:
                charge_duration = spec.min_charging_time
            if charge_duration > duration:
                continue
            for placement in ("early", "late"):
                if placement == "early":
                    charge_start = start
                    charge_end = start + charge_duration
                else:
                    charge_end = end
                    charge_start = end - charge_duration
                if charge_start % 60 or charge_end % 60:
                    continue
                if not _can_reserve_split(ledger, node, spot, start, charge_start, charge_end, end):
                    continue
                expected_gain = min(max_gain, charge_gain(spec, charge_duration, spot))
                future_pressure = _future_charger_pressure(data, activities, pos + 1, node, spot)
                score = (
                    charge_duration
                    + 120.0 * future_pressure
                    + (30.0 if spot == "fastCharging" else 0.0)
                    + (5.0 if placement == "late" else 0.0)
                )
                plans.append(
                    ChargingPlan(
                        activity=activity,
                        node=node,
                        break_start=start,
                        break_end=end,
                        charge_start=charge_start,
                        charge_end=charge_end,
                        spot=spot,
                        score=score,
                        expected_gain_km=expected_gain,
                    )
                )

    if not plans:
        return None
    return min(plans, key=lambda plan: (plan.score, plan.charge_end - plan.charge_start, plan.spot))


def _can_reserve_split(
    ledger: CapacityLedger,
    node: str,
    spot: str,
    start: int,
    charge_start: int,
    charge_end: int,
    end: int,
) -> bool:
    if charge_start > start and not ledger.can_reserve(node, "parking", start, charge_start):
        return False
    if not ledger.can_reserve(node, spot, charge_start, charge_end):
        return False
    if charge_end < end and not ledger.can_reserve(node, "parking", charge_end, end):
        return False
    return True


def _required_autonomy_gain(
    data: JsonDict,
    activities: list[JsonDict],
    start_pos: int,
    residual: float,
    spec: ElectricSpec,
) -> float:
    """Estimate the minimum useful gain at the current break.

    The target is the smaller of (a) autonomy needed until the next usable
    charging opportunity and (b) autonomy needed until the block ends. This is
    the look-ahead part of the local charging optimizer.
    """
    need_until_next = 0.0
    need_until_end = 0.0
    next_charger_found = False
    for future in activities[start_pos:]:
        if "activityTrip" in future or "deadhead" in future:
            dist = activity_distance(data, future)
            need_until_end += dist
            if not next_charger_found:
                need_until_next += dist
        elif "break" in future and not next_charger_found:
            node, break_start, break_end = _break_bounds(future)
            if break_end - break_start >= spec.min_charging_time and preferred_charging_spots(data, node):
                next_charger_found = True

    target = need_until_next if next_charger_found else need_until_end
    safety_margin = min(0.05 * spec.autonomy, 2.0)
    return max(0.0, target + safety_margin - residual)


def _future_charger_pressure(
    data: JsonDict,
    activities: list[JsonDict],
    start_pos: int,
    current_node: str,
    current_spot: str,
) -> int:
    pressure = 0
    for future in activities[start_pos:]:
        if "break" not in future:
            continue
        node, _, _ = _break_bounds(future)
        if node == current_node and current_spot in preferred_charging_spots(data, node):
            pressure += 1
    return pressure


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
