# Start-UI2Code.ps1
# UI2Code Super-Engine Startup Script for Windows
# Automatische installatie en validatie van Python dependencies

param(
    [switch]$Verbose = $false,
    [switch]$NoPause = $false
)

# ============================================================================
# CONFIGURATIE
# ============================================================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = $ScriptDir
$VenvDir = Join-Path $ProjectRoot ".venv"
$LogsDir = Join-Path $ProjectRoot "logs"
$RequirementsFile = Join-Path $ProjectRoot "requirements.txt"
$PythonModule = "ui.ui2code_super_engine"

# Minimale Python versie vereisten
$MinPythonMajor = 3
$MinPythonMinor = 10
$Require64Bit = $true

# ============================================================================
# LOGGING SETUP
# ============================================================================
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogFilename = "startup-$Timestamp.log"
$LogPath = Join-Path $LogsDir $LogFilename
$ErrorLogPath = Join-Path $LogsDir "latest-error.log"

function Initialize-Logging {
    if (!(Test-Path $LogsDir)) {
        New-Item -ItemType Directory -Path $LogsDir | Out-Null
    }
    
    # Clear latest-error.log at start
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
    
    # Write to file
    Add-Content -Path $LogPath -Value $logEntry -Encoding UTF8
    
    # Write to console
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
    
    # Also write to latest-error.log
    $errorEntry = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - $Message"
    Add-Content -Path $ErrorLogPath -Value $errorEntry -Encoding UTF8
}

# ============================================================================
# PYTHON DETECTION
# ============================================================================
function Test-PythonVersion {
    param(
        [string]$PythonExe,
        [ref]$VersionInfo
    )
    
    try {
        $versionOutput = & $PythonExe --version 2>&1
        if ($versionOutput -match "Python (\d+)\.(\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            $patch = [int]$matches[3]
            
            # Check 64-bit
            $bitsOutput = & $PythonExe -c "import struct; print(struct.calcsize('P') * 8)" 2>&1
            $is64Bit = $bitsOutput -eq "64"
            
            $VersionInfo.Value = @{
                Major = $major
                Minor = $minor
                Patch = $patch
                Is64Bit = $is64Bit
                Executable = $PythonExe
                FullVersion = "$major.$minor.$patch"
            }
            
            # Validate requirements
            $versionOk = ($major -eq $MinPythonMajor -and $minor -ge $MinPythonMinor) -or ($major -gt $MinPythonMajor)
            $bitsOk = if ($Require64Bit) { $is64Bit } else { $true }
            
            return $versionOk -and $bitsOk
        }
    }
    catch {
        return $false
    }
    
    return $false
}

function Find-Python {
    Write-Log "Zoeken naar geschikte Python installatie..."
    
    $pythonCandidates = @()
    
    # Try py launcher first (recommended on Windows)
    try {
        $pyOutput = & py --list 2>&1
        Write-Log "py launcher output: $pyOutput" -Level "DEBUG"
        
        # Parse py --list output
        $pyOutput | ForEach-Object {
            if ($_ -match "-(\d+)\.(\d+)-64" -and $_ -notmatch "py -") {
                $major = [int]$matches[1]
                $minor = [int]$matches[2]
                if (($major -eq $MinPythonMajor -and $minor -ge $MinPythonMinor) -or ($major -gt $MinPythonMajor)) {
                    $pythonCandidates += "py -$major.$minor-64"
                }
            }
        }
    }
    catch {
        Write-Log "py launcher niet beschikbaar" -Level "WARNING"
    }
    
    # Try python command
    try {
        $pythonExe = Get-Command python -ErrorAction SilentlyContinue
        if ($pythonExe) {
            $versionInfo = $null
            if (Test-PythonVersion $pythonExe.Source ([ref]$versionInfo)) {
                $pythonCandidates += $pythonExe.Source
                Write-Log "Gevonden: $($versionInfo.Executable) (Python $($versionInfo.FullVersion) $($versionInfo.Is64Bit ? '64-bit' : '32-bit'))"
            }
        }
    }
    catch {
        Write-Log "python command niet gevonden" -Level "WARNING"
    }
    
    # Try python3 command
    try {
        $python3Exe = Get-Command python3 -ErrorAction SilentlyContinue
        if ($python3Exe -and $python3Exe.Source -notin $pythonCandidates) {
            $versionInfo = $null
            if (Test-PythonVersion $python3Exe.Source ([ref]$versionInfo)) {
                $pythonCandidates += $python3Exe.Source
                Write-Log "Gevonden: $($versionInfo.Executable) (Python $($versionInfo.FullVersion))"
            }
        }
    }
    catch {
        Write-Log "python3 command niet gevonden" -Level "WARNING"
    }
    
    # Return best candidate
    if ($pythonCandidates.Count -gt 0) {
        Write-Log "Gevonden $($pythonCandidates.Count) geschikte Python installatie(s)"
        return $pythonCandidates[0]
    }
    
    return $null
}

# ============================================================================
# PYTHON INSTALLATIE VIA WINGET
# ============================================================================
function Install-PythonViaWinget {
    Write-Log "Python niet gevonden. Proberen te installeren via winget..."
    
    # Check if winget is available
    try {
        $wingetVersion = & winget --version 2>&1
        Write-Log "winget gevonden: $wingetVersion"
    }
    catch {
        Write-Error-Log "winget is niet beschikbaar op dit systeem"
        Write-Host "`n=== FOUT: winget niet beschikbaar ===" -ForegroundColor Red
        Write-Host "winget is vereist voor automatische Python installatie." -ForegroundColor Red
        Write-Host "`nHandmatige installatie opties:" -ForegroundColor Yellow
        Write-Host "1. Download Python $MinPythonMajor.$MinPythonMinor van https://www.python.org/downloads/" -ForegroundColor Yellow
        Write-Host "2. Installeer winget: https://aka.ms/winget" -ForegroundColor Yellow
        Write-Host "`nDruk op een toets om af te sluiten..."
        if (!$NoPause) { $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
        exit 1
    }
    
    # Install Python 3.12 64-bit (latest stable)
    $pythonVersion = "3.12"
    Write-Log "Installeren Python $pythonVersion..."
    
    try {
        $installCmd = "winget install -e --id Python.Python.$pythonVersion --silent --accept-package-agreements --accept-source-agreements"
        Write-Log "Uitvoeren: $installCmd"
        
        $installOutput = Invoke-Expression $installCmd 2>&1
        Write-Log "Installatie output: $installOutput"
        
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        Write-Log "Python installatie voltooid" -Level "SUCCESS"
        return $true
    }
    catch {
        Write-Error-Log "Python installatie mislukt: $_"
        Write-Host "`n=== FOUT: Python installatie mislukt ===" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        Write-Host "`nInstalleer Python handmatig van https://www.python.org/downloads/" -ForegroundColor Yellow
        Write-Host "`nDruk op een toets om af te sluiten..."
        if (!$NoPause) { $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
        exit 1
    }
}

# ============================================================================
# VIRTUELE OMGEVING
# ============================================================================
function Setup-VirtualEnvironment {
    param([string]$PythonExe)
    
    Write-Log "Controleren virtuele omgeving: $VenvDir"
    
    $venvPython = Join-Path $VenvDir "Scripts\python.exe"
    $venvPip = Join-Path $VenvDir "Scripts\pip.exe"
    
    if (!(Test-Path $venvPython)) {
        Write-Log "Aanmaken virtuele omgeving..."
        try {
            & $PythonExe -m venv $VenvDir
            Write-Log "Virtuele omgeving aangemaakt" -Level "SUCCESS"
        }
        catch {
            Write-Error-Log "Virtuele omgeving aanmaken mislukt: $_"
            throw "Kan virtuele omgeving niet aanmaken: $_"
        }
    }
    else {
        Write-Log "Virtuele omgeving bestaat al"
    }
    
    return @{
        Python = $venvPython
        Pip = $venvPip
    }
}

# ============================================================================
# DEPENDENCIES INSTALLEREN
# ============================================================================
function Install-Dependencies {
    param(
        [string]$PipExe,
        [string]$RequirementsPath
    )
    
    Write-Log "Controleren dependencies..."
    
    if (!(Test-Path $RequirementsPath)) {
        Write-Error-Log "requirements.txt niet gevonden: $RequirementsPath"
        throw "requirements.txt niet gevonden"
    }
    
    # Get pip version
    try {
        $pipVersion = & $PipExe --version 2>&1
        Write-Log "pip versie: $pipVersion"
    }
    catch {
        Write-Error-Log "pip versie check mislukt: $_"
        throw "pip is niet beschikbaar"
    }
    
    # Install requirements
    Write-Log "Installeren dependencies uit requirements.txt..."
    try {
        $installOutput = & $PipExe install -r $RequirementsPath 2>&1
        Write-Log "pip install output: $installOutput"
        
        if ($installOutput -match "Successfully installed|Requirement already satisfied|already satisfied") {
            Write-Log "Dependencies geïnstalleerd/gecontroleerd" -Level "SUCCESS"
        }
    }
    catch {
        Write-Error-Log "Dependencies installeren mislukt: $_"
        throw "Kan dependencies niet installeren: $_"
    }
}

# ============================================================================
# IMPORT TESTS
# ============================================================================
function Test-Imports {
    param([string]$PythonExe)
    
    Write-Log "Testen imports..."
    
    $testScript = @"
import sys
try:
    import PySide6.QtWidgets
    print('✓ PySide6 geïmporteerd')
except ImportError as e:
    print(f'✗ PySide6 import mislukt: {e}')
    sys.exit(1)

try:
    sys.path.insert(0, '$ProjectRoot')
    from ui.ui2code_super_engine import UI2CodeSuperEngine
    print('✓ ui.ui2code_super_engine geïmporteerd')
except ImportError as e:
    print(f'✗ UI2Code import mislukt: {e}')
    sys.exit(1)

print('✓ Alle imports succesvol')
sys.exit(0)
"@
    
    try {
        $testOutput = & $PythonExe -c $testScript 2>&1
        Write-Log "Import test output: $testOutput"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Log "Import test mislukt met exit code $($LASTEXITCODE)"
            throw "Import test mislukt"
        }
        
        Write-Log "Alle imports succesvol" -Level "SUCCESS"
        return $true
    }
    catch {
        Write-Error-Log "Import test mislukt: $_"
        throw "Import test mislukt: $_"
    }
}

# ============================================================================
# GUI STARTEN
# ============================================================================
function Start-GUI {
    param([string]$PythonExe)
    
    Write-Log "Starten GUI..."
    Write-Log "Commando: $PythonExe -m $PythonModule"
    
    try {
        & $PythonExe -m $PythonModule
        $exitCode = $LASTEXITCODE
        
        Write-Log "GUI gesloten met exit code: $exitCode"
        
        if ($exitCode -ne 0) {
            Write-Error-Log "GUI crashte met exit code $exitCode"
        }
        
        return $exitCode
    }
    catch {
        Write-Error-Log "GUI starten mislukt: $_"
        Write-Host "`n=== FOUT: GUI starten mislukt ===" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        Write-Host "`nZie logbestand: $LogPath" -ForegroundColor Yellow
        Write-Host "`nDruk op een toets om af te sluiten..."
        if (!$NoPause) { $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
        exit 1
    }
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================
try {
    Initialize-Logging
    Write-Log "=== UI2Code Startup Script Gestart ==="
    Write-Log "Script directory: $ScriptDir"
    Write-Log "Project root: $ProjectRoot"
    
    # 1. Zoek Python
    $pythonExe = Find-Python
    
    if (!$pythonExe) {
        Write-Log "Geen geschikte Python gevonden (vereist: ${MinPythonMajor}.${MinPythonMinor}+ 64-bit)"
        Install-PythonViaWinget
        
        # Zoek opnieuw na installatie
        $pythonExe = Find-Python
        if (!$pythonExe) {
            Write-Error-Log "Python nog steeds niet gevonden na installatie"
            throw "Python installatie mislukt"
        }
    }
    
    # 2. Get Python details
    $versionInfo = $null
    if (!(Test-PythonVersion $pythonExe ([ref]$versionInfo))) {
        Write-Error-Log "Python versie check mislukt voor $pythonExe"
        throw "Ongeldige Python versie"
    }
    
    Write-Log "Python versie: $($versionInfo.FullVersion) ($($versionInfo.Is64Bit ? '64-bit' : '32-bit'))"
    Write-Log "Python executable: $($versionInfo.Executable)"
    
    # 3. Setup virtual environment
    $venv = Setup-VirtualEnvironment -PythonExe $pythonExe
    Write-Log "Venv Python: $($venv.Python)"
    Write-Log "Venv Pip: $($venv.Pip)"
    
    # 4. Install dependencies
    Install-Dependencies -PipExe $venv.Pip -RequirementsPath $RequirementsFile
    
    # 5. Test imports
    Test-Imports -PythonExe $venv.Python
    
    # 6. Start GUI
    Write-Log "`n=== GUI Wordt Gestart ===" -Level "SUCCESS"
    Write-Log "Start logbestand: $LogPath"
    
    $exitCode = Start-GUI -PythonExe $venv.Python
    
    Write-Log "=== UI2Code Script Voltooid (exit code: $exitCode) ==="
    
    if ($exitCode -ne 0) {
        Write-Host "`nGUI is gesloten met een fout (exit code: $exitCode)" -ForegroundColor Yellow
        Write-Host "Zie logbestand voor details: $LogPath" -ForegroundColor Yellow
        Write-Host "Laatste fouten: $ErrorLogPath" -ForegroundColor Yellow
        Write-Host "`nDruk op een toets om af te sluiten..."
        if (!$NoPause) { $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
    }
    
    exit $exitCode
}
catch {
    Write-Error-Log "Fatale fout: $_"
    Write-Error-Log "Stacktrace: $($_.ScriptStackTrace)"
    
    Write-Host "`n=== KRITIEKE FOUT ===" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "`nDetails:" -ForegroundColor Yellow
    Write-Host $_.ScriptStackTrace -ForegroundColor Yellow
    Write-Host "`nLogbestand: $LogPath" -ForegroundColor Cyan
    Write-Host "Foutlog: $ErrorLogPath" -ForegroundColor Cyan
    Write-Host "`nDruk op een toets om af te sluiten..."
    if (!$NoPause) { $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
    
    exit 1
}
