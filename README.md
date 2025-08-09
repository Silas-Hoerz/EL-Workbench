# EL-Workbench

<<<<<<< HEAD
![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.12.5-blue)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green)
=======
![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)
![Lizenz](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.12.5-blue)
>>>>>>> 3ea7afd (updating README.md)

**Modulare Python-Plattform zur Ansteuerung von Laborgeräten und zur Auswertung von Messdaten – hauptsächlich für Elektrolumineszenz-Messplatz entwickelt.**

---

## Deutsche Version

### Problemstellung

EL-Workbench löst das Problem der **fragmentierten Laborgerätesteuerung** in Forschungsumgebungen. Anstatt separate Software-Tools für verschiedene Instrumente zu verwenden, haben Forscher oft Schwierigkeiten mit:

<<<<<<< HEAD
- **Unverbundenen Arbeitsabläufen** zwischen Messung und Analyse
- **Inkonsistenten Datenformaten** zwischen verschiedenen Geräten
- **Fehlender Benutzerprofilverwaltung** für gemeinsam genutzte Laborgeräte
- **Steilen Lernkurven** für Studenten und neue Forscher
- **Schwierigkeiten bei der Funktionserweiterung** für spezifische Forschungsanforderungen
=======
## Architektur: Das `SharedState`-Konzept mit APIs
>>>>>>> 3ea7afd (updating README.md)

**EL-Workbench löst diese Probleme durch:**
- Einheitliche Steuerungsschnittstelle für mehrere Laborinstrumente
- Zentralisierte Datenverwaltung mit konsistenten Formaten
- Benutzerprofil-System für personalisierte Konfigurationen
- Studentenfreundliche Architektur mit klaren Erweiterungsmustern
- Modulares Design für einfache Hinzufügung neuer Funktionalität

<<<<<<< HEAD
### Installation

#### Voraussetzungen

- **Python 3.12.5** oder höher
- **PyQt6** für die grafische Benutzeroberfläche
- **NumPy** für numerische Berechnungen
- **Matplotlib** für Datenvisualisierung
- **Seabreeze** für Ocean Optics Spektrometer-Steuerung
=======
### Das bedeutet:

- **Zentraler Zugriff:** Für spezifische Datenbereiche (z. B. Profile, Gerätedaten) oder komplexe Gerätesteuerungen stellen wir **dedizierte API-Klassen** bereit (z. B. `ProfileApi`, `SmuApi`). Diese APIs sind der primäre Weg, um auf Daten zuzugreifen oder Geräte zu steuern.
- **Kapselung:** Die **Tabs** (Benutzeroberflächen-Module) sind für die Anzeige und Interaktion mit der UI zuständig. Datenhaltung und Speicherung übernehmen sie weiterhin selbst, nutzen jedoch die APIs zur Kommunikation.
- **Flüchtige Daten:** Für sehr dynamische Messdaten (z. B. aktuelle Wellenlängen/Intensitäten eines Spektrums), die temporär von einem Tab erzeugt und von anderen gelesen werden, darf `SharedState` weiterhin Attribute direkt bereitstellen.

Das Ergebnis ist ein noch klarer strukturiertes, modular erweiterbares System mit **klar definierten Schnittstellen (APIs)**.
>>>>>>> 3ea7afd (updating README.md)

#### Schnelle Einrichtung

<<<<<<< HEAD
```bash
# Repository klonen
git clone https://github.com/your-username/el-workbench.git
cd el-workbench

# Abhängigkeiten installieren
pip install -r requirements.txt

# Anwendung starten
python main.py
```

#### Hardware-Anforderungen

- **Ocean Optics Spektrometer** (NIRQUEST Serie empfohlen)
- **Keithley 26xx Serie SMU** für elektrische Messungen
- **USB-Verbindungen** für Gerätekommunikation

### Verwendung
=======
## Neues Modul in 4 Schritten

### 1. Modul-Datei anlegen

Im Verzeichnis `tabs/` eine neue Python-Datei mit sinnvollem Namen erstellen, z. B. `meine_analyse_tab.py`.

---

### 2. Modul-Klasse schreiben

Jedes Modul ist eine `QWidget`-Klasse. Der `SharedState` wird im Konstruktor übergeben – primär zum Zugriff auf APIs:
>>>>>>> 3ea7afd (updating README.md)

#### Erste Schritte

1. **Anwendung starten**: `python main.py` ausführen
2. **Profil erstellen**: "Profile"-Tab verwenden um Benutzerprofil einzurichten
3. **Geräte konfigurieren**: Messgeräte mit ihren Spezifikationen hinzufügen
4. **Hardware verbinden**: Gerätespezifische Tabs verwenden um Verbindungen herzustellen
5. **Messungen starten**: Daten mit Spektrometer- und SMU-Tabs erfassen
6. **Ergebnisse analysieren**: Analyse-Tabs verwenden oder eigene erstellen

#### Kern-Arbeitsablauf

```
Profil-Setup → Gerätekonfiguration → Hardware-Verbindung → Datenerfassung → Analyse
```

#### Hauptfunktionen

- **Profilverwaltung**: Benutzerspezifische Einstellungen und Gerätekonfigurationen speichern
- **Echtzeit-Messung**: Live-Datenerfassung von verbundenen Instrumenten
- **Datenanalyse**: Eingebaute Analyse-Tools mit erweiterbarem Framework
- **Export-Funktionen**: Messungen in Standardformaten speichern
- **Logging-System**: Umfassende Status-Verfolgung und Fehlerberichterstattung

### Erweiterbarkeit für Studenten

EL-Workbench ist speziell darauf ausgelegt, **studentenfreundlich** und **leicht erweiterbar** zu sein. Die Architektur folgt klaren Mustern, die es Studenten und Forschern ermöglichen, neue Funktionalität ohne tiefe Programmierkenntnisse hinzuzufügen.

#### Architektur-Philosophie

Die Software folgt einem **SharedData-zentrierten Design** mit diesen Kernprinzipien:

##### 1. **Einzige Quelle der Wahrheit (SharedData)**
```python
# Alle geteilten Daten fließen durch ein zentrales Objekt
self.shared_data.current_profile      # Aktives Benutzerprofil
self.shared_data.current_device       # Ausgewähltes Messgerät
self.shared_data.current_wavelengths  # Aktuelle Spektrumdaten
self.shared_data.smu_device          # Hardware-Geräteinstanzen
```

##### 2. **Modulare Tab-Architektur**
- Jede Hauptfunktion lebt in ihrem eigenen **Tab** (separate Datei)
- Tabs kommunizieren nur über **SharedData**
- Neue Funktionen = neue Tabs (einfach zu verstehen und zu implementieren)

<<<<<<< HEAD
##### 3. **Klarer Datenfluss**
```
Benutzereingabe → Tab-Logik → SharedData → Andere Tabs → Anzeige/Analyse
```

#### Eigene Funktionalität hinzufügen

##### Schritt 1: Vorlage kopieren
```bash
cp tabs/example_tab.py tabs/my_analysis_tab.py
```
=======
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
>>>>>>> 3ea7afd (updating README.md)

##### Schritt 2: Tab anpassen
```python
class MyAnalysisTab(QWidget):
    def __init__(self, shared_data):
        super().__init__()
<<<<<<< HEAD
        self.shared_data = shared_data  # Ihr Zugang zu allen Daten!
        self.init_ui()
    
    def my_analysis_function(self):
        # Auf aktuelle Messdaten zugreifen
        wavelengths = self.shared_data.current_wavelengths
        intensities = self.shared_data.current_intensities
        
        # Auf aktuelle Geräteinformationen zugreifen
        device = self.shared_data.current_device
        
        # Ihr Analyse-Code hier...
        
        # Ergebnisse melden
        self.shared_data.info_manager.status(
            self.shared_data.info_manager.INFO,
            "Analyse erfolgreich abgeschlossen!"
        )
```

##### Schritt 3: Tab registrieren
Zwei Zeilen zu `main.py` in der `load_modules()` Methode hinzufügen:
```python
from tabs.my_analysis_tab import MyAnalysisTab
self.tabs.addTab(MyAnalysisTab(self.shared_data), "Meine Analyse")
```

#### Studenten-Lernpfad

##### Anfänger-Level
1. **Beispiel-Tab erkunden** (`example_tab.py`) - umfassende Demonstrationen
2. **Bestehende Analyse modifizieren** - Berechnungen ändern, neue Metriken hinzufügen
3. **Einfache UI-Elemente erstellen** - Buttons, Labels, Textanzeigen

##### Fortgeschrittenen-Level
1. **Benutzerdefinierte Analyse-Tabs erstellen** - forschungsspezifische Algorithmen implementieren
2. **Datenexport-Funktionen hinzufügen** - Ergebnisse in benutzerdefinierten Formaten speichern
3. **Messprotokolle erstellen** - automatisierte Messsequenzen

##### Experten-Level
1. **Neue Hardware integrieren** - Unterstützung für zusätzliche Instrumente hinzufügen
2. **API-Erweiterungen entwickeln** - neue API-Klassen für komplexe Operationen erstellen
3. **Erweiterte UI-Funktionen implementieren** - Echtzeit-Plotting, interaktive Steuerungen

#### Wichtige Design-Muster für Studenten

##### 1. **Zugriff auf geteilte Daten**
```python
# Immer prüfen ob Daten existieren bevor sie verwendet werden
if self.shared_data.current_wavelengths.size > 0:
    # Sicher die Daten zu verwenden
    wavelengths = self.shared_data.current_wavelengths
```

##### 2. **Fehlerbehandlung**
```python
try:
    # Ihr Code hier
    result = perform_analysis()
    self.shared_data.info_manager.status(
        self.shared_data.info_manager.INFO,
        "Erfolgsmeldung"
    )
except Exception as e:
    self.shared_data.info_manager.status(
        self.shared_data.info_manager.ERROR,
        f"Fehler: {str(e)}"
    )
```

##### 3. **UI-Updates**
```python
# Timer für periodische Updates verwenden
self.update_timer = QTimer()
self.update_timer.timeout.connect(self.update_display)
self.update_timer.start(1000)  # Jede Sekunde aktualisieren
```

#### Entwicklungsrichtlinien

##### Dateistruktur
```
el-workbench/
├── main.py              # Anwendungs-Einstiegspunkt
├── tabs/                # Ihre neue Funktionalität kommt hierhin!
│   ├── example_tab.py   # Vorlage und Beispiel
│   ├── profile_tab.py   # Benutzerprofilverwaltung
│   ├── spectrum_tab.py  # Spektrometer-Steuerung
│   └── your_tab.py      # Ihr neuer Tab hier
├── data/profiles/       # Benutzerprofil-Speicherung
├── styles/              # UI-Themes
└── other/               # Hilfsprogramm-Module
```

##### Namenskonventionen
- **Dateien**: `snake_case_tab.py`
- **Klassen**: `PascalCaseTab`
- **Methoden**: `snake_case_method()`
- **SharedData Attribute**: `current_something`, `device_name_device`

##### Dokumentationsstandards
- **Immer Docstrings einschließen** für Klassen und Methoden
- **Komplexe Logik kommentieren** - "warum" erklären, nicht nur "was"
- **Aussagekräftige Variablennamen verwenden** - `peak_wavelength` nicht `pw`
- **Header-Format befolgen** wie in bestehenden Dateien gezeigt

---

## English Version

### Problem Solved

EL-Workbench addresses the challenge of **fragmented laboratory equipment control** in research environments. Instead of using separate software tools for different instruments, researchers often struggle with:

- **Disconnected workflows** between measurement and analysis
- **Inconsistent data formats** across different devices
- **Lack of user profile management** for shared laboratory equipment
- **Steep learning curves** for students and new researchers
- **Difficulty extending functionality** for specific research needs

**EL-Workbench solves these problems by providing:**
- Unified control interface for multiple laboratory instruments
- Centralized data management with consistent formats
- User profile system for personalized configurations
- Student-friendly architecture with clear extension patterns
- Modular design allowing easy addition of new functionality

### Installation

#### Prerequisites

- **Python 3.12.5** or higher
- **PyQt6** for the graphical interface
- **NumPy** for numerical computations
- **Matplotlib** for data visualization
- **Seabreeze** for Ocean Optics spectrometer control

#### Quick Setup

```bash
# Clone the repository
git clone https://github.com/your-username/el-workbench.git
cd el-workbench

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

#### Hardware Requirements

- **Ocean Optics Spectrometer** (NIRQUEST series recommended)
- **Keithley 26xx Series SMU** for electrical measurements
- **USB connections** for device communication

### Usage

#### Getting Started

1. **Launch the application**: Run `python main.py`
2. **Create a profile**: Use the "Profile" tab to set up your user profile
3. **Configure devices**: Add your measurement devices with their specifications
4. **Connect hardware**: Use device-specific tabs to establish connections
5. **Start measuring**: Acquire data using the Spectrometer and SMU tabs
6. **Analyze results**: Use analysis tabs or create your own

#### Core Workflow

```
Profile Setup → Device Configuration → Hardware Connection → Data Acquisition → Analysis
```

#### Key Features

- **Profile Management**: Store user-specific settings and device configurations
- **Real-time Measurement**: Live data acquisition from connected instruments
- **Data Analysis**: Built-in analysis tools with extensible framework
- **Export Capabilities**: Save measurements in standard formats
- **Logging System**: Comprehensive status tracking and error reporting

### Extensibility for Students

EL-Workbench is specifically designed to be **student-friendly** and **easily extensible**. The architecture follows clear patterns that allow students and researchers to add new functionality without deep programming knowledge.

#### Architecture Philosophy

The software follows a **SharedData-centric design** with these core principles:

##### 1. **Single Source of Truth (SharedData)**
```python
# All shared data flows through one central object
self.shared_data.current_profile      # Active user profile
self.shared_data.current_device       # Selected measurement device
self.shared_data.current_wavelengths  # Latest spectrum data
self.shared_data.smu_device          # Hardware device instances
```

##### 2. **Modular Tab Architecture**
- Each major function lives in its own **tab** (separate file)
- Tabs communicate only through **SharedData**
- New features = new tabs (simple to understand and implement)

##### 3. **Clear Data Flow**
```
User Input → Tab Logic → SharedData → Other Tabs → Display/Analysis
```

#### Adding Your Own Functionality

##### Step 1: Copy the Template
```bash
cp tabs/example_tab.py tabs/my_analysis_tab.py
```

##### Step 2: Customize Your Tab
```python
class MyAnalysisTab(QWidget):
    def __init__(self, shared_data):
        super().__init__()
        self.shared_data = shared_data  # Your gateway to all data!
        self.init_ui()
    
    def my_analysis_function(self):
        # Access current measurement data
        wavelengths = self.shared_data.current_wavelengths
        intensities = self.shared_data.current_intensities
        
        # Access current device info
        device = self.shared_data.current_device
        
        # Your analysis code here...
        
        # Report results
        self.shared_data.info_manager.status(
            self.shared_data.info_manager.INFO,
            "Analysis completed successfully!"
        )
```

##### Step 3: Register Your Tab
Add two lines to `main.py` in the `load_modules()` method:
```python
from tabs.my_analysis_tab import MyAnalysisTab
self.tabs.addTab(MyAnalysisTab(self.shared_data), "My Analysis")
```

#### Student Learning Path

##### Beginner Level
1. **Explore the Example Tab** (`example_tab.py`) - comprehensive demonstrations
2. **Modify existing analysis** - change calculations, add new metrics
3. **Create simple UI elements** - buttons, labels, text displays

##### Intermediate Level
1. **Build custom analysis tabs** - implement your research-specific algorithms
2. **Add data export features** - save results in custom formats
3. **Create measurement protocols** - automated measurement sequences

##### Advanced Level
1. **Integrate new hardware** - add support for additional instruments
2. **Develop API extensions** - create new API classes for complex operations
3. **Implement advanced UI features** - real-time plotting, interactive controls

#### Key Design Patterns for Students

##### 1. **Accessing Shared Data**
```python
# Always check if data exists before using it
if self.shared_data.current_wavelengths.size > 0:
    # Safe to use the data
    wavelengths = self.shared_data.current_wavelengths
```

##### 2. **Error Handling**
```python
try:
    # Your code here
    result = perform_analysis()
    self.shared_data.info_manager.status(
        self.shared_data.info_manager.INFO,
        "Success message"
    )
except Exception as e:
    self.shared_data.info_manager.status(
        self.shared_data.info_manager.ERROR,
        f"Error: {str(e)}"
    )
```

##### 3. **UI Updates**
```python
# Use timers for periodic updates
self.update_timer = QTimer()
self.update_timer.timeout.connect(self.update_display)
self.update_timer.start(1000)  # Update every second
```

#### Development Guidelines

##### File Structure
```
el-workbench/
├── main.py              # Application entry point
├── tabs/                # Your new functionality goes here!
│   ├── example_tab.py   # Template and example
│   ├── profile_tab.py   # User profile management
│   ├── spectrum_tab.py  # Spectrometer control
│   └── your_tab.py      # Your new tab here
├── data/profiles/       # User profile storage
├── styles/              # UI themes
└── other/               # Utility modules
```

##### Naming Conventions
- **Files**: `snake_case_tab.py`
- **Classes**: `PascalCaseTab`
- **Methods**: `snake_case_method()`
- **SharedData attributes**: `current_something`, `device_name_device`

##### Documentation Standards
- **Always include docstrings** for classes and methods
- **Comment complex logic** - explain "why", not just "what"
- **Use meaningful variable names** - `peak_wavelength` not `pw`
- **Follow the header format** shown in existing files

---

## Technical Architecture

### Core Components

| Component | Purpose | Student Interaction |
|-----------|---------|-------------------|
| **SharedData** | Central data hub | Primary interface for all data access |
| **Tabs** | Functional modules | Where you add new features |
| **InfoManager** | Logging system | Report status and errors |

### Data Flow

```
Hardware Devices → Device Tabs → SharedData → Analysis Tabs → Results
                                      ↓
                                 Profile Data
                                 User Settings
```

### Extension Points

- **New Tabs**: Add functionality (recommended for students)
- **Device Drivers**: Support for additional hardware
- **Analysis Modules**: Custom algorithms and calculations

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Institute for Semiconductor Technology, University of Stuttgart**
- **Ocean Optics** for spectrometer integration support
- **Keithley/Tektronix** for SMU documentation and examples
- **PyQt6 Community** for excellent GUI framework

---

## Support

For questions, issues, or contributions:
- **Create an issue** on GitHub
- **Check the documentation** in `design_rules.md`
- **Study the example tab** for implementation patterns
=======
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

>>>>>>> 3ea7afd (updating README.md)
