@echo off
setlocal
cd /d "%~dp0\..\.."

echo MINOA retained final thesis table
echo =================================
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

echo Printing the retained no-regression archive table used in the thesis.
echo This command also creates the compact result JSON/CSV if it is absent.
echo.
python scripts\print_final_results_table.py --summary-file outputs\minoa\final_pipeline\final_results_summary.md
set "STATUS=%ERRORLEVEL%"

echo.
if "%STATUS%"=="0" (
  echo Final table check completed.
) else (
  echo Final table check failed with exit code %STATUS%.
)
echo.
pause
exit /b %STATUS%
