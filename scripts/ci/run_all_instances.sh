#!/usr/bin/env bash
set -euo pipefail

mkdir -p outputs/minoa/ci-all data/processed/minoa/ci-all

echo "Running MINOA pipeline on all available senior instances"
.venv/bin/python scripts/run_all_experiments.py \
  --input-dir data/raw/minoa/senior \
  --processed-dir data/processed/minoa/ci-all \
  --output-dir outputs/minoa/ci-all \
  | tee outputs/minoa/ci-all/all_instances_report.md

if grep -E '\|[[:space:]]+[^|]+[[:space:]]+\|[[:space:]]+[^|]+[[:space:]]+\|[[:space:]]+no[[:space:]]+\|' outputs/minoa/ci-all/all_instances_report.md; then
  echo "At least one instance failed validation." >&2
  exit 1
fi

echo "All listed instances validated successfully."
