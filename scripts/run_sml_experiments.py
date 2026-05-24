#!/usr/bin/env python3
"""Run MINOA Small/Medium/Large experiments and print validator table.

Professor-friendly command:

    .venv/bin/python scripts/run_sml_experiments.py

The script runs the solver, writes output JSON files, passes each input/output
pair to the official desktop validator, and prints one Markdown result table.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


HEADLINE_RUNS = {
    "Small": {
        "input": Path("data/raw/minoa/senior/Small_Input_S.json"),
        "output": Path("outputs/minoa/professor/Small_Output_multi_start_pathcover.json"),
        "variants": 8,
        "iterations": 64,
        "seed": 19,
        "time_limit": 240,
    },
    "Medium": {
        "input": Path("data/raw/minoa/senior/Medium_Input_S.json"),
        "output": Path("outputs/minoa/professor/Medium_Output_multi_start_pathcover.json"),
        "variants": 8,
        "iterations": 48,
        "seed": 103,
        "time_limit": 420,
    },
    "Large": {
        "input": Path("data/raw/minoa/senior/Large_Input_S.json"),
        "output": Path("outputs/minoa/professor/Large_Output_multi_start_pathcover.json"),
        "variants": 8,
        "iterations": 24,
        "seed": 23,
        "time_limit": 900,
    },
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Small, Medium, and Large MINOA experiments, validate them, and print a table."
    )
    parser.add_argument(
        "--only",
        choices=["Small", "Medium", "Large"],
        help="Run only one headline instance.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/minoa/professor"),
        help="Directory where generated output JSON files and logs are written.",
    )
    parser.add_argument(
        "--validator",
        type=Path,
        default=Path("tools/minoa/desktopValidator/desktopValidator/desktopValidator.jar"),
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Use a smaller search. Faster, but may produce weaker costs.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    selected = {args.only: HEADLINE_RUNS[args.only]} if args.only else HEADLINE_RUNS
    pairs: list[str] = []

    for instance, config in selected.items():
        input_path = config["input"]
        output_path = output_dir / config["output"].name
        log_path = output_dir / f"{instance}_search.log"
        variants = 4 if args.quick else config["variants"]
        iterations = 4 if args.quick else config["iterations"]
        time_limit = 120 if args.quick else config["time_limit"]

        print(f"\n=== Running {instance} experiment ===", flush=True)
        command = [
            sys.executable,
            "scripts/minoa_optimize.py",
            str(input_path),
            "--output",
            str(output_path),
            "--variants",
            str(variants),
            "--per-direction",
            "--local-iterations",
            str(iterations),
            "--seed",
            str(config["seed"]),
            "--builder",
            "pathcover-cost",
            "--ev-mode",
            "charging",
            "--time-limit",
            str(time_limit),
            "--validator",
            str(args.validator),
        ]
        env = os.environ.copy()
        env["MINOA_DEPOT_BRIDGE_MIN_GAP"] = env.get("MINOA_DEPOT_BRIDGE_MIN_GAP", "999999")
        with log_path.open("w") as handle:
            proc = subprocess.run(command, cwd=ROOT, text=True, stdout=handle, stderr=subprocess.STDOUT, env=env)
        if proc.returncode != 0:
            raise SystemExit(f"{instance} experiment failed. See {log_path}")
        if not output_path.exists():
            raise SystemExit(f"{instance} produced no valid output. See {log_path}")
        pairs.append(f"{input_path}:{output_path}")

    print("\n=== Official validator result table ===")
    report_command = [
        sys.executable,
        "scripts/minoa_report.py",
        *pairs,
        "--validator",
        str(args.validator),
    ]
    subprocess.run(report_command, cwd=ROOT, check=True)

    print(f"\nGenerated outputs and logs: {output_dir}")


if __name__ == "__main__":
    main()
