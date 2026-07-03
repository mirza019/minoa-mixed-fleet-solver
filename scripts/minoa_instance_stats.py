#!/usr/bin/env python3
"""Report structural statistics for MINOA senior input instances."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create MINOA instance statistics tables.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/processed/minoa/all_multistart"),
        help="Directory containing input JSON files.",
    )
    parser.add_argument("--latex", type=Path, help="Optional path for a LaTeX tabular fragment.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    rows = []
    for path in sorted(args.input_dir.glob("*.json")):
        if "Output" in path.name or "output" in path.name:
            continue
        rows.append(instance_stats(path))
    rows = canonical_order(rows)
    print(markdown_table(rows))
    if args.latex:
        args.latex.parent.mkdir(parents=True, exist_ok=True)
        args.latex.write_text(latex_table(rows))
        print(f"\nLaTeX table written to: {args.latex}")


def instance_stats(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text())
    horizon = data["timeHorizon"]
    directions = [wrap["direction"] for wrap in data["directions"]]
    nodes = [wrap["node"] for wrap in data["nodes"]]
    electric = next(
        wrap["vehicleType"]
        for wrap in data["fleet"]["vehicleList"]
        if "electricInfo" in wrap["vehicleType"]
    )
    ev_info = electric["electricInfo"]
    return {
        "Instance": instance_name(path),
        "Directions": len(directions),
        "Nodes": len(nodes),
        "Deadhead arcs": len(data["deadheadArcs"]),
        "Headway windows": sum(len(direction["headways"]) for direction in directions),
        "Candidate trips": sum(len(direction["trips"]) for direction in directions),
        "Planning horizon (min)": int(round((max(horizon) - min(horizon)) / 60)),
        "EV fleet cap": int(ev_info["numberVehicle"]),
        "EV autonomy (km)": float(ev_info["vehicleAutonomy"]),
        "Slow chargers": sum(int(node.get("slowChargeCapacity", 0)) for node in nodes),
        "Fast chargers": sum(int(node.get("fastChargeCapacity", 0)) for node in nodes),
    }


def instance_name(path: Path) -> str:
    name = path.stem
    for token in ["_Input_S", "_input_S", "_Instance_S", "_input", "_Input"]:
        name = name.replace(token, "")
    return name.replace("_", " ").strip()


def canonical_order(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    order = {
        "Small": 0,
        "Medium": 1,
        "Large": 2,
        "Toy Example": 3,
        "1line": 4,
        "1line 6timeWindow": 5,
        "2lines": 6,
        "2lines 6 timeWindows": 7,
        "3lines": 8,
        "3linesTriangle": 9,
        "5lines": 10,
        "8lines": 11,
    }
    return sorted(rows, key=lambda row: (order.get(str(row["Instance"]), 99), str(row["Instance"])))


def markdown_table(rows: list[dict[str, object]]) -> str:
    headers = [
        "Instance",
        "Directions",
        "Nodes",
        "Deadhead arcs",
        "Headway windows",
        "Candidate trips",
        "Planning horizon (min)",
        "EV fleet cap",
        "EV autonomy (km)",
    ]
    table = [headers]
    for row in rows:
        table.append(
            [
                str(row["Instance"]),
                str(row["Directions"]),
                str(row["Nodes"]),
                str(row["Deadhead arcs"]),
                str(row["Headway windows"]),
                f"{int(row['Candidate trips']):,}",
                str(row["Planning horizon (min)"]),
                str(row["EV fleet cap"]),
                f"{float(row['EV autonomy (km)']):.0f}",
            ]
        )
    widths = [max(len(line[idx]) for line in table) for idx in range(len(headers))]
    out = []
    out.append("| " + " | ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(table[0])) + " |")
    out.append("| " + " | ".join("-" * width for width in widths) + " |")
    for line in table[1:]:
        out.append("| " + " | ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(line)) + " |")
    return "\n".join(out)


def latex_table(rows: list[dict[str, object]]) -> str:
    lines = [
        "\\begin{tabular}{lrrrrrrrr}",
        "\\toprule",
        "Instance & Dir. & Nodes & Deadhead & Headway & Cand. trips & Horizon & EV cap & Auton. \\\\",
        " & & & arcs & windows & & (min) & & (km) \\\\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(
            "{} & {} & {} & {} & {} & {:,} & {} & {} & {:.0f} \\\\".format(
                latex_escape(str(row["Instance"])),
                int(row["Directions"]),
                int(row["Nodes"]),
                int(row["Deadhead arcs"]),
                int(row["Headway windows"]),
                int(row["Candidate trips"]),
                int(row["Planning horizon (min)"]),
                int(row["EV fleet cap"]),
                float(row["EV autonomy (km)"]),
            )
        )
    lines.extend(["\\bottomrule", "\\end{tabular}", ""])
    return "\n".join(lines)


def latex_escape(text: str) -> str:
    return text.replace("_", "\\_").replace("%", "\\%").replace("&", "\\&")


if __name__ == "__main__":
    main()
