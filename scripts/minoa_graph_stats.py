#!/usr/bin/env python3
"""Report compatibility-graph statistics for MINOA input/output pairs."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from minoa_lib.blocks import bridge_activities, depot_bridge_activities
from minoa_lib.network import min_max_stop
from minoa_lib.types import JsonDict, SelectedTrip


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compute compatibility-graph statistics from MINOA input/output "
            "pairs. Each pair is written as input.json:output.json."
        )
    )
    parser.add_argument("pairs", nargs="+", help="Input/output pair as input.json:output.json")
    parser.add_argument(
        "--approach",
        default="multi-start path-cover",
        help="Approach name printed in the table.",
    )
    parser.add_argument(
        "--latex",
        type=Path,
        help="Optional path for a LaTeX tabular fragment.",
    )
    parser.add_argument(
        "--depot-bridge-min-gap",
        default="999999",
        help=(
            "Value for MINOA_DEPOT_BRIDGE_MIN_GAP during graph reconstruction. "
            "The optimized headline runs use 999999."
        ),
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    rows = []
    previous_gap = os.environ.get("MINOA_DEPOT_BRIDGE_MIN_GAP")
    os.environ["MINOA_DEPOT_BRIDGE_MIN_GAP"] = str(args.depot_bridge_min_gap)
    try:
        for pair in args.pairs:
            input_text, output_text = pair.split(":", 1)
            rows.append(graph_stats(Path(input_text), Path(output_text), args.approach))
    finally:
        if previous_gap is None:
            os.environ.pop("MINOA_DEPOT_BRIDGE_MIN_GAP", None)
        else:
            os.environ["MINOA_DEPOT_BRIDGE_MIN_GAP"] = previous_gap

    print(markdown_table(rows))
    if args.latex:
        args.latex.parent.mkdir(parents=True, exist_ok=True)
        args.latex.write_text(latex_table(rows))
        print(f"\nLaTeX table written to: {args.latex}")


def graph_stats(input_path: Path, output_path: Path, approach: str) -> dict[str, object]:
    data = json.loads(input_path.read_text())
    output = json.loads(output_path.read_text())
    selected_items = selected_items_from_output(output)
    items = sorted(
        selected_items,
        key=lambda x: (x["trip"]["startTime"], x["trip"]["endTime"], x["trip"]["tripId"]),
    )

    inline_edges = 0
    depot_edges = 0
    graph_edges = 0
    time_ordered_pairs = 0
    both_edges = 0
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i]["trip"]["endTime"] > items[j]["trip"]["startTime"]:
                continue
            time_ordered_pairs += 1
            inline = inline_feasible(data, items[i], items[j])
            depot = depot_feasible(data, items[i], items[j])
            if inline:
                inline_edges += 1
            if depot:
                depot_edges += 1
            if inline and depot:
                both_edges += 1
            if bridge_activities(data, items[i], items[j]) is not None:
                graph_edges += 1

    selected = len(items)
    vehicles = len(output.get("vehicleBlockList", []))
    matched_arcs = max(0, selected - vehicles)
    density = (graph_edges / time_ordered_pairs * 100.0) if time_ordered_pairs else 0.0
    return {
        "Instance": instance_name(input_path),
        "Approach": approach,
        "Candidate trips": count_candidate_trips(data),
        "Selected trips": selected,
        "Time-ordered pairs": time_ordered_pairs,
        "In-line arcs": inline_edges,
        "Depot-bridge arcs": depot_edges,
        "Graph arcs": graph_edges,
        "Matched arcs": matched_arcs,
        "Vehicles": vehicles,
        "Density (%)": density,
        "Both feasible": both_edges,
    }


def selected_items_from_output(output: JsonDict) -> list[SelectedTrip]:
    items: list[SelectedTrip] = []
    for direction_wrap in output["directions"]:
        direction = direction_wrap["direction"]
        for trip_wrap in direction["trips"]:
            items.append({"direction": direction, "trip": trip_wrap["trip"]})
    return items


def inline_feasible(data: JsonDict, prev: SelectedTrip, nxt: SelectedTrip) -> bool:
    prev_trip = prev["trip"]
    next_trip = nxt["trip"]
    prev_dir = prev["direction"]
    next_dir = nxt["direction"]
    if prev_dir["endNode"] != next_dir["startNode"]:
        return False
    if prev_trip["endTime"] > next_trip["startTime"]:
        return False
    avoid_nodes = {
        node.strip()
        for node in os.environ.get("MINOA_AVOID_TERMINAL_BREAK_NODES", "").split(",")
        if node.strip()
    }
    if prev_dir["endNode"] in avoid_nodes:
        return False
    gap = next_trip["startTime"] - prev_trip["endTime"]
    min_stop, max_stop = min_max_stop(data, prev_dir["endNode"], prev_trip["endTime"])
    return min_stop <= gap <= max_stop


def depot_feasible(data: JsonDict, prev: SelectedTrip, nxt: SelectedTrip) -> bool:
    prev_trip = prev["trip"]
    next_trip = nxt["trip"]
    prev_dir = prev["direction"]
    next_dir = nxt["direction"]
    if prev_trip["endTime"] > next_trip["startTime"]:
        return False
    if prev_dir["endNode"] == next_dir["startNode"]:
        gap = next_trip["startTime"] - prev_trip["endTime"]
        min_gap = int(os.environ.get("MINOA_DEPOT_BRIDGE_MIN_GAP", "0"))
        if gap < min_gap:
            return False
    return depot_bridge_activities(data, prev, nxt) is not None


def count_candidate_trips(data: JsonDict) -> int:
    return sum(len(direction_wrap["direction"]["trips"]) for direction_wrap in data["directions"])


def instance_name(path: Path) -> str:
    name = path.stem
    for token in ["_Input_S", "_input_S", "_Instance_S", "_input", "_Input"]:
        name = name.replace(token, "")
    return name.replace("_", " ").strip()


def markdown_table(rows: list[dict[str, object]]) -> str:
    headers = [
        "Instance",
        "Approach",
        "Candidate trips",
        "Selected trips",
        "Time-ordered pairs",
        "In-line arcs",
        "Depot-bridge arcs",
        "Graph arcs",
        "Matched arcs",
        "Vehicles",
        "Density (%)",
    ]
    table = [headers]
    for row in rows:
        table.append(
            [
                str(row["Instance"]),
                str(row["Approach"]),
                f"{int(row['Candidate trips']):,}",
                f"{int(row['Selected trips']):,}",
                f"{int(row['Time-ordered pairs']):,}",
                f"{int(row['In-line arcs']):,}",
                f"{int(row['Depot-bridge arcs']):,}",
                f"{int(row['Graph arcs']):,}",
                f"{int(row['Matched arcs']):,}",
                f"{int(row['Vehicles']):,}",
                f"{float(row['Density (%)']):.2f}",
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
        "\\begin{tabular}{lrrrrrrrrr}",
        "\\toprule",
        "Instance & Cand. trips & Sel. trips & Time pairs & In-line & Depot & Graph arcs & Matched & Veh. & Density \\\\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(
            "{} & {:,} & {:,} & {:,} & {:,} & {:,} & {:,} & {:,} & {:,} & {:.2f}\\% \\\\".format(
                latex_escape(str(row["Instance"])),
                int(row["Candidate trips"]),
                int(row["Selected trips"]),
                int(row["Time-ordered pairs"]),
                int(row["In-line arcs"]),
                int(row["Depot-bridge arcs"]),
                int(row["Graph arcs"]),
                int(row["Matched arcs"]),
                int(row["Vehicles"]),
                float(row["Density (%)"]),
            )
        )
    lines.extend(["\\bottomrule", "\\end{tabular}", ""])
    return "\n".join(lines)


def latex_escape(text: str) -> str:
    return text.replace("_", "\\_").replace("%", "\\%").replace("&", "\\&")


if __name__ == "__main__":
    main()
