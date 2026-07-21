#!/bin/zsh
set -u

cd "$(dirname "$0")/../.." || exit 1

echo "MINOA setup"
echo "==========="
echo

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 was not found."
  echo "Please install Python 3.9 or newer, then run 01_setup.command again."
  echo
  read -r "?Press Enter to close..."
  exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if ! python3 - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 9) else 1)
PY
then
  echo "Python 3.9 or newer is required. Found Python $PYTHON_VERSION."
  echo "Please install Python 3.9 or newer, then run 01_setup.command again."
  echo
  read -r "?Press Enter to close..."
  exit 1
fi

echo "Creating virtual environment in .venv ..."
if ! python3 -m venv .venv; then
  echo "Virtual environment creation failed."
  echo
  read -r "?Press Enter to close..."
  exit 1
fi
if [ ! -x ".venv/bin/python" ]; then
  echo "Virtual environment creation failed."
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

echo "Installing Python requirements ..."
if ! python -m pip install --upgrade pip; then
  echo "pip upgrade failed."
  echo
  read -r "?Press Enter to close..."
  exit 1
fi
if ! python -m pip install -r requirements.txt; then
  echo "Requirement installation failed."
  echo
  read -r "?Press Enter to close..."
  exit 1
fi

echo
echo "Checking installed packages, Java, validator, and input data ..."
if ! python scripts/check_environment.py --require-java --require-validator --require-data; then
  echo
  echo "Setup did not pass the final environment check."
  echo "Fix the message above, then run 01_setup.command again."
  echo
  read -r "?Press Enter to close..."
  exit 1
fi

echo
echo "Setup complete."
echo "Next step: double-click 02_run_sml.command for Small/Medium/Large."
echo "Optional later step: double-click 03_run_all.command for all Senior instances."
echo
read -r "?Press Enter to close..."
