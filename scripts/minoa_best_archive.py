#!/usr/bin/env python3
"""Build a no-regression archive of the best validated MINOA outputs.

The script evaluates candidate JSON outputs with the official validator and
copies the best accepted solution for each input instance into a stable archive.
It is intentionally separate from the solver: it does not generate new
solutions, it only protects and reports the best validator-confirmed files.
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
from pathlib import Path

from minoa_lib.experiments.metrics import evaluate_solution
from minoa_lib.experiments.table import markdown_table


INSTANCE_ORDER = [
    "Small",
    "Medium",
    "Large",
    "Toy Example",
    "1line",
    "1line 6timeWindow",
    "2lines",
    "2lines 6 timeWindows",
    "3lines",
    "3linesTriangle",
    "5lines",
    "8lines",
]


CSV_COLUMNS = [
    "instance",
    "approach",
    "valid",
    "objective",
    "fixed_cost",
    "break_cost",
    "pull_cost",
    "co2_cost",
    "official_residual",
    "global_lower_bound",
    "global_bound_gap_ub",
    "selected_tt_lower_bound",
    "selected_tt_bound_gap_ub",
    "total_blocks",
    "ev_blocks",
    "ice_blocks",
    "ev_share",
    "selected_trips",
    "deadhead_min",
    "break_min",
    "charging_min",
    "source_output",
    "archived_output",
]


def normalized_name(path_or_name: str) -> str:
    name = Path(path_or_name).name
    name = re.sub(r"_Instance_S_Output_pipeline_opt_\d+\.json$", "_Instance_S_Output_pipeline.json", name)
    name = re.sub(r"_Instance_S_Output_pipeline_opt_\d+_\d+\.json$", "_Instance_S_Output_pipeline.json", name)
    name = re.sub(r"_Output_pipeline_opt_\d+\.json$", "_Output_pipeline.json", name)
    name = re.sub(r"_Output_pipeline_opt_\d+_\d+\.json$", "_Output_pipeline.json", name)
    name = re.sub(r"_Output_multistart_opt_\d+\.json$", "_Output_multistart.json", name)
    for suffix in (
        "_Input_S.json",
        "_input_S.json",
        "_Instance_S_Output_pipeline_repair_node2.json",
        "_Instance_S_Output_pipeline.json",
        "_Output_multistart.json",
        "_Output_multi_start_pathcover.json",
        "_Output_experiment.json",
        ".json",
    ):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    name = name.replace("_", " ").strip()
    aliases = {
        "8lines": "8lines",
        "Toy Example": "Toy Example",
    }
    return aliases.get(name, name)


def input_map(input_dir: Path) -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    for path in sorted(input_dir.glob("*.json")):
        if "Output" in path.name:
            continue
        mapping[normalized_name(path.name)] = path
    return mapping


def instance_sort_key(row: dict[str, object]) -> tuple[int, str]:
    instance = str(row["instance"]).strip()
    try:
        return (INSTANCE_ORDER.index(instance), instance)
    except ValueError:
        return (len(INSTANCE_ORDER), instance)


def candidate_key(row: dict[str, object]) -> tuple[float, int, int, float, float, float, float]:
    objective = float(row["objective"])
    return (
        objective,
        int(row["total_blocks"]),
        -int(row["ev_blocks"]),
        float(row["pull_cost"]),
        float(row["break_cost"]),
        float(row["co2_cost"]),
        abs(float(row["official_residual"] or 0.0)),
    )


def evaluate_candidates(input_dir: Path, candidate_dirs: list[Path], validator: Path) -> list[dict[str, object]]:
    inputs = input_map(input_dir)
    rows: list[dict[str, object]] = []
    for candidate_dir in candidate_dirs:
        if not candidate_dir.exists():
            continue
        for output_path in sorted(candidate_dir.glob("*.json")):
            if "Output" not in output_path.name:
                continue
            instance = normalized_name(output_path.name)
            input_path = inputs.get(instance)
            if input_path is None:
                continue
            row = evaluate_solution(input_path, output_path, validator)
            row["instance"] = instance
            row["source_output"] = str(output_path)
            rows.append(row)
    return rows


def choose_best(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    best: dict[str, dict[str, object]] = {}
    for row in rows:
        if not row.get("valid") or row.get("objective") is None:
            continue
        instance = str(row["instance"]).strip()
        previous = best.get(instance)
        if previous is None or candidate_key(row) < candidate_key(previous):
            best[instance] = row
    return sorted(best.values(), key=instance_sort_key)


def write_csv(rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in CSV_COLUMNS})


def archive_rows(rows: list[dict[str, object]], output_dir: Path) -> list[dict[str, object]]:
    solution_dir = output_dir / "solutions"
    solution_dir.mkdir(parents=True, exist_ok=True)
    archived: list[dict[str, object]] = []
    for row in rows:
        source = Path(str(row["source_output"]))
        target_name = source.name
        target = solution_dir / target_name
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)
        copied = dict(row)
        copied["archived_output"] = str(target)
        archived.append(copied)
    return archived


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a best validated MINOA solution archive.")
    parser.add_argument("--input-dir", type=Path, default=Path("data/raw/minoa/senior"))
    parser.add_argument("--candidate-dir", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/minoa/final_archive"))
    parser.add_argument(
        "--validator",
        type=Path,
        default=Path("tools/minoa/desktopValidator/desktopValidator/desktopValidator.jar"),
    )
    args = parser.parse_args()

    evaluated = evaluate_candidates(args.input_dir, args.candidate_dir, args.validator)
    best = choose_best(evaluated)
    archived = archive_rows(best, args.output_dir)

    write_csv(evaluated, args.output_dir / "candidate_evaluation.csv")
    write_csv(archived, args.output_dir / "final_results.csv")
    (args.output_dir / "final_results_report.md").write_text(markdown_table(archived) + "\n", encoding="utf-8")

    print(f"Evaluated candidates: {len(evaluated)}")
    print(f"Archived best valid instances: {len(archived)}")
    print(args.output_dir / "final_results.csv")
    print(args.output_dir / "final_results_report.md")


if __name__ == "__main__":
    main()
