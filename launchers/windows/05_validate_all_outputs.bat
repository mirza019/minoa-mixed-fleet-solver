@echo off
setlocal
cd /d "%~dp0\..\.."

echo MINOA all-output validation audit
echo =================================
echo.

set "VENV_PYTHON=.venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
  echo Virtual environment not found.
  echo Please run 01_setup.bat first.
  echo.
  pause
  exit /b 1
)

if not exist "outputs\minoa\all_multistart\pipeline_manifest.json" (
  echo All-instance pipeline manifest not found.
  echo Please run 03_run_all.bat first.
  echo.
  pause
  exit /b 1
)

where java >nul 2>nul
if errorlevel 1 (
  echo Java was not found.
  echo Please install Java before running the validation audit.
  echo.
  pause
  exit /b 1
)

echo Re-validating all generated all-instance outputs ...
"%VENV_PYTHON%" scripts\validate_pipeline_outputs.py --manifest outputs\minoa\all_multistart\pipeline_manifest.json
set "STATUS=%ERRORLEVEL%"

echo.
if "%STATUS%"=="0" (
  echo All-output validation audit completed.
  echo Next optional step: double-click 06_run_lower_bounds.bat.
) else (
  echo Validation audit failed with exit code %STATUS%.
)
echo.
pause
exit /b %STATUS%
