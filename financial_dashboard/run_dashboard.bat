@echo off
setlocal

cd /d "%~dp0"

set "PYTHON=.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
  echo Virtual environment not found at .venv\Scripts\python.exe
  echo Create it first or install dependencies before running the dashboard.
  pause
  exit /b 1
)

%PYTHON% -c "import flask, pymysql" >nul 2>&1
if errorlevel 1 (
  echo Installing missing dependencies from requirements.txt...
  %PYTHON% -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
  )
)

echo Starting Financial Dashboard...
%PYTHON% app.py

endlocal
