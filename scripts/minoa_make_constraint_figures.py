#!/usr/bin/env python3
"""Create thesis figures that explain MINOA constraints and all-instance results."""

from __future__ import annotations

import csv
from pathlib import Path
import json

ALGORITHM_TOTALS_CSV = Path("outputs/minoa/algorithm_study/algorithm_totals.csv")
ALL_INSTANCE_EVIDENCE_MD = Path("outputs/minoa/professor_all/evidence_all_instances_report.md")
FINAL_RESULTS_CSV = Path("outputs/minoa/final_archive/final_results.csv")


ROWS = [
    # instance, cost, trips, vehicles, ev_share, deadhead_min, break_min, charge_min,
    # fixed_cost, break_cost, pull_cost, co2_cost
    ("Small", 162.44, 48, 2, 0.0, 42.0, 240.0, 0.0, 154.0, 7.69, 0.25, 0.50),
    ("Medium", 371.35, 139, 5, 100.0, 752.0, 1717.0, 391.0, 350.0, 16.84, 4.51, 0.0),
    ("Large", 1163.35, 260, 15, 33.33, 2600.0, 2520.0, 505.0, 1120.0, 25.79, 15.60, 1.96),
    ("Toy", 488.44, 68, 6, 83.33, 463.0, 913.0, 126.0, 470.0, 15.58, 2.78, 0.08),
    ("1line", 323.63, 102, 4, 50.0, 426.0, 1389.0, 245.0, 294.0, 26.38, 2.56, 0.70),
    ("1line 6TW", 530.77, 112, 7, 42.86, 1432.0, 1315.0, 349.0, 518.0, 3.02, 8.59, 1.16),
    ("2lines", 910.15, 204, 12, 41.67, 3218.0, 2710.0, 717.0, 889.0, 0.00, 19.31, 1.85),
    ("2lines 6TW", 626.24, 204, 8, 37.50, 1150.0, 2400.0, 215.0, 595.0, 22.51, 6.90, 1.83),
    ("3lines", 999.99, 306, 12, 33.33, 1258.0, 3654.0, 351.0, 896.0, 93.62, 7.55, 2.83),
    ("3lines tri.", 941.41, 306, 12, 41.67, 1734.0, 2967.0, 651.0, 889.0, 39.48, 10.40, 2.52),
    ("5lines", 1669.01, 510, 20, 25.0, 2110.0, 6485.0, 956.0, 1505.0, 146.58, 12.66, 4.77),
    ("8lines", 2617.76, 819, 33, 15.15, 5036.0, 5552.0, 257.0, 2506.0, 71.78, 30.22, 9.77),
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
    ("Validated cost", "cost"),
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


def _read_csv_dicts(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _parse_markdown_table(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    table_lines = [line for line in lines if line.strip().startswith("|")]
    if len(table_lines) < 3:
        return []
    header = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == len(header):
            rows.append(dict(zip(header, cells)))
    return rows


def _float_cell(row: dict[str, str], key: str, default: float = 0.0) -> float:
    value = row.get(key, "")
    try:
        return float(value.replace(",", ""))
    except ValueError:
        return default


def _display_instance(name: str) -> str:
    return {
        "Toy Example": "Toy",
        "1line 6timeWindow": "1line 6TW",
        "2lines 6 timeWindows": "2lines 6TW",
        "3linesTriangle": "3lines tri.",
        "8lines": "8lines",
        " 8lines": "8lines",
    }.get(name.strip(), name.strip())


def _result_rows() -> list[tuple[str, float, float, float, float, float, float, float, float, float, float, float]]:
    rows = _read_csv_dicts(FINAL_RESULTS_CSV)
    if rows:
        return [
            (
                _display_instance(row["instance"]),
                float(row["objective"]),
                float(row["selected_trips"]),
                float(row["total_blocks"]),
                float(row["ev_share"]),
                float(row["deadhead_min"]),
                float(row["break_min"]),
                float(row["charging_min"]),
                float(row["fixed_cost"]),
                float(row["break_cost"]),
                float(row["pull_cost"]),
                float(row["co2_cost"]),
            )
            for row in rows
        ]

    evidence_rows = _parse_markdown_table(ALL_INSTANCE_EVIDENCE_MD)
    if evidence_rows:
        parsed = []
        for row in evidence_rows:
            parsed.append(
                (
                    _display_instance(row.get("Instance", "")),
                    _float_cell(row, "Cost"),
                    _float_cell(row, "Trips"),
                    _float_cell(row, "Vehicles"),
                    _float_cell(row, "EV share (%)"),
                    _float_cell(row, "Deadhead min"),
                    _float_cell(row, "Break min"),
                    _float_cell(row, "Charge min"),
                    _float_cell(row, "Fixed"),
                    _float_cell(row, "Break cost"),
                    _float_cell(row, "Pull cost"),
                    _float_cell(row, "CO2 cost"),
                )
            )
        order = {row[0]: idx for idx, row in enumerate(ROWS)}
        return sorted(parsed, key=lambda row: order.get(row[0], 10_000))

    return ROWS


def _algorithm_totals() -> list[dict[str, float | str]]:
    rows = _read_csv_dicts(ALGORITHM_TOTALS_CSV)
    if rows:
        final_rows = _result_rows()
        final_cost = sum(row[1] for row in final_rows)
        final_vehicles = sum(row[3] for row in final_rows)
        final_ev = sum(row[3] * row[4] / 100.0 for row in final_rows)
        display = {
            "Greedy": "Greedy",
            "Path-cover": "Unweighted path cover",
            "Weighted path-cover": "Weighted path cover",
            "Multi-start path-cover": "Multi-start path cover",
        }
        totals = []
        for row in rows:
            label = display.get(row["Algorithm label"], row["Algorithm label"])
            if label == "Multi-start path cover" and final_rows:
                totals.append(
                    {
                        "label": label,
                        "cost": final_cost,
                        "vehicles": final_vehicles,
                        "ev": final_ev,
                    }
                )
                continue
            totals.append(
                {
                    "label": label,
                    "cost": float(row["Cost"]),
                    "vehicles": float(row["Vehicles"]),
                    "ev": float(row["EV"]),
                }
            )
        return totals
    return [
        {"label": "Greedy", "cost": 10993.20, "vehicles": 138.0, "ev": 46.0},
        {"label": "Unweighted path cover", "cost": 11027.94, "vehicles": 138.0, "ev": 39.0},
        {"label": "Weighted path cover", "cost": 10946.25, "vehicles": 138.0, "ev": 50.0},
        {"label": "Multi-start path cover", "cost": 10000.48, "vehicles": 126.0, "ev": 32.0},
    ]


def _cost_audit_rows() -> list[dict[str, float | str]]:
    return [
        {
            "label": row[0],
            "cost": row[1],
            "fixed": row[8],
            "remaining": max(row[1] - row[8], 0.0),
            "break": row[9],
            "pull": row[10],
            "co2": row[11],
            "residual": 0.0,
        }
        for row in _result_rows()
    ]


def main() -> None:
    out_dir = Path("FAU_Thesis_temp/figures")
    out_dir.mkdir(parents=True, exist_ok=True)
    make_archive_result_figures(out_dir)
    make_path_cover_workflow(out_dir / "fig18_graph_path_cover_explained.png")
    make_method_decision_layers(out_dir / "fig19_method_decision_layers.png")
    make_ev_workflow(out_dir / "fig23_ev_feasibility_workflow.png")
    make_final_solver_workflow(out_dir / "fig29_final_solver_workflow.png")
    make_constraint_matrix(out_dir / "fig24_constraint_coverage_matrix.png")
    make_resource_pressure(out_dir / "fig25_all_instance_resource_pressure.png")
    make_efficiency_panel(out_dir / "fig26_all_instance_efficiency_panel.png")
    make_cost_audit_panel(out_dir / "fig27_all_instance_cost_audit.png")
    make_vehicle_journey_figure(out_dir / "fig28_ev_ice_vehicle_journey.png")
    make_algorithm_gain_panel(out_dir / "fig40_algorithm_gain_panel.png")
    make_sml_improvement_heatmap(out_dir / "fig41_sml_algorithm_improvement.png")
    make_all_instance_tradeoff_dashboard(out_dir / "fig44_all_instance_tradeoff_dashboard.png")


def make_archive_result_figures(out_dir: Path) -> None:
    """Refresh older result figures from the final no-regression archive."""
    import matplotlib.pyplot as plt
    import numpy as np

    rows = _result_rows()
    labels = [row[0] for row in rows]
    headline = [row for row in rows if row[0] in {"Small", "Medium", "Large"}]
    hlabels = [row[0] for row in headline]

    def save(fig, path: Path) -> None:
        fig.tight_layout()
        fig.savefig(path, dpi=300)
        plt.close(fig)

    def label_bars(ax, bars, fmt="{:.2f}", dy=0.0) -> None:
        top = max((bar.get_height() for bar in bars), default=1.0)
        ax.set_ylim(top=top * 1.16 + dy)
        for bar in bars:
            value = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + top * 0.015,
                fmt.format(value),
                ha="center",
                va="bottom",
                fontsize=10.8,
            )

    # Fig. 01: headline costs.
    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=180)
    x = np.arange(len(headline))
    bars = ax.bar(x, [row[1] for row in headline], color="#4c78a8", width=0.55)
    ax.set_title("Best validated cost for headline instances", pad=14)
    ax.set_ylabel("Validator cost")
    ax.set_xticks(x, hlabels)
    ax.grid(axis="y", color="#e5e7eb")
    ax.spines[["top", "right"]].set_visible(False)
    label_bars(ax, bars)
    save(fig, out_dir / "fig01_cost_by_instance.png")

    # Fig. 02 and 03: headline fleet mix and EV share.
    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=180)
    ev = [round(row[3] * row[4] / 100.0) for row in headline]
    ice = [row[3] - e for row, e in zip(headline, ev)]
    ax.bar(x, ice, color="#6f7785", label="ICE vehicles")
    ax.bar(x, ev, bottom=ice, color="#2b8cbe", label="EV vehicles")
    ax.set_title("Fleet composition for headline instances", pad=14)
    ax.set_ylabel("Vehicles")
    ax.set_xticks(x, hlabels)
    ax.legend(frameon=False)
    ax.grid(axis="y", color="#e5e7eb")
    ax.spines[["top", "right"]].set_visible(False)
    for idx, row in enumerate(headline):
        ax.text(idx, row[3] + 0.2, f"{int(row[3])} veh", ha="center", fontsize=10.8)
    save(fig, out_dir / "fig02_fleet_mix.png")

    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=180)
    bars = ax.bar(x, [row[4] for row in headline], color="#2a9d8f", width=0.55)
    ax.set_title("Electric-vehicle share for headline instances", pad=14)
    ax.set_ylabel("EV share (%)")
    ax.set_ylim(0, 112)
    ax.set_xticks(x, hlabels)
    ax.grid(axis="y", color="#e5e7eb")
    ax.spines[["top", "right"]].set_visible(False)
    label_bars(ax, bars, fmt="{:.0f}%")
    save(fig, out_dir / "fig03_ev_share.png")

    # Fig. 04 and 05: operational components.
    fig, ax = plt.subplots(figsize=(10.5, 5.2), dpi=180)
    width = 0.24
    ax.bar(x - width, [row[5] for row in headline], width, label="Deadhead min", color="#4c78a8")
    ax.bar(x, [row[6] for row in headline], width, label="Break min", color="#f2b447")
    ax.bar(x + width, [row[7] for row in headline], width, label="Charge min", color="#2a9d8f")
    ax.set_title("Operational time components for headline instances", pad=14)
    ax.set_ylabel("Minutes")
    ax.set_xticks(x, hlabels)
    ax.legend(frameon=False, ncol=3)
    ax.grid(axis="y", color="#e5e7eb")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, out_dir / "fig04_operational_components.png")

    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=180)
    bars = ax.bar(x, [row[5] for row in headline], color="#4c78a8", width=0.55)
    ax.set_title("Deadhead minutes for headline instances", pad=14)
    ax.set_ylabel("Deadhead minutes")
    ax.set_xticks(x, hlabels)
    ax.grid(axis="y", color="#e5e7eb")
    ax.spines[["top", "right"]].set_visible(False)
    label_bars(ax, bars, fmt="{:.0f}")
    save(fig, out_dir / "fig05_deadhead_minutes.png")

    # Fig. 06 and 31: all-algorithm aggregate comparison.
    totals = _algorithm_totals()
    alg_labels = [str(row["label"]) for row in totals]
    short_alg_labels = ["Greedy", "Unweighted", "Weighted", "Multi-start"]
    fig, ax = plt.subplots(figsize=(11.2, 5.4), dpi=180)
    ax.bar(np.arange(len(totals)), [float(row["cost"]) for row in totals], color=["#9aa4b2", "#5b8cc0", "#26736d", "#b44949"])
    ax.set_title("All-instance validated cost by implemented algorithm", pad=14)
    ax.set_ylabel("Summed audited cost")
    ax.set_xticks(np.arange(len(totals)), alg_labels, rotation=18, ha="right")
    ax.grid(axis="y", color="#e5e7eb")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, out_dir / "fig06_algorithm_costs.png")

    fig, axes = plt.subplots(1, 3, figsize=(15.0, 5.6), dpi=190)
    metrics = [("Cost", "cost"), ("Vehicles", "vehicles"), ("EV vehicles", "ev")]
    for ax, (title, key) in zip(axes, metrics):
        values = [float(row[key]) for row in totals]
        ax.bar(np.arange(len(totals)), values, color="#4c78a8", width=0.58)
        ax.set_title(title, fontsize=13, weight="bold")
        ax.set_xticks(np.arange(len(totals)), short_alg_labels, rotation=0, ha="center", fontsize=10.8)
        ax.tick_params(axis="y", labelsize=10)
        ax.grid(axis="y", color="#e5e7eb")
        ax.spines[["top", "right"]].set_visible(False)
        for idx, value in enumerate(values):
            ax.text(idx, value + max(values) * 0.02, f"{value:.0f}", ha="center", fontsize=10.8)
    save(fig, out_dir / "fig31_all_algorithm_summary.png")

    # All-instance result figures.
    xi = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(12.8, 5.4), dpi=180)
    bars = ax.bar(xi, [row[1] for row in rows], color="#4c78a8")
    ax.set_title("Validated cost across all senior instances", pad=14)
    ax.set_ylabel("Validator cost")
    ax.set_xticks(xi, labels, rotation=36, ha="right")
    ax.grid(axis="y", color="#e5e7eb")
    ax.spines[["top", "right"]].set_visible(False)
    label_bars(ax, bars, fmt="{:.0f}")
    save(fig, out_dir / "fig12_additional_instance_costs.png")

    fig, ax = plt.subplots(figsize=(10.8, 5.4), dpi=180)
    ax.scatter([row[2] for row in rows], [row[3] for row in rows], s=55, color="#4c78a8", edgecolor="black", linewidth=0.4)
    for row in rows:
        ax.annotate(row[0], (row[2], row[3]), xytext=(4, 4), textcoords="offset points", fontsize=10.8)
    ax.set_title("Selected trips and used vehicles", pad=14)
    ax.set_xlabel("Selected trips")
    ax.set_ylabel("Used vehicles")
    ax.grid(color="#e5e7eb")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, out_dir / "fig13_additional_vehicle_scaling.png")

    fig, ax = plt.subplots(figsize=(12.8, 5.4), dpi=180)
    bars = ax.bar(xi, [row[4] for row in rows], color="#2a9d8f")
    ax.set_title("EV share across all senior instances", pad=14)
    ax.set_ylabel("EV share (%)")
    ax.set_xticks(xi, labels, rotation=36, ha="right")
    ax.set_ylim(0, 112)
    ax.grid(axis="y", color="#e5e7eb")
    ax.spines[["top", "right"]].set_visible(False)
    label_bars(ax, bars, fmt="{:.0f}%")
    save(fig, out_dir / "fig14_additional_ev_share.png")

    fig, ax = plt.subplots(figsize=(12.8, 5.4), dpi=180)
    bars = ax.bar(xi, [row[1] / row[2] for row in rows], color="#4c78a8")
    ax.set_title("Validated cost per selected trip", pad=14)
    ax.set_ylabel("Cost per selected trip")
    ax.set_xticks(xi, labels, rotation=36, ha="right")
    ax.grid(axis="y", color="#e5e7eb")
    ax.spines[["top", "right"]].set_visible(False)
    label_bars(ax, bars, fmt="{:.1f}")
    save(fig, out_dir / "fig15_cost_per_trip.png")

    fig, ax = plt.subplots(figsize=(12.8, 5.8), dpi=180)
    y = np.arange(len(rows))
    dead = [row[5] / row[2] for row in rows]
    brk = [row[6] / row[2] for row in rows]
    chg = [row[7] / row[2] for row in rows]
    ax.barh(y, dead, color="#4c78a8", label="Deadhead/trip")
    ax.barh(y, brk, left=dead, color="#f2b447", label="Break/trip")
    ax.barh(y, chg, left=np.array(dead) + np.array(brk), color="#2a9d8f", label="Charge/trip")
    ax.set_title("Operational minutes per selected trip", pad=14)
    ax.set_xlabel("Minutes per selected trip")
    ax.set_yticks(y, labels)
    ax.legend(frameon=False, ncol=3)
    ax.grid(axis="x", color="#e5e7eb")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, out_dir / "fig16_additional_operational_mix.png")

    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.0), dpi=180)
    panels = [
        (axes[0, 0], "Cost", [row[1] for row in rows]),
        (axes[0, 1], "Vehicles", [row[3] for row in rows]),
        (axes[1, 0], "EV share (%)", [row[4] for row in rows]),
        (axes[1, 1], "Trips per vehicle", [row[2] / row[3] for row in rows]),
    ]
    for ax, title, values in panels:
        ax.bar(xi, values, color="#4c78a8")
        ax.set_title(title)
        ax.set_xticks(xi, labels, rotation=45, ha="right", fontsize=10.8)
        ax.grid(axis="y", color="#e5e7eb")
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("All-instance result summary", y=1.01, weight="bold")
    save(fig, out_dir / "fig17_all_instance_summary.png")

    fig, ax = plt.subplots(figsize=(9.5, 5.4), dpi=180)
    ax.scatter([row[3] for row in headline], [row[1] for row in headline], s=80, color="#4c78a8", edgecolor="black")
    for row in headline:
        ax.annotate(row[0], (row[3], row[1]), xytext=(6, 4), textcoords="offset points", fontsize=10.8)
    ax.set_title("Headline cost-vehicle trade-off", pad=14)
    ax.set_xlabel("Used vehicles")
    ax.set_ylabel("Validator cost")
    ax.grid(color="#e5e7eb")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, out_dir / "fig20_cost_vehicle_tradeoff.png")

    fig, ax = plt.subplots(figsize=(10.2, 5.4), dpi=180)
    ax.scatter([row[4] for row in rows], [row[1] / row[2] for row in rows], s=55, color="#4c78a8", edgecolor="black", linewidth=0.4)
    for row in rows:
        ax.annotate(row[0], (row[4], row[1] / row[2]), xytext=(4, 4), textcoords="offset points", fontsize=10.8)
    ax.set_title("EV share and cost efficiency", pad=14)
    ax.set_xlabel("EV share (%)")
    ax.set_ylabel("Cost per selected trip")
    ax.grid(color="#e5e7eb")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, out_dir / "fig21_ev_share_cost_efficiency.png")

    fig, ax = plt.subplots(figsize=(12.8, 5.4), dpi=180)
    bars = ax.bar(xi, [row[2] / row[3] for row in rows], color="#26736d")
    ax.set_title("Vehicle productivity across all senior instances", pad=14)
    ax.set_ylabel("Selected trips per vehicle")
    ax.set_xticks(xi, labels, rotation=36, ha="right")
    ax.grid(axis="y", color="#e5e7eb")
    ax.spines[["top", "right"]].set_visible(False)
    label_bars(ax, bars, fmt="{:.1f}")
    save(fig, out_dir / "fig22_vehicle_productivity.png")


def make_method_decision_layers(path: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    fig, ax = plt.subplots(figsize=(13.0, 6.9), dpi=180)
    ax.set_xlim(0, 13.0)
    ax.set_ylim(0, 6.9)
    ax.axis("off")
    ax.text(6.5, 6.45, "Decision Layers in the Multi-Start Path-Cover Method", ha="center", fontsize=17, weight="bold")
    ax.text(
        6.5,
        6.08,
        "The method separates planning decisions into readable layers while passing information forward between them.",
        ha="center",
        fontsize=10.8,
        color="#5d6a78",
    )

    layers = [
        (0.45, 4.65, "1", "Timetable layer", "select trips under\nheadway rules", "#dbeafe", "#2563eb"),
        (3.35, 4.65, "2", "Graph layer", "build feasible\ncontinuation arcs", "#ecfdf5", "#26736d"),
        (6.25, 4.65, "3", "Path-cover layer", "solve matching and\nreconstruct blocks", "#fff7ed", "#c87b24"),
        (9.15, 4.65, "4", "Fleet layer", "choose ICE or EV\nfor each block", "#f5f3ff", "#6c55a3"),
        (3.35, 2.40, "5", "Energy layer", "simulate autonomy and\ninsert charging", "#eef6ff", "#4c78a8"),
        (6.25, 2.40, "6", "Capacity layer", "reserve parking and\ncharger resources", "#f0fdf4", "#2a9d8f"),
        (9.15, 2.40, "7", "Reporting layer", "write output and\ncompute audit values", "#fff1f2", "#b44949"),
    ]

    for x, y, num, title, body, face, edge in layers:
        box = FancyBboxPatch(
            (x, y),
            2.35,
            1.05,
            boxstyle="round,pad=0.035,rounding_size=0.12",
            linewidth=1.5,
            edgecolor=edge,
            facecolor=face,
        )
        ax.add_patch(box)
        ax.text(x + 0.22, y + 0.82, num, ha="center", va="center", color="white", fontsize=10.8, weight="bold",
                bbox=dict(boxstyle="circle,pad=0.28", facecolor=edge, edgecolor=edge))
        ax.text(x + 1.25, y + 0.68, title, ha="center", va="center", fontsize=11, weight="bold", color="#111827")
        ax.text(x + 1.25, y + 0.32, body, ha="center", va="center", fontsize=10.8, color="#4b5563")

    arrows = [
        ((2.82, 5.18), (3.30, 5.18)),
        ((5.72, 5.18), (6.20, 5.18)),
        ((8.62, 5.18), (9.10, 5.18)),
        ((10.32, 4.65), (10.32, 3.45)),
        ((9.15, 2.92), (8.62, 2.92)),
        ((6.25, 2.92), (5.72, 2.92)),
        ((4.52, 3.45), (4.52, 4.62)),
    ]
    for start, end in arrows:
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=13, linewidth=1.4, color="#374151"))

    ax.plot([1.6, 11.4], [1.35, 1.35], color="#d0d7de", linewidth=1.0)
    ax.text(6.5, 1.02, "Multi-start search repeats layers 1--7 with different timetable tie-breaking choices.", ha="center", fontsize=10.8)
    ax.text(
        6.5,
        0.62,
        r"The selected candidate is $h^*=\arg\min_{h\in H_{int}} C^{int,h}$; external validation audits the final output.",
        ha="center",
        fontsize=10.8,
        color="#1f2937",
    )

    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


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
            ax.text(c, r, label, ha="center", va="center", fontsize=10.8, weight="bold")

    for idx, (_, group) in enumerate(RULES):
        ax.text(len(LAYERS) - 0.05, idx, group, va="center", ha="left", fontsize=10.8, color="#495057")

    ax.set_xlim(-0.5, len(LAYERS) + 1.65)
    ax.spines[:].set_visible(False)
    ax.tick_params(axis="both", length=0)
    fig.text(
        0.5,
        0.035,
        "I = internally constructed or checked, V = independently checked or reported after output generation",
        ha="center",
        fontsize=10.8,
        color="#343a40",
    )
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    fig.savefig(path, dpi=300)
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
        fontsize=10.8,
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
    ax.text(0.85, 3.45, "Selected arcs create two disjoint paths. Each path is one vehicle block.", fontsize=10.8, color="#5d6a78")

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
        fontsize=10.8,
        color="#1f2937",
    )

    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def make_ev_workflow(path: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, FancyBboxPatch

    def draw_ev_box(ax, x, y, w, h, num, title, body, badge_color="#2563eb") -> None:
        box = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.04,rounding_size=0.14",
            linewidth=1.35,
            edgecolor="#1f2937",
            facecolor="#ffffff",
        )
        ax.add_patch(box)
        badge = Circle(
            (x + 0.50, y + h + 0.04),
            0.29,
            facecolor=badge_color,
            edgecolor="white",
            linewidth=1.1,
        )
        ax.add_patch(badge)
        ax.text(x + 0.50, y + h + 0.04, str(num), ha="center", va="center", color="white", weight="bold", fontsize=12.8)
        ax.text(x + w / 2, y + h * 0.65, title, ha="center", va="center", fontsize=13.2, weight="bold", color="#111827")
        ax.text(x + w / 2, y + h * 0.30, body, ha="center", va="center", fontsize=12.0, color="#374151", linespacing=1.05)

    fig, ax = plt.subplots(figsize=(18.5, 9.2), dpi=220)
    ax.set_xlim(0, 18.5)
    ax.set_ylim(0, 9.2)
    ax.axis("off")
    ax.text(9.25, 8.66, "EV Feasibility and Charging-Capacity Workflow", ha="center", fontsize=23.0, weight="bold")
    ax.text(
        9.25,
        8.18,
        "This local workflow tests whether a constructed vehicle block can be operated by an electric bus.",
        ha="center",
        fontsize=14.0,
        color="#4b5563",
    )

    top = [
        (0.75, 6.05, "1", "Candidate block", "trips, deadheads,\nand waits"),
        (4.95, 6.05, "2", "Energy simulation", "subtract driving\nconsumption"),
        (9.15, 6.05, "3", "Break-window search", "find idle time at\ncharging nodes"),
        (13.35, 6.05, "4", "Insert charging", "only if time and\nnode allow it"),
    ]
    bottom = [
        (2.70, 3.55, "5", "Capacity check", "reserve parking and\ncharging capacity"),
        (7.40, 3.55, "6", "EV accepted", "autonomy and\ncapacity valid"),
        (12.10, 3.55, "7", "ICE fallback", "if EV infeasible,\nkeep ICE block"),
    ]
    for item in top + bottom:
        color = "#f28e2b" if item[2] == "3" else ("#2a9d8f" if item[2] in {"4", "5", "6"} else ("#e15759" if item[2] == "7" else "#2563eb"))
        draw_ev_box(ax, item[0], item[1], 3.45, 1.24, item[2], item[3], item[4], badge_color=color)

    for start, end in [
        ((4.28, 6.67), (4.88, 6.67)),
        ((8.48, 6.67), (9.08, 6.67)),
        ((12.68, 6.67), (13.28, 6.67)),
        ((15.08, 6.05), (15.08, 5.15)),
        ((15.08, 5.15), (4.43, 5.15)),
        ((4.43, 5.15), (4.43, 4.87)),
        ((6.23, 4.17), (7.32, 4.17)),
        ((10.93, 4.17), (12.02, 4.17)),
    ]:
        _arrow(ax, start, end)

    ax.text(6.85, 4.55, "feasible", fontsize=13.0, color="#2a9d8f", ha="center", weight="bold")
    ax.text(11.52, 4.55, "not feasible", fontsize=13.0, color="#e15759", ha="center", weight="bold")

    _draw_formula_panel(
        ax,
        (3.15, 0.72),
        12.20,
        1.58,
        "Feasibility logic",
        "Battery update and feasibility check",
        "Charging is accepted only when node parking and charging capacities are not exceeded.",
    )

    fig.tight_layout(pad=1.15)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.12, dpi=320)
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)


def make_final_solver_workflow(path: Path) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(17.4, 9.3), dpi=220)
    ax.set_xlim(0, 17.4)
    ax.set_ylim(0, 9.3)
    ax.axis("off")
    ax.text(8.70, 8.82, "Final Multi-Start Path-Cover Matheuristic", ha="center", fontsize=24.0, weight="bold")
    ax.text(
        8.70,
        8.36,
        "Each start is a complete candidate schedule; the best retained output has the lowest audited total cost.",
        ha="center",
        fontsize=14.2,
        color="#5d6a78",
    )

    steps = [
        (0.70, 6.48, "1", "Start h", "variant\nweights", "#2563eb"),
        (3.85, 6.48, "2", "Timetable", "headway\npath", "#2a9d8f"),
        (7.00, 6.48, "3", "Graph", "feasible\narcs", "#c87b24"),
        (10.15, 6.48, "4", "Matching", "weighted\npath cover", "#6c55a3"),
        (13.30, 6.48, "5", "Blocks", "paths and\ndepot moves", "#1f2937"),
        (2.85, 3.92, "6", "Fleet", "EV/ICE\nchoice", "#26736d"),
        (6.85, 3.92, "7", "Charging", "breaks and\ncapacity", "#26736d"),
        (10.85, 3.92, "8", "Cost", "fixed, break,\npull, CO$_2$", "#c87b24"),
        (6.85, 1.62, "9", "Best output", r"$\min\, C^{int,h}$", "#b44949"),
    ]
    for x, y, num, title, body, color in steps:
        _draw_box(
            ax,
            x,
            y,
            2.85,
            1.20,
            num,
            title,
            body,
            badge_color=color,
            title_fs=14.2,
            body_fs=13.0,
            badge_fs=12.4,
            badge_radius=0.30,
        )

    arrows = [
        ((3.56, 7.08), (3.82, 7.08), None),
        ((6.71, 7.08), (6.97, 7.08), None),
        ((9.86, 7.08), (10.12, 7.08), None),
        ((13.01, 7.08), (13.27, 7.08), None),
        ((14.72, 6.48), (14.72, 5.46), None),
        ((14.72, 5.46), (4.28, 5.46), None),
        ((4.28, 5.46), (4.28, 5.14), None),
        ((5.72, 4.52), (6.82, 4.52), None),
        ((9.72, 4.52), (10.82, 4.52), None),
        ((12.27, 3.92), (12.27, 2.96), None),
        ((12.27, 2.96), (8.28, 2.96), None),
        ((8.28, 2.96), (8.28, 2.67), None),
    ]
    for start, end, label in arrows:
        _arrow(ax, start, end, label=label)

    _draw_formula_panel(
        ax,
        (0.92, 0.20),
        5.45,
        1.35,
        "Multi-start set",
        r"$H=\{0,1,\ldots,H_{max}\}$",
        "Each h changes timetable tie-breaking\nand therefore graph quality.",
        title_fs=13.4,
        formula_fs=12.5,
        body_fs=11.8,
    )
    _draw_formula_panel(
        ax,
        (10.20, 0.20),
        5.75,
        1.35,
        "Selection rule",
        r"$h^*=\operatorname{argmin}_{h\in H_{int}} C^{int,h}$",
        "Final output is audited\nafter construction.",
        title_fs=13.4,
        formula_fs=12.5,
        body_fs=11.8,
    )

    fig.tight_layout(pad=1.15)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.12, dpi=320)
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)


def make_algorithm_gain_panel(path: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    final_rows = _result_rows()
    final_by_instance = {row[0]: {"cost": row[1], "vehicles": row[3]} for row in final_rows}
    baseline = [
        ("Small", 162.44, 2),
        ("Medium", 371.35, 5),
        ("Large", 1163.35, 15),
        ("Toy", 488.44, 6),
        ("1line", 323.63, 4),
        ("1line 6TW", 530.77, 7),
        ("2lines", 910.15, 12),
        ("2lines 6TW", 626.24, 8),
        ("3lines", 999.99, 12),
        ("3lines tri.", 941.41, 12),
        ("5lines", 1669.01, 20),
        ("8lines", 2617.76, 33),
    ]
    labels = [row[0] for row in baseline]
    cost_gain = np.array(
        [row[1] - final_by_instance.get(row[0], {"cost": row[1]})["cost"] for row in baseline],
        dtype=float,
    )
    vehicle_gain = np.array(
        [row[2] - final_by_instance.get(row[0], {"vehicles": row[2]})["vehicles"] for row in baseline],
        dtype=float,
    )
    y = np.arange(len(labels))

    fig, (ax_cost, ax_vehicle) = plt.subplots(
        1,
        2,
        figsize=(13.2, 6.2),
        dpi=180,
        gridspec_kw={"width_ratios": [1.5, 1.0], "wspace": 0.18},
        sharey=True,
    )
    fig.suptitle("Baseline Archive vs Final No-Regression Archive", y=0.98, weight="bold")

    cost_colors = ["#b44949" if value > 0.005 else "#d8dde6" for value in cost_gain]
    vehicle_colors = ["#26736d" if value > 0.005 else "#d8dde6" for value in vehicle_gain]
    cost_bars = ax_cost.barh(y, cost_gain, color=cost_colors, height=0.58)
    vehicle_bars = ax_vehicle.barh(y, vehicle_gain, color=vehicle_colors, height=0.58)

    ax_cost.set_yticks(y, labels)
    ax_cost.invert_yaxis()
    ax_cost.set_xlabel("Cost reduction retained by final archive")
    ax_vehicle.set_xlabel("Vehicle reduction retained by final archive")
    ax_cost.set_title("Cost reduction", fontsize=10.8, weight="bold")
    ax_vehicle.set_title("Vehicle reduction", fontsize=10.8, weight="bold")

    for ax in (ax_cost, ax_vehicle):
        ax.grid(axis="x", color="#e5e7eb")
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.axvline(0, color="#6b7280", linewidth=0.8)

    ax_cost.set_xlim(0, max(cost_gain) * 1.25 if max(cost_gain) > 0 else 1)
    ax_vehicle.set_xlim(0, max(vehicle_gain) + 0.8 if max(vehicle_gain) > 0 else 1)

    for bar, value in zip(cost_bars, cost_gain):
        label = "kept" if value <= 0.005 else f"{value:.2f}"
        ax_cost.text(
            bar.get_width() + ax_cost.get_xlim()[1] * 0.015,
            bar.get_y() + bar.get_height() / 2,
            label,
            va="center",
            ha="left",
            fontsize=10.8,
            color="#1f2937",
        )

    for bar, value in zip(vehicle_bars, vehicle_gain):
        label = "kept" if abs(value) < 1e-6 else f"{int(value)}"
        ax_vehicle.text(
            bar.get_width() + ax_vehicle.get_xlim()[1] * 0.025,
            bar.get_y() + bar.get_height() / 2,
            label,
            va="center",
            ha="left",
            fontsize=10.8,
            color="#1f2937",
        )

    fig.text(
        0.5,
        0.025,
        "Zero bars mean the baseline archive output was retained. Positive bars show improvements kept in the final archive.",
        ha="center",
        fontsize=10.8,
        color="#495057",
    )
    fig.tight_layout(rect=(0, 0.07, 1, 0.95))
    fig.savefig(path, bbox_inches="tight", dpi=300)
    plt.close(fig)


def make_sml_improvement_heatmap(path: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    instances = ["Small", "Medium", "Large"]
    algorithms = ["Greedy", "Path-cover", "Weighted", "Multi-start"]
    final_by_instance = {row[0]: row[1] for row in _result_rows()}
    costs = np.array(
        [
            [213.55, 213.43, 213.55, final_by_instance.get("Small", 162.44)],
            [457.10, 456.81, 458.36, final_by_instance.get("Medium", 371.35)],
            [1169.87, 1168.77, 1166.94, final_by_instance.get("Large", 1163.35)],
        ]
    )
    best = costs[:, [-1]]
    improvement = costs - best

    fig, ax = plt.subplots(figsize=(11.6, 5.2), dpi=190)
    image = ax.imshow(improvement, cmap="YlOrRd", aspect="auto")
    ax.set_title("Per-Instance Cost Gap to the Final Multi-Start Method", fontsize=15, weight="bold")
    ax.set_xticks(range(len(algorithms)), algorithms)
    ax.set_yticks(range(len(instances)), instances)
    ax.set_xlabel("Algorithm", fontsize=11)
    ax.set_ylabel("Headline instance", fontsize=11)
    ax.tick_params(axis="both", labelsize=10)
    for r in range(improvement.shape[0]):
        for c in range(improvement.shape[1]):
            value = improvement[r, c]
            text = "best" if abs(value) < 1e-6 else f"+{value:.2f}"
            color = "white" if value > improvement.max() * 0.55 else "#1f2937"
            ax.text(c, r, text, ha="center", va="center", fontsize=10.8, weight="bold", color=color)
    cbar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("Cost above final method", fontsize=10.8)
    cbar.ax.tick_params(labelsize=9)
    ax.spines[:].set_visible(False)
    ax.tick_params(length=0)
    fig.text(
        0.5,
        0.02,
        "The largest gains come from Small and Medium, where timetable variation reduces one vehicle block.",
        ha="center",
        fontsize=10.8,
        color="#495057",
    )
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(path, dpi=300)
    plt.close(fig)


def make_all_instance_tradeoff_dashboard(path: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    labels = [row[0] for row in _result_rows()]
    cost = np.array([row[1] for row in _result_rows()], dtype=float)
    trips = np.array([row[2] for row in _result_rows()], dtype=float)
    vehicles = np.array([row[3] for row in _result_rows()], dtype=float)
    ev_share = np.array([row[4] for row in _result_rows()], dtype=float)
    deadhead = np.array([row[5] for row in _result_rows()], dtype=float)
    breaks = np.array([row[6] for row in _result_rows()], dtype=float)
    charge = np.array([row[7] for row in _result_rows()], dtype=float)

    cost_per_trip = cost / trips
    trips_per_vehicle = trips / vehicles
    deadhead_per_trip = deadhead / trips
    break_per_trip = breaks / trips
    charge_per_trip = charge / trips
    resource = np.column_stack([deadhead_per_trip, break_per_trip, charge_per_trip])
    total_pressure = resource.sum(axis=1)
    order = np.argsort(total_pressure)
    code_map = {
        "Small": "S",
        "Medium": "M",
        "Large": "LG",
        "Toy": "T",
        "1line": "1",
        "1line 6TW": "1W",
        "2lines": "2",
        "2lines 6TW": "2W",
        "3lines": "3",
        "3lines tri.": "3T",
        "5lines": "5",
        "8lines": "8",
    }

    def add_callout_labels(ax, xs, ys, offsets):
        for x_value, y_value, label in zip(xs, ys, labels):
            dx, dy = offsets[label]
            ax.annotate(
                code_map[label],
                (x_value, y_value),
                xytext=(dx, dy),
                textcoords="offset points",
                ha="center",
                va="center",
                fontsize=8.7,
                weight="bold",
                color="#1f2937",
                bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="#94a3b8", lw=0.65, alpha=0.96),
                arrowprops=dict(arrowstyle="-", color="#94a3b8", lw=0.65, shrinkA=2, shrinkB=4),
                annotation_clip=False,
                zorder=6,
            )

    fig = plt.figure(figsize=(12.4, 9.0), dpi=220)
    gs = fig.add_gridspec(
        3,
        2,
        width_ratios=[1.18, 1.02],
        height_ratios=[1.0, 0.30, 1.18],
        wspace=0.46,
        hspace=0.34,
    )
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax_code = fig.add_subplot(gs[1, :])
    ax3 = fig.add_subplot(gs[2, :])

    scatter = ax1.scatter(
        trips_per_vehicle,
        cost_per_trip,
        s=110 + ev_share * 2.6,
        c=ev_share,
        cmap="viridis",
        edgecolor="white",
        linewidth=0.85,
    )
    ax1.set_title("Efficiency and electrification", fontsize=14.0, weight="bold")
    ax1.set_xlabel("Selected trips per vehicle", fontsize=12)
    ax1.set_ylabel("Cost per selected trip", fontsize=12)
    ax1.tick_params(labelsize=10.8)
    ax1.grid(color="#e5e7eb", linewidth=0.8)
    ax1.spines[["top", "right"]].set_visible(False)
    ax1.set_xlim(float(trips_per_vehicle.min()) - 1.0, float(trips_per_vehicle.max()) + 1.0)
    ax1.set_ylim(float(cost_per_trip.min()) - 0.18, float(cost_per_trip.max()) + 0.42)
    ax1_offsets = {
        "Small": (16, -18),
        "Medium": (14, -18),
        "Large": (18, 16),
        "Toy": (-20, -18),
        "1line": (-18, -18),
        "1line 6TW": (-20, 16),
        "2lines": (-28, 24),
        "2lines 6TW": (-18, -16),
        "3lines": (18, -16),
        "3lines tri.": (19, 12),
        "5lines": (18, 14),
        "8lines": (-20, -16),
    }
    add_callout_labels(ax1, trips_per_vehicle, cost_per_trip, ax1_offsets)
    cbar = fig.colorbar(scatter, ax=ax1, fraction=0.045, pad=0.025)
    cbar.set_label("EV share (%)", fontsize=11.0)
    cbar.ax.tick_params(labelsize=9.8)

    ax2.scatter(
        deadhead_per_trip,
        charge_per_trip,
        s=105 + vehicles * 4.2,
        color="#2f6db3",
        alpha=0.82,
        edgecolor="white",
        linewidth=0.85,
    )
    ax2.set_title("Repositioning and charging pressure", fontsize=14.0, weight="bold")
    ax2.set_xlabel("Deadhead minutes per trip", fontsize=12)
    ax2.set_ylabel("Charging minutes per trip", fontsize=12)
    ax2.tick_params(labelsize=10.8)
    ax2.grid(color="#e5e7eb", linewidth=0.8)
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.set_xlim(float(deadhead_per_trip.min()) - 0.65, float(deadhead_per_trip.max()) + 0.85)
    ax2.set_ylim(float(charge_per_trip.min()) - 0.14, float(charge_per_trip.max()) + 0.42)
    ax2_offsets = {
        "Small": (-16, 16),
        "Medium": (16, 16),
        "Large": (18, -14),
        "Toy": (-16, -17),
        "1line": (-24, 22),
        "1line 6TW": (18, -17),
        "2lines": (18, 16),
        "2lines 6TW": (-22, -16),
        "3lines": (-24, -11),
        "3lines tri.": (18, 16),
        "5lines": (-22, 16),
        "8lines": (18, 16),
    }
    add_callout_labels(ax2, deadhead_per_trip, charge_per_trip, ax2_offsets)

    ax_code.axis("off")
    code_line_1 = "   ".join([f"{code_map[k]}={k}" for k in ["Small", "Medium", "Large", "Toy", "1line", "1line 6TW"]])
    code_line_2 = "   ".join([f"{code_map[k]}={k}" for k in ["2lines", "2lines 6TW", "3lines", "3lines tri.", "5lines", "8lines"]])
    ax_code.text(
        0.5,
        0.67,
        "Scatter-label code map",
        ha="center",
        va="center",
        fontsize=10.8,
        weight="bold",
        color="#1f2937",
    )
    ax_code.text(
        0.5,
        0.23,
        f"{code_line_1}\n{code_line_2}",
        ha="center",
        va="center",
        fontsize=10.8,
        color="#334155",
        linespacing=1.45,
    )

    resource_sorted = resource[order]
    labels_sorted = [labels[i] for i in order]
    y = np.arange(len(labels_sorted))
    left = np.zeros(len(labels_sorted))
    colors = ["#4c78a8", "#f2b447", "#2a9d8f"]
    names = ["Deadhead/trip", "Break/trip", "Charge/trip"]
    for idx, (values, color, name) in enumerate(zip(resource_sorted.T, colors, names)):
        bars = ax3.barh(y, values, left=left, color=color, label=name)
        for bar, value, base in zip(bars, values, left):
            if value >= 0.55:
                ax3.text(base + value / 2, bar.get_y() + bar.get_height() / 2, f"{value:.1f}", ha="center", va="center", fontsize=11.0, color="white", weight="bold")
        left += values
    ax3.set_title("Operational minutes per selected trip, sorted by total pressure", fontsize=14.0, weight="bold")
    ax3.set_xlabel("Minutes per selected trip", fontsize=12)
    ax3.set_yticks(y, labels_sorted)
    ax3.grid(axis="x", color="#e5e7eb", linewidth=0.8)
    ax3.spines[["top", "right", "left"]].set_visible(False)
    ax3.tick_params(axis="y", length=0, labelsize=10.8)
    ax3.tick_params(axis="x", labelsize=10.8)
    ax3.legend(frameon=False, ncol=3, loc="lower right", fontsize=11.0)
    for idx, total in enumerate(total_pressure[order]):
        ax3.text(total + 0.25, idx, f"{total:.1f}", va="center", fontsize=11.0, color="#334155")

    fig.suptitle("All-Instance Operational Trade-Off Summary", fontsize=20.0, weight="bold", y=0.982)
    fig.text(
        0.5,
        0.020,
        "Reading guide: good schedules combine high vehicle productivity with manageable repositioning, waiting, and charging pressure.",
        ha="center",
        fontsize=11.3,
        color="#495057",
    )
    fig.tight_layout(rect=(0.03, 0.055, 0.985, 0.95))
    fig.savefig(path, bbox_inches="tight", pad_inches=0.14, dpi=320)
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight", pad_inches=0.14)
    plt.close(fig)


def make_resource_pressure(path: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    labels = [row[0] for row in _result_rows()]
    values = np.array(
        [
            [row[5] / row[2], row[6] / row[2], row[7] / max(row[2], 1), row[4] / 100.0]
            for row in _result_rows()
        ]
    )
    col_labels = ["Deadhead/trip", "Break/trip", "Charge/trip", "EV share"]
    norm = values.copy()
    for c in range(3):
        norm[:, c] = norm[:, c] / max(norm[:, c].max(), 1e-9)

    fig, ax = plt.subplots(figsize=(12.2, 7.7), dpi=190)
    image = ax.imshow(norm, cmap="YlGnBu", aspect="auto", vmin=0, vmax=1)
    ax.set_title("Constraint Pressure Indicators Across All Senior Instances", pad=14, fontsize=16, weight="bold")
    ax.set_xticks(range(len(col_labels)), col_labels)
    ax.set_yticks(range(len(labels)), labels)
    ax.tick_params(axis="x", labelsize=11)
    ax.tick_params(axis="y", labelsize=10)

    for r, row in enumerate(values):
        for c, value in enumerate(row):
            text = f"{value:.1f}" if c < 3 else f"{value * 100:.0f}%"
            color = "white" if norm[r, c] > 0.62 else "#1f2933"
            ax.text(c, r, text, ha="center", va="center", fontsize=10.8, color=color, weight="bold")

    ax.set_xlabel("Indicators derived from validated schedules", fontsize=11)
    cbar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("Relative pressure within each column", fontsize=10.8)
    cbar.ax.tick_params(labelsize=9)
    ax.spines[:].set_visible(False)
    ax.tick_params(axis="both", length=0)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def make_efficiency_panel(path: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    labels = [row[0] for row in _result_rows()]
    costs_per_trip = [row[1] / row[2] for row in _result_rows()]
    trips_per_vehicle = [row[2] / row[3] for row in _result_rows()]
    ev_share = [row[4] for row in _result_rows()]
    x = np.arange(len(labels))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13.2, 8.8), dpi=190, sharex=True)
    bars = ax1.bar(x, costs_per_trip, color="#26736d", width=0.62)
    ax1.set_title("All-Instance Efficiency View", fontsize=16, weight="bold")
    ax1.set_ylabel("Cost per selected trip", fontsize=11)
    ax1.tick_params(labelsize=10)
    ax1.grid(axis="y", color="#dde2e6", linewidth=0.8)
    ax1.spines[["top", "right"]].set_visible(False)
    for bar, value in zip(bars, costs_per_trip):
        ax1.text(bar.get_x() + bar.get_width() / 2, value + 0.08, f"{value:.2f}", ha="center", fontsize=10.8)

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
    ax2.set_ylabel("Trips per used vehicle", fontsize=11)
    ax2.set_xticks(x, labels, rotation=32, ha="right")
    ax2.tick_params(axis="x", labelsize=10)
    ax2.tick_params(axis="y", labelsize=10)
    ax2.grid(axis="y", color="#dde2e6", linewidth=0.8)
    ax2.spines[["top", "right"]].set_visible(False)
    for idx, value in enumerate(trips_per_vehicle):
        ax2.text(idx, value + 0.55, f"{value:.1f}", ha="center", fontsize=10.8)
    cbar = fig.colorbar(scatter, ax=ax2, fraction=0.025, pad=0.02)
    cbar.set_label("EV share (%)", fontsize=10.8)
    cbar.ax.tick_params(labelsize=9)

    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def make_cost_audit_panel(path: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    rows = _cost_audit_rows()
    labels = [str(row["label"]) for row in rows]
    total = np.array([float(row["cost"]) for row in rows])
    fixed = np.array([float(row["fixed"]) for row in rows])
    other = np.array([float(row["remaining"]) for row in rows])
    fixed_share = fixed / total * 100.0
    y = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(14.2, 8.0), dpi=190)
    ax.barh(y, fixed, color="#536878", label="Fixed vehicle cost")
    ax.barh(y, other, left=fixed, color="#f2b447", label="Remaining validated cost")

    ax.set_title("Validated Cost Audit Across All Senior Instances", pad=14, weight="bold")
    ax.set_xlabel("Validated objective value", fontsize=11)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.grid(axis="x", color="#dde2e6", linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper right")
    ax.set_xlim(0, max(total) * 1.14)
    ax.tick_params(axis="y", length=0, labelsize=10)
    ax.tick_params(axis="x", labelsize=10)

    for idx, value in enumerate(total):
        ax.text(value + max(total) * 0.014, idx, f"{value:.0f}", va="center", fontsize=10.8, weight="bold")
        if fixed[idx] > 120:
            ax.text(
                fixed[idx] * 0.52,
                idx,
                f"{fixed_share[idx]:.0f}% fixed",
                ha="center",
                va="center",
                fontsize=10.8,
                color="white",
                weight="bold",
            )
        if other[idx] > 55:
            ax.text(
                fixed[idx] + other[idx] / 2,
                idx,
                f"{other[idx]:.1f}",
                ha="center",
                va="center",
                fontsize=10.8,
                color="#343a40",
            )

    fig.text(
        0.5,
        0.01,
        "Number at the bar end = total validated cost. The remaining segment equals total cost minus fixed vehicle cost.",
        ha="center",
        fontsize=10.8,
        color="#495057",
    )
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    fig.savefig(path, dpi=300)
    plt.close(fig)


def make_vehicle_journey_figure(path: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import LinearSegmentedColormap

    labels = [row[0] for row in _result_rows()]
    trips = np.array([row[2] for row in _result_rows()], dtype=float)
    vehicles = np.array([row[3] for row in _result_rows()], dtype=float)
    ev_share = np.array([row[4] for row in _result_rows()], dtype=float) / 100.0
    ev = np.rint(vehicles * ev_share).astype(int)
    ice = vehicles.astype(int) - ev
    deadhead = np.array([row[5] for row in _result_rows()], dtype=float) / trips
    breaks = np.array([row[6] for row in _result_rows()], dtype=float) / trips
    charge = np.array([row[7] for row in _result_rows()], dtype=float) / trips
    matrix = np.column_stack([deadhead, breaks, charge])

    fig, (ax1, ax2) = plt.subplots(
        1,
        2,
        figsize=(14.4, 8.0),
        dpi=190,
        gridspec_kw={"width_ratios": [1.05, 1.45], "wspace": 0.18},
    )
    fig.suptitle("All-Instance Operational Profile of the Final Schedules", fontsize=17, weight="bold", y=0.98)
    fig.text(
        0.5,
        0.935,
        "Each row is one senior instance. The left panel shows the validated fleet mix; the right panel normalizes operational activity minutes by selected trips.",
        ha="center",
        fontsize=10.8,
        color="#5d6a78",
    )

    y = np.arange(len(labels))
    ax1.barh(y, ev, color="#2a9d8f", edgecolor="#1f2937", linewidth=0.4, label="EV vehicles")
    ax1.barh(y, ice, left=ev, color="#536878", edgecolor="#1f2937", linewidth=0.4, label="ICE vehicles")
    ax1.set_yticks(y, labels)
    ax1.invert_yaxis()
    ax1.set_xlabel("Used vehicles", fontsize=11)
    ax1.set_title("Validated EV/ICE fleet mix\n(green = EV, gray = ICE)", fontsize=12.4, weight="bold")
    ax1.grid(axis="x", color="#e5e7eb", linewidth=0.8)
    ax1.spines[["top", "right", "left"]].set_visible(False)
    ax1.tick_params(axis="y", length=0, labelsize=10)
    ax1.tick_params(axis="x", labelsize=10)
    for idx, (e, i, total) in enumerate(zip(ev, ice, vehicles.astype(int))):
        ax1.text(total + 0.35, idx, f"{total}", va="center", fontsize=10.8, color="#263445")
        if e > 0:
            ax1.text(e / 2, idx, str(e), ha="center", va="center", fontsize=10.8, color="white", weight="bold")
        if i > 0:
            ax1.text(e + i / 2, idx, str(i), ha="center", va="center", fontsize=10.8, color="white", weight="bold")

    cmap = LinearSegmentedColormap.from_list("activity_pressure", ["#f8fafc", "#b7d7ee", "#2f6db3"])
    image = ax2.imshow(matrix, cmap=cmap, aspect="auto")
    ax2.set_title("Operational minutes per selected trip", fontsize=13, weight="bold")
    ax2.set_xticks([0, 1, 2], ["Deadhead", "Break", "Charge"])
    ax2.set_yticks(y, labels)
    ax2.tick_params(axis="both", length=0, labelsize=10)
    ax2.spines[:].set_visible(False)
    for r in range(matrix.shape[0]):
        for c in range(matrix.shape[1]):
            value = matrix[r, c]
            color = "white" if value > matrix.max() * 0.62 else "#1f2937"
            ax2.text(c, r, f"{value:.1f}", ha="center", va="center", fontsize=10.8, color=color, weight="bold")
    cbar = fig.colorbar(image, ax=ax2, fraction=0.035, pad=0.02)
    cbar.set_label("minutes / trip", fontsize=10.8)
    cbar.ax.tick_params(labelsize=9)

    fig.text(
        0.5,
        0.018,
        "Reading guide: high deadhead values indicate more repositioning, high break values indicate more stationary paid time, and high charge values indicate stronger EV charging use.",
        ha="center",
        fontsize=10.8,
        color="#495057",
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.91))
    fig.savefig(path, dpi=300)
    plt.close(fig)


def _draw_journey_lane(ax, segments, y, colors, max_labels) -> None:
    label_count = 0
    for start, end, kind, label in segments:
        if end <= start:
            continue
        ax.broken_barh(
            [(start, end - start)],
            (y, 6),
            facecolors=colors[kind],
            edgecolors="#1f2937",
            linewidth=0.7,
            alpha=0.95,
        )
        duration_min = (end - start) / 60
        if kind in {"trip", "charge"} and label_count < max_labels and duration_min >= 7:
            ax.text(
                (start + end) / 2,
                y + 3,
                label,
                ha="center",
                va="center",
                fontsize=10.8,
                color="white" if kind == "trip" else "#1f2937",
                weight="bold" if kind == "charge" else "normal",
            )
            label_count += 1


def _block_segments(data, block) -> tuple[list[tuple[float, float, str, str]], dict[str, float]]:
    trips = _trip_index(data)
    segments = []
    stats = {"trips": 0, "deadhead_min": 0.0, "break_min": 0.0, "charge_min": 0.0}
    for activity in block["vehicleBlock"]["activityList"]:
        if "activityTrip" in activity:
            trip_id = activity["activityTrip"]["tripId"]
            trip = trips[trip_id]
            segments.append((trip["startTime"], trip["endTime"], "trip", f"T{stats['trips'] + 1}"))
            stats["trips"] += 1
        elif "deadhead" in activity:
            deadhead = activity["deadhead"]
            start = deadhead["startingTime"]
            end = deadhead["endingTime"]
            segments.append((start, end, "deadhead", "D"))
            stats["deadhead_min"] += (end - start) / 60
        elif "break" in activity:
            for wrapper in activity["break"].get("breakTimeWindows", []):
                window = wrapper["breakTimeWindow"]
                start = window["startTime"]
                end = window["endTime"]
                kind = "charge" if window.get("isCharging") else "break"
                segments.append((start, end, kind, "CH" if kind == "charge" else "B"))
                if kind == "charge":
                    stats["charge_min"] += (end - start) / 60
                else:
                    stats["break_min"] += (end - start) / 60
    return sorted(segments), stats


def _select_block(output, vehicle_type: str, prefer_charging: bool):
    candidates = []
    for block in output["vehicleBlockList"]:
        current_type = block["vehicleBlock"]["vehicleTypeName"].lower()
        if current_type != vehicle_type.lower():
            continue
        charges = 0
        trips = 0
        for activity in block["vehicleBlock"]["activityList"]:
            if "activityTrip" in activity:
                trips += 1
            if "break" in activity:
                for wrapper in activity["break"].get("breakTimeWindows", []):
                    if wrapper["breakTimeWindow"].get("isCharging"):
                        charges += 1
        candidates.append((charges, trips, block))
    if not candidates:
        raise ValueError(f"No {vehicle_type} block found.")
    if prefer_charging:
        return max(candidates, key=lambda item: (item[0], item[1]))[2]
    return max(candidates, key=lambda item: item[1])[2]


def _trip_index(data) -> dict[int, dict]:
    trips = {}
    for direction_wrapper in data["directions"]:
        direction = direction_wrapper.get("direction", direction_wrapper)
        for trip_wrapper in direction.get("tripList", direction.get("trips", [])):
            trip = trip_wrapper.get("trip", trip_wrapper)
            trips[trip["tripId"]] = trip
    return trips


def _load_json(path: Path):
    with path.open() as handle:
        return json.load(handle)


def _hhmm(seconds: float) -> str:
    minutes = int(seconds // 60)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _draw_box(
    ax,
    x,
    y,
    w,
    h,
    num,
    title,
    body,
    badge_color="#2563eb",
    title_fs=11,
    body_fs=10.8,
    badge_fs=10.8,
    badge_radius=0.25,
) -> None:
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
    badge = Circle((x + 0.45, y + h + 0.03), badge_radius, facecolor=badge_color, edgecolor="white", linewidth=1.0)
    ax.add_patch(badge)
    ax.text(x + 0.45, y + h + 0.03, str(num), ha="center", va="center", color="white", weight="bold", fontsize=badge_fs)
    ax.text(x + w / 2, y + h * 0.64, title, ha="center", va="center", fontsize=title_fs, weight="bold", color="#111827")
    ax.text(x + w / 2, y + h * 0.30, body, ha="center", va="center", fontsize=body_fs, color="#5d6a78", linespacing=0.95)


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
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=10.8, color="#1f2937", linespacing=0.95)


def _draw_formula_panel(ax, xy, w, h, title, formula, body, title_fs=12, formula_fs=11, body_fs=10.8) -> None:
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
    ax.text(x + w / 2, y + h * 0.72, title, ha="center", va="center", fontsize=title_fs, weight="bold", color="#111827")
    ax.text(x + w / 2, y + h * 0.45, formula, ha="center", va="center", fontsize=formula_fs, color="#1f2937")
    ax.text(x + w / 2, y + h * 0.20, body, ha="center", va="center", fontsize=body_fs, color="#5d6a78")


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
        ax.text(mx, my + 0.12, label, ha="center", va="bottom", fontsize=10.8, color="#5d6a78")


if __name__ == "__main__":
    main()
