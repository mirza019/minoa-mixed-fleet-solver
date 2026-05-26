# GitHub Actions Workflows

This folder contains reproducibility workflows for the MINOA solver.

## `minoa-headline-instances.yml`

Runs the three headline instances separately:

```text
small, medium, large
```

Each job:

1. Checks out the repository.
2. Installs Python dependencies.
3. Installs Java.
4. Runs the optimized multi-start path-cover solver.
5. Validates the output with the official desktop validator.
6. Writes a result table to the GitHub Actions summary.
7. Uploads output JSON, logs, and Markdown report artifacts.

## `minoa-all-instances.yml`

Runs the full senior benchmark.

Each run:

1. Creates processed working input copies when needed.
2. Solves every available senior input.
3. Uses optimized headline search for Small, Medium, and Large.
4. Uses the robust charging-aware path-cover pipeline for additional instances.
5. Validates every generated output with the official desktop validator.
6. Writes documentation, table interpretation, totals, file lists, and artifacts
   to the GitHub Actions summary.

## Manual Execution on GitHub

1. Open the repository on GitHub.
2. Go to **Actions**.
3. Select either workflow.
4. Click **Run workflow**.

The result table appears on the run summary page. Full JSON outputs and reports
are available as downloadable artifacts.
