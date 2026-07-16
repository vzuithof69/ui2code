# Start-UI2Code.ps1
# UI2Code Super-Engine Startup Script for Windows
# Geavanceerde Python detectie, 3.14 compatibiliteitstest en veilige installatie

param(
    [switch]$Verbose = $false,
    [switch]$NoPause = $false,
    [switch]$SkipPython314Test = $false
)

# ============================================================================
# CONFIGURATIE
# ============================================================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = $ScriptDir
$VenvDir = Join-Path $ProjectRoot ".venv"
$VenvBackupDir = Join-Path $ProjectRoot ".venv.backup"
$LogsDir = Join-Path $ProjectRoot "logs"
$RequirementsFile = Join-Path $ProjectRoot "requirements.txt"
$PythonModule = "ui.ui2code_super_engine"
$ConfigBackupDir = Join-Path $ProjectRoot "config.backup"

# Python versie vereisten
$PreferredPythonMajor = 3
$PreferredPythonMinor = 12
$MaxPythonMajor = 3
$MaxPythonMinor = 14
$Require64Bit = $true

# ============================================================================
# LOGGING SETUP
# ============================================================================
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogFilename = "startup-$Timestamp.log"
$LogPath = Join-Path $LogsDir $LogFilename
$ErrorLogPath = Join-Path $LogsDir "latest-error.log"
$DetectLogPath = Join-Path $LogsDir "python-detection-$Timestamp.log"

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
        "DETECT" { Write-Host $logEntry -ForegroundColor Cyan }
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
# PYTHON DETECTIE - MEERVOUDIGE METHODEN
# ============================================================================
function Get-PythonFromPyLauncher {
    Write-Log "Methode 1: py launcher (py -0p)" -Level "DETECT"
    $pythons = @()
    
    try {
        $pyOutput = & py -0p 2>&1
        Write-Log "py -0p output:" -Level "DETECT"
        Add-Content -Path $DetectLogPath -Value $pyOutput -Encoding UTF8
        
        $pyOutput | ForEach-Object {
            $line = $_.Trim()
            if ($line -match "-V:(\d+)\.(\d+)-(\d+)" -and $line -notmatch "py -") {
                $major = [int]$matches[1]
                $minor = [int]$matches[2]
                $bits = [int]$matches[3]
                $exePath = ($line -split '\s+')[-1]
                
                if ($bits -eq 64) {
                    $pythons += @{
                        Version = "$major.$minor"
                        Major = $major
                        Minor = $minor
                        Bits = 64
                        Executable = $exePath
                        Method = "py launcher"
                        Priority = if ($major -eq 3 -and $minor -eq 14) { 1 } 
                                   elseif ($major -eq 3 -and $minor -eq 12) { 2 }
                                   else { 3 }
                    }
                    Write-Log "  Gevonden: Python $major.$minor ($bits-bit) - $exePath" -Level "DETECT"
                }
            }
        }
    }
    catch {
        Write-Log "  py launcher niet beschikbaar: $_" -Level "WARNING"
    }
    
    return $pythons
}

function Get-PythonFromPath {
    Write-Log "Methode 2: PATH environment variable (where python)" -Level "DETECT"
    $pythons = @()
    
    try {
        $whereOutput = & where.exe python 2>&1
        $whereOutput += & where.exe python3 2>&1
        
        $whereOutput | Where-Object { $_ -notmatch "Could not find" } | ForEach-Object {
            $exePath = $_.Trim()
            if (Test-Path $exePath) {
                try {
                    $versionOutput = & $exePath --version 2>&1
                    if ($versionOutput -match "Python (\d+)\.(\d+)") {
                        $major = [int]$matches[1]
                        $minor = [int]$matches[2]
                        
                        $bitsOutput = & $exePath -c "import struct; print(struct.calcsize('P') * 8)" 2>&1
                        $is64Bit = $bitsOutput -eq "64"
                        
                        if ($is64Bit) {
                            $pythons += @{
                                Version = "$major.$minor"
                                Major = $major
                                Minor = $minor
                                Bits = 64
                                Executable = $exePath
                                Method = "PATH"
                                Priority = 3
                            }
                            Write-Log "  Gevonden: Python $major.$minor (64-bit) - $exePath" -Level "DETECT"
                        }
                    }
                }
                catch {
                    Write-Log "  Kan versie niet bepalen voor $exePath" -Level "WARNING"
                }
            }
        }
    }
    catch {
        Write-Log "  where command mislukt: $_" -Level "WARNING"
    }
    
    return $pythons
}

function Get-PythonFromRegistry {
    Write-Log "Methode 3: Windows Registry" -Level "DETECT"
    $pythons = @()
    
    $regPaths = @(
        "HKLM:\SOFTWARE\Python\PythonCore",
        "HKCU:\SOFTWARE\Python\PythonCore",
        "HKLM:\SOFTWARE\Wow6432Node\Python\PythonCore",
        "HKCU:\SOFTWARE\Wow6432Node\Python\PythonCore"
    )
    
    foreach ($regPath in $regPaths) {
        try {
            if (Test-Path $regPath) {
                $versions = Get-ChildItem $regPath -ErrorAction SilentlyContinue
                foreach ($version in $versions) {
                    $versionName = $version.PSChildName
                    $installPath = Get-ItemProperty "$regPath\$versionName\InstallPath" -ErrorAction SilentlyContinue
                    if ($installPath) {
                        $exePath = Join-Path $installPath.PSPath "python.exe"
                        if (Test-Path $exePath) {
                            $bitsOutput = & $exePath -c "import struct; print(struct.calcsize('P') * 8)" 2>&1
                            $is64Bit = $bitsOutput -eq "64"
                            
                            if ($is64Bit -and $versionName -match "^(\d+)\.(\d+)") {
                                $major = [int]$matches[1]
                                $minor = [int]$matches[2]
                                $pythons += @{
                                    Version = "$major.$minor"
                                    Major = $major
                                    Minor = $minor
                                    Bits = 64
                                    Executable = $exePath
                                    Method = "Registry ($regPath)"
                                    Priority = 3
                                }
                                Write-Log "  Gevonden: Python $major.$minor (64-bit) - $exePath" -Level "DETECT"
                            }
                        }
                    }
                }
            }
        }
        catch {
            Write-Log "  Registry pad $regPath niet leesbaar: $_" -Level "WARNING"
        }
    }
    
    return $pythons
}

function Get-PythonFromKnownPaths {
    Write-Log "Methode 4: Bekende installatiemappen" -Level "DETECT"
    $pythons = @()
    
    $knownPaths = @(
        "$env:LOCALAPPDATA\Programs\Python",
        "$env:ProgramFiles\Python",
        "$env:ProgramFiles (x86)\Python",
        "C:\Python*",
        "$env:USERPROFILE\AppData\Local\Programs\Python"
    )
    
    foreach ($basePath in $knownPaths) {
        try {
            $directories = Get-ChildItem -Path $basePath -Directory -ErrorAction SilentlyContinue
            foreach ($dir in $directories) {
                $exePath = Join-Path $dir.FullName "python.exe"
                if (Test-Path $exePath) {
                    try {
                        $versionOutput = & $exePath --version 2>&1
                        if ($versionOutput -match "Python (\d+)\.(\d+)") {
                            $major = [int]$matches[1]
                            $minor = [int]$matches[2]
                            
                            $bitsOutput = & $exePath -c "import struct; print(struct.calcsize('P') * 8)" 2>&1
                            $is64Bit = $bitsOutput -eq "64"
                            
                            if ($is64Bit) {
                                $pythons += @{
                                    Version = "$major.$minor"
                                    Major = $major
                                    Minor = $minor
                                    Bits = 64
                                    Executable = $exePath
                                    Method = "Known Path ($($dir.FullName))"
                                    Priority = 3
                                }
                                Write-Log "  Gevonden: Python $major.$minor (64-bit) - $exePath" -Level "DETECT"
                            }
                        }
                    }
                    catch {
                        Write-Log "  Kan versie niet bepalen voor $exePath" -Level "WARNING"
                    }
                }
            }
        }
        catch {
            Write-Log "  Pad $basePath niet toegankelijk: $_" -Level "WARNING"
        }
    }
    
    return $pythons
}

function Find-AllPythonVersions {
    Write-Log "=== Python Detectie Gestart ===" -Level "DETECT"
    Initialize-DetectionLog
    
    $allPythons = @()
    
    $allPythons += Get-PythonFromPyLauncher
    $allPythons += Get-PythonFromPath
    $allPythons += Get-PythonFromRegistry
    $allPythons += Get-PythonFromKnownPaths
    
    # Remove duplicates based on executable path
    $uniquePythons = $allPythons | Sort-Object -Property Executable -Unique
    
    # Sort by priority (lower is better)
    $sortedPythons = $uniquePythons | Sort-Object -Property Priority, Version
    
    Write-Log "`nTotaal gevonden: $($sortedPythons.Count) unieke 64-bit Python installatie(s)" -Level "DETECT"
    
    return $sortedPythons
}

function Initialize-DetectionLog {
    $detectHeader = @"
===========================================
Python Detectie Log - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
===========================================

"@
    Add-Content -Path $DetectLogPath -Value $detectHeader -Encoding UTF8
}

# ============================================================================
# PYTHON 3.14 COMPATIBILITEITSTEST
# ============================================================================
function Test-Python314Compatibility {
    param([hashtable]$Python314Info)
    
    Write-Log "`n=== Python 3.14 Compatibiliteitstest ===" -Level "DETECT"
    Write-Log "Testen Python $($Python314Info.Version) met UI2Code dependencies..."
    
    $testVenvDir = Join-Path $ProjectRoot ".venv.py314test"
    $testPassed = $false
    $testResults = @{
        VenvCreated = $false
        DependenciesInstalled = $false
        ImportsSuccessful = $false
        Errors = @()
    }
    
    try {
        # 1. Maak tijdelijke venv
        Write-Log "  [1/3] Aanmaken tijdelijke virtuele omgeving..."
        & $Python314Info.Executable -m venv $testVenvDir 2>&1 | Out-Null
        
        if (Test-Path (Join-Path $testVenvDir "Scripts\python.exe")) {
            $testResults.VenvCreated = $true
            Write-Log "  ✓ Virtuele omgeving aangemaakt" -Level "SUCCESS"
        }
        else {
            throw "Kan virtuele omgeving niet aanmaken"
        }
        
        # 2. Installeer dependencies
        Write-Log "  [2/3] Installeren dependencies (PySide6, etc.)..."
        $testPip = Join-Path $testVenvDir "Scripts\pip.exe"
        $installOutput = & $testPip install -r $RequirementsFile --quiet 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            $testResults.DependenciesInstalled = $true
            Write-Log "  ✓ Dependencies geïnstalleerd" -Level "SUCCESS"
        }
        else {
            $testResults.Errors += "Dependency installatie mislukt: $installOutput"
            Write-Log "  ✗ Dependency installatie mislukt" -Level "ERROR"
        }
        
        # 3. Test imports
        Write-Log "  [3/3] Testen van imports..."
        $testPython = Join-Path $testVenvDir "Scripts\python.exe"
        $importTest = @"
import sys
try:
    import PySide6.QtWidgets
    print('✓ PySide6')
except Exception as e:
    print(f'✗ PySide6: {e}')
    sys.exit(1)

try:
    from ui.ui2code_super_engine import UI2CodeSuperEngine
    print('✓ UI2Code')
except Exception as e:
    print(f'✗ UI2Code: {e}')
    sys.exit(1)

print('✓ Alle imports succesvol')
sys.exit(0)
"@
        
        $importOutput = & $testPython -c $importTest 2>&1
        Write-Log "  Import test output: $importOutput"
        
        if ($LASTEXITCODE -eq 0) {
            $testResults.ImportsSuccessful = $true
            $testPassed = $true
            Write-Log "  ✓ Alle imports succesvol" -Level "SUCCESS"
        }
        else {
            $testResults.Errors += "Import test mislukt met exit code $LASTEXITCODE"
            Write-Log "  ✗ Import test mislukt" -Level "ERROR"
        }
    }
    catch {
        $testResults.Errors += $_.Exception.Message
        Write-Log "  ✗ Test mislukt: $_" -Level "ERROR"
    }
    finally {
        # Cleanup tijdelijke venv
        if (Test-Path $testVenvDir) {
            Write-Log "  Opruimen tijdelijke testomgeving..."
            Remove-Item -Recurse -Force $testVenvDir -ErrorAction SilentlyContinue
        }
    }
    
    return @{
        Passed = $testPassed
        Results = $testResults
    }
}

# ============================================================================
# PYTHON VERWIJDERING MET VEILIGHEIDSCONTROLES
# ============================================================================
function Test-Python314Usage {
    Write-Log "Controleren op ander gebruik van Python 3.14..." -Level "WARNING"
    
    $warnings = @()
    
    # Check voor andere venvs die Python 3.14 gebruiken
    $venvPattern = Join-Path $ProjectRoot "*.venv*"
    $venvs = Get-ChildItem -Path $venvPattern -Directory -ErrorAction SilentlyContinue
    
    foreach ($venv in $venvs) {
        $venvPython = Join-Path $venv.FullName "Scripts\python.exe"
        if (Test-Path $venvPython) {
            try {
                $version = & $venvPython --version 2>&1
                if ($version -match "Python 3.14") {
                    $warnings += "Virtuele omgeving gebruikt Python 3.14: $($venv.FullName)"
                }
            }
            catch {}
        }
    }
    
    # Check voor bekende programma's
    $commonPrograms = @(
        "Django", "Flask", "FastAPI", "Jupyter", "Anaconda", "Miniconda"
    )
    
    foreach ($program in $commonPrograms) {
        $programPath = "$env:LOCALAPPDATA\$program"
        if (Test-Path $programPath) {
            $warnings += "Programma gevonden dat Python kan gebruiken: $program ($programPath)"
        }
    }
    
    return $warnings
}

function Confirm-Python314Removal {
    Write-Host "`n" -NoNewline
    Write-Host "=============================================" -ForegroundColor Red
    Write-Host "  PYTHON 3.14 VERWIJDEREN" -ForegroundColor Red
    Write-Host "=============================================" -ForegroundColor Red
    Write-Host "`n"
    Write-Host "Dit zal Python 3.14 van uw systeem verwijderen." -ForegroundColor Yellow
    Write-Host "Deze actie kan niet ongedaan worden gemaakt via dit script." -ForegroundColor Yellow
    Write-Host "`n"
    
    $usageWarnings = Test-Python314Usage
    if ($usageWarnings.Count -gt 0) {
        Write-Host "WAARSCHUWING - Python 3.14 wordt mogelijk gebruikt door:" -ForegroundColor Red
        foreach ($warning in $usageWarnings) {
            Write-Host "  ⚠ $warning" -ForegroundColor Yellow
        }
        Write-Host "`n"
    }
    
    Write-Host "Typ exact het volgende om te bevestigen:" -ForegroundColor Red
    Write-Host "  VERWIJDER PYTHON 3.14" -ForegroundColor White -BackgroundColor Red
    Write-Host "`n"
    
    $confirmation = Read-Host "Bevestiging"
    
    if ($confirmation -eq "VERWIJDER PYTHON 3.14") {
        Write-Log "Gebruiker heeft Python 3.14 verwijdering bevestigd" -Level "WARNING"
        return $true
    }
    else {
        Write-Log "Gebruiker heeft Python 3.14 verwijdering geweigerd (input: '$confirmation')" -Level "WARNING"
        Write-Host "`nPython 3.14 verwijdering geannuleerd." -ForegroundColor Yellow
        return $false
    }
}

function Remove-Python314 {
    param([hashtable]$Python314Info)
    
    Write-Log "Starten Python 3.14 verwijdering..." -Level "WARNING"
    
    # Check of geïnstalleerd via winget
    $wingetManaged = $false
    try {
        $wingetList = & winget list --id Python.Python.3.14 2>&1
        if ($wingetList -match "Python.Python.3.14") {
            $wingetManaged = $true
            Write-Log "Python 3.14 is winget-beheerd" -Level "DETECT"
        }
    }
    catch {
        Write-Log "Kan winget status niet bepalen: $_" -Level "WARNING"
    }
    
    if ($wingetManaged) {
        Write-Log "Verwijderen via winget..." -Level "WARNING"
        try {
            $uninstallCmd = "winget uninstall -e --id Python.Python.3.14 --silent"
            Write-Log "Uitvoeren: $uninstallCmd"
            Invoke-Expression $uninstallCmd 2>&1 | Out-Null
            Write-Log "Python 3.14 verwijderd via winget" -Level "SUCCESS"
            return $true
        }
        catch {
            Write-Error-Log "Winget uninstall mislukt: $_"
            Write-Host "`nAutomatische verwijdering mislukt." -ForegroundColor Red
        }
    }
    
    # Handmatige instructies
    Write-Host "`n=============================================" -ForegroundColor Yellow
    Write-Host "  HANDMATIGE VERWIJDERINGSINSTRUCTIES" -ForegroundColor Yellow
    Write-Host "=============================================" -ForegroundColor Yellow
    Write-Host "`nPython 3.14 is niet via winget geïnstalleerd."
    Write-Host "Volg deze stappen om handmatig te verwijderen:"
    Write-Host "`n1. Open Configuratiescherm > Programma's > Programma's en onderdelen"
    Write-Host "2. Zoek naar 'Python 3.14*' in de lijst"
    Write-Host "3. Klik met rechtermuisknop > Verwijderen"
    Write-Host "`nOf gebruik PowerShell als Administrator:"
    Write-Host "  Get-WmiObject Win32_Product | Where-Object { \$_.Name -like 'Python 3.14*' } | Remove-WmiObject"
    Write-Host "`n4. Verwijder ook deze mappen (indien aanwezig):"
    Write-Host "  - $($Python314Info.Executable)"
    Write-Host "  - $env:LOCALAPPDATA\Programs\Python\Python314"
    Write-Host "  - $env:ProgramFiles\Python314"
    Write-Host "`nDruk op een toets als u klaar bent..."
    Read-Host
    
    return $false
}

# ============================================================================
# PYTHON INSTALLATIE VIA WINGET
# ============================================================================
function Install-PythonViaWinget {
    param([string]$Version = "3.12")
    
    Write-Log "Installeren Python $Version via winget..."
    
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
        Write-Host "1. Download Python $Version van https://www.python.org/downloads/" -ForegroundColor Yellow
        Write-Host "2. Installeer winget: https://aka.ms/winget" -ForegroundColor Yellow
        Write-Host "`nDruk op een toets om af te sluiten..."
        if (!$NoPause) { $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
        exit 1
    }
    
    Write-Log "Installeren Python $Version 64-bit..."
    
    try {
        $installCmd = "winget install -e --id Python.Python.$Version --silent --accept-package-agreements --accept-source-agreements"
        Write-Log "Uitvoeren: $installCmd"
        
        $installOutput = Invoke-Expression $installCmd 2>&1
        Write-Log "Installatie output: $installOutput"
        
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        Write-Log "Python $Version installatie voltooid" -Level "SUCCESS"
        return $true
    }
    catch {
        Write-Error-Log "Python $Version installatie mislukt: $_"
        Write-Host "`n=== FOUT: Python installatie mislukt ===" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        Write-Host "`nInstalleer Python handmatig van https://www.python.org/downloads/" -ForegroundColor Yellow
        Write-Host "`nDruk op een toets om af te sluiten..."
        if (!$NoPause) { $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
        exit 1
    }
}

# ============================================================================
# BACKUP VAN CONFIGURATIEBESTANDEN
# ============================================================================
function Backup-Configuration {
    Write-Log "Maken back-up van configuratiebestanden..."
    
    if (!(Test-Path $ConfigBackupDir)) {
        New-Item -ItemType Directory -Path $ConfigBackupDir | Out-Null
    }
    
    $backupTimestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $configFiles = @(
        (Join-Path $ProjectRoot "config\engine_config.json")
    )
    
    foreach ($configFile in $configFiles) {
        if (Test-Path $configFile) {
            $backupName = "$(Split-Path $configFile -Leaf).$backupTimestamp.backup"
            $backupPath = Join-Path $ConfigBackupDir $backupName
            Copy-Item $configFile $backupPath -Force
            Write-Log "  Back-up: $(Split-Path $configFile -Leaf) -> $backupName" -Level "SUCCESS"
        }
    }
    
    Write-Log "Back-up voltooid in: $ConfigBackupDir" -Level "SUCCESS"
}

# ============================================================================
# VIRTUELE OMGEVING
# ============================================================================
function Setup-VirtualEnvironment {
    param([string]$PythonExe)
    
    Write-Log "Controleren virtuele omgeving: $VenvDir"
    
    $venvPython = Join-Path $VenvDir "Scripts\python.exe"
    $venvPip = Join-Path $VenvDir "Scripts\pip.exe"
    
    # Backup bestaande venv
    if (Test-Path $venvPython) {
        Write-Log "Bestaande .venv gevonden, maken back-up..."
        if (Test-Path $VenvBackupDir) {
            Remove-Item -Recurse -Force $VenvBackupDir -ErrorAction SilentlyContinue
        }
        Move-Item $VenvDir $VenvBackupDir -Force
        Write-Log "  Back-up: .venv -> .venv.backup" -Level "SUCCESS"
    }
    
    Write-Log "Aanmaken virtuele omgeving..."
    try {
        & $PythonExe -m venv $VenvDir
        Write-Log "Virtuele omgeving aangemaakt" -Level "SUCCESS"
    }
    catch {
        Write-Error-Log "Virtuele omgeving aanmaken mislukt: $_"
        throw "Kan virtuele omgeving niet aanmaken: $_"
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
# GEBRUIKERSKEUZES
# ============================================================================
function Show-Python314Options {
    Write-Host "`n=============================================" -ForegroundColor Yellow
    Write-Host "  PYTHON 3.14 COMPATIBILITEITSPROBLEEM" -ForegroundColor Yellow
    Write-Host "=============================================" -ForegroundColor Yellow
    Write-Host "`n"
    Write-Host "Python 3.14 is niet volledig compatibel met UI2Code." -ForegroundColor Red
    Write-Host "`n"
    Write-Host "Kies een optie:" -ForegroundColor Cyan
    Write-Host "`n"
    Write-Host "  [1] Python 3.14 behouden EN Python 3.12 64-bit daarnaast installeren" -ForegroundColor White
    Write-Host "      (Aanbevolen - geen wijzigingen aan Python 3.14)" -ForegroundColor Green
    Write-Host "`n"
    Write-Host "  [2] Python 3.14 VERWIJDEREN en daarna Python 3.12 installeren" -ForegroundColor White
    Write-Host "      (Let op: vereist expliciete bevestiging)" -ForegroundColor Yellow
    Write-Host "`n"
    Write-Host "  [3] Afbreken zonder wijzigingen" -ForegroundColor White
    Write-Host "`n"
    
    $choice = Read-Host "Voer keuze in (1, 2, of 3)"
    
    switch ($choice) {
        "1" { return "Install-312-SideBySide" }
        "2" { return "Remove-314-Install-312" }
        "3" { return "Abort" }
        default {
            Write-Host "Ongeldige keuze. Afbreken." -ForegroundColor Red
            return "Abort"
        }
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
    
    # 1. Detecteer alle Python versies
    $allPythons = Find-AllPythonVersions
    
    if ($allPythons.Count -eq 0) {
        Write-Log "Geen Python gevonden. Installeren Python $PreferredPythonMajor.$PreferredPythonMinor..."
        Install-PythonViaWinget -Version "$PreferredPythonMajor.$PreferredPythonMinor"
        
        $allPythons = Find-AllPythonVersions
        if ($allPythons.Count -eq 0) {
            Write-Error-Log "Python nog steeds niet gevonden na installatie"
            throw "Python installatie mislukt"
        }
    }
    
    # 2. Zoek Python 3.14
    $python314 = $allPythons | Where-Object { $_.Major -eq 3 -and $_.Minor -eq 14 } | Select-Object -First 1
    
    # 3. Zoek Python 3.12 of andere geschikte versie
    $suitablePythons = $allPythons | Where-Object {
        ($_.Major -eq 3 -and $_.Minor -ge $PreferredPythonMinor -and $_.Minor -lt 14) -or
        ($_.Major -eq 3 -and $_.Minor -eq 12)
    } | Sort-Object -Property Minor
    
    $python312 = $suitablePythons | Where-Object { $_.Major -eq 3 -and $_.Minor -eq 12 } | Select-Object -First 1
    
    # 4. Test Python 3.14 compatibiliteit als deze gevonden is
    $python314Compatible = $false
    if ($python314 -and !$SkipPython314Test) {
        $testResult = Test-Python314Compatibility -Python314Info $python314
        
        if ($testResult.Passed) {
            Write-Log "Python 3.14 is compatibel! Deze versie wordt gebruikt." -Level "SUCCESS"
            $python314Compatible = $true
            $selectedPython = $python314
        }
        else {
            Write-Log "Python 3.14 is NIET compatibel." -Level "WARNING"
            Write-Log "Fouten: $($testResult.Results.Errors -join ', ')" -Level "WARNING"
        }
    }
    
    # 5. Beslis welke Python te gebruiken
    if (!$python314) {
        # Geen Python 3.14, gebruik beste beschikbare
        if ($suitablePythons.Count -gt 0) {
            $selectedPython = $suitablePythons[0]
            Write-Log "Gebruiken: Python $($selectedPython.Version) (geen 3.14 gevonden)" -Level "SUCCESS"
        }
        else {
            # Installeer Python 3.12
            Write-Log "Geen geschikte Python gevonden. Installeren Python 3.12..."
            Install-PythonViaWinget -Version "3.12"
            $allPythons = Find-AllPythonVersions
            $selectedPython = $allPythons | Where-Object { $_.Major -eq 3 -and $_.Minor -eq 12 } | Select-Object -First 1
        }
    }
    elseif ($python314Compatible) {
        # Python 3.14 is compatibel
        Write-Log "Python 3.14 wordt gebruikt (compatibiliteitstest geslaagd)" -Level "SUCCESS"
    }
    else {
        # Python 3.14 is niet compatibel, toon opties
        $userChoice = Show-Python314Options
        
        switch ($userChoice) {
            "Install-312-SideBySide" {
                Write-Log "Keuze: Python 3.12 naast 3.14 installeren"
                Install-PythonViaWinget -Version "3.12"
                $allPythons = Find-AllPythonVersions
                $selectedPython = $allPythons | Where-Object { $_.Major -eq 3 -and $_.Minor -eq 12 } | Select-Object -First 1
            }
            "Remove-314-Install-312" {
                Write-Log "Keuze: Python 3.14 verwijderen en 3.12 installeren"
                
                if (Confirm-Python314Removal) {
                    Backup-Configuration
                    Remove-Python314 -Python314Info $python314
                    
                    Write-Log "Installeren Python 3.12..."
                    Install-PythonViaWinget -Version "3.12"
                    
                    $allPythons = Find-AllPythonVersions
                    $selectedPython = $allPythons | Where-Object { $_.Major -eq 3 -and $_.Minor -eq 12 } | Select-Object -First 1
                }
                else {
                    Write-Log "Verwijdering geannuleerd door gebruiker" -Level "WARNING"
                    Write-Host "`nOpdracht geannuleerd. Python 3.14 is niet verwijderd." -ForegroundColor Yellow
                    Write-Host "Installeer Python 3.12 handmatig als u UI2Code wilt gebruiken." -ForegroundColor Yellow
                    if (!$NoPause) { $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
                    exit 1
                }
            }
            "Abort" {
                Write-Log "Gebruiker heeft afgebroken" -Level "WARNING"
                Write-Host "`nOpdracht geannuleerd." -ForegroundColor Yellow
                if (!$NoPause) { $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
                exit 0
            }
        }
    }
    
    # 6. Validate geselecteerde Python
    if (!$selectedPython) {
        Write-Error-Log "Geen geschikte Python gevonden na alle pogingen"
        throw "Geen geschikte Python beschikbaar"
    }
    
    $versionInfo = $selectedPython
    Write-Log "`nGeselecteerde Python:" -Level "SUCCESS"
    Write-Log "  Versie: $($versionInfo.Version)"
    Write-Log "  Executable: $($versionInfo.Executable)"
    Write-Log "  Architectuur: $($versionInfo.Bits)-bit"
    Write-Log "  Detectiemethode: $($versionInfo.Method)"
    
    # 7. Setup virtual environment
    $venv = Setup-VirtualEnvironment -PythonExe $versionInfo.Executable
    Write-Log "Venv Python: $($venv.Python)"
    Write-Log "Venv Pip: $($venv.Pip)"
    
    # 8. Install dependencies
    Install-Dependencies -PipExe $venv.Pip -RequirementsPath $RequirementsFile
    
    # 9. Test imports
    Test-Imports -PythonExe $venv.Python
    
    # 10. Start GUI
    Write-Log "`n=== GUI Wordt Gestart ===" -Level "SUCCESS"
    Write-Log "Start logbestand: $LogPath"
    Write-Log "Detectie logbestand: $DetectLogPath"
    
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
    Write-Host "Detectielog: $DetectLogPath" -ForegroundColor Cyan
    Write-Host "`nDruk op een toets om af te sluiten..."
    if (!$NoPause) { $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") }
    
    exit 1
}
