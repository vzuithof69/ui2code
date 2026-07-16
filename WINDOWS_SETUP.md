# Windows Installatie- en Opstartinstructies voor UI2Code Super-Engine

## Vereisten

- Windows 10/11 (64-bit)
- Python 3.10 of hoger (64-bit)
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
- ✅ Controleert Python versie (vereist 3.10+ 64-bit)
- ✅ Installeert Python via winget als deze ontbreekt
- ✅ Maakt een virtuele omgeving (.venv)
- ✅ Installeert alle dependencies (PySide6, etc.)
- ✅ Test imports vóór het starten
- ✅ Start de GUI
- ✅ Logt alle acties naar `logs/startup-YYYYMMDD-HHMMSS.log`
- ✅ Toon foutmeldingen in `logs/latest-error.log`

### Methode 2: PowerShell Direct

```powershell
.\Start-UI2Code.ps1
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

### Stap 2: Controleer Python (Optioneel)

De opstartscripts controleren dit automatisch, maar handmatig controleren:

```powershell
# Controleer Python versie
python --version

# Of gebruik py launcher (aanbevolen op Windows)
py --version
py --list

# Vereist: Python 3.10+ 64-bit
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
├── Start-UI2Code.ps1         # PowerShell installatie & validatie
├── requirements.txt          # Python dependencies
├── .venv/                    # Virtuele omgeving (automatisch aangemaakt)
├── logs/                     # Logbestanden (automatisch aangemaakt)
│   ├── startup-*.log        # Startup logs per sessie
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

### Probleem 4: "Qt platform plugin 'windows' could not be loaded"

**Oorzaak:** Microsoft Visual C++ Redistributable ontbreekt.

**Oplossing:**
Download en installeer: https://aka.ms/vs/17/release/vc_redist.x64.exe

### Probleem 5: "libEGL.dll" of "libGLESv2.dll" niet gevonden

**Oorzaak:** PySide6 DLL's ontbreken.

**Oplossing:**
```powershell
# Herinstalleer PySide6
.\.venv\Scripts\activate.ps1
pip uninstall PySide6
pip install PySide6 --force-reinstall
```

### Probleem 6: GUI opent maar toont zwarte/lege window

**Oorzaak:** Graphics driver probleem.

**Oplossing:**
1. Update je graphics drivers
2. Herinstalleer PySide6:
   ```powershell
   pip uninstall PySide6
   pip install PySide6
   ```

### Probleem 7: Virtuele omgeving corrupt

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

### Alle Tests
```powershell
start.bat  # Start GUI handmatig testen
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
py -3.11 -m venv .venv
```

---

## 📞 Support

Bij problemen:

1. **Controleer logs:**
   - `logs/startup-*.log` voor volledige output
   - `logs/latest-error.log` voor foutmeldingen

2. **Controleer omgeving:**
   ```powershell
   python --version
   pip --version
   pip list
   ```

3. **Maak issue aan:**
   https://github.com/vzuithof69/ui2code/issues

**Voeg altijd toe:**
- Windows versie
- Python versie
- Foutmelding uit `logs/latest-error.log`
- Stappen om het probleem te reproduceren
