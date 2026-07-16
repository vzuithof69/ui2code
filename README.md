# UI2Code

UI-to-Code conversion system for automated UI analysis and code generation.

## Fase 3B: Multi-Pass UI Herkenning

Deze fase implementeert geavanceerde UI-herkenning met meerdere detectiemethoden,
classificatie, hiërarchie en overlay-weergave.

### Detectiepassen

De detector voert nu **meerdere herkenningspassen** uit:

**A. Contourdetectie** (bestaand + verbeterd)
- Rand-gebaseerde detectie via gradient-analyse
- Connected component flood-fill
- Configureerbare minimumafmetingen

**B. Kleurvlakdetectie**
- Vindt rechthoekige regio's met distincte kleuren
- Gebruik kleurverschil met omgeving
- Negeert uniforme achtergronden

**C. Lijnendetectie**
- Detecteert horizontale en verticale lijnen
- Combineert lijnstukken tot rechthoeken
- Handig voor invoervelden, panelen, separators

**D. Connected Components**
- Vindt samenhangende visuele regio's
- Filtert ruis en kleine fragmenten
- Gebaseerd op kleurverschil met buren

**E. Tekstzone-kandidaten**
- Identificeert potentiële tekstgebieden
- Gebruikt lokaal contrast en clustering
- Markeert als `text_candidate` (voor toekomstige OCR)

### Resultaatfusie en Filtering

Na alle passes worden resultaten gefuseerd:

- **IoU (Intersection over Union)** verwijdert duplicaten
- **Non-maximum suppression** behoudt beste detecties
- **Filtering** van kleine elementen en achtergronden
- **Sortering** van boven-naar-beneden, links-naar-rechts

### Confidence Scores

Elk element krijgt een confidence (0.0 - 1.0) gebaseerd op:

- Rechthoekigheid van de vorm
- Contrast met omgeving
- Grootte van het element
- Aantal detectiepassen dat het vond
- Overlap-kwaliteit met andere detecties
- Randsterkte

### Elementclassificatie

Ondersteunde typen:

| Type | Beschrijving | Heuristiek |
|------|-------------|------------|
| `window` | Hoofdvenster | Groot, bevat veel kinderen |
| `panel` | Container panel | Groot, bevat meerdere elementen |
| `group` | Groep container | Medium, bevat elementen |
| `button` | Knop | Klein, vierkantig |
| `label` | Tekstlabel | Text zone candidate |
| `input` | Invoerveld | Breed, kort |
| `checkbox` | Selectievakje | Klein vierkant |
| `tab` | Tabblad | Horizontale reeks |
| `table_or_list` | Tabel/lijst | Groot, gestructureerd |
| `image` | Afbeelding | Diverse vormen |
| `separator` | Scheidingslijn | Zeer dun |
| `unknown` | Onbekend | Default bij lage zekerheid |

### Hiërarchie (Parent-Child)

Elementen krijgen **parent-child relaties**:

- `parent_id` verwijst naar container-element
- Kleinste geldige container wordt gekozen
- Meerdere niveaus ondersteund
- Geen cycli mogelijk
- Buttons/labels kunnen binnen panels vallen

### Preview Overlay

Gedetecteerde elementen worden **visueel getoond** over de afbeelding:

- Gekleurde rechthoeken per elementtype
- Geselecteerde elementen geel gemarkeerd
- Element-ID labels voor grote elementen
- Overlay schaalt mee met zoom
- Semi-transparante vulling

### Handmatige Correcties

Wijzigingen van gebruikers worden **bijgehouden**:

- `manually_corrected` set registreert bewerkte velden
- Bij herdetectie: behoud correcties waar mogelijk
- Koppel oude/nieuwe elementen via overlap
- Log behouden correcties

### OCR-Voorbereiding

Toekomstige OCR is **voorbereid**:

- `OCRLabel` model met bbox, text, confidence
- `text_candidate` veld op UIElement
- Voorbewerking configuratie (grayscale, contrast, upscale)
- Per-zone OCR in plaats van volledige afbeelding

### Versieerbaar JSON-Schema

Schema **versie 1.0** met:

```json
{
  "schema_version": "1.0",
  "engine_version": "0.3.0",
  "created_at": "ISO timestamp",
  "image": { "path": "...", "width": 800, "height": 600 },
  "detection_settings": { ... },
  "elements": [...],
  "ocr_labels": [...],
  "statistics": { ... }
}
```

- Volledige serialisatie/deserialisatie
- Validatie
- Roundtrip tests

### Logging

Uitgebreide logging van:

- Start/einde per detectiepas
- Aantal resultaten per pass
- Verwijderde duplicaten
- Uiteindelijke elementaantallen
- Classificatieverdeling
- Confidence statistieken
- Handmatige correcties

## Gebruik

1. Klik op **"Kies afbeelding"** en selecteer een UI-screenshot.
2. Klik op **"Detecteer UI"**.
3. Bekijk elementen in tabel **én** overlay op afbeelding.
4. Klik op een rij om element te selecteren (geel gemarkeerd).
5. Bewerk velden in **Element Editor**.
6. Wijzigingen worden direct gesynchroniseerd met tabel.

## Bekende Beperkingen

- **Geen AI/ML**: Regelgebaseerde heuristieken, geen deep learning
- **Geen echte OCR**: Text zones alleen gedetecteerd, niet gelezen
- **Geen codegeneratie**: HTML/PySide6 export komt later
- **Geen snapshot/load**: Knoppen aanwezig maar nog niet werkend
- **Classificatie niet perfect**: Heuristieken kunnen fouten maken

## Tests

```bash
# Model tests
python tools/test_models.py

# Fase 3B tests (IoU, hiërarchie, JSON, classificatie)
python tools/test_fase3b.py

# Detection and logging tests
python tools/test_detection_logging.py

# Editor synchronization tests
python tools/test_editor_sync.py

# GUI tests (vereist PySide6)
python tools/test_gui.py

# Import tests
python tools/test_import.py
```

## Technische Details

- **Modellen**: `engine/models.py` - UIElement met parent_id, manually_corrected
- **OCR Model**: `engine/ocr_models.py` - OCRLabel voor toekomstige OCR
- **Schema**: `engine/schema_v1.py` - JSON schema v1.0
- **Detector**: `engine/ui2code_detect_v2.py` - Multi-pass detectie
- **Overlay**: `ui/preview_overlay.py` - Overlay rendering
- **GUI**: `ui/ui2code_super_engine.py` - Tabel, editor, overlay binding

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

## Fase 3A (Vorige Versie)

Zie [originele README](#fase-3a-elementdetectie) voor Fase 3A documentatie.

