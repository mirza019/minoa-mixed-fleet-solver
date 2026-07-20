#!/usr/bin/env python3
"""Revalidate all input/output pairs recorded by a MINOA pipeline manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from minoa_lib.experiments.table import evaluate_many, markdown_table


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the external validator for all outputs listed in a pipeline manifest."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("outputs/minoa/all_multistart/pipeline_manifest.json"),
        help="Pipeline manifest written by scripts/minoa_pipeline.py.",
    )
    parser.add_argument(
        "--validator",
        type=Path,
        default=Path("tools/minoa/desktopValidator/desktopValidator/desktopValidator.jar"),
    )
    return parser


def pairs_from_manifest(manifest_path: Path) -> list[tuple[Path, Path]]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    processed_by_instance = {
        str(record["instance"]): Path(record["processed"])
        for record in data.get("normalization", [])
        if record.get("status") == "ok"
    }
    pairs: list[tuple[Path, Path]] = []
    for row in data.get("rows", []):
        output = row.get("Output")
        instance = row.get("Instance")
        if not output or not instance:
            continue
        input_path = processed_by_instance.get(str(instance))
        if input_path is None:
            continue
        pairs.append((input_path, Path(str(output))))
    if not pairs:
        raise ValueError(f"No input/output pairs found in {manifest_path}")
    return pairs


def main() -> None:
    args = build_parser().parse_args()
    rows = evaluate_many(pairs_from_manifest(args.manifest), args.validator)
    print(markdown_table(rows))


if __name__ == "__main__":
    main()
