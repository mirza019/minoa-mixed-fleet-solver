# MINOA Tools

This folder contains external tools supplied with the MINOA challenge.

## Desktop Validator

The official validator JAR is located at:

```text
tools/minoa/desktopValidator/desktopValidator/desktopValidator.jar
```

It is used as an external feasibility and cost check:

```bash
java -jar tools/minoa/desktopValidator/desktopValidator/desktopValidator.jar \
  data/raw/minoa/senior/Small_Input_S.json \
  outputs/minoa/professor/Small_Output_multi_start_pathcover.json
```

The validator files are intentionally left untouched. The solver creates output
JSON files, then the reporting scripts pass input/output pairs to this validator.

## Archive

`desktopValidator.7z` is the original validator archive kept for traceability.
