# Scripts

This folder contains the Python commands used to run the MINOA experiments.
Most users only need the two runner scripts below.

## Start Here

Run the main Small, Medium, and Large experiments:

```bash
.venv/bin/python scripts/run_sml_experiments.py
```

You can also choose an algorithm with one command:

```bash
.venv/bin/python scripts/run_experiment.py --algorithm multistart --scope sml
.venv/bin/python scripts/run_experiment.py --algorithm greedy --scope sml
.venv/bin/python scripts/run_experiment.py --algorithm weighted --scope all
```

Run all available senior instances:

```bash
.venv/bin/python scripts/run_all_experiments.py
```

Both commands create output JSON files, call the official desktop validator, and
print a result table.

## What Each Script Does

| File | What it does |
|---|---|
| `run_sml_experiments.py` | Main runner for Small, Medium, and Large. This is the easiest command for checking the headline thesis results. |
| `run_all_experiments.py` | Runs the full senior benchmark and reports all instances in one table. |
| `run_experiment.py` | One-command experiment runner where the algorithm is selected with `--algorithm`. |
| `minoa_solver.py` | Solves one input file with one selected builder. Useful for quick manual tests. |
| `minoa_optimize.py` | Runs the stronger multi-start search used for the best Small, Medium, and Large results. |
| `minoa_pipeline.py` | Runs the automatic all-instance pipeline. It prepares working input copies, solves, validates, and reports. |
| `minoa_report.py` | Takes existing input/output pairs and creates a validator-based result table. |
| `minoa_make_latex_thesis.py` | Helper script for generating LaTeX thesis material. |
| `minoa_make_thesis.py` | Helper script for generating thesis-style documentation. |
| `minoa_thesis_report.py` | Helper script for thesis summaries and figures. |

## Folder Structure

| Folder | Meaning |
|---|---|
| `minoa_lib/` | Main solver implementation, split into smaller modules. |
| `ci/` | Small shell scripts used by GitHub Actions. |

Generated files are written to `outputs/`. They are not tracked in Git because
they can be produced again by running the scripts.
