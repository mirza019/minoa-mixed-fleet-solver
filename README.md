# MINOA Mixed-Fleet Bus Scheduling Solver

This repository contains my Python implementation for the MINOA senior
challenge. The task is to select timetable trips, build vehicle schedules, assign
electric or conventional buses, and add charging when it is possible.

The main method is a **multi-start path-cover matheuristic**. Here, this means a
practical heuristic that uses graph-optimization ideas. In simple words, the
solver creates several timetable variants, connects compatible trips in a graph,
turns graph paths into vehicle blocks, assigns ICE/EV vehicles, and then checks
the final output with an external feasibility and objective audit.

## Repository Contents

```text
scripts/
  minoa_solver.py              Single-instance solver CLI
  minoa_optimize.py            Multi-start search for stronger headline results
  minoa_pipeline.py            Normalizes raw inputs, solves, validates, reports
  minoa_report.py              External-validator table reporter
  run_experiment.py            One-command runner with --algorithm
  run_sml_experiments.py       Small/Medium/Large experiment runner
  run_all_experiments.py       All-instance experiment runner
  run_lower_bounds.py          Global and selected-timetable bound reporter
  generate_lower_bound_figures.py  Lower-bound plots from CSV results
  minoa_lib/                   Solver modules

data/raw/minoa/senior/
  Raw MINOA senior JSON instances

tools/minoa/desktopValidator/desktopValidator/desktopValidator.jar
  Official desktop validator jar used for external feasibility checks

.github/workflows/
  MINOA Headline Instances     Runs Small, Medium, Large separately
  MINOA All Instances          Runs all senior instances
  Final Results Check          Checks the canonical thesis result table
```

Generated outputs are written mainly under `outputs/minoa/` and processed
working inputs under `data/processed/minoa/`. These folders are ignored by Git
because they are recreated by the runner commands. The raw Senior input files
under `data/raw/minoa/senior/` are tracked and are not modified by the solver.

## Method Summary

The main idea has four steps:

1. **Timetable variants:** selects timetable-feasible trips for each
   line and direction.
2. **Compatibility graph:** each selected trip is a graph node; an arc
   \(i \rightarrow j\) exists if one bus can operate trip \(j\) after trip \(i\).
3. **Weighted path cover:** each selected graph path becomes one vehicle block.
   Reducing the number of paths reduces the number of vehicles.
4. **Mixed-fleet check:** blocks are assigned to ICE/EV vehicles, EV autonomy is
   simulated, charging is inserted, and capacity is checked.

The official validator is used as an **external feasibility check** for reported
results. It is not used to derive or repair the solution structure.

## Installation

Use Python 3.9 or newer. The GitHub Actions workflows use Python 3.11.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Java is required for the desktop validator:

```bash
java -version
```

## Quick Start

From a clean checkout, run the following commands:

```bash
source .venv/bin/activate

# Optional: remove old generated files before a fresh run.
rm -rf outputs/minoa data/processed/minoa results/lower_bounds

# Professor-facing thesis-result pipeline.
# Creates/checks results/final_validated_results.json and prints the final table.
python scripts/run_experiment.py --algorithm multistart --scope all

# Generate and audit Small, Medium, and Large output JSON files.
python scripts/run_experiment.py --algorithm multistart --scope sml

# Run the unit tests.
python -m pytest
```

The first command with `--scope all` is the shortest professor-facing
reproducibility command. It creates or checks
`results/final_validated_results.json`, prints the final thesis table, and
writes the same Markdown summary to
`outputs/minoa/final_pipeline/final_results_summary.md`. If the JSON file was
deleted in a fresh clone, the command recreates it before checking the expected
Small, Medium, Large, and all-instance values.
The second command regenerates fresh heuristic output files for Small, Medium,
and Large and checks them with the external audit. Because multi-start search is
bounded, a fresh direct search can produce a slightly different feasible
schedule than the retained archive; report such a run separately instead of
silently replacing the archive.

## Run Small, Medium, and Large

This command runs the main method on Small, Medium, and Large. It validates the
outputs and prints a table.

```bash
.venv/bin/python scripts/run_sml_experiments.py
```

The same run can also be started through the algorithm-selecting wrapper:

```bash
.venv/bin/python scripts/run_experiment.py --algorithm multistart --scope sml
```

Other available algorithm names are:

```text
greedy, pathcover, weighted, multistart, ice-greedy, no-charge
```

Run one headline instance only:

```bash
.venv/bin/python scripts/run_sml_experiments.py --only Small
.venv/bin/python scripts/run_sml_experiments.py --only Medium
.venv/bin/python scripts/run_sml_experiments.py --only Large
```

Quick test:

```bash
.venv/bin/python scripts/run_sml_experiments.py --quick
```

## Run All Senior Instances

This command runs all available Senior instances through the direct pipeline.
Small, Medium, and Large use the optimized headline search. The other instances
use the robust charging-aware path-cover pipeline.

```bash
.venv/bin/python scripts/run_all_experiments.py
```

Quick all-instance test:

```bash
.venv/bin/python scripts/run_all_experiments.py --quick-headliners
```

The all-instance report is written to:

```text
outputs/minoa/all_instances/all_instances_report.md
```

For the exact final thesis archive summary, use:

```bash
.venv/bin/python scripts/run_experiment.py --algorithm multistart --scope all
```

This creates/checks `results/final_validated_results.json`, writes
`outputs/minoa/final_pipeline/final_results_summary.md`, and prints the final
no-regression archive table used in the thesis. The final all-instance result is
total validated cost `10000.48` and `126` vehicles.

For an additional fresh direct all-instance audit before printing the archive,
use:

```bash
.venv/bin/python scripts/run_experiment.py --algorithm multistart --scope all --fresh-audit
```

## Validate Existing Input/Output Pairs

Use `minoa_report.py` if output JSON files already exist and you only want to
check them with the validator and print a table.

```bash
.venv/bin/python scripts/minoa_report.py \
  data/raw/minoa/senior/Small_Input_S.json:outputs/minoa/headline/Small_Output_multi_start_pathcover.json \
  data/raw/minoa/senior/Medium_Input_S.json:outputs/minoa/headline/Medium_Output_multi_start_pathcover.json \
  data/raw/minoa/senior/Large_Input_S.json:outputs/minoa/headline/Large_Output_multi_start_pathcover.json
```

## Lower-Bound Reports

The feasible schedules are upper bounds. Lower-bound reporting is separated
into two scopes:

- `Global LB`: a globally valid timetable-overlap lower bound, or `0.0` when no
  certified value is available within the time limit.
- `Selected-TT LB`: a diagnostic lower bound for the timetable already selected
  by one output file. This is useful for analysis, but it is not a global
  optimality certificate.

Run the lower-bound report for Small, Medium, and Large:

```bash
.venv/bin/python scripts/run_lower_bounds.py \
  --scope sml \
  --time-limit 60 \
  --output-csv results/lower_bounds/sml_lower_bounds.csv
```

Run it for all senior instances and regenerate the thesis figures:

```bash
.venv/bin/python scripts/run_lower_bounds.py \
  --scope all \
  --input-dir data/processed/minoa/final_adaptive_bounded \
  --archive-csv outputs/minoa/final_archive/final_results.csv \
  --time-limit 180 \
  --output-csv results/lower_bounds/all_instances_lower_bounds.csv

.venv/bin/python scripts/generate_lower_bound_figures.py \
  --csv results/lower_bounds/all_instances_lower_bounds.csv \
  --out-dir FAU_Thesis_temp/figures
```

## Regenerate Thesis Result Graphs

Use the commands in this section when you only want to regenerate the numerical
graphs used in the thesis result chapter. These commands do not regenerate the
conceptual workflow diagrams or method flowcharts.

First make sure the final verified archive exists:

```bash
.venv/bin/python scripts/run_experiment.py --algorithm multistart --scope all
```

This command prints the canonical final no-regression archive table used in the
thesis, which reports total validated cost `10000.48` and `126` vehicles. To
rerun the direct all-instance pipeline as an additional audit before printing
the archive, add `--fresh-audit`.

Then regenerate the result graphs based on the final validated archive:

```bash
.venv/bin/python scripts/minoa_make_constraint_figures.py
```

This updates the cost, fleet-mix, operational-component, efficiency,
resource-pressure, and all-instance result graphs in:

```text
FAU_Thesis_temp/figures/
```

If the lower-bound graphs are also needed, first refresh the lower-bound CSV and
then regenerate the lower-bound figures:

```bash
.venv/bin/python scripts/run_lower_bounds.py \
  --scope all \
  --input-dir data/processed/minoa/final_adaptive_bounded \
  --archive-csv outputs/minoa/final_archive/final_results.csv \
  --time-limit 180 \
  --output-csv results/lower_bounds/all_instances_lower_bounds.csv

.venv/bin/python scripts/generate_lower_bound_figures.py \
  --csv results/lower_bounds/all_instances_lower_bounds.csv \
  --out-dir FAU_Thesis_temp/figures
```

Finally, create a figure audit file that records which graph came from which
data source:

```bash
.venv/bin/python scripts/minoa_figure_audit.py
```

The audit is written to:

```text
outputs/minoa/final_archive/figure_audit.md
```

Note: `scripts/generate_thesis_figures.py` regenerates both numerical result
graphs and conceptual method figures. For result graphs only, use the commands
above.

## Headline Results

Current headline results:

The canonical machine-readable thesis result file is:

```text
results/final_validated_results.json
```

This file is part of the reproducibility material. It records the final
no-regression archive used in the thesis and is checked by GitHub Actions.

The compact final thesis result table is:

| Scope | Instance / Benchmark | Validated cost | Vehicles |
|---|---:|---:|---:|
| Headline | Small | 162.44 | 2 |
| Headline | Medium | 371.35 | 5 |
| Headline | Large | 1163.35 | 15 |
| Headline total | Small + Medium + Large | 1697.15 | 22 |
| Full Senior benchmark | 12 instances total | 10000.48 | 126 |

The detailed table below is the final archive used for the thesis. A fresh multi-start
run is a search procedure and may find an equal or better candidate when it is
allowed to use the full time limit. In that case, the new output should be
validated and reported separately instead of silently replacing the archived
thesis table.

| Instance | Approach | Valid | Cost | Vehicles | EV | ICE | EV share | Trips | Deadhead min | Break min | Charge min |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Small | Multi-start path-cover | yes | 162.44 | 2 | 0 | 2 | 0.00% | 48 | 42.00 | 240.00 | 0.00 |
| Medium | Multi-start path-cover | yes | 371.35 | 5 | 5 | 0 | 100.00% | 139 | 752.00 | 1717.00 | 391.00 |
| Large | Multi-start path-cover | yes | 1163.35 | 15 | 5 | 10 | 33.33% | 260 | 2600.00 | 2520.00 | 505.00 |

Headline totals:

| Metric | Value |
|---|---:|
| Total cost | 1697.15 |
| Total vehicles | 22 |
| EV vehicles | 10 |
| ICE vehicles | 12 |

## Algorithm Comparison

This table shows how the method improved step by step.

| Instance | Method | Valid | Cost | Vehicles | EV | ICE | EV share | Trips | Possible trips | Selected | Deadhead | Break | Charge |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Small | Greedy constructive | yes | 317.17 | 4 | 2 | 2 | 50.00% | 48 | 1064 | 4.51% | 82.00 | 586.00 | 0.00 |
| Small | Path-cover | yes | 248.79 | 3 | 1 | 2 | 33.33% | 48 | 1064 | 4.51% | 98.00 | 722.00 | 0.00 |
| Small | Charging-aware path-cover | yes | 213.55 | 3 | 3 | 0 | 100.00% | 48 | 1064 | 4.51% | 402.00 | 418.00 | 243.00 |
| Small | Multi-start path-cover | yes | 162.44 | 2 | 0 | 2 | 0.00% | 48 | 1064 | 4.51% | 42.00 | 240.00 | 0.00 |
| Medium | Greedy constructive | yes | 497.11 | 6 | 2 | 4 | 33.33% | 139 | 3368 | 4.13% | 771.00 | 2558.00 | 0.00 |
| Medium | Path-cover | no | - | 6 | 2 | 4 | 33.33% | 139 | 3368 | 4.13% | 931.00 | 2398.00 | 0.00 |
| Medium | Charging-aware path-cover | yes | 458.40 | 6 | 5 | 1 | 83.33% | 139 | 3368 | 4.13% | 847.00 | 2482.00 | 749.00 |
| Medium | Multi-start path-cover | yes | 371.35 | 5 | 5 | 0 | 100.00% | 139 | 3368 | 4.13% | 752.00 | 1717.00 | 391.00 |
| Large | Greedy constructive | yes | 1242.33 | 15 | 0 | 15 | 0.00% | 260 | 6960 | 3.74% | 2732.00 | 2829.00 | 0.00 |
| Large | Path-cover | yes | 1259.95 | 15 | 0 | 15 | 0.00% | 260 | 6960 | 3.74% | 2351.00 | 3210.00 | 0.00 |
| Large | Charging-aware path-cover | yes | 1169.28 | 15 | 5 | 10 | 33.33% | 260 | 6960 | 3.74% | 3215.00 | 2346.00 | 686.00 |
| Large | Multi-start path-cover | yes | 1163.35 | 15 | 5 | 10 | 33.33% | 260 | 6960 | 3.74% | 2600.00 | 2520.00 | 505.00 |

## All-Instance Results

The all-instance run covers these 12 senior instances:

```text
Small, Medium, Large, Toy Example,
1line, 1line 6timeWindow,
2lines, 2lines 6 timeWindows,
3lines, 3linesTriangle,
5lines, 8lines
```

Current all-instance totals:

| Metric | Value |
|---|---:|
| Feasible instances | 12 / 12 |
| Total cost | 10000.48 |
| Total vehicles | 126 |
| EV vehicles | 32 |
| ICE vehicles | 94 |

The final archive is no-regression: if a new adaptive candidate is not better
than the previous validated solution for an instance, the previous solution is
kept.

## GitHub Actions

Three workflows are provided.

### Final Results Check

Workflow file:

```text
.github/workflows/results-check.yml
```

This workflow creates/checks `results/final_validated_results.json`, prints the
compact final thesis table, writes
`outputs/minoa/final_pipeline/final_results_summary.md`, and fails if any
expected final value is missing or inconsistent.

### MINOA Headline Instances

Workflow file:

```text
.github/workflows/minoa-headline-instances.yml
```

This workflow runs three separate jobs:

```text
small
medium
large
```

Each job runs the solver, validates the output, shows a result table, and uploads
the generated files as artifacts.

Manual run:

1. Open the repository on GitHub.
2. Go to **Actions**.
3. Select **MINOA Headline Instances**.
4. Click **Run workflow**.

### MINOA All Instances

Workflow file:

```text
.github/workflows/minoa-all-instances.yml
```

This workflow runs the full senior benchmark. It validates every generated
output and shows the full table on the run summary page.

Manual run:

1. Open the repository on GitHub.
2. Go to **Actions**.
3. Select **MINOA All Instances**.
4. Click **Run workflow**.

Artifacts:

| Workflow | Artifact |
|---|---|
| Final Results Check | no output artifact |
| MINOA Headline Instances | `minoa-small-outputs`, `minoa-medium-outputs`, `minoa-large-outputs` |
| MINOA All Instances | `minoa-all-instance-outputs` |

## Notes

- The validator is used only for external feasibility checking of reported
  solutions.
- Generated outputs are ignored by Git.
- Processed input copies are ignored by Git because they can be regenerated from
  the raw senior datasets.
- The LaTeX thesis files and documentation drafts are intentionally not included
  in this code repository.

## Tests and Reproducibility Checks

Run the complete lightweight test suite with:

```bash
.venv/bin/python -m pytest
```

The tests check official-rule helper functions, objective reconciliation,
command plumbing, output-directory creation, and the canonical final result
table. The GitHub Actions result check also verifies imports, runs the tests,
executes a Small-instance smoke run, prints the final archive table, and fails if
generated output, cache, or log files are accidentally tracked.

## Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| `No module named pytest` | Dependencies were not installed from the current `requirements.txt`. | Run `python -m pip install -r requirements.txt`. |
| `java: command not found` | Java is not installed or not on `PATH`. | Install a Java runtime and check with `java -version`. |
| Solver output is feasible but not exactly the archive cost | Multi-start search is heuristic and may find a different feasible candidate. | Use `python scripts/run_experiment.py --algorithm multistart --scope all` for the canonical thesis archive table. |
| Generated files appear in `git status` | A local ignore rule is missing or the file is outside ignored output folders. | Keep generated runs under `outputs/minoa/`, `data/processed/minoa/`, or `results/lower_bounds/`. |
| A raw input file cannot be parsed | One downloaded benchmark file may need a processed working copy. | Use the pipeline commands; they write normalized working files under `data/processed/minoa/` without changing raw inputs. |
