@echo off
setlocal
cd /d "%~dp0\..\.."

echo MINOA Small/Medium/Large experiment
echo ===================================
echo.

if not exist python (
  echo Virtual environment not found.
  echo Please run 01_setup.bat first.
  echo.
  pause
  exit /b 1
)

echo Activating virtual environment ...
call ".venv\Scripts\activate.bat"
if errorlevel 1 (
  echo Virtual environment activation failed.
  echo.
  pause
  exit /b 1
)

where java >nul 2>nul
if errorlevel 1 (
  echo Java was not found.
  echo Please install Java before running the validator-based experiment pipeline.
  echo.
  pause
  exit /b 1
)

if not exist "tools\minoa\desktopValidator\desktopValidator\desktopValidator.jar" (
  echo MINOA desktop validator was not found at:
  echo tools\minoa\desktopValidator\desktopValidator\desktopValidator.jar
  echo.
  pause
  exit /b 1
)

echo Running final method on Small, Medium, and Large ...
python scripts\run_experiment.py --algorithm multistart --scope sml
set "STATUS=%ERRORLEVEL%"

echo.
if "%STATUS%"=="0" (
  echo Small/Medium/Large experiment completed.
  echo Next step: double-click 03_run_all.bat for all Senior instances,
  echo or 04_print_final_table.bat to print the retained thesis result table.
) else (
  echo Experiment failed with exit code %STATUS%.
)
echo.
pause
exit /b %STATUS%
