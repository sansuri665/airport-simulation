@echo off
setlocal
cd /d "%~dp0"
set "URL=http://127.0.0.1:8776/"
echo Starting Airport Seed Explorer...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $healthOk=$false; try { $r = Invoke-WebRequest -UseBasicParsing -Uri '%URL%api/health' -TimeoutSec 1; if ($r.StatusCode -eq 200) { $healthOk=$true } } catch { exit 1 }; if (-not $healthOk) { exit 1 }; try { $r = Invoke-WebRequest -UseBasicParsing -Uri '%URL%api/sim-save-slots' -TimeoutSec 1; if ($r.StatusCode -eq 200) { exit 0 } } catch {}; $conn = Get-NetTCPConnection -LocalPort 8776 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1; if ($conn) { Stop-Process -Id $conn.OwningProcess -Force; Start-Sleep -Milliseconds 500 }; exit 1"
if "%ERRORLEVEL%"=="0" (
  echo Seed Explorer is already running.
  start "" "%URL%"
  pause
  exit /b 0
)
echo Open %URL% if the browser does not open automatically.
echo Press Ctrl+C in this window to stop the server.
echo.
py -3 seed_explorer_server.py --host 127.0.0.1 --port 8776 --open
pause
