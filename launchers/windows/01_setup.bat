@echo off
setlocal
cd /d "%~dp0\..\.."

echo MINOA setup
echo ===========
echo.

set "PY_CMD="
where py >nul 2>nul
if %errorlevel%==0 set "PY_CMD=py -3"
if not defined PY_CMD (
  where python >nul 2>nul
  if %errorlevel%==0 set "PY_CMD=python"
)

if not defined PY_CMD (
  echo Python 3 was not found.
  echo Please install Python 3.9 or newer, then run 01_setup.bat again.
  echo.
  pause
  exit /b 1
)

%PY_CMD% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)"
if errorlevel 1 (
  echo Python 3.9 or newer is required.
  echo Please install Python 3.9 or newer, then run 01_setup.bat again.
  echo.
  pause
  exit /b 1
)

echo Creating virtual environment in .venv ...
%PY_CMD% -m venv .venv
if not exist ".venv\Scripts\python.exe" (
  echo Virtual environment creation failed.
  echo.
  pause
  exit /b 1
)

set "VENV_PYTHON=.venv\Scripts\python.exe"

echo Installing Python requirements ...
"%VENV_PYTHON%" -m pip install --upgrade pip
if errorlevel 1 (
  echo pip upgrade failed.
  echo.
  pause
  exit /b 1
)

"%VENV_PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 (
  echo Requirement installation failed.
  echo.
  pause
  exit /b 1
)

echo.
echo Checking installed packages, Java, validator, and input data ...
"%VENV_PYTHON%" scripts\check_environment.py --require-java --require-validator --require-data
if errorlevel 1 (
  echo.
  echo Setup did not pass the final environment check.
  echo Fix the message above, then run 01_setup.bat again.
  echo.
  pause
  exit /b 1
)

echo.
echo Setup complete.
echo Next step: double-click 02_run_sml.bat for Small/Medium/Large.
echo Optional later step: double-click 03_run_all.bat for all Senior instances.
echo.
pause
