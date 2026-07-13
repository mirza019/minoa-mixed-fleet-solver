#!/usr/bin/env python3
"""Regenerate focused thesis figures without changing experiment data."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


OUT = Path("FAU_Thesis_temp/figures")
FINAL_RESULTS = Path("outputs/minoa/final_archive/final_results.csv")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    make_algorithm_comparison(OUT / "fig54_algorithm_network_comparison.pdf")
    make_combined_pipeline(OUT / "fig55_combined_implementation_pipeline.pdf")
    final = pd.read_csv(FINAL_RESULTS)
    make_resource_pressure(final, OUT / "fig25_all_instance_resource_pressure.png")
    make_efficiency_panel(final, OUT / "fig26_all_instance_efficiency_panel.png")
    for path in [
        OUT / "fig54_algorithm_network_comparison.pdf",
        OUT / "fig55_combined_implementation_pipeline.pdf",
        OUT / "fig25_all_instance_resource_pressure.png",
        OUT / "fig26_all_instance_efficiency_panel.png",
    ]:
        print(path)


def make_algorithm_comparison(path: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch

    fig, axes = plt.subplots(3, 1, figsize=(8.2, 10.2), dpi=180)
    positions = {
        "A": (0.12, 0.64),
        "B": (0.46, 0.64),
        "C": (0.80, 0.64),
        "D": (0.28, 0.26),
        "E": (0.65, 0.26),
    }
    arcs = [("A", "B"), ("A", "D"), ("B", "C"), ("B", "E"), ("D", "E"), ("E", "C")]
    selected = [
        [("A", "B"), ("B", "C")],
        [("A", "D"), ("D", "E"), ("E", "C")],
        [("A", "B"), ("B", "E"), ("E", "C")],
    ]
    titles = [
        "(a) Greedy constructive heuristic",
        "(b) Unweighted path-cover matching",
        "(c) Weighted path-cover matching",
    ]
    notes = [
        "chooses the next successor locally",
        "maximizes the number of matched continuations",
        "uses the same graph with operational edge scores",
    ]
    score_labels = {
        ("A", "B"): "+high",
        ("A", "D"): "+1",
        ("B", "C"): "+medium",
        ("B", "E"): "+high",
        ("D", "E"): "+low",
        ("E", "C"): "+high",
    }

    for panel, ax in enumerate(axes):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.text(0.02, 0.94, titles[panel], ha="left", va="top", fontsize=13.5, weight="bold", color="#1f2937")
        ax.text(0.02, 0.08, notes[panel], ha="left", va="center", fontsize=10.8, color="#475569")
        for a, b in arcs:
            x1, y1 = positions[a]
            x2, y2 = positions[b]
            is_sel = (a, b) in selected[panel]
            color = "#1f5f99" if is_sel else "#aeb8c4"
            lw = 2.5 if is_sel else 1.25
            style = "-" if is_sel else "--"
            arrow = FancyArrowPatch(
                (x1, y1),
                (x2, y2),
                arrowstyle="-|>",
                mutation_scale=15,
                linewidth=lw,
                linestyle=style,
                color=color,
                shrinkA=18,
                shrinkB=18,
            )
            ax.add_patch(arrow)
            if panel == 2 and is_sel:
                ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.05, score_labels[(a, b)], ha="center", fontsize=10.0, color="#1f5f99")
        for name, (x, y) in positions.items():
            face = "#1f5f99" if any(name in edge for edge in selected[panel]) else "#eef2f7"
            text_color = "white" if face == "#1f5f99" else "#334155"
            ax.scatter([x], [y], s=1050, c=face, edgecolors="#334155", linewidths=1.25, zorder=3)
            ax.text(x, y, name, ha="center", va="center", fontsize=13.5, weight="bold", color=text_color, zorder=4)
        ax.text(0.68, 0.12, "selected arc", color="#1f5f99", fontsize=9.2, weight="bold")
        ax.plot([0.60, 0.66], [0.125, 0.125], color="#1f5f99", lw=2.6)
        ax.text(0.68, 0.06, "available arc", color="#64748b", fontsize=9.2)
        ax.plot([0.60, 0.66], [0.065, 0.065], color="#aeb8c4", lw=1.35, ls="--")

    fig.suptitle("Local and Matching-Based Vehicle-Block Construction", fontsize=15.8, weight="bold", y=0.995)
    fig.tight_layout(h_pad=1.0, rect=(0, 0, 1, 0.97))
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def make_combined_pipeline(path: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    fig, axes = plt.subplots(2, 1, figsize=(8.2, 8.8), dpi=180)
    for ax in axes:
        ax.set_xlim(0, 8.2)
        ax.set_ylim(0, 4.4)
        ax.axis("off")

    ax = axes[0]
    ax.text(0.1, 4.15, "(a) Solution-construction pipeline", ha="left", va="top", fontsize=13.5, weight="bold", color="#1f2937")
    boxes = [
        ("Input parser", "JSON instance\nand cost data", "#3b6ea8"),
        ("Timetable", "headway-feasible\nselected trips", "#2d8a5f"),
        ("Graph", "compatible arcs\nand attributes", "#bd7420"),
        ("Path cover", "matching and block\nreconstruction", "#6c55a3"),
        ("EV and charging", "fleet, battery,\ncapacity checks", "#b44949"),
    ]
    draw_pipeline(ax, boxes, y=1.75)
    ax.text(4.1, 0.62, "Construction ranks complete internally checked candidates; edge scores are surrogate matching weights.", ha="center", fontsize=9.7, color="#475569")

    ax = axes[1]
    ax.text(0.1, 4.15, "(b) Validation, reporting, and visualization pipeline", ha="left", va="top", fontsize=13.5, weight="bold", color="#1f2937")
    boxes = [
        ("JSON output", "complete timetable\nand vehicle blocks", "#3b6ea8"),
        ("External audit", "validator feasibility\nand objective check", "#b44949"),
        ("Cost audit", "internal/external\ncost reconciliation", "#2d8a5f"),
        ("Result tables", "cost, vehicles,\nruntime, bounds", "#bd7420"),
        ("Figures", "graph, fleet, and\nresource views", "#6c55a3"),
    ]
    draw_pipeline(ax, boxes, y=1.75)
    ax.text(4.1, 0.62, "Reporting analyzes the selected output; it does not guide graph construction or matching decisions.", ha="center", fontsize=9.7, color="#475569")

    fig.suptitle("Implementation Flow from Construction to Reported Evidence", fontsize=15.2, weight="bold", y=0.995)
    fig.tight_layout(h_pad=1.0)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def draw_pipeline(ax, boxes, y: float) -> None:
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    box_w = 1.34
    box_h = 1.42
    xs = [0.20, 1.78, 3.36, 4.94, 6.52]
    for x, (title, body, color) in zip(xs, boxes):
        patch = FancyBboxPatch(
            (x, y),
            box_w,
            box_h,
            boxstyle="round,pad=0.055,rounding_size=0.12",
            facecolor="#ffffff",
            edgecolor=color,
            linewidth=1.45,
        )
        ax.add_patch(patch)
        ax.text(x + box_w / 2, y + 0.91, title, ha="center", va="center", fontsize=8.7, weight="bold", color="#1f2937")
        ax.text(x + box_w / 2, y + 0.39, body, ha="center", va="center", fontsize=7.25, color="#475569", linespacing=1.08)
    for x1, x2 in zip(xs[:-1], xs[1:]):
        ax.add_patch(
            FancyArrowPatch(
                (x1 + box_w + 0.06, y + box_h / 2),
                (x2 - 0.06, y + box_h / 2),
                arrowstyle="-|>",
                mutation_scale=12,
                linewidth=1.15,
                color="#667085",
            )
        )


def make_resource_pressure(df: pd.DataFrame, path: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    plot_df = df.copy()
    plot_df["label"] = plot_df["instance"].replace({"2lines 6 timeWindows": "2lines 6TW", "1line 6timeWindow": "1line 6TW", "Toy Example": "Toy"})
    plot_df["deadhead_per_trip"] = plot_df["deadhead_min"] / plot_df["selected_trips"]
    plot_df["break_per_trip"] = plot_df["break_min"] / plot_df["selected_trips"]
    plot_df["charge_per_ev"] = plot_df.apply(lambda r: r["charging_min"] / r["ev_blocks"] if r["ev_blocks"] else 0.0, axis=1)
    x = np.arange(len(plot_df))

    fig, axes = plt.subplots(3, 1, figsize=(13.6, 9.2), dpi=190, sharex=True)
    colors = ["#2f6db3", "#9b6a20", "#2d8a5f"]
    metrics = [
        ("deadhead_per_trip", "Deadhead min per trip", colors[0]),
        ("break_per_trip", "Paid-break min per trip", colors[1]),
        ("charge_per_ev", "Charging min per EV", colors[2]),
    ]
    for ax, (col, ylabel, color) in zip(axes, metrics):
        bars = ax.bar(x, plot_df[col], color=color, alpha=0.86, edgecolor="#334155", linewidth=0.5)
        ax.set_ylabel(ylabel, fontsize=10.5)
        ax.grid(axis="y", color="#d9dee7", linewidth=0.7, alpha=0.8)
        ax.set_axisbelow(True)
        top = max(plot_df[col].max(), 1)
        ax.set_ylim(0, top * 1.23)
        for bar, val in zip(bars, plot_df[col]):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + top * 0.025, f"{val:.1f}", ha="center", va="bottom", fontsize=7.5, rotation=0)
    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(plot_df["label"], rotation=32, ha="right", fontsize=8.6)
    fig.suptitle("Operational Resource Pressure in the Final Schedules", fontsize=14.5, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def make_efficiency_panel(df: pd.DataFrame, path: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    plot_df = df.copy()
    plot_df["label"] = plot_df["instance"].replace({"2lines 6 timeWindows": "2lines 6TW", "1line 6timeWindow": "1line 6TW", "Toy Example": "Toy"})
    plot_df["cost_per_trip"] = plot_df["objective"] / plot_df["selected_trips"]
    plot_df["trips_per_vehicle"] = plot_df["selected_trips"] / plot_df["total_blocks"]
    plot_df["ev_share_frac"] = plot_df["ev_share"] / 100.0
    x = np.arange(len(plot_df))

    fig, axes = plt.subplots(2, 1, figsize=(13.6, 7.4), dpi=190, sharex=True)
    bars = axes[0].bar(x, plot_df["cost_per_trip"], color="#4f6f8f", edgecolor="#334155", linewidth=0.5)
    axes[0].set_ylabel("Cost per selected trip", fontsize=10.5)
    axes[0].grid(axis="y", color="#d9dee7", linewidth=0.7, alpha=0.8)
    top = plot_df["cost_per_trip"].max()
    axes[0].set_ylim(0, top * 1.18)
    for bar, val in zip(bars, plot_df["cost_per_trip"]):
        axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + top * 0.025, f"{val:.2f}", ha="center", va="bottom", fontsize=7.5)

    scatter = axes[1].scatter(
        x,
        plot_df["trips_per_vehicle"],
        s=90 + plot_df["total_blocks"] * 7,
        c=plot_df["ev_share_frac"],
        cmap="YlGn",
        edgecolor="#334155",
        linewidth=0.8,
        vmin=0,
        vmax=1,
    )
    axes[1].plot(x, plot_df["trips_per_vehicle"], color="#9aa4b2", linewidth=1.0, zorder=0)
    axes[1].set_ylabel("Trips per vehicle", fontsize=10.5)
    axes[1].grid(axis="y", color="#d9dee7", linewidth=0.7, alpha=0.8)
    top = plot_df["trips_per_vehicle"].max()
    axes[1].set_ylim(0, top * 1.20)
    for xi, val in zip(x, plot_df["trips_per_vehicle"]):
        axes[1].text(xi, val + top * 0.035, f"{val:.1f}", ha="center", va="bottom", fontsize=7.6)
    cbar = fig.colorbar(scatter, ax=axes[1], pad=0.012)
    cbar.set_label("EV share", fontsize=9.5)
    cbar.ax.tick_params(labelsize=8)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(plot_df["label"], rotation=32, ha="right", fontsize=8.6)
    fig.suptitle("Efficiency Indicators in the Final Schedules", fontsize=14.5, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.955))
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
