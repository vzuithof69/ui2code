# Start-UI2Code.ps1
# UI2Code Super-Engine Startup Script for Windows
# Simplified version - uses Python 3.12 directly

param(
    [switch]$NoPause = $false
)

# ============================================================================
# CONFIGURATIE
# ============================================================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = $ScriptDir
$LogsDir = Join-Path $ProjectRoot "logs"
$RequirementsFile = Join-Path $ProjectRoot "requirements.txt"
$PythonModule = "ui.ui2code_super_engine"

# ============================================================================
# LOGGING SETUP
# ============================================================================
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogFilename = "startup-$Timestamp.log"
$LogPath = Join-Path $LogsDir $LogFilename
$ErrorLogPath = Join-Path $LogsDir "latest-error.log"

function Initialize-Logging {
    if (!(Test-Path $LogsDir)) {
        New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null
    }
    
    if (Test-Path $ErrorLogPath) {
        Clear-Content -Path $ErrorLogPath -ErrorAction SilentlyContinue
    }
}

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    Add-Content -Path $LogPath -Value $logEntry -Encoding UTF8
    
    switch ($Level) {
        "ERROR" { Write-Host $logEntry -ForegroundColor Red }
        "WARNING" { Write-Host $logEntry -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
        default { Write-Host $logEntry }
    }
}

function Write-Error-Log {
    param([string]$Message)
    Write-Log -Message $Message -Level "ERROR"
    $errorEntry = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - $Message"
    Add-Content -Path $ErrorLogPath -Value $errorEntry -Encoding UTF8
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================
try {
    Initialize-Logging
    Write-Log "=== UI2Code Startup Script Gestart ==="
    Write-Log "Script directory: $ScriptDir"
    Write-Log "Project root: $ProjectRoot"
    
    # Change to project directory
    Set-Location $ProjectRoot
    Write-Log "Working directory: $(Get-Location)"
    
    # Check if Python 3.12 is available via py launcher
    Write-Log "Checking for Python 3.12..."
    $pythonExe = $null
    
    try {
        $pyOutput = & py -3.12 --version 2>&1
        if ($pyOutput -match "Python 3\.12") {
            $pythonExe = "py -3.12"
            Write-Log "Found Python 3.12: $pyOutput" -Level "SUCCESS"
        }
    }
    catch {
        Write-Log "Python 3.12 not found via py launcher" -Level "WARNING"
    }
    
    if (!$pythonExe) {
        Write-Error-Log "Python 3.12 is not installed or not accessible via 'py -3.12'"
        Write-Host "`n=== FOUT: Python 3.12 niet gevonden ===" -ForegroundColor Red
        Write-Host "Installeer Python 3.12 van https://www.python.org/downloads/" -ForegroundColor Yellow
        Write-Host "Of gebruik: py -3.12 --version om te controleren" -ForegroundColor Yellow
        Write-Host "`nDruk op een toets om af te sluiten..."
        if (!$NoPause) { $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
        exit 1
    }
    
    # Check if requirements.txt exists
    if (!(Test-Path $RequirementsFile)) {
        Write-Error-Log "requirements.txt niet gevonden: $RequirementsFile"
        Write-Host "`n=== FOUT: requirements.txt niet gevonden ===" -ForegroundColor Red
        exit 1
    }
    
    # Install requirements if needed
    Write-Log "Checking dependencies..."
    try {
        $checkOutput = & $pythonExe -c "import PySide6; print('PySide6 OK')" 2>&1
        if ($checkOutput -match "OK") {
            Write-Log "Dependencies already installed" -Level "SUCCESS"
        }
        else {
            Write-Log "Installing dependencies from requirements.txt..."
            & $pythonExe -m pip install -r $RequirementsFile --quiet
            Write-Log "Dependencies installed" -Level "SUCCESS"
        }
    }
    catch {
        Write-Log "Installing dependencies..."
        & $pythonExe -m pip install -r $RequirementsFile --quiet
        Write-Log "Dependencies installed" -Level "SUCCESS"
    }
    
    # Start GUI
    Write-Log "`n=== Starting GUI ===" -Level "SUCCESS"
    Write-Log "Command: $pythonExe -m $PythonModule"
    Write-Log "Log file: $LogPath"
    
    & $pythonExe -m $PythonModule
    $exitCode = $LASTEXITCODE
    
    Write-Log "=== UI2Code Script Voltooid (exit code: $exitCode) ==="
    
    if ($exitCode -ne 0) {
        Write-Host "`nGUI exited with error (exit code: $exitCode)" -ForegroundColor Yellow
        Write-Host "See log file: $LogPath" -ForegroundColor Yellow
        Write-Host "Error log: $ErrorLogPath" -ForegroundColor Yellow
        Write-Host "`nPress any key to exit..."
        if (!$NoPause) { $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
    }
    
    exit $exitCode
}
catch {
    Write-Error-Log "Fatal error: $_"
    Write-Error-Log "Stacktrace: $($_.ScriptStackTrace)"
    
    Write-Host "`n=== CRITICAL ERROR ===" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "`nDetails:" -ForegroundColor Yellow
    Write-Host $_.ScriptStackTrace -ForegroundColor Yellow
    Write-Host "`nLog file: $LogPath" -ForegroundColor Cyan
    Write-Host "Error log: $ErrorLogPath" -ForegroundColor Cyan
    Write-Host "`nPress any key to exit..."
    if (!$NoPause) { $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
    
    exit 1
}
