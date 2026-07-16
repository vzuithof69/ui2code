# Windows Installatie- en Opstartinstructies voor UI2Code Super-Engine

## Vereisten

- Windows 10/11 (64-bit)
- Python 3.10 - 3.14 (64-bit)
- Git (optioneel, voor repository clone)

---

## 🚀 Snelle Start (Aanbevolen)

### Methode 1: start.bat (Eenvoudigst)

1. **Navigeer naar projectmap** (optioneel, kan vanuit elke locatie):
   ```cmd
   cd ui2code
   ```

2. **Start de applicatie**:
   ```cmd
   start.bat
   ```

**Wat start.bat automatisch doet:**
- ✅ Detecteert ALLE geïnstalleerde 64-bit Python versies
- ✅ Toont versie, executable-pad, architectuur en installatiemethode
- ✅ Test Python 3.14 eerst met echte UI2Code dependencies
- ✅ Gebruikt Python 3.14 als deze volledig compatibel is
- ✅ Biedt keuzes als Python 3.14 niet compatibel is:
  - Python 3.12 naast 3.14 installeren (aanbevolen)
  - Python 3.14 verwijderen en 3.12 installeren
  - Afbreken zonder wijzigingen
- ✅ Verwijdert NOOIT Python zonder expliciete bevestiging
- ✅ Maakt back-up van configuratiebestanden
- ✅ Controleert op ander gebruik van Python 3.14
- ✅ Maakt een virtuele omgeving (.venv)
- ✅ Installeert alle dependencies (PySide6, etc.)
- ✅ Test imports vóór het starten
- ✅ Start de GUI
- ✅ Logt alle acties naar `logs/startup-YYYYMMDD-HHMMSS.log`
- ✅ Logt detectie naar `logs/python-detection-YYYYMMDD-HHMMSS.log`
- ✅ Toon foutmeldingen in `logs/latest-error.log`

### Methode 2: PowerShell Direct

```powershell
# Standaard
.\Start-UI2Code.ps1

# Met opties
.\Start-UI2Code.ps1 -Verbose          # Uitgebreide output
.\Start-UI2Code.ps1 -NoPause          # Geen pause bij fouten
.\Start-UI2Code.ps1 -SkipPython314Test # Python 3.14 test overslaan
```

### Methode 3: Handmatig (Voor Ontwikkelaars)

```powershell
# 1. Virtuele omgeving aanmaken
python -m venv .venv

# 2. Activeren
.\.venv\Scripts\Activate.ps1

# 3. Dependencies installeren
pip install -r requirements.txt

# 4. GUI starten
python -m ui.ui2code_super_engine
```

---

## 📋 Uitgebreide Installatie

### Stap 1: Repository Clonen (indien niet gedaan)

```powershell
git clone https://github.com/vzuithof69/ui2code.git
cd ui2code
```

### Stap 2: Python Detectie (Automatisch)

Het startup script detecteert Python via 4 methoden:

1. **py launcher** (`py -0p`) - Aanbevolen methode
2. **PATH environment variable** (`where python`)
3. **Windows Registry** (HKLM/HKCU SOFTWARE\Python\PythonCore)
4. **Bekende installatiemappen** (Program Files, LocalAppData, etc.)

**Handmatig controleren:**
```powershell
# py launcher (beste optie)
py -0p

# PATH
where python
where python3

# Versie check
python --version
py --version
```

### Stap 3: Winget (Voor Automatische Installatie)

Winget is ingebouwd in Windows 10/11. Controleer beschikbaarheid:

```powershell
winget --version
```

**Winget niet gevonden?** Installeer via:
- Microsoft Store: https://aka.ms/winget
- Of download van GitHub: https://github.com/microsoft/winget-cli/releases

---

## 🔍 Python 3.14 Compatibiliteit

### Automatische Test

Bij het opstarten test het script Python 3.14 door:

1. **Tijdelijke virtuele omgeving** aanmaken (`.venv.py314test`)
2. **Echte dependencies installeren** uit `requirements.txt` (PySide6, etc.)
3. **Alle vereiste imports uitvoeren**:
   - `PySide6.QtWidgets`
   - `ui.ui2code_super_engine.UI2CodeSuperEngine`
4. **Resultaat**: Als alle imports slagen, wordt Python 3.14 gebruikt

### Als Python 3.14 Niet Compatibel Is

Het script toont drie opties:

**Optie 1: Python 3.12 naast 3.14 installeren (Aanbevolen)**
- ✅ Python 3.14 blijft behouden voor andere projecten
- ✅ Python 3.12 wordt gebruikt voor UI2Code
- ✅ Geen risico op dataverlies

**Optie 2: Python 3.14 verwijderen en 3.12 installeren**
- ⚠️ **Vereist expliciete bevestiging**: Typ exact `VERWIJDER PYTHON 3.14`
- ⚠️ Script controleert eerst op ander gebruik:
  - Andere virtuele omgevingen
  - Bekende programma's (Django, Flask, Jupyter, etc.)
- ⚠️ Toont waarschuwingen als Python 3.14 elders wordt gebruikt
- ✅ Maakt back-up van configuratiebestanden
- ✅ Verwijdert via winget (indien winget-beheerd)
- ✅ Geeft handmatige instructies als niet winget-beheerd

**Optie 3: Afbreken zonder wijzigingen**
- ✅ Geen wijzigingen aan Python installaties
- ℹ️ Installeer Python 3.12 handmatig indien gewenst

---

## 🧪 Visuele Test

Na het opstarten van de GUI:

1. **Kies afbeelding** knop:
   - Klik op "Kies afbeelding"
   - Selecteer een PNG, JPG, JPEG of BMP bestand
   - De afbeelding moet verschijnen in het previewgebied

2. **Zoom functionaliteit**:
   - Test de `-` knop (zoom uit)
   - Sleep de slider (van 10% tot 500%)
   - Test de `+` knop (zoom in)
   - Controleer of het percentage correct wordt weergegeven

3. **Element Editor**:
   - Controleer of alle velden aanwezig zijn:
     - ID
     - Naam
     - Type
     - Categorie
     - Kleur (RGB)
     - Kleur (HEX) ← **Let op: moet HEX zijn, niet HFX**
     - X, Y, W, H

4. **Tabs**:
   - Controleer de 4 tabs rechts onder:
     - Elementen
     - Groepen
     - Labels (OCR)
     - OCR Zones

5. **Overige knoppen**:
   - Klik op "Detecteer UI", "OCR Labels", etc.
   - Er moet een melding verschijnen: "Nog niet geïmplementeerd"

---

## 📁 Bestandsstructuur

```
ui2code/
├── start.bat                 # Hoofd opstartscript (gebruik deze!)
├── Start-UI2Code.ps1         # PowerShell installatie & validatie (976 regels)
├── requirements.txt          # Python dependencies
├── .venv/                    # Virtuele omgeving (automatisch aangemaakt)
├── .venv.backup/             # Back-up van vorige .venv
├── config.backup/            # Back-up van configuratiebestanden
├── logs/                     # Logbestanden (automatisch aangemaakt)
│   ├── startup-*.log        # Startup logs per sessie
│   ├── python-detection-*.log  # Python detectie logs
│   └── latest-error.log     # Laatste foutmeldingen
├── ui/
│   └── ui2code_super_engine.py
├── engine/
│   ├── ui2code_core.py
│   ├── ui2code_detect.py
│   ├── ui2code_layout.py
│   └── ui2code_export.py
└── tools/
    ├── test_import.py
    └── test_gui.py
```

---

## 🔍 Logbestanden

### Startup Logs
- **Locatie:** `logs/startup-YYYYMMDD-HHMMSS.log`
- **Bevat:** Python versie, executable pad, pip versie, installatiestappen, imports, commando's, exitcodes

### Python Detection Logs
- **Locatie:** `logs/python-detection-YYYYMMDD-HHMMSS.log`
- **Bevat:** Alle gedetecteerde Python versies, versie-informatie, executable-paden, installatiemethoden

### Error Log
- **Locatie:** `logs/latest-error.log`
- **Bevat:** Laatste foutmeldingen en stacktraces

---

## ⚠️ Bekende Problemen en Oplossingen

### Probleem 1: "Python niet gevonden"

**Oorzaak:** Python is niet geïnstalleerd of niet toegevoegd aan PATH.

**Oplossing:**
1. Automatisch: start.bat probeert Python te installeren via winget
2. Handmatig: Download van https://www.python.org/downloads/
   - ✅ Vink "Add Python to PATH" aan tijdens installatie
   - ✅ Kies "Install for all users" of "Install just for me"

### Probleem 2: "winget niet beschikbaar"

**Oorzaak:** Winget is niet geïnstalleerd op dit systeem.

**Oplossing:**
1. Installeer winget: https://aka.ms/winget
2. Of installeer Python handmatig van https://www.python.org/downloads/

### Probleem 3: "PowerShell execution policy"

**Oorzaak:** PowerShell staat script execution niet toe.

**Oplossing:**
```powershell
# Eenmalig uitvoeren als administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Of gebruik start.bat (deze omzeilt de policy)
```

### Probleem 4: "Python 3.14 is niet compatibel"

**Oorzaak:** PySide6 of andere dependencies werken niet met Python 3.14.

**Oplossing:**
1. **Aanbevolen:** Kies optie 1 - Python 3.12 naast 3.14 installeren
2. Python 3.12 installeren via:
   ```powershell
   winget install -e --id Python.Python.3.12
   ```
3. Opnieuw `start.bat` uitvoeren

### Probleem 5: "VERWIJDER PYTHON 3.14 bevestiging"

**Oorzaak:** Script vereist expliciete bevestiging voor verwijdering.

**Oplossing:**
- Typ exact: `VERWIJDER PYTHON 3.14` (hoofdletters, spaties)
- Andere input wordt geweigerd
- Script toont waarschuwingen voor ander gebruik van Python 3.14

### Probleem 6: "Qt platform plugin 'windows' could not be loaded"

**Oorzaak:** Microsoft Visual C++ Redistributable ontbreekt.

**Oplossing:**
Download en installeer: https://aka.ms/vs/17/release/vc_redist.x64.exe

### Probleem 7: "libEGL.dll" of "libGLESv2.dll" niet gevonden

**Oorzaak:** PySide6 DLL's ontbreken.

**Oplossing:**
```powershell
# Herinstalleer PySide6
.\.venv\Scripts\activate.ps1
pip uninstall PySide6
pip install PySide6 --force-reinstall
```

### Probleem 8: GUI opent maar toont zwarte/lege window

**Oorzaak:** Graphics driver probleem.

**Oplossing:**
1. Update je graphics drivers
2. Herinstalleer PySide6:
   ```powershell
   pip uninstall PySide6
   pip install PySide6
   ```

### Probleem 9: Virtuele omgeving corrupt

**Oorzaak:** .venv directory is beschadigd.

**Oplossing:**
```powershell
# Verwijder .venv en laat opnieuw aanmaken
Remove-Item -Recurse -Force .venv
start.bat
```

---

## 🧪 Tests Uitvoeren

### Import Test
```powershell
python -m tools.test_import
```

### GUI Test (Headless)
```powershell
$env:QT_QPA_PLATFORM="offscreen"
python -m tools.test_gui
```

### Python Detectie Test
```powershell
# Toont alle gedetecteerde Python versies
.\Start-UI2Code.ps1 -SkipPython314Test
```

---

## 📝 Requirements

De volgende packages worden automatisch geïnstalleerd:

```txt
PySide6>=6.5.0
```

**Let op:** requirements.txt wordt bijgewerkt wanneer er nieuwe dependencies worden toegevoegd.

---

## 🛠️ Ontwikkelaars Opties

### PowerShell Parameters

```powershell
# Verbose output
.\Start-UI2Code.ps1 -Verbose

# Geen pause bij fouten (voor scripting)
.\Start-UI2Code.ps1 -NoPause

# Python 3.14 test overslaan
.\Start-UI2Code.ps1 -SkipPython314Test
```

### Handmatige Dependency Installatie

```powershell
.\.venv\Scripts\activate.ps1
pip install -r requirements.txt
```

### Python Versie Specificeren

Als je meerdere Python versies hebt:

```powershell
# Gebruik specifieke versie via py launcher
py -3.12 -m venv .venv
```

### Back-up Terugzetten

```powershell
# .venv back-up terugzetten
Remove-Item -Recurse -Force .venv
Move-Item .venv.backup .venv

# Config back-up terugzetten
Copy-Item config.backup\*.json config\
```

---

## 🔒 Veiligheidsmaatregelen

### Python Verwijdering

- ❌ **NOOIT** automatisch of stilzwijgend verwijderen
- ✅ Vereist expliciete bevestiging: `VERWIJDER PYTHON 3.14`
- ✅ Controleert op ander gebruik (venvs, programma's)
- ✅ Toont waarschuwingen voor afhankelijkheden
- ✅ Maakt back-up van configuratiebestanden
- ✅ Gebruikt winget uninstall alleen voor winget-beheerde installaties
- ✅ Geeft veilige handmatige instructies voor niet-winget installaties

### Back-ups

- ✅ `.venv.backup` - Vorige virtuele omgeving
- ✅ `config.backup/` - Configuratiebestanden met timestamp
- ✅ Logs worden nooit verwijderd

### Geen Vaste Pad

- ✅ Gebruikt `%~dp0` voor locatie-onafhankelijk starten
- ✅ Geen hardcoded gebruikerspaden
- ✅ Geen opslag van tokens of geheimen

---

## 📞 Support

Bij problemen:

1. **Controleer logs:**
   - `logs/startup-*.log` voor volledige output
   - `logs/python-detection-*.log` voor detectie details
   - `logs/latest-error.log` voor foutmeldingen

2. **Controleer omgeving:**
   ```powershell
   python --version
   pip --version
   pip list
   py -0p
   ```

3. **Maak issue aan:**
   https://github.com/vzuithof69/ui2code/issues

**Voeg altijd toe:**
- Windows versie
- Python versie(s) uit `logs/python-detection-*.log`
- Foutmelding uit `logs/latest-error.log`
- Stappen om het probleem te reproduceren
- Output van `py -0p`
