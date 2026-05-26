# MINOA Tools

This folder contains external MINOA tools.

## Desktop Validator

The official validator is here:

```text
tools/minoa/desktopValidator/desktopValidator/desktopValidator.jar
```

Example use:

```bash
java -jar tools/minoa/desktopValidator/desktopValidator/desktopValidator.jar \
  data/raw/minoa/senior/Small_Input_S.json \
  outputs/minoa/professor/Small_Output_multi_start_pathcover.json
```

The validator is only used to check final input/output pairs. It is not changed
and it is not used as part of the optimization logic.

`desktopValidator.7z` is kept as the original validator archive.
