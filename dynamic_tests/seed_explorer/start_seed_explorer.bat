@echo off
setlocal
call "%~dp0..\..\start_airport_ui.bat" /seed-explorer
exit /b %ERRORLEVEL%
