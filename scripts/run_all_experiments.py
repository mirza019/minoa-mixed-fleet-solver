#!/usr/bin/env python3
"""Run every available MINOA senior instance and print validator table.

Recommended command:

    .venv/bin/python scripts/run_all_experiments.py

The script creates processed working copies when needed, leaves raw data and
the provided validator untouched, solves each instance, validates the
outputs, and prints one Markdown result table plus totals.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run all MINOA senior instances through the solver, validator, and table reporter."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/raw/minoa/senior"),
        help="Directory containing raw senior input JSON files.",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("data/processed/minoa/all_instances"),
        help="Directory for normalized working copies. Raw files are not modified.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/minoa/all_instances"),
        help="Directory for generated output JSON files, report table, and manifest.",
    )
    parser.add_argument(
        "--validator",
        type=Path,
        default=Path("tools/minoa/desktopValidator/desktopValidator/desktopValidator.jar"),
    )
    parser.add_argument(
        "--quick-headliners",
        action="store_true",
        help=(
            "Skip deeper local search for Small/Medium/Large. "
            "Faster, but the headline rows may not reproduce the best 2/5/15 vehicle counts."
        ),
    )
    parser.add_argument(
        "--optimized-all",
        action="store_true",
        help="Run adaptive multi-start path-cover search on every Senior instance.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "scripts/minoa_pipeline.py",
        "--input-dir",
        str(args.input_dir),
        "--processed-dir",
        str(args.processed_dir),
        "--output-dir",
        str(args.output_dir),
        "--validator",
        str(args.validator),
    ]
    if args.quick_headliners:
        command.append("--no-optimized-headliners")
    if args.optimized_all:
        command.append("--optimized-all")
    else:
        command.append("--optimized-headliners")

    print("=== Running all MINOA senior instances ===", flush=True)
    report_path = args.output_dir / "all_instances_report.md"
    with report_path.open("w") as handle:
        proc = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(proc.stdout)
        handle.write(proc.stdout)

    if proc.returncode != 0:
        raise SystemExit(f"All-instance pipeline failed. See {report_path}")
    if "| no " in proc.stdout or "| no   " in proc.stdout:
        raise SystemExit(f"At least one instance failed validation. See {report_path}")

    print(f"Report saved to: {report_path}")
    print(f"Generated outputs: {args.output_dir}")
    print(f"Processed working inputs: {args.processed_dir}")


if __name__ == "__main__":
    main()
