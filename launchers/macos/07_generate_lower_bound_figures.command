#!/bin/zsh
set -u

cd "$(dirname "$0")/../.." || exit 1

echo "MINOA lower-bound figure generation"
echo "==================================="
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

if [ ! -f "results/lower_bounds/all_instances_lower_bounds.csv" ]; then
  echo "Lower-bound CSV not found."
  echo "Please run 06_run_lower_bounds.command first."
  echo
  read -r "?Press Enter to close..."
  exit 1
fi

echo "Generating lower-bound figures ..."
python scripts/generate_lower_bound_figures.py \
  --csv results/lower_bounds/all_instances_lower_bounds.csv \
  --out-dir FAU_Thesis_temp/figures
STATUS=$?

echo
if [ "$STATUS" -eq 0 ]; then
  echo "Lower-bound figures generated."
else
  echo "Figure generation failed with exit code $STATUS."
fi
echo
read -r "?Press Enter to close..."
exit "$STATUS"
