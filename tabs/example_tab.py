# el-workbench/tabs/example_tab.py
# -*- coding: utf-8 -*-
"""
============================================================================
 File:           example_tab.py
 Author:         Team EL-Workbench
 Creation date:  2025-06-25
 Last modified:  2025-01-15
 Version:        1.1.0
============================================================================
 Description:
    Vorlage und Beispielmodul für neue EL-Workbench Tabs.
    Studenten können diese Datei als Ausgangspunkt für ihre eigenen
    Funktionen und Analysemodule verwenden.
============================================================================
 Change Log:
 - 2025-06-25: Erste Version erstellt. Anweisungen für EL-Workbench aktualisiert.
 - 2025-01-15: Als umfassendes Beispiel für v1.1.0 erweitert. Detaillierte
               Demonstrationen von SharedData-Nutzung, Logging und UI-Mustern hinzugefügt.
               Datei von beispiel_tab.py zu example_tab.py umbenannt.
============================================================================
"""

"""
================================================================================================
*** STUDENTEN-ANLEITUNG: ERSTELLEN EINES NEUEN EL-WORKBENCH MODULS ***
================================================================================================

Diese Datei dient sowohl als Vorlage als auch als umfassendes Beispiel für die Erstellung neuer Tabs.
Folgen Sie diesen Schritten, um Ihre eigene Funktionalität zu EL-Workbench hinzuzufügen:

1. DATEI KOPIEREN:
   Kopieren Sie `example_tab.py` und benennen Sie sie entsprechend um, z.B. `iv_measurement_tab.py`

2. KLASSE UMBENENNEN:
   Ändern Sie `ExampleTab` zu Ihrem Klassennamen, z.B. `IVMeasurementTab`

3. UI GESTALTEN:
   - Ändern Sie die `init_ui` Methode um Ihre Benutzeroberfläche zu erstellen
   - Verwenden Sie PyQt6 Widgets (QLabel, QPushButton, QLineEdit, etc.)
   - Folgen Sie den unten gezeigten Layout-Mustern

4. GETEILTE DATEN ZUGREIFEN:
   Das `self.shared_data` Objekt ist Ihr Zugang zur gesamten Anwendung:
   
   AKTUELLE AUSWAHL:
   - `self.shared_data.current_profile` - Aktuell ausgewähltes Benutzerprofil
   - `self.shared_data.current_device` - Aktuell ausgewähltes Gerät
   
   MESSDATEN:
   - `self.shared_data.current_wavelengths` - Aktuelle Spektrum-Wellenlängen
   - `self.shared_data.current_intensities` - Aktuelle Spektrum-Intensitäten
   
   GERÄTE-INSTANZEN:
   - `self.shared_data.smu_device` - SMU Gerät für Strom-/Spannungssteuerung
   - `self.shared_data.spectrometer_device` - Spektrometer-Gerät
   
   LOGGING:
   - `self.shared_data.info_manager.status(level, message)` - Statusmeldungen senden

5. IN main.py INTEGRIEREN:
   Fügen Sie diese zwei Zeilen in der `load_modules` Methode hinzu:
   a) Import: `from tabs.iv_measurement_tab import IVMeasurementTab`
   b) Tab hinzufügen: `self.tabs.addTab(IVMeasurementTab(self.shared_data), "I-V Messung")`

6. DESIGN-PRINZIPIEN BEFOLGEN:
   - Verwenden Sie try-except Blöcke für Fehlerbehandlung
   - Melden Sie Status über info_manager
   - Halten Sie UI-Logik getrennt von Mess-Logik
   - Dokumentieren Sie Ihren Code mit klaren Kommentaren

FERTIG! Starten Sie `main.py` und Ihr neues Modul wird Teil von EL-Workbench sein.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QMessageBox, QLineEdit, QTextEdit, QGridLayout
)
from PyQt6.QtCore import QTimer
import numpy as np


class ExampleTab(QWidget):
    """
    Beispiel-Tab der EL-Workbench Entwicklungsmuster demonstriert.
    
    Dieser Tab zeigt Studenten wie man:
    - Auf geteilte Daten zugreift (Profile, Geräte, Messungen)
    - Das Logging-System verwendet
    - Responsive UI-Elemente erstellt
    - Fehler elegant behandelt
    - EL-Workbench Design-Prinzipien befolgt
    """
    
    def __init__(self, shared_data):
        """
        Initialisiert den Beispiel-Tab.
        
        Args:
            shared_data: SharedData Instanz die Zugriff auf Anwendungsdaten bietet
        """
        super().__init__()
        self.shared_data = shared_data
        
        # Timer für periodische Updates (Demonstration von Live-Datenüberwachung)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # Aktualisierung jede Sekunde
        
        self.init_ui()
        
        # Sende initiale Statusmeldung
        self.shared_data.info_manager.status(
            self.shared_data.info_manager.INFO,
            "Beispiel-Tab erfolgreich initialisiert"
        )

    def init_ui(self):
        """Erstellt die Benutzeroberfläche."""
        main_layout = QVBoxLayout(self)
        
        # === KOPFZEILEN-BEREICH ===
        header_label = QLabel("🔬 EL-Workbench Beispiel & Vorlage Tab")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(header_label)
        
        # === AKTUELLER STATUS BEREICH ===
        status_header = QLabel("Aktueller Anwendungsstatus")
        status_header.setStyleSheet("font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(status_header)
        
        status_layout = QGridLayout()
        
        # Profil-Informationen
        status_layout.addWidget(QLabel("Aktives Profil:"), 0, 0)
        self.profile_label = QLabel("Kein Profil ausgewählt")
        status_layout.addWidget(self.profile_label, 0, 1)
        
        # Geräte-Informationen
        status_layout.addWidget(QLabel("Aktives Gerät:"), 1, 0)
        self.device_label = QLabel("Kein Gerät ausgewählt")
        status_layout.addWidget(self.device_label, 1, 1)
        
        # Messdaten-Status
        status_layout.addWidget(QLabel("Spektrum-Daten:"), 2, 0)
        self.spectrum_label = QLabel("Keine Daten verfügbar")
        status_layout.addWidget(self.spectrum_label, 2, 1)
        
        main_layout.addLayout(status_layout)
        
        # === ANALYSE-BEREICH ===
        analysis_header = QLabel("Datenanalyse Beispiel")
        analysis_header.setStyleSheet("font-weight: bold; margin-top: 20px;")
        main_layout.addWidget(analysis_header)
        
        # Analyse-Button
        self.analyze_button = QPushButton("🔍 Aktuelle Spektrumdaten analysieren")
        self.analyze_button.clicked.connect(self.analyze_spectrum_data)
        main_layout.addWidget(self.analyze_button)
        
        # Ergebnis-Anzeige
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(150)
        self.results_text.setPlaceholderText("Analyseergebnisse werden hier angezeigt...")
        main_layout.addWidget(self.results_text)
        
        # === LOGGING-DEMONSTRATION ===
        logging_header = QLabel("Logging-System Demonstration")
        logging_header.setStyleSheet("font-weight: bold; margin-top: 20px;")
        main_layout.addWidget(logging_header)
        
        logging_layout = QHBoxLayout()
        
        info_btn = QPushButton("INFO senden")
        info_btn.clicked.connect(lambda: self.demo_logging("INFO"))
        logging_layout.addWidget(info_btn)
        
        warning_btn = QPushButton("WARNUNG senden")
        warning_btn.clicked.connect(lambda: self.demo_logging("WARNING"))
        logging_layout.addWidget(warning_btn)
        
        error_btn = QPushButton("FEHLER senden")
        error_btn.clicked.connect(lambda: self.demo_logging("ERROR"))
        logging_layout.addWidget(error_btn)
        
        main_layout.addLayout(logging_layout)
        
        # === GERÄTE-INTERAKTION BEISPIEL ===
        device_header = QLabel("Geräte-Interaktion Beispiel")
        device_header.setStyleSheet("font-weight: bold; margin-top: 20px;")
        main_layout.addWidget(device_header)
        
        device_info_label = QLabel(
            "Dieser Bereich demonstriert wie man Geräteverfügbarkeit überprüft.\n"
            "In einem echten Mess-Tab würden Sie diese Gerätereferenzen verwenden\n"
            "um Hardware zu steuern und Daten zu erfassen."
        )
        main_layout.addWidget(device_info_label)
        
        self.device_status_label = QLabel("Gerätestatus wird hier angezeigt")
        main_layout.addWidget(self.device_status_label)
        
        check_devices_btn = QPushButton("🔌 Geräteverbindungen überprüfen")
        check_devices_btn.clicked.connect(self.check_device_connections)
        main_layout.addWidget(check_devices_btn)
        
        # === SHARED DATA UPDATE BEISPIEL ===
        update_header = QLabel("SharedData Update Beispiel")
        update_header.setStyleSheet("font-weight: bold; margin-top: 20px;")
        main_layout.addWidget(update_header)
        
        update_layout = QHBoxLayout()
        self.meta_input = QLineEdit()
        self.meta_input.setPlaceholderText("Geben Sie Metadaten ein...")
        update_layout.addWidget(self.meta_input)
        
        update_btn = QPushButton("Metadaten aktualisieren")
        update_btn.clicked.connect(self.update_measurement_meta)
        update_layout.addWidget(update_btn)
        
        main_layout.addLayout(update_layout)
        
        # Stretch hinzufügen um alles nach oben zu drücken
        main_layout.addStretch()

    def update_display(self):
        """
        Aktualisiert die Anzeige mit aktuellen geteilten Daten.
        
        Diese Methode demonstriert wie man Änderungen der geteilten Daten überwacht
        und die UI entsprechend aktualisiert. Wird jede Sekunde vom Timer aufgerufen.
        """
        try:
            # Profil-Informationen aktualisieren
            if self.shared_data.current_profile:
                profile_name = self.shared_data.current_profile.get("name", "Unbekannt")
                self.profile_label.setText(f"✅ {profile_name}")
            else:
                self.profile_label.setText("❌ Kein Profil ausgewählt")
            
            # Geräte-Informationen aktualisieren
            if self.shared_data.current_device:
                device_name = self.shared_data.current_device.get("device_name", "Unbekannt")
                self.device_label.setText(f"✅ {device_name}")
            else:
                self.device_label.setText("❌ Kein Gerät ausgewählt")
            
            # Spektrumdaten-Status aktualisieren
            if (self.shared_data.current_wavelengths.size > 0 and 
                self.shared_data.current_intensities.size > 0):
                data_points = len(self.shared_data.current_wavelengths)
                self.spectrum_label.setText(f"✅ {data_points} Datenpunkte verfügbar")
            else:
                self.spectrum_label.setText("❌ Keine Spektrumdaten")
                
        except Exception as e:
            # Demonstriere Fehlerbehandlung
            self.shared_data.info_manager.status(
                self.shared_data.info_manager.ERROR,
                f"Fehler beim Aktualisieren der Anzeige: {str(e)}"
            )

    def analyze_spectrum_data(self):
        """
        Analysiert aktuelle Spektrumdaten und zeigt Ergebnisse an.
        
        Diese Methode demonstriert:
        - Datenvalidierung
        - Fehlerbehandlung
        - Ergebnispräsentation
        - Status-Berichterstattung
        """
        try:
            # Prüfen ob Daten verfügbar sind
            if (self.shared_data.current_wavelengths.size == 0 or 
                self.shared_data.current_intensities.size == 0):
                
                QMessageBox.warning(
                    self, 
                    "Keine Daten verfügbar", 
                    "Bitte erfassen Sie zuerst Spektrumdaten mit dem Spektrometer-Tab."
                )
                return
            
            # Datenreferenzen holen
            wavelengths = self.shared_data.current_wavelengths
            intensities = self.shared_data.current_intensities
            
            # Analyse durchführen
            max_intensity = np.max(intensities)
            max_index = np.argmax(intensities)
            peak_wavelength = wavelengths[max_index]
            mean_intensity = np.mean(intensities)
            std_intensity = np.std(intensities)
            
            # Zusätzliche Metriken berechnen
            fwhm = self.calculate_fwhm(wavelengths, intensities)
            
            # Ergebnisse formatieren
            results = f"""SPEKTRUM-ANALYSE ERGEBNISSE
{'='*40}
Peak-Analyse:
  • Maximale Intensität: {max_intensity:.2f} Counts
  • Peak-Wellenlänge: {peak_wavelength:.2f} nm
  • FWHM: {fwhm:.2f} nm

Statistische Analyse:
  • Mittlere Intensität: {mean_intensity:.2f} Counts
  • Standardabweichung: {std_intensity:.2f} Counts
  • Datenpunkte: {len(wavelengths)}
  • Wellenlängenbereich: {wavelengths.min():.1f} - {wavelengths.max():.1f} nm

Analyse abgeschlossen um: {self.shared_data.info_manager.get_timestamp()}
"""
            
            self.results_text.setText(results)
            
            # Erfolg melden
            self.shared_data.info_manager.status(
                self.shared_data.info_manager.INFO,
                f"Spektrumanalyse abgeschlossen. Peak bei {peak_wavelength:.1f} nm"
            )
            
        except Exception as e:
            # Fehler behandeln und melden
            error_msg = f"Analyse fehlgeschlagen: {str(e)}"
            self.results_text.setText(f"FEHLER: {error_msg}")
            self.shared_data.info_manager.status(
                self.shared_data.info_manager.ERROR,
                error_msg
            )

    def calculate_fwhm(self, wavelengths, intensities):
        """
        Berechnet die Halbwertsbreite (FWHM) des Spektrums.
        
        Dies ist eine vereinfachte FWHM-Berechnung für Demonstrationszwecke.
        """
        try:
            max_intensity = np.max(intensities)
            half_max = max_intensity / 2
            
            # Indizes finden wo Intensität über der Halbwertsbreite liegt
            above_half = intensities >= half_max
            indices = np.where(above_half)[0]
            
            if len(indices) > 0:
                fwhm = wavelengths[indices[-1]] - wavelengths[indices[0]]
                return fwhm
            else:
                return 0.0
        except:
            return 0.0

    def demo_logging(self, level):
        """
        Demonstriert das Logging-System.
        
        Args:
            level: Log-Level ("INFO", "WARNING" oder "ERROR")
        """
        messages = {
            "INFO": "Dies ist eine Informationsmeldung vom Beispiel-Tab",
            "WARNING": "Dies ist eine Warnmeldung - etwas könnte Aufmerksamkeit benötigen",
            "ERROR": "Dies ist eine Fehlermeldung - etwas ist schiefgelaufen"
        }
        
        log_level = getattr(self.shared_data.info_manager, level)
        self.shared_data.info_manager.status(log_level, messages[level])

    def check_device_connections(self):
        """
        Überprüft und meldet Geräteverbindungsstatus.
        
        Dies demonstriert wie man Geräteverfügbarkeit überprüft und Status meldet.
        """
        try:
            status_lines = []
            
            # Spektrometer überprüfen
            if self.shared_data.spectrometer_device is not None:
                status_lines.append("✅ Spektrometer: Verbunden")
            else:
                status_lines.append("❌ Spektrometer: Nicht verbunden")
            
            # SMU überprüfen
            if self.shared_data.smu_device is not None:
                status_lines.append("✅ SMU: Verbunden")
            else:
                status_lines.append("❌ SMU: Nicht verbunden")
            
            # Prüfen ob Messfunktion verfügbar ist
            if self.shared_data.smu_apply_and_measure is not None:
                status_lines.append("✅ SMU Messfunktion: Verfügbar")
            else:
                status_lines.append("❌ SMU Messfunktion: Nicht verfügbar")
            
            status_text = "\n".join(status_lines)
            self.device_status_label.setText(status_text)
            
            # An Log melden
            connected_devices = sum(1 for line in status_lines if "✅" in line)
            self.shared_data.info_manager.status(
                self.shared_data.info_manager.INFO,
                f"Geräteprüfung abgeschlossen: {connected_devices} Geräte verbunden"
            )
            
        except Exception as e:
            error_msg = f"Geräteprüfung fehlgeschlagen: {str(e)}"
            self.device_status_label.setText(f"FEHLER: {error_msg}")
            self.shared_data.info_manager.status(
                self.shared_data.info_manager.ERROR,
                error_msg
            )

    def update_measurement_meta(self):
        """
        Demonstriert wie man SharedData aktualisiert.
        
        Dies zeigt wie Tabs Daten in SharedData schreiben können,
        die dann von anderen Tabs gelesen werden können.
        """
        try:
            meta_text = self.meta_input.text().strip()
            if not meta_text:
                QMessageBox.warning(self, "Eingabe erforderlich", "Bitte geben Sie Metadaten ein.")
                return
            
            # SharedData aktualisieren
            self.shared_data.current_measurement_meta["example_note"] = meta_text
            self.shared_data.current_measurement_meta["timestamp"] = self.shared_data.info_manager.get_timestamp()
            
            # Eingabefeld leeren
            self.meta_input.clear()
            
            # Erfolg melden
            self.shared_data.info_manager.status(
                self.shared_data.info_manager.INFO,
                f"Metadaten aktualisiert: {meta_text}"
            )
            
        except Exception as e:
            error_msg = f"Fehler beim Aktualisieren der Metadaten: {str(e)}"
            self.shared_data.info_manager.status(
                self.shared_data.info_manager.ERROR,
                error_msg
            )