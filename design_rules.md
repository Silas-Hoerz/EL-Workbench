# EL-Workbench Design-Regeln v1.1.0

## 1. Zentraler Datenzugriff über SharedData-Attribute und Methoden

Das SharedData-Objekt ist das zentrale Hub für den Austausch von Daten und Funktionen zwischen allen Modulen. Direkter Zugriff auf seine Attribute und Methoden ist die primäre Art der Interaktion.

**Regel 1.1: SharedData als primäre Schnittstelle.** Für alle Datenbereiche (z.B. Profile, Gerätedaten, Messdaten) und zur Steuerung von Geräten dient das SharedData-Objekt als einzige empfohlene Schnittstelle für alle Programmteile.

**Regel 1.2: Kapselung im SharedData.** Das SharedData-Objekt enthält direkt die Attribute für Daten (persistente wie flüchtige) und Referenzen auf Geräte-Objekte sowie Methoden zur Gerätesteuerung.

**Regel 1.3: Direkte Getter und Setter (wenn nötig).** Für Daten, die persistiert oder geändert werden müssen, können die "besitzenden" Tabs entsprechende Getter- und Setter-Methoden im SharedData registrieren oder das SharedData ruft direkt Methoden im Tab auf, wenn es Persistenzaufgaben delegiert. Alternativ können Methoden, die Daten manipulieren, direkt im SharedData implementiert werden, falls die Logik allgemein genug ist.

**Regel 1.4: SharedData als zentraler Datenspeicher.** Das SharedData-Objekt in main.py wird weiterhin existieren und ist dafür zuständig, alle gemeinsamen Daten, Geräteinstanzen und Funktionen zu halten und an alle Tabs zu verteilen.

**Ausnahme für "flüchtige" Daten:** Für sehr dynamische, nicht-persistente oder temporäre Messdaten, die von einem Tab erzeugt und von anderen Tabs nur gelesen werden, kann SharedData weiterhin direkte Attribute (z.B. shared_data.current_wavelengths, shared_data.current_intensities) als Puffer nutzen. Diese Attribute sollten jedoch stets von den produzierenden Tabs aktualisiert und von den konsumierenden Tabs nur gelesen werden.

**Regel 1.5: Einheitliche Benennung.**

- SharedData-Attribute für Daten: `shared_data.[bereich_datenname]` (z.B. `shared_data.current_profile`, `shared_data.current_wavelengths`)
- SharedData-Attribute für Geräteinstanzen: `shared_data.[gerätename]_device` (z.B. `shared_data.smu_device`, `shared_data.spectrometer_device`)
- SharedData-Methoden zur Steuerung: `shared_data.[gerätename]_[aktion]` (z.B. `shared_data.smu_apply_and_measure`)

## 2. Modulare Tab-Struktur und Verantwortlichkeiten

Jeder Tab ist eine eigenständige Einheit mit klar definierten Verantwortlichkeiten.

**Regel 2.1: Kapselung der UI-Logik.** Jeder Tab ist von QWidget abgeleitet und für seine eigene Benutzeroberfläche und die direkte Interaktion mit dieser UI verantwortlich.

**Regel 2.2: Datenbesitz und Persistenz.** Ein Tab, der Daten generiert oder verwaltet (z.B. ProfileTab für Profile, ein zukünftiger ExperimentTab für Experimente), ist für die Persistierung dieser Daten (Speichern/Laden in Dateien) verantwortlich. Das SharedData kann Methoden im Tab aufrufen, um solche Operationen auszuführen, oder der Tab greift direkt auf seine eigenen Daten zu, die dann in das SharedData geschrieben werden.

**Regel 2.3: Interaktion über SharedData.** Tabs interagieren untereinander ausschließlich über die direkten Attribute und Methoden des SharedData-Objekts. Direkte Aufrufe von Methoden eines anderen Tabs sind zu vermeiden, um Kopplung zu reduzieren.

**Regel 2.4: Geräte-Instanzen und Steuerung.**

- Low-Level-Treiber (z.B. Keithley2602-Objekt für SMU) werden an einem zentralen Ort (z.B. main.py) instanziiert und direkt als Attribute im SharedData gehalten (z.B. `self.shared_data.smu_device`)
- Für komplexere Gerätesteuerungen können High-Level-Methoden direkt im SharedData implementiert werden, die dann diese Low-Level-Treiber kapseln (z.B. `shared_data.smu_apply_and_measure(...)`). Diese Methoden werden dann von anderen Tabs aufgerufen.

## 3. Konsistente Datenhaltung

**Regel 3.1: JSON für persistente Daten.** Persistente Konfigurations- und Profildaten werden im JSON-Format gespeichert.

**Regel 3.2: Standardattribute.** Jedes persistente Datenobjekt (Profil, Gerät) sollte ein `id`-Feld (UUID) und ein `name`-Feld enthalten.

**Regel 3.3: Daten-Kopien für Lesezugriffe.** Wenn SharedData-Methoden Daten-Dictionaries zurückgeben, sollten dies Kopien sein (`.copy()`), um unbeabsichtigte direkte Manipulationen der internen Zustände zu verhindern, die nicht persistent gespeichert werden.

## 4. Code-Organisation

**Regel 4.1: Logische Verzeichnisstruktur.**

- `main.py`: Startpunkt, Hauptfenster, Instanziierung von SharedData und allen Tabs/Geräten
- `tabs/`: Enthält alle UI-Module (Ableitungen von QWidget)
- `data/`: Für persistente Datendateien (Profile-JSONs, etc.)
- `other/`: Hilfsdialoge (device_dialog.py), Utility-Funktionen, die keine eigene Top-Level-Kategorie verdienen
- `styles/`: Für UI-Styling
- `devices/`: Falls gerätespezifische Treiber/Wrapper-Klassen existieren, die direkt im SharedData instanziiert und gehalten werden

**Regel 4.2: Klare Imports.** Imports sollten spezifisch sein (`from module.submodule import ClassName` statt `import module`). Relative Imports innerhalb von Paketen (`from . import submodule`) sind zu bevorzugen, wenn anwendbar.

**Regel 4.3: Sprachkonventionen.**

- **UI-Text (Labels, Buttons, Fenstertitel, etc.):** Vollständig auf **Deutsch**
- **Code (Funktionsnamen, Variablennamen, Klassennamen, Dateinamen):** Vollständig auf **Englisch** (CamelCase für Klassen, snake_case für Funktionen/Variablen)
- **Code-Kommentare:** Vollständig auf **Deutsch**. Kommentare sollen prägnant und für Studenten verständlich sein.
- **Keine QGroupBox verwenden:** Stattdessen einfache QLabel als Überschriften für Bereiche verwenden

## 5. Fehlerbehandlung und Benutzerfeedback

**Regel 5.1: Robuste Fehlerbehandlung.** Kritische Operationen (Dateizugriffe, Gerätekommunikation) müssen von try-except-Blöcken umgeben sein.

**Regel 5.2: Benutzerfeedback.** Fehler, Warnungen und wichtige Statusmeldungen sollten dem Benutzer über QMessageBox oder eine Statusleiste klar kommuniziert werden. SharedData-Methoden sollten oft einen Status (True/False) oder eine Fehlermeldung zurückgeben, die dann vom aufrufenden UI-Tab verarbeitet wird.

**Regel 5.3: Zentralisiertes Logging.** Alle Status-, Warn- und Fehlermeldungen sollen über das InfoManager-System (`self.shared_data.info_manager.status()`) gemeldet werden.

## 6. Dokumentation

**Regel 6.1: README.md Aktualisierung.** Das Haupt-README muss die aktuelle Architektur und die neuen Design-Regeln widerspiegeln, insbesondere die zentrale Rolle des SharedData.

**Regel 6.2: Docstrings.** Alle Module, Klassen, Methoden und komplexeren Funktionen müssen aussagekräftige Docstrings enthalten, die deren Zweck, Parameter, Rückgabewerte und Ausnahmen beschreiben.

**Regel 6.3: In-Code-Kommentare.** Kommentare sollen komplexe Logik erklären, nicht offensichtliche Entscheidungen begründen und "Warum" statt nur "Was" erklären.

**Regel 6.4: Header-Konsistenz.** Alle Python-Dateien müssen dem standardisierten Header-Format folgen:

```python
# el-workbench/path/to/file.py
# -*- coding: utf-8 -*-
"""
============================================================================
 File:           file.py
 Author:         Team EL-Workbench
 Creation date:  YYYY-MM-DD
 Last modified:  YYYY-MM-DD
 Version:        1.1.0
============================================================================
 Description:
    [Kurze, klare Beschreibung des Dateizwecks auf Deutsch]
============================================================================
 Change Log:
 - YYYY-MM-DD: [Beschreibung der Änderungen auf Deutsch]
============================================================================
"""
```

## 7. Studentenfreundliche Entwicklung

**Regel 7.1: Einfache Erweiterbarkeit.** Neue Funktionalität soll primär durch das Hinzufügen neuer Tabs erfolgen. Das Muster ist klar definiert und in `example_tab.py` demonstriert.

**Regel 7.2: Klare Beispiele.** Der `example_tab.py` dient als umfassende Vorlage und Demonstration aller wichtigen Entwicklungsmuster.

**Regel 7.3: Konsistente Muster.** Alle Tabs folgen dem gleichen Grundmuster:
- Konstruktor nimmt `shared_data` Parameter
- `init_ui()` Methode für UI-Erstellung
- Fehlerbehandlung mit try-except
- Status-Meldungen über InfoManager
- Deutsche UI-Texte, englische Code-Namen, deutsche Kommentare

**Regel 7.4: Dokumentierte Integration.** Neue Tabs werden in `main.py` in der `load_modules()` Methode registriert. Der Prozess ist klar dokumentiert und mit Beispielen versehen.