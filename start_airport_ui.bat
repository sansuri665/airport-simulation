@echo off
setlocal
cd /d "%~dp0"

set "OPEN_PATH=%~1"
if "%OPEN_PATH%"=="" set "OPEN_PATH=/"
set "BASE_URL=http://127.0.0.1:8776"
set "URL=%BASE_URL%%OPEN_PATH%"

echo Checking Airport local UI...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='SilentlyContinue'; try { $health=Invoke-RestMethod -Uri '%BASE_URL%/api/health' -TimeoutSec 2; if ($health.serviceId -eq 'airport-local-ui-v1') { exit 0 } } catch {}; $conn=Get-NetTCPConnection -LocalPort 8776 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1; if ($conn) { Write-Host ('Port 8776 is already used by PID ' + $conn.OwningProcess + '. Airport did not stop or replace that process.'); exit 2 }; exit 1"
set "CHECK_RESULT=%ERRORLEVEL%"

if "%CHECK_RESULT%"=="0" (
  echo Airport local UI is already running.
  start "" "%URL%"
  exit /b 0
)

if "%CHECK_RESULT%"=="2" (
  echo.
  echo Please close the program using port 8776, or change the Airport UI port.
  pause
  exit /b 2
)

echo Starting Airport local UI...
echo Open %URL% if the browser does not open automatically.
echo Press Ctrl+C in this window to stop the service.
echo.
py -3.13 -m airport_sim serve --host 127.0.0.1 --port 8776 --open --open-path "%OPEN_PATH%"
set "SERVER_RESULT=%ERRORLEVEL%"
echo.
if not "%SERVER_RESULT%"=="0" echo Airport local UI exited with code %SERVER_RESULT%.
pause
exit /b %SERVER_RESULT%
