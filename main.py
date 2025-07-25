# el-workbench/main.py
# -*- coding: utf-8 -*-
"""
============================================================================
 File:          main.py
 Author:        Silas Hörz
 Creation date: 2025-06-25
 Last modified: 2025-07-25 (Updated for API-driven architecture)
 Version:       2.0.0
============================================================================
 Description:
    Haupt-Startdatei für das EL-Workbench.
    Diese Software dient als zentrale Steuerungs- und Auswertungs-
    plattform für einen Elektrolumineszenz (EL)-Messplatz.
============================================================================
 Change Log:
 - 2025-06-25: Initial version created. Name changed to EL-Workbench.
 - 2025-07-25: Refactored SharedState to hold API instances.
               Introduced ProfileApi for dedicated profile management.
============================================================================
"""

import sys
import os
import numpy
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout
from PyQt6.QtCore import QObject # Important if SharedState will emit signals

# --- Globale Anwendungs-Metadaten ---
__version__ = "2.0.0" # Updated version

# --- Importiere die Styles und die einzelnen Tab-Klassen ---
from styles.dark_theme import DARK_STYLESHEET
from tabs.profile_tab import ProfileTab
from tabs.spectrum_tab import SpectrumTab
from tabs.smu_tab import SmuTab
from tabs.sweep_tab import SweepTab
from tabs.settings_tab import SettingsTab
from other.info import InfoManager, InfoWidget

from tabs.beispiel_tab import BeispielTab

# Importiere die neuen API-Klassen
from api.profile_api import ProfileApi
# from api.smu_api import SmuApi # FÜR ZUKÜNFTIGE SMU-API
# from api.spectrometer_api import SpectrometerApi # FÜR ZUKÜNFTIGE SPEKTRUM-API


class SharedState(QObject): # Erbt von QObject, falls später Signals/Slots verwendet werden
    """
    Ein zentrales Objekt, das Instanzen von API-Klassen und Geräten
    sowie temporäre/flüchtige Messdaten zwischen den Modulen (Tabs) teilt.
    API-Instanzen sind die primäre Schnittstelle für den Zugriff auf Daten und Funktionen.
    """
    def __init__(self):
        super().__init__()
        
        # API-Instanzen (primärer Zugriff für persistente/komplexe Daten)
        self.profile_api = None      # Wird in MainWindow initialisiert
        # self.smu_api = None        # Zukünftige SMU API Instanz
   

        # Direkte Referenzen auf Low-Level-Geräte-Objekte (könnten auch in APIs gekapselt werden)
        self.smu_device = None       # Das low-level Keithley2602-Objekt
        self.spectrometer_device = None # Das low-level Spektrometer-Objekt (z.B. OceanOptics)
        self.info_manager = InfoManager()

        self.smu_apply_and_measure = None 

        # Temporäre/flüchtige Messdaten (Regel 1.4: Direkter Zugriff für Read-Only-Daten)
        # Diese Daten werden vom Spektrometer-Tab gesetzt und von anderen Tabs gelesen.
        self.current_wavelengths = numpy.array([])
        self.current_intensities = numpy.array([])
        self.current_measurement_meta = {} # Metadaten der letzten Messung


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        
        self.setWindowTitle(f"EL-Workbench - v{__version__}")
        self.setGeometry(100, 100, 1200, 700)

        self.shared_data = SharedState()

        # Erstelle ein zentrales Widget und ein Haupt-Layout dafür
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)
        
        # Tabs sollen den größten Teil des Platzes einnehmen
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs, 1) # <-- Hinzufügen mit Stretch-Faktor 1

        self.load_modules()

        # NEU: Erstelle das InfoWidget und übergebe die InfoManager-Instanz aus shared_data
        self.info_widget = InfoWidget(self.shared_data.info_manager)
        self.main_layout.addWidget(self.info_widget) # <-- Füge das InfoWidget hinzu

        # Starte mit einer Initialmeldung
        self.shared_data.info_manager.status(InfoManager.INFO, "Anwendung gestartet.")


    def load_modules(self):
        """
        Erstellt die Instanzen der einzelnen Module und API-Klassen und fügt sie den Tabs hinzu.
        Stellt sicher, dass APIs korrekt an SharedState und Tabs übergeben werden.
        """
        # Profile Tab (Verwaltet Profildaten und persistiert sie)
        self.profile_tab_widget = ProfileTab(self.shared_data)
        self.tabs.addTab(self.profile_tab_widget, "Profile")

        # Initialisiere die ProfileApi, die Zugriff auf die Profildaten bietet
        # Wichtig: Die ProfileApi benötigt eine Referenz zum ProfileTab für Speichervorgänge.
        self.shared_data.profile_api = ProfileApi(self.shared_data, self.profile_tab_widget)


        # Spektrometer-Modul (setzt current_wavelengths/intensities in shared_data)
        # Zukünftig könnte hier eine SpectrometerApi initialisiert werden
        self.spectrum_tab_widget = SpectrumTab(self.shared_data)
        self.tabs.addTab(self.spectrum_tab_widget, "Spektrometer")

        # SMU-Modul (setzt smu_device in shared_data, könnte später eigene API bekommen)
        # Zukünftig könnte hier eine SmuApi initialisiert werden
        self.smu_widget = SmuTab(self.shared_data)
        self.tabs.addTab(self.smu_widget, "SMU Steuerung")

        # Sweep Funktion (nutzt smu_device und current_wavelengths/intensities über shared_data)
        # Wenn SMU/Spectrum eine API bekommen, sollte Sweep diese APIs nutzen.
        self.sweep_widget = SweepTab(self.shared_data)
        self.tabs.addTab(self.sweep_widget, "Sweep") 

        # Settings-Modul (könnte eine SettingsApi nutzen)
        self.settings_tab_widget = SettingsTab(self.shared_data)
        self.tabs.addTab(self.settings_tab_widget, "Einstellungen")

        # Beispiel-Modul (nutzt die APIs)
        # WICHTIG: Hier muss die shared_data.profile_api übergeben werden, damit es die neuen APIs nutzen kann!
        self.beispiel_tab_widget = BeispielTab(self.shared_data)
        self.tabs.addTab(self.beispiel_tab_widget, "Beispiel Analyse")


        # HIER NEUE MODULE HINZUFÜGEN
        # self.kennlinien_widget = KennlinienMessungTab(self.shared_data)
        # self.tabs.addTab(self.kennlinien_widget, "I-V Kennlinie")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    main_win = MainWindow()
    app.setStyleSheet(DARK_STYLESHEET)
    main_win.show()
    
    sys.exit(app.exec())