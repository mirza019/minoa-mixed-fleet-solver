#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from minoa_lib.experiments.table import evaluate_many, markdown_table


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

    rows = evaluate_many(args.pairs, args.validator)
    print(markdown_table(rows))


if __name__ == "__main__":
    main()
