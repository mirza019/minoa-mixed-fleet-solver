@echo off
setlocal
cd /d "%~dp0\..\.."

echo MINOA Python test suite
echo =======================
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

echo Running pytest ...
python -m pytest -q
set "STATUS=%ERRORLEVEL%"

echo.
if "%STATUS%"=="0" (
  echo Tests completed successfully.
) else (
  echo Tests failed with exit code %STATUS%.
)
echo.
pause
exit /b %STATUS%
