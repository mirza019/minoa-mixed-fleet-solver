#!/usr/bin/env python3
"""Print and validate the canonical final MINOA thesis result table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


DEFAULT_RESULTS = Path("results/final_validated_results.json")

EXPECTED_HEADLINE = {
    "Small": {"validated_cost": 162.44, "vehicles": 2},
    "Medium": {"validated_cost": 371.35, "vehicles": 5},
    "Large": {"validated_cost": 1163.35, "vehicles": 15},
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


def _load_results(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing canonical result file: {path}")
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


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
    summary = data.get("full_benchmark_summary")
    if not isinstance(summary, dict):
        raise ValueError("Missing or invalid field: full_benchmark_summary")

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
        "| Full Senior benchmark | 12 instances total | "
        f"{_fmt_cost(summary['total_validated_cost'])} | {int(summary['total_vehicles'])} |"
    )

    detail_rows = _detail_rows(data)
    lines.extend(
        [
            "",
            "## Final no-regression archive table",
            "",
            "This is the canonical table used for the thesis result summary.",
            "",
        ]
    )
    detail_headers = [header for header, _ in DETAIL_COLUMNS]
    detail_values = [
        [_fmt_value(row.get(key)) for _, key in DETAIL_COLUMNS]
        for row in detail_rows
    ]
    lines.extend(_markdown_table(detail_headers, detail_values))
    lines.extend(
        [
            "",
            "## Final archive totals",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| Feasible instances | {sum(1 for row in detail_rows if row.get('valid'))} / {len(detail_rows)} |",
            f"| Total validated cost | {_fmt_cost(summary['total_validated_cost'])} |",
            f"| Total vehicles | {int(summary['total_vehicles'])} |",
            f"| EV vehicles | {int(summary.get('ev_vehicles', 0))} |",
            f"| ICE vehicles | {int(summary.get('ice_vehicles', 0))} |",
            f"| Selected trips | {int(summary.get('selected_trips', 0))} |",
        ]
    )

    lines.extend(
        [
            "",
            "## Consistency check",
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

    total_cost_status = _status(
        EXPECTED_FULL["total_validated_cost"], summary.get("total_validated_cost")
    )
    total_vehicle_status = _status(
        EXPECTED_FULL["total_vehicles"], summary.get("total_vehicles")
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
        f"{_fmt_cost(summary.get('total_validated_cost'))} | {total_cost_status} |"
    )
    lines.append(
        f"| Total vehicles | {EXPECTED_FULL['total_vehicles']} | "
        f"{int(summary.get('total_vehicles'))} | {total_vehicle_status} |"
    )
    lines.append(
        f"| Detailed row cost sum | {_fmt_cost(EXPECTED_FULL['total_validated_cost'])} | "
        f"{_fmt_cost(detail_total_cost)} | {detail_cost_status} |"
    )
    lines.append(
        f"| Detailed row vehicle sum | {EXPECTED_FULL['total_vehicles']} | "
        f"{detail_total_vehicles} | {detail_vehicle_status} |"
    )
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
