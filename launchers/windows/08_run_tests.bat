@echo off
setlocal
cd /d "%~dp0\..\.."

echo MINOA Python test suite
echo =======================
echo.

set "VENV_PYTHON=.venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
  echo Virtual environment not found.
  echo Please run 01_setup.bat first.
  echo.
  pause
  exit /b 1
)

echo Running pytest ...
"%VENV_PYTHON%" -m pytest -q
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
