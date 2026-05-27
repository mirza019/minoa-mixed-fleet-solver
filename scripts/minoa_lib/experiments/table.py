from __future__ import annotations

from pathlib import Path

from .metrics import evaluate_solution
from ..types import JsonDict


DEFAULT_COLUMNS = [
    ("Instance", "instance"),
    ("Approach", "approach"),
    ("Valid", "valid"),
    ("Cost", "objective"),
    ("Fixed", "fixed_cost"),
    ("Break cost", "break_cost"),
    ("Pull cost", "pull_cost"),
    ("CO2 cost", "co2_cost"),
    ("Best cost", "best_objective"),
    ("Gap to best (%)", "gap_to_best"),
    ("Vehicles", "total_blocks"),
    ("EV vehicles", "ev_blocks"),
    ("ICE vehicles", "ice_blocks"),
    ("EV share (%)", "ev_share"),
    ("Trips", "selected_trips"),
    ("Deadhead min", "deadhead_min"),
    ("Break min", "break_min"),
    ("Charge min", "charging_min"),
]


def enrich_best(rows: list[JsonDict]) -> list[JsonDict]:
    best_by_instance: dict[str, float] = {}
    for row in rows:
        if row["objective"] is None:
            continue
        key = row["instance"]
        best_by_instance[key] = min(row["objective"], best_by_instance.get(key, row["objective"]))

    enriched = []
    for row in rows:
        new_row = dict(row)
        best = best_by_instance.get(row["instance"])
        new_row["best_objective"] = best
        if row["objective"] is None or best is None or best == 0:
            new_row["gap_to_best"] = None
        else:
            new_row["gap_to_best"] = 100.0 * (row["objective"] - best) / best
        enriched.append(new_row)
    return enriched


def format_value(value: object) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def markdown_table(rows: list[JsonDict]) -> str:
    rows = enrich_best(rows)
    headers = [header for header, _ in DEFAULT_COLUMNS]
    rendered_rows = [
        [format_value(row.get(key)) for _, key in DEFAULT_COLUMNS]
        for row in rows
    ]
    widths = [
        max(len(headers[i]), *(len(row[i]) for row in rendered_rows)) if rendered_rows else len(headers[i])
        for i in range(len(headers))
    ]

    def render_line(values: list[str]) -> str:
        return "| " + " | ".join(value.ljust(widths[i]) for i, value in enumerate(values)) + " |"

    separator = "| " + " | ".join("-" * widths[i] for i in range(len(headers))) + " |"
    lines = [render_line(headers), separator]
    lines.extend(render_line(row) for row in rendered_rows)
    return "\n".join(lines)


def evaluate_many(input_outputs: list[tuple[Path, Path]], validator_path: Path) -> list[JsonDict]:
    return [
        evaluate_solution(input_path, output_path, validator_path)
        for input_path, output_path in input_outputs
    ]
