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
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,  QSplashScreen
from PyQt6.QtCore import QObject,Qt,QSettings, QPoint, QSize # Important if SharedState will emit signals
from PyQt6.QtGui import QIcon, QPixmap
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

        # QSettings mit Organisation und Anwendungname
        self.settings = QSettings("ELWorkbenchTeam", "EL-Workbench")

        # Fenster-Icon und Titel
        icon_path = os.path.join(os.path.dirname(__file__), "icons", "logo.ico")
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle(f"EL-Workbench - v{__version__}")

        # Fenstergröße und Position laden
        self.restore_window_settings()

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

    def closeEvent(self, event):
        # Fenstergröße und Position speichern beim Schließen
        self.save_window_settings()
        super().closeEvent(event)

    def save_window_settings(self):
        self.settings.setValue("window_size", self.size())
        self.settings.setValue("window_pos", self.pos())

    def restore_window_settings(self):
        size = self.settings.value("window_size")
        pos = self.settings.value("window_pos")

        if size is not None and isinstance(size, QSize):
            self.resize(size)
        else:
            self.resize(1200, 700)  # Standardgröße

        if pos is not None and isinstance(pos, QPoint):
            self.move(pos)
        else:
            self.move(100, 100)     # Standardposition

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    splash_path = os.path.join(os.path.dirname(__file__), "icons", "logo.png")

    if os.path.exists(splash_path):
        pixmap_orig = QPixmap(splash_path)

        # Skaliere auf 16:9, z.B. 480x270 px
        splash_size = (480, 270)
        pixmap_scaled = pixmap_orig.scaled(splash_size[0], splash_size[1], 
                                        Qt.AspectRatioMode.IgnoreAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation)

        splash = QSplashScreen(pixmap_scaled)
    else:
        splash = QSplashScreen()
        splash.setStyleSheet("background-color: #3498db; color: white; font-size: 20px;")
        splash.showMessage("EL-Workbench wird geladen...", Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.white)

    splash.setWindowFlag(Qt.WindowType.FramelessWindowHint)
    splash.show()
    app.processEvents()  # Wichtig, damit der Splash sofort angezeigt wird

    import time
    time.sleep(0.1)  # 1,5 Sekunden warten (im echten Fall Initialisierung)

    main_win = MainWindow()
    app.setStyleSheet(DARK_STYLESHEET)
    
    splash.finish(main_win)  # Splash Screen schließen, sobald Hauptfenster bereit ist
    
    main_win.show()
    
    sys.exit(app.exec())