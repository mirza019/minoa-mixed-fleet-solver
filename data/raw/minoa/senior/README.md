# MINOA Senior Instances

This folder contains the senior MINOA JSON instances used in the experiments.

## Headline Instances

These are the main instances discussed in the thesis results:

| File | Thesis name |
|---|---|
| `Small_Input_S.json` | Small |
| `Medium_Input_S.json` | Medium |
| `Large_Input_S.json` | Large |

## Additional Senior Instances

These are used as an additional robustness benchmark and are reported
separately from the headline instances:

| File | Thesis name |
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

`Toy_Example_Output_S.json` is a provided example output, not a solver-generated
result.

## Data Integrity Rule

Raw files in this folder should remain unchanged. The automatic all-instance
pipeline creates processed working copies only when needed for validation-safe
execution.
