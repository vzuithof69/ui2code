@echo off
REM Start-UI2Code.bat
REM UI2Code Super-Engine Launcher for Windows
REM Kan vanuit iedere locatie worden gestart

REM Set script directory regardless of current working directory
set "SCRIPT_DIR=%~dp0"

REM Change to script directory
cd /d "%SCRIPT_DIR%"

REM Execute PowerShell script with execution policy bypass
REM Use -NoProfile for faster startup, -ExecutionPolicy Bypass to allow script execution
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%Start-UI2Code.ps1" %*

REM Capture exit code
set EXIT_CODE=%ERRORLEVEL%

REM Exit with the same code as the PowerShell script
exit /b %EXIT_CODE%
