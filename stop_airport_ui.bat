@echo off
setlocal
cd /d "%~dp0"

echo Stopping Airport local UI...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; try { $health=Invoke-RestMethod -Uri 'http://127.0.0.1:8776/api/health' -TimeoutSec 2 } catch { Write-Host 'Airport local UI is not running.'; exit 0 }; if ($health.serviceId -ne 'airport-local-ui-v1') { Write-Host 'The service on port 8776 is not the Airport local UI. It was left running.'; exit 2 }; $pidValue=[int]$health.servicePid; $process=Get-CimInstance Win32_Process -Filter ('ProcessId = ' + $pidValue); $isModuleEntry=$process -and $process.CommandLine -match '(?:^|\s)-m\s+airport_sim\s+serve(?:\s|$)'; $hasExpectedPort=$process -and $process.CommandLine -match '(--port\s+8776|--port=8776)'; if (-not $isModuleEntry -or -not $hasExpectedPort) { Write-Host ('PID ' + $pidValue + ' did not match the expected Airport command. It was left running.'); exit 3 }; Stop-Process -Id $pidValue; Write-Host ('Airport local UI stopped. PID=' + $pidValue)"
set "STOP_RESULT=%ERRORLEVEL%"
if not "%STOP_RESULT%"=="0" pause
exit /b %STOP_RESULT%
