#!/usr/bin/env python3
"""Create thesis framework figures for the MINOA solver."""

from __future__ import annotations

from pathlib import Path


def main() -> None:
    output_dir = Path("FAU_Thesis_temp/figures")
    output_dir.mkdir(parents=True, exist_ok=True)
    make_computational_framework(output_dir / "fig33_computational_framework.png")
    make_output_validation_visualization(output_dir / "fig34_output_validation_visualization.png")
    print(output_dir / "fig33_computational_framework.png")
    print(output_dir / "fig34_output_validation_visualization.png")


def make_computational_framework(path: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

    fig, ax = plt.subplots(figsize=(13.8, 10.0), dpi=180)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 14)
    ax.axis("off")

    title_color = "#203044"
    ax.text(
        7,
        13.45,
        "Computational Framework for the MINOA Multi-Start Path-Cover Solver",
        ha="center",
        va="center",
        fontsize=20,
        fontweight="bold",
        color=title_color,
    )

    layer_specs = [
        (10.65, 2.10, "#e8f1ff", "#4472b9", "1. Benchmark Input and Configuration"),
        (7.85, 2.65, "#e8f6ed", "#3c8b5b", "2. Shared Data and Graph Preprocessing"),
        (4.75, 2.65, "#fff3df", "#c87b24", "3. Algorithmic Solution Layer"),
        (1.55, 2.35, "#fdeaea", "#b65050", "4. Output, Validation, and Result Analysis"),
    ]

    for y, h, face, edge, title in layer_specs:
        rounded(ax, 0.55, y, 12.9, h, face, edge, lw=1.6, radius=0.18)
        ax.text(0.95, y + h - 0.42, title, ha="left", va="center", fontsize=13.5, fontweight="bold", color=edge)

    # Layer 1
    box(ax, 1.25, 11.05, 3.1, 1.0, "Senior instances", "Small, Medium, Large\nand 9 additional files", "#4472b9")
    box(ax, 5.05, 11.05, 3.1, 1.0, "Problem rules", "headways, vehicle blocks,\ncharging, capacity, cost", "#4472b9")
    box(ax, 8.85, 11.05, 3.8, 1.0, "Run configuration", "algorithm name, scope,\nvariant count, time limit", "#4472b9")

    # Layer 2
    box(ax, 1.15, 8.45, 3.35, 1.05, "Timetable objects", "directions, candidate trips,\nmain-stop arrivals, headways", "#3c8b5b")
    box(ax, 5.00, 8.45, 3.35, 1.05, "Infrastructure objects", "nodes, depot movements,\nparking and charging capacities", "#3c8b5b")
    box(ax, 8.85, 8.45, 3.35, 1.05, "Compatibility graph", r"$G=(T_S,A)$ with in-line" + "\nand depot-bridge arcs", "#3c8b5b")
    rounded(ax, 1.15, 7.95, 11.05, 0.48, "#ffffff", "#3c8b5b", lw=1.1, radius=0.10)
    ax.text(
        6.68,
        8.18,
        "The same selected-trip graph is reused by greedy, path-cover, weighted path-cover, and multi-start variants.",
        ha="center",
        va="center",
        fontsize=10.7,
        color="#4f5f70",
        style="italic",
    )

    # Layer 3
    box(ax, 0.95, 5.40, 2.75, 1.0, "Greedy", "earliest uncovered trip\nlocal successor choice", "#c87b24")
    box(ax, 4.00, 5.40, 2.75, 1.0, "Path-cover", "maximum-cardinality\nbipartite matching", "#c87b24")
    box(ax, 7.05, 5.40, 2.75, 1.0, "Weighted path-cover", "matching with deadhead,\nwaiting and break scores", "#c87b24")
    box(ax, 10.10, 5.40, 2.75, 1.0, "Multi-start path-cover", "many timetable variants\nbest complete schedule", "#c87b24")
    rounded(ax, 2.2, 4.93, 9.2, 0.42, "#ffffff", "#c87b24", lw=1.1, radius=0.10)
    ax.text(
        6.8,
        5.13,
        "EV/ICE assignment and charging insertion are applied after block construction under autonomy and capacity limits.",
        ha="center",
        va="center",
        fontsize=10.4,
        color="#4f5f70",
        style="italic",
    )

    # Layer 4
    box(ax, 1.25, 2.10, 3.1, 0.95, "MINOA JSON output", "selected timetable and\nvehicleBlockList", "#b65050")
    box(ax, 5.05, 2.10, 3.1, 0.95, "Desktop validator", "feasibility check and\nreported objective", "#b65050")
    box(ax, 8.85, 2.10, 3.8, 0.95, "Thesis analysis", "tables, graph statistics,\nfigures and discussion", "#b65050")

    # Down arrows
    for x, y0, y1 in [(7.0, 10.65, 10.12), (7.0, 7.85, 7.30), (7.0, 4.75, 4.18)]:
        arrow(ax, x, y0, x, y1, "#7b8794")

    # Within layer arrows
    arrow(ax, 4.35, 11.55, 4.95, 11.55, "#7b8794")
    arrow(ax, 8.15, 11.55, 8.75, 11.55, "#7b8794")
    arrow(ax, 4.50, 8.95, 4.90, 8.95, "#7b8794")
    arrow(ax, 8.35, 8.95, 8.75, 8.95, "#7b8794")
    arrow(ax, 3.70, 5.90, 3.92, 5.90, "#7b8794")
    arrow(ax, 6.75, 5.90, 6.97, 5.90, "#7b8794")
    arrow(ax, 9.80, 5.90, 10.02, 5.90, "#7b8794")
    arrow(ax, 4.35, 2.58, 4.95, 2.58, "#7b8794")
    arrow(ax, 8.15, 2.58, 8.75, 2.58, "#7b8794")

    ax.text(
        7,
        0.72,
        "The framework separates construction from evaluation: validator checks are applied after a complete output file is generated.",
        ha="center",
        va="center",
        fontsize=11.2,
        color="#4f5f70",
    )

    fig.tight_layout(pad=0.3)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def make_output_validation_visualization(path: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

    fig, ax = plt.subplots(figsize=(13.5, 7.0), dpi=180)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis("off")

    ax.text(
        7,
        7.35,
        "Output, Validation, and Visualization Workflow",
        ha="center",
        va="center",
        fontsize=19,
        fontweight="bold",
        color="#203044",
    )

    # Main pipeline
    labels = [
        ("Solver candidate", "timetable variant,\nvehicle blocks,\nEV/ICE assignment", "#4472b9"),
        ("JSON writer", "MINOA-compliant\ninput/output structure", "#3c8b5b"),
        ("Validator run", "feasibility, vehicle count,\nobjective value", "#b65050"),
        ("Metrics parser", "cost, EV share,\ndeadhead, charge", "#c87b24"),
        ("Thesis artefacts", "tables, figures,\nappendix commands", "#6b5b95"),
    ]
    xs = [0.65, 3.30, 5.95, 8.60, 11.25]
    for x, (title, sub, color) in zip(xs, labels):
        box(ax, x, 4.55, 2.1, 1.35, title, sub, color)
    for x1, x2 in zip(xs[:-1], xs[1:]):
        arrow(ax, x1 + 2.1, 5.22, x2 - 0.08, 5.22, "#7b8794")

    # Visualization outputs
    rounded(ax, 0.65, 1.00, 12.72, 2.55, "#f7f9fb", "#7b8794", lw=1.25, radius=0.18)
    ax.text(1.00, 3.24, "Visualization and explanation layer", ha="left", va="center", fontsize=13, fontweight="bold", color="#203044")
    viz = [
        ("Compatibility graph", "feasible continuations\nand path-cover idea"),
        ("Matching view", "left/right trip copies\nmatched arcs save vehicles"),
        ("Vehicle journey", "EV and ICE activity\ntimelines with costs"),
        ("Result plots", "fleet mix, cost audit,\nresource pressure"),
    ]
    for i, (title, sub) in enumerate(viz):
        x = 1.05 + i * 3.05
        box(ax, x, 1.55, 2.55, 1.1, title, sub, "#4f6f8f")
        arrow(ax, xs[min(i + 1, len(xs) - 1)] + 1.05, 4.55, x + 1.27, 2.70, "#a0a9b4", style="dashed")

    ax.text(
        7,
        0.45,
        "The visualizations are not separate experiments; they explain the same validator-accepted outputs from graph, vehicle, and cost perspectives.",
        ha="center",
        va="center",
        fontsize=10.8,
        color="#4f5f70",
    )

    fig.tight_layout(pad=0.3)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def rounded(ax, x: float, y: float, w: float, h: float, face: str, edge: str, lw: float = 1.2, radius: float = 0.15) -> None:
    from matplotlib.patches import FancyBboxPatch

    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.02,rounding_size={radius}",
        linewidth=lw,
        edgecolor=edge,
        facecolor=face,
    )
    ax.add_patch(patch)


def box(ax, x: float, y: float, w: float, h: float, title: str, subtitle: str, color: str) -> None:
    rounded(ax, x, y, w, h, "#ffffff", color, lw=1.3, radius=0.13)
    ax.text(x + w / 2, y + h * 0.62, title, ha="center", va="center", fontsize=11.3, fontweight="bold", color="#1f2937")
    ax.text(x + w / 2, y + h * 0.30, subtitle, ha="center", va="center", fontsize=8.8, color="#516173", style="italic", linespacing=1.35)


def arrow(ax, x1: float, y1: float, x2: float, y2: float, color: str, style: str = "solid") -> None:
    from matplotlib.patches import FancyArrowPatch

    ax.add_patch(
        FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle="-|>",
            mutation_scale=13,
            linewidth=1.2,
            linestyle=style,
            color=color,
        )
    )


if __name__ == "__main__":
    main()
