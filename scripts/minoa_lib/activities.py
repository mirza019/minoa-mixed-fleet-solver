from __future__ import annotations

from .network import deadhead_arcs, deadhead_duration
from .types import JsonDict


def activity_trip(trip_id: int) -> JsonDict:
    return {"activityTrip": {"tripId": trip_id}}


def activity_deadhead(start: int, end: int, code: int) -> JsonDict:
    return {
        "deadhead": {
            "startingTime": int(start),
            "endingTime": int(end),
            "deadheadArcCode": int(code),
        }
    }


def activity_break(
    node: str,
    start: int,
    end: int,
    spot: str = "parking",
    charging: bool = False,
) -> JsonDict:
    return {
        "break": {
            "nameNode": node,
            "breakTimeWindows": [
                {
                    "breakTimeWindow": {
                        "startTime": int(start),
                        "endTime": int(end),
                        "typeSpot": spot,
                        "isCharging": charging,
                    }
                }
            ],
        }
    }


def pull_out_activity(data: JsonDict, start_node: str, trip_start: int) -> JsonDict:
    arc = deadhead_arcs(data)[(start_node, "pullOut")]
    dur = deadhead_duration(data, arc, trip_start)
    return activity_deadhead(trip_start - dur, trip_start, arc["deadheadArcCode"])


def pull_in_activity(data: JsonDict, end_node: str, trip_end: int) -> JsonDict:
    arc = deadhead_arcs(data)[(end_node, "pullIn")]
    dur = deadhead_duration(data, arc, trip_end)
    return activity_deadhead(trip_end, trip_end + dur, arc["deadheadArcCode"])

