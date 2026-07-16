# Start-UI2Code.ps1
# UI2Code Super-Engine Startup Script for Windows
# Fase 3B - Auto-installs dependencies and verifies imports

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
# PYTHON LAUNCHER SETUP
# ============================================================================
# Use py.exe launcher with proper argument separation
# ALWAYS use py -3.12, never plain "pip"
try {
    $PyLauncher = (Get-Command py.exe -ErrorAction Stop).Source
    Write-Host "Found py.exe launcher: $PyLauncher" -ForegroundColor Green
}
catch {
    Write-Host "ERROR: py.exe not found. Please install Python from https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "Ensure 'Python Launcher' is selected during installation." -ForegroundColor Yellow
    exit 1
}

function Test-PythonAvailable {
    param([string]$Version = "-3.12")
    
    $exitCode = 0
    & $PyLauncher $Version --version 2>&1 | Out-Null
    $exitCode = $LASTEXITCODE
    
    return $exitCode -eq 0
}

function Test-PipAvailable {
    param([string]$Version = "-3.12")
    
    $exitCode = 0
    & $PyLauncher $Version -m pip --version 2>&1 | Out-Null
    $exitCode = $LASTEXITCODE
    
    return $exitCode -eq 0
}

function Install-Requirements {
    param([string]$Version = "-3.12", [string]$RequirementsFile)
    
    Write-Log "Installing dependencies from requirements.txt..."
    Write-Log "Command: $PyLauncher $Version -m pip install -r $RequirementsFile"
    
    # Install with verbose output logged
    $installOutput = & $PyLauncher $Version -m pip install -r $RequirementsFile 2>&1
    $exitCode = $LASTEXITCODE
    
    # Log full pip output
    $installOutput | ForEach-Object { Write-Log "pip: $_" }
    
    if ($exitCode -ne 0) {
        Write-Error-Log "pip install failed with exit code $exitCode"
        return $false
    }
    return $true
}

function Start-UI2CodeModule {
    param([string]$Version = "-3.12", [string]$ModuleName)
    
    Write-Log "Starting GUI module: $ModuleName"
    & $PyLauncher $Version -m $ModuleName
    $exitCode = $LASTEXITCODE
    
    return $exitCode
}

function Test-RequiredImports {
    param([string]$Version = "-3.12")
    
    Write-Log "Testing required imports..."
    
    $imports = @(
        @{Name = "cv2"; Package = "opencv-python"},
        @{Name = "numpy"; Package = "numpy"},
        @{Name = "PySide6"; Package = "PySide6"}
    )
    
    $allOk = $true
    
    foreach ($import in $imports) {
        $testCode = "try: import $($import.Name); print('OK'); except ImportError as e: print(f'FAIL: {e}')"
        $result = & $PyLauncher $Version -c $testCode 2>&1
        
        if ($result -match "OK") {
            Write-Log "✓ $($import.Name) (from $($import.Package)) imported successfully" -Level "SUCCESS"
        }
        else {
            Write-Log "✗ $($import.Name) (from $($import.Package)) import failed: $result" -Level "ERROR"
            $allOk = $false
        }
    }
    
    return $allOk
}

function Get-PackageVersions {
    param([string]$Version = "-3.12")
    
    Write-Log "Checking package versions..."
    
    # Python version
    $pyVersion = & $PyLauncher $Version --version 2>&1
    Write-Log "Python: $pyVersion"
    
    # pip version
    $pipVersion = & $PyLauncher $Version -m pip --version 2>&1
    Write-Log "pip: $pipVersion"
    
    # cv2 version
    $cv2Version = & $PyLauncher $Version -c "import cv2; print(cv2.__version__)" 2>&1
    Write-Log "cv2 (OpenCV): $cv2Version"
    
    # numpy version
    $numpyVersion = & $PyLauncher $Version -c "import numpy; print(numpy.__version__)" 2>&1
    Write-Log "numpy: $numpyVersion"
    
    # PySide6 version
    $pysideVersion = & $PyLauncher $Version -c "import PySide6; print(PySide6.__version__)" 2>&1
    Write-Log "PySide6: $pysideVersion"
}

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
    
    # Don't clear error log - append instead
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
    $errorEntry = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - $Message`n"
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
    $pythonVersion = "-3.12"
    
    if (!(Test-PythonAvailable -Version $pythonVersion)) {
        Write-Error-Log "Python 3.12 is not installed or not accessible via py.exe"
        Write-Host "`n=== FOUT: Python 3.12 niet gevonden ===" -ForegroundColor Red
        Write-Host "Installeer Python 3.12 van https://www.python.org/downloads/" -ForegroundColor Yellow
        Write-Host "Of gebruik: py -3.12 --version om te controleren" -ForegroundColor Yellow
        Write-Host "`nDruk op een toets om af te sluiten..."
        if (!$NoPause) { $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
        exit 1
    }
    
    $pyVersionOutput = & $PyLauncher $pythonVersion --version 2>&1
    Write-Log "Found Python 3.12: $pyVersionOutput" -Level "SUCCESS"
    
    # Check if requirements.txt exists
    if (!(Test-Path $RequirementsFile)) {
        Write-Error-Log "requirements.txt niet gevonden: $RequirementsFile"
        Write-Host "`n=== FOUT: requirements.txt niet gevonden ===" -ForegroundColor Red
        exit 1
    }
    
    # Check if pip is available
    Write-Log "Checking for pip availability..."
    if (!(Test-PipAvailable -Version $pythonVersion)) {
        Write-Error-Log "pip is not available for Python 3.12"
        Write-Host "`n=== FOUT: pip niet beschikbaar ===" -ForegroundColor Red
        Write-Host "Probeer: py -3.12 -m ensurepip" -ForegroundColor Yellow
        Write-Host "`nDruk op een toets om af te sluiten..."
        if (!$NoPause) { $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
        exit 1
    }
    
    $pipVersionOutput = & $PyLauncher $pythonVersion -m pip --version 2>&1
    Write-Log "Found pip: $pipVersionOutput" -Level "SUCCESS"
    
    # Test required imports
    Write-Log "Testing required imports (cv2, numpy, PySide6)..."
    $importsOk = Test-RequiredImports -Version $pythonVersion
    
    if ($importsOk) {
        Write-Log "All required imports available" -Level "SUCCESS"
        Get-PackageVersions -Version $pythonVersion
    }
    else {
        Write-Log "Some imports missing, installing dependencies..." -Level "WARNING"
        $installResult = Install-Requirements -Version $pythonVersion -RequirementsFile $RequirementsFile
        if (!$installResult) {
            Write-Host "`n=== FOUT: Installatie van dependencies mislukt ===" -ForegroundColor Red
            Write-Host "Zie log file: $LogPath" -ForegroundColor Yellow
            Write-Host "`nDruk op een toets om af te sluiten..."
            if (!$NoPause) { $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
            exit 1
        }
        
        # Re-test imports after installation
        Write-Log "Re-testing imports after installation..."
        $importsOk = Test-RequiredImports -Version $pythonVersion
        
        if ($importsOk) {
            Write-Log "All imports now available" -Level "SUCCESS"
            Get-PackageVersions -Version $pythonVersion
        }
        else {
            Write-Error-Log "Import test failed after installation"
            Write-Host "`n=== FOUT: Imports werken niet na installatie ===" -ForegroundColor Red
            Write-Host "Zie log file: $LogPath" -ForegroundColor Yellow
            Write-Host "`nDruk op een toets om af te sluiten..."
            if (!$NoPause) { $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
            exit 1
        }
    }
    
    # Start GUI
    Write-Log "`n=== Starting GUI ===" -Level "SUCCESS"
    Write-Log "Command: $PyLauncher $pythonVersion -m $PythonModule"
    Write-Log "Log file: $LogPath"
    
    $exitCode = Start-UI2CodeModule -Version $pythonVersion -ModuleName $PythonModule
    
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
