#!/bin/zsh
set -u

cd "$(dirname "$0")/../.." || exit 1

echo "MINOA retained final thesis table"
echo "================================="
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

echo "Printing the retained no-regression archive table used in the thesis."
echo "This command also creates the compact result JSON/CSV if it is absent."
echo
python scripts/print_final_results_table.py --summary-file outputs/minoa/final_pipeline/final_results_summary.md
STATUS=$?

echo
if [ "$STATUS" -eq 0 ]; then
  echo "Final table check completed."
else
  echo "Final table check failed with exit code $STATUS."
fi
echo
read -r "?Press Enter to close..."
exit "$STATUS"
