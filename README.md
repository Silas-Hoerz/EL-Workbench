# EL-Workbench

![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)
![Lizenz](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)

**English version below**

Modulare Python-Plattform zur Ansteuerung von Laborgeräten und zur Auswertung von Messdaten – hauptsächlich für Elektrolumineszenz-Messplätze entwickelt.

---

## Entwickler-Doku: Das EL-Workbench erweitern

Diese Dokumentation richtet sich an alle, die das System mit eigenen Funktionen, Geräteanbindungen oder Analysemodulen ausbauen möchten – egal ob für Studienarbeiten, Forschung oder Laborexperimente.

### 🏛️ Architektur: Das `SharedState`-Konzept

Zentrales Element ist ein `SharedState`-Objekt – quasi die gemeinsame Daten- und Funktionsdrehscheibe. Es wird beim Start erzeugt und steht allen Modulen (Tabs) zur Verfügung.

Zwei Hauptaufgaben übernimmt dieses Objekt:

1.  **Daten teilen:** Erzeugt ein Modul Messdaten (z. B. der **Spektrometer-Tab**), landen diese im `SharedState`. Andere Module können sie dann live auslesen.
2.  **Funktionen teilen:** Module mit spezifischer Logik (z. B. der **SMU-Tab**) können Methoden im `SharedState` registrieren. Andere Tabs (z. B. **Sweep**) rufen sie bei Bedarf einfach auf – ohne die interne Logik kennen zu müssen.

Das Ergebnis: Ein klar strukturiertes, modular erweiterbares System im Stil von Producer/Consumer.

### 🚀 Neues Modul in 4 Schritten

So lässt sich ein eigener Tab in wenigen Schritten ergänzen.

#### 1. Modul-Datei anlegen

Im Verzeichnis `tabs/` eine neue Python-Datei anlegen – mit einem sinnvollen Namen, etwa `meine_analyse_tab.py`.

#### 2. Modul-Klasse schreiben

Jedes Modul ist eine Klasse, die von `QWidget` erbt. Die Grundstruktur ist immer gleich:

```python
# /tabs/meine_analyse_tab.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
import numpy as np

class MeineAnalyseTab(QWidget):
    def __init__(self, shared_data):
        super().__init__()
        self.shared_data = shared_data
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
````

#### 3. Zugriff auf gemeinsame Ressourcen

In der Klasse steht `self.shared_data` zur Verfügung – für Daten, Funktionen oder Statuswerte.

**Beispiel: Spektrum-Peak finden**

```python
def finde_spektrum_peak(self):
    if self.shared_data.spec and self.shared_data.intensities.size > 0:
        intensities = self.shared_data.intensities
        wavelengths = self.shared_data.wavelengths
        
        peak_index = np.argmax(intensities)
        print(f"Peak bei {wavelengths[peak_index]:.2f} nm gefunden.")
    else:
        print("Keine Spektrometer-Daten vorhanden.")
```

**Beispiel: SMU fernsteuern**

```python
def steuere_smu_fern(self):
    if self.shared_data.smu and callable(self.shared_data.smu_apply_and_measure):
        print("SMU wird angesteuert (0.5 V)…")
        
        result = self.shared_data.smu_apply_and_measure(
            channel='a',
            is_voltage_source=True,
            level=0.5,
            limit=0.01
        )
        
        if result:
            current, voltage = result
            print(f"Messwert: {voltage:.4f} V, {current:.4e} A")
    else:
        print("SMU nicht bereit oder Funktion nicht verfügbar.")
```

#### 4. Modul registrieren (`main.py`)

Zum Schluss muss das neue Modul bekannt gemacht werden:

1. **Import in `main.py`:**

   ```python
   from tabs.meine_analyse_tab import MeineAnalyseTab
   ```

2. **In `load_modules()` einfügen:**

   ```python
   mein_tab = MeineAnalyseTab(self.shared_data)
   self.tabs.addTab(mein_tab, "Meine Analyse")
   ```

Fertig! Beim nächsten Start ist der neue Tab aktiv und vollständig ins System eingebunden.

---

---

# EL-Workbench (English Version)

![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)

Modular Python platform for controlling lab equipment and evaluating measurement data – mainly designed for electroluminescence test benches.

---

## Developer Guide: Extending EL-Workbench

This guide provides a starting point for extending the platform with new devices, routines, or logic modules – useful for research, experiments, or academic projects.

### 🏛️ Architecture: The `SharedState` Concept

At the core of the system is a central `SharedState` object – a common data and function hub created once and passed to all modules.

It serves two key purposes:

1. **Sharing data:** Modules like the **Spectrometer Tab** can store their results in the `SharedState`, where others can read them live.
2. **Sharing functions:** Modules like the **SMU Tab** can register internal methods in the `SharedState`, so other modules (e.g., **Sweep**) can use them without knowing implementation details.

This approach follows a clean producer/consumer pattern and keeps the architecture highly modular.

### 🚀 Create a Custom Module (4 Steps)

Add a new tab with minimal setup effort:

#### 1. Create a Python file

Place a new file in `tabs/`, e.g. `my_analysis_tab.py`.

#### 2. Write the class

Each module is a `QWidget` subclass:

```python
# /tabs/my_analysis_tab.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
import numpy as np

class MyAnalysisTab(QWidget):
    def __init__(self, shared_data):
        super().__init__()
        self.shared_data = shared_data
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

#### 3. Access shared resources

`self.shared_data` provides access to everything needed.

**Example: Finding the spectrum peak**

```python
def find_spectrum_peak(self):
    if self.shared_data.spec and self.shared_data.intensities.size > 0:
        intensities = self.shared_data.intensities
        wavelengths = self.shared_data.wavelengths
        
        peak_index = np.argmax(intensities)
        print(f"Peak found at {wavelengths[peak_index]:.2f} nm.")
    else:
        print("No spectrometer data available.")
```

**Example: Remote control of the SMU**

```python
def remote_control_smu(self):
    if self.shared_data.smu and callable(self.shared_data.smu_apply_and_measure):
        print("Controlling SMU to apply 0.5 V...")
        
        result = self.shared_data.smu_apply_and_measure(
            channel='a',
            is_voltage_source=True,
            level=0.5,
            limit=0.01
        )
        
        if result:
            current, voltage = result
            print(f"SMU measured: {voltage:.4f} V, {current:.4e} A")
    else:
        print("SMU not ready or function unavailable.")
```

#### 4. Register the module (`main.py`)

To activate the tab:

1. **Import in `main.py`:**

   ```python
   from tabs.my_analysis_tab import MyAnalysisTab
   ```

2. **Add it in `load_modules()`:**

   ```python
   my_tab = MyAnalysisTab(self.shared_data)
   self.tabs.addTab(my_tab, "My Analysis")
   ```

Done! After restarting, the new tab will show up and work out of the box.
