from __future__ import annotations

import math

from .time_utils import max_headway_for_pair
from .types import JsonDict, TripWrap


def select_direction_trips(direction: JsonDict, bounds: list[int], variant: int = 0) -> list[TripWrap]:
    """Shortest path from any initial trip to any final trip in the headway graph.

    `variant` changes only tie-breaking among feasible sparse timetables. This
    is useful because many trip selections use the same number of trips but lead
    to very different vehicle waiting/deadhead costs after scheduling.
    """
    trips = sorted(
        direction["trips"],
        key=lambda tw: (tw["trip"]["mainStopArrivalTime"], tw["trip"]["tripId"]),
    )
    n = len(trips)
    if not trips:
        raise ValueError(f"Direction {direction.get('lineName')} has no trips")

    initial = {
        i
        for i, tw in enumerate(trips)
        if tw["trip"].get("isInitialFinalTT", "").lower() == "initial"
    }
    final = {
        i
        for i, tw in enumerate(trips)
        if tw["trip"].get("isInitialFinalTT", "").lower() == "final"
    }
    if not initial or not final:
        raise ValueError(
            f"Direction {direction.get('lineName')} {direction.get('directionType')} "
            "has no initial/final candidate"
        )

    dist = [math.inf] * n
    cost = [math.inf] * n
    pred: list[int | None] = [None] * n
    arrivals = [tw["trip"]["mainStopArrivalTime"] for tw in trips]
    horizon_start, horizon_end = bounds[0], bounds[-1]
    span = max(1, horizon_end - horizon_start)

    for i in initial:
        dist[i] = 1
        cost[i] = _initial_cost(arrivals[i], horizon_start, span, variant)

    headways = direction["headways"]
    max_direction_headway = max(h["headway"]["maxHeadway"] for h in headways)

    for i in range(n):
        if math.isinf(dist[i]):
            continue
        ai = arrivals[i]
        for j in range(i + 1, n):
            aj = arrivals[j]
            if aj - ai > max_direction_headway:
                break
            if aj - ai <= max_headway_for_pair(bounds, headways, ai, aj):
                candidate_dist = dist[i] + 1
                candidate_cost = cost[i] + _edge_cost(ai, aj, bounds, headways, variant)
                if (candidate_dist, candidate_cost) < (dist[j], cost[j]):
                    dist[j] = dist[i] + 1
                    cost[j] = candidate_cost
                    pred[j] = i

    end = min(final, key=lambda i: (dist[i], cost[i], _final_cost(arrivals[i], horizon_end, span, variant)))
    if math.isinf(dist[end]):
        raise ValueError(
            f"No feasible TT path for {direction.get('lineName')} {direction.get('directionType')}"
        )

    path: list[int] = []
    cur: int | None = end
    while cur is not None:
        path.append(cur)
        cur = pred[cur]
    path.reverse()
    return [trips[i] for i in path]


def _initial_cost(arrival: int, horizon_start: int, span: int, variant: int) -> float:
    mode = variant % 8
    normalized = (arrival - horizon_start) / span
    if mode == 1:
        return -arrival
    if mode == 2:
        return arrival
    if mode in {3, 4, 5, 6, 7}:
        target = ((variant * 0.137) % 0.85) + 0.05
        return abs(normalized - target) * span
    return 0.0


def _final_cost(arrival: int, horizon_end: int, span: int, variant: int) -> float:
    mode = variant % 8
    if mode == 1:
        return arrival
    if mode == 2:
        return -arrival
    if mode in {3, 4, 5, 6, 7}:
        target = horizon_end - (((variant * 0.173) % 0.5) * span)
        return abs(arrival - target)
    return 0.0


def _edge_cost(
    first_arrival: int,
    second_arrival: int,
    bounds: list[int],
    headways: list[JsonDict],
    variant: int,
) -> float:
    gap = second_arrival - first_arrival
    max_gap = max_headway_for_pair(bounds, headways, first_arrival, second_arrival)
    mode = variant % 8
    if mode == 1:
        return -second_arrival
    if mode == 2:
        return second_arrival
    if mode == 3:
        return gap
    if mode == 4:
        return -gap
    if mode == 5:
        return abs(gap - 0.80 * max_gap)
    if mode == 6:
        return abs(gap - 0.90 * max_gap)
    if mode == 7:
        return abs(gap - 0.70 * max_gap)
    return 0.0
