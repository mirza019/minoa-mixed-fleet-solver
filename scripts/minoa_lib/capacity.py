from __future__ import annotations

from dataclasses import dataclass, field

from .time_utils import time_window_index
from .types import JsonDict


def node_capacity(data: JsonDict, node_name: str, spot: str) -> int:
    spot = normalize_spot(spot)
    for wrap in data["nodes"]:
        node = wrap["node"]
        if node["nodeName"] != node_name:
            continue
        if spot == "parking":
            return int(node["breakCapacity"])
        if spot == "slowCharging":
            return int(node["slowChargeCapacity"])
        if spot == "fastCharging":
            return int(node["fastChargeCapacity"])
    raise KeyError(node_name)


@dataclass
class CapacityLedger:
    """Minute-level reservation ledger for parking and charger capacity checks."""

    data: JsonDict
    usage: dict[tuple[str, str, int], int] = field(default_factory=dict)

    def can_reserve(self, node: str, spot: str, start: int, end: int) -> bool:
        spot = normalize_spot(spot)
        if end <= start:
            return True
        if start % 60 or end % 60:
            return False
        cap = node_capacity(self.data, node, spot)
        if cap <= 0:
            return False
        for minute in range(start, end, 60):
            key = (node, spot, minute)
            if self.usage.get(key, 0) + 1 > cap:
                return False
        return True

    def reserve(self, node: str, spot: str, start: int, end: int) -> None:
        spot = normalize_spot(spot)
        if end <= start:
            return
        if not self.can_reserve(node, spot, start, end):
            raise ValueError(f"Capacity exceeded for {node} {spot} {start}-{end}")
        for minute in range(start, end, 60):
            key = (node, spot, minute)
            self.usage[key] = self.usage.get(key, 0) + 1

    def reserve_existing_breaks(self, vehicle_blocks: list[JsonDict]) -> None:
        for block_wrap in vehicle_blocks:
            for activity in block_wrap["vehicleBlock"]["activityList"]:
                if "break" not in activity:
                    continue
                node = activity["break"]["nameNode"]
                for window_wrap in activity["break"]["breakTimeWindows"]:
                    window = window_wrap["breakTimeWindow"]
                    spot = normalize_spot(window["typeSpot"])
                    self.reserve(node, spot, int(window["startTime"]), int(window["endTime"]))


def normalize_spot(spot: str) -> str:
    lowered = spot.lower()
    if lowered == "slowcharge":
        return "slowCharging"
    if lowered == "fastcharge":
        return "fastCharging"
    if lowered == "slowcharging":
        return "slowCharging"
    if lowered == "fastcharging":
        return "fastCharging"
    return "parking"


def has_charger(data: JsonDict, node: str, spot: str) -> bool:
    return node_capacity(data, node, spot) > 0


def preferred_charging_spots(data: JsonDict, node: str) -> list[str]:
    spots = []
    if has_charger(data, node, "fastCharging"):
        spots.append("fastCharging")
    if has_charger(data, node, "slowCharging"):
        spots.append("slowCharging")
    return spots
