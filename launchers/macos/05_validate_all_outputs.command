#!/bin/zsh
set -u

cd "$(dirname "$0")/../.." || exit 1

echo "MINOA all-output validation audit"
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

if [ ! -f "outputs/minoa/all_multistart/pipeline_manifest.json" ]; then
  echo "All-instance pipeline manifest not found."
  echo "Please run 03_run_all.command first."
  echo
  read -r "?Press Enter to close..."
  exit 1
fi

if ! command -v java >/dev/null 2>&1; then
  echo "Java was not found."
  echo "Please install Java before running the validation audit."
  echo
  read -r "?Press Enter to close..."
  exit 1
fi

echo "Re-validating all generated all-instance outputs ..."
python scripts/validate_pipeline_outputs.py --manifest outputs/minoa/all_multistart/pipeline_manifest.json
STATUS=$?

echo
if [ "$STATUS" -eq 0 ]; then
  echo "All-output validation audit completed."
  echo "Next optional step: double-click 06_run_lower_bounds.command."
else
  echo "Validation audit failed with exit code $STATUS."
fi
echo
read -r "?Press Enter to close..."
exit "$STATUS"
