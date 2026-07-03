#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from contextlib import contextmanager
import json
import itertools
import os
import random
import shutil
import time
from pathlib import Path

from minoa_lib.costs import cost_breakdown
from minoa_lib.experiments.metrics import parse_vs_cost
from minoa_lib.reporting import update_report_sol
from minoa_lib.solver import solve
from minoa_lib.validation import validate


@dataclass(frozen=True)
class SearchConfig:
    name: str
    edge_mode: str
    ev_strategy: str
    depot_bridge_min_gap: str | None = None
    avoid_break_nodes: str | None = None


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
        "--edge-mode",
        choices=["time", "balanced", "ev", "charging"],
        default="time",
    )
    parser.add_argument(
        "--ev-strategy",
        choices=["legacy", "lookahead", "risk"],
        default="legacy",
    )
    parser.add_argument(
        "--no-adaptive",
        action="store_true",
        help="Disable adaptive candidate families and use only the requested edge/EV strategy.",
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


def search_configs(args: argparse.Namespace) -> list[SearchConfig]:
    """Named bounded neighborhoods used by the multi-start controller.

    Each configuration still builds a complete solution from the same selected
    timetable vector.  The configurations differ only in local edge scoring,
    charging insertion, or depot-bridge preference.  This makes the search
    reproducible. Candidate ranking uses the internally reconstructed official
    objective; the external validator is called only after the incumbent has
    been selected.
    """
    base = SearchConfig("base", args.edge_mode, args.ev_strategy)
    if args.no_adaptive:
        return [base]

    configs = [
        base,
        SearchConfig("charging-edge-score", "charging", args.ev_strategy),
        SearchConfig("balanced-edge-score", "balanced", args.ev_strategy),
        SearchConfig("ev-pressure-score", "ev", args.ev_strategy),
    ]
    if args.ev_mode == "charging":
        configs.extend(
            [
                SearchConfig("lookahead-charging", args.edge_mode, "lookahead"),
                SearchConfig("charging-edge-lookahead", "charging", "lookahead"),
                SearchConfig("balanced-lookahead", "balanced", "lookahead"),
                SearchConfig("risk-aware-ev-assignment", args.edge_mode, "risk"),
                SearchConfig("charging-risk-rematch", "charging", "risk"),
                SearchConfig("balanced-risk-rematch", "balanced", "risk"),
            ]
        )
    configs.extend(
        [
            SearchConfig("successor-swap-no-depot-shortcut", args.edge_mode, args.ev_strategy, "999999"),
            SearchConfig("successor-swap-wide-depot", "balanced", args.ev_strategy, "1800"),
            SearchConfig("local-no-depot-risk", "charging", "risk", "999999"),
            SearchConfig("local-wide-depot-risk", "balanced", "risk", "1800"),
        ]
    )

    deduped: list[SearchConfig] = []
    seen = set()
    for config in configs:
        key = (config.edge_mode, config.ev_strategy, config.depot_bridge_min_gap, config.avoid_break_nodes)
        if key not in seen:
            seen.add(key)
            deduped.append(config)
    return deduped


@contextmanager
def solver_environment(config: SearchConfig):
    previous_gap = os.environ.get("MINOA_DEPOT_BRIDGE_MIN_GAP")
    previous_avoid = os.environ.get("MINOA_AVOID_TERMINAL_BREAK_NODES")
    try:
        if config.depot_bridge_min_gap is None:
            os.environ.pop("MINOA_DEPOT_BRIDGE_MIN_GAP", None)
        else:
            os.environ["MINOA_DEPOT_BRIDGE_MIN_GAP"] = config.depot_bridge_min_gap
        if config.avoid_break_nodes is None:
            os.environ.pop("MINOA_AVOID_TERMINAL_BREAK_NODES", None)
        else:
            os.environ["MINOA_AVOID_TERMINAL_BREAK_NODES"] = config.avoid_break_nodes
        yield
    finally:
        if previous_gap is None:
            os.environ.pop("MINOA_DEPOT_BRIDGE_MIN_GAP", None)
        else:
            os.environ["MINOA_DEPOT_BRIDGE_MIN_GAP"] = previous_gap
        if previous_avoid is None:
            os.environ.pop("MINOA_AVOID_TERMINAL_BREAK_NODES", None)
        else:
            os.environ["MINOA_AVOID_TERMINAL_BREAK_NODES"] = previous_avoid


def main() -> None:
    args = build_parser().parse_args()
    wall_start = time.perf_counter()
    algorithm_seconds = 0.0
    validation_seconds = 0.0
    instance_key = (
        args.input.stem.replace("Input", "Instance")
        .replace("input", "instance")
        .replace("INPUT", "INSTANCE")
    )
    search_dir = Path("outputs/minoa/search") / instance_key
    search_dir.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    input_data = json.loads(args.input.read_text())

    best_cost: float | None = None
    best_path: Path | None = None
    rows = []

    vector_start = time.perf_counter()
    vectors = variant_vectors(args)
    configs = search_configs(args)
    algorithm_seconds += time.perf_counter() - vector_start

    for config_index, config in enumerate(configs):
        for run_index, vector in enumerate(vectors):
            if args.time_limit and time.perf_counter() - wall_start >= args.time_limit:
                break
            variant = run_index if vector is None else 0

            candidate_path = search_dir / (
                f"candidate_config_{config_index:02d}_variant_{run_index:03d}_{args.builder}_{args.ev_mode}_output.json"
            )
            internal_objective = None
            failure_reason = ""
            try:
                solve_start = time.perf_counter()
                with solver_environment(config):
                    output, stats = solve(
                        args.input,
                        builder=args.builder,
                        ev_mode=args.ev_mode,
                        tt_variant=variant,
                        tt_variants=vector,
                        edge_mode=config.edge_mode,
                        ev_strategy=config.ev_strategy,
                    )
                algorithm_seconds += time.perf_counter() - solve_start
                cost_start = time.perf_counter()
                internal_objective = cost_breakdown(input_data, output).total
                algorithm_seconds += time.perf_counter() - cost_start
                candidate_path.write_text(json.dumps(output, indent=2))
                objective = internal_objective
                valid = True
            except Exception as exc:
                stats = {"tt_variant": variant, "error": str(exc)}
                objective = None
                valid = False
                failure_reason = classify_failure(str(exc))

            row = {
                "config": config.name,
                "edge_mode": config.edge_mode,
                "ev_strategy": config.ev_strategy,
                "depot_bridge_min_gap": config.depot_bridge_min_gap,
                "variant": variant,
                "tt_variants": vector,
                "valid": valid,
                "objective": objective,
                "internal_objective": internal_objective,
                "failure_reason": failure_reason,
                **stats,
            }
            rows.append(row)
            print(json.dumps(row))

            comparison_start = time.perf_counter()
            improves_incumbent = is_better_internal_candidate(row, best_cost)
            algorithm_seconds += time.perf_counter() - comparison_start
            if improves_incumbent:
                best_cost = internal_objective
                best_path = candidate_path
                shutil.copyfile(candidate_path, args.output)
        if args.time_limit and time.perf_counter() - wall_start >= args.time_limit:
            break

    external_objective = None
    final_validated = False
    final_validation_output = ""
    if best_cost is not None and best_path is not None:
        validation_start = time.perf_counter()
        validation = validate(args.validator, args.input, args.output)
        validation_seconds += time.perf_counter() - validation_start
        final_validation_output = validation.stdout
        external_objective = parse_vs_cost(validation.stdout)
        final_validated = external_objective is not None
        if not final_validated:
            raise SystemExit(
                "Selected incumbent failed independent external validation:\n"
                f"{final_validation_output}"
            )
        update_report_sol(args.output, upper_bound=external_objective, execution_time=algorithm_seconds)

    summary = {
        "best_internal_objective": best_cost,
        "external_objective": external_objective,
        "objective_delta": None
        if best_cost is None or external_objective is None
        else round(float(external_objective) - float(best_cost), 6),
        "best_candidate": str(best_path) if best_path else None,
        "output": str(args.output) if best_path else None,
        "tried": len(rows),
        "configs": [config.name for config in configs],
        "valid": sum(1 for row in rows if row["valid"]),
        "invalid": sum(1 for row in rows if not row["valid"]),
        "final_validated": final_validated,
        "failure_counts": failure_counts(rows),
        "algorithm_seconds": round(algorithm_seconds, 6),
        "validation_seconds": round(validation_seconds, 6),
        "wall_seconds": round(time.perf_counter() - wall_start, 6),
    }
    print(json.dumps(summary, indent=2))

    if not args.keep_candidates:
        for candidate in search_dir.glob("candidate_*.json"):
            if best_path is None or candidate != best_path:
                candidate.unlink(missing_ok=True)


def classify_failure(text: str) -> str:
    lowered = text.lower()
    if "no initial/final" in lowered:
        return "boundary-trip failure"
    if "no feasible tt path" in lowered:
        return "no valid headway path"
    if "parking capacity" in lowered:
        return "parking-capacity conflict"
    if "slow" in lowered and "capacity" in lowered:
        return "slow-charge capacity conflict"
    if "fast" in lowered and "capacity" in lowered:
        return "fast-charge capacity conflict"
    if "autonomy" in lowered or "not feasible vehicle block" in lowered:
        return "EV autonomy failure"
    if "trip coverage mismatch" in lowered:
        return "trip coverage failure"
    if "time" in lowered and "activity" in lowered:
        return "invalid activity order"
    if text.strip():
        return "output validation failure"
    return "other"


def is_better_internal_candidate(row: dict[str, object], incumbent_cost: float | None) -> bool:
    """Return true only when a complete candidate has a lower internal objective.

    Timetable scores, matching edge weights, and internal cost estimates are
    useful during construction, but the incumbent update uses the reconstructed
    official objective of a complete candidate schedule. The external validator
    is reserved for the final independent audit.
    """
    if not row.get("valid"):
        return False
    objective = row.get("internal_objective")
    if objective is None:
        return False
    return incumbent_cost is None or float(objective) < incumbent_cost


def failure_counts(rows: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        reason = str(row.get("failure_reason") or "")
        if not reason:
            continue
        counts[reason] = counts.get(reason, 0) + 1
    return counts


if __name__ == "__main__":
    main()
