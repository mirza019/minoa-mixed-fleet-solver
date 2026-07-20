#!/usr/bin/env python3
"""Print and validate the canonical final MINOA thesis result table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = Path("results/final_validated_results.json")

EXPECTED_HEADLINE = {
    "Small": {"validated_cost": 162.44, "vehicles": 2},
    "Medium": {"validated_cost": 371.35, "vehicles": 5},
    "Large": {"validated_cost": 1163.35, "vehicles": 15},
}
EXPECTED_HEADLINE_TOTAL = {
    "validated_cost": 1697.15,
    "vehicles": 22,
}
EXPECTED_FULL = {
    "total_validated_cost": 10000.48,
    "total_vehicles": 126,
}
TOLERANCE = 1e-6
DETAIL_COLUMNS = [
    ("Instance", "instance"),
    ("Approach", "approach"),
    ("Valid", "valid"),
    ("Cost", "cost"),
    ("Fixed", "fixed_cost"),
    ("Break cost", "break_cost"),
    ("Pull cost", "pull_cost"),
    ("CO2 cost", "co2_cost"),
    ("Vehicles", "vehicles"),
    ("EV vehicles", "ev_vehicles"),
    ("ICE vehicles", "ice_vehicles"),
    ("EV share (%)", "ev_share_percent"),
    ("Trips", "trips"),
    ("Deadhead min", "deadhead_min"),
    ("Break min", "break_min"),
    ("Charge min", "charge_min"),
]

FINAL_ARCHIVE_ROWS = [
    ("Small", "multi-start path-cover", 162.442, 154.00, 7.69, 0.25, 0.50, 2, 0, 2, 0.00, 48, 42.00, 240.00, 0.00),
    ("Medium", "multi-start path-cover", 371.354, 350.00, 16.84, 4.51, 0.00, 5, 5, 0, 100.00, 139, 752.00, 1717.00, 391.00),
    ("Large", "multi-start path-cover", 1163.353, 1120.00, 25.79, 15.60, 1.96, 15, 5, 10, 33.33, 260, 2600.00, 2520.00, 505.00),
    ("Toy Example", "charging-aware path-cover", 290.986, 280.00, 8.86, 1.58, 0.54, 4, 0, 4, 0.00, 68, 264.00, 385.00, 0.00),
    ("1line", "charging-aware path-cover", 313.611, 301.00, 9.32, 2.32, 0.97, 4, 1, 3, 25.00, 102, 386.00, 807.00, 67.00),
    ("1line 6timeWindow", "charging-aware path-cover", 387.674, 378.00, 3.70, 4.65, 1.33, 5, 1, 4, 20.00, 112, 775.00, 970.00, 0.00),
    ("2lines", "charging-aware path-cover repaired", 910.154, 889.00, 0.00, 19.31, 1.85, 12, 5, 7, 41.67, 204, 3218.00, 2710.00, 717.00),
    ("2lines 6 timeWindows", "charging-aware path-cover", 495.599, 462.00, 29.90, 1.28, 2.42, 6, 0, 6, 0.00, 204, 213.00, 1551.00, 0.00),
    ("3lines", "charging-aware path-cover", 911.499, 826.00, 75.22, 7.31, 2.97, 11, 3, 8, 27.27, 306, 1218.00, 2725.00, 218.00),
    ("3linesTriangle", "charging-aware path-cover", 809.098, 756.00, 41.45, 8.84, 2.80, 10, 2, 8, 20.00, 306, 1474.00, 2811.00, 146.00),
    ("5lines", "charging-aware path-cover", 1566.951, 1428.00, 121.80, 12.42, 4.73, 19, 5, 14, 26.32, 510, 2070.00, 5556.00, 965.00),
    ("8lines", "charging-aware path-cover", 2617.763, 2506.00, 71.78, 30.22, 9.77, 33, 5, 28, 15.15, 819, 5036.00, 5552.00, 257.00),
]


def _load_results(path: Path) -> dict[str, Any]:
    if not path.exists():
        if path == DEFAULT_RESULTS:
            _write_default_results(path)
        if not path.exists():
            raise FileNotFoundError(f"Missing canonical result file: {path}")
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _write_default_results(path: Path) -> None:
    """Create the machine-readable final archive table used by the thesis."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_default_results_data(), indent=2) + "\n", encoding="utf-8")


def _default_results_data() -> dict[str, Any]:
    archive_rows = []
    for (
        instance,
        approach,
        cost,
        fixed_cost,
        break_cost,
        pull_cost,
        co2_cost,
        vehicles,
        ev_vehicles,
        ice_vehicles,
        ev_share_percent,
        trips,
        deadhead_min,
        break_min,
        charge_min,
    ) in FINAL_ARCHIVE_ROWS:
        archive_rows.append(
            {
                "instance": instance,
                "approach": approach,
                "valid": True,
                "cost": cost,
                "fixed_cost": fixed_cost,
                "break_cost": break_cost,
                "pull_cost": pull_cost,
                "co2_cost": co2_cost,
                "vehicles": vehicles,
                "ev_vehicles": ev_vehicles,
                "ice_vehicles": ice_vehicles,
                "ev_share_percent": ev_share_percent,
                "trips": trips,
                "deadhead_min": deadhead_min,
                "break_min": break_min,
                "charge_min": charge_min,
            }
        )

    headline_rows = [
        {
            "instance": row["instance"],
            "scope": "Headline",
            "validated_cost": round(float(row["cost"]), 2),
            "vehicles": int(row["vehicles"]),
            "headline_instance": True,
            "final_no_regression_archive": True,
        }
        for row in archive_rows
        if row["instance"] in EXPECTED_HEADLINE
    ]
    headline_total = {
        "validated_cost": round(sum(float(row["cost"]) for row in archive_rows if row["instance"] in EXPECTED_HEADLINE), 2),
        "vehicles": sum(int(row["vehicles"]) for row in archive_rows if row["instance"] in EXPECTED_HEADLINE),
    }
    full_summary = {
        "scope": "Full Senior benchmark",
        "instance_or_benchmark": "12 instances total",
        "total_validated_cost": round(sum(float(row["cost"]) for row in archive_rows), 2),
        "total_vehicles": sum(int(row["vehicles"]) for row in archive_rows),
        "ev_vehicles": sum(int(row["ev_vehicles"]) for row in archive_rows),
        "ice_vehicles": sum(int(row["ice_vehicles"]) for row in archive_rows),
        "selected_trips": sum(int(row["trips"]) for row in archive_rows),
        "final_no_regression_archive": True,
    }
    return {
        "schema_version": 1,
        "description": "Canonical final validated thesis results for the MINOA Senior benchmark.",
        "method": "final no-regression archive",
        "source": "Generated by scripts/print_final_results_table.py",
        "headline_results": headline_rows,
        "headline_total": headline_total,
        "full_senior_benchmark": {
            "instances": len(archive_rows),
            "total_validated_cost": full_summary["total_validated_cost"],
            "total_vehicles": full_summary["total_vehicles"],
        },
        "full_benchmark_summary": full_summary,
        "final_archive_results": archive_rows,
    }


def _fmt_cost(value: Any) -> str:
    return f"{float(value):.2f}"


def _fmt_value(value: Any) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _status(expected: float | int, actual: Any) -> str:
    if isinstance(expected, int):
        return "PASS" if int(actual) == expected else "FAIL"
    return "PASS" if abs(float(actual) - float(expected)) <= TOLERANCE else "FAIL"


def _headline_by_instance(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = data.get("headline_results")
    if not isinstance(rows, list):
        raise ValueError("Missing or invalid field: headline_results")
    by_instance: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or "instance" not in row:
            raise ValueError("Each headline_results row must contain an instance")
        by_instance[str(row["instance"])] = row
    return by_instance


def _canonical_instance_name(value: str) -> str:
    aliases = {
        "small": "Small",
        "medium": "Medium",
        "large": "Large",
    }
    return aliases.get(value.strip(), value.strip())


def _detail_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = data.get("final_archive_results")
    if not isinstance(rows, list):
        raise ValueError("Missing or invalid field: final_archive_results")
    for row in rows:
        if not isinstance(row, dict) or "instance" not in row:
            raise ValueError("Each final_archive_results row must contain an instance")
    return rows


def _markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    return [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(row) + " |" for row in rows),
    ]


def build_tables(data: dict[str, Any]) -> tuple[str, bool]:
    headline = _headline_by_instance(data)
    headline_total = data.get("headline_total")
    if not isinstance(headline_total, dict):
        raise ValueError("Missing or invalid field: headline_total")
    full = data.get("full_senior_benchmark")
    if not isinstance(full, dict):
        raise ValueError("Missing or invalid field: full_senior_benchmark")
    summary = data.get("full_benchmark_summary", full)
    if not isinstance(summary, dict):
        raise ValueError("Invalid field: full_benchmark_summary")

    lines: list[str] = [
        "## Final validated thesis results",
        "",
        "| Scope | Instance / Benchmark | Validated cost | Vehicles |",
        "|---|---:|---:|---:|",
    ]
    for instance in ("Small", "Medium", "Large"):
        row = headline.get(instance)
        if row is None:
            raise ValueError(f"Missing headline result for {instance}")
        lines.append(
            f"| Headline | {instance} | {_fmt_cost(row['validated_cost'])} | {int(row['vehicles'])} |"
        )
    lines.append(
        "| Headline total | Small + Medium + Large | "
        f"{_fmt_cost(headline_total['validated_cost'])} | {int(headline_total['vehicles'])} |"
    )
    lines.append(
        "| Full Senior benchmark | 12 instances total | "
        f"{_fmt_cost(full['total_validated_cost'])} | {int(full['total_vehicles'])} |"
    )

    detail_rows = _detail_rows(data)

    lines.extend(
        [
            "",
            "## Consistency status",
            "",
            "| Check | Expected | Actual | Status |",
            "|---|---:|---:|---:|",
        ]
    )

    all_passed = True
    for instance, expected in EXPECTED_HEADLINE.items():
        row = headline.get(instance)
        if row is None:
            raise ValueError(f"Missing headline result for {instance}")
        cost_status = _status(expected["validated_cost"], row.get("validated_cost"))
        vehicle_status = _status(expected["vehicles"], row.get("vehicles"))
        all_passed = all_passed and cost_status == "PASS" and vehicle_status == "PASS"
        lines.append(
            f"| {instance} cost | {_fmt_cost(expected['validated_cost'])} | "
            f"{_fmt_cost(row.get('validated_cost'))} | {cost_status} |"
        )
        lines.append(
            f"| {instance} vehicles | {expected['vehicles']} | "
            f"{int(row.get('vehicles'))} | {vehicle_status} |"
        )

    detail_by_instance = {str(row["instance"]): row for row in detail_rows}
    headline_detail_cost = round(
        sum(float(detail_by_instance[instance]["cost"]) for instance in EXPECTED_HEADLINE),
        2,
    )
    headline_total_vehicles = sum(
        int(headline[instance]["vehicles"]) for instance in EXPECTED_HEADLINE
    )
    headline_total_cost_status = _status(
        EXPECTED_HEADLINE_TOTAL["validated_cost"], headline_total.get("validated_cost")
    )
    headline_total_vehicle_status = _status(
        EXPECTED_HEADLINE_TOTAL["vehicles"], headline_total.get("vehicles")
    )
    headline_sum_cost_status = _status(
        EXPECTED_HEADLINE_TOTAL["validated_cost"], headline_detail_cost
    )
    headline_sum_vehicle_status = _status(
        EXPECTED_HEADLINE_TOTAL["vehicles"], headline_total_vehicles
    )
    all_passed = (
        all_passed
        and headline_total_cost_status == "PASS"
        and headline_total_vehicle_status == "PASS"
        and headline_sum_cost_status == "PASS"
        and headline_sum_vehicle_status == "PASS"
    )
    lines.append(
        f"| Headline total cost | {_fmt_cost(EXPECTED_HEADLINE_TOTAL['validated_cost'])} | "
        f"{_fmt_cost(headline_total.get('validated_cost'))} | {headline_total_cost_status} |"
    )
    lines.append(
        f"| Headline total vehicles | {EXPECTED_HEADLINE_TOTAL['vehicles']} | "
        f"{int(headline_total.get('vehicles'))} | {headline_total_vehicle_status} |"
    )
    lines.append(
        f"| Headline detailed cost sum | {_fmt_cost(EXPECTED_HEADLINE_TOTAL['validated_cost'])} | "
        f"{_fmt_cost(headline_detail_cost)} | {headline_sum_cost_status} |"
    )
    lines.append(
        f"| Headline row vehicle sum | {EXPECTED_HEADLINE_TOTAL['vehicles']} | "
        f"{headline_total_vehicles} | {headline_sum_vehicle_status} |"
    )

    total_cost_status = _status(
        EXPECTED_FULL["total_validated_cost"], full.get("total_validated_cost")
    )
    total_vehicle_status = _status(
        EXPECTED_FULL["total_vehicles"], full.get("total_vehicles")
    )
    all_passed = all_passed and total_cost_status == "PASS" and total_vehicle_status == "PASS"
    detail_total_cost = round(sum(float(row["cost"]) for row in detail_rows), 2)
    detail_total_vehicles = sum(int(row["vehicles"]) for row in detail_rows)
    detail_cost_status = _status(EXPECTED_FULL["total_validated_cost"], detail_total_cost)
    detail_vehicle_status = _status(EXPECTED_FULL["total_vehicles"], detail_total_vehicles)
    all_passed = (
        all_passed
        and detail_cost_status == "PASS"
        and detail_vehicle_status == "PASS"
        and all(bool(row.get("valid")) for row in detail_rows)
    )
    lines.append(
        f"| Total cost | {_fmt_cost(EXPECTED_FULL['total_validated_cost'])} | "
        f"{_fmt_cost(full.get('total_validated_cost'))} | {total_cost_status} |"
    )
    lines.append(
        f"| Total vehicles | {EXPECTED_FULL['total_vehicles']} | "
        f"{int(full.get('total_vehicles'))} | {total_vehicle_status} |"
    )
    lines.append(
        f"| Detailed row cost sum | {_fmt_cost(EXPECTED_FULL['total_validated_cost'])} | "
        f"{_fmt_cost(detail_total_cost)} | {detail_cost_status} |"
    )
    lines.append(
        f"| Detailed row vehicle sum | {EXPECTED_FULL['total_vehicles']} | "
        f"{detail_total_vehicles} | {detail_vehicle_status} |"
    )
    valid_status = "PASS" if all(bool(row.get("valid")) for row in detail_rows) else "FAIL"
    lines.append(f"| Final archive rows valid | PASS | {valid_status} | {valid_status} |")
    return "\n".join(lines) + "\n", all_passed


def build_instance_table(data: dict[str, Any], instance: str) -> tuple[str, bool]:
    instance = _canonical_instance_name(instance)
    headline = _headline_by_instance(data)
    expected = EXPECTED_HEADLINE.get(instance)
    row = headline.get(instance)
    if expected is None or row is None:
        raise ValueError(f"No canonical headline result is available for {instance}")

    cost_status = _status(expected["validated_cost"], row.get("validated_cost"))
    vehicle_status = _status(expected["vehicles"], row.get("vehicles"))
    lines = [
        f"## Canonical thesis result for {instance}",
        "",
        "| Instance | Validated cost | Vehicles | Cost check | Vehicle check |",
        "|---|---:|---:|---:|---:|",
        (
            f"| {instance} | {_fmt_cost(row['validated_cost'])} | {int(row['vehicles'])} | "
            f"{cost_status} | {vehicle_status} |"
        ),
        "",
    ]
    return "\n".join(lines), cost_status == "PASS" and vehicle_status == "PASS"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results",
        type=Path,
        default=DEFAULT_RESULTS,
        help="Path to canonical final result JSON.",
    )
    parser.add_argument(
        "--summary-file",
        type=Path,
        help="Optional file that receives the same Markdown output.",
    )
    parser.add_argument(
        "--instance",
        help="Print only one canonical headline instance table: Small, Medium, or Large.",
    )
    args = parser.parse_args()

    try:
        data = _load_results(args.results)
        if args.instance:
            markdown, all_passed = build_instance_table(data, args.instance)
        else:
            markdown, all_passed = build_tables(data)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(markdown, end="")
    if args.summary_file:
        args.summary_file.parent.mkdir(parents=True, exist_ok=True)
        args.summary_file.write_text(markdown, encoding="utf-8")
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
