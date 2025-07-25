1. Zentraler Datenzugriff: APIs statt direkter SharedState-Attribute
Der direkte Zugriff auf individuelle Attribute des SharedState-Objekts für spezifische Datenbereiche wird zugunsten von dedizierten API-Klassen abgelöst.

Regel 1.1: Daten-APIs als primäre Schnittstelle. Für klar definierte Datenbereiche (z.B. Profile, Gerätedaten, Messdaten) müssen eigene API-Klassen erstellt werden (z.B. ProfileApi, MeasurementApi, DeviceControlApi). Diese APIs sind die einzige empfohlene Schnittstelle für andere Programmteile, um auf die zugehörigen Daten zuzugreifen oder diese zu manipulieren.

Regel 1.2: Kapselung des SharedState. Die API-Klassen erhalten in ihrem Konstruktor das SharedState-Objekt (um auf aktuelle Zustände zuzugreifen) und, falls notwendig, Referenzen zu den "besitzenden" Tabs (z.B. ProfileApi benötigt ProfileTab für Speicheroperationen). API-Klassen sollten die SharedState-Attribute nur lesen und indirekt über die Methoden der "besitzenden" Tabs aktualisieren.

Regel 1.3: Getter und Setter in APIs. API-Klassen sollen für jedes zugängliche Attribut klare Getter-Methoden (get_attribute_name()) und, falls Daten persistiert oder geändert werden müssen, Setter-Methoden (set_attribute_name(value)) bereitstellen. Wenn ein Setter eine Änderung in einer Datei speichern muss, ist die Logik dafür im "besitzenden" Tab zu implementieren, und die API ruft diese Methode auf.

Regel 1.4: SharedState als Transportmechanismus für API-Instanzen. Das SharedState-Objekt in main.py wird weiterhin existieren, aber primär dazu dienen, die Instanzen der API-Klassen (und ggf. Gerätesteuerungs-Objekte, die keine vollständige API-Klasse rechtfertigen) zu halten und an alle Tabs zu verteilen.

Ausnahme für "flüchtige" Daten: Für sehr dynamische, nicht-persistente oder temporäre Messdaten, die von einem Tab erzeugt und von anderen Tabs nur gelesen werden, kann SharedState weiterhin direkte Attribute (shared_data.wavelengths, shared_data.intensities) als Puffer nutzen. Diese Attribute sollten jedoch stets von den produzierenden Tabs aktualisiert und von den konsumierenden Tabs nur gelesen werden.

Regel 1.5: Einheitliche Benennung.

API-Dateien im api/ Verzeichnis: [Bereich]_api.py (z.B. profile_api.py, smu_api.py).

API-Klassen: [Bereich]Api (z.B. ProfileApi, SmuApi).

2. Modulare Tab-Struktur und Verantwortlichkeiten
Jeder Tab ist eine eigenständige Einheit mit klar definierten Verantwortlichkeiten.

Regel 2.1: Kapselung der UI-Logik. Jeder Tab ist von QWidget abgeleitet und für seine eigene Benutzeroberfläche und die direkte Interaktion mit dieser UI verantwortlich.

Regel 2.2: Datenbesitz und Persistenz. Ein Tab, der Daten generiert oder verwaltet (z.B. ProfileTab für Profile, ein zukünftiger ExperimentTab für Experimente), ist für die Persistierung dieser Daten (Speichern/Laden in Dateien) verantwortlich. Die API-Klasse für diesen Bereich delegiert an die Speichermethoden des Tabs.

Regel 2.3: Interaktion über APIs. Tabs interagieren untereinander ausschließlich über die bereitgestellten API-Instanzen oder über die direkten, flüchtigen SharedState-Attribute (gemäß Regel 1.4). Direkte Aufrufe von Methoden eines anderen Tabs sind zu vermeiden, um Kopplung zu reduzieren.

Regel 2.4: Geräte-Instanzen und Steuerung.

Low-Level-Treiber (z.B. Keithley2602-Objekt für SMU) werden in einem zentralen Ort (z.B. einem device_manager.py oder direkt im SharedState) instanziiert und im SharedState gehalten.

Für komplexe Gerätesteuerungen sollte eine eigene API-Klasse (SmuApi, SpectrometerApi) erstellt werden, die diese Low-Level-Treiber kapselt und High-Level-Methoden bereitstellt (z.B. smu_api.apply_and_measure(...)). Diese API-Klasse wird im SharedState gespeichert und an andere Tabs weitergegeben.

3. Konsistente Datenhaltung
Regel 3.1: JSON für persistente Daten. Persistente Konfigurations- und Profildaten werden im JSON-Format gespeichert.

Regel 3.2: Standardattribute. Jedes persistente Datenobjekt (Profil, Gerät) sollte ein id-Feld (UUID) und ein name-Feld enthalten.

Regel 3.3: Daten-Kopien für Lesezugriffe. Wenn API-Methoden Daten-Dictionaries zurückgeben, sollten dies Kopien sein (.copy()), um unbeabsichtigte direkte Manipulationen der internen Zustände zu verhindern, die nicht persistent gespeichert werden.

4. Code-Organisation
Regel 4.1: Logische Verzeichnisstruktur.

main.py: Startpunkt, Hauptfenster, Instanziierung von SharedState und allen Tabs/APIs.

tabs/: Enthält alle UI-Module (Ableitungen von QWidget).

api/: Enthält alle API-Klassen für Datenzugriff und Gerätesteuerung.

data/: Für persistente Datendateien (Profile-JSONs, etc.).

other/: Hilfsdialoge (device_dialog.py), Utility-Funktionen, die keine eigene Top-Level-Kategorie verdienen.

styles/: Für UI-Styling.

devices/: Falls gerätespezifische Treiber/Wrapper-Klassen existieren, die von den SmuTab oder SpectrumTab instanziiert und im SharedState gehalten werden.

Regel 4.2: Klare Imports. Imports sollten spezifisch sein (from module.submodule import ClassName statt import module). Relative Imports innerhalb von Paketen (from . import submodule) sind zu bevorzugen, wenn anwendbar.

5. Fehlerbehandlung und Benutzerfeedback
Regel 5.1: Robuste Fehlerbehandlung. Kritische Operationen (Dateizugriffe, Gerätekommunikation) müssen von try-except-Blöcken umgeben sein.

Regel 5.2: Benutzerfeedback. Fehler, Warnungen und wichtige Statusmeldungen sollten dem Benutzer über QMessageBox oder eine Statusleiste klar kommuniziert werden. Bei API-Aufrufen ist es oft sinnvoll, dass die API selbst keine Dialoge anzeigt, sondern einen Status (True/False) oder eine Fehlermeldung zurückgibt, die dann vom aufrufenden UI-Tab verarbeitet wird.

6. Dokumentation
Regel 6.1: README.md Aktualisierung. Das Haupt-README muss die aktuelle Architektur und die neuen Design-Regeln widerspiegeln, insbesondere die Rolle der APIs.

Regel 6.2: Docstrings. Alle Module, Klassen, Methoden und komplexeren Funktionen müssen aussagekräftige Docstrings enthalten, die deren Zweck, Parameter, Rückgabewerte und Ausnahmen beschreiben.

Regel 6.3: In-Code-Kommentare. Kommentare sollen komplexe Logik erklären, nicht offensichtliche Entscheidungen begründen und "Warum" statt nur "Was" erklären.