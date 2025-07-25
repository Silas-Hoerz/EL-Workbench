
# el-workbench/main.py
# -*- coding: utf-8 -*-
"""
============================================================================
 File:          main.py
 Author:        Silas Hörz
 Creation date: 2025-06-25
 Last modified: 2025-06-25
 Version:       1.0.0
============================================================================
 Description:
     Haupt-Startdatei für das EL-Workbench.
     Diese Software dient als zentrale Steuerungs- und Auswertungs-
     plattform für einen Elektrolumineszenz (EL)-Messplatz.
============================================================================
 Change Log:
 - 2025-06-25: Initial version created. Name changed to EL-Workbench.
============================================================================
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))


import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget

# --- Globale Anwendungs-Metadaten ---
__version__ = "1.0.0"
# --- Importiere die Styles und die einzelnen Tab-Klassen ---


# from styles.dark_theme import DARK_STYLESHEET
from tabs.profile_tab import ProfileTab
from tabs.spectrum_tab import SpectrumTab
from tabs.smu_tab import SmuTab
from tabs.sweep_tab import SweepTab
from tabs.settings_tab import SettingsTab

from tabs.beispiel_tab import BeispielTab

# HIER NEUE MODULE IMPORTIEREN
# from tabs.kennlinien_messung_tab import KennlinienMessungTab

class SharedState:
    """
    Ein Objekt, um Daten und Geräte-Instanzen zwischen den Modulen (Tabs) zu teilen.
    Eine Instanz dieser Klasse wird an jedes Modul übergeben.
    """
    def __init__(self):

        #Das aktuell geladene Profil
        self.current_profile = None 

        # Hier werden die Geräte-Objekte gespeichert
        self.spec = None
        

        # Referenzen für die Source-Measure Unit (SMU)
        self.smu = None  # Hält das low-level Keithley2602-Objekt
        self.smu_apply_and_measure = None # Hält eine high-level Funktion zum Ansteuern

        
        # Hier werden die geteilten Messdaten gespeichert
        self.wavelengths = np.array([])
        self.intensities = np.array([])


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"EL-Workbench - v{__version__}")
        self.setGeometry(100, 100, 1200, 700)

        # 1. Erstelle die zentrale Instanz des geteilten Datenobjekts
        self.shared_data = SharedState()

        # 2. Erstelle das Tab-Widget für die Module
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # 3. Lade die einzelnen Module und füge sie als Tabs hinzu
        self.load_modules()

    def load_modules(self):
        """Erstellt die Instanzen der einzelnen Module und fügt sie den Tabs hinzu."""
        
        # User Tab
        self.profile_tab_widget = ProfileTab(self.shared_data)
        self.tabs.addTab(self.profile_tab_widget, "Profile")

        # Spektrometer-Modul
        self.spectrum_tab_widget = SpectrumTab(self.shared_data)
        self.tabs.addTab(self.spectrum_tab_widget, "Spektrometer")

         # SMU-Modul
        self.smu_widget = SmuTab(self.shared_data)
        self.tabs.addTab(self.smu_widget, "SMU Steuerung")

        # Sweep Funktion
        self.sweep_widget = SweepTab(self.shared_data)
        self.tabs.addTab(self.sweep_widget, "Sweep") 


        # Settings-Modul
        self.settings_tab_widget = SettingsTab(self.shared_data)
        self.tabs.addTab(self.settings_tab_widget, "Einstellungen")

        # Beispiel-Modul
        self.beispiel_tab_widget = BeispielTab(self.shared_data)
        self.tabs.addTab(self.beispiel_tab_widget, "Beispiel Analyse")


        # HIER NEUE MODULE HINZUFÜGEN
        # self.kennlinien_widget = KennlinienMessungTab(self.shared_data)
        # self.tabs.addTab(self.kennlinien_widget, "I-V Kennlinie")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    main_win = MainWindow()
    #app.setStyleSheet(DARK_STYLESHEET)
    main_win.show()
    
    sys.exit(app.exec())