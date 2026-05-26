# CI Scripts

This folder contains small shell wrappers used by GitHub Actions. They are kept
separate from the Python solver so the workflow files stay readable.

| File | Used by | Purpose |
|---|---|---|
| `run_headline_instance.sh` | `MINOA Headline Instances` workflow | Runs one of `small`, `medium`, or `large`, validates it, and writes a Markdown report artifact. |
| `run_all_instances.sh` | `MINOA All Instances` workflow | Runs the full senior benchmark pipeline, validates every output, writes the all-instance report, and fails if any row is invalid. |

These scripts assume dependencies have already been installed by the workflow:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

They also require Java because the official MINOA desktop validator is a JAR
file.
