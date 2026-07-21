#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from minoa_lib.experiments.table import evaluate_many, markdown_table


def missing_path_message(missing_paths: list[Path]) -> str:
    formatted = "\n".join(f"  - {path}" for path in missing_paths)
    return (
        "Cannot build the report because these input/output files do not exist:\n"
        f"{formatted}\n\n"
        "Generate the corresponding outputs first. For example:\n"
        "  .venv/bin/python scripts/run_experiment.py --algorithm multistart --scope sml\n\n"
        "For all Senior instances, run:\n"
        "  .venv/bin/python scripts/run_experiment.py --algorithm multistart --scope all"
    )


def parse_pair(text: str) -> tuple[Path, Path]:
    if ":" not in text:
        raise argparse.ArgumentTypeError("Use INPUT_JSON:OUTPUT_JSON")
    input_text, output_text = text.split(":", 1)
    return Path(input_text), Path(output_text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "pairs",
        nargs="+",
        type=parse_pair,
        help="Pairs in the form INPUT_JSON:OUTPUT_JSON",
    )
    parser.add_argument(
        "--validator",
        type=Path,
        default=Path("tools/minoa/desktopValidator/desktopValidator/desktopValidator.jar"),
    )
    args = parser.parse_args()

    missing_paths = [
        path
        for pair in args.pairs
        for path in pair
        if not path.exists()
    ]
    if missing_paths:
        raise SystemExit(missing_path_message(missing_paths))

    rows = evaluate_many(args.pairs, args.validator)
    print(markdown_table(rows))


if __name__ == "__main__":
    main()
