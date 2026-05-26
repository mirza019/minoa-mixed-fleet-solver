# GitHub Actions Workflows

This folder contains the GitHub Actions workflows for checking the solver online.
They are useful when someone wants to run the experiments without setting up
everything manually.

## `minoa-headline-instances.yml`

This workflow runs the main thesis instances:

```text
Small, Medium, Large
```

For each instance it:

1. installs Python and Java,
2. runs the solver,
3. validates the generated output with the official desktop validator,
4. shows a result table on the GitHub Actions summary page,
5. uploads the output JSON files and logs as artifacts.

## `minoa-all-instances.yml`

This workflow runs all senior instances in one pipeline.

It also writes a clear summary page with:

- what was run,
- how to read the table,
- the result table checked by the validator,
- total cost and vehicle counts,
- generated output files,
- downloadable artifacts.

## How to Run on GitHub

1. Open the repository.
2. Click **Actions**.
3. Select the workflow.
4. Click **Run workflow**.

After the run finishes, open the run summary page. The tables and artifacts are
shown there.
