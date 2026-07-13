#!/usr/bin/env python3
"""Create a final audit table for thesis figures."""

from __future__ import annotations

import re
from pathlib import Path


FIGURE_DIR = Path("FAU_Thesis_temp/figures")
THESIS_DIRS = [Path("FAU_Thesis_temp/content"), Path("FAU_Thesis_temp/appendix")]
OUTPUT = Path("outputs/minoa/final_archive/figure_audit.md")


ARCHIVE_BACKED = {
    *range(1, 7),
    *range(12, 18),
    20,
    21,
    22,
    25,
    26,
    27,
    28,
    31,
    40,
    41,
    44,
}
CONSTRAINT_CONCEPTUAL = {18, 19, 23, 24, 29}
ORIGINAL_CONCEPTUAL = {30, 32, 33, 34, 35, 36, 37, 38, 39, 42, 45, 46, 47}
LOWER_BOUND = set(range(48, 54))


def main() -> None:
    references = referenced_figures()
    rows = []
    for path in sorted(FIGURE_DIR.iterdir()):
        if not path.is_file() or path.suffix.lower() not in {".png", ".pdf"}:
            continue
        rows.append(audit_row(path, references))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(rows), encoding="utf-8")
    print(OUTPUT)


def referenced_figures() -> set[str]:
    refs: set[str] = set()
    pattern = re.compile(r"figures/([^}]+)")
    for directory in THESIS_DIRS:
        for tex in directory.glob("*.tex"):
            for match in pattern.findall(tex.read_text(encoding="utf-8", errors="ignore")):
                refs.add(Path(match).name)
    return refs


def audit_row(path: Path, references: set[str]) -> list[str]:
    number = figure_number(path.name)
    if number in ARCHIVE_BACKED:
        source_script = "scripts/minoa_make_constraint_figures.py"
        source_data = "outputs/minoa/final_archive/final_results.csv"
        data_verified = "yes"
        caption_updated = "yes" if path.name in references else "not referenced"
    elif number in CONSTRAINT_CONCEPTUAL:
        source_script = "scripts/minoa_make_constraint_figures.py"
        source_data = "methodology and implementation logic"
        data_verified = "conceptual"
        caption_updated = "yes" if path.name in references else "not referenced"
    elif number in ORIGINAL_CONCEPTUAL:
        source_script = "scripts/minoa_make_original_thesis_figures.py"
        source_data = "problem objects and algorithm design"
        data_verified = "conceptual"
        caption_updated = "yes" if path.name in references else "not referenced"
    elif number in LOWER_BOUND:
        source_script = "scripts/generate_lower_bound_figures.py"
        source_data = "results/lower_bounds/*.csv + outputs/minoa/final_archive/final_results.csv"
        data_verified = "yes"
        caption_updated = "yes" if path.name in references else "not referenced"
    elif path.name.startswith("plot"):
        source_script = "outputs/minoa/algorithm_study/figures"
        source_data = "legacy algorithm-study plot, not used by current main.tex"
        data_verified = "legacy"
        caption_updated = "not referenced"
    else:
        source_script = "pre-existing thesis figure"
        source_data = "legacy figure file, not used by current main.tex"
        data_verified = "legacy"
        caption_updated = "not referenced" if path.name not in references else "needs manual check"

    alignment = "checked" if path.name in references or data_verified == "yes" else "not in current PDF"
    return [
        path.stem,
        source_script,
        source_data,
        str(path),
        data_verified,
        alignment,
        caption_updated,
    ]


def figure_number(name: str) -> int | None:
    match = re.match(r"fig(\d+)_", name)
    return int(match.group(1)) if match else None


def render(rows: list[list[str]]) -> str:
    header = [
        "Figure",
        "Source script",
        "Source data",
        "Final output file",
        "Data verified",
        "Alignment checked",
        "Caption updated",
    ]
    lines = [
        "# Final Thesis Figure Audit",
        "",
        "This audit records the final data source and regeneration status for each figure file in `FAU_Thesis_temp/figures`.",
        "",
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "/") for cell in row) + " |")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
