# CI Scripts

This folder contains the shell scripts used by GitHub Actions. They keep the
workflow files short and readable.

| File | Used in workflow | What it does |
|---|---|---|
| `run_headline_instance.sh` | `MINOA Headline Instances` | Runs one headline instance: Small, Medium, or Large. It writes output files, validates them, and saves a report. |
| `run_all_instances.sh` | `MINOA All Instances` | Runs the full senior benchmark and fails the workflow if any instance is not validator-feasible. |

The workflows install Python dependencies and Java before these scripts run.
Java is needed because the official MINOA validator is a `.jar` file.
