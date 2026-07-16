# UI2Code

UI-to-Code conversion system for automated UI analysis and code generation.

## Fase 3A: Elementdetectie

Deze fase implementeert een minimale maar volledig werkende elementdetectie-keten.

### Wat "Detecteer UI" nu doet

Wanneer je op de knop **"Detecteer UI"** klikt:

1. **Afbeelding laden**: De detector laadt de geselecteerde afbeelding.
2. **Contourdetectie**: Een deterministische, op randen gebaseerde methode vindt rechthoekige regio's:
   - Converteert afbeelding naar grijstinten
   - Detecteert randen met gradient-analyse
   - Vindt verbonden componenten via flood-fill
   - Benadert regio's als rechthoeken
3. **Filtering**:
   - Verwijdert zeer kleine elementen (< 16 pixels)
   - Verwijdert achtergrond-achtige rechthoeken (> 95% dekking)
   - Verwijdert duplicaten en sterk overlappende elementen
4. **Kleurextractie**: Bepaalt de dominante kleur per element.
5. **Resultaten weergeven**:
   - Toont elementen in een tabel (Elementen-tabblad)
   - Element Editor toont bewerkbare velden
   - Selectie synchroniseert tussen tabel en editor

### Gebruik

1. Klik op **"Kies afbeelding"** en selecteer een UI-screenshot.
2. Klik op **"Detecteer UI"**.
3. Bekijk de gedetecteerde elementen in het tabblad **"Elementen"**.
4. Klik op een rij om het element in de **Element Editor** te bekijken.
5. Bewerk velden (Naam, Type, Categorie, Positie, Grootte, Kleur).
6. Wijzigingen worden direct gesynchroniseerd.

### Bekende beperkingen

- **Geen AI/ML**: Dit is een basis contourdetector, geen slimme herkenning.
- **Geen OCR**: Label-tekst wordt niet herkend.
- **Geen componentclassificatie**: Alle elementen zijn "unknown" type.
- **Geen overlay**: Rechthoeken worden niet visueel getoond op de afbeelding.
- **Geen export**: Resultaten kunnen nog niet worden geëxporteerd.
- **Geen snapshot/state**: Opslaan/herladen is nog niet geïmplementeerd.

### Technische details

- **Data model**: `engine/models.py` - `UIElement` dataclass
- **Detector**: `engine/ui2code_detect.py` - `UI2CodeDetect.detect_elements()`
- **GUI**: `ui/ui2code_super_engine.py` - Tabel en editor binding

## Tests

```bash
# Model tests
python tools/test_models.py

# Detection tests
python tools/test_detection.py

# GUI tests (vereist PySide6)
python tools/test_gui.py

# Import tests
python tools/test_import.py

# PowerShell syntax (vereist Windows/PowerShell)
python tools/test_powershell_syntax.py
```

## Vereisten

- Python 3.12
- PySide6 (voor GUI en detectie)
- Windows (voor PowerShell startup script)

## GUI starten

```powershell
.\Start-UI2Code.ps1
```

Of direct:

```bash
python -m ui.ui2code_super_engine
```

