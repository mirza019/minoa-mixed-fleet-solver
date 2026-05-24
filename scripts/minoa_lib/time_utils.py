from __future__ import annotations

from .types import JsonDict


def time_window_index(bounds: list[int], t: int) -> int:
    for i in range(1, len(bounds)):
        if bounds[i - 1] <= t <= bounds[i]:
            return i - 1
    if t < bounds[0]:
        return 0
    return len(bounds) - 2


def max_headway_for_pair(bounds: list[int], headways: list[JsonDict], a: int, b: int) -> int:
    ia = time_window_index(bounds, a)
    ib = time_window_index(bounds, b)
    return max(
        headways[ia]["headway"]["maxHeadway"],
        headways[ib]["headway"]["maxHeadway"],
    )

