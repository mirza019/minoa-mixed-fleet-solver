#!/usr/bin/env python3
"""Generate thesis figures from the lower-bound master CSV."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


HEADLINE = ["Small", "Medium", "Large"]
FINAL_RESULTS_CSV = Path("outputs/minoa/final_archive/final_results.csv")
BLUE = "#2f6fb0"
GREEN = "#4f9d69"
ORANGE = "#d98c2b"
GRAY = "#6f7782"
RED = "#b04a4a"


plt.rcParams.update(
    {
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
    }
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=Path("results/lower_bounds/all_instances_lower_bounds.csv"))
    parser.add_argument("--out-dir", type=Path, default=Path("FAU_Thesis_temp/figures"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    rows = read_rows(args.csv)
    rows = sync_upper_bounds_from_final_archive(rows, FINAL_RESULTS_CSV)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    plot_headline_bounds(rows, args.out_dir / "fig48_headline_global_and_tt_bounds.pdf")
    plot_global_gaps(rows, args.out_dir / "fig49_global_gap_by_instance.pdf")
    plot_gap_comparison(rows, args.out_dir / "fig50_global_vs_selected_tt_gap.pdf")
    plot_vehicle_bounds(rows, args.out_dir / "fig51_vehicle_bound_comparison.pdf")
    plot_runtime(rows, args.out_dir / "fig52_lower_bound_runtime.pdf")
    plot_gap_vs_size(rows, args.out_dir / "fig53_gap_vs_candidate_trips.pdf")
    print(f"Generated lower-bound figures in {args.out_dir}")


def read_rows(path: Path) -> list[dict[str, object]]:
    with path.open() as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            converted: dict[str, object] = dict(row)
            for key, value in row.items():
                if key in {"instance", "global_lb_status", "solver", "input", "output", "globally_valid"}:
                    continue
                if value == "":
                    converted[key] = np.nan
                else:
                    converted[key] = float(value)
            rows.append(converted)
        return rows


def sync_upper_bounds_from_final_archive(
    rows: list[dict[str, object]], final_csv: Path
) -> list[dict[str, object]]:
    """Use final validated archive results as UB source for lower-bound plots."""
    if not final_csv.exists():
        return rows
    archive: dict[str, dict[str, str]] = {}
    with final_csv.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            archive[normal_name(row.get("instance", ""))] = row

    for row in rows:
        archived = archive.get(normal_name(str(row.get("instance", ""))))
        if not archived:
            continue
        ub = float(archived["objective"])
        selected_lb = num(row, "selected_tt_cost_lb")
        global_lb = num(row, "global_cost_lb")
        row["validated_upper_bound"] = ub
        row["used_vehicles"] = float(archived["total_blocks"])
        row["selected_trips"] = float(archived["selected_trips"])
        row["output"] = archived.get("archived_output", row.get("output", ""))
        if ub > 0:
            row["global_gap_percent"] = 100.0 * (ub - global_lb) / ub
            row["selected_tt_gap_percent"] = 100.0 * (ub - selected_lb) / ub
    return rows


def normal_name(value: str) -> str:
    return " ".join(value.strip().split()).lower()


def headline_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_name = {str(row["instance"]).strip(): row for row in rows}
    return [by_name[name] for name in HEADLINE if name in by_name]


def plot_headline_bounds(rows: list[dict[str, object]], path: Path) -> None:
    data = headline_rows(rows)
    labels = [str(row["instance"]) for row in data]
    x = np.arange(len(data))
    width = 0.25
    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    series = [
        ("Validated UB", [num(row, "validated_upper_bound") for row in data], BLUE, -width),
        ("Global LB", [num(row, "global_cost_lb") for row in data], GREEN, 0.0),
        ("Selected-TT LB", [num(row, "selected_tt_cost_lb") for row in data], ORANGE, width),
    ]
    for name, values, color, offset in series:
        bars = ax.bar(x + offset, values, width, label=name, color=color, edgecolor="black", linewidth=0.5)
        label_bars(ax, bars, fmt="{:.0f}", dy=8, preserve_ylim=True)
    max_value = max(value for _, values, _, _ in series for value in values if not np.isnan(value))
    ax.set_ylim(0, max_value * 1.16)
    ax.set_ylabel("Cost units")
    ax.set_xticks(x, labels)
    ax.set_title("Upper Bounds and Lower Bounds on Headline Instances")
    ax.legend(ncol=3, loc="upper left", frameon=False)
    ax.grid(axis="y", alpha=0.25)
    save(fig, path)


def plot_global_gaps(rows: list[dict[str, object]], path: Path) -> None:
    data = sorted(rows, key=lambda row: num(row, "global_gap_percent"))
    labels = [str(row["instance"]) for row in data]
    values = [num(row, "global_gap_percent") for row in data]
    colors = [GREEN if num(row, "global_cost_lb") > 0 else GRAY for row in data]
    fig, ax = plt.subplots(figsize=(9.2, 6.8))
    y = np.arange(len(data))
    bars = ax.barh(y, values, color=colors, edgecolor="black", linewidth=0.4)
    ax.set_yticks(y, labels)
    ax.set_xlabel("Global gap to validated UB (%)")
    ax.set_title("Certified Global Gap by Instance")
    ax.grid(axis="x", alpha=0.25)
    label_bars_h(ax, bars, fmt="{:.1f}%")
    save(fig, path)


def plot_gap_comparison(rows: list[dict[str, object]], path: Path) -> None:
    data = sorted(rows, key=lambda row: str(row["instance"]))
    display = {
        "1line 6timeWindow": "1line 6TW",
        "2lines 6 timeWindows": "2lines 6TW",
        "3linesTriangle": "3lines tri.",
        "Toy Example": "Toy",
    }
    labels = [display.get(str(row["instance"]), str(row["instance"])) for row in data]
    y = np.arange(len(data))
    global_gap = [num(row, "global_gap_percent") for row in data]
    selected_gap = [num(row, "selected_tt_gap_percent") for row in data]
    dark = "#111827"
    fig, ax = plt.subplots(figsize=(10.2, 7.3))
    ax.scatter(global_gap, y + 0.18, s=110, color=GREEN, edgecolor=dark, linewidth=0.45, label="Global gap", zorder=3)
    ax.scatter(selected_gap, y - 0.18, s=110, color=ORANGE, edgecolor=dark, linewidth=0.45, label="Selected-TT diagnostic gap", zorder=3)
    for row_idx, row in enumerate(data):
        g = num(row, "global_gap_percent")
        s = num(row, "selected_tt_gap_percent")
        ax.plot(
            [g, s],
            [row_idx, row_idx],
            color="#c8ccd2",
            linewidth=1.5,
            zorder=0,
        )
        ax.text(min(g + 1.5, 102.5), row_idx + 0.18, f"{g:.1f}", va="center", ha="left", fontsize=13, color=dark, weight="bold")
        ax.text(min(s + 1.5, 102.5), row_idx - 0.18, f"{s:.1f}", va="center", ha="left", fontsize=13, color=dark, weight="bold")
    ax.set_yticks(y, labels)
    ax.set_xlim(-1, 108)
    ax.set_xlabel("Gap to validated upper bound (%)", labelpad=9, fontsize=15, color=dark)
    ax.set_title("Global and Selected-Timetable Gaps", pad=16, weight="bold", fontsize=18, color=dark)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=2, frameon=False, fontsize=13)
    ax.grid(axis="x", alpha=0.28)
    ax.tick_params(axis="both", labelsize=14, colors=dark)
    for spine in ax.spines.values():
        spine.set_color(dark)
        spine.set_linewidth(1.1)
    save(fig, path)


def plot_vehicle_bounds(rows: list[dict[str, object]], path: Path) -> None:
    data = sorted(rows, key=lambda row: num(row, "used_vehicles"))
    labels = [str(row["instance"]) for row in data]
    x = np.arange(len(data))
    width = 0.26
    fig, ax = plt.subplots(figsize=(11.6, 5.8))
    series = [
        ("Used vehicles", [num(row, "used_vehicles") for row in data], BLUE, -width),
        ("Global vehicle LB", [num(row, "global_vehicle_lb") for row in data], GREEN, 0.0),
        ("Selected-TT path-cover LB", [num(row, "selected_tt_path_cover_vehicle_lb") for row in data], ORANGE, width),
    ]
    for name, values, color, offset in series:
        bars = ax.bar(x + offset, values, width, label=name, color=color, edgecolor="black", linewidth=0.4)
        label_bars(ax, bars, fmt="{:.0f}", dy=1)
    ax.set_ylabel("Vehicles")
    ax.set_xticks(x, labels, rotation=38, ha="right")
    ax.set_title("Used Vehicles Compared with Vehicle Lower Bounds")
    ax.legend(ncol=3, loc="upper left", frameon=False)
    ax.grid(axis="y", alpha=0.25)
    save(fig, path)


def plot_runtime(rows: list[dict[str, object]], path: Path) -> None:
    data = sorted(rows, key=lambda row: num(row, "global_lb_runtime_seconds"))
    labels = [str(row["instance"]) for row in data]
    values = [num(row, "global_lb_runtime_seconds") for row in data]
    colors = [GREEN if str(row["global_lb_status"]) == "optimal" else GRAY for row in data]
    fig, ax = plt.subplots(figsize=(9.4, 6.8))
    y = np.arange(len(data))
    bars = ax.barh(y, values, color=colors, edgecolor="black", linewidth=0.4)
    ax.set_yticks(y, labels)
    ax.set_xlabel("Runtime (seconds)")
    ax.set_title("Runtime of Global Lower-Bound Computation")
    ax.grid(axis="x", alpha=0.25)
    label_bars_h(ax, bars, fmt="{:.1f}s")
    save(fig, path)


def plot_gap_vs_size(rows: list[dict[str, object]], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10.4, 6.4))
    offsets = {
        "8lines": (-24, -13),
        "5lines": (-32, 7),
        "3linesTriangle": (-30, -14),
        "3lines": (-22, 8),
        "Large": (7, -13),
        "2lines 6 timeWindows": (7, -13),
    }
    for row in rows:
        x = num(row, "candidate_trips")
        y = num(row, "global_gap_percent")
        color = GREEN if num(row, "global_cost_lb") > 0 else RED
        ax.scatter(x, y, s=55, color=color, edgecolor="black", linewidth=0.5)
        label = str(row["instance"]).strip()
        dx, dy = offsets.get(label, (5, 5))
        ax.annotate(label, (x, y), xytext=(dx, dy), textcoords="offset points", fontsize=9)
    ax.set_xscale("log")
    ax.set_xlabel("Candidate trips (log scale)")
    ax.set_ylabel("Global gap to validated UB (%)")
    ax.set_title("Model Size and Certified Global Gap")
    ax.grid(alpha=0.25, which="both")
    ax.set_ylim(0, 108)
    save(fig, path)


def num(row: dict[str, object], key: str) -> float:
    value = row.get(key, np.nan)
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def label_bars(ax: plt.Axes, bars, *, fmt: str, dy: float, preserve_ylim: bool = False) -> None:
    top = max((bar.get_height() for bar in bars), default=0)
    if not preserve_ylim:
        ax.set_ylim(top=top * 1.18 + 1)
    for bar in bars:
        value = bar.get_height()
        if np.isnan(value):
            continue
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + dy,
            fmt.format(value),
            ha="center",
            va="bottom",
            fontsize=9,
        )


def label_bars_h(ax: plt.Axes, bars, *, fmt: str) -> None:
    right = max((bar.get_width() for bar in bars), default=0)
    ax.set_xlim(right=right * 1.22 + 1)
    for bar in bars:
        value = bar.get_width()
        if np.isnan(value):
            continue
        ax.text(value + max(0.5, right * 0.01), bar.get_y() + bar.get_height() / 2, fmt.format(value), va="center", fontsize=9)


def save(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


if __name__ == "__main__":
    main()
