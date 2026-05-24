from __future__ import annotations

import argparse
import json
from pathlib import Path

from .solver import solve
from .validation import validate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--validator",
        type=Path,
        default=Path("tools/minoa/desktopValidator/desktopValidator/desktopValidator.jar"),
    )
    parser.add_argument("--no-validate", action="store_true")
    parser.add_argument(
        "--builder",
        choices=["greedy", "pathcover", "pathcover-cost"],
        default="greedy",
        help=(
            "Vehicle block builder. greedy is capacity-safe baseline; "
            "pathcover minimizes blocks for fixed trips but may need capacity repair."
        ),
    )
    parser.add_argument(
        "--ev-mode",
        choices=["none", "no-charge", "charging"],
        default="charging",
        help="EV assignment mode. charging inserts validator-compatible charge windows during existing breaks.",
    )
    parser.add_argument(
        "--tt-variant",
        type=int,
        default=0,
        help="Timetable tie-breaking variant used for multi-start experiments.",
    )
    parser.add_argument(
        "--tt-variants",
        help="Comma-separated per-direction timetable variants, e.g. 1,0,5,2.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    output_path = args.output or Path("outputs/minoa") / args.input.name.replace("Input", "Output")
    if "output" not in output_path.name.lower():
        output_path = output_path.with_name(output_path.stem + "_output" + output_path.suffix)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tt_variants = None
    if args.tt_variants:
        tt_variants = [int(part) for part in args.tt_variants.split(",") if part.strip()]

    output, stats = solve(
        args.input,
        builder=args.builder,
        ev_mode=args.ev_mode,
        tt_variant=args.tt_variant,
        tt_variants=tt_variants,
    )
    output_path.write_text(json.dumps(output, indent=2))
    print(json.dumps({"output": str(output_path), **stats}, indent=2))

    if not args.no_validate:
        result = validate(args.validator, args.input, output_path)
        print(result.stdout)
        raise SystemExit(result.returncode)
