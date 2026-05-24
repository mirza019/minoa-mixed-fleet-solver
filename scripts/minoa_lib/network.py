from __future__ import annotations

from .time_utils import time_window_index
from .types import JsonDict


def deadhead_arcs(data: JsonDict) -> dict[tuple[str, str], JsonDict]:
    arcs = {}
    for wrap in data["deadheadArcs"]:
        arc = wrap["deadheadArc"]
        arcs[(arc["terminalNode"], arc["deadheadType"])] = arc
    return arcs


def arc_by_code(data: JsonDict) -> dict[int, JsonDict]:
    return {wrap["deadheadArc"]["deadheadArcCode"]: wrap["deadheadArc"] for wrap in data["deadheadArcs"]}


def node_by_name(data: JsonDict) -> dict[str, JsonDict]:
    return {wrap["node"]["nodeName"]: wrap["node"] for wrap in data["nodes"]}


def deadhead_duration(data: JsonDict, arc: JsonDict, terminal_time: int) -> int:
    idx = time_window_index(data["timeHorizon"], terminal_time)
    return arc["travelTimes"][idx]


def min_max_stop(data: JsonDict, node_name: str, arrival_time: int) -> tuple[int, int]:
    node = node_by_name(data)[node_name]
    idx = time_window_index(data["timeHorizon"], arrival_time)
    # MINOA input files use both names in the provided senior instances.
    # Keep the official data unchanged and normalize the schema at read time.
    stopping_windows = node.get("breakingTimes", node.get("stoppingTimes"))
    if stopping_windows is None:
        raise KeyError(f"Node {node_name} has no breakingTimes/stoppingTimes")
    stop = stopping_windows[idx]["stoppingTime"]
    return stop["minStoppingTime"], stop["maxStoppingTime"]


def trip_by_id(data: JsonDict) -> dict[int, JsonDict]:
    result = {}
    for direction_wrap in data["directions"]:
        for tw in direction_wrap["direction"]["trips"]:
            result[tw["trip"]["tripId"]] = tw["trip"]
    return result
