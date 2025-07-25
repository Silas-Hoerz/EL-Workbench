# el-workbench/tabs/settings_tab.py

# -*- coding: utf-8 -*-
"""
============================================================================
 File:          settings_tab.py
 Author:        Silas Hörz
 Creation date: 2025-06-25
 Last modified: 2025-06-25
 Version:       1.0.0
============================================================================
 Description:
     Tab für allgemeine Einstellungen
============================================================================
 Change Log:
 - 2025-06-25: Initial version created. Updated instructions for EL-Workbench.
============================================================================
"""

"""
****************************************************************************************
*** ANLEITUNG ZUM ERSTELLEN EINES NEUEN EL-WORKBENCH-MODULS ***
****************************************************************************************
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox
import numpy as np

from styles.realdarkmode import RealDarkmodeOverlay



class SettingsTab(QWidget):
    def __init__(self, shared_data):
        super().__init__()
        self.shared_data = shared_data
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.darkmode_button = QPushButton("Real Darkmode aktivieren")
        self.darkmode_button.setCheckable(True)
        self.darkmode_button.clicked.connect(self.toggle_darkmode)
        layout.addWidget(self.darkmode_button)

        
        layout.addStretch()

    def toggle_darkmode(self, checked):
        if checked:
            self.overlay = RealDarkmodeOverlay()
            self.overlay.showFullScreen()
            self.darkmode_button.setText("Real Darkmode deaktivieren")
        else:
            # Sicherheitsabfrage
            reply = QMessageBox.question(
                self,
                "Real Darkmode deaktivieren",
                "Möchten Sie den Real Darkmode wirklich deaktivieren?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                if hasattr(self, 'overlay'):
                    self.overlay.hide()
                    self.overlay.deleteLater()
                    del self.overlay
                self.darkmode_button.setText("Real Darkmode aktivieren")
            else:
                # Abbrechen: Button bleibt aktiviert
                self.darkmode_button.setChecked(True)
