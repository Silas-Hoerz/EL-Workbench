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

### Architektur: Das `SharedState`-Konzept mit APIs

Das Herzstück unseres Systems ist weiterhin das **`SharedState`-Objekt**. Es dient nun aber nicht mehr für den direkten Datenzugriff oder die Registrierung von Funktionen. Stattdessen fungiert es als **zentraler Verteiler für API-Instanzen**.

Das bedeutet:

* **Zentraler Zugriff:** Für spezifische Datenbereiche (z.B. Profile, Gerätedaten) oder komplexe Gerätesteuerungen stellen wir **dedizierte API-Klassen** bereit (z.B. `ProfileApi`, `SmuApi`). Diese APIs sind der primäre Weg, um auf Daten zuzugreifen oder Geräte zu steuern.
* **Kapselung:** Die **Tabs** (Ihre Benutzeroberflächen-Module) sind für die Anzeige und Interaktion mit der UI zuständig. Datenhaltung und Speicherung übernehmen sie weiterhin selbst. Sie nutzen die APIs, um mit den Daten zu interagieren und andere Module anzusprechen.
* **Flüchtige Daten:** Für sehr dynamische, temporäre Messdaten (z.B. aktuelle Wellenlängen oder Intensitäten eines Spektrums), die von einem Tab erzeugt und von anderen Tabs nur gelesen werden, kann das `SharedState` weiterhin direkte Attribute nutzen. Diese Attribute sollten jedoch stets von den produzierenden Tabs aktualisiert und von den konsumierenden Tabs nur gelesen werden.

Das Ergebnis ist ein noch klarer strukturiertes, modular erweiterbares System, das **Kommunikation über klar definierte Schnittstellen (APIs)** fördert.

---

### Neues Modul in 4 Schritten

So lässt sich ein eigener Tab in wenigen Schritten ergänzen und korrekt in die neue Architektur einbinden.

#### 1. Modul-Datei anlegen

Im Verzeichnis `tabs/` eine neue Python-Datei anlegen – mit einem sinnvollen Namen, etwa `meine_analyse_tab.py`.

#### 2. Modul-Klasse schreiben

Jedes Modul ist eine Klasse, die von `QWidget` erbt. Die Grundstruktur ist immer gleich. Der `SharedState` wird im Konstruktor übergeben, aber primär dafür genutzt, um auf die **API-Instanzen** zuzugreifen:

```python
# /tabs/meine_analyse_tab.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
import numpy as np

class MeineAnalyseTab(QWidget):
    def __init__(self, shared_data):
        super().__init__()
        self.shared_data = shared_data
        # Hier greifen Sie auf die API-Instanzen zu, z.B.:
        self.profile_api = shared_data.profile_api
        self.smu_api = shared_data.smu_api
        # Optional: Direkter Zugriff auf flüchtige Daten
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
3. Zugriff auf gemeinsame Ressourcen über APIs
Nutzen Sie die im SharedState gespeicherten API-Instanzen für den Datenzugriff und die Gerätesteuerung. Direkte Zugriffe auf Attribute anderer Tabs oder das SharedState für persistente Daten sind zu vermeiden (Ausnahme: flüchtige Messdaten).

Beispiel: Spektrum-Peak über shared_data.wavelengths und shared_data.intensities finden (flüchtige Daten)

Python

def finde_spektrum_peak(self):
    # Direkter Zugriff auf flüchtige Messdaten aus SharedState ist hier erlaubt
    if self.shared_data.wavelengths is not None and self.shared_data.intensities.size > 0:
        intensities = self.shared_data.intensities
        wavelengths = self.shared_data.wavelengths
        
        peak_index = np.argmax(intensities)
        print(f"Peak bei {wavelengths[peak_index]:.2f} nm gefunden.")
    else:
        print("Keine Spektrometer-Daten vorhanden.")
Beispiel: SMU fernsteuern über SmuApi

Python

def steuere_smu_fern(self):
    # Zugriff auf SMU-Funktionen über die dedizierte SMU-API
    if self.smu_api:
        print("SMU wird angesteuert (0.5 V)…")
        
        # Nutzen Sie die High-Level-Methode der SMU-API
        result = self.smu_api.apply_and_measure(
            channel='a',
            is_voltage_source=True,
            level=0.5,
            limit=0.01
        )
        
        if result:
            current, voltage = result
            print(f"Messwert: {voltage:.4f} V, {current:.4e} A")
        else:
            print("SMU-Operation fehlgeschlagen oder keine Daten zurückgegeben.")
    else:
        print("SMU-API nicht verfügbar.")
Beispiel: Profilinformationen über ProfileApi abrufen

Python

def lade_aktives_profil(self):
    # Zugriff auf Profil-Daten über die Profile-API
    if self.profile_api:
        active_profile = self.profile_api.get_active_profile()
        if active_profile:
            print(f"Aktives Profil: {active_profile.get('name', 'Unbekanntes Profil')} (ID: {active_profile.get('id', 'N/A')})")
        else:
            print("Kein aktives Profil geladen.")
    else:
        print("Profile-API nicht verfügbar.")
4. Modul registrieren (main.py)
Zum Schluss muss das neue Modul bekannt gemacht werden:

Import in main.py:

Python

from tabs.meine_analyse_tab import MeineAnalyseTab
In load_modules() einfügen:

Python

# Stellen Sie sicher, dass die benötigten APIs vor dem Tab instanziiert sind
# und dem SharedState hinzugefügt wurden, z.B.:
# self.shared_data.profile_api = ProfileApi(...)
# self.shared_data.smu_api = SmuApi(...)

mein_tab = MeineAnalyseTab(self.shared_data)
self.tabs.addTab(mein_tab, "Meine Analyse")
Fertig! Beim nächsten Start ist der neue Tab aktiv und vollständig ins System eingebunden.

Code-Organisation
Um die Übersichtlichkeit zu wahren, folgen wir einer klaren Verzeichnisstruktur:

main.py: Startpunkt der Anwendung, Initialisierung des Hauptfensters, des SharedState und aller Tabs/APIs.

tabs/: Enthält alle UI-Module, die von QWidget abgeleitet sind. Jede Datei repräsentiert einen Tab.

api/: Beherbergt alle API-Klassen für den Datenzugriff und die Gerätesteuerung. Dateinamen sollten dem Muster [bereich]_api.py folgen (z.B. profile_api.py, smu_api.py).

data/: Für persistente Datendateien, wie z.B. JSON-Profile.

other/: Hilfsdialoge und Utility-Funktionen, die keiner eigenen Top-Level-Kategorie bedürfen.

styles/: Für UI-Styling-Dateien (z.B. .qss).

devices/: Wenn gerätespezifische Treiber oder Wrapper-Klassen existieren, die von APIs oder Tabs instanziiert und ggf. im SharedState gehalten werden.

Datenhaltung und Persistenz
JSON-Format: Persistente Konfigurations- und Profildaten werden standardmäßig im JSON-Format gespeichert.

Standardattribute: Jedes persistente Datenobjekt (z.B. ein Profil) sollte id (UUID) und name Felder enthalten.

Datenkopien: Wenn API-Methoden Daten-Dictionaries zurückgeben, sollten dies Kopien (.copy()) sein, um unbeabsichtigte direkte Manipulationen der internen Zustände zu verhindern.

Fehlerbehandlung und Benutzerfeedback
Robuste Fehlerbehandlung: Kritische Operationen (Dateizugriffe, Gerätekommunikation) sollten stets von try-except-Blöcken umgeben sein.

Benutzerfeedback: Fehler, Warnungen und wichtige Statusmeldungen müssen dem Benutzer klar kommuniziert werden, bevorzugt über QMessageBox oder eine Statusleiste. APIs sollten in der Regel keinen direkten Dialog anzeigen, sondern einen Status (True/False) oder eine Fehlermeldung zurückgeben, die dann vom aufrufenden UI-Tab verarbeitet wird.

Dokumentation
Eine gute Dokumentation ist entscheidend:

README.md: Dieses Haupt-README wird regelmäßig aktualisiert, um die aktuelle Architektur und die Design-Prinzipien widerzuspiegeln.

Docstrings: Alle Module, Klassen, Methoden und komplexeren Funktionen müssen aussagekräftige Docstrings enthalten, die deren Zweck, Parameter, Rückgabewerte und Ausnahmen beschreiben.

In-Code-Kommentare: Kommentare sollen komplexe Logik erklären, nicht offensichtliche Entscheidungen begründen und "Warum" statt nur "Was" erklären.

EL-Workbench (English Version)
Modular Python platform for controlling lab equipment and evaluating measurement data – mainly designed for electroluminescence test bench.

Developer Guide: Extending EL-Workbench
This guide provides a starting point for extending the platform with new devices, routines, or logic modules – useful for research, experiments, or academic projects.

Architecture: The SharedState Concept with APIs
The SharedState object remains at the core of our system, but its role has evolved. It no longer serves for direct data access or function registration. Instead, it acts as a central distributor for API instances.

This means:

Centralized Access: For specific data domains (e.g., profiles, device data) or complex device controls, we provide dedicated API classes (e.g., ProfileApi, SmuApi). These APIs are the primary way to access data or control devices.

Encapsulation: The Tabs (your UI modules) are responsible for displaying and interacting with the user interface. They continue to handle data ownership and persistence. They use the APIs to interact with data and communicate with other modules.

Volatile Data: For highly dynamic, temporary measurement data (e.g., current wavelengths or intensities of a spectrum) produced by one tab and only read by others, SharedState can still use direct attributes. However, these attributes should always be updated by the producing tabs and only read by consuming tabs.

The result is an even more clearly structured, modularly extensible system that promotes communication through well-defined interfaces (APIs).

Create a Custom Module (4 Steps)
Add a new tab with minimal setup effort and integrate it correctly into the new architecture.

1. Create a Python file
Place a new file in tabs/, e.g. my_analysis_tab.py.

2. Write the class
Each module is a QWidget subclass. The basic structure remains the same. The SharedState is passed in the constructor, but primarily used to access the API instances:

Python

# /tabs/my_analysis_tab.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
import numpy as np

class MyAnalysisTab(QWidget):
    def __init__(self, shared_data):
        super().__init__()
        self.shared_data = shared_data
        # Access API instances here, e.g.:
        self.profile_api = shared_data.profile_api
        self.smu_api = shared_data.smu_api
        # Optional: Direct access to volatile data
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
3. Access shared resources via APIs
Use the API instances stored in SharedState for data access and device control. Direct access to attributes of other tabs or SharedState for persistent data should be avoided (exception: volatile measurement data).

Example: Finding the spectrum peak using shared_data.wavelengths and shared_data.intensities (volatile data)

Python

def find_spectrum_peak(self):
    # Direct access to volatile measurement data from SharedState is allowed here
    if self.shared_data.wavelengths is not None and self.shared_data.intensities.size > 0:
        intensities = self.shared_data.intensities
        wavelengths = self.shared_data.wavelengths
        
        peak_index = np.argmax(intensities)
        print(f"Peak found at {wavelengths[peak_index]:.2f} nm.")
    else:
        print("No spectrometer data available.")
Example: Remote control of the SMU via SmuApi

Python

def remote_control_smu(self):
    # Access SMU functions via the dedicated SMU API
    if self.smu_api:
        print("Controlling SMU to apply 0.5 V...")
        
        # Use the high-level method of the SMU API
        result = self.smu_api.apply_and_measure(
            channel='a',
            is_voltage_source=True,
            level=0.5,
            limit=0.01
        )
        
        if result:
            current, voltage = result
            print(f"SMU measured: {voltage:.4f} V, {current:.4e} A")
        else:
            print("SMU operation failed or no data returned.")
    else:
        print("SMU API not available.")
Example: Retrieving profile information via ProfileApi

Python

def load_active_profile(self):
    # Access profile data via the Profile API
    if self.profile_api:
        active_profile = self.profile_api.get_active_profile()
        if active_profile:
            print(f"Active Profile: {active_profile.get('name', 'Unknown Profile')} (ID: {active_profile.get('id', 'N/A')})")
        else:
            print("No active profile loaded.")
    else:
        print("Profile API not available.")
4. Register the module (main.py)
To activate the tab:

Import in main.py:

Python

from tabs.my_analysis_tab import MyAnalysisTab
Add it in load_modules():

Python

# Ensure that required APIs are instantiated before the tab
# and added to SharedState, e.g.:
# self.shared_data.profile_api = ProfileApi(...)
# self.shared_data.smu_api = SmuApi(...)

my_tab = MyAnalysisTab(self.shared_data)
self.tabs.addTab(my_tab, "My Analysis")
Done! After restarting, the new tab will show up and work out of the box.

Code Organization
To maintain clarity, we follow a clear directory structure:

main.py: Application entry point, initialization of the main window, SharedState, and all tabs/APIs.

tabs/: Contains all UI modules derived from QWidget. Each file represents a tab.

api/: Houses all API classes for data access and device control. Filenames should follow the pattern [area]_api.py (e.g., profile_api.py, smu_api.py).

data/: For persistent data files, such as JSON profiles.

other/: Helper dialogs and utility functions that do not warrant their own top-level category.

styles/: For UI styling files (e.g., .qss).

devices/: If device-specific drivers or wrapper classes exist, which are instantiated by APIs or tabs and potentially held in SharedState.

Data Handling and Persistence
JSON Format: Persistent configuration and profile data are by default stored in JSON format.

Standard Attributes: Every persistent data object (e.g., a profile) should include id (UUID) and name fields.

Data Copies: When API methods return data dictionaries, these should be copies (.copy()) to prevent unintended direct manipulation of internal states.

Error Handling and User Feedback
Robust Error Handling: Critical operations (file access, device communication) should always be enclosed in try-except blocks.

User Feedback: Errors, warnings, and important status messages must be clearly communicated to the user, preferably via QMessageBox or a status bar. APIs should generally not display direct dialogs but rather return a status (True/False) or an error message that is then processed by the calling UI tab.

Documentation
Good documentation is crucial:

README.md: This main README will be regularly updated to reflect the current architecture and design principles.

Docstrings: All modules, classes, methods, and more complex functions must include meaningful Docstrings describing their purpose, parameters, return values, and exceptions.

In-Code Comments: Comments should explain complex logic, justify non-obvious decisions, and explain "Why" rather than just "What".