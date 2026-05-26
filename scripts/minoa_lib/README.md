# `minoa_lib`

This folder contains the main solver code. The implementation is split into
small files so the project is easier to read, test, and explain in the thesis.

## Main Solver Parts

| File | Role in the solver |
|---|---|
| `solver.py` | Connects all steps: reads input, selects trips, builds vehicle blocks, assigns fleet type, creates activities, and returns the output JSON. |
| `timetable.py` | Selects trips and creates timetable variants while respecting headway rules. |
| `network.py` | Builds the trip compatibility graph and supports the path-cover vehicle chaining. |
| `blocks.py` | Creates and updates vehicle blocks. |
| `activities.py` | Creates output activities such as trips, deadheads, breaks, charging, pull-out, and pull-in. |
| `capacity.py` | Checks parking and charging capacity logic. |
| `ev_assignment.py` | Decides which blocks can be served by EVs and which need ICE buses. |
| `ev_battery.py` | Simulates EV autonomy along a block. |
| `ev_charging.py` | Adds charging where there is enough feasible waiting time. |
| `validation.py` | Contains internal checks before the output is passed to the official validator. |
| `time_utils.py` | Small helper functions for time and duration handling. |
| `types.py` | Shared type definitions. |
| `cli.py` | Shared command-line helper code. |

## Experiment Helpers

| Folder | Role |
|---|---|
| `experiments/` | Builds metrics, Markdown tables, and plots. |
| `thesis/` | Contains helper code for thesis text and figures. |

## Method Idea in Simple Words

The solver first selects a valid set of trips. Then it builds a graph:

- each selected trip is a node,
- an arc `i -> j` means the same bus can serve trip `j` after trip `i`,
- a path in the graph becomes one vehicle block.

After the blocks are built, the solver assigns EV or ICE vehicles and inserts
charging if it is possible. The official desktop validator is then used outside
the algorithm to check the final input/output pair.
