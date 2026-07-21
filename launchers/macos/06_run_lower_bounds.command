#!/bin/zsh
set -u

cd "$(dirname "$0")/../.." || exit 1

echo "MINOA lower-bound diagnostics"
echo "============================="
echo

if [ ! -x ".venv/bin/python" ]; then
  echo "Virtual environment not found."
  echo "Please run 01_setup.command first."
  echo
  read -r "?Press Enter to close..."
  exit 1
fi

echo "Activating virtual environment ..."
if ! source .venv/bin/activate; then
  echo "Virtual environment activation failed."
  echo
  read -r "?Press Enter to close..."
  exit 1
fi

if [ ! -d "data/processed/minoa/all_multistart" ] || [ ! -f "outputs/minoa/final_archive/final_results.csv" ]; then
  echo "Required all-instance outputs or final archive CSV are missing."
  echo "Please run 03_run_all.command first."
  echo
  read -r "?Press Enter to close..."
  exit 1
fi

echo "Computing lower-bound diagnostics for all Senior instances ..."
echo "This can take several minutes depending on the machine."
python scripts/run_lower_bounds.py \
  --scope all \
  --input-dir data/processed/minoa/all_multistart \
  --archive-csv outputs/minoa/final_archive/final_results.csv \
  --time-limit 180 \
  --output-csv results/lower_bounds/all_instances_lower_bounds.csv
STATUS=$?

echo
if [ "$STATUS" -eq 0 ]; then
  echo "Lower-bound diagnostics completed."
  echo "Next optional step: double-click 07_generate_lower_bound_figures.command."
else
  echo "Lower-bound diagnostics failed with exit code $STATUS."
fi
echo
read -r "?Press Enter to close..."
exit "$STATUS"
