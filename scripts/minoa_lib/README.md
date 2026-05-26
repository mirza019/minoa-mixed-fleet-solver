# `minoa_lib`

This package contains the implementation modules used by the command-line
scripts in `scripts/`. The code is split by responsibility so the solver is not
one large file.

## Core Solver Modules

| File | Responsibility |
|---|---|
| `solver.py` | Main orchestration: load an instance, select trips, build blocks, assign fleet, insert activities, and return output JSON. |
| `timetable.py` | Timetable-feasible trip selection and timetable variant handling. |
| `network.py` | Compatibility graph construction and path-cover style chaining logic. |
| `blocks.py` | Vehicle block construction and block-level transformations. |
| `activities.py` | Output activity creation such as trips, deadheads, pull-in, pull-out, breaks, and charging. |
| `capacity.py` | Parking and charging capacity checks/helpers. |
| `ev_assignment.py` | Mixed-fleet assignment logic for deciding whether a block can be EV or ICE. |
| `ev_battery.py` | EV autonomy simulation and residual battery calculations. |
| `ev_charging.py` | Charging insertion inside feasible break windows. |
| `validation.py` | Internal structural validation helpers before external desktop-validator checks. |
| `time_utils.py` | Time conversions and duration helpers. |
| `types.py` | Shared type aliases and small data structures. |
| `cli.py` | Common command-line helper functions. |

## Experiment and Thesis Support

| Folder | Responsibility |
|---|---|
| `experiments/` | Metrics, Markdown table generation, and plots for reports. |
| `thesis/` | Thesis-specific content and figure-generation helpers. |

## Method Structure

The main optimization idea is graph-based:

1. Select a timetable-feasible subset of trips.
2. Build a compatibility graph where trips are nodes.
3. Add an arc `i -> j` if one vehicle can serve trip `j` after trip `i`.
4. Find good path covers; each path becomes one vehicle block.
5. Assign ICE/EV vehicle types and insert charging where feasible.
6. Export a MINOA-format output file.

The official desktop validator is not called from these modules as an
optimization oracle. It is used by the reporting/pipeline scripts as an external
check for final generated output files.
