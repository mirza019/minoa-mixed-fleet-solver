from __future__ import annotations

import argparse
import copy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from minoa_lib.activities import activity_break, activity_deadhead, activity_trip
from minoa_lib.blocks import bridge_activities, bridge_cost_seconds, build_path_cover_blocks
from minoa_lib.capacity import CapacityLedger, normalize_spot
from minoa_lib.costs import assert_cost_reconciled, cost_breakdown, paid_break_seconds
from minoa_lib.ev_assignment import block_ev_priority
from minoa_lib.ev_battery import activity_distance, battery_trace, charge_gain, electric_spec, required_charge_seconds
from minoa_lib.ev_charging import make_block_electric_with_charging_result
from minoa_lib.lower_bounds import (
    coverage_issues,
    global_timetable_overlap_lower_bound,
    selected_timetable_fixed_cost_lower_bound,
    selected_timetable_path_cover_vehicle_lower_bound,
    selected_timetable_vehicle_lower_bound,
    validate_trip_coverage,
)
from minoa_lib.network import deadhead_duration, min_max_stop
from minoa_lib.reporting import cpu_report
from minoa_lib.timetable import select_direction_trips
from minoa_lib.time_utils import time_window_index
from minoa_optimize import classify_failure, failure_counts, is_better_internal_candidate, search_configs


def base_data() -> dict:
    return {
        "timeHorizon": [0, 1000, 2000],
        "nodes": [
            {
                "node": {
                    "nodeName": "dep",
                    "breakCapacity": 2,
                    "slowChargeCapacity": 1,
                    "fastChargeCapacity": 1,
                    "breakingTimes": [
                        {"stoppingTime": {"minStoppingTime": 60, "maxStoppingTime": 99999}},
                        {"stoppingTime": {"minStoppingTime": 60, "maxStoppingTime": 99999}},
                    ],
                }
            },
            {
                "node": {
                    "nodeName": "A",
                    "breakCapacity": 1,
                    "slowChargeCapacity": 1,
                    "fastChargeCapacity": 1,
                    "breakingTimes": [
                        {"stoppingTime": {"minStoppingTime": 120, "maxStoppingTime": 600}},
                        {"stoppingTime": {"minStoppingTime": 180, "maxStoppingTime": 700}},
                    ],
                }
            },
            {
                "node": {
                    "nodeName": "B",
                    "breakCapacity": 1,
                    "slowChargeCapacity": 1,
                    "fastChargeCapacity": 0,
                    "breakingTimes": [
                        {"stoppingTime": {"minStoppingTime": 120, "maxStoppingTime": 600}},
                        {"stoppingTime": {"minStoppingTime": 180, "maxStoppingTime": 700}},
                    ],
                }
            },
        ],
        "deadheadArcs": [
            {
                "deadheadArc": {
                    "deadheadArcCode": 1,
                    "terminalNode": "A",
                    "deadheadType": "pullOut",
                    "arcLength": 2.0,
                    "travelTimes": [100, 200],
                }
            },
            {
                "deadheadArc": {
                    "deadheadArcCode": 2,
                    "terminalNode": "A",
                    "deadheadType": "pullIn",
                    "arcLength": 2.0,
                    "travelTimes": [110, 210],
                }
            },
            {
                "deadheadArc": {
                    "deadheadArcCode": 3,
                    "terminalNode": "B",
                    "deadheadType": "pullOut",
                    "arcLength": 3.0,
                    "travelTimes": [130, 230],
                }
            },
            {
                "deadheadArc": {
                    "deadheadArcCode": 4,
                    "terminalNode": "B",
                    "deadheadType": "pullIn",
                    "arcLength": 3.0,
                    "travelTimes": [140, 240],
                }
            },
        ],
        "directions": [
            {
                "direction": {
                    "lineName": "L1",
                    "directionType": "inBound",
                    "startNode": "A",
                    "endNode": "A",
                    "headways": [
                        {"headway": {"minHeadway": 0, "idealHeadway": 300, "maxHeadway": 500}},
                        {"headway": {"minHeadway": 0, "idealHeadway": 300, "maxHeadway": 500}},
                    ],
                    "trips": [
                        {
                            "trip": {
                                "tripId": 1,
                                "startTime": 100,
                                "endTime": 700,
                                "mainStopArrivalTime": 200,
                                "lengthTrip": 5.0,
                                "isInitialFinalTT": "initial",
                            }
                        },
                        {
                            "trip": {
                                "tripId": 2,
                                "startTime": 1000,
                                "endTime": 1600,
                                "mainStopArrivalTime": 600,
                                "lengthTrip": 7.0,
                                "isInitialFinalTT": "final",
                            }
                        },
                    ],
                }
            }
        ],
        "fleet": {
            "phi": 0.5,
            "vehicleList": [
                {
                    "vehicleType": {
                        "vehicleTypeName": "ICE",
                        "usageCost": 100.0,
                        "pullInOutCost": 0.1,
                        "iceInfo": {"emissionCoefficient": 0.01},
                    }
                },
                {
                    "vehicleType": {
                        "vehicleTypeName": "electric",
                        "usageCost": 120.0,
                        "pullInOutCost": 0.05,
                        "electricInfo": {
                            "numberVehicle": 2,
                            "vehicleAutonomy": 20,
                            "maxChargingTime": 1200,
                            "minChargingTime": 120,
                        },
                    }
                },
            ],
        },
        "globalCost": {"breakCostCoefficient": 0.02},
    }


def selected_item(data: dict, trip_id: int, direction_index: int = 0) -> dict:
    direction = data["directions"][direction_index]["direction"]
    for wrap in direction["trips"]:
        if wrap["trip"]["tripId"] == trip_id:
            return {"direction": direction, "trip": wrap["trip"]}
    raise KeyError(trip_id)


def selected_output(data: dict) -> dict:
    output = copy.deepcopy(data)
    output["vehicleBlockList"] = [
        {
            "vehicleBlock": {
                "vehicleTypeName": "ICE",
                "activityList": [activity_trip(1), activity_trip(2)],
            }
        }
    ]
    return output


def test_time_window_boundary_uses_right_closed_interval() -> None:
    assert time_window_index([0, 10, 20], 10) == 0
    assert time_window_index([0, 10, 20], 11) == 1


def test_deadhead_duration_uses_terminal_time_window() -> None:
    data = base_data()
    arc = data["deadheadArcs"][0]["deadheadArc"]
    assert deadhead_duration(data, arc, 900) == 100
    assert deadhead_duration(data, arc, 1500) == 200


def test_min_max_stop_uses_arrival_time_window() -> None:
    assert min_max_stop(base_data(), "A", 900) == (120, 600)
    assert min_max_stop(base_data(), "A", 1500) == (180, 700)


def test_timetable_selection_requires_initial_trip() -> None:
    data = base_data()
    direction = copy.deepcopy(data["directions"][0]["direction"])
    direction["trips"][0]["trip"]["isInitialFinalTT"] = "null"
    try:
        select_direction_trips(direction, data["timeHorizon"])
    except ValueError as exc:
        assert "initial/final" in str(exc)
    else:
        raise AssertionError("missing initial trip was not rejected")


def test_timetable_selection_requires_final_trip() -> None:
    data = base_data()
    direction = copy.deepcopy(data["directions"][0]["direction"])
    direction["trips"][1]["trip"]["isInitialFinalTT"] = "null"
    try:
        select_direction_trips(direction, data["timeHorizon"])
    except ValueError as exc:
        assert "initial/final" in str(exc)
    else:
        raise AssertionError("missing final trip was not rejected")


def test_timetable_selection_respects_maximum_headway() -> None:
    data = base_data()
    direction = copy.deepcopy(data["directions"][0]["direction"])
    direction["headways"][0]["headway"]["maxHeadway"] = 100
    direction["headways"][1]["headway"]["maxHeadway"] = 100
    try:
        select_direction_trips(direction, data["timeHorizon"])
    except ValueError as exc:
        assert "No feasible TT path" in str(exc)
    else:
        raise AssertionError("excessive headway was not rejected")


def test_output_spot_names_follow_validator_terms() -> None:
    # The PDF lists slowCharge/fastCharge, but the provided Java validator
    # recognizes the legacy slowCharging/fastCharging labels in generated
    # output files. The writer therefore emits validator-compatible labels.
    assert activity_break("A", 0, 60, "slowCharging", True)["break"]["breakTimeWindows"][0]["breakTimeWindow"]["typeSpot"] == "slowCharging"
    assert activity_break("A", 0, 60, "fastCharging", True)["break"]["breakTimeWindows"][0]["breakTimeWindow"]["typeSpot"] == "fastCharging"


def test_spot_normalizer_accepts_format_and_internal_terms() -> None:
    assert normalize_spot("slowCharge") == "slowCharging"
    assert normalize_spot("fastCharge") == "fastCharging"


def test_capacity_rejects_non_minute_granularity() -> None:
    ledger = CapacityLedger(base_data())
    assert not ledger.can_reserve("A", "parking", 0, 61)


def test_capacity_counts_slot_occupation() -> None:
    ledger = CapacityLedger(base_data())
    assert ledger.can_reserve("A", "slowCharge", 0, 60)
    ledger.reserve("A", "slowCharge", 0, 60)
    assert not ledger.can_reserve("A", "slowCharge", 0, 60)


def test_charge_gain_accepts_official_fast_charge_spelling() -> None:
    spec = electric_spec(base_data())
    assert spec is not None
    assert charge_gain(spec, 300, "fastCharge") == 10


def test_required_charge_seconds_rounds_to_minutes() -> None:
    spec = electric_spec(base_data())
    assert spec is not None
    assert required_charge_seconds(spec, 1, "slowCharge") == 60


def test_activity_distance_uses_trip_km() -> None:
    assert activity_distance(base_data(), activity_trip(1)) == 5.0


def test_activity_distance_uses_deadhead_km() -> None:
    assert activity_distance(base_data(), activity_deadhead(0, 100, 1)) == 2.0


def test_battery_trace_records_pre_and_post_residuals() -> None:
    data = base_data()
    spec = electric_spec(data)
    assert spec is not None
    block = {
        "vehicleBlock": {
            "vehicleTypeName": "electric",
            "activityList": [
                activity_trip(1),
                {
                    "break": {
                        "nameNode": "A",
                        "breakTimeWindows": [
                            {
                                "breakTimeWindow": {
                                    "startTime": 720,
                                    "endTime": 840,
                                    "typeSpot": "slowCharging",
                                    "isCharging": True,
                                }
                            }
                        ],
                    }
                },
                activity_deadhead(840, 940, 1),
            ],
        }
    }

    trace = battery_trace(data, block, spec)

    assert trace.feasible
    assert [event.activity_kind for event in trace.events] == ["trip", "break", "deadhead"]
    assert trace.events[0].residual_pre_km == 20
    assert trace.events[0].residual_post_km == 15
    assert trace.events[1].charge_gain_km == 2
    assert trace.events[1].residual_post_km == 17
    assert trace.events[2].residual_post_km == 15


def test_charging_optimizer_skips_unnecessary_charging() -> None:
    data = base_data()
    spec = electric_spec(data)
    assert spec is not None
    block = {
        "vehicleBlock": {
            "vehicleTypeName": "ICE",
            "activityList": [
                activity_trip(1),
                activity_break("A", 720, 960, "parking", False),
                activity_trip(2),
            ],
        }
    }

    result = make_block_electric_with_charging_result(data, block, spec, CapacityLedger(data), strategy="lookahead")

    assert result is not None
    assert result.charging_events == 0
    break_windows = result.block["vehicleBlock"]["activityList"][1]["break"]["breakTimeWindows"]
    assert len(break_windows) == 1
    assert not break_windows[0]["breakTimeWindow"]["isCharging"]


def test_charging_optimizer_inserts_minimum_partial_charge() -> None:
    data = base_data()
    data["directions"][0]["direction"]["trips"][1]["trip"]["lengthTrip"] = 18.0
    spec = electric_spec(data)
    assert spec is not None
    block = {
        "vehicleBlock": {
            "vehicleTypeName": "ICE",
            "activityList": [
                activity_trip(1),
                activity_break("A", 720, 1200, "parking", False),
                activity_trip(2),
            ],
        }
    }

    result = make_block_electric_with_charging_result(data, block, spec, CapacityLedger(data), strategy="lookahead")

    assert result is not None
    assert result.charging_events == 1
    assert 0 < result.charging_seconds < 480
    trace = battery_trace(data, result.block, spec)
    assert trace.feasible
    assert trace.min_residual_km >= -1e-6


def test_paid_break_inline_uses_max_of_charge_and_min_stop() -> None:
    data = base_data()
    activities = [
        activity_trip(1),
        activity_break("A", 700, 1000, "parking", False),
        activity_trip(2),
    ]
    assert paid_break_seconds(data, activities, 1) == 180


def test_paid_break_inline_charging_absorbs_stop_time() -> None:
    data = base_data()
    activities = [
        activity_trip(1),
        {
            "break": {
                "nameNode": "A",
                "breakTimeWindows": [
                    {"breakTimeWindow": {"startTime": 700, "endTime": 940, "typeSpot": "slowCharge", "isCharging": True}},
                    {"breakTimeWindow": {"startTime": 940, "endTime": 1000, "typeSpot": "parking", "isCharging": False}},
                ],
            }
        },
        activity_trip(2),
    ]
    assert paid_break_seconds(data, activities, 1) == 60


def test_paid_break_next_to_pull_movement_is_zero() -> None:
    data = base_data()
    activities = [
        activity_trip(1),
        activity_break("A", 700, 900, "parking", False),
        activity_deadhead(900, 1010, 2),
    ]
    assert paid_break_seconds(data, activities, 1) == 0


def test_cost_breakdown_uses_reported_service_driving_duration_for_co2() -> None:
    data = base_data()
    output = {
        "vehicleBlockList": [
            {
                "vehicleBlock": {
                    "vehicleTypeName": "ICE",
                    "activityList": [
                        activity_deadhead(0, 100, 1),
                        activity_trip(1),
                        activity_break("A", 700, 1000, "parking", False),
                        activity_trip(2),
                        activity_deadhead(1600, 1710, 2),
                    ],
                }
            }
        ]
    }
    costs = cost_breakdown(data, output)
    assert round(costs.co2_cost, 2) == 12.00
    assert round(costs.pull_cost, 2) == 21.00
    assert round(costs.break_cost, 2) == 3.60
    assert_cost_reconciled(136.60, costs)


def test_cost_reconciliation_rejects_mismatch() -> None:
    data = base_data()
    output = {
        "vehicleBlockList": [
            {
                "vehicleBlock": {
                    "vehicleTypeName": "ICE",
                    "activityList": [
                        activity_deadhead(0, 100, 1),
                        activity_trip(1),
                        activity_deadhead(700, 810, 2),
                    ],
                }
            }
        ]
    }
    costs = cost_breakdown(data, output)
    try:
        assert_cost_reconciled(costs.total + 1.0, costs)
    except ValueError as exc:
        assert "Cost audit mismatch" in str(exc)
    else:
        raise AssertionError("expected a cost audit mismatch")


def test_selected_timetable_vehicle_lower_bound_uses_half_open_intervals() -> None:
    data = base_data()
    output = selected_output(data)
    assert selected_timetable_vehicle_lower_bound(output) == 1


def test_selected_timetable_fixed_cost_lower_bound_uses_cheapest_vehicle_type() -> None:
    data = base_data()
    output = selected_output(data)
    report = selected_timetable_fixed_cost_lower_bound(data, output)
    assert report.vehicle_count_lb == 1
    assert report.fixed_cost_lb == 100.0
    assert report.scope == "selected timetable diagnostic fixed-cost lower bound"


def test_selected_timetable_path_cover_bound_counts_singletons() -> None:
    data = base_data()
    output = selected_output(data)
    output["directions"][0]["direction"]["trips"].append(
        {
            "trip": {
                "tripId": 99,
                "startTime": 500,
                "endTime": 800,
                "mainStopArrivalTime": 500,
                "lengthTrip": 3.0,
                "isInitialFinalTT": "null",
            }
        }
    )
    data["directions"][0]["direction"]["trips"].append(copy.deepcopy(output["directions"][0]["direction"]["trips"][-1]))
    assert selected_timetable_path_cover_vehicle_lower_bound(data, output) == 2


def test_global_timetable_overlap_lower_bound_counts_unavoidable_parallel_directions() -> None:
    data = base_data()
    second = copy.deepcopy(data["directions"][0])
    second["direction"]["lineName"] = "L2"
    second["direction"]["directionType"] = "outBound"
    second["direction"]["trips"][0]["trip"]["tripId"] = 3
    second["direction"]["trips"][1]["trip"]["tripId"] = 4
    data["directions"].append(second)

    report = global_timetable_overlap_lower_bound(data, time_limit_seconds=10)
    assert report.globally_valid
    assert report.vehicle_count_lb == 2
    assert report.fixed_cost_lb == 200.0
    assert report.status == "optimal"


def test_trip_coverage_accepts_exact_selected_served_match() -> None:
    data = base_data()
    validate_trip_coverage(data, selected_output(data))


def test_trip_coverage_detects_duplicate_trip() -> None:
    data = base_data()
    output = selected_output(data)
    output["vehicleBlockList"][0]["vehicleBlock"]["activityList"].append(activity_trip(1))
    issues = coverage_issues(data, output)
    assert issues["duplicate_served_trips"] == [1]


def test_trip_coverage_detects_unserved_selected_trip() -> None:
    data = base_data()
    output = selected_output(data)
    output["vehicleBlockList"][0]["vehicleBlock"]["activityList"] = [activity_trip(1)]
    issues = coverage_issues(data, output)
    assert issues["unserved_selected_trips"] == [2]


def test_trip_coverage_detects_unselected_served_trip() -> None:
    data = base_data()
    output = selected_output(data)
    output["directions"][0]["direction"]["trips"] = output["directions"][0]["direction"]["trips"][:1]
    issues = coverage_issues(data, output)
    assert issues["unselected_served_trips"] == [2]


def test_cpu_report_marks_unmeasured_benchmarks() -> None:
    report = cpu_report()["cpuType"]
    assert report["numberCpu"] == 1
    assert report["cpuIntegerIndex"] == 0.0
    assert report["cpuFloatIndex"] == 0.0
    assert "NBench" in report["description"]


def test_multistart_incumbent_uses_internal_objective_before_external_audit() -> None:
    incumbent = 200.0
    invalid_low_internal = {
        "valid": False,
        "objective": None,
        "internal_objective": 100.0,
    }
    valid_better_internal = {
        "valid": True,
        "objective": 210.0,
        "internal_objective": 150.0,
    }
    valid_worse_internal = {
        "valid": True,
        "objective": 190.0,
        "internal_objective": 250.0,
    }
    assert not is_better_internal_candidate(invalid_low_internal, incumbent)
    assert is_better_internal_candidate(valid_better_internal, incumbent)
    assert not is_better_internal_candidate(valid_worse_internal, incumbent)


def test_failure_counts_group_recorded_candidate_reasons() -> None:
    rows = [
        {"valid": False, "failure_reason": classify_failure("No feasible TT path")},
        {"valid": False, "failure_reason": classify_failure("slow charge capacity exceeded")},
        {"valid": False, "failure_reason": classify_failure("slow charge capacity exceeded")},
        {"valid": True, "failure_reason": ""},
    ]
    assert failure_counts(rows) == {
        "no valid headway path": 1,
        "slow-charge capacity conflict": 2,
    }


def test_inline_bridge_respects_stopping_bounds(monkeypatch) -> None:
    monkeypatch.setenv("MINOA_DEPOT_BRIDGE_MIN_GAP", "9999")
    data = base_data()
    bridge = bridge_activities(data, selected_item(data, 1), selected_item(data, 2))
    assert bridge is not None
    assert "break" in bridge[0]


def test_charging_aware_edge_scoring_prefers_useful_terminal_break(monkeypatch) -> None:
    monkeypatch.setenv("MINOA_DEPOT_BRIDGE_MIN_GAP", "9999")
    data = base_data()
    data["fleet"]["vehicleList"][1]["vehicleType"]["electricInfo"]["vehicleAutonomy"] = 100
    prev = selected_item(data, 1)
    nxt = selected_item(data, 2)
    bridge = bridge_activities(data, prev, nxt)
    assert bridge is not None

    time_only = bridge_cost_seconds(bridge, data, prev, nxt, mode="time")
    charging_aware = bridge_cost_seconds(bridge, data, prev, nxt, mode="charging")

    assert charging_aware < time_only


def test_risk_ev_priority_rewards_charging_capable_blocks() -> None:
    data = base_data()
    data["nodes"][0]["node"]["slowChargeCapacity"] = 0
    data["nodes"][0]["node"]["fastChargeCapacity"] = 0
    charging_block = {
        "vehicleBlock": {
            "vehicleTypeName": "ICE",
            "activityList": [
                activity_trip(1),
                activity_break("A", 720, 1080, "parking", False),
                activity_trip(2),
            ],
        }
    }
    no_charging_block = copy.deepcopy(charging_block)
    no_charging_block["vehicleBlock"]["activityList"][1] = activity_break(
        "dep",
        720,
        1080,
        "parking",
        False,
    )

    assert block_ev_priority(data, charging_block, strategy="risk") > block_ev_priority(
        data,
        no_charging_block,
        strategy="risk",
    )


def test_risk_ev_priority_penalizes_energy_risk_without_charging() -> None:
    data = base_data()
    data["nodes"][0]["node"]["slowChargeCapacity"] = 0
    data["nodes"][0]["node"]["fastChargeCapacity"] = 0
    data["directions"][0]["direction"]["trips"][0]["trip"]["lengthTrip"] = 16.0
    data["directions"][0]["direction"]["trips"][1]["trip"]["lengthTrip"] = 16.0
    risky_block = {
        "vehicleBlock": {
            "vehicleTypeName": "ICE",
            "activityList": [
                activity_trip(1),
                activity_break("dep", 720, 1080, "parking", False),
                activity_trip(2),
            ],
        }
    }
    safer_block = copy.deepcopy(risky_block)
    safer_block["vehicleBlock"]["activityList"][1] = activity_break(
        "A",
        720,
        1080,
        "parking",
        False,
    )

    assert block_ev_priority(data, safer_block, strategy="risk") > block_ev_priority(
        data,
        risky_block,
        strategy="risk",
    )


def test_adaptive_multistart_adds_named_local_neighborhoods() -> None:
    args = argparse.Namespace(
        edge_mode="time",
        ev_strategy="legacy",
        ev_mode="charging",
        no_adaptive=False,
    )

    names = [config.name for config in search_configs(args)]

    assert "base" in names
    assert "charging-edge-score" in names
    assert "lookahead-charging" in names
    assert "risk-aware-ev-assignment" in names
    assert "charging-risk-rematch" in names
    assert "successor-swap-no-depot-shortcut" in names
    assert "local-no-depot-risk" in names


def test_path_cover_reconstructs_unmatched_singletons_as_blocks() -> None:
    data = base_data()
    blocks = build_path_cover_blocks(data, [selected_item(data, 1), selected_item(data, 2)])
    assert len(blocks) == 1
    trip_ids = [
        act["activityTrip"]["tripId"]
        for act in blocks[0]["vehicleBlock"]["activityList"]
        if "activityTrip" in act
    ]
    assert trip_ids == [1, 2]
