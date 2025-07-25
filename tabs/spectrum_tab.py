# el-workbench/tabs/spectrum_tab.py

# -*- coding: utf-8 -*-
"""
============================================================================
 File:          spectrum_tab.py
 Author:        Silas Hörz
 Creation date: 2025-06-25
 Last modified: 2025-07-18
 Version:       1.3.0
============================================================================
 Description:
    Modul (Tab) für die Ansteuerung eines Ocean Optics Spektrometers
    innerhalb des EL-Workbench.
============================================================================
 Change Log:
 - 2025-06-25: Initial version created. Refactored from single-file app.
 - 2025-07-18: Added device status log, enhanced connect/disconnect,
               and refined device selection refresh.
 - 2025-07-18: Implemented dummy mode with checkbox, simulated spectrum,
               integration time-dependent noise, and random variations.
 - 2025-07-18: Enhanced dummy noise model: adjustable strength and
               clearer integration time dependency (strong at 20ms, low at 1000ms).
 - 2025-07-18: Adapted dummy spectrum generation to simulate NIRQUEST512
               structure (wavelength range and number of points).
============================================================================
"""

import numpy as np
import matplotlib.pyplot as plt
import datetime # Für Zeitstempel im Log

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QHBoxLayout,
    QSpinBox, QMessageBox, QTextEdit, QSizePolicy, QCheckBox
)
from PyQt6.QtCore import QTimer, Qt, QEvent

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

import seabreeze
seabreeze.use('cseabreeze')
from seabreeze.spectrometers import Spectrometer, list_devices

class SpectrumTab(QWidget):
    """
    Ein QWidget-Tab zur Steuerung und Anzeige von Spektrometerdaten.
    """
    def __init__(self, shared_data):
        """
        Initialisiert den SpectrumTab.

        Args:
            shared_data: Ein Objekt, das gemeinsame Daten (z.B. das Spektrometer-Objekt)
                         zwischen verschiedenen Tabs oder Modulen enthält.
        """
        super().__init__()

        self.shared_data = shared_data
        self.devices = []
        self.integration_time_ms = 100 # Standard-Integrationszeit
        self.dummy_mode_active = False # Flag für den Dummy-Modus
        self.dummy_noise_strength = 50 # Standard-Rauschstärke für Dummy-Modus

        # --- NEU: Feste Wellenlängen für den Dummy-Modus basierend auf echten Daten ---
        # Diese Werte kommen aus dem JSON des NIRQUEST512:
        self.dummy_wavelengths = np.linspace(903.07996, 2527.059023186984, 512)
        # ----------------------------------------------------------------------

        self._init_timer()
        self._init_ui()
        self._log_message("Initialisierung des Spektrometer-Tabs abgeschlossen.")
        self.update_devices() # Geräte beim Start aktualisieren
        self.device_combo.installEventFilter(self) # Event Filter für die Combobox

        # Initialer Zustand der Steuerelemente (deaktiviert, da noch kein Gerät verbunden)
        self._set_controls_enabled(False)
        # Dummy-Checkbox initial aktiviert lassen
        self.dummy_mode_checkbox.setEnabled(True)

    def _init_timer(self):
        """Initialisiert den QTimer für die Spektrummessung."""
        self.spectrum_timer = QTimer(self)
        self.spectrum_timer.timeout.connect(self.update_spectrum)

    def _init_ui(self):
        """Initialisiert das User Interface des Tabs."""
        main_layout = QHBoxLayout(self)

        # Steuerungsbereich erstellen
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)

        # Plotbereich erstellen
        plot_panel = self._create_plot_panel()
        main_layout.addWidget(plot_panel, stretch=1)

    def _create_control_panel(self):
        """Erstellt und konfiguriert das Bedienfeld."""
        control_widget = QWidget()
        control_widget.setFixedWidth(300)
        control_layout = QVBoxLayout(control_widget)

        # Dummy-Modus Checkbox
        self.dummy_mode_checkbox = QCheckBox("Dummy-Modus aktivieren")
        self.dummy_mode_checkbox.clicked.connect(self._toggle_dummy_mode)
        control_layout.addWidget(self.dummy_mode_checkbox)

        # Rauschstärke für Dummy-Modus
        dummy_noise_layout = QHBoxLayout()
        dummy_noise_layout.addWidget(QLabel("Rauschstärke (Dummy):"))
        self.dummy_noise_spinbox = QSpinBox()
        self.dummy_noise_spinbox.setRange(0, 500)
        self.dummy_noise_spinbox.setValue(self.dummy_noise_strength)
        self.dummy_noise_spinbox.setSingleStep(10)
        self.dummy_noise_spinbox.valueChanged.connect(self._update_dummy_noise_strength)
        # Deaktiviert, solange Dummy-Modus nicht aktiv ist
        self.dummy_noise_spinbox.setEnabled(False)
        dummy_noise_layout.addWidget(self.dummy_noise_spinbox)
        control_layout.addLayout(dummy_noise_layout)


        # Geräteauswahl
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("Gerät:"))
        self.device_combo = QComboBox()
        device_layout.addWidget(self.device_combo)

        self.connect_button = QPushButton("Verbinden")
        self.connect_button.clicked.connect(self.toggle_device_connection)
        device_layout.addWidget(self.connect_button)
        control_layout.addLayout(device_layout)

        # Integrationszeit-Einstellung
        integration_layout = QHBoxLayout()
        integration_layout.addWidget(QLabel("Integration Time (ms):"))
        self.integration_spinbox = QSpinBox()
        self.integration_spinbox.setRange(10, 10000)
        self.integration_spinbox.setValue(self.integration_time_ms)
        integration_layout.addWidget(self.integration_spinbox)

        self.set_integration_button = QPushButton("Setzen")
        self.set_integration_button.clicked.connect(self.set_integration_time)
        integration_layout.addWidget(self.set_integration_button)
        control_layout.addLayout(integration_layout)

        # Messungs-Start/Stopp-Button
        self.start_measurement_button = QPushButton("Messung starten")
        self.start_measurement_button.clicked.connect(self.toggle_measurement)
        control_layout.addWidget(self.start_measurement_button)

        # Status/Log-Feld
        self.status_log_label = QLabel("Status/Log:")
        control_layout.addWidget(self.status_log_label)
        self.status_log_textedit = QTextEdit()
        self.status_log_textedit.setReadOnly(True)
        self.status_log_textedit.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        control_layout.addWidget(self.status_log_textedit)

        control_layout.addStretch() # Leerraum am Ende

        return control_widget

    def _create_plot_panel(self):
        """Erstellt und konfiguriert das Plot-Anzeigefeld."""
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)

        self.figure, self.ax = plt.subplots()
        self.figure.patch.set_facecolor("#00000000")
        self.ax.set_facecolor("#ffffff22")
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.title.set_color('white')

        self.canvas = FigureCanvas(self.figure)
        plot_layout.addWidget(self.canvas)

        return plot_widget

    def _log_message(self, message, level="INFO"):
        """Schreibt eine Nachricht mit Zeitstempel in das Log-Feld."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.status_log_textedit.append(log_entry)

    def _set_controls_enabled(self, enabled: bool):
        """Aktiviert oder deaktiviert die Steuerlemente für das Spektrometer."""
        self.device_combo.setEnabled(enabled)
        # connect_button wird durch toggle_device_connection gehandhabt, sollte aber klickbar sein, wenn nicht im dummy mode
        # self.connect_button.setEnabled(enabled)
        self.integration_spinbox.setEnabled(enabled)
        self.set_integration_button.setEnabled(enabled)
        self.start_measurement_button.setEnabled(enabled)
        # Dummy-Checkbox und Rauschstärke-Spinbox sollten immer aktiv sein
        self.dummy_mode_checkbox.setEnabled(True)
        self.dummy_noise_spinbox.setEnabled(self.dummy_mode_active) # Nur aktiv, wenn Dummy-Modus an

    def _update_dummy_noise_strength(self, value: int):
        """Aktualisiert die Rauschstärke für den Dummy-Modus."""
        self.dummy_noise_strength = value
        self._log_message(f"Dummy-Rauschstärke auf {value} gesetzt.")
        # Wenn Messung im Dummy-Modus läuft, sofort aktualisieren
        if self.spectrum_timer.isActive() and self.dummy_mode_active:
            self.update_spectrum()


    def _toggle_dummy_mode(self):
        """Schaltet den Dummy-Modus an/aus und aktualisiert den UI-Zustand."""
        self.dummy_mode_active = self.dummy_mode_checkbox.isChecked()
        self.dummy_noise_spinbox.setEnabled(self.dummy_mode_active) # Rauschstärke-Spinbox Zustand anpassen

        if self.dummy_mode_active:
            self._log_message("Dummy-Modus aktiviert. Spektrometer-Funktionen simuliert.", level="WARNING")
            # Deaktiviere echte Geräteauswahl, da wir im Dummy-Modus sind
            self.device_combo.setEnabled(False)
            self.connect_button.setText("Verbinden (Dummy)")
            self.connect_button.setEnabled(True) # Dummy "Verbinden" Button muss klickbar sein
            # Erzwinge das Trennen, falls ein echtes Spektrometer verbunden war
            if self.shared_data.spec and self.shared_data.spec != "DUMMY_SPEC_CONNECTED":
                self.close_device()
            # Aktiviere die Dummy-Steuerelemente
            self.integration_spinbox.setEnabled(True)
            self.set_integration_button.setEnabled(True)
            self.start_measurement_button.setEnabled(True)
            # Simuliere eine "Verbindung" zum Dummy
            self.shared_data.spec = "DUMMY_SPEC_CONNECTED" # Einfacher String als Indikator
            self._log_message("Dummy-Spektrometer verbunden.")

        else:
            self._log_message("Dummy-Modus deaktiviert. Versuche, echte Geräte zu erkennen.")
            # Trenne das Dummy-Spektrometer
            if self.shared_data.spec == "DUMMY_SPEC_CONNECTED":
                self.spectrum_timer.stop()
                self.start_measurement_button.setText("Messung starten")
                self.shared_data.spec = None
                self._log_message("Dummy-Spektrometer getrennt.")
                # Plot zurücksetzen, da jetzt nichts verbunden ist
                self.ax.clear()
                self.ax.set_xlabel("Wellenlänge [nm]")
                self.ax.set_ylabel("Intensität [a.u.]")
                self.ax.set_title("Live Spektrum (nicht verbunden)")
                self.ax.grid(True, linestyle='--', alpha=0.6)
                self.canvas.draw()


            # Aktiviere echte Geräteauswahl und aktualisiere
            self.update_devices()
            # _set_controls_enabled kümmert sich um den Zustand basierend auf update_devices
            self._set_controls_enabled(False) # Deaktiviere alle bis ein echtes Gerät gefunden/verbunden ist
            if self.devices: # Wenn echte Geräte gefunden wurden, Verbinden-Button aktivieren
                self.connect_button.setEnabled(True)
            self.connect_button.setText("Verbinden") # Standardtext


    def eventFilter(self, obj, event):
        """
        Event-Filter, um Aktionen auszuführen, wenn die Combobox geöffnet wird.
        """
        if obj is self.device_combo and event.type() == QEvent.Type.Show:
            # Nur aktualisieren, wenn nicht im Dummy-Modus
            if not self.dummy_mode_active:
                self._log_message("Geräteliste wird aktualisiert...")
                self.update_devices()
            return True # Event wurde behandelt
        return super().eventFilter(obj, event)

    def update_devices(self):
        """Aktualisiert die Liste der verfügbaren Spektrometer."""
        if self.dummy_mode_active:
            # Im Dummy-Modus zeigen wir keine echten Geräte an
            self.device_combo.clear()
            self.device_combo.addItem("DUMMY Spectrometer (SIMULATED)")
            self.connect_button.setEnabled(True) # Immer "verbindbar" im Dummy-Modus
            return

        # Logik für echte Geräte
        current_selection_text = self.device_combo.currentText()
        self.device_combo.clear()
        try:
            self.devices = list_devices()
        except Exception as e:
            self._log_message(f"Geräte konnten nicht geladen werden: {e}", level="ERROR")
            self.connect_button.setEnabled(False) # Deaktiviere, wenn Fehler
            return

        if not self.devices:
            self.device_combo.addItem("Keine Geräte gefunden")
            self.connect_button.setEnabled(False)
            self._log_message("Keine echten Spektrometer gefunden.")
        else:
            for dev in self.devices:
                self.device_combo.addItem(f"{dev.model} ({dev.serial_number})")
            self.connect_button.setEnabled(True)
            self._log_message(f"{len(self.devices)} echte Spektrometer gefunden.")

            # Auswahl wiederherstellen
            index = self.device_combo.findText(current_selection_text)
            if index != -1:
                self.device_combo.setCurrentIndex(index)
            elif self.shared_data.spec and not self.dummy_mode_active: # Wenn ein echtes Gerät verbunden ist
                connected_dev_str = f"{self.shared_data.spec.model} ({self.shared_data.spec.serial_number})"
                index = self.device_combo.findText(connected_dev_str)
                if index != -1:
                    self.device_combo.setCurrentIndex(index)


    def toggle_device_connection(self):
        """Schaltet die Verbindung zum Spektrometer um (Verbinden/Trennen)."""
        if self.dummy_mode_active:
            # Im Dummy-Modus simulieren wir das Verbinden/Trennen
            if self.shared_data.spec == "DUMMY_SPEC_CONNECTED":
                self.close_device() # Nutze close_device, um den Zustand zurückzusetzen
            else:
                # Simuliere das "Verbinden" des Dummy-Specs
                self.shared_data.spec = "DUMMY_SPEC_CONNECTED"
                self.connect_button.setText("Trennen (Dummy)")
                self._log_message("Dummy-Spektrometer 'verbunden'.")
                # Aktiviere Steuerelemente für Dummy
                self.integration_spinbox.setEnabled(True)
                self.set_integration_button.setEnabled(True)
                self.start_measurement_button.setEnabled(True)
                # Setze Integrationszeit zurück und Logge
                self.integration_spinbox.setValue(self.integration_time_ms)
                self._log_message(f"Integrationszeit (Dummy) auf {self.integration_time_ms} ms gesetzt.")

            return # Wichtig: Hier aufhören, um die echte Logik nicht auszuführen

        # Echte Geräte-Logik
        if self.shared_data.spec is None:
            self.open_device()
        else:
            self.close_device()

    def open_device(self):
        """Öffnet das ausgewählte Spektrometergerät."""
        # Diese Methode wird nur für echte Geräte aufgerufen
        index = self.device_combo.currentIndex()
        if index < 0 or index >= len(self.devices):
            self._log_message("Kein gültiges Gerät ausgewählt.", level="WARNING")
            return

        try:
            if self.shared_data.spec:
                self.shared_data.spec.close()
                self.shared_data.spec = None

            self.shared_data.spec = Spectrometer(self.devices[index])
            self._log_message(f"Gerät verbunden: {self.shared_data.spec.model} ({self.shared_data.spec.serial_number})")
            self.connect_button.setText("Trennen")
            self._set_controls_enabled(True)
            self.dummy_mode_checkbox.setEnabled(True) # Dummy-Checkbox bleibt aktiv
            self.dummy_noise_spinbox.setEnabled(False) # Rauschstärke-Spinbox deaktivieren, da nicht im Dummy-Modus

            try:
                self.shared_data.spec.integration_time_micros(self.integration_time_ms * 1000)
                self._log_message(f"Integrationszeit auf {self.integration_time_ms} ms gesetzt (Standard).")
            except Exception as e:
                self._log_message(f"Konnte Standard-Integrationszeit nicht setzen: {e}", level="WARNING")

        except Exception as e:
            self._log_message(f"Gerät konnte nicht geöffnet werden: {e}", level="ERROR")
            self.shared_data.spec = None
            self.connect_button.setText("Verbinden")
            self._set_controls_enabled(False) # Deaktiviere alle Steuerelemente
            self.dummy_mode_checkbox.setEnabled(True) # Dummy-Checkbox bleibt aktiv


    def close_device(self):
        """Schließt die Verbindung zum Spektrometer."""
        # Stoppe Timer und setze Mess-Button zurück, falls aktiv
        self.spectrum_timer.stop()
        self.start_measurement_button.setText("Messung starten")
        self._log_message("Messung gestoppt.")

        # Wenn Dummy-Modus aktiv, behandle Dummy-Spektrometer
        if self.dummy_mode_active:
            if self.shared_data.spec == "DUMMY_SPEC_CONNECTED":
                self.shared_data.spec = None
                self.connect_button.setText("Verbinden (Dummy)")
                self._log_message("Dummy-Spektrometer 'getrennt'.")
                # Deaktiviere Mess- und Integrationszeit-Steuerung für Dummy
                self.integration_spinbox.setEnabled(False)
                self.set_integration_button.setEnabled(False)
                self.start_measurement_button.setEnabled(False)
            else:
                self._log_message("Kein Dummy-Spektrometer zum Trennen verbunden.", level="WARNING")
            # Unabhängig vom Status, Dummy-Modus spezifische UI-Anpassungen beibehalten
            self.device_combo.setEnabled(False)
            self.connect_button.setEnabled(True) # Dummy "Verbinden" Button bleibt aktiv
            self.dummy_noise_spinbox.setEnabled(True) # Dummy-Rauschstärke bleibt aktiv
            self._log_message("Plot zurückgesetzt (Dummy-Modus deaktiviert oder getrennt).")


        # Wenn echter Spektrometer verbunden
        elif self.shared_data.spec:
            try:
                self.shared_data.spec.close()
                self._log_message(f"Gerät getrennt: {self.shared_data.spec.model}")
                self.shared_data.spec = None
                self.connect_button.setText("Verbinden")
                self._set_controls_enabled(False) # Deaktiviere alle Steuerelemente
                self.dummy_mode_checkbox.setEnabled(True) # Dummy-Checkbox bleibt aktiv
                self.dummy_noise_spinbox.setEnabled(False) # Rauschstärke-Spinbox deaktivieren
                self._log_message("Plot zurückgesetzt (Gerät getrennt).")
            except Exception as e:
                self._log_message(f"Fehler beim Trennen des Geräts: {e}", level="ERROR")
        else:
            self._log_message("Kein Spektrometer zum Trennen verbunden.", level="WARNING")

        # Plot zurücksetzen (unabhängig davon, ob Dummy oder echt)
        self.ax.clear()
        self.ax.set_xlabel("Wellenlänge [nm]")
        self.ax.set_ylabel("Intensität [a.u.]")
        self.ax.set_title("Live Spektrum (nicht verbunden)")
        self.ax.grid(True, linestyle='--', alpha=0.6)
        self.canvas.draw()


    def set_integration_time(self):
        """Stellt die Integrationszeit des Spektrometers ein."""
        if self.shared_data.spec is None:
            self._log_message("Zuerst ein Spektrometer verbinden!", level="WARNING")
            return

        integration_time_ms = self.integration_spinbox.value()
        if self.dummy_mode_active:
            self.integration_time_ms = integration_time_ms
            self._log_message(f"Integrationszeit (Dummy) auf {integration_time_ms} ms gesetzt.")
            # Wenn Messung im Dummy-Modus läuft, sofort aktualisieren, um Rauschen anzupassen
            if self.spectrum_timer.isActive():
                self.update_spectrum()
        else:
            # Echte Logik
            try:
                self.shared_data.spec.integration_time_micros(integration_time_ms * 1000)
                self.integration_time_ms = integration_time_ms
                self._log_message(f"Integrationszeit auf {integration_time_ms} ms gesetzt.")
            except Exception as e:
                self._log_message(f"Konnte Integrationszeit nicht setzen: {e}", level="ERROR")

    def toggle_measurement(self):
        """Startet oder stoppt die kontinuierliche Spektrummessung."""
        if self.spectrum_timer.isActive():
            self.spectrum_timer.stop()
            self.start_measurement_button.setText("Messung starten")
            self._log_message("Messung gestoppt.")
        else:
            if self.shared_data.spec is None:
                self._log_message("Bitte zuerst ein Gerät verbinden!", level="WARNING")
                return
            self._log_message("Messung gestartet.")
            # Erste Messung sofort ausführen, dann Timer starten
            self.update_spectrum()
            self.spectrum_timer.start(self.integration_time_ms)
            self.start_measurement_button.setText("Messung stoppen")


    def update_spectrum(self):
        """Holt die aktuellen Spektrumdaten und aktualisiert den Plot."""
        if self.shared_data.spec is None:
            self.spectrum_timer.stop()
            self.start_measurement_button.setText("Messung starten")
            self._log_message("Messung automatisch gestoppt: Spektrometer nicht mehr verbunden.", level="WARNING")
            return

        if self.dummy_mode_active:
            wavelengths, intensities = self._generate_dummy_spectrum()
            self.shared_data.intensities = intensities
            self.shared_data.wavelengths = wavelengths
        else:
            # Echte Spektrometer-Logik
            try:
                intensities = self.shared_data.spec.intensities()
                wavelengths = self.shared_data.spec.wavelengths()

                self.shared_data.intensities = intensities
                self.shared_data.wavelengths = wavelengths

            except Exception as e:
                self.spectrum_timer.stop()
                self.start_measurement_button.setText("Messung starten")
                self._log_message(f"Messung fehlgeschlagen: {e}", level="ERROR")
                self.shared_data.spec = None
                self.connect_button.setText("Verbinden")
                self._set_controls_enabled(False)
                self.dummy_mode_checkbox.setEnabled(True) # Dummy-Checkbox bleibt aktiv
                self.dummy_noise_spinbox.setEnabled(False) # Rauschstärke-Spinbox deaktivieren
                return

        # Plot aktualisieren (gemeinsam für Dummy und Echt)
        self.ax.clear()
        self.ax.plot(wavelengths, intensities, color='cyan')
        self.ax.set_xlabel("Wellenlänge [nm]")
        self.ax.set_ylabel("Intensität [a.u.]")
        self.ax.set_title("Live Spektrum (Dummy-Modus)" if self.dummy_mode_active else "Live Spektrum")
        self.ax.grid(True, linestyle='--', alpha=0.6)
        self.ax.legend(["Spektrum"])
        self.canvas.draw()

    def _generate_dummy_spectrum(self):
        """
        Generiert ein simuliertes Spektrum mit der Struktur der echten Messung
        (NIRQUEST512 Wellenlängenbereich und 512 Punkte) und relevanten NIR-Peaks.
        """
        # Verwende die vordefinierten dummy_wavelengths (von 903nm bis 2527nm, 512 Punkte)
        wavelengths = self.dummy_wavelengths
        num_points = len(wavelengths)
        intensities = np.zeros(num_points)

        # Grundrauschen und Hintergrund (Anpassung für NIR-Spektrum, das oft weniger "dunkel" ist)
        baseline = 1000 + np.random.rand(num_points) * 500 # Beispiel für eine leicht schwankende Basislinie im NIR

        # Funktion zum Hinzufügen von Gaußschen Peaks
        def gaussian(x, amplitude, mean, stddev):
            return amplitude * np.exp(-((x - mean) / stddev)**2 / 2)

        # Beispiel-Peaks für den NIR-Bereich (Anpassung je nach dem, was du simulieren möchtest)
        # Typische NIR-Absorptionsbanden können von O-H, C-H, N-H Obertönen und Kombinationsbanden stammen.
        # Hier einige fiktive, aber plausible Peaks im NIR-Bereich:

        # Peak 1: Erste Obertöne von C-H (ca. 1700-1800 nm)
        intensities += gaussian(wavelengths, 25000, 1720, 30)
        # Peak 2: Zweite Obertöne von O-H (ca. 1400-1500 nm, Wasserabsorption)
        intensities += gaussian(wavelengths, 35000, 1450, 40)
        # Peak 3: C-H Kombinationsbande (ca. 2300-2400 nm)
        intensities += gaussian(wavelengths, 20000, 2350, 50)
        # Peak 4: Kleinere Bande (z.B. N-H Obertöne, ca. 2000-2100 nm)
        intensities += gaussian(wavelengths, 10000, 2050, 25)

        # Addiere die Baseline zum Spektrum
        intensities += baseline

        # Überlagertes Rauschen basierend auf Integrationszeit und einstellbarer Stärke
        # Skalierung: Bei kurzer Integrationszeit (z.B. 20ms) soll das Rauschen stärker sein,
        # bei langer Integrationszeit (z.B. 1000ms) soll es geringer sein.
        # Eine inverse Beziehung, z.B. 1/sqrt(integration_time) ist oft realistisch für Schrotrauschen.
        # Hier verwenden wir eine logarithmisch-inverse Skalierung, um den Effekt zu betonen.
        # Wir wollen einen deutlichen Unterschied zwischen 20ms (viel Rauschen) und 1000ms (wenig Rauschen).
        # Eine einfache lineare Abnahme des Rauschfaktors mit der Integrationszeit (im Verhältnis zu einem Referenzwert)
        # und einer Basis-Rauschkomponente, die immer vorhanden ist.

        # Normalize integration time relative to a baseline (e.g., 100ms)
        # Max noise at 20ms, min noise at 10000ms (max spinbox value)
        min_integration_time = 20 # ms (earliest time where noise is high)
        max_integration_time = 10000 # ms (latest time where noise is low)

        # Calculate a noise factor that decreases as integration time increases
        # Using a clamped linear inverse, or more smoothly:
        if self.integration_time_ms <= min_integration_time:
            noise_factor_integration = 1.0 # Max noise at or below min_integration_time
        else:
            # Interpolate between 1.0 and 0.1 (or less) as time increases
            # We want noise to decrease, e.g., from 1.0 at 20ms to 0.1 at 1000ms, and even less for 10000ms
            # Using a reciprocal scaling: factor = (min_time / current_time) ^ power
            # For 1/sqrt(t) like behavior, power = 0.5
            noise_factor_integration = (min_integration_time / self.integration_time_ms)**0.7
            noise_factor_integration = max(0.05, noise_factor_integration) # Clamp minimum noise factor


        # Die einstellbare Rauschstärke multipliziert den Rauschfaktor
        final_noise_amplitude = self.dummy_noise_strength * noise_factor_integration
        random_noise = np.random.normal(0, final_noise_amplitude, num_points)
        intensities += random_noise

        # Sicherstellen, dass Intensitäten nicht negativ werden
        intensities[intensities < 0] = 0

        return wavelengths, intensities