#!/usr/bin/env python3
"""Compute global and selected-timetable lower-bound reports for MINOA runs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from minoa_lib.experiments.metrics import block_metrics, instance_name
from minoa_lib.experiments.metrics import parse_vs_cost
from minoa_lib.lower_bounds import (
    count_candidate_trips,
    global_timetable_overlap_lower_bound,
    selected_timetable_fixed_cost_lower_bound,
)
from minoa_lib.reporting import update_report_sol
from minoa_lib.validation import validate


HEADLINE_INPUTS = {
    "Small": Path("data/raw/minoa/senior/Small_Input_S.json"),
    "Medium": Path("data/raw/minoa/senior/Medium_Input_S.json"),
    "Large": Path("data/raw/minoa/senior/Large_Input_S.json"),
}

CSV_COLUMNS = [
    "instance",
    "validated_upper_bound",
    "global_vehicle_lb",
    "global_cost_lb",
    "global_gap_percent",
    "global_lb_status",
    "global_lb_runtime_seconds",
    "global_lb_dual_bound",
    "global_lb_incumbent",
    "global_lb_solver_gap",
    "selected_tt_overlap_vehicle_lb",
    "selected_tt_path_cover_vehicle_lb",
    "selected_tt_vehicle_lb",
    "selected_tt_cost_lb",
    "selected_tt_gap_percent",
    "used_vehicles",
    "selected_trips",
    "candidate_trips",
    "compatibility_edges",
    "solver",
    "time_limit_seconds",
    "globally_valid",
    "input",
    "output",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compute certified global lower bounds and selected-timetable diagnostic bounds."
    )
    parser.add_argument("--scope", choices=["sml", "all"], default="sml")
    parser.add_argument("--input-dir", type=Path, default=Path("data/raw/minoa/senior"))
    parser.add_argument("--solution-dir", type=Path)
    parser.add_argument(
        "--archive-csv",
        type=Path,
        help="Use archived_output paths from a final archive CSV instead of filename matching.",
    )
    parser.add_argument("--output-csv", type=Path, default=Path("results/lower_bounds/all_instances_lower_bounds.csv"))
    parser.add_argument("--time-limit", type=float, default=60.0)
    parser.add_argument(
        "--validator",
        type=Path,
        default=Path("tools/minoa/desktopValidator/desktopValidator/desktopValidator.jar"),
    )
    parser.add_argument(
        "--write-output-lower-bound",
        action="store_true",
        help="Write the certified global lower bound into reportSol.lowerBound of each output JSON.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    pairs = input_output_pairs(args)
    rows = []
    for input_path, output_path in pairs:
        row = evaluate_pair(input_path, output_path, args.time_limit, args.validator)
        rows.append(row)
        if args.write_output_lower_bound and output_path is not None and row["globally_valid"]:
            update_report_sol(
                output_path,
                global_lower_bound=float(row["global_cost_lb"] or 0.0),
            )
        print(render_one_line(row), flush=True)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved lower-bound CSV: {args.output_csv}")


def input_output_pairs(args: argparse.Namespace) -> list[tuple[Path, Path | None]]:
    if args.archive_csv:
        return archive_input_output_pairs(args)
    if args.scope == "sml":
        solution_dir = args.solution_dir or Path("outputs/minoa/sml_multistart")
        pairs = []
        for name, input_path in HEADLINE_INPUTS.items():
            output_path = solution_dir / f"{name}_Output_multistart.json"
            if not output_path.exists():
                output_path = find_output_for_instance(solution_dir, name)
            pairs.append((input_path, output_path))
        return pairs

    solution_dir = args.solution_dir or Path("outputs/minoa/all_multistart")
    pairs = []
    for input_path in sorted(args.input_dir.glob("*.json")):
        if "Output" in input_path.name or "output" in input_path.name:
            continue
        pairs.append((input_path, final_output_for_input(solution_dir, input_path)))
    return pairs


def archive_input_output_pairs(args: argparse.Namespace) -> list[tuple[Path, Path | None]]:
    archive: dict[str, Path] = {}
    missing_outputs: list[str] = []
    if not args.archive_csv.exists():
        raise SystemExit(
            "Missing archive CSV: "
            f"{args.archive_csv}\n\n"
            "Generate it first with:\n"
            "  .venv/bin/python scripts/run_experiment.py --algorithm multistart --scope all\n\n"
            "That command writes the final archive CSV under outputs/minoa/final_archive/."
        )
    with args.archive_csv.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            instance = row["instance"]
            raw_output = (row.get("archived_output") or "").strip()
            if not raw_output:
                missing_outputs.append(f"{instance}: archived_output is empty")
                continue
            output_path = Path(raw_output)
            if not output_path.exists():
                missing_outputs.append(f"{instance}: {output_path}")
                continue
            archive[normalize_name(instance)] = output_path
    if missing_outputs:
        formatted = "\n".join(f"  - {item}" for item in missing_outputs)
        raise SystemExit(
            "The archive CSV exists, but the output JSON schedules needed for "
            "selected-timetable lower bounds are missing:\n"
            f"{formatted}\n\n"
            "Regenerate the schedules and archive with:\n"
            "  .venv/bin/python scripts/run_experiment.py --algorithm multistart --scope all"
        )

    if args.scope == "sml":
        input_paths = HEADLINE_INPUTS.values()
    else:
        input_paths = [
            path
            for path in sorted(args.input_dir.glob("*.json"))
            if "Output" not in path.name and "output" not in path.name
        ]

    pairs = []
    for input_path in input_paths:
        pairs.append((input_path, archive.get(normalize_name(instance_name(input_path)))))
    return pairs


def find_output_for_instance(solution_dir: Path, instance: str) -> Path | None:
    if not solution_dir.exists():
        return None
    candidates = []
    target = normalize_name(instance)
    for path in solution_dir.glob("*Output*.json"):
        if "_opt_" in path.stem or "_repair_" in path.stem:
            continue
        if target in normalize_name(path.stem):
            candidates.append(path)
    return sorted(candidates)[0] if candidates else None


def final_output_for_input(solution_dir: Path, input_path: Path) -> Path | None:
    safe = validator_safe_stem(input_path)
    repairs = sorted(solution_dir.glob(f"{safe}_Output_pipeline_repair_*.json"))
    if repairs:
        return repairs[0]
    primary = solution_dir / f"{safe}_Output_pipeline.json"
    if primary.exists():
        return primary
    return None


def validator_safe_stem(path: Path) -> str:
    return (
        path.stem.replace("Input", "Instance")
        .replace("input", "Instance")
        .replace("INPUT", "INSTANCE")
    )


def evaluate_pair(input_path: Path, output_path: Path | None, time_limit: float, validator_path: Path) -> dict[str, Any]:
    data = read_minoa_json(input_path)
    output = read_minoa_json(output_path) if output_path and output_path.exists() else None

    global_lb = global_timetable_overlap_lower_bound(data, time_limit_seconds=time_limit)
    selected_lb = selected_timetable_fixed_cost_lower_bound(data, output) if output else None
    metrics = block_metrics(output) if output else {}
    ub = upper_bound(input_path, output_path, output, validator_path) if output else None

    global_gap = 100.0 * (ub - global_lb.fixed_cost_lb) / ub if ub else None
    selected_gap = selected_lb.gap_ub_percent(ub) if selected_lb and ub else None

    return {
        "instance": instance_name(input_path),
        "validated_upper_bound": round_or_blank(ub),
        "global_vehicle_lb": global_lb.vehicle_count_lb,
        "global_cost_lb": global_lb.fixed_cost_lb,
        "global_gap_percent": round_or_blank(global_gap),
        "global_lb_status": global_lb.status,
        "global_lb_runtime_seconds": round(global_lb.runtime_seconds, 6),
        "global_lb_dual_bound": round_or_blank(global_lb.dual_bound),
        "global_lb_incumbent": round_or_blank(global_lb.incumbent),
        "global_lb_solver_gap": round_or_blank(global_lb.solver_gap),
        "selected_tt_overlap_vehicle_lb": selected_lb.overlap_vehicle_lb if selected_lb else "",
        "selected_tt_path_cover_vehicle_lb": selected_lb.path_cover_vehicle_lb if selected_lb else "",
        "selected_tt_vehicle_lb": selected_lb.vehicle_count_lb if selected_lb else "",
        "selected_tt_cost_lb": selected_lb.fixed_cost_lb if selected_lb else "",
        "selected_tt_gap_percent": round_or_blank(selected_gap),
        "used_vehicles": metrics.get("total_blocks", ""),
        "selected_trips": metrics.get("selected_trips", ""),
        "candidate_trips": count_candidate_trips(data),
        "compatibility_edges": global_lb.timetable_arcs,
        "solver": global_lb.solver,
        "time_limit_seconds": time_limit,
        "globally_valid": global_lb.globally_valid,
        "input": str(input_path),
        "output": str(output_path or ""),
    }


def read_minoa_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    text = path.read_text()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = json.loads(text.rstrip() + "\n}\n")
    normalize_minoa_data(data)
    return data


def upper_bound(input_path: Path, output_path: Path | None, output: dict[str, Any], validator_path: Path) -> float | None:
    raw = output.get("reportSol", {}).get("upperBound")
    if raw is not None:
        return float(raw)
    if output_path is None or not output_path.exists() or not validator_path.exists():
        return None
    result = validate(validator_path, normalized_validator_input(input_path), output_path)
    return parse_vs_cost(result.stdout)


def normalized_validator_input(input_path: Path) -> Path:
    data = read_minoa_json(input_path)
    out_dir = Path("results/lower_bounds/processed_inputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / input_path.name
    out_path.write_text(json.dumps(data, indent=2))
    return out_path


def normalize_minoa_data(data: dict[str, Any]) -> None:
    for wrap in data.get("nodes", []):
        node = wrap.get("node", {})
        if "stoppingTimes" in node and "breakingTimes" not in node:
            node["breakingTimes"] = node.pop("stoppingTimes")
    for wrap in data.get("fleet", {}).get("vehicleList", []):
        vehicle = wrap.get("vehicleType", {})
        if "pulliInOutCost" in vehicle and "pullInOutCost" not in vehicle:
            vehicle["pullInOutCost"] = vehicle.pop("pulliInOutCost")


def normalize_name(text: str) -> str:
    return "".join(ch.lower() for ch in text if ch.isalnum())


def round_or_blank(value: float | None) -> float | str:
    if value is None:
        return ""
    return round(float(value), 6)


def render_one_line(row: dict[str, Any]) -> str:
    return (
        f"{row['instance']}: UB={row['validated_upper_bound']} "
        f"globalLB={row['global_cost_lb']} ({row['global_lb_status']}), "
        f"selectedTTLB={row['selected_tt_cost_lb']}"
    )


if __name__ == "__main__":
    main()
