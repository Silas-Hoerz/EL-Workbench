# el-workbench/tabs/beispiel_tab.py

# -*- coding: utf-8 -*-
"""
============================================================================
 File:          beispiel_tab.py
 Author:        Silas Hörz
 Creation date: 2025-06-25
 Last modified: 2025-06-25
 Version:       1.0.0
============================================================================
 Description:
     Vorlage für ein neues Modul (Tab) im EL-Workbench.
     Studenten können diese Datei als Startpunkt für eigene
     Funktionen und Analysen verwenden.
============================================================================
 Change Log:
 - 2025-06-25: Initial version created. Updated instructions for EL-Workbench.
============================================================================
"""

"""
****************************************************************************************
*** ANLEITUNG ZUM ERSTELLEN EINES NEUEN EL-WORKBENCH-MODULS ***
****************************************************************************************

So fügst du deine eigene Funktion als neuen Tab zum EL-Workbench hinzu:

1.  DATEI KOPIEREN:
    Kopiere diese Datei (`beispiel_tab.py`) und gib ihr einen passenden Namen, 
    z.B. `kennlinien_messung_tab.py`.

2.  KLASSE UMBENENNEN:
    Ändere den Klassennamen `BeispielTab` in deiner neuen Datei, z.B. `KennlinienMessungTab`.

3.  EIGENEN CODE SCHREIBEN:
    - Gestalte deine Benutzeroberfläche in der `init_ui`-Methode.
    - Implementiere deine Logik in eigenen Methoden (z.B. `starte_kennlinie`).
    
4.  AUF GETEILTE DATEN UND GERÄTE ZUGREIFEN:
    Das Objekt `self.shared_data` ist dein Tor zur restlichen Anwendung. Es enthält:
    - `self.shared_data.spec`: Das Spektrometer-Objekt.
    - `self.shared_data.wavelengths`: NumPy-Array der Wellenlängen.
    - `self.shared_data.intensities`: NumPy-Array der Intensitäten.
    
    -> Zukünftig könnten hier weitere Geräte (Spannungsquelle, etc.) hinzugefügt werden:
    -> `self.shared_data.sourcemeter`
    -> `self.shared_data.temperature_controller`

5.  MODUL IN `main.py` INTEGRIEREN:
    Öffne `main.py` und füge zwei Zeilen hinzu:
    a) Importiere deine Klasse: `from tabs.kennlinien_messung_tab import KennlinienMessungTab`
    b) Erstelle eine Instanz und füge sie den Tabs hinzu:
       `kennlinien_tab = KennlinienMessungTab(self.shared_data)`
       `self.tabs.addTab(kennlinien_tab, "I-V Kennlinie")`

FERTIG! Starte `main.py` und dein neues Modul ist Teil des EL-Workbench.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox
import numpy as np

class BeispielTab(QWidget):
    def __init__(self, shared_data):
        super().__init__()
        self.shared_data = shared_data
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        info_label = QLabel("Dies ist ein Beispiel-Modul. Es kann auf Daten anderer Module zugreifen.")
        layout.addWidget(info_label)

        self.data_label = QLabel("Noch keine Daten vom Spektrometer empfangen.")
        layout.addWidget(self.data_label)
        
        self.analyze_button = QPushButton("Analysiere aktuelle Messdaten")
        self.analyze_button.clicked.connect(self.analyze_data)
        layout.addWidget(self.analyze_button)
        
        layout.addStretch()

    def analyze_data(self):
        if self.shared_data.wavelengths.size > 0 and self.shared_data.intensities.size > 0:
            wavelengths = self.shared_data.wavelengths
            intensities = self.shared_data.intensities
            
            max_intensity = np.max(intensities)
            max_index = np.argmax(intensities)
            peak_wavelength = wavelengths[max_index]
            
            result_text = (f"Analyse-Ergebnis:\n"
                           f"  - Maximale Intensität: {max_intensity:.2f}\n"
                           f"  - Bei Wellenlänge: {peak_wavelength:.2f} nm")
            self.data_label.setText(result_text)
        else:
            QMessageBox.warning(self, "EL-Workbench: Keine Daten", 
                                "Bitte starte zuerst eine Messung im 'Spektrometer'-Tab.")