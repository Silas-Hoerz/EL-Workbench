# el-workbench/main.py
# -*- coding: utf-8 -*-
"""
============================================================================
 File:           main.py
 Author:         Team EL-Workbench
 Creation date:  2025-06-25
 Last modified:  2025-01-15
 Version:        1.1.0
============================================================================
 Description:
    Haupt-Einstiegspunkt für die EL-Workbench Anwendung.
    Diese Software dient als zentrale Steuerungs- und Analyseplattform
    für einen Elektrolumineszenz (EL) Messaufbau.
============================================================================
 Change Log:
 - 2025-06-25: Erste Version erstellt. Name geändert zu EL-Workbench.
 - 2025-07-25: SharedState refaktoriert um API-Instanzen zu halten.
               ProfileApi für dedizierte Profilverwaltung eingeführt.
 - 2025-07-28: 'current_profile' und 'current_device' zu SharedState
               Initialisierung hinzugefügt um AttributeError in InfoWidget zu beheben.
 - 2025-01-15: Große Refaktorierung für v1.1.0. Verbesserte Code-Struktur,
               Dokumentation und studentenfreundliche Design-Muster.
               SharedState zu SharedData umbenannt, ProfileApi entfernt.
============================================================================
"""

import sys
import os
import numpy
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout
from PyQt6.QtCore import QObject # Important if SharedState will emit signals

# --- Global Application Metadata ---
__version__ = "1.1.0"

# --- Importiere die Styles und die einzelnen Tab-Klassen ---
from styles.dark_theme import DARK_STYLESHEET
from tabs.profile_tab import ProfileTab
from tabs.analysis_tab import AnalysisTab
from tabs.spectrum_tab import SpectrumTab
from tabs.smu_tab import SmuTab
from tabs.sweep_tab import SweepTab
from tabs.settings_tab import SettingsTab
from other.info import InfoManager, InfoWidget

from tabs.example_tab import ExampleTab

# Zukünftige API-Klassen können hier importiert werden
# from api.smu_api import SmuApi # FÜR ZUKÜNFTIGE SMU-API
# from api.spectrometer_api import SpectrometerApi # FÜR ZUKÜNFTIGE SPEKTRUM-API


class SharedData(QObject):
    """
    Zentrales Datenobjekt für die EL-Workbench Anwendung.
    
    Diese Klasse dient als einzige Quelle der Wahrheit für alle geteilten Daten,
    Geräteinstanzen und Referenzen. Sie ermöglicht die Kommunikation zwischen
    verschiedenen Tabs und Modulen bei klarer Datenverantwortung.
    
    Hauptverantwortlichkeiten:
    - Speichern der aktuellen Profil- und Geräteauswahl
    - Verwalten von Geräteinstanzen und Messdaten
    - Bereitstellen von zentralisiertem Logging über InfoManager
    
    Für Studenten: Dies ist Ihre Hauptschnittstelle für den Zugriff auf geteilte Daten!
    Verwenden Sie self.shared_data.current_profile, self.shared_data.current_device
    und andere Attribute für den Datenzugriff aus jedem Tab.
    """
    def __init__(self):
        super().__init__()
        
        # === ZUKÜNFTIGE API INSTANZEN ===
        # Hier können zukünftige API-Klassen für strukturierten Datenzugriff hinzugefügt werden
        # self.smu_api = None        # Für SMU-Gerätesteuerung
        # self.spectrometer_api = None # Für Spektrometer-Operationen
   
        # === ZENTRALISIERTES LOGGING ===
        self.info_manager = InfoManager()

        # === AKTUELLE AUSWAHL ===
        # Diese werden vom ProfileTab aktualisiert, wenn Benutzer Profil/Gerät auswählt
        self.current_profile = None  # Vollständiges Profil-Dictionary
        self.current_device = None   # Vollständiges Geräte-Dictionary

        # === GERÄTE-INSTANZEN ===
        # Low-Level-Geräteobjekte für direkte Hardware-Steuerung
        self.smu_device = None       # Keithley SMU Geräteinstanz
        self.spectrometer_device = None # Ocean Optics Spektrometer-Instanz
        self.smu_apply_and_measure = None # High-Level SMU Messfunktion

        # === LIVE MESSDATEN ===
        # Flüchtige Daten, die von Mess-Tabs aktualisiert und von Analyse-Tabs gelesen werden
        self.current_wavelengths = numpy.array([])  # Aktuelle Spektrum-Wellenlängen
        self.current_intensities = numpy.array([])  # Aktuelle Spektrum-Intensitäten
        self.current_measurement_meta = {}          # Mess-Metadaten


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        
        self.setWindowTitle(f"EL-Workbench - v{__version__}")
        self.setGeometry(100, 100, 1200, 700)

        self.shared_data = SharedData() # SharedData wird hier korrekt initialisiert

        # Erstelle ein zentrales Widget und ein Haupt-Layout dafür
        self.central_widget = QWidget()
        self.central_widget.setObjectName("Main")
        self.main_layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)
        
        # Tabs sollen den größten Teil des Platzes einnehmen
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs, 1) # <-- Hinzufügen mit Stretch-Faktor 1

        self.load_modules()

        # Erstelle das InfoWidget und übergebe die InfoManager-Instanz aus shared_data
        self.info_widget = InfoWidget(self.shared_data) # Hier wird shared_data übergeben
        self.main_layout.addWidget(self.info_widget) # <-- Füge das InfoWidget hinzu

        # Sende initiale Startmeldung
        self.shared_data.info_manager.status(InfoManager.INFO, "EL-Workbench v1.1.0 erfolgreich gestartet")


    def load_modules(self):
        """
        Erstellt Instanzen aller Module und fügt sie den Tabs hinzu.
        
        Diese Methode demonstriert das Standardmuster für die Integration neuer Tabs:
        1. Tab-Instanz mit shared_data Parameter erstellen
        2. Tab zum Tab-Widget mit beschreibendem Namen hinzufügen
        
        Studenten: Fügen Sie hier Ihre neuen Tabs nach dem gleichen Muster hinzu!
        """
        # === KERN-TABS ===
        
        # Profilverwaltungs-Tab - verwaltet Benutzerprofile und Gerätekonfigurationen
        self.profile_tab_widget = ProfileTab(self.shared_data)
        

        # === MESS-TABS ===

        # Analyse-Tab - für Datenanalyse und Visualisierung
        self.analysis_tab_widget = AnalysisTab(self.shared_data)
        self.tabs.addTab(self.analysis_tab_widget, "Analyse")
        self.tabs.addTab(self.profile_tab_widget, "Profile")
        # Spektrometer-Steuerungs-Tab - verwaltet Ocean Optics Spektrometer
        self.spectrum_tab_widget = SpectrumTab(self.shared_data)
        self.tabs.addTab(self.spectrum_tab_widget, "Spektrometer")

        # SMU-Steuerungs-Tab - verwaltet Keithley SMU Gerät
        self.smu_widget = SmuTab(self.shared_data)
        self.tabs.addTab(self.smu_widget, "SMU Steuerung")

        # Sweep-Mess-Tab - automatisierte Messprotokolle
        self.sweep_widget = SweepTab(self.shared_data)
        self.tabs.addTab(self.sweep_widget, "Sweep Messungen") 

        # === HILFSPROGRAMM-TABS ===
        
        # Einstellungs-Tab - Anwendungskonfiguration
        self.settings_tab_widget = SettingsTab(self.shared_data)
        self.tabs.addTab(self.settings_tab_widget, "Einstellungen")

        # Beispiel/Vorlage-Tab - demonstriert Entwicklungsmuster für Studenten
        self.example_tab_widget = ExampleTab(self.shared_data)
        self.tabs.addTab(self.example_tab_widget, "Beispiel & Vorlage")

        # === FÜGEN SIE HIER IHRE NEUEN TABS HINZU ===
        # Folgen Sie diesem Muster:
        # self.my_tab_widget = MyCustomTab(self.shared_data)
        # self.tabs.addTab(self.my_tab_widget, "Meine Analyse")
        
        # Beispiel für Studenten:
        # self.iv_measurement_widget = IVMeasurementTab(self.shared_data)
        # self.tabs.addTab(self.iv_measurement_widget, "I-V Kennlinien")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    main_win = MainWindow()
    app.setStyleSheet(DARK_STYLESHEET)
    main_win.show()
    
    sys.exit(app.exec())