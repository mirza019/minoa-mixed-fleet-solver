#!/usr/bin/env python3
"""Regenerate the explanatory figures used in the thesis draft.

The figures created here are derived from the implemented MINOA workflow and
the stored experiment summaries. They are meant for documentation and thesis
explanation, not for changing solver results.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


FIGURE_SCRIPTS = [
    "scripts/minoa_make_original_thesis_figures.py",
    "scripts/minoa_make_constraint_figures.py",
]


def main() -> None:
    for script in FIGURE_SCRIPTS:
        print(f"=== Regenerating figures with {script} ===", flush=True)
        subprocess.run([sys.executable, script], cwd=ROOT, check=True)

    out_dir = ROOT / "FAU_Thesis_temp" / "figures"
    generated = sorted(path.name for path in out_dir.glob("fig*.png"))
    print()
    print(f"Figure directory: {out_dir}")
    print(f"Available fig*.png files: {len(generated)}")
    for name in generated:
        print(f"- {name}")


if __name__ == "__main__":
    main()
