# MINOA Mixed-Fleet Bus Scheduling Solver

This repository contains my Python implementation for the MINOA senior
challenge. The task is to select timetable trips, build vehicle schedules, assign
electric or conventional buses, and add charging when it is possible.

The main method is a **multi-start path-cover matheuristic**. Here, this means a
practical heuristic that uses graph-optimization ideas. It does not use Pyomo or
Gurobi. In simple words, the solver creates several timetable variants, connects
compatible trips in a graph, turns graph paths into vehicle blocks, assigns
ICE/EV vehicles, and then checks the final output with the official desktop
validator.

## Repository Contents

```text
scripts/
  minoa_solver.py              Single-instance solver CLI
  minoa_optimize.py            Multi-start search for stronger headline results
  minoa_pipeline.py            Normalizes raw inputs, solves, validates, reports
  minoa_report.py              Validator-backed table reporter
  run_sml_experiments.py       Small/Medium/Large experiment runner
  run_all_experiments.py       All-instance experiment runner
  minoa_lib/                   Solver modules

data/raw/minoa/senior/
  Raw MINOA senior JSON instances

tools/minoa/desktopValidator/desktopValidator/desktopValidator.jar
  Official desktop validator jar used for external feasibility checks

.github/workflows/
  MINOA Headline Instances     Runs Small, Medium, Large separately
  MINOA All Instances          Runs all senior instances
```

Each important folder also has a short README:

| Path | What it explains |
|---|---|
| [`scripts/README.md`](scripts/README.md) | Which command-line script does what. |
| [`scripts/minoa_lib/README.md`](scripts/minoa_lib/README.md) | How the implementation modules are separated. |
| [`scripts/ci/README.md`](scripts/ci/README.md) | Shell wrappers used by GitHub Actions. |
| [`data/raw/minoa/README.md`](data/raw/minoa/README.md) | Raw-data handling policy. |
| [`data/raw/minoa/senior/README.md`](data/raw/minoa/senior/README.md) | Instance list and headline/additional split. |
| [`tools/minoa/README.md`](tools/minoa/README.md) | Desktop validator location and usage. |
| [`.github/workflows/README.md`](.github/workflows/README.md) | CI workflow behavior and artifacts. |

Generated outputs are written under `outputs/`. They are ignored by Git because
they can be regenerated.

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

Use Python 3.11 or newer.

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

## Run Small, Medium, and Large

This command runs the main method on Small, Medium, and Large. It validates the
outputs and prints a table.

```bash
.venv/bin/python scripts/run_sml_experiments.py
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

This command runs all available senior instances. Small, Medium, and Large use
the optimized headline search. The other instances use the robust
charging-aware path-cover pipeline.

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

## Validate Existing Input/Output Pairs

Use `minoa_report.py` if output JSON files already exist and you only want to
check them with the validator and print a table.

```bash
.venv/bin/python scripts/minoa_report.py \
  data/raw/minoa/senior/Small_Input_S.json:outputs/minoa/headline/Small_Output_multi_start_pathcover.json \
  data/raw/minoa/senior/Medium_Input_S.json:outputs/minoa/headline/Medium_Output_multi_start_pathcover.json \
  data/raw/minoa/senior/Large_Input_S.json:outputs/minoa/headline/Large_Output_multi_start_pathcover.json
```

## Headline Results

Current headline results:

| Instance | Approach | Valid | Cost | Vehicles | EV | ICE | EV share | Trips | Deadhead min | Break min | Charge min |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Small | Multi-start path-cover | yes | 162.44 | 2 | 0 | 2 | 0.00% | 48 | 42.00 | 240.00 | 0.00 |
| Medium | Multi-start path-cover | yes | 371.35 | 5 | 5 | 0 | 100.00% | 139 | 752.00 | 1717.00 | 391.00 |
| Large | Multi-start path-cover | yes | 1165.24 | 15 | 5 | 10 | 33.33% | 260 | 2139.00 | 2448.00 | 518.00 |

Headline totals:

| Metric | Value |
|---|---:|
| Total cost | 1699.03 |
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
| Large | Multi-start path-cover | yes | 1165.24 | 15 | 5 | 10 | 33.33% | 260 | 6960 | 3.74% | 2139.00 | 2448.00 | 518.00 |

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
| Total cost | 10806.44 |
| Total vehicles | 136 |
| EV vehicles | 47 |
| ICE vehicles | 89 |

## GitHub Actions

Two workflows are provided.

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
