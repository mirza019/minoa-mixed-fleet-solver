# MINOA Senior Instances

This folder contains the senior MINOA JSON input files used by the solver.

## Main Thesis Instances

These are the three headline instances:

| File | Name in reports |
|---|---|
| `Small_Input_S.json` | Small |
| `Medium_Input_S.json` | Medium |
| `Large_Input_S.json` | Large |

## Additional Instances

These instances are used as extra tests. They are useful for showing that the
pipeline also works beyond Small, Medium, and Large.

| File | Name in reports |
|---|---|
| `Toy_Example_Input_S.json` | Toy Example |
| `1line_input_S.json` | 1line |
| `1line_6timeWindow_input_S.json` | 1line 6timeWindow |
| `2lines_input_S.json` | 2lines |
| `2lines_6_timeWindows_input_S.json` | 2lines 6 timeWindows |
| `3lines_input_S.json` | 3lines |
| `3linesTriangle_input_S.json` | 3linesTriangle |
| `5lines_input_S.json` | 5lines |
| `_8lines_input_S.json` | 8lines |

`Toy_Example_Output_S.json` is an example output that came with the data. It is
not one of the generated thesis results.

## Important Note

Do not edit the raw input files directly. The automatic pipeline creates working
copies when needed, and those copies are not tracked in Git.
