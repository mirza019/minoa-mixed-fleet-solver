#!/bin/zsh
set -u

cd "$(dirname "$0")/../.." || exit 1

echo "MINOA Python test suite"
echo "======================="
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

echo "Running pytest ..."
python -m pytest -q
STATUS=$?

echo
if [ "$STATUS" -eq 0 ]; then
  echo "Tests completed successfully."
else
  echo "Tests failed with exit code $STATUS."
fi
echo
read -r "?Press Enter to close..."
exit "$STATUS"
