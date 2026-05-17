@echo off
setlocal

cd /d "%~dp0"

set "PYTHON=.venv\Scripts\python.exe"
set "MYSQL_BIN=C:\Program Files\MySQL\MySQL Server 8.0\bin"
set "MYSQLD=%MYSQL_BIN%\mysqld.exe"
set "MYSQL_CONFIG=C:\ProgramData\MySQL\MySQL Server 8.0\my.ini"

if not exist "%PYTHON%" (
  echo Virtual environment not found at .venv\Scripts\python.exe
  echo Create it first or install dependencies before running the dashboard.
  pause
  exit /b 1
)

if not exist "%MYSQLD%" (
  echo MySQL server executable not found at:
  echo %MYSQLD%
  pause
  exit /b 1
)

tasklist /FI "IMAGENAME eq mysqld.exe" | find /I "mysqld.exe" >nul
if errorlevel 1 (
  echo Starting MySQL server...
  if exist "%MYSQL_CONFIG%" (
    start "" "%MYSQLD%" --defaults-file="%MYSQL_CONFIG%"
  ) else (
    start "" "%MYSQLD%"
  )
  timeout /t 5 /nobreak >nul
) else (
  echo MySQL server is already running.
)

%PYTHON% -c "import cryptography, flask, pymysql, requests, yfinance" >nul 2>&1
if errorlevel 1 (
  echo Installing missing dependencies from requirements.txt...
  %PYTHON% -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
  )
)

set "DASHBOARD_URL=http://127.0.0.1:5000"

echo Starting Financial Dashboard...
echo Chrome will open when the dashboard is ready.
start "" powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "$url='%DASHBOARD_URL%'; for ($i = 0; $i -lt 60; $i++) { try { $response = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 1; if ($response.StatusCode -ge 200) { try { Start-Process 'chrome.exe' -ArgumentList $url } catch { Start-Process $url }; exit 0 } } catch { }; Start-Sleep -Seconds 1 }; try { Start-Process 'chrome.exe' -ArgumentList $url } catch { Start-Process $url }"
%PYTHON% app.py

endlocal
