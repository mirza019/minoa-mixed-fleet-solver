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
  run_experiment.py            Main one-command runner with --algorithm and --scope
  print_final_results_table.py Recreates/checks the final thesis archive table
  minoa_solver.py              Single-instance solver CLI
  minoa_optimize.py            Multi-start search for stronger headline results
  minoa_pipeline.py            Normalizes raw inputs, solves, validates, reports
  minoa_report.py              External-validator table reporter
  validate_pipeline_outputs.py Revalidates all outputs listed in a manifest
  run_sml_experiments.py       Legacy Small/Medium/Large convenience runner
  run_all_experiments.py       Legacy all-instance convenience runner
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
  Final Results Check          Checks the final no-regression archive table
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
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

Java is required for the desktop validator:

```bash
java -version
```

## Quick Start

From a clean checkout, run the following commands:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Optional: remove old generated files before a fresh run.
rm -rf outputs/minoa data/processed/minoa results/lower_bounds

# Run the final method on Small, Medium, and Large.
.venv/bin/python scripts/run_experiment.py --algorithm multistart --scope sml

# Run the final method on all Senior instances.
.venv/bin/python scripts/run_experiment.py --algorithm multistart --scope all

# Print/check the retained final no-regression archive table.
.venv/bin/python scripts/print_final_results_table.py \
  --summary-file outputs/minoa/final_pipeline/final_results_summary.md

# Run the unit tests.
.venv/bin/python -m pytest
```

## Double-Click Launchers

For users who prefer not to type commands, the repository contains numbered
launchers in separate operating-system folders. Open `README_RUN_FIRST.txt` and
use the files in order:

```text
macOS folder:
launchers/macos/01_setup.command
-> launchers/macos/02_run_sml.command
-> launchers/macos/03_run_all.command
-> launchers/macos/04_print_final_table.command
-> launchers/macos/05_validate_all_outputs.command
-> launchers/macos/06_run_lower_bounds.command
-> launchers/macos/07_generate_lower_bound_figures.command
-> launchers/macos/08_run_tests.command

Windows folder:
launchers/windows/01_setup.bat
-> launchers/windows/02_run_sml.bat
-> launchers/windows/03_run_all.bat
-> launchers/windows/04_print_final_table.bat
-> launchers/windows/05_validate_all_outputs.bat
-> launchers/windows/06_run_lower_bounds.bat
-> launchers/windows/07_generate_lower_bound_figures.bat
-> launchers/windows/08_run_tests.bat
```

The setup file creates `.venv` and installs the Python requirements. Each later
launcher calls the virtual environment's Python interpreter directly, so
activation does not need to persist between separate launcher windows. The
experiment launchers also check for Java and the MINOA validator path before
starting the pipeline. If a file is opened out of order, it prints the required
previous step instead of showing a Python traceback.

`run_experiment.py` always means "run a fresh experiment". With `--scope all`,
the command generates output JSON files, passes the generated input/output pairs
through the validator inside the pipeline, and prints the resulting table.
Because the multi-start search is bounded, a fresh direct run can produce a
slightly different feasible schedule than the retained final archive.

`print_final_results_table.py` is a separate result-check command. It creates or
checks `results/final_validated_results.json`, prints the retained final archive
table, writes the same Markdown summary to
`outputs/minoa/final_pipeline/final_results_summary.md`, and creates the compact
archive CSV under `outputs/minoa/final_archive/` if that CSV is absent.

## Run Experiments

Use the same command pattern for all implemented algorithms:

```bash
.venv/bin/python scripts/run_experiment.py --algorithm <name> --scope <instances>
```

The four algorithm names are:

```text
greedy       constructive greedy baseline
pathcover    unweighted path-cover method
weighted     weighted path-cover method
multistart   final multi-start weighted path-cover method
```

The instance scope can be:

```text
sml   Small, Medium, and Large only
all   all 12 MINOA Senior instances
```

Example:

```bash
.venv/bin/python scripts/run_experiment.py --algorithm multistart --scope sml
```

This command generates output JSON files, runs the validator inside the
pipeline, and prints the result table.

To run one headline instance only, add `--only`:

```bash
.venv/bin/python scripts/run_experiment.py --algorithm multistart --scope sml --only Small
```

Run all four algorithms on Small, Medium, and Large:

```bash
.venv/bin/python scripts/run_experiment.py --algorithm greedy --scope sml
.venv/bin/python scripts/run_experiment.py --algorithm pathcover --scope sml
.venv/bin/python scripts/run_experiment.py --algorithm weighted --scope sml
.venv/bin/python scripts/run_experiment.py --algorithm multistart --scope sml
```

Run all four algorithms on all Senior instances:

```bash
.venv/bin/python scripts/run_experiment.py --algorithm greedy --scope all
.venv/bin/python scripts/run_experiment.py --algorithm pathcover --scope all
.venv/bin/python scripts/run_experiment.py --algorithm weighted --scope all
.venv/bin/python scripts/run_experiment.py --algorithm multistart --scope all
```

Fresh all-instance runs create output JSON files under
`outputs/minoa/all_<algorithm>/`, create processed working inputs under
`data/processed/minoa/all_<algorithm>/`, run the validator inside the pipeline,
and print the fresh result table. For the final method, the default output
folder is `outputs/minoa/all_multistart/`.

Because the multi-start search is bounded, a fresh direct run can produce a
slightly different feasible schedule than the retained final archive. For the
retained final no-regression archive summary, use:


```bash
.venv/bin/python scripts/print_final_results_table.py \
  --summary-file outputs/minoa/final_pipeline/final_results_summary.md
```

This creates/checks `results/final_validated_results.json`, writes
`outputs/minoa/final_pipeline/final_results_summary.md`, creates the compact
archive CSV under `outputs/minoa/final_archive/` if needed, and prints the
retained final archive table. The retained all-instance archive result is total
validated cost `10000.48` and `126` used vehicle blocks.

## Validate Existing Input/Output Pairs

The experiment runner already generates output JSON files, runs the validator
inside the pipeline, and prints the result table. For a fresh clone, generate
the Small/Medium/Large outputs first:

```bash
.venv/bin/python scripts/run_experiment.py --algorithm multistart --scope sml
```

Use `minoa_report.py` only after those output JSON files exist and you want to
recheck selected input/output pairs with the validator and print the table
again.

```bash
.venv/bin/python scripts/minoa_report.py \
  data/raw/minoa/senior/Small_Input_S.json:outputs/minoa/sml_multistart/Small_Output_multistart.json \
  data/raw/minoa/senior/Medium_Input_S.json:outputs/minoa/sml_multistart/Medium_Output_multistart.json \
  data/raw/minoa/senior/Large_Input_S.json:outputs/minoa/sml_multistart/Large_Output_multistart.json
```

After an all-instance pipeline run, revalidate every generated output listed in
the pipeline manifest with:

```bash
.venv/bin/python scripts/validate_pipeline_outputs.py \
  --manifest outputs/minoa/all_multistart/pipeline_manifest.json
```

If a different output directory was used, point `--manifest` to that run's
`pipeline_manifest.json` file. For example:

```bash
.venv/bin/python scripts/validate_pipeline_outputs.py \
  --manifest outputs/minoa/all_weighted/pipeline_manifest.json
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

For all Senior instances, first run the final method. This creates generated
outputs, processed working inputs, and
`outputs/minoa/final_archive/final_results.csv`.

```bash
.venv/bin/python scripts/run_experiment.py --algorithm multistart --scope all
```

Then run the lower-bound report and regenerate the thesis figures:

```bash
.venv/bin/python scripts/run_lower_bounds.py \
  --scope all \
  --input-dir data/processed/minoa/all_multistart \
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

First make sure the compact final archive table exists:

```bash
.venv/bin/python scripts/print_final_results_table.py \
  --summary-file outputs/minoa/final_pipeline/final_results_summary.md
```

This command prints the canonical final no-regression archive table used in the
thesis, reports total validated cost `10000.48` and `126` vehicles, and creates
`outputs/minoa/final_archive/final_results.csv` if it is absent.

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
.venv/bin/python scripts/run_experiment.py --algorithm multistart --scope all

.venv/bin/python scripts/run_lower_bounds.py \
  --scope all \
  --input-dir data/processed/minoa/all_multistart \
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
| `python: command not found` | macOS may provide `python3` but not `python`. | Use `python3 -m venv .venv`, then `source .venv/bin/activate`. |
| `No module named pytest` | Dependencies were not installed from the current `requirements.txt`. | Run `python3 -m pip install -r requirements.txt` after activating `.venv`. |
| `java: command not found` | Java is not installed or not on `PATH`. | Install a Java runtime and check with `java -version`. |
| Solver output is feasible but not exactly the archive cost | Multi-start search is heuristic and may find a different feasible candidate. | Use `.venv/bin/python scripts/print_final_results_table.py --summary-file outputs/minoa/final_pipeline/final_results_summary.md` for the exact thesis archive table. |
| Generated files appear in `git status` | A local ignore rule is missing or the file is outside ignored output folders. | Keep generated runs under `outputs/minoa/`, `data/processed/minoa/`, or `results/lower_bounds/`. |
| A raw input file cannot be parsed | One downloaded benchmark file may need a processed working copy. | Use the pipeline commands; they write normalized working files under `data/processed/minoa/` without changing raw inputs. |
