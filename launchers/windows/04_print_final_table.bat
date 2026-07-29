@echo off
setlocal
cd /d "%~dp0\..\.."

echo MINOA retained final thesis table
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

echo Printing the retained no-regression archive table used in the thesis.
echo This command also creates the compact result JSON/CSV if it is absent.
echo.
"%VENV_PYTHON%" scripts\print_final_results_table.py --summary-file outputs\minoa\final_pipeline\final_results_summary.md
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
