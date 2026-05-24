from __future__ import annotations

from pathlib import Path

from .table import enrich_best
from ..types import JsonDict


def write_csv(rows: list[JsonDict], output_path: Path) -> None:
    import csv

    output_path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "instance",
        "approach",
        "valid",
        "objective",
        "total_blocks",
        "ev_blocks",
        "ice_blocks",
        "ev_share",
        "selected_trips",
        "deadhead_min",
        "break_min",
        "charging_min",
    ]
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column) for column in columns})


def plot_objective_comparison(rows: list[JsonDict], output_path: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = _canonical_instance_order(rows)
    labels = [row["instance"] for row in rows]
    costs = [row["objective"] for row in rows]

    x = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=180)
    bars = ax.bar(x, costs, width=0.52, label="Best validated cost", color="#26736d")

    ax.set_title("Best Validated Cost by Instance")
    ax.set_ylabel("Official VS cost")
    ax.set_xticks(x, labels)
    ax.grid(axis="y", color="#d9d9d9", linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    _label_bars(ax, bars)

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_fleet_comparison(rows: list[JsonDict], output_path: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = _canonical_instance_order(rows)
    labels = [row["instance"] for row in rows]
    evs = [row["ev_blocks"] for row in rows]
    ice = [row["ice_blocks"] for row in rows]
    x = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=180)
    ax.bar(x, ice, label="ICE vehicles", color="#6f7785")
    ax.bar(x, evs, bottom=ice, label="EV vehicles", color="#2b8cbe")

    ax.set_title("Vehicle Count and Fleet Mix")
    ax.set_ylabel("Vehicles")
    ax.set_xticks(x, labels)
    ax.set_ylim(0, max(e + i for e, i in zip(evs, ice)) + 2)
    ax.grid(axis="y", color="#d9d9d9", linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False)

    for idx, row in enumerate(rows):
        ax.text(
            idx,
            row["total_blocks"] + 0.25,
            f'{row["total_blocks"]} veh, {row["ev_share"]:.0f}% EV',
            ha="center",
            va="bottom",
            fontsize=8,
        )

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_operational_breakdown(rows: list[JsonDict], output_path: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = _canonical_instance_order(rows)
    labels = [row["instance"] for row in rows]
    deadhead = [row["deadhead_min"] for row in rows]
    breaks = [row["break_min"] for row in rows]
    charging = [row["charging_min"] for row in rows]

    x = np.arange(len(labels))
    width = 0.24

    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=180)
    ax.bar(x - width, deadhead, width, label="Deadhead min", color="#4c78a8")
    ax.bar(x, breaks, width, label="Break min", color="#72b7b2")
    ax.bar(x + width, charging, width, label="Charging min", color="#f2b447")

    ax.set_title("Operational Time Components")
    ax.set_ylabel("Minutes")
    ax.set_xticks(x, labels)
    ax.grid(axis="y", color="#d9d9d9", linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False)

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def best_rows(rows: list[JsonDict]) -> list[JsonDict]:
    selected: dict[str, JsonDict] = {}
    for row in enrich_best(rows):
        if not row.get("valid") or row.get("objective") is None:
            continue
        current = selected.get(row["instance"])
        if current is None or row["objective"] < current["objective"]:
            selected[row["instance"]] = row
    return _canonical_instance_order(list(selected.values()))


def _canonical_instance_order(rows: list[JsonDict]) -> list[JsonDict]:
    order = {"Small": 0, "Medium": 1, "Large": 2}
    return sorted(rows, key=lambda row: order.get(row["instance"], 99))


def _label_bars(ax, bars) -> None:
    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{height:.1f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
        )
