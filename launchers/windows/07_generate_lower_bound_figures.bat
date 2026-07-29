@echo off
setlocal
cd /d "%~dp0\..\.."

echo MINOA lower-bound figure generation
echo ===================================
echo.

set "VENV_PYTHON=.venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
  echo Virtual environment not found.
  echo Please run 01_setup.bat first.
  echo.
  pause
  exit /b 1
)

if not exist "results\lower_bounds\all_instances_lower_bounds.csv" (
  echo Lower-bound CSV not found.
  echo Please run 06_run_lower_bounds.bat first.
  echo.
  pause
  exit /b 1
)

echo Generating lower-bound figures ...
"%VENV_PYTHON%" scripts\generate_lower_bound_figures.py ^
  --csv results\lower_bounds\all_instances_lower_bounds.csv ^
  --out-dir FAU_Thesis_temp\figures
set "STATUS=%ERRORLEVEL%"

echo.
if "%STATUS%"=="0" (
  echo Lower-bound figures generated.
) else (
  echo Figure generation failed with exit code %STATUS%.
)
echo.
pause
exit /b %STATUS%
