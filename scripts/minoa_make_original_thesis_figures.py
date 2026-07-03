#!/usr/bin/env python3
"""Generate original thesis figures for the implemented MINOA solver.

These figures intentionally use a different visual language from earlier
drafting references.  They explain the actual implementation: shortest-path
timetable selection, compatibility arcs, bipartite matching, EV charging and
capacity checks, and the reporting pipeline.
"""

from __future__ import annotations

from pathlib import Path


OUT = Path("FAU_Thesis_temp/figures")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    make_decision_river(OUT / "fig37_research_positioning.png")
    make_headway_story(OUT / "fig36_headway_selection.png")
    make_input_object_map(OUT / "fig42_input_solver_object_map.png")
    make_algorithm_positioning(OUT / "fig39_algorithm_positioning.png")
    make_compatibility_canvas(OUT / "fig30_feasible_trip_graph.png")
    make_matching_strips(OUT / "fig32_bipartite_matching_pathcover.png")
    make_greedy_network(OUT / "fig45_greedy_successor_network.png")
    make_unweighted_pathcover_network(OUT / "fig46_unweighted_pathcover_network.png")
    make_weighted_pathcover_network(OUT / "fig47_weighted_pathcover_network.png")
    make_capacity_calendar(OUT / "fig35_capacity_ledger.png")
    make_paid_break_clock(OUT / "fig38_paid_break_accounting.png")
    make_solver_compass(OUT / "fig33_computational_framework.png")
    make_reporting_loop(OUT / "fig34_output_validation_visualization.png")
    for name in [
        "fig37_research_positioning.png",
        "fig36_headway_selection.png",
        "fig42_input_solver_object_map.png",
        "fig39_algorithm_positioning.png",
        "fig30_feasible_trip_graph.png",
        "fig32_bipartite_matching_pathcover.png",
        "fig45_greedy_successor_network.png",
        "fig46_unweighted_pathcover_network.png",
        "fig47_weighted_pathcover_network.png",
        "fig35_capacity_ledger.png",
        "fig38_paid_break_accounting.png",
        "fig33_computational_framework.png",
        "fig34_output_validation_visualization.png",
    ]:
        print(OUT / name)


def make_algorithm_positioning(path: Path) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(13.4, 6.2), dpi=180)
    ax.set_xlim(0, 13.4)
    ax.set_ylim(0, 6.2)
    ax.axis("off")
    ax.text(6.7, 5.82, "Positioning of the Implemented Algorithms", ha="center", fontsize=16.5, weight="bold")
    ax.text(
        6.7,
        5.48,
        "The thesis moves from standard planning components to a graph-based matheuristic for mixed fleets.",
        ha="center",
        fontsize=9.4,
        color="#596579",
    )

    top = [
        (0.45, "Timetabling", "select departures\nunder headway rules", "#edf4ff", "#3b6ea8"),
        (3.05, "Vehicle scheduling", "chain trips into\nvehicle blocks", "#edf4ff", "#3b6ea8"),
        (5.65, "Electric bus scheduling", "battery, charging,\nterminal capacity", "#eefbf4", "#2d8a5f"),
        (8.25, "Graph matching", "path cover on a\ncompatibility graph", "#fff6e8", "#bd7420"),
        (10.85, "Final method", "multi-start weighted\npath cover", "#fff0f0", "#b44949"),
    ]
    for idx, (x, title, body, face, edge) in enumerate(top, start=1):
        _round(ax, x, 3.55, 2.12, 1.08, face, edge, lw=1.25)
        ax.text(x + 1.06, 4.20, title, ha="center", fontsize=9.9, weight="bold", color="#1d2733")
        ax.text(x + 1.06, 3.78, body, ha="center", fontsize=8.0, color="#596579", linespacing=1.05)
        if idx < len(top):
            _arrow(ax, (x + 2.15, 4.08), (top[idx][0] - 0.03, 4.08), "#667085")

    experiments = [
        (1.2, "Greedy", "local successor\nselection"),
        (3.9, "Path-cover", "maximum-cardinality\nmatching"),
        (6.6, "Weighted path-cover", "cost-aware\nmatching"),
        (9.3, "Multi-start path-cover", "several timetable\nvariants"),
    ]
    for x, title, body in experiments:
        _round(ax, x, 1.15, 2.45, 1.10, "#f8fafc", "#98a2b3", lw=1.05)
        ax.text(x + 1.22, 1.86, title, ha="center", fontsize=9.5, weight="bold", color="#263445")
        ax.text(x + 1.22, 1.46, body, ha="center", fontsize=7.9, color="#596579", linespacing=1.05)
    ax.text(
        6.7,
        0.48,
        "The four experimental algorithms are therefore not isolated: each one adds one modeling idea to the previous one.",
        ha="center",
        fontsize=9.0,
        color="#596579",
    )
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def make_decision_river(path: Path) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(15.8, 7.2), dpi=180)
    ax.set_xlim(0, 15.8)
    ax.set_ylim(0, 7.6)
    ax.axis("off")
    ax.text(7.9, 7.18, "Planning Story of the MINOA Path-Cover Method", ha="center", fontsize=18, weight="bold")
    ax.text(
        7.9,
        6.80,
        "The figure follows one schedule candidate from raw trips to the final mixed-fleet vehicle schedule.",
        ha="center",
        fontsize=10.2,
        color="#596579",
    )

    stages = [
        ("Candidate trip pool", "all possible departures\nfrom the MINOA input", "#edf4ff", "#3b6ea8"),
        ("Timetable path", "headway-feasible\nselected trips", "#eefbf4", "#2d8a5f"),
        ("Compatibility graph", "trip nodes and arcs\n$G_\\pi=(\\pi,A_\\pi)$", "#fff6e8", "#bd7420"),
        ("Path-cover blocks", "matching chooses\nvehicle continuations", "#f4efff", "#6c55a3"),
        ("Mixed-fleet schedule", "EV/ICE assignment,\ncharging and capacity", "#fff0f0", "#b44949"),
    ]
    xs = [0.45, 3.55, 6.65, 9.75, 12.85]
    edge_labels = [
        "headway selection",
        "selected trips",
        "matched arcs",
        "fleet checks",
    ]
    for i, ((title, body, face, edge), x) in enumerate(zip(stages, xs), start=1):
        _round(ax, x, 4.48, 2.45, 1.28, face, edge, lw=1.45)
        ax.text(
            x + 0.25,
            5.58,
            f"{i}",
            ha="center",
            va="center",
            fontsize=9.5,
            weight="bold",
            color="white",
            bbox=dict(boxstyle="circle,pad=0.23", fc=edge, ec="white", lw=0.8),
        )
        ax.text(x + 1.22, 5.22, title, ha="center", fontsize=10.4, weight="bold", color="#1d2733")
        ax.text(x + 1.22, 4.82, body, ha="center", fontsize=8.4, color="#536173", linespacing=1.15)
        if i < len(stages):
            _arrow(ax, (x + 2.48, 5.12), (xs[i] - 0.08, 5.12), "#667085")
            ax.text((x + 2.48 + xs[i] - 0.08) / 2, 5.38, edge_labels[i - 1], ha="center", fontsize=7.3, color="#596579")

    _round(ax, 4.85, 3.18, 6.10, 0.62, "#ffffff", "#cbd5e1", lw=1.0)
    ax.text(
        7.90,
        3.49,
        "Multi-start idea: if one timetable variant gives poor graph arcs or EV feasibility,\n"
        "another variant is evaluated.",
        ha="center",
        va="center",
        fontsize=8.1,
        color="#596579",
    )

    evidence = [
        ("Graph evidence", "nodes, arcs,\nmatched continuations"),
        ("Cost evidence", "$C^{VS}$ split into fixed,\nbreak, pull and CO2"),
        ("Operational evidence", "vehicles, EV share,\ncharge and deadhead"),
    ]
    for x, (title, body) in zip([1.15, 6.25, 11.35], evidence):
        _round(ax, x, 1.25, 3.30, 1.12, "#f8fafc", "#98a2b3", lw=1.1)
        ax.text(x + 1.68, 1.81, title, ha="center", fontsize=10.2, weight="bold", color="#263445")
        ax.text(x + 1.68, 1.41, body, ha="center", fontsize=8.4, color="#596579", linespacing=1.15)
    ax.text(7.9, 0.48, "The final thesis result is a reproducible route through these objects on all senior instances.", ha="center", fontsize=9.2, color="#596579")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def make_headway_story(path: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    fig, ax = plt.subplots(figsize=(12.4, 4.6), dpi=180)
    ax.set_xlim(7.4, 12.4)
    ax.set_ylim(0, 4.8)
    ax.axis("off")
    ax.text(9.9, 4.45, "Timetable Selection as a Shortest Path in the Headway Graph", ha="center", fontsize=15.5, weight="bold")
    ax.text(9.9, 4.12, "Blue trips are selected; grey trips remain alternatives in the dense candidate pool.", ha="center", fontsize=9.4, color="#596579")

    y = 2.2
    ax.hlines(y, 7.65, 12.15, color="#1f2937", lw=1.1)
    ax.arrow(12.08, y, 0.06, 0, head_width=0.08, head_length=0.08, color="#1f2937")
    times = [8.0, 8.42, 9.02, 9.48, 10.16, 10.58, 11.25, 11.95]
    selected = {0, 2, 4, 6, 7}
    labels = ["initial", "", "", "", "", "", "", "final"]
    for idx, t in enumerate(times):
        color = "#2f6db3" if idx in selected else "#9aa4b2"
        ax.vlines(t, y - 0.33, y + 0.33, color=color, lw=3.2)
        ax.text(t, y - 0.60, f"{int(t):02d}:{int(round((t % 1) * 60)):02d}", ha="center", fontsize=8.2, color="#334155")
        if labels[idx]:
            ax.text(t, y - 0.98, labels[idx], ha="center", fontsize=8, color="#2f6db3", style="italic")
    for a, b, text in [(8.0, 9.02, "edge allowed"), (9.02, 10.16, "edge allowed"), (10.16, 11.25, "edge allowed"), (11.25, 11.95, "edge allowed")]:
        ax.annotate("", xy=(b, 2.95), xytext=(a, 2.95), arrowprops=dict(arrowstyle="<->", lw=1.1, color="#2f6db3"))
        ax.text((a + b) / 2, 3.12, text, ha="center", fontsize=8, color="#2f6db3")
    ax.text(7.7, 0.42, r"Selection rule: minimize $|\pi_d|$ first; use $Q_h(P)$ only to break ties among equally sparse feasible paths.", fontsize=9.3, color="#263445")
    ax.add_patch(Rectangle((7.58, 0.20), 4.80, 0.58, fill=False, edgecolor="#d0d5dd", lw=1.0))
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def make_input_object_map(path: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch

    fig, ax = plt.subplots(figsize=(16.0, 8.8), dpi=200)
    ax.set_xlim(0, 16.0)
    ax.set_ylim(0, 8.8)
    ax.axis("off")
    ax.text(8.0, 8.38, "From MINOA Input Data to Solver Objects", ha="center", fontsize=18, weight="bold")
    ax.text(
        8.0,
        7.98,
        "Each row follows one group of input data through the objects used by the solver and the reported evidence.",
        ha="center",
        fontsize=10.3,
        color="#596579",
    )

    def box(x, y, w, h, title, lines, face, edge):
        _round(ax, x, y, w, h, face, edge, lw=1.25)
        ax.text(x + w / 2, y + h - 0.25, title, ha="center", va="top", fontsize=10.8, weight="bold", color="#1d2733")
        ax.text(x + w / 2, y + h / 2 - 0.10, lines, ha="center", va="center", fontsize=8.8, color="#536173", linespacing=1.15)

    def arrow(a, b, label=None, color="#667085"):
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=16, lw=1.35, color=color))
        if label:
            ax.text((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 0.22, label, ha="center", fontsize=8.1, color=color)

    x0, x1, x2, x3 = 0.55, 4.35, 8.35, 12.55
    widths = [2.90, 3.05, 3.25, 2.75]
    y_rows = [6.15, 4.62, 3.09, 1.56]
    h = 1.05
    header_y = 7.37
    ax.text(x0 + widths[0] / 2, header_y, "Input data", ha="center", fontsize=11.4, weight="bold", color="#263445")
    ax.text(x1 + widths[1] / 2, header_y, "Solver object", ha="center", fontsize=11.4, weight="bold", color="#263445")
    ax.text(x2 + widths[2] / 2, header_y, "Algorithm use", ha="center", fontsize=11.4, weight="bold", color="#263445")
    ax.text(x3 + widths[3] / 2, header_y, "Reported evidence", ha="center", fontsize=11.4, weight="bold", color="#263445")

    rows = [
        (
            ("Service data", "candidate trips\nline directions\nheadway windows", "#edf4ff", "#3b6ea8"),
            ("Timetable object", "selected trips $\\pi$\ninitial and final trips\nheadway-feasible path", "#edf4ff", "#3b6ea8"),
            ("Timetable selection", "shortest path\nvariant tie-breaks\ntrip share", "#f8fafc", "#64748b"),
            ("Trip evidence", "selected trips\ntrip share", "#ffffff", "#98a2b3"),
            "headway",
        ),
        (
            ("Network data", "terminals and depot\ndeadhead arcs\ntravel times", "#fff6e8", "#bd7420"),
            ("Compatibility graph", "$G_\\pi=(\\pi,A_\\pi)$\nin-line arcs\ndepot-bridge arcs", "#fff6e8", "#bd7420"),
            ("Path-cover construction", "matched successors\nvehicle blocks\nblock count", "#f8fafc", "#64748b"),
            ("Block evidence", "vehicles\nEV/ICE mix", "#ffffff", "#98a2b3"),
            "arcs",
        ),
        (
            ("Fleet data", "EV/ICE availability\nbattery autonomy\nparking and chargers", "#eefbf4", "#2d8a5f"),
            ("Operational ledger", "battery states\ncharging intervals\ncapacity reservations", "#eefbf4", "#2d8a5f"),
            ("Mixed-fleet checks", "EV feasibility\ncharging insertion\nICE fallback", "#f8fafc", "#64748b"),
            ("Resource evidence", "deadhead, break\ncharge pressure", "#ffffff", "#98a2b3"),
            "state",
        ),
        (
            ("Cost data", "vehicle cost\nbreak cost\npull and CO2 cost", "#fff0f0", "#b44949"),
            ("Objective terms", "$C^{VS}$ components\nfixed, break\npull and CO2", "#fff0f0", "#b44949"),
            ("Schedule evaluation", "cost audit\nvehicles\nruntime", "#f8fafc", "#64748b"),
            ("Result evidence", "cost, vehicles\nbounds and gaps", "#ffffff", "#98a2b3"),
            "cost",
        ),
    ]

    for y, (inp, obj, use, out, label) in zip(y_rows, rows):
        box(x0, y, widths[0], h, *inp)
        box(x1, y, widths[1], h, *obj)
        box(x2, y, widths[2], h, *use)
        box(x3, y, widths[3], h, *out)
        arrow((x0 + widths[0] + 0.05, y + h / 2), (x1 - 0.10, y + h / 2), label)
        arrow((x1 + widths[1] + 0.05, y + h / 2), (x2 - 0.10, y + h / 2))
        arrow((x2 + widths[2] + 0.05, y + h / 2), (x3 - 0.10, y + h / 2))

    ax.text(
        8.0,
        0.52,
        "Reading guide: the same benchmark data feed all algorithms; the algorithms differ in timetable variants, graph weights, and EV charging checks.",
        ha="center",
        fontsize=9.6,
        color="#596579",
    )
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def make_compatibility_canvas(path: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

    fig, ax = plt.subplots(figsize=(13.8, 7.4), dpi=180)
    ax.set_xlim(0, 13.8)
    ax.set_ylim(0, 7.4)
    ax.axis("off")
    ax.text(6.9, 7.02, "Compatibility-Graph Formulation Used by the Solver", ha="center", fontsize=16.5, weight="bold")
    ax.text(
        6.9,
        6.67,
        "A directed arc is added only when the same vehicle can finish one selected trip and start the next trip on time.",
        ha="center",
        fontsize=9.4,
        color="#596579",
    )

    def arrow(start, end, color, text=None, dashed=False, curve=0.0, lw=1.35):
        ax.add_patch(
            FancyArrowPatch(
                start,
                end,
                arrowstyle="-|>",
                mutation_scale=13,
                lw=lw,
                color=color,
                linestyle="--" if dashed else "-",
                connectionstyle=f"arc3,rad={curve}",
            )
        )
        if text:
            mx, my = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
            ax.text(mx, my + 0.12, text, ha="center", fontsize=7.0, color=color)

    # Panel A: selected trips on a time line.
    _round(ax, 0.35, 3.88, 5.10, 2.18, "#f8fafc", "#cbd5e1", lw=1.1)
    ax.text(2.90, 5.75, "A. Selected timetable trips", ha="center", fontsize=10.8, weight="bold", color="#263445")
    ax.hlines(4.85, 0.78, 5.05, color="#1f2937", lw=1.0)
    ax.arrow(5.00, 4.85, 0.05, 0, head_width=0.07, head_length=0.07, color="#1f2937")
    ax.text(5.08, 4.70, "time", fontsize=7.5, color="#596579")
    trips = [
        (0.95, 1.95, 5.02, "i", "A -> B", "08:00-08:30", "#dbeafe"),
        (2.25, 3.20, 4.48, "j", "B -> C", "08:42-09:10", "#dbeafe"),
        (1.25, 2.45, 4.08, "k", "A -> C", "08:05-08:45", "#ecfdf3"),
        (3.55, 4.55, 5.02, "m", "C -> A", "09:35-10:05", "#fef3c7"),
    ]
    for x0, x1, y, name, od, time, face in trips:
        ax.add_patch(Rectangle((x0, y - 0.18), x1 - x0, 0.36, facecolor=face, edgecolor="#64748b", lw=0.9))
        ax.text((x0 + x1) / 2, y + 0.02, f"Trip {name}", ha="center", va="center", fontsize=7.5, weight="bold", color="#1f2937")
        ax.text((x0 + x1) / 2, y - 0.36, od, ha="center", fontsize=6.8, color="#596579")
        ax.text((x0 + x1) / 2, y + 0.31, time, ha="center", fontsize=6.8, color="#596579")

    # Panel B: tests.
    _round(ax, 0.35, 0.72, 5.10, 2.70, "#ffffff", "#cbd5e1", lw=1.1)
    ax.text(2.90, 3.08, "B. Arc acceptance tests", ha="center", fontsize=10.8, weight="bold", color="#263445")
    test_rows = [
        ("time order", r"$et(i)+travel \leq st(j)$", "#e0f2fe"),
        ("in-line continuation", "same terminal and layover bounds", "#dcfce7"),
        ("depot bridge", "pull-in + depot stop + pull-out fits", "#ffedd5"),
    ]
    for idx, (title, body, face) in enumerate(test_rows):
        y = 2.50 - idx * 0.65
        _round(ax, 0.80, y, 4.20, 0.46, face, "#cbd5e1", lw=0.8)
        ax.text(1.00, y + 0.23, f"{idx+1}", ha="center", va="center", fontsize=8, weight="bold", color="#334155")
        ax.text(1.88, y + 0.23, title, ha="center", va="center", fontsize=7.8, weight="bold", color="#263445")
        ax.text(3.68, y + 0.23, body, ha="center", va="center", fontsize=7.2, color="#596579")

    # Panel C: graph over trips.
    _round(ax, 6.15, 0.72, 7.25, 5.34, "#ffffff", "#cbd5e1", lw=1.1)
    ax.text(9.78, 5.75, r"C. Directed graph $G_\pi=(\pi,A_\pi)$", ha="center", fontsize=10.8, weight="bold", color="#263445")
    pos = {
        "i": (7.20, 4.70),
        "k": (7.20, 3.15),
        "j": (9.35, 4.10),
        "m": (11.45, 4.70),
        "r": (11.45, 2.65),
    }
    for name, (x, y) in pos.items():
        ax.add_patch(Circle((x, y), 0.30, facecolor="#1f2937", edgecolor="#ffffff", lw=1.1))
        ax.text(x, y, name, ha="center", va="center", fontsize=9.2, color="white", weight="bold")
        ax.text(x, y - 0.48, f"Trip {name}", ha="center", fontsize=7.1, color="#596579")

    def graph_edge(a, b, color, label, dashed=False, curve=0.0):
        s, e = pos[a], pos[b]
        ax.add_patch(
            FancyArrowPatch(
                s,
                e,
                arrowstyle="-|>",
                mutation_scale=14,
                lw=1.55,
                color=color,
                linestyle="--" if dashed else "-",
                connectionstyle=f"arc3,rad={curve}",
                shrinkA=18,
                shrinkB=18,
            )
        )
        mx, my = (s[0] + e[0]) / 2, (s[1] + e[1]) / 2
        ax.text(mx, my + 0.16, label, ha="center", fontsize=7.0, color=color)

    graph_edge("i", "j", "#2f6db3", "in-line", curve=-0.08)
    graph_edge("j", "m", "#2f6db3", "in-line", curve=0.05)
    graph_edge("k", "r", "#d98b2b", "depot bridge", dashed=True, curve=-0.06)
    graph_edge("i", "m", "#d98b2b", "depot bridge", dashed=True, curve=0.16)
    ax.plot([7.35, 9.20], [3.30, 3.95], color="#b44949", lw=1.3, linestyle=":")
    ax.text(8.25, 3.42, "rejected pair", ha="center", fontsize=7.1, color="#b44949")

    legend_items = [
        (6.75, 1.35, "#2f6db3", "solid arc = direct terminal continuation"),
        (9.35, 1.35, "#d98b2b", "dashed arc = depot-mediated continuation"),
        (6.75, 0.95, "#b44949", "dotted line = infeasible pair, not in graph"),
    ]
    for x, y, color, text in legend_items:
        ax.plot([x, x + 0.42], [y, y], color=color, lw=1.6, linestyle=":" if color == "#b44949" else "--" if color == "#d98b2b" else "-")
        ax.text(x + 0.50, y, text, va="center", fontsize=7.3, color="#596579")

    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def make_matching_strips(path: Path) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=180)
    ax.set_xlim(0, 12.8)
    ax.set_ylim(0, 7.4)
    ax.axis("off")
    ax.text(6.4, 6.95, "Bipartite Matching View of the Path-Cover Problem", ha="center", fontsize=16, weight="bold")
    ax.text(6.4, 6.60, "Each selected trip appears once as a predecessor copy and once as a successor copy.", ha="center", fontsize=9.4, color="#596579")
    left_x, right_x = 2.35, 6.15
    yvals = [5.50, 4.62, 3.74, 2.86, 1.98]
    names = ["1", "2", "3", "4", "5"]
    ax.text(left_x, 6.03, r"left copy $L_i$: trip used as predecessor", ha="center", fontsize=8.5, color="#334155")
    ax.text(right_x, 6.03, r"right copy $R_j$: trip used as successor", ha="center", fontsize=8.5, color="#334155")
    for y, name in zip(yvals, names):
        _node(ax, left_x, y, f"L{name}", "#e8f1ff")
        _node(ax, right_x, y, f"R{name}", "#eefbf4")
    edges = [(0, 2), (2, 4), (1, 3)]
    for a, b in edges:
        _arrow(ax, (left_x + 0.38, yvals[a]), (right_x - 0.38, yvals[b]), "#2f6db3")
    _arrow(ax, (left_x + 0.38, yvals[0]), (right_x - 0.38, yvals[3]), "#98a2b3", dashed=True)
    ax.text(4.25, 1.05, "solid blue = chosen continuation", ha="center", fontsize=7.8, color="#2f6db3")
    ax.text(4.25, 0.73, "dashed grey = feasible but not selected", ha="center", fontsize=7.8, color="#667085")
    ax.text(4.25, 0.35, r"$|M_G|=3,\ |\pi|=5 \Rightarrow |B|=|\pi|-|M_G|=2$", ha="center", fontsize=10, color="#263445")
    _round(ax, 8.55, 4.10, 3.00, 1.35, "#fff6e8", "#bd7420", lw=1.2)
    ax.text(10.05, 5.03, "Vehicle block 1", ha="center", weight="bold", fontsize=10.5)
    ax.text(10.05, 4.62, "Trip 1 -> Trip 3 -> Trip 5", ha="center", fontsize=8.8)
    ax.text(10.05, 4.32, "Trip 1 has no predecessor;\nTrip 5 has no successor.", ha="center", fontsize=7.5, color="#596579")
    _round(ax, 8.55, 2.15, 3.00, 1.35, "#f4efff", "#6c55a3", lw=1.2)
    ax.text(10.05, 3.08, "Vehicle block 2", ha="center", weight="bold", fontsize=10.5)
    ax.text(10.05, 2.67, "Trip 2 -> Trip 4", ha="center", fontsize=8.8)
    ax.text(10.05, 2.37, "Unmatched starts and ends\ncreate block boundaries.", ha="center", fontsize=7.5, color="#596579")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def make_greedy_network(path: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, FancyArrowPatch

    fig, ax = plt.subplots(figsize=(12.6, 6.6), dpi=180)
    ax.set_xlim(0, 12.6)
    ax.set_ylim(0, 6.6)
    ax.axis("off")
    ax.text(6.3, 6.20, "Approach I: Greedy Successor Network", ha="center", fontsize=16, weight="bold")
    ax.text(6.3, 5.86, "The block is extended by choosing the best feasible successor of the current last trip.", ha="center", fontsize=9.0, color="#596579")

    def node(x, y, label, face, edge="#ffffff", color="white"):
        ax.add_patch(Circle((x, y), 0.34, facecolor=face, edgecolor=edge, lw=1.2))
        ax.text(x, y, label, ha="center", va="center", fontsize=10, weight="bold", color=color)

    def arrow(start, end, color, label, dashed=False, curve=0.0, lw=1.4):
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=13, lw=lw, color=color, linestyle="--" if dashed else "-", connectionstyle=f"arc3,rad={curve}"))
        ax.text((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + 0.17, label, ha="center", fontsize=7.2, color=color)

    _round(ax, 0.55, 2.30, 1.55, 1.05, "#e8f1ff", "#3b6ea8", lw=1.2)
    ax.text(1.33, 2.98, "current\nblock", ha="center", va="center", fontsize=8.4, weight="bold", color="#263445")
    ax.text(1.33, 2.53, "...\nTrip i", ha="center", va="center", fontsize=7.6, color="#596579")
    node(2.80, 2.82, "i", "#1f2937")

    candidates = [
        (5.35, 4.35, "j", "deadhead 5\nwait 12\nscore 6.8", "#e5e7eb", "#98a2b3"),
        (5.35, 2.82, "k", "deadhead 2\nwait 7\nscore 3.1", "#2a9d8f", "#2a9d8f"),
        (5.35, 1.70, "m", "deadhead 8\nwait 3\nscore 7.4", "#e5e7eb", "#98a2b3"),
    ]
    for x, y, label, text, face, edge in candidates:
        node(x, y, label, face, edge=edge, color="white" if face == "#2a9d8f" else "#263445")
        ax.text(x + 1.05, y, text, ha="left", va="center", fontsize=7.2, color="#596579", linespacing=1.05)
        arrow((3.16, 2.82), (x - 0.36, y), "#2a9d8f" if label == "k" else "#a7b0bd", "feasible", dashed=label != "k")

    _round(ax, 8.80, 2.30, 2.80, 1.05, "#eefbf4", "#2a9d8f", lw=1.2)
    ax.text(10.20, 2.98, "selected extension", ha="center", fontsize=8.8, weight="bold", color="#263445")
    ax.text(10.20, 2.56, "block becomes\n... -> i -> k", ha="center", fontsize=7.6, color="#596579")
    arrow((5.70, 2.82), (8.76, 2.82), "#2a9d8f", "", lw=1.7)
    ax.text(7.20, 3.17, "minimum local score", ha="center", fontsize=7.2, color="#2a9d8f")

    _round(ax, 2.35, 0.15, 8.15, 0.58, "#f8fafc", "#cbd5e1", lw=1.0)
    ax.text(6.42, 0.44, r"Local rule: $i_{r+1}=\arg\min_{j\in\Gamma_U^+(i_r)} \ell_{ij}$", ha="center", va="center", fontsize=9.0, color="#263445")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def make_unweighted_pathcover_network(path: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch

    fig, ax = plt.subplots(figsize=(12.8, 6.4), dpi=180)
    ax.set_xlim(0, 12.8)
    ax.set_ylim(0, 6.4)
    ax.axis("off")
    ax.text(6.4, 6.02, "Approach II: Unweighted Path-Cover Matching", ha="center", fontsize=16, weight="bold")
    ax.text(6.4, 5.68, "The method chooses as many feasible trip continuations as possible in one global matching problem.", ha="center", fontsize=9.0, color="#596579")

    left_x, right_x = 2.0, 5.35
    yvals = [4.95, 4.05, 3.15, 2.25, 1.45]
    for idx, y in enumerate(yvals, start=1):
        _node(ax, left_x, y, f"L{idx}", "#e8f1ff")
        _node(ax, right_x, y, f"R{idx}", "#eefbf4")
    ax.text(left_x, 5.30, "predecessor copy", ha="center", fontsize=8, color="#596579")
    ax.text(right_x, 5.30, "successor copy", ha="center", fontsize=8, color="#596579")

    def edge(a, b, color, chosen=False, dashed=False):
        ax.add_patch(FancyArrowPatch((left_x + 0.38, yvals[a]), (right_x - 0.38, yvals[b]), arrowstyle="-|>", mutation_scale=12, lw=1.6 if chosen else 1.1, color=color, linestyle="--" if dashed else "-"))

    for a, b in [(0, 2), (1, 0), (2, 4), (3, 1), (4, 3)]:
        edge(a, b, "#b8c0cc", dashed=True)
    for a, b in [(0, 1), (1, 3), (2, 4)]:
        edge(a, b, "#2f6db3", chosen=True)

    _round(ax, 7.25, 3.82, 3.35, 0.88, "#fff7ed", "#d98b2b", lw=1.1)
    ax.text(8.92, 4.34, "Vehicle block 1", ha="center", fontsize=9.0, weight="bold", color="#263445")
    ax.text(8.92, 4.02, "Trip 1 -> Trip 2 -> Trip 4", ha="center", fontsize=7.8, color="#596579")
    _round(ax, 7.25, 2.60, 3.35, 0.88, "#f4efff", "#6c55a3", lw=1.1)
    ax.text(8.92, 3.12, "Vehicle block 2", ha="center", fontsize=9.0, weight="bold", color="#263445")
    ax.text(8.92, 2.80, "Trip 3 -> Trip 5", ha="center", fontsize=7.8, color="#596579")
    _round(ax, 7.25, 1.38, 3.35, 0.88, "#f8fafc", "#98a2b3", lw=1.1)
    ax.text(8.92, 1.90, "Boundary rule", ha="center", fontsize=9.0, weight="bold", color="#263445")
    ax.text(8.92, 1.58, "unmatched trips start or end blocks", ha="center", fontsize=7.8, color="#596579")

    _round(ax, 1.85, 0.20, 8.95, 0.55, "#f8fafc", "#cbd5e1", lw=1.0)
    ax.text(6.33, 0.47, r"Global rule: maximize $|M_G|$, then reconstruct blocks from matched successor links.", ha="center", va="center", fontsize=8.7, color="#263445")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def make_weighted_pathcover_network(path: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, FancyArrowPatch

    fig, ax = plt.subplots(figsize=(12.8, 6.4), dpi=180)
    ax.set_xlim(0, 12.8)
    ax.set_ylim(0, 6.4)
    ax.axis("off")
    ax.text(6.4, 6.02, "Approach III: Weighted Path-Cover Matching", ha="center", fontsize=16, weight="bold")
    ax.text(6.4, 5.68, "The graph is the same as in Approach II, but each arc receives an operational score.", ha="center", fontsize=9.0, color="#596579")

    pos = {"1": (1.40, 3.80), "2": (3.60, 4.65), "3": (3.60, 2.95), "4": (5.90, 4.10), "5": (5.90, 2.25), "6": (8.20, 3.20)}
    for label, (x, y) in pos.items():
        ax.add_patch(Circle((x, y), 0.32, facecolor="#1f2937", edgecolor="white", lw=1.1))
        ax.text(x, y, label, ha="center", va="center", fontsize=9.5, color="white", weight="bold")
        ax.text(x, y - 0.47, f"Trip {label}", ha="center", fontsize=7.0, color="#596579")

    def edge(a, b, cost, chosen=False, curve=0.0):
        color = "#2a9d8f" if chosen else "#98a2b3"
        lw = 1.8 if chosen else 1.1
        ax.add_patch(FancyArrowPatch(pos[a], pos[b], arrowstyle="-|>", mutation_scale=13, lw=lw, color=color, connectionstyle=f"arc3,rad={curve}", shrinkA=17, shrinkB=17))
        x = (pos[a][0] + pos[b][0]) / 2
        y = (pos[a][1] + pos[b][1]) / 2
        ax.text(x, y + 0.18, f"$\\hat c={cost}$", ha="center", fontsize=7.2, color=color)

    edge("1", "2", 2.1, chosen=True, curve=0.05)
    edge("1", "3", 6.4, chosen=False, curve=-0.05)
    edge("2", "4", 3.0, chosen=True, curve=0.04)
    edge("3", "5", 2.8, chosen=True, curve=-0.04)
    edge("4", "6", 4.2, chosen=True, curve=0.04)
    edge("5", "6", 7.5, chosen=False, curve=-0.10)

    _round(ax, 9.45, 3.60, 2.45, 1.00, "#eefbf4", "#2a9d8f", lw=1.1)
    ax.text(10.68, 4.25, "Selected arcs", ha="center", fontsize=9.0, weight="bold", color="#263445")
    ax.text(10.68, 3.88, "high weight\nlow local cost", ha="center", fontsize=7.6, color="#596579")
    _round(ax, 9.45, 2.10, 2.45, 1.00, "#fff7ed", "#d98b2b", lw=1.1)
    ax.text(10.68, 2.75, "Rejected arcs", ha="center", fontsize=9.0, weight="bold", color="#263445")
    ax.text(10.68, 2.38, "feasible but\nmore expensive", ha="center", fontsize=7.6, color="#596579")
    _round(ax, 2.05, 0.35, 8.70, 0.76, "#f8fafc", "#cbd5e1", lw=1.0)
    ax.text(6.40, 0.72, r"Vehicle-first weight: $w_{ij}=M-\hat c_{ij}$. More continuations remain the main priority; lower local cost breaks ties.", ha="center", va="center", fontsize=8.6, color="#263445")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def make_approach12_networks(path: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, FancyArrowPatch

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.0, 6.4), dpi=180)
    fig.suptitle("Network Logic of the First Two Implemented Approaches", fontsize=16.5, weight="bold", y=0.98)

    for ax in (ax1, ax2):
        ax.set_xlim(0, 7)
        ax.set_ylim(0, 6)
        ax.axis("off")

    # Approach I: local greedy successor choice.
    ax1.set_title("Approach I: greedy local extension", fontsize=11.3, weight="bold", color="#263445")
    ax1.text(3.5, 5.48, "Only the next successor of the current block is chosen.", ha="center", fontsize=8.2, color="#596579")
    current = (1.05, 3.15)
    candidates = [(3.65, 4.75, "j", "score 4.1"), (3.65, 3.15, "k", "score 2.7"), (3.65, 1.55, "m", "score 5.3")]
    next_trip = (5.85, 3.15)

    def node(ax, xy, label, face="#1f2937", edge="white", txt="white"):
        ax.add_patch(Circle(xy, 0.34, facecolor=face, edgecolor=edge, lw=1.2))
        ax.text(xy[0], xy[1], label, ha="center", va="center", fontsize=9.5, weight="bold", color=txt)

    def arrow(ax, start, end, color, label=None, dashed=False, curve=0.0, lw=1.4):
        ax.add_patch(
            FancyArrowPatch(
                start,
                end,
                arrowstyle="-|>",
                mutation_scale=13,
                lw=lw,
                color=color,
                linestyle="--" if dashed else "-",
                connectionstyle=f"arc3,rad={curve}",
            )
        )
        if label:
            ax.text((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + 0.15, label, ha="center", fontsize=7.0, color=color)

    node(ax1, current, "i")
    ax1.text(current[0], current[1] - 0.55, "current\nlast trip", ha="center", fontsize=7.0, color="#596579")
    for x, y, label, score in candidates:
        face = "#2a9d8f" if label == "k" else "#e5e7eb"
        txt = "white" if label == "k" else "#263445"
        node(ax1, (x, y), label, face=face, edge="#64748b", txt=txt)
        ax1.text(x, y - 0.55, score, ha="center", fontsize=7.0, color="#596579")
        arrow(ax1, (current[0] + 0.35, current[1]), (x - 0.35, y), "#2f6db3" if label == "k" else "#98a2b3", dashed=label != "k")
    node(ax1, next_trip, "block", face="#fff7ed", edge="#d98b2b", txt="#7c4a12")
    arrow(ax1, (4.00, 3.15), (5.50, 3.15), "#2a9d8f", "chosen\nsuccessor")
    ax1.text(
        3.5,
        0.55,
        r"Decision rule: choose the feasible successor with minimum local score $\ell_{ij}$.",
        ha="center",
        fontsize=8.1,
        color="#263445",
    )

    # Approach II: global unweighted matching.
    ax2.set_title("Approach II: global path cover by matching", fontsize=11.3, weight="bold", color="#263445")
    ax2.text(3.5, 5.48, "All feasible continuations are considered in one bipartite graph.", ha="center", fontsize=8.2, color="#596579")
    left_x, right_x = 1.45, 4.45
    yvals = [4.55, 3.55, 2.55, 1.55]
    for idx, y in enumerate(yvals, start=1):
        node(ax2, (left_x, y), f"L{idx}", face="#e8f1ff", edge="#64748b", txt="#263445")
        node(ax2, (right_x, y), f"R{idx}", face="#eefbf4", edge="#64748b", txt="#263445")
    chosen = [(0, 1), (1, 3), (2, 0)]
    alternatives = [(0, 2), (2, 3), (3, 1)]
    for a, b in alternatives:
        arrow(ax2, (left_x + 0.35, yvals[a]), (right_x - 0.35, yvals[b]), "#b8c0cc", dashed=True, lw=1.1)
    for a, b in chosen:
        arrow(ax2, (left_x + 0.35, yvals[a]), (right_x - 0.35, yvals[b]), "#2f6db3", lw=1.6)
    _round(ax2, 5.45, 3.30, 1.15, 1.20, "#fff7ed", "#d98b2b", lw=1.0)
    ax2.text(6.02, 4.10, "block A", ha="center", fontsize=8.2, weight="bold")
    ax2.text(6.02, 3.75, "1 -> 2\n-> 4", ha="center", fontsize=7.2, color="#596579")
    _round(ax2, 5.45, 1.68, 1.15, 0.82, "#f4efff", "#6c55a3", lw=1.0)
    ax2.text(6.02, 2.15, "block B", ha="center", fontsize=8.2, weight="bold")
    ax2.text(6.02, 1.86, "3", ha="center", fontsize=7.2, color="#596579")
    ax2.text(
        3.5,
        0.55,
        r"Decision rule: maximize the number of matched arcs, so $|B|=|\pi|-|M|$.",
        ha="center",
        fontsize=8.1,
        color="#263445",
    )
    fig.text(
        0.5,
        0.02,
        "The first approach is easy to inspect but local. The second approach uses the same compatibility arcs globally, which usually improves vehicle reuse.",
        ha="center",
        fontsize=8.6,
        color="#596579",
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.92))
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def make_capacity_calendar(path: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    fig, ax = plt.subplots(figsize=(12.4, 6.2), dpi=180)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6.0)
    ax.set_yticks([4.55, 3.35, 2.15], [r"parking $P_n=2$", r"slow charger $S_n=1$", r"fast charger $F_n=1$"])
    ax.set_xticks([1, 3, 5, 7, 9, 11], ["08:00", "09:00", "10:00", "11:00", "12:00", "13:00"])
    ax.grid(axis="x", color="#e5e7eb")
    ax.set_title("Capacity Ledger at Terminal Node n", fontsize=15, weight="bold", pad=16)
    ax.text(6, 5.35, "Capacity is checked at event times where the active set of intervals changes.", ha="center", fontsize=9.3, color="#596579")
    bars = [
        (1.2, 3.3, 4.35, "A parked", "#cbd5e1"),
        (3.0, 5.8, 4.75, "D parked", "#cbd5e1"),
        (3.2, 7.0, 3.35, "B slow charging", "#b7ebc6"),
        (3.0, 5.0, 2.15, "C fast charging", "#52a66a"),
    ]
    for start, end, y, label, color in bars:
        ax.add_patch(Rectangle((start, y - 0.28), end - start, 0.45, facecolor=color, edgecolor="#475467", lw=0.8))
        ax.text((start + end) / 2, y - 0.055, label, ha="center", va="center", fontsize=8.2, color="#263445")
    for x, label in [(1.2, r"$t_1$"), (3.0, r"$t_2$"), (5.0, r"$t_3$"), (7.0, r"$t_4$")]:
        ax.axvline(x, color="#94a3b8", linestyle="--", lw=0.9)
        ax.text(x, 1.22, label, ha="center", fontsize=8.5, color="#475467")
    ax.axvline(3.0, color="#ef4444", linestyle="--", lw=1.2)
    ax.text(3.08, 5.05, "new arrivals:\ncheck capacity", ha="left", fontsize=7.8, color="#ef4444")
    ax.text(8.85, 0.63, r"At every event time: $|\mathcal{A}^{park}_n(t)|\leq P_n,\ |\mathcal{A}^{slow}_n(t)|\leq S_n,\ |\mathcal{A}^{fast}_n(t)|\leq F_n$.", ha="center", fontsize=8.8, color="#263445")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def make_paid_break_clock(path: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    fig, ax = plt.subplots(figsize=(12.2, 4.8), dpi=180)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4.8)
    ax.axis("off")
    ax.text(6, 4.35, "Paid-Break Accounting Inside One Stop", ha="center", fontsize=15.5, weight="bold")
    ax.text(6, 4.02, "Only the remaining time after required stop and recharge contributes to break cost.", ha="center", fontsize=9.3, color="#596579")
    x0, y0 = 1.0, 2.35
    segments = [
        (0.0, 1.6, "#dbeafe", "minimum stop\nor recharge"),
        (1.6, 3.4, "#fbbf24", "paid break"),
        (3.4, 4.6, "#e5e7eb", "buffer / next\nactivity prep"),
    ]
    for start, width, color, label in segments:
        ax.add_patch(Rectangle((x0 + start * 2.0, y0), width * 2.0, 0.72, facecolor=color, edgecolor="#475467"))
        ax.text(x0 + (start + width / 2) * 2.0, y0 + 0.36, label, ha="center", va="center", fontsize=8.2)
    ax.annotate("", xy=(x0, y0 - 0.28), xytext=(x0 + 9.2, y0 - 0.28), arrowprops=dict(arrowstyle="<->", color="#263445"))
    ax.text(x0 + 4.6, y0 - 0.62, r"total stop duration $\tau_a$", ha="center", fontsize=9)
    ax.text(6, 1.02, r"$p_a=\max\{0,\;\tau_a-\max(\tau_a^r,\delta^{min}_{n(a)})\}$ for an in-line stop", ha="center", fontsize=12, color="#263445")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def make_solver_compass(path: Path) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(13.4, 8.2), dpi=180)
    ax.axis("off")
    ax.set_xlim(0, 13.4)
    ax.set_ylim(0, 8.2)
    ax.text(6.7, 7.78, "Software Architecture of the Implemented Solver", ha="center", fontsize=17, weight="bold")
    ax.text(
        6.7,
        7.43,
        "The implementation is a pipeline of reusable modules, not one monolithic script.",
        ha="center",
        fontsize=9.4,
        color="#596579",
    )

    lanes = [
        (5.95, "#edf4ff", "#3b6ea8", "Input and instance model"),
        (4.25, "#eefbf4", "#2d8a5f", "Optimization modules"),
        (2.55, "#fff6e8", "#bd7420", "Schedule construction"),
        (0.85, "#fff0f0", "#b44949", "Output and analysis"),
    ]
    for y, face, edge, label in lanes:
        _round(ax, 0.55, y, 12.30, 1.18, face, edge, lw=1.2)
        ax.text(0.88, y + 0.92, label, ha="left", fontsize=10.0, weight="bold", color=edge)

    modules = [
        (1.00, 6.15, "parser", "raw JSON ->\ninstance object", "#3b6ea8"),
        (4.00, 6.15, "lookup tables", "trips, nodes,\ndeadhead arcs", "#3b6ea8"),
        (7.00, 6.15, "configuration", "algorithm,\nscope, starts", "#3b6ea8"),
        (1.00, 4.45, "timetable.py", "headway paths\nand variants", "#2d8a5f"),
        (4.00, 4.45, "blocks.py", "compatibility graph\nand matching", "#2d8a5f"),
        (7.00, 4.45, "ev_assignment.py", "EV/ICE block\nselection", "#2d8a5f"),
        (10.00, 4.45, "ev_charging.py", "battery and\ncharging insertion", "#2d8a5f"),
        (1.00, 2.75, "capacity.py", "parking and\ncharger reservations", "#bd7420"),
        (4.00, 2.75, "output writer", "MINOA JSON\nvehicleBlockList", "#bd7420"),
        (7.00, 2.75, "costs.py", "fixed, break,\npull, CO2 audit", "#bd7420"),
        (1.00, 1.05, "validator run", "external feasibility\nand objective", "#b44949"),
        (4.00, 1.05, "metrics parser", "tables and\nsummary rows", "#b44949"),
        (7.00, 1.05, "figure scripts", "graph, fleet,\ncost, resource views", "#b44949"),
        (10.00, 1.05, "thesis output", "reported results\nand discussion", "#b44949"),
    ]
    for x, y, title, body, color in modules:
        _round(ax, x, y, 2.28, 0.70, "#ffffff", color, lw=1.0)
        ax.text(x + 1.14, y + 0.47, title, ha="center", fontsize=8.4, weight="bold", color="#263445")
        ax.text(x + 1.14, y + 0.20, body, ha="center", fontsize=6.9, color="#596579", linespacing=0.95)

    connections = [
        ((3.28, 6.50), (3.95, 6.50)),
        ((6.28, 6.50), (6.95, 6.50)),
        ((2.14, 6.15), (2.14, 5.15)),
        ((5.14, 6.15), (5.14, 5.15)),
        ((2.28, 4.80), (3.95, 4.80)),
        ((6.28, 4.80), (6.95, 4.80)),
        ((9.28, 4.80), (9.95, 4.80)),
        ((11.14, 4.45), (11.14, 3.45)),
        ((2.14, 4.45), (2.14, 3.45)),
        ((5.14, 4.45), (5.14, 3.45)),
        ((8.14, 4.45), (8.14, 3.45)),
        ((2.28, 3.10), (3.95, 3.10)),
        ((6.28, 3.10), (6.95, 3.10)),
        ((5.14, 2.75), (5.14, 1.75)),
        ((8.14, 2.75), (8.14, 1.75)),
        ((2.28, 1.40), (3.95, 1.40)),
        ((6.28, 1.40), (6.95, 1.40)),
        ((9.28, 1.40), (9.95, 1.40)),
    ]
    for start, end in connections:
        _arrow(ax, start, end, "#667085")

    ax.text(
        11.15,
        6.52,
        "All four algorithms\nreuse the same data,\nwriter and metrics.",
        ha="center",
        va="center",
        fontsize=8.0,
        color="#334155",
        bbox=dict(boxstyle="round,pad=0.25", fc="#ffffff", ec="#cbd5e1"),
    )
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def make_reporting_loop(path: Path) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(13.4, 7.2), dpi=180)
    ax.axis("off")
    ax.set_xlim(0, 13.4)
    ax.set_ylim(0, 7.2)
    ax.text(6.7, 6.82, "Output and Visualization Network", ha="center", fontsize=16.5, weight="bold")
    ax.text(
        6.7,
        6.48,
        "The same output files feed every table and plot; figures are explanatory views, not separate experiments.",
        ha="center",
        fontsize=9.4,
        color="#596579",
    )

    algorithms = [
        (0.65, "Greedy"),
        (3.05, "Path-cover"),
        (5.45, "Weighted\npath-cover"),
        (7.85, "Multi-start\npath-cover"),
    ]
    for x, title in algorithms:
        _round(ax, x, 5.15, 1.65, 0.78, "#edf4ff", "#3b6ea8", lw=1.0)
        ax.text(x + 0.82, 5.54, title, ha="center", va="center", fontsize=8.3, weight="bold", color="#263445")

    _round(ax, 4.00, 3.95, 3.10, 0.82, "#eefbf4", "#2d8a5f", lw=1.1)
    ax.text(5.55, 4.36, "MINOA-compatible JSON schedules", ha="center", fontsize=9.0, weight="bold")
    _round(ax, 7.95, 3.95, 2.65, 0.82, "#fff0f0", "#b44949", lw=1.1)
    ax.text(9.27, 4.36, "external feasibility check", ha="center", fontsize=9.0, weight="bold")
    _round(ax, 4.45, 2.65, 5.25, 0.82, "#fff6e8", "#bd7420", lw=1.1)
    ax.text(7.07, 3.06, "metric row: cost, vehicles, EV/ICE, trips, deadhead, break, charge, runtime", ha="center", fontsize=8.2, weight="bold")

    outputs = [
        (0.85, 1.10, "algorithm\ncomparison"),
        (3.15, 1.10, "cost\naudit"),
        (5.45, 1.10, "vehicle\njourneys"),
        (7.75, 1.10, "resource\npressure"),
        (10.05, 1.10, "efficiency\nplots"),
    ]
    for x, y, title in outputs:
        _round(ax, x, y, 1.65, 0.80, "#f8fafc", "#64748b", lw=1.0)
        ax.text(x + 0.82, y + 0.40, title, ha="center", va="center", fontsize=8.0, color="#263445", weight="bold")

    for x, _ in algorithms:
        _arrow(ax, (x + 0.82, 5.15), (5.10, 4.77), "#667085")
    _arrow(ax, (7.10, 4.36), (7.94, 4.36), "#667085")
    _arrow(ax, (9.27, 3.95), (7.07, 3.47), "#667085")
    for x, _, _ in outputs:
        _arrow(ax, (7.07, 2.65), (x + 0.82, 1.92), "#667085")

    ax.text(
        11.55,
        4.05,
        "One checked output\ncan be read from\nseveral perspectives.",
        ha="center",
        va="center",
        fontsize=8.1,
        color="#334155",
        bbox=dict(boxstyle="round,pad=0.28", fc="#ffffff", ec="#cbd5e1"),
    )
    ax.text(
        6.7,
        0.42,
        "This network is used in the results chapter to connect aggregate tables with graph, vehicle, cost and capacity interpretations.",
        ha="center",
        fontsize=8.8,
        color="#596579",
    )
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def _round(ax, x, y, w, h, face, edge, lw=1.0):
    from matplotlib.patches import FancyBboxPatch

    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.025,rounding_size=0.12", facecolor=face, edgecolor=edge, lw=lw))


def _node(ax, x, y, label, face):
    import matplotlib.pyplot as plt

    ax.add_patch(plt.Circle((x, y), 0.36, facecolor=face, edgecolor="#475467", lw=1.1))
    ax.text(x, y, label, ha="center", va="center", fontsize=9.2, weight="bold")


def _arrow(ax, start, end, color="#263445", dashed=False):
    from matplotlib.patches import FancyArrowPatch

    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=12, lw=1.2, color=color, linestyle="--" if dashed else "-"))


def _curved_arrow(ax, start, end, color, rad=0.2):
    from matplotlib.patches import FancyArrowPatch

    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=14, lw=1.4, color=color, connectionstyle=f"arc3,rad={rad}"))


if __name__ == "__main__":
    main()
