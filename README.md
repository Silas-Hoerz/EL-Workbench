# EL-Workbench

![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)
![Lizenz](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.12.5-blue)

**English version below**

Modulare Python-Plattform zur Ansteuerung von Laborgeräten und zur Auswertung von Messdaten – hauptsächlich für Elektrolumineszenz-Messplatz entwickelt.

---

## Entwickler-Doku: Das EL-Workbench erweitern

Diese Dokumentation richtet sich an alle, die das System mit eigenen Funktionen, Geräteanbindungen oder Analysemodulen ausbauen möchten – egal ob für Studienarbeiten, Forschung oder Laborexperimente.

---

## Architektur: Das `SharedState`-Konzept mit APIs

Das Herzstück unseres Systems ist weiterhin das **`SharedState`-Objekt**. Es dient nun aber nicht mehr für den direkten Datenzugriff oder die Registrierung von Funktionen. Stattdessen fungiert es als **zentraler Verteiler für API-Instanzen**.

### Das bedeutet:

- **Zentraler Zugriff:** Für spezifische Datenbereiche (z. B. Profile, Gerätedaten) oder komplexe Gerätesteuerungen stellen wir **dedizierte API-Klassen** bereit (z. B. `ProfileApi`, `SmuApi`). Diese APIs sind der primäre Weg, um auf Daten zuzugreifen oder Geräte zu steuern.
- **Kapselung:** Die **Tabs** (Benutzeroberflächen-Module) sind für die Anzeige und Interaktion mit der UI zuständig. Datenhaltung und Speicherung übernehmen sie weiterhin selbst, nutzen jedoch die APIs zur Kommunikation.
- **Flüchtige Daten:** Für sehr dynamische Messdaten (z. B. aktuelle Wellenlängen/Intensitäten eines Spektrums), die temporär von einem Tab erzeugt und von anderen gelesen werden, darf `SharedState` weiterhin Attribute direkt bereitstellen.

Das Ergebnis ist ein noch klarer strukturiertes, modular erweiterbares System mit **klar definierten Schnittstellen (APIs)**.

---

## Neues Modul in 4 Schritten

### 1. Modul-Datei anlegen

Im Verzeichnis `tabs/` eine neue Python-Datei mit sinnvollem Namen erstellen, z. B. `meine_analyse_tab.py`.

---

### 2. Modul-Klasse schreiben

Jedes Modul ist eine `QWidget`-Klasse. Der `SharedState` wird im Konstruktor übergeben – primär zum Zugriff auf APIs:

```python
# /tabs/meine_analyse_tab.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
import numpy as np

class MeineAnalyseTab(QWidget):
    def __init__(self, shared_data):
        super().__init__()
        self.shared_data = shared_data
        self.profile_api = shared_data.profile_api
        self.smu_api = shared_data.smu_api
        self.current_wavelengths = shared_data.wavelengths 
        self.current_intensities = shared_data.intensities
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        info_label = QLabel("Dies ist mein neues Analyse-Modul.")
        mein_button = QPushButton("Analyse starten")
        mein_button.clicked.connect(self.fuehre_analyse_durch)
        
        layout.addWidget(info_label)
        layout.addWidget(mein_button)
    
    def fuehre_analyse_durch(self):
        print("Analyse wird durchgeführt…")
```

---

### 3. Gemeinsame Ressourcen über APIs nutzen

**Beispiel: Spektrum-Peak finden (flüchtige Daten)**

```python
def finde_spektrum_peak(self):
    if self.shared_data.wavelengths is not None and self.shared_data.intensities.size > 0:
        intensities = self.shared_data.intensities
        wavelengths = self.shared_data.wavelengths
        peak_index = np.argmax(intensities)
        print(f"Peak bei {wavelengths[peak_index]:.2f} nm gefunden.")
    else:
        print("Keine Spektrometer-Daten vorhanden.")
```

**Beispiel: SMU fernsteuern über `SmuApi`**

```python
def steuere_smu_fern(self):
    if self.smu_api:
        print("SMU wird angesteuert (0.5 V)…")
        result = self.smu_api.apply_and_measure(
            channel='a',
            is_voltage_source=True,
            level=0.5,
            limit=0.01
        )
        if result:
            current, voltage = result
            print(f"Messwert: {voltage:.4f} V, {current:.4e} A")
        else:
            print("SMU-Operation fehlgeschlagen.")
    else:
        print("SMU-API nicht verfügbar.")
```

**Beispiel: Profil abrufen über `ProfileApi`**

```python
def lade_aktives_profil(self):
    if self.profile_api:
        active_profile = self.profile_api.get_active_profile()
        if active_profile:
            print(f"Aktives Profil: {active_profile.get('name', 'Unbekannt')} (ID: {active_profile.get('id', 'N/A')})")
        else:
            print("Kein aktives Profil geladen.")
    else:
        print("Profile-API nicht verfügbar.")
```

---

### 4. Modul registrieren (`main.py`)

**Import in `main.py`:**

```python
from tabs.meine_analyse_tab import MeineAnalyseTab
```

**In `load_modules()` einfügen:**

```python
# Vorher sicherstellen, dass die APIs existieren
self.shared_data.profile_api = ProfileApi(...)
self.shared_data.smu_api = SmuApi(...)

mein_tab = MeineAnalyseTab(self.shared_data)
self.tabs.addTab(mein_tab, "Meine Analyse")
```

Fertig! Der neue Tab ist integriert.

---

## Code-Organisation

| Verzeichnis   | Inhalt                                                                 |
|---------------|------------------------------------------------------------------------|
| `main.py`     | Einstiegspunkt, Initialisierung                                        |
| `tabs/`       | UI-Module (`QWidget`-Klassen), pro Datei ein Tab                       |
| `api/`        | API-Klassen für Daten & Geräte                                         |
| `data/`       | Persistente Dateien (z. B. JSON-Profile)                               |
| `devices/`    | Gerätespezifische Wrapper oder Treiber                                 |
| `styles/`     | Stylesheets (.qss)                                                     |
| `other/`      | Hilfsdialoge und sonstige Funktionen                                   |

---

## Datenhaltung und Persistenz

- **Format:** JSON
- **Standardattribute:** `id`, `name`
- **Datensicherheit:** Rückgaben aus API-Methoden sollten `.copy()` verwenden
- **Flüchtige Daten:** Direkter Zugriff auf z. B. Wellenlängen/Intensitäten erlaubt

---

## Fehlerbehandlung und Benutzerfeedback

- **try-except** für alle kritischen Operationen
- **QMessageBox** oder **Statusleiste** für Benutzerfeedback
- APIs sollten **keine Dialoge** öffnen – nur Rückgabewerte

---

## Dokumentation

- **README.md**: Aktuell und vollständig halten
- **Docstrings**: Für alle Module, Klassen und komplexeren Funktionen
- **Kommentare:** Erklären *Warum*, nicht nur *Was*

---

## EL-Workbench (English Version)

Modular Python platform for controlling lab equipment and evaluating measurement data – mainly designed for electroluminescence test bench.

---

## Developer Guide: Extending EL-Workbench

This guide provides a starting point for extending the platform with new devices, routines, or logic modules – useful for research, experiments, or academic projects.

---

### Architecture: The SharedState Concept with APIs

The SharedState object remains at the core of our system, but its role has evolved. It no longer serves for direct data access or function registration. Instead, it acts as a central distributor for API instances.

#### This means:

- **Centralized Access:** For specific data domains (e.g., profiles, device data) or complex device controls, we provide dedicated API classes (e.g., `ProfileApi`, `SmuApi`).
- **Encapsulation:** Tabs (UI modules) are responsible for display and interaction. Data ownership and persistence stay in the tabs, but communication goes through APIs.
- **Volatile Data:** Highly dynamic, temporary measurement data (e.g., wavelengths or intensities) may still be directly stored in SharedState attributes, if used read-only by other tabs.

---

### Create a Custom Module (4 Steps)

#### 1. Create a Python file

Place a new file in `tabs/`, e.g. `my_analysis_tab.py`.

---

#### 2. Write the class

```python
# /tabs/my_analysis_tab.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
import numpy as np

class MyAnalysisTab(QWidget):
    def __init__(self, shared_data):
        super().__init__()
        self.shared_data = shared_data
        self.profile_api = shared_data.profile_api
        self.smu_api = shared_data.smu_api
        self.current_wavelengths = shared_data.wavelengths 
        self.current_intensities = shared_data.intensities
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        info_label = QLabel("This is my new analysis module.")
        my_button = QPushButton("Start Analysis")
        my_button.clicked.connect(self.perform_analysis)
        
        layout.addWidget(info_label)
        layout.addWidget(my_button)
    
    def perform_analysis(self):
        print("Performing analysis…")
```

---

#### 3. Access shared resources via APIs

**Example: Spectrum peak**

```python
def find_spectrum_peak(self):
    if self.shared_data.wavelengths is not None and self.shared_data.intensities.size > 0:
        intensities = self.shared_data.intensities
        wavelengths = self.shared_data.wavelengths
        peak_index = np.argmax(intensities)
        print(f"Peak found at {wavelengths[peak_index]:.2f} nm.")
    else:
        print("No spectrometer data available.")
```

**Example: SMU remote control**

```python
def remote_control_smu(self):
    if self.smu_api:
        print("Controlling SMU to apply 0.5 V...")
        result = self.smu_api.apply_and_measure(
            channel='a',
            is_voltage_source=True,
            level=0.5,
            limit=0.01
        )
        if result:
            current, voltage = result
            print(f"SMU measured: {voltage:.4f} V, {current:.4e} A")
        else:
            print("SMU operation failed or no data returned.")
    else:
        print("SMU API not available.")
```

**Example: Retrieve profile**

```python
def retrieve_profile_info(self):
    if self.profile_api:
        active_profile = self.profile_api.get_active_profile()
        if active_profile:
            print(f"Active Profile: {active_profile.get('name', 'Unknown')} (ID: {active_profile.get('id', 'N/A')})")
        else:
            print("No active profile loaded.")
    else:
        print("Profile API not available.")
```

---

#### 4. Register the module (`main.py`)

```python
from tabs.my_analysis_tab import MyAnalysisTab

# Inside load_modules()
self.shared_data.profile_api = ProfileApi(...)
self.shared_data.smu_api = SmuApi(...)

my_tab = MyAnalysisTab(self.shared_data)
self.tabs.addTab(my_tab, "My Analysis")
```

---

### Code Organization

| Directory      | Contents                                             |
|----------------|------------------------------------------------------|
| `main.py`      | Application entry point                              |
| `tabs/`        | UI modules (`QWidget` subclasses)                    |
| `api/`         | API classes for data access and control              |
| `data/`        | JSON-based persistent data                           |
| `devices/`     | Device-specific drivers or wrappers                  |
| `styles/`      | .qss stylesheet files                                |
| `other/`       | Helper dialogs and utilities                         |

---

### Data Handling and Persistence

- JSON format for all persistent data
- Objects should have `id` and `name`
- Use `.copy()` to avoid modifying internal states
- Volatile data is allowed via `SharedState` directly

---

### Error Handling and Feedback

- Use `try-except` blocks around critical code
- Feedback via `QMessageBox` or status bar
- APIs should return status/errors, not show dialogs

---

### Documentation

- `README.md` is always up-to-date
- All classes/functions should have meaningful docstrings
- Comments should explain **why**, not just **what**

