from __future__ import annotations

from dataclasses import dataclass
import math
import time
from typing import Iterable

from .costs import vehicle_cost_specs
from .network import trip_by_id
from .time_utils import max_headway_for_pair, time_window_index
from .types import JsonDict

try:  # Optional at import time, required only for global MILP bounds.
    import numpy as np
    from scipy.optimize import Bounds, LinearConstraint, milp
    from scipy.sparse import coo_matrix
except Exception:  # pragma: no cover - exercised when SciPy is unavailable.
    np = None
    Bounds = None
    LinearConstraint = None
    coo_matrix = None
    milp = None

try:
    import networkx as nx
except Exception:  # pragma: no cover - networkx is part of the project env.
    nx = None


@dataclass(frozen=True)
class LowerBoundReport:
    vehicle_count_lb: int
    fixed_cost_lb: float
    scope: str

    def gap_ub_percent(self, upper_bound: float | None) -> float | None:
        if upper_bound is None or upper_bound <= 0:
            return None
        return 100.0 * (upper_bound - self.fixed_cost_lb) / upper_bound


@dataclass(frozen=True)
class SelectedTimetableLowerBoundReport(LowerBoundReport):
    overlap_vehicle_lb: int
    path_cover_vehicle_lb: int
    selected_trips: int


@dataclass(frozen=True)
class GlobalLowerBoundReport(LowerBoundReport):
    status: str
    runtime_seconds: float
    solver: str
    time_limit_seconds: float | None
    dual_bound: float | None
    incumbent: float | None
    solver_gap: float | None
    globally_valid: bool
    candidate_trips: int
    timetable_arcs: int
    overlap_constraints: int


def selected_timetable_overlap_vehicle_lower_bound(output: JsonDict) -> int:
    """Overlap lower bound for the timetable selected in one output.

    Every passenger trip active at the same time must be served by a different
    vehicle. This gives a valid lower bound for this fixed selected timetable.
    It is not a global bound for the full integrated problem because a different
    feasible timetable may select different trips.
    """
    events: list[tuple[int, int]] = []
    for direction_wrap in output.get("directions", []):
        for trip_wrap in direction_wrap["direction"].get("trips", []):
            trip = trip_wrap["trip"]
            events.append((int(trip["startTime"]), 1))
            events.append((int(trip["endTime"]), -1))

    active = 0
    max_active = 0
    # End events are processed before start events at the same timestamp, so
    # half-open trip intervals [start, end) do not create false overlap.
    for _time, delta in sorted(events, key=lambda item: (item[0], item[1])):
        active += delta
        max_active = max(max_active, active)
    return max_active


def selected_timetable_vehicle_lower_bound(output: JsonDict) -> int:
    """Backward-compatible alias for the selected-timetable overlap bound."""
    return selected_timetable_overlap_vehicle_lower_bound(output)


def selected_timetable_path_cover_vehicle_lower_bound(data: JsonDict, output: JsonDict) -> int:
    """Exact relaxed path-cover bound for the selected timetable.

    The graph contains one node per selected trip and an arc when two trips do
    not overlap in time. Deadhead, stopping, charging, and capacity constraints
    are ignored here, so every original vehicle block remains feasible in this
    relaxed graph. The minimum path-cover size is therefore a valid diagnostic
    lower bound for this fixed selected timetable.
    """
    selected = _selected_trip_records(data, output)
    n = len(selected)
    if n == 0:
        return 0
    if nx is None:
        return selected_timetable_overlap_vehicle_lower_bound(output)

    items = sorted(selected, key=lambda item: (item["startTime"], item["endTime"], item["tripId"]))
    graph = nx.Graph()
    left = [f"L{i}" for i in range(n)]
    right = [f"R{i}" for i in range(n)]
    graph.add_nodes_from(left, bipartite=0)
    graph.add_nodes_from(right, bipartite=1)

    for i in range(n):
        end_i = int(items[i]["endTime"])
        for j in range(i + 1, n):
            if end_i <= int(items[j]["startTime"]):
                graph.add_edge(f"L{i}", f"R{j}")

    matching = nx.algorithms.bipartite.maximum_matching(graph, top_nodes=left)
    matched_left = sum(1 for node in matching if node.startswith("L"))
    return n - matched_left


def selected_timetable_fixed_cost_lower_bound(data: JsonDict, output: JsonDict) -> SelectedTimetableLowerBoundReport:
    overlap_lb = selected_timetable_overlap_vehicle_lower_bound(output)
    path_cover_lb = selected_timetable_path_cover_vehicle_lower_bound(data, output)
    vehicle_lb = max(overlap_lb, path_cover_lb)
    min_fixed_cost = min(spec.usage_cost for spec in vehicle_cost_specs(data).values())
    return SelectedTimetableLowerBoundReport(
        vehicle_count_lb=vehicle_lb,
        fixed_cost_lb=round(vehicle_lb * min_fixed_cost, 3),
        scope="selected timetable diagnostic fixed-cost lower bound",
        overlap_vehicle_lb=overlap_lb,
        path_cover_vehicle_lb=path_cover_lb,
        selected_trips=len(_selected_trip_records(data, output)),
    )


def zero_global_lower_bound(data: JsonDict, *, status: str = "not_computed") -> GlobalLowerBoundReport:
    return GlobalLowerBoundReport(
        vehicle_count_lb=0,
        fixed_cost_lb=0.0,
        scope="global lower bound",
        status=status,
        runtime_seconds=0.0,
        solver="none",
        time_limit_seconds=None,
        dual_bound=0.0,
        incumbent=None,
        solver_gap=None,
        globally_valid=True,
        candidate_trips=count_candidate_trips(data),
        timetable_arcs=0,
        overlap_constraints=0,
    )


def global_timetable_overlap_lower_bound(
    data: JsonDict,
    *,
    time_limit_seconds: float | None = 60.0,
) -> GlobalLowerBoundReport:
    """Compute a globally valid timetable-overlap lower bound.

    The model keeps the timetable path requirements in every direction and
    minimizes the maximum number of selected trips that overlap in time. Since
    every real vehicle schedule must use at least one vehicle for every active
    passenger trip, this peak-overlap value is a global vehicle-count lower
    bound. The model relaxes deadhead, charging, break, parking, and vehicle
    assignment decisions, so it cannot overestimate the true optimum.
    """
    if milp is None or np is None or Bounds is None or LinearConstraint is None or coo_matrix is None:
        return zero_global_lower_bound(data, status="solver_unavailable")

    start = time.perf_counter()
    model = _build_timetable_overlap_model(data)
    if model["trip_count"] == 0:
        return zero_global_lower_bound(data, status="empty_instance")

    c = np.zeros(model["var_count"])
    c[model["k_index"]] = 1.0
    lb = np.zeros(model["var_count"])
    ub = np.ones(model["var_count"])
    ub[model["k_index"]] = model["trip_count"]
    integrality = np.ones(model["var_count"])
    integrality[model["k_index"]] = 1

    options = {"disp": False}
    if time_limit_seconds is not None and time_limit_seconds > 0:
        options["time_limit"] = float(time_limit_seconds)

    try:
        result = milp(
            c=c,
            integrality=integrality,
            bounds=Bounds(lb, ub),
            constraints=LinearConstraint(model["matrix"], model["row_lb"], model["row_ub"]),
            options=options,
        )
    except Exception as exc:
        report = zero_global_lower_bound(data, status=f"solver_error:{type(exc).__name__}")
        return _replace_global_runtime(report, time.perf_counter() - start)

    runtime = time.perf_counter() - start
    incumbent = _finite_float(getattr(result, "fun", None))
    dual_bound = _finite_float(getattr(result, "mip_dual_bound", None))
    solver_gap = _finite_float(getattr(result, "mip_gap", None))

    status_code = int(getattr(result, "status", -1))
    if status_code == 0 and incumbent is not None:
        bound_value = incumbent
        status = "optimal"
    elif dual_bound is not None:
        bound_value = max(0.0, dual_bound)
        status = "time_limit_dual_bound" if status_code == 1 else "dual_bound"
    else:
        return _zero_global_lower_bound_from_model(
            data,
            model,
            status=f"no_certified_bound_status_{status_code}",
            runtime=runtime,
        )

    vehicle_lb = int(math.ceil(max(0.0, bound_value) - 1e-7))
    min_fixed_cost = min(spec.usage_cost for spec in vehicle_cost_specs(data).values())
    return GlobalLowerBoundReport(
        vehicle_count_lb=vehicle_lb,
        fixed_cost_lb=round(max(0.0, bound_value) * min_fixed_cost, 3),
        scope="global timetable-overlap fixed-cost lower bound",
        status=status,
        runtime_seconds=round(runtime, 6),
        solver="scipy-highs",
        time_limit_seconds=time_limit_seconds,
        dual_bound=dual_bound,
        incumbent=incumbent,
        solver_gap=solver_gap,
        globally_valid=True,
        candidate_trips=model["trip_count"],
        timetable_arcs=model["arc_count"],
        overlap_constraints=model["overlap_constraints"],
    )


def count_candidate_trips(data: JsonDict) -> int:
    return sum(len(direction_wrap["direction"].get("trips", [])) for direction_wrap in data.get("directions", []))


def _build_timetable_overlap_model(data: JsonDict) -> JsonDict:
    trip_index: dict[int, int] = {}
    trips: list[JsonDict] = []
    direction_arcs: list[tuple[int, int | None, int | None]] = []
    incoming: dict[int, list[int]] = {}
    outgoing: dict[int, list[int]] = {}
    source_arcs: dict[int, list[int]] = {}
    sink_arcs: dict[int, list[int]] = {}

    for direction_index, direction_wrap in enumerate(data["directions"]):
        direction = direction_wrap["direction"]
        local = sorted(
            direction.get("trips", []),
            key=lambda tw: (tw["trip"]["mainStopArrivalTime"], tw["trip"]["tripId"]),
        )
        local_indices: list[int] = []
        for wrap in local:
            trip = wrap["trip"]
            idx = len(trips)
            trip_index[int(trip["tripId"])] = idx
            trips.append(trip)
            incoming[idx] = []
            outgoing[idx] = []
            local_indices.append(idx)

        initial = [
            idx
            for idx in local_indices
            if str(trips[idx].get("isInitialFinalTT", "")).lower() == "initial"
        ]
        final = [
            idx
            for idx in local_indices
            if str(trips[idx].get("isInitialFinalTT", "")).lower() == "final"
        ]
        source_arcs[direction_index] = []
        sink_arcs[direction_index] = []

        for idx in initial:
            arc_idx = len(direction_arcs)
            direction_arcs.append((direction_index, None, idx))
            incoming[idx].append(arc_idx)
            source_arcs[direction_index].append(arc_idx)

        for idx in final:
            arc_idx = len(direction_arcs)
            direction_arcs.append((direction_index, idx, None))
            outgoing[idx].append(arc_idx)
            sink_arcs[direction_index].append(arc_idx)

        headways = direction["headways"]
        max_direction_headway = max(h["headway"]["maxHeadway"] for h in headways)
        for pos_i, idx_i in enumerate(local_indices):
            ai = int(trips[idx_i]["mainStopArrivalTime"])
            for idx_j in local_indices[pos_i + 1 :]:
                aj = int(trips[idx_j]["mainStopArrivalTime"])
                if aj - ai > max_direction_headway:
                    break
                min_gap, max_gap = _headway_bounds_for_pair(data["timeHorizon"], headways, ai, aj)
                if min_gap <= aj - ai <= max_gap:
                    arc_idx = len(direction_arcs)
                    direction_arcs.append((direction_index, idx_i, idx_j))
                    outgoing[idx_i].append(arc_idx)
                    incoming[idx_j].append(arc_idx)

    trip_count = len(trips)
    x_offset = 0
    z_offset = trip_count
    k_index = z_offset + len(direction_arcs)
    var_count = k_index + 1

    rows: list[int] = []
    cols: list[int] = []
    vals: list[float] = []
    row_lb: list[float] = []
    row_ub: list[float] = []

    def add_row(entries: Iterable[tuple[int, float]], lb: float, ub: float) -> None:
        row = len(row_lb)
        for col, value in entries:
            rows.append(row)
            cols.append(col)
            vals.append(value)
        row_lb.append(lb)
        row_ub.append(ub)

    for direction_index in range(len(data["directions"])):
        add_row(((z_offset + arc, 1.0) for arc in source_arcs[direction_index]), 1.0, 1.0)
        add_row(((z_offset + arc, 1.0) for arc in sink_arcs[direction_index]), 1.0, 1.0)

    for idx in range(trip_count):
        add_row(
            [(z_offset + arc, 1.0) for arc in incoming[idx]] + [(x_offset + idx, -1.0)],
            0.0,
            0.0,
        )
        add_row(
            [(z_offset + arc, 1.0) for arc in outgoing[idx]] + [(x_offset + idx, -1.0)],
            0.0,
            0.0,
        )

    overlap_constraints = 0
    for event_time in sorted({int(trip["startTime"]) for trip in trips}):
        active = [
            idx
            for idx, trip in enumerate(trips)
            if int(trip["startTime"]) <= event_time < int(trip["endTime"])
        ]
        if not active:
            continue
        add_row([(x_offset + idx, 1.0) for idx in active] + [(k_index, -1.0)], -math.inf, 0.0)
        overlap_constraints += 1

    matrix = coo_matrix((vals, (rows, cols)), shape=(len(row_lb), var_count))
    return {
        "matrix": matrix,
        "row_lb": np.array(row_lb, dtype=float),
        "row_ub": np.array(row_ub, dtype=float),
        "var_count": var_count,
        "k_index": k_index,
        "trip_count": trip_count,
        "arc_count": len(direction_arcs),
        "overlap_constraints": overlap_constraints,
    }


def _headway_bounds_for_pair(
    bounds: list[int],
    headways: list[JsonDict],
    first_arrival: int,
    second_arrival: int,
) -> tuple[int, int]:
    ia = time_window_index(bounds, first_arrival)
    ib = time_window_index(bounds, second_arrival)
    min_gap = max(
        int(headways[ia]["headway"].get("minHeadway", 0)),
        int(headways[ib]["headway"].get("minHeadway", 0)),
    )
    max_gap = max_headway_for_pair(bounds, headways, first_arrival, second_arrival)
    return min_gap, max_gap


def _selected_trip_records(data: JsonDict, output: JsonDict) -> list[JsonDict]:
    input_trips = trip_by_id(data)
    selected: list[JsonDict] = []
    for direction_wrap in output.get("directions", []):
        for trip_wrap in direction_wrap["direction"].get("trips", []):
            trip_id = int(trip_wrap["trip"]["tripId"])
            selected.append(input_trips.get(trip_id, trip_wrap["trip"]))
    return selected


def _finite_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _replace_global_runtime(report: GlobalLowerBoundReport, runtime: float) -> GlobalLowerBoundReport:
    return GlobalLowerBoundReport(
        vehicle_count_lb=report.vehicle_count_lb,
        fixed_cost_lb=report.fixed_cost_lb,
        scope=report.scope,
        status=report.status,
        runtime_seconds=round(runtime, 6),
        solver=report.solver,
        time_limit_seconds=report.time_limit_seconds,
        dual_bound=report.dual_bound,
        incumbent=report.incumbent,
        solver_gap=report.solver_gap,
        globally_valid=report.globally_valid,
        candidate_trips=report.candidate_trips,
        timetable_arcs=report.timetable_arcs,
        overlap_constraints=report.overlap_constraints,
    )


def _zero_global_lower_bound_from_model(
    data: JsonDict,
    model: JsonDict,
    *,
    status: str,
    runtime: float,
) -> GlobalLowerBoundReport:
    report = zero_global_lower_bound(data, status=status)
    return GlobalLowerBoundReport(
        vehicle_count_lb=report.vehicle_count_lb,
        fixed_cost_lb=report.fixed_cost_lb,
        scope=report.scope,
        status=report.status,
        runtime_seconds=round(runtime, 6),
        solver="scipy-highs",
        time_limit_seconds=report.time_limit_seconds,
        dual_bound=report.dual_bound,
        incumbent=report.incumbent,
        solver_gap=report.solver_gap,
        globally_valid=report.globally_valid,
        candidate_trips=model["trip_count"],
        timetable_arcs=model["arc_count"],
        overlap_constraints=model["overlap_constraints"],
    )


def coverage_sets(data: JsonDict, output: JsonDict) -> tuple[set[int], list[int]]:
    selected: set[int] = set()
    served: list[int] = []
    for direction_wrap in output.get("directions", []):
        for trip_wrap in direction_wrap["direction"].get("trips", []):
            selected.add(int(trip_wrap["trip"]["tripId"]))
    for block_wrap in output.get("vehicleBlockList", []):
        for activity in block_wrap["vehicleBlock"].get("activityList", []):
            if "activityTrip" in activity:
                served.append(int(activity["activityTrip"]["tripId"]))
    # Touch the input trip index so tests catch outputs with unknown trip ids.
    trips = trip_by_id(data)
    for trip_id in served:
        if trip_id not in trips:
            raise KeyError(f"served trip {trip_id} is not present in the input")
    return selected, served


def coverage_issues(data: JsonDict, output: JsonDict) -> dict[str, list[int]]:
    selected, served_list = coverage_sets(data, output)
    served = set(served_list)
    duplicates = sorted({trip_id for trip_id in served_list if served_list.count(trip_id) > 1})
    return {
        "duplicate_served_trips": duplicates,
        "unserved_selected_trips": sorted(selected - served),
        "unselected_served_trips": sorted(served - selected),
    }


def validate_trip_coverage(data: JsonDict, output: JsonDict) -> None:
    issues = coverage_issues(data, output)
    failures = {key: value for key, value in issues.items() if value}
    if failures:
        raise ValueError(f"trip coverage mismatch: {failures}")
