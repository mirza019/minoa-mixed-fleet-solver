#!/bin/zsh
set -u

cd "$(dirname "$0")/../.." || exit 1

echo "MINOA Small/Medium/Large experiment"
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

if ! command -v java >/dev/null 2>&1; then
  echo "Java was not found."
  echo "Please install Java before running the validator-based experiment pipeline."
  echo
  read -r "?Press Enter to close..."
  exit 1
fi

if [ ! -f "tools/minoa/desktopValidator/desktopValidator/desktopValidator.jar" ]; then
  echo "MINOA desktop validator was not found at:"
  echo "tools/minoa/desktopValidator/desktopValidator/desktopValidator.jar"
  echo
  read -r "?Press Enter to close..."
  exit 1
fi

echo "Running final method on Small, Medium, and Large ..."
python scripts/run_experiment.py --algorithm multistart --scope sml
STATUS=$?

echo
if [ "$STATUS" -eq 0 ]; then
  echo "Small/Medium/Large experiment completed."
  echo "Next step: double-click 03_run_all.command for all Senior instances,"
  echo "or 04_print_final_table.command to print the retained thesis result table."
else
  echo "Experiment failed with exit code $STATUS."
fi
echo
read -r "?Press Enter to close..."
exit "$STATUS"
