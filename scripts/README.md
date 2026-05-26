# Scripts

This folder contains the executable entry points for solving MINOA instances,
validating generated outputs, producing result tables, and creating thesis
support material.

## Recommended Commands

Use these two scripts for normal reproducible experiments:

```bash
.venv/bin/python scripts/run_sml_experiments.py
.venv/bin/python scripts/run_all_experiments.py
```

`run_sml_experiments.py` is the professor-friendly headline runner for Small,
Medium, and Large. It uses the multi-start path-cover method and prints a
validator-backed table.

`run_all_experiments.py` runs every available senior instance. It keeps raw data
unchanged, creates processed working copies when needed, solves the instances,
validates the outputs, and prints one all-instance result table.

## Main Entry Points

| File | Purpose |
|---|---|
| `run_sml_experiments.py` | Runs Small, Medium, and Large with the optimized multi-start path-cover method. |
| `run_all_experiments.py` | Runs the full senior benchmark through the automatic pipeline. |
| `minoa_solver.py` | Solves one instance with a selected constructive builder. Useful for quick checks. |
| `minoa_optimize.py` | Runs multi-start/local-search variants for stronger single-instance results. |
| `minoa_pipeline.py` | Normalizes raw inputs into validator-safe working copies, solves, validates, repairs parking overflows when possible, and reports all rows. |
| `minoa_report.py` | Takes existing input/output pairs, runs the official validator, and prints a Markdown table. |
| `minoa_make_latex_thesis.py` | Generates LaTeX thesis-support material from experiment data. |
| `minoa_make_thesis.py` | Generates document-style thesis-support material. |
| `minoa_thesis_report.py` | Builds thesis-oriented summaries and figures from available reports. |

## Subfolders

| Folder | Purpose |
|---|---|
| `minoa_lib/` | Reusable solver modules. The real implementation logic lives here. |
| `ci/` | Shell wrappers used by GitHub Actions workflows. |

Generated outputs are written under `outputs/`, which is intentionally ignored
by Git.
