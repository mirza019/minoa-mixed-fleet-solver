#!/usr/bin/env python3
"""Run MINOA experiments with one command and an algorithm name.

Examples:

    .venv/bin/python scripts/run_experiment.py --algorithm greedy
    .venv/bin/python scripts/run_experiment.py --algorithm multistart --scope sml
    .venv/bin/python scripts/run_experiment.py --algorithm weighted --scope all
    .venv/bin/python scripts/print_final_results_table.py
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

HEADLINE_INPUTS = {
    "Small": Path("data/raw/minoa/senior/Small_Input_S.json"),
    "Medium": Path("data/raw/minoa/senior/Medium_Input_S.json"),
    "Large": Path("data/raw/minoa/senior/Large_Input_S.json"),
}

MULTISTART_SETTINGS = {
    "Small": {"variants": 8, "iterations": 64, "seed": 19, "time_limit": 240},
    "Medium": {"variants": 8, "iterations": 48, "seed": 103, "time_limit": 420},
    "Large": {"variants": 8, "iterations": 24, "seed": 23, "time_limit": 900},
}

ALGORITHMS = {
    "greedy": {"builder": "greedy", "ev_mode": "charging", "multistart": False},
    "pathcover": {"builder": "pathcover", "ev_mode": "charging", "multistart": False},
    "weighted": {"builder": "pathcover-cost", "ev_mode": "charging", "multistart": False},
    "multistart": {"builder": "pathcover-cost", "ev_mode": "charging", "multistart": True},
    "ice-greedy": {"builder": "greedy", "ev_mode": "none", "multistart": False},
    "no-charge": {"builder": "pathcover-cost", "ev_mode": "no-charge", "multistart": False},
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run MINOA experiments by choosing an algorithm name."
    )
    parser.add_argument(
        "--algorithm",
        choices=sorted(ALGORITHMS),
        default="multistart",
        help="Algorithm variant to run.",
    )
    parser.add_argument(
        "--scope",
        choices=["sml", "all"],
        default="sml",
        help="sml runs Small/Medium/Large. all runs every senior instance.",
    )
    parser.add_argument(
        "--only",
        choices=["Small", "Medium", "Large"],
        help="Run only one headline instance. Only valid with --scope sml.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Use a smaller search for multistart runs.",
    )
    parser.add_argument(
        "--fresh-audit",
        action="store_true",
        help="Deprecated compatibility flag. All --scope all runs now execute a fresh experiment.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/raw/minoa/senior"),
        help="Input directory for --scope all.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory. Defaults to outputs/minoa/<scope>_<algorithm>.",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        help="Processed working input directory for --scope all.",
    )
    parser.add_argument(
        "--validator",
        type=Path,
        default=Path("tools/minoa/desktopValidator/desktopValidator/desktopValidator.jar"),
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.only and args.scope != "sml":
        raise SystemExit("--only can only be used with --scope sml")

    if args.scope == "all":
        run_all(args)
    else:
        run_sml(args)


def run_sml(args: argparse.Namespace) -> None:
    algorithm = ALGORITHMS[args.algorithm]
    output_dir = args.output_dir or Path("outputs/minoa") / f"sml_{args.algorithm}"
    output_dir.mkdir(parents=True, exist_ok=True)
    selected = {args.only: HEADLINE_INPUTS[args.only]} if args.only else HEADLINE_INPUTS
    pairs: list[str] = []

    for instance, input_path in selected.items():
        output_path = output_dir / f"{instance}_Output_{args.algorithm}.json"
        log_path = output_dir / f"{instance}_{args.algorithm}.log"
        print(f"\n=== Running {instance} with {args.algorithm} ===", flush=True)
        if algorithm["multistart"]:
            command = multistart_command(input_path, output_path, instance, args, algorithm)
        else:
            command = single_run_command(input_path, output_path, args, algorithm)

        env = os.environ.copy()
        if algorithm["multistart"]:
            env["MINOA_DEPOT_BRIDGE_MIN_GAP"] = env.get("MINOA_DEPOT_BRIDGE_MIN_GAP", "999999")
        with log_path.open("w") as handle:
            proc = subprocess.run(command, cwd=ROOT, text=True, stdout=handle, stderr=subprocess.STDOUT, env=env)
        if proc.returncode != 0:
            raise SystemExit(f"{instance} failed. See {log_path}")
        if not output_path.exists():
            raise SystemExit(f"{instance} produced no output. See {log_path}")
        pairs.append(f"{input_path}:{output_path}")

    print("\n=== Validator result table ===", flush=True)
    run_report(pairs, args.validator)
    print(f"\nGenerated outputs and logs: {output_dir}")


def run_all(args: argparse.Namespace) -> None:
    if args.algorithm == "multistart":
        output_dir = args.output_dir or Path("outputs/minoa/all_multistart")
        processed_dir = args.processed_dir or Path("data/processed/minoa/all_multistart")
        command = [
            sys.executable,
            "scripts/run_all_experiments.py",
            "--input-dir",
            str(args.input_dir),
            "--processed-dir",
            str(processed_dir),
            "--output-dir",
            str(output_dir),
            "--validator",
            str(args.validator),
        ]
        if args.quick:
            command.append("--quick-headliners")
        else:
            command.append("--optimized-all")
        subprocess.run(command, cwd=ROOT, check=True)
        return

    algorithm = ALGORITHMS[args.algorithm]
    output_dir = args.output_dir or Path("outputs/minoa") / f"all_{args.algorithm}"
    processed_dir = args.processed_dir or Path("data/processed/minoa") / f"all_{args.algorithm}"
    command = [
        sys.executable,
        "scripts/minoa_pipeline.py",
        "--input-dir",
        str(args.input_dir),
        "--processed-dir",
        str(processed_dir),
        "--output-dir",
        str(output_dir),
        "--validator",
        str(args.validator),
        "--builder",
        str(algorithm["builder"]),
        "--ev-mode",
        str(algorithm["ev_mode"]),
        "--no-optimized-headliners",
    ]
    subprocess.run(command, cwd=ROOT, check=True)


def single_run_command(
    input_path: Path,
    output_path: Path,
    args: argparse.Namespace,
    algorithm: dict[str, object],
) -> list[str]:
    return [
        sys.executable,
        "scripts/minoa_solver.py",
        str(input_path),
        "--output",
        str(output_path),
        "--builder",
        str(algorithm["builder"]),
        "--ev-mode",
        str(algorithm["ev_mode"]),
        "--validator",
        str(args.validator),
    ]


def multistart_command(
    input_path: Path,
    output_path: Path,
    instance: str,
    args: argparse.Namespace,
    algorithm: dict[str, object],
) -> list[str]:
    settings = MULTISTART_SETTINGS[instance]
    variants = 4 if args.quick else settings["variants"]
    iterations = 4 if args.quick else settings["iterations"]
    time_limit = 120 if args.quick else settings["time_limit"]
    return [
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
        str(settings["seed"]),
        "--builder",
        str(algorithm["builder"]),
        "--ev-mode",
        str(algorithm["ev_mode"]),
        "--time-limit",
        str(time_limit),
        "--validator",
        str(args.validator),
    ]


def run_report(pairs: list[str], validator: Path) -> None:
    command = [
        sys.executable,
        "scripts/minoa_report.py",
        *pairs,
        "--validator",
        str(validator),
    ]
    subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
