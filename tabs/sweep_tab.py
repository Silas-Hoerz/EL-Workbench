# el-workbench/tabs/sweep_tab.py

# -*- coding: utf-8 -*-
"""
============================================================================
 File:          sweep_tab.py
 Author:        Silas Hörz
 Creation date: 2025-07-11
 Last modified: 2025-07-11
 Version:       1.0.0
============================================================================
 Description:
     Modul für Strom- und Spannungssweeps unter Verwendung der SMU.
     Die Messung läuft in einem separaten Thread, um die GUI nicht zu
     blockieren.
============================================================================
 Change Log:
 - 2025-07-11: Initial version created.
============================================================================
"""
import time
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox,
    QGridLayout, QGroupBox, QLineEdit, QRadioButton, QProgressBar
)
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtGui import QDoubleValidator

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

# Dies ist der Worker, der die eigentliche Arbeit im Hintergrund erledigt.
class SweepWorker(QObject):
    # Signale, um mit dem Haupt-Thread (GUI) zu kommunizieren
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    newData = pyqtSignal(float, float) # Sendet (x_wert, y_wert)
    error = pyqtSignal(str)

    def __init__(self, shared_data, params):
        super().__init__()
        self.shared_data = shared_data
        self.params = params
        self._is_running = True

    def run(self):
        """Führt den Sweep durch."""
        try:
            start = self.params['start']
            end = self.params['end']
            step = self.params['step']
            is_voltage_sweep = self.params['is_voltage_sweep']
            
            sweep_points = np.arange(start, end + step, step)
            total_steps = len(sweep_points)

            for i, level in enumerate(sweep_points):
                if not self._is_running:
                    break # Schleife abbrechen, wenn stop() aufgerufen wurde

                # Die High-Level-Funktion aus dem SMU-Tab aufrufen
                result = self.shared_data.smu_apply_and_measure(
                    channel='a',
                    is_voltage_source=is_voltage_sweep,
                    level=level,
                    limit=0.1 # Limit sollte hier vielleicht auch einstellbar sein
                )
                
                if result is None:
                    raise ConnectionError("Messung fehlgeschlagen. SMU nicht bereit?")

                current, voltage = result
                
                # Daten an die GUI senden
                if is_voltage_sweep:
                    self.newData.emit(voltage, current) # x=V, y=I
                else:
                    self.newData.emit(current, voltage) # x=I, y=V

                # Fortschritt senden
                self.progress.emit(int(((i + 1) / total_steps) * 100))
                time.sleep(0.05) # Kurze Pause, um die SMU nicht zu überlasten

        except Exception as e:
            self.error.emit(f"Fehler während des Sweeps: {e}")
        
        self.finished.emit()

    def stop(self):
        """Signalisiert dem Worker, die Arbeit zu beenden."""
        self._is_running = False


# Dies ist das Haupt-Widget für den Tab
class SweepTab(QWidget):
    def __init__(self, shared_data):
        super().__init__()
        self.shared_data = shared_data
        self.is_sweeping = False
        
        # Daten-Listen für den Plot
        self.x_data = []
        self.y_data = []
        
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        # Linke Seite: Steuer-Elemente
        controls_widget = QWidget()
        controls_widget.setFixedWidth(300)
        controls_layout = QVBoxLayout(controls_widget)
        
        # Parameter-Box
        params_group = QGroupBox("Sweep-Parameter")
        params_layout = QGridLayout()

        self.rb_voltage = QRadioButton("Spannungssweep (V)"); self.rb_voltage.setChecked(True)
        self.rb_current = QRadioButton("Stromsweep (A)")
        params_layout.addWidget(self.rb_voltage, 0, 0, 1, 2)
        params_layout.addWidget(self.rb_current, 1, 0, 1, 2)
        
        validator = QDoubleValidator() # Validator für Fließkommazahlen
        
        params_layout.addWidget(QLabel("Start:"), 2, 0)
        self.le_start = QLineEdit("-1.0"); self.le_start.setValidator(validator)
        params_layout.addWidget(self.le_start, 2, 1)

        params_layout.addWidget(QLabel("Ende:"), 3, 0)
        self.le_end = QLineEdit("1.0"); self.le_end.setValidator(validator)
        params_layout.addWidget(self.le_end, 3, 1)

        params_layout.addWidget(QLabel("Schrittweite:"), 4, 0)
        self.le_step = QLineEdit("0.1"); self.le_step.setValidator(validator)
        params_layout.addWidget(self.le_step, 4, 1)

        params_group.setLayout(params_layout)
        controls_layout.addWidget(params_group)

        # Steuerungs-Box
        control_group = QGroupBox("Steuerung")
        control_layout_v = QVBoxLayout()
        self.btn_start_stop = QPushButton("Sweep starten")
        self.btn_start_stop.clicked.connect(self._start_or_stop_sweep)
        control_layout_v.addWidget(self.btn_start_stop)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout_v.addWidget(self.progress_bar)

        control_group.setLayout(control_layout_v)
        controls_layout.addWidget(control_group)

        controls_layout.addStretch()
        layout.addWidget(controls_widget)

        # Rechte Seite: Plot
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self._configure_plot()
        plot_layout.addWidget(self.canvas)
        layout.addWidget(plot_widget, stretch=1)

    def _configure_plot(self):
        """Setzt das Styling für den Plot (Dark Mode)."""
        
        self.figure.patch.set_facecolor("#18181800")
        self.ax.set_facecolor("#18181800")
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.title.set_color('white')
        self.ax.grid(True, linestyle='--', alpha=0.6)

    def _start_or_stop_sweep(self):
        if self.is_sweeping:
            self._stop_sweep()
        else:
            self._start_sweep()

    def _start_sweep(self):
        # 1. Prüfen, ob SMU bereit ist
        if not self.shared_data.smu_apply_and_measure:
            QMessageBox.warning(self, "Fehler", "SMU ist nicht verbunden oder die Steuerungsfunktion ist nicht bereit.")
            return

        # 2. Parameter auslesen und validieren
        try:
            params = {
                'start': float(self.le_start.text()),
                'end': float(self.le_end.text()),
                'step': float(self.le_step.text()),
                'is_voltage_sweep': self.rb_voltage.isChecked()
            }
            if params['step'] == 0:
                QMessageBox.warning(self, "Fehler", "Die Schrittweite darf nicht Null sein.")
                return
        except ValueError:
            QMessageBox.warning(self, "Fehler", "Bitte gültige Zahlen für alle Parameter eingeben.")
            return
            
        # 3. UI für den Sweep vorbereiten
        self._set_controls_enabled(False)
        self.is_sweeping = True
        self.btn_start_stop.setText("Sweep abbrechen")
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.x_data, self.y_data = [], [] # Alte Daten löschen
        self._update_plot() # Plot leeren

        # 4. Worker-Thread erstellen und starten
        self.thread = QThread()
        self.worker = SweepWorker(self.shared_data, params)
        self.worker.moveToThread(self.thread)

        # 5. Signale und Slots verbinden
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._sweep_finished)
        
        self.worker.newData.connect(self._on_new_data)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.error.connect(self._on_error)

        self.thread.start()

    def _stop_sweep(self):
        if hasattr(self, 'worker'):
            self.worker.stop()

    def _sweep_finished(self):
        """Wird aufgerufen, wenn der Thread endet (normal oder durch Abbruch)."""
        self.is_sweeping = False
        self.btn_start_stop.setText("Sweep starten")
        self.progress_bar.setVisible(False)
        self._set_controls_enabled(True)
        QMessageBox.information(self, "Info", "Sweep beendet.")

    def _on_error(self, message):
        QMessageBox.critical(self, "Sweep-Fehler", message)
        self._stop_sweep()

    def _on_new_data(self, x, y):
        self.x_data.append(x)
        self.y_data.append(y)
        self._update_plot()
        
    def _set_controls_enabled(self, enabled):
        """Aktiviert/Deaktiviert die Eingabefelder."""
        for widget in [self.le_start, self.le_end, self.le_step, self.rb_voltage, self.rb_current]:
            widget.setEnabled(enabled)

    def _update_plot(self):
        self.ax.clear()
        self._configure_plot()
        
        if self.rb_voltage.isChecked():
            self.ax.set_xlabel("Spannung (V)")
            self.ax.set_ylabel("Strom (A)")
            self.ax.set_title("I-V Kennlinie")
        else:
            self.ax.set_xlabel("Strom (A)")
            self.ax.set_ylabel("Spannung (V)")
            self.ax.set_title("V-I Kennlinie")
            
        self.ax.plot(self.x_data, self.y_data, 'o-', color='cyan')
        self.canvas.draw()