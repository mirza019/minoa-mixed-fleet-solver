#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import itertools
import random
import shutil
import time
from pathlib import Path

from minoa_lib.experiments.metrics import parse_vs_cost
from minoa_lib.solver import solve
from minoa_lib.validation import validate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variants", type=int, default=24)
    parser.add_argument("--per-direction", action="store_true")
    parser.add_argument("--local-iterations", type=int, default=0)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--time-limit", type=float, default=0.0)
    parser.add_argument(
        "--builder",
        choices=["greedy", "pathcover", "pathcover-cost"],
        default="pathcover-cost",
    )
    parser.add_argument(
        "--ev-mode",
        choices=["none", "no-charge", "charging"],
        default="charging",
    )
    parser.add_argument(
        "--validator",
        type=Path,
        default=Path("tools/minoa/desktopValidator/desktopValidator/desktopValidator.jar"),
    )
    parser.add_argument(
        "--keep-candidates",
        action="store_true",
        help="Keep all candidate output JSONs under outputs/minoa/search.",
    )
    return parser


def direction_count(input_path: Path) -> int:
    data = json.loads(input_path.read_text())
    return len(data["directions"])


def variant_vectors(args: argparse.Namespace) -> list[list[int] | None]:
    if not args.per_direction:
        return [None for _ in range(args.variants)]

    n_dirs = direction_count(args.input)
    base = [0] * n_dirs
    vectors: list[list[int]] = [base]

    # Coordinate search: change one direction at a time. This is cheap and
    # often enough to align terminals better without exploding combinations.
    for direction_index in range(n_dirs):
        for variant in range(args.variants):
            candidate = base.copy()
            candidate[direction_index] = variant
            vectors.append(candidate)

    # A small deterministic random layer explores interactions between
    # directions while staying M3-friendly.
    rng = random.Random(args.seed)
    for _ in range(args.local_iterations):
        vectors.append([rng.randrange(args.variants) for _ in range(n_dirs)])

    deduped = []
    seen = set()
    for vector in vectors:
        key = tuple(vector)
        if key not in seen:
            seen.add(key)
            deduped.append(vector)
    return deduped


def main() -> None:
    args = build_parser().parse_args()
    start = time.perf_counter()
    instance_key = (
        args.input.stem.replace("Input", "Instance")
        .replace("input", "instance")
        .replace("INPUT", "INSTANCE")
    )
    search_dir = Path("outputs/minoa/search") / instance_key
    search_dir.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    best_cost: float | None = None
    best_path: Path | None = None
    rows = []

    vectors = variant_vectors(args)

    for run_index, vector in enumerate(vectors):
        if args.time_limit and time.perf_counter() - start >= args.time_limit:
            break
        variant = run_index if vector is None else 0

        candidate_path = search_dir / (
            f"candidate_variant_{run_index:03d}_{args.builder}_{args.ev_mode}_output.json"
        )
        try:
            output, stats = solve(
                args.input,
                builder=args.builder,
                ev_mode=args.ev_mode,
                tt_variant=variant,
                tt_variants=vector,
            )
            candidate_path.write_text(json.dumps(output, indent=2))
            validation = validate(args.validator, args.input, candidate_path)
            objective = parse_vs_cost(validation.stdout)
            valid = objective is not None
        except Exception as exc:
            stats = {"tt_variant": variant, "error": str(exc)}
            objective = None
            valid = False

        row = {
            "variant": variant,
            "tt_variants": vector,
            "valid": valid,
            "objective": objective,
            **stats,
        }
        rows.append(row)
        print(json.dumps(row))

        if valid and objective is not None and (best_cost is None or objective < best_cost):
            best_cost = objective
            best_path = candidate_path
            shutil.copyfile(candidate_path, args.output)

    summary = {
        "best_objective": best_cost,
        "best_candidate": str(best_path) if best_path else None,
        "output": str(args.output) if best_path else None,
        "tried": len(rows),
        "valid": sum(1 for row in rows if row["valid"]),
    }
    print(json.dumps(summary, indent=2))

    if not args.keep_candidates:
        for candidate in search_dir.glob("*_Output.json"):
            if best_path is None or candidate != best_path:
                candidate.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
