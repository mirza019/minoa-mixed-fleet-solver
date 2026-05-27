#!/usr/bin/env python3
"""Create thesis figures that explain MINOA constraints and all-instance results."""

from __future__ import annotations

from pathlib import Path
from textwrap import fill


ROWS = [
    # instance, cost, trips, vehicles, ev_share, deadhead_min, break_min, charge_min,
    # fixed_cost, break_cost, pull_cost, co2_cost
    ("Small", 162.44, 48, 2, 0.0, 42.0, 240.0, 0.0, 154.0, 7.66, 0.25, 0.53),
    ("Medium", 371.35, 139, 5, 100.0, 752.0, 1717.0, 391.0, 350.0, 16.84, 4.51, 0.0),
    ("Large", 1165.24, 260, 15, 33.33, 2139.0, 2448.0, 518.0, 1120.0, 29.65, 12.83, 2.75),
    ("Toy", 488.44, 68, 6, 83.33, 463.0, 913.0, 126.0, 470.0, 15.54, 2.78, 0.12),
    ("1line", 323.63, 102, 4, 50.0, 426.0, 1389.0, 245.0, 294.0, 26.22, 2.56, 0.85),
    ("1line 6TW", 530.77, 112, 7, 42.86, 1432.0, 1315.0, 349.0, 518.0, 2.35, 8.59, 1.83),
    ("2lines", 910.15, 204, 12, 41.67, 3218.0, 2710.0, 717.0, 889.0, -1.42, 19.31, 3.27),
    ("2lines 6TW", 626.24, 204, 8, 37.50, 1150.0, 2400.0, 215.0, 595.0, 22.09, 6.90, 2.24),
    ("3lines", 999.99, 306, 12, 33.33, 1258.0, 3654.0, 351.0, 896.0, 93.0, 7.55, 3.44),
    ("3lines tri.", 941.41, 306, 12, 41.67, 1734.0, 2967.0, 651.0, 889.0, 38.80, 10.40, 3.20),
    ("5lines", 1669.01, 510, 20, 25.0, 2110.0, 6485.0, 956.0, 1505.0, 145.67, 12.66, 5.68),
    ("8lines", 2617.76, 819, 33, 15.15, 5036.0, 5552.0, 257.0, 2506.0, 69.04, 30.22, 12.51),
]


RULES = [
    ("Headway", "timing"),
    ("First/last trip", "timing"),
    ("Trip covered once", "flow"),
    ("Compatible chaining", "flow"),
    ("Depot deadhead", "flow"),
    ("EV autonomy", "energy"),
    ("Charging time", "energy"),
    ("Parking capacity", "capacity"),
    ("Charging capacity", "capacity"),
    ("Vehicle availability", "fleet"),
    ("Official cost", "cost"),
]

LAYERS = ["Timetable", "Path cover", "EV/charge", "Capacity", "Validator", "Report"]

# 0 = not handled in this layer, 1 = constructed/checked internally, 2 = external check/report.
COVERAGE = [
    [1, 0, 0, 0, 2, 2],
    [1, 0, 0, 0, 2, 2],
    [0, 1, 0, 0, 2, 2],
    [0, 1, 0, 0, 2, 2],
    [0, 1, 0, 0, 2, 2],
    [0, 0, 1, 0, 2, 2],
    [0, 0, 1, 1, 2, 2],
    [0, 0, 0, 1, 2, 2],
    [0, 0, 1, 1, 2, 2],
    [0, 0, 1, 0, 2, 2],
    [0, 0, 0, 0, 2, 2],
]


def main() -> None:
    out_dir = Path("FAU_Thesis_temp/figures")
    out_dir.mkdir(parents=True, exist_ok=True)
    make_path_cover_workflow(out_dir / "fig18_graph_path_cover_explained.png")
    make_ev_workflow(out_dir / "fig23_ev_feasibility_workflow.png")
    make_constraint_matrix(out_dir / "fig24_constraint_coverage_matrix.png")
    make_resource_pressure(out_dir / "fig25_all_instance_resource_pressure.png")
    make_efficiency_panel(out_dir / "fig26_all_instance_efficiency_panel.png")
    make_cost_audit_panel(out_dir / "fig27_all_instance_cost_audit.png")


def make_constraint_matrix(path: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import ListedColormap

    matrix = np.array(COVERAGE)
    fig, ax = plt.subplots(figsize=(11.2, 6.4), dpi=180)
    cmap = ListedColormap(["#f1f3f5", "#4c78a8", "#f2b447"])
    ax.imshow(matrix, cmap=cmap, vmin=0, vmax=2, aspect="auto")

    ax.set_title("MINOA Rule Coverage by Solver Layer", pad=18)
    ax.set_xticks(range(len(LAYERS)), LAYERS, rotation=30, ha="right")
    ax.set_yticks(range(len(RULES)), [name for name, _ in RULES])

    for r in range(matrix.shape[0]):
        for c in range(matrix.shape[1]):
            label = "" if matrix[r, c] == 0 else ("I" if matrix[r, c] == 1 else "V")
            ax.text(c, r, label, ha="center", va="center", fontsize=9, weight="bold")

    for idx, (_, group) in enumerate(RULES):
        ax.text(len(LAYERS) - 0.05, idx, group, va="center", ha="left", fontsize=8, color="#495057")

    ax.set_xlim(-0.5, len(LAYERS) + 1.65)
    ax.spines[:].set_visible(False)
    ax.tick_params(axis="both", length=0)
    fig.text(
        0.5,
        0.035,
        "I = internally constructed or checked, V = independently checked or reported after output generation",
        ha="center",
        fontsize=9,
        color="#343a40",
    )
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    fig.savefig(path)
    plt.close(fig)


def make_path_cover_workflow(path: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Circle

    fig, ax = plt.subplots(figsize=(13.5, 8.5), dpi=180)
    ax.set_xlim(0, 13.5)
    ax.set_ylim(0, 8.5)
    ax.axis("off")
    ax.text(6.75, 8.05, "Method Flow and Path-Cover Graph Idea", ha="center", fontsize=18, weight="bold")
    ax.text(
        6.75,
        7.72,
        "The upper panel shows the solver layers. The lower panel shows how compatible trip arcs become vehicle blocks.",
        ha="center",
        fontsize=10,
        color="#5d6a78",
    )

    boxes = [
        (0.45, 6.05, "1", "MINOA input", "trips, fleet,\nnodes, costs"),
        (3.35, 6.05, "2", "Timetable variants", "headway-feasible\ntrip selections"),
        (6.25, 6.05, "3", "Compatibility graph", "trip nodes and\ncontinuation arcs"),
        (9.15, 6.05, "4", "Weighted path cover", "paths become\nvehicle blocks"),
        (9.15, 4.55, "5", "ICE/EV assignment", "fleet limits and\nEV autonomy"),
        (6.25, 4.55, "6", "Charging insertion", "break windows and\nnode capacity"),
        (3.35, 4.55, "7", "External validation", "official input-output\ncheck"),
    ]
    for x, y, num, title, body in boxes:
        _draw_box(ax, x, y, 2.55, 1.0, num, title, body)
    for start, end in [
        ((3.0, 6.55), (3.30, 6.55)),
        ((5.90, 6.55), (6.20, 6.55)),
        ((8.80, 6.55), (9.10, 6.55)),
        ((10.43, 6.05), (10.43, 5.60)),
        ((9.15, 5.05), (8.85, 5.05)),
        ((6.25, 5.05), (5.95, 5.05)),
    ]:
        _arrow(ax, start, end)

    ax.plot([0.8, 12.7], [4.05, 4.05], color="#d0d7de", linewidth=1.0)
    ax.text(0.85, 3.72, "Path-cover example", fontsize=13, weight="bold", color="#111827")
    ax.text(0.85, 3.45, "Selected arcs create two disjoint paths. Each path is one vehicle block.", fontsize=9, color="#5d6a78")

    trips = [
        (1.15, 2.35, "Trip 1\n08:00-08:30"),
        (3.85, 2.35, "Trip 2\n08:42-09:10"),
        (6.55, 2.35, "Trip 3\n09:25-09:55"),
        (3.85, 1.35, "Trip 4\n08:50-09:20"),
        (6.55, 1.35, "Trip 5\n09:35-10:05"),
    ]
    for x, y, label in trips:
        _draw_plain_box(ax, x, y, 1.85, 0.62, label)
    _arrow(ax, (3.0, 2.66), (3.82, 2.66), "selected arc")
    _arrow(ax, (5.70, 2.66), (6.52, 2.66), "selected arc")
    _arrow(ax, (5.70, 1.66), (6.52, 1.66), "selected arc")
    _arrow(ax, (3.0, 2.32), (3.82, 1.72), "feasible but not chosen", dashed=True)

    result = FancyBboxPatch(
        (1.15, 0.25),
        10.9,
        0.72,
        boxstyle="round,pad=0.035,rounding_size=0.15",
        linewidth=1.1,
        edgecolor="#8ec5ff",
        facecolor="#eef6ff",
    )
    ax.add_patch(result)
    ax.text(6.6, 0.72, "Path-cover result", ha="center", va="center", fontsize=12, weight="bold")
    ax.text(
        6.6,
        0.44,
        "Path 1: Trip 1 -> Trip 2 -> Trip 3 = vehicle block 1     |     Path 2: Trip 4 -> Trip 5 = vehicle block 2",
        ha="center",
        va="center",
        fontsize=9,
        color="#1f2937",
    )

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def make_ev_workflow(path: Path) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(13.5, 7.3), dpi=180)
    ax.set_xlim(0, 13.5)
    ax.set_ylim(0, 7.3)
    ax.axis("off")
    ax.text(6.75, 6.85, "EV Feasibility and Charging-Capacity Workflow", ha="center", fontsize=18, weight="bold")
    ax.text(
        6.75,
        6.52,
        "This local workflow tests whether a constructed vehicle block can be operated by an electric bus.",
        ha="center",
        fontsize=10,
        color="#5d6a78",
    )

    top = [
        (0.55, 5.10, "1", "Candidate block", "ordered trips,\ndeadheads, waits"),
        (3.50, 5.10, "2", "Energy simulation", "subtract trip and\ndeadhead consumption"),
        (6.45, 5.10, "3", "Break-window search", "find idle time at\ncharging-capable nodes"),
        (9.40, 5.10, "4", "Insert charging", "only if time and\nnode allow it"),
    ]
    bottom = [
        (1.90, 3.12, "5", "Capacity check", "reserve parking and\ncharging capacity"),
        (5.35, 3.12, "6", "EV accepted", "autonomy non-negative\nand capacity valid"),
        (8.80, 3.12, "7", "ICE fallback", "if EV infeasible,\nkeep conventional block"),
    ]
    for item in top + bottom:
        color = "#f28e2b" if item[2] == "3" else ("#2a9d8f" if item[2] in {"4", "5", "6"} else ("#e15759" if item[2] == "7" else "#2563eb"))
        _draw_box(ax, item[0], item[1], 2.65, 0.95, item[2], item[3], item[4], badge_color=color)

    for start, end in [
        ((3.20, 5.57), (3.47, 5.57)),
        ((6.15, 5.57), (6.42, 5.57)),
        ((9.10, 5.57), (9.37, 5.57)),
        ((10.72, 5.10), (10.72, 4.35)),
        ((10.72, 4.35), (3.23, 4.35)),
        ((3.23, 4.35), (3.23, 4.07)),
        ((4.55, 3.59), (5.32, 3.59)),
        ((8.00, 3.59), (8.77, 3.59)),
    ]:
        _arrow(ax, start, end)

    ax.text(4.95, 3.86, "feasible", fontsize=8, color="#2a9d8f", ha="center")
    ax.text(8.40, 3.86, "not feasible", fontsize=8, color="#e15759", ha="center")

    _draw_formula_panel(
        ax,
        (2.25, 0.65),
        9.0,
        1.25,
        "Feasibility logic",
        r"$b_{a+1}=\min\{B,\; b_a-q_a+\rho_s c_a\},\quad b_a\geq 0$",
        "Charging is accepted only when node parking and charging capacities are not exceeded.",
    )

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def make_resource_pressure(path: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    labels = [row[0] for row in ROWS]
    values = np.array(
        [
            [row[5] / row[2], row[6] / row[2], row[7] / max(row[2], 1), row[4] / 100.0]
            for row in ROWS
        ]
    )
    col_labels = ["Deadhead/trip", "Break/trip", "Charge/trip", "EV share"]
    norm = values.copy()
    for c in range(3):
        norm[:, c] = norm[:, c] / max(norm[:, c].max(), 1e-9)

    fig, ax = plt.subplots(figsize=(10.8, 6.9), dpi=180)
    image = ax.imshow(norm, cmap="YlGnBu", aspect="auto", vmin=0, vmax=1)
    ax.set_title("Constraint Pressure Indicators Across All Senior Instances", pad=14)
    ax.set_xticks(range(len(col_labels)), col_labels)
    ax.set_yticks(range(len(labels)), labels)

    for r, row in enumerate(values):
        for c, value in enumerate(row):
            text = f"{value:.1f}" if c < 3 else f"{value * 100:.0f}%"
            color = "white" if norm[r, c] > 0.62 else "#1f2933"
            ax.text(c, r, text, ha="center", va="center", fontsize=8, color=color, weight="bold")

    ax.set_xlabel("Indicators derived from validator-accepted schedules")
    cbar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("Relative pressure within each column")
    ax.spines[:].set_visible(False)
    ax.tick_params(axis="both", length=0)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def make_efficiency_panel(path: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    labels = [row[0] for row in ROWS]
    costs_per_trip = [row[1] / row[2] for row in ROWS]
    trips_per_vehicle = [row[2] / row[3] for row in ROWS]
    ev_share = [row[4] for row in ROWS]
    x = np.arange(len(labels))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11.5, 8.2), dpi=180, sharex=True)
    bars = ax1.bar(x, costs_per_trip, color="#26736d", width=0.62)
    ax1.set_title("All-Instance Efficiency View")
    ax1.set_ylabel("Cost per selected trip")
    ax1.grid(axis="y", color="#dde2e6", linewidth=0.8)
    ax1.spines[["top", "right"]].set_visible(False)
    for bar, value in zip(bars, costs_per_trip):
        ax1.text(bar.get_x() + bar.get_width() / 2, value + 0.08, f"{value:.2f}", ha="center", fontsize=7)

    scatter = ax2.scatter(
        x,
        trips_per_vehicle,
        s=[70 + share * 1.2 for share in ev_share],
        c=ev_share,
        cmap="viridis",
        edgecolor="#263238",
        linewidth=0.5,
    )
    ax2.plot(x, trips_per_vehicle, color="#adb5bd", linewidth=1.0, zorder=0)
    ax2.set_ylabel("Trips per used vehicle")
    ax2.set_xticks(x, labels, rotation=35, ha="right")
    ax2.grid(axis="y", color="#dde2e6", linewidth=0.8)
    ax2.spines[["top", "right"]].set_visible(False)
    for idx, value in enumerate(trips_per_vehicle):
        ax2.text(idx, value + 0.55, f"{value:.1f}", ha="center", fontsize=7)
    cbar = fig.colorbar(scatter, ax=ax2, fraction=0.025, pad=0.02)
    cbar.set_label("EV share (%)")

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def make_cost_audit_panel(path: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    labels = [row[0] for row in ROWS]
    total = np.array([row[1] for row in ROWS])
    fixed = np.array([row[8] for row in ROWS])
    pull = np.array([row[10] for row in ROWS])
    co2 = np.array([row[11] for row in ROWS])
    other = total - fixed
    fixed_share = fixed / total * 100.0
    x = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(12.0, 6.0), dpi=180)
    bars_fixed = ax.bar(x, fixed, color="#536878", label="Fixed vehicle cost")
    bars_other = ax.bar(x, other, bottom=fixed, color="#f2b447", label="Other official cost")

    ax.set_title("Official Cost Audit Across All Senior Instances")
    ax.set_ylabel("Official VS cost")
    ax.set_xticks(x, labels, rotation=35, ha="right")
    ax.grid(axis="y", color="#dde2e6", linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper left")

    for idx, value in enumerate(total):
        ax.text(idx, value + max(total) * 0.012, f"{value:.0f}", ha="center", fontsize=7)
        ax.text(idx, fixed[idx] * 0.52, f"{fixed_share[idx]:.0f}% fixed", ha="center", fontsize=6, color="white")
        ax.text(
            idx,
            fixed[idx] + max(other[idx], 0.0) * 0.45,
            f"P {pull[idx]:.1f}\nCO2 {co2[idx]:.1f}",
            ha="center",
            va="center",
            fontsize=6,
            color="#343a40",
        )

    fig.text(
        0.01,
        0.01,
        "Other official cost contains break, pull-in/out, and CO2 terms. Pull and CO2 labels are shown because they are read directly from input coefficients.",
        fontsize=8,
        color="#495057",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path)
    plt.close(fig)


def _draw_box(ax, x, y, w, h, num, title, body, badge_color="#2563eb") -> None:
    from matplotlib.patches import Circle, FancyBboxPatch

    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.025,rounding_size=0.12",
        linewidth=1.2,
        edgecolor="#1f2937",
        facecolor="#ffffff",
    )
    ax.add_patch(box)
    badge = Circle((x + 0.45, y + h + 0.03), 0.25, facecolor=badge_color, edgecolor="white", linewidth=1.0)
    ax.add_patch(badge)
    ax.text(x + 0.45, y + h + 0.03, str(num), ha="center", va="center", color="white", weight="bold", fontsize=9)
    ax.text(x + w / 2, y + h * 0.64, title, ha="center", va="center", fontsize=11, weight="bold", color="#111827")
    ax.text(x + w / 2, y + h * 0.30, body, ha="center", va="center", fontsize=8.2, color="#5d6a78", linespacing=0.95)


def _draw_plain_box(ax, x, y, w, h, label) -> None:
    from matplotlib.patches import FancyBboxPatch

    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.1",
        linewidth=1.0,
        edgecolor="#1f2937",
        facecolor="#f8fafc",
    )
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=8.5, color="#1f2937", linespacing=0.95)


def _draw_formula_panel(ax, xy, w, h, title, formula, body) -> None:
    from matplotlib.patches import FancyBboxPatch

    x, y = xy
    panel = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.035,rounding_size=0.15",
        linewidth=1.1,
        edgecolor="#8ec5ff",
        facecolor="#eef6ff",
    )
    ax.add_patch(panel)
    ax.text(x + w / 2, y + h * 0.72, title, ha="center", va="center", fontsize=12, weight="bold", color="#111827")
    ax.text(x + w / 2, y + h * 0.45, formula, ha="center", va="center", fontsize=11, color="#1f2937")
    ax.text(x + w / 2, y + h * 0.20, body, ha="center", va="center", fontsize=8.6, color="#5d6a78")


def _arrow(ax, start, end, label=None, dashed=False) -> None:
    from matplotlib.patches import FancyArrowPatch

    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=1.2,
        linestyle="--" if dashed else "-",
        color="#1f2937",
        shrinkA=0,
        shrinkB=0,
    )
    ax.add_patch(arrow)
    if label:
        mx = (start[0] + end[0]) / 2
        my = (start[1] + end[1]) / 2
        ax.text(mx, my + 0.12, label, ha="center", va="bottom", fontsize=7.5, color="#5d6a78")


if __name__ == "__main__":
    main()
