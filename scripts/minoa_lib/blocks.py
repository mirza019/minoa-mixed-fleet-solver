from __future__ import annotations

import os

import networkx as nx

from .activities import activity_break, activity_deadhead, activity_trip, pull_in_activity, pull_out_activity
from .capacity import preferred_charging_spots
from .ev_battery import electric_spec
from .network import deadhead_arcs, deadhead_duration, min_max_stop
from .types import JsonDict, SelectedTrip


def bridge_activities(data: JsonDict, prev: SelectedTrip, nxt: SelectedTrip) -> list[JsonDict] | None:
    prev_trip = prev["trip"]
    next_trip = nxt["trip"]
    prev_dir = prev["direction"]
    next_dir = nxt["direction"]
    if prev_trip["endTime"] > next_trip["startTime"]:
        return None

    candidates: list[list[JsonDict]] = []

    avoid_break_nodes = {
        node.strip()
        for node in os.environ.get("MINOA_AVOID_TERMINAL_BREAK_NODES", "").split(",")
        if node.strip()
    }

    if prev_dir["endNode"] == next_dir["startNode"] and prev_dir["endNode"] not in avoid_break_nodes:
        gap = next_trip["startTime"] - prev_trip["endTime"]
        min_stop, max_stop = min_max_stop(data, prev_dir["endNode"], prev_trip["endTime"])
        if min_stop <= gap <= max_stop:
            if gap == 0:
                candidates.append([])
            else:
                candidates.append(
                    [activity_break(prev_dir["endNode"], prev_trip["endTime"], next_trip["startTime"])]
                )

    allow_depot = True
    if prev_dir["endNode"] == next_dir["startNode"]:
        gap = next_trip["startTime"] - prev_trip["endTime"]
        min_gap = int(os.environ.get("MINOA_DEPOT_BRIDGE_MIN_GAP", "0"))
        allow_depot = gap >= min_gap

    depot_bridge = depot_bridge_activities(data, prev, nxt) if allow_depot else None
    if depot_bridge is not None:
        candidates.append(depot_bridge)

    if candidates:
        return min(candidates, key=bridge_cost_seconds)
    return None


def depot_bridge_activities(data: JsonDict, prev: SelectedTrip, nxt: SelectedTrip) -> list[JsonDict] | None:
    prev_trip = prev["trip"]
    next_trip = nxt["trip"]
    prev_dir = prev["direction"]
    next_dir = nxt["direction"]
    pull_in_arc = deadhead_arcs(data)[(prev_dir["endNode"], "pullIn")]
    pull_in_dur = deadhead_duration(data, pull_in_arc, prev_trip["endTime"])
    pull_in_start = prev_trip["endTime"]
    pull_in_end = pull_in_start + pull_in_dur

    pull_out_arc = deadhead_arcs(data)[(next_dir["startNode"], "pullOut")]
    pull_out_dur = deadhead_duration(data, pull_out_arc, next_trip["startTime"])
    pull_out_end = next_trip["startTime"]
    pull_out_start = pull_out_end - pull_out_dur
    if pull_in_end > pull_out_start:
        return None

    result = [activity_deadhead(pull_in_start, pull_in_end, pull_in_arc["deadheadArcCode"])]
    if pull_in_end < pull_out_start:
        result.append(activity_break("dep", pull_in_end, pull_out_start))
    result.append(activity_deadhead(pull_out_start, pull_out_end, pull_out_arc["deadheadArcCode"]))
    return result


def block_end_trip(block: JsonDict) -> SelectedTrip:
    return block["_items"][-1]


def append_trip_to_block(data: JsonDict, block: JsonDict, item: SelectedTrip) -> bool:
    bridge = bridge_activities(data, block_end_trip(block), item)
    if bridge is None:
        return False
    block["activityList"].extend(bridge)
    block["activityList"].append(activity_trip(item["trip"]["tripId"]))
    block["_items"].append(item)
    return True


def build_chained_ice_blocks(data: JsonDict, selected_items: list[SelectedTrip]) -> list[JsonDict]:
    items = sorted(
        selected_items,
        key=lambda x: (x["trip"]["startTime"], x["trip"]["endTime"], x["trip"]["tripId"]),
    )
    open_blocks: list[JsonDict] = []

    for item in items:
        candidates: list[tuple[int, int, JsonDict]] = []
        for idx, block in enumerate(open_blocks):
            if bridge_activities(data, block_end_trip(block), item) is not None:
                idle = item["trip"]["startTime"] - block_end_trip(block)["trip"]["endTime"]
                candidates.append((idle, idx, block))
        if candidates:
            _, _, block = min(candidates, key=lambda x: x[0])
            appended = append_trip_to_block(data, block, item)
            assert appended
            continue

        block = {
            "vehicleTypeName": "ICE",
            "activityList": [
                pull_out_activity(data, item["direction"]["startNode"], item["trip"]["startTime"]),
                activity_trip(item["trip"]["tripId"]),
            ],
            "_items": [item],
        }
        open_blocks.append(block)

    vehicle_blocks = []
    for block in open_blocks:
        last = block_end_trip(block)
        block["activityList"].append(
            pull_in_activity(data, last["direction"]["endNode"], last["trip"]["endTime"])
        )
        block.pop("_items", None)
        vehicle_blocks.append({"vehicleBlock": block})
    return vehicle_blocks


def build_path_cover_blocks(data: JsonDict, selected_items: list[SelectedTrip]) -> list[JsonDict]:
    """Minimum-cardinality vehicle blocks for a fixed selected trip set."""
    items = sorted(
        selected_items,
        key=lambda x: (x["trip"]["startTime"], x["trip"]["endTime"], x["trip"]["tripId"]),
    )
    n = len(items)
    graph = nx.Graph()
    left = [f"L{i}" for i in range(n)]
    right = [f"R{i}" for i in range(n)]
    graph.add_nodes_from(left, bipartite=0)
    graph.add_nodes_from(right, bipartite=1)

    for i in range(n):
        for j in range(i + 1, n):
            if items[i]["trip"]["endTime"] > items[j]["trip"]["startTime"]:
                continue
            if bridge_activities(data, items[i], items[j]) is not None:
                graph.add_edge(f"L{i}", f"R{j}")

    matching = nx.algorithms.bipartite.maximum_matching(graph, top_nodes=left)
    successor: dict[int, int] = {}
    predecessor: dict[int, int] = {}
    for l_node, r_node in matching.items():
        if not l_node.startswith("L"):
            continue
        i = int(l_node[1:])
        j = int(r_node[1:])
        successor[i] = j
        predecessor[j] = i

    paths: list[list[int]] = []
    for i in range(n):
        if i in predecessor:
            continue
        path = [i]
        while path[-1] in successor:
            path.append(successor[path[-1]])
        paths.append(path)

    vehicle_blocks = []
    for path in paths:
        first = items[path[0]]
        activities = [
            pull_out_activity(data, first["direction"]["startNode"], first["trip"]["startTime"]),
            activity_trip(first["trip"]["tripId"]),
        ]
        for prev_idx, next_idx in zip(path, path[1:]):
            bridge = bridge_activities(data, items[prev_idx], items[next_idx])
            assert bridge is not None
            activities.extend(bridge)
            activities.append(activity_trip(items[next_idx]["trip"]["tripId"]))
        last = items[path[-1]]
        activities.append(pull_in_activity(data, last["direction"]["endNode"], last["trip"]["endTime"]))
        vehicle_blocks.append(
            {
                "vehicleBlock": {
                    "vehicleTypeName": "ICE",
                    "activityList": activities,
                }
            }
        )
    return vehicle_blocks


def bridge_cost_seconds(
    bridge: list[JsonDict],
    data: JsonDict | None = None,
    prev: SelectedTrip | None = None,
    nxt: SelectedTrip | None = None,
    *,
    mode: str = "time",
) -> int:
    """Approximate connection cost used to choose better path covers.

    The official objective is reconstructed internally after EV assignment and
    audited externally for the selected output.  Here we use a solver-side
    surrogate that strongly prefers fewer vehicles first and then lower-cost
    successor choices among matchings with the same cardinality.  The
    charging-aware modes add small penalties and bonuses for EV-relevant break
    structure; complete candidate schedules are ranked by the internal
    objective.
    """
    cost = 0
    for activity in bridge:
        if "deadhead" in activity:
            d = activity["deadhead"]
            cost += d["endingTime"] - d["startingTime"]
        elif "break" in activity:
            windows = activity["break"]["breakTimeWindows"]
            start = windows[0]["breakTimeWindow"]["startTime"]
            end = windows[-1]["breakTimeWindow"]["endTime"]
            if activity["break"]["nameNode"].lower() != "dep":
                cost += end - start
            else:
                cost += (end - start) // 10

    if mode in {"ev", "charging", "balanced"} and data is not None:
        cost += charging_edge_adjustment(data, bridge, mode=mode)
        if prev is not None and nxt is not None:
            cost += successor_pressure_adjustment(data, prev, nxt, mode=mode)
    return cost


def charging_edge_adjustment(data: JsonDict, bridge: list[JsonDict], *, mode: str) -> int:
    """Return an EV-aware edge-cost adjustment in seconds.

    A connection with an existing break at a charging-capable terminal is more
    useful for future EV conversion than a connection with only depot waiting
    or no charging opportunity.  The adjustment remains deliberately bounded:
    it can break ties inside the weighted path cover, but it cannot dominate
    the primary maximum-cardinality objective.
    """
    spec = electric_spec(data)
    if spec is None:
        return 0

    adjustment = 0
    for activity in bridge:
        if "break" not in activity:
            continue
        node = activity["break"]["nameNode"]
        windows = activity["break"]["breakTimeWindows"]
        start = int(windows[0]["breakTimeWindow"]["startTime"])
        end = int(windows[-1]["breakTimeWindow"]["endTime"])
        duration = max(0, end - start)
        has_charger = bool(preferred_charging_spots(data, node))
        if node.lower() == "dep":
            adjustment += min(duration // 8, 900)
        elif has_charger and duration >= spec.min_charging_time:
            bonus = min(duration // 3, 900)
            adjustment -= bonus if mode != "ev" else bonus // 2
        elif duration >= spec.min_charging_time:
            adjustment += min(duration // 12, 300)
    return adjustment


def successor_pressure_adjustment(
    data: JsonDict,
    prev: SelectedTrip,
    nxt: SelectedTrip,
    *,
    mode: str,
) -> int:
    """Penalize successor choices that make EV conversion harder.

    The term is based on the immediate driving distance around an edge.  It is
    not a feasibility proof; it is only a scoring hint for matching.  Full EV
    autonomy, charging, and capacity feasibility are still checked later.
    """
    spec = electric_spec(data)
    if spec is None:
        return 0
    distance = float(prev["trip"].get("lengthTrip", 0.0)) + float(nxt["trip"].get("lengthTrip", 0.0))
    pressure = distance / max(spec.autonomy, 1.0)
    if pressure <= 0.35:
        return 0
    scale = 180 if mode == "balanced" else 300
    return int(scale * pressure)


def build_weighted_path_cover_blocks(
    data: JsonDict,
    selected_items: list[SelectedTrip],
    *,
    edge_mode: str = "time",
) -> list[JsonDict]:
    """Minimum-block path cover with low-cost compatible connections.

    `build_path_cover_blocks` only minimizes the number of paths. This variant
    keeps that priority but, among maximum-cardinality matchings, prefers edges
    with shorter waiting/deadhead connections using weighted matching.  In
    charging-aware modes, the same matching also favors successor edges that
    leave useful charging opportunities inside existing breaks.
    """
    items = sorted(
        selected_items,
        key=lambda x: (x["trip"]["startTime"], x["trip"]["endTime"], x["trip"]["tripId"]),
    )
    n = len(items)
    graph = nx.Graph()
    left = [f"L{i}" for i in range(n)]
    right = [f"R{i}" for i in range(n)]
    graph.add_nodes_from(left, bipartite=0)
    graph.add_nodes_from(right, bipartite=1)

    edge_bridge: dict[tuple[int, int], list[JsonDict]] = {}
    max_possible_cost = 24 * 60 * 60
    for i in range(n):
        for j in range(i + 1, n):
            if items[i]["trip"]["endTime"] > items[j]["trip"]["startTime"]:
                continue
            bridge = bridge_activities(data, items[i], items[j])
            if bridge is None:
                continue
            edge_bridge[(i, j)] = bridge
            edge_cost = bridge_cost_seconds(bridge, data, items[i], items[j], mode=edge_mode)
            graph.add_edge(
                f"L{i}",
                f"R{j}",
                weight=max_possible_cost - edge_cost,
            )

    matching_edges = nx.algorithms.matching.max_weight_matching(
        graph,
        maxcardinality=True,
        weight="weight",
    )
    successor: dict[int, int] = {}
    predecessor: dict[int, int] = {}
    for a, b in matching_edges:
        l_node, r_node = (a, b) if a.startswith("L") else (b, a)
        i = int(l_node[1:])
        j = int(r_node[1:])
        successor[i] = j
        predecessor[j] = i

    paths: list[list[int]] = []
    for i in range(n):
        if i in predecessor:
            continue
        path = [i]
        while path[-1] in successor:
            path.append(successor[path[-1]])
        paths.append(path)

    vehicle_blocks = []
    for path in paths:
        first = items[path[0]]
        activities = [
            pull_out_activity(data, first["direction"]["startNode"], first["trip"]["startTime"]),
            activity_trip(first["trip"]["tripId"]),
        ]
        for prev_idx, next_idx in zip(path, path[1:]):
            bridge = edge_bridge[(prev_idx, next_idx)]
            activities.extend(bridge)
            activities.append(activity_trip(items[next_idx]["trip"]["tripId"]))
        last = items[path[-1]]
        activities.append(pull_in_activity(data, last["direction"]["endNode"], last["trip"]["endTime"]))
        vehicle_blocks.append(
            {
                "vehicleBlock": {
                    "vehicleTypeName": "ICE",
                    "activityList": activities,
                }
            }
        )
    return vehicle_blocks
