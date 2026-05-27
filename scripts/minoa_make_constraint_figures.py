#!/usr/bin/env python3
"""Create thesis figures that explain MINOA constraints and all-instance results."""

from __future__ import annotations

from pathlib import Path


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

    ax.set_title("MINOA Rule Coverage by Solver Layer", pad=14)
    ax.set_xticks(range(len(LAYERS)), LAYERS, rotation=30, ha="right")
    ax.set_yticks(range(len(RULES)), [name for name, _ in RULES])

    for r in range(matrix.shape[0]):
        for c in range(matrix.shape[1]):
            label = "" if matrix[r, c] == 0 else ("I" if matrix[r, c] == 1 else "V")
            ax.text(c, r, label, ha="center", va="center", fontsize=9, weight="bold")

    for idx, (_, group) in enumerate(RULES):
        ax.text(len(LAYERS) - 0.05, idx, group, va="center", ha="left", fontsize=8, color="#495057")

    ax.text(
        0.0,
        -1.35,
        "I = internally constructed or checked, V = independently checked or reported after output generation",
        fontsize=9,
        color="#343a40",
    )
    ax.set_xlim(-0.5, len(LAYERS) + 1.65)
    ax.spines[:].set_visible(False)
    ax.tick_params(axis="both", length=0)
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


if __name__ == "__main__":
    main()
