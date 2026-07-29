@echo off
setlocal
cd /d "%~dp0\..\.."

echo MINOA lower-bound diagnostics
echo =============================
echo.

set "VENV_PYTHON=.venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
  echo Virtual environment not found.
  echo Please run 01_setup.bat first.
  echo.
  pause
  exit /b 1
)

if not exist "data\processed\minoa\all_multistart" (
  echo Processed all-instance input folder not found.
  echo Please run 03_run_all.bat first.
  echo.
  pause
  exit /b 1
)

if not exist "outputs\minoa\final_archive\final_results.csv" (
  echo Final archive CSV not found.
  echo Please run 03_run_all.bat first.
  echo.
  pause
  exit /b 1
)

echo Computing lower-bound diagnostics for all Senior instances ...
echo This can take several minutes depending on the machine.
"%VENV_PYTHON%" scripts\run_lower_bounds.py ^
  --scope all ^
  --input-dir data\processed\minoa\all_multistart ^
  --archive-csv outputs\minoa\final_archive\final_results.csv ^
  --time-limit 180 ^
  --output-csv results\lower_bounds\all_instances_lower_bounds.csv
set "STATUS=%ERRORLEVEL%"

echo.
if "%STATUS%"=="0" (
  echo Lower-bound diagnostics completed.
  echo Next optional step: double-click 07_generate_lower_bound_figures.bat.
) else (
  echo Lower-bound diagnostics failed with exit code %STATUS%.
)
echo.
pause
exit /b %STATUS%
