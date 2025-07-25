# -*- coding: utf-8 -*-

"""
GUI-Controller für Keithley 2602 SourceMeter via RS-232.

Diese Anwendung bietet eine grafische Benutzeroberfläche zur Steuerung
beider Kanäle eines Keithley 2602.

Struktur:
- Keithley2602: Klasse für die serielle Kommunikation und Befehlslogik.
- KeithleyGUI: PyQt6-Klasse für die Benutzeroberfläche.
"""

import sys
import time
import serial
from serial.tools import list_ports

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton, QComboBox, QRadioButton,
    QMessageBox, QSplitter, QButtonGroup
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator, QFont, QPalette, QColor

# Konstanten für die Befehle, um die Lesbarkeit zu verbessern
# (entsprechen den Werten in der Keithley TSP-Sprache)
TSP_SMU_OFF = 'OUTPUT_OFF'
TSP_SMU_ON = 'OUTPUT_ON'
TSP_DC_VOLTS = 'OUTPUT_DCVOLTS'
TSP_DC_AMPS = 'OUTPUT_DCAMPS'
TSP_SENSE_LOCAL = 'SENSE_LOCAL'    # 2-Draht
TSP_SENSE_REMOTE = 'SENSE_REMOTE'  # 4-Draht


class Keithley2602:
    """
    Diese Klasse handhabt die RS-232 Kommunikation mit dem Keithley 2602.
    Sie sendet und empfängt TSP-Befehle (Test Script Processor).
    """
    def __init__(self):
        self.ser = serial.Serial()
        self.ser.timeout = 2  # Timeout für Lesevorgänge in Sekunden

    def connect(self, port: str, baudrate: int = 115200) -> (bool, str):
        """Stellt die serielle Verbindung her."""
        if self.ser.is_open:
            self.disconnect()
        try:
            self.ser.port = port
            self.ser.baudrate = baudrate
            self.ser.open()
            # Nach dem Öffnen schickt das Keithley oft eine Willkommensnachricht.
            # Wir lesen sie, um den Puffer zu leeren.
            time.sleep(0.1)
            self.ser.read_all()
            # Testbefehl, um die Verbindung zu verifizieren
            self.send_command("*IDN?")
            response = self.read_response()
            #if "KEITHLEY" in response:
                # Lokales Echo deaktivieren für saubere Kommunikation
            self.send_command("_G.remote_echo=0")
            return True, response.strip()
            #else:
                #self.disconnect()
                #return False, "Gerät antwortet nicht wie erwartet."
        except serial.SerialException as e:
            return False, f"Verbindungsfehler: {e}"

    def disconnect(self):
        """Schließt die serielle Verbindung."""
        if self.ser.is_open:
            self.ser.close()

    def send_command(self, command: str):
        """Sendet einen Befehl an das Gerät."""
        if self.ser.is_open:
            # Befehle müssen mit einem Newline-Zeichen enden
            full_command = command + '\n'
            self.ser.write(full_command.encode('ascii'))
            # Kurze Pause, damit das Gerät den Befehl verarbeiten kann
            time.sleep(0.05)
        else:
            raise ConnectionError("Keine Verbindung zum Gerät.")

    def read_response(self) -> str:
        """Liest eine Antwort vom Gerät."""
        if self.ser.is_open:
            return self.ser.readline().decode('ascii').strip()
        return ""

    def query(self, command: str) -> str:
        """Sendet einen Befehl und liest die direkte Antwort (für 'print()')."""
        self.send_command(command)
        return self.read_response()
        
    def reset_channel(self, channel: str):
        """Setzt den angegebenen Kanal zurück."""
        self.send_command(f"smu{channel}.reset()")

    def set_source_function(self, channel: str, func: str):
        """Setzt die Source-Funktion (Spannung oder Strom)."""
        self.send_command(f"smu{channel}.source.func = smu{channel}.{func}")
        
    ##????????????????????????????????
    def set_sense_mode(self, channel: str, mode: str):
        """Setzt den Sense-Modus (2- oder 4-Draht)."""
        self.send_command(f"smu{channel}.sense = {mode}")

    def set_source_level(self, channel: str, func: str, level: float):
        """Setzt den Source-Pegel für Spannung oder Strom."""
        level_cmd = 'levelv' if func == TSP_DC_VOLTS else 'leveli'
        self.send_command(f"smu{channel}.source.{level_cmd} = {level}")

    def set_source_limit(self, channel: str, func: str, limit: float):
        """Setzt das Limit für Spannung oder Strom."""
        limit_cmd = 'limiti' if func == TSP_DC_VOLTS else 'limitv'
        self.send_command(f"smu{channel}.source.{limit_cmd} = {limit}")
        
    def set_output_state(self, channel: str, state: str):
        """Schaltet den Ausgang ein oder aus."""
        self.send_command(f"smu{channel}.source.output = smu{channel}.{state}")

    def measure_voltage(self, channel: str) -> float:
        """Misst die Spannung."""
        response = self.query(f"print(smu{channel}.measure.v())")
        return float(response)

    def measure_current(self, channel: str) -> float:
        """Misst den Strom."""
        response = self.query(f"print(smu{channel}.measure.i())")
        return float(response)

    def measure_iv(self, channel: str) -> (float, float):
        """Misst Strom und Spannung gleichzeitig."""
        response = self.query(f"print(smu{channel}.measure.iv())")
        # Antwort ist z.B. "1.234e-03\t5.000e+00"
        parts = response.split('\t')
        return float(parts[0]), float(parts[1]) # Strom, Spannung


class KeithleyGUI(QMainWindow):
    """
    Hauptfenster der Anwendung zur Steuerung des Keithley 2602.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Keithley 2602 GUI Controller")
        self.setGeometry(100, 100, 900, 600)

        self.keithley = Keithley2602()
        self.channel_widgets = {} # Speichert Widgets für jeden Kanal
        self.channel_output_state = {'a': False, 'b': False}

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self._create_com_port_ui()
        self._create_channel_ui()
        
        # Initial alle Kanal-Steuerelemente deaktivieren
        self._set_channel_controls_enabled(False)

    def _create_com_port_ui(self):
        """Erstellt den oberen Bereich für die COM-Port-Steuerung."""
        com_groupbox = QGroupBox("Allgemeine Funktionen / COM Port")
        com_layout = QHBoxLayout()
        
        com_layout.addWidget(QLabel("COM Port:"))
        self.com_port_combo = QComboBox()
        self.com_port_combo.addItems([port.device for port in list_ports.comports()])
        com_layout.addWidget(self.com_port_combo)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._refresh_com_ports)
        com_layout.addWidget(self.refresh_button)

        self.connect_button = QPushButton("Verbinden")
        self.connect_button.clicked.connect(self._connect_keithley)
        com_layout.addWidget(self.connect_button)

        self.disconnect_button = QPushButton("Trennen")
        self.disconnect_button.clicked.connect(self._disconnect_keithley)
        self.disconnect_button.setEnabled(False)
        com_layout.addWidget(self.disconnect_button)
        
        com_layout.addStretch()

        self.status_label = QLabel("Status: Nicht verbunden")
        font = QFont()
        font.setBold(True)
        self.status_label.setFont(font)
        self._update_status_color(False)
        com_layout.addWidget(self.status_label)

        com_groupbox.setLayout(com_layout)
        self.main_layout.addWidget(com_groupbox)

    def _create_channel_ui(self):
        """Erstellt den geteilten Bereich für die beiden Kanäle."""
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        channel_a_group = self._create_single_channel_ui('a')
        channel_b_group = self._create_single_channel_ui('b')
        
        splitter.addWidget(channel_a_group)
        splitter.addWidget(channel_b_group)
        splitter.setSizes([400, 400]) # Anfangsgröße

        self.main_layout.addWidget(splitter)
    
    def _create_single_channel_ui(self, channel_id: str) -> QGroupBox:
        """Erstellt die UI-Elemente für einen einzelnen SMU-Kanal."""
        channel_group = QGroupBox(f"Channel {channel_id.upper()}")
        main_v_layout = QVBoxLayout()
        
        # --- Source Konfiguration ---
        source_group = QGroupBox("Source")
        source_layout = QGridLayout()

    

        # --- NEU: Button-Gruppen erstellen, um die Radio-Buttons zu entkoppeln ---
        self.source_func_group = QButtonGroup(source_group)
        self.sense_mode_group = QButtonGroup(source_group)
        # --------------------------------------------------------------------

        # Source Funktion (Spannung/Strom)
        source_layout.addWidget(QLabel("Funktion:"), 0, 0)
        rb_voltage = QRadioButton("Spannung (V)")
        rb_voltage.setChecked(True)
        rb_current = QRadioButton("Strom (A)")
        source_layout.addWidget(rb_voltage, 0, 1)
        source_layout.addWidget(rb_current, 0, 2)
        
        # --- NEU: Buttons der ersten Gruppe hinzufügen ---
        self.source_func_group.addButton(rb_voltage)
        self.source_func_group.addButton(rb_current)
        # -----------------------------------------------
        
        # Source Level
        source_layout.addWidget(QLabel("Source Level:"), 1, 0)
        level_input = QLineEdit("0")
        level_input.setValidator(QDoubleValidator())
        source_layout.addWidget(level_input, 1, 1, 1, 2)
        
        # Source Limit
        source_layout.addWidget(QLabel("Limit:"), 2, 0)
        limit_input = QLineEdit("0.01")
        limit_input.setValidator(QDoubleValidator())
        source_layout.addWidget(limit_input, 2, 1, 1, 2)

        # Set Settings
        set_settings_btn = QPushButton("Einstellungen übernehmen")
        set_settings_btn.clicked.connect(lambda _, ch=channel_id: self._apply_source_settings(ch))
        source_layout.addWidget(set_settings_btn, 4, 0)
    
        
        # Sense Mode
        source_layout.addWidget(QLabel("Sense Mode:"), 3, 0)
        sense_local = QRadioButton("Local (2-Draht)")
        sense_local.setChecked(True)
        sense_remote = QRadioButton("Remote (4-Draht)")
        source_layout.addWidget(sense_local, 3, 1)
        source_layout.addWidget(sense_remote, 3, 2)

        self.sense_mode_group.addButton(rb_voltage)
        self.sense_mode_group.addButton(rb_current)

        source_group.setLayout(source_layout)
        main_v_layout.addWidget(source_group)
        
        # --- Messungen ---
        measure_group = QGroupBox("Messergebnisse")
        measure_layout = QGridLayout()

        measure_v_btn = QPushButton("Spannung messen")
        measure_v_btn.clicked.connect(lambda _, ch=channel_id: self._measure_voltage(ch))
        measure_layout.addWidget(measure_v_btn, 0, 0)
        v_read_label = QLabel("--- V")
        measure_layout.addWidget(v_read_label, 0, 1)
        
        measure_i_btn = QPushButton("Strom messen")
        measure_i_btn.clicked.connect(lambda _, ch=channel_id: self._measure_current(ch))
        measure_layout.addWidget(measure_i_btn, 1, 0)
        i_read_label = QLabel("--- A")
        measure_layout.addWidget(i_read_label, 1, 1)

        measure_iv_btn = QPushButton("I & V messen")
        measure_iv_btn.clicked.connect(lambda _, ch=channel_id: self._measure_iv(ch))
        measure_layout.addWidget(measure_iv_btn, 2, 0)
        
        measure_group.setLayout(measure_layout)
        main_v_layout.addWidget(measure_group)

        # --- Output Steuerung ---
        output_group = QGroupBox("Steuerung")
        output_layout = QHBoxLayout()
        output_btn = QPushButton("OUTPUT ON")
        output_btn.setCheckable(True)
        output_btn.clicked.connect(lambda _, ch=channel_id: self._toggle_output(ch))
        output_layout.addWidget(output_btn)
        
        reset_btn = QPushButton("Reset Channel")
        reset_btn.clicked.connect(lambda _, ch=channel_id: self._reset_channel(ch))
        output_layout.addWidget(reset_btn)

        output_group.setLayout(output_layout)
        main_v_layout.addWidget(output_group)

        main_v_layout.addStretch()
        channel_group.setLayout(main_v_layout)

        # Widgets für späteren Zugriff speichern
        self.channel_widgets[channel_id] = {
            'group': channel_group,
            'rb_voltage': rb_voltage,
            'rb_current': rb_current,
            'level_input': level_input,
            'limit_input': limit_input,
            'sense_local': sense_local,
            'sense_remote': sense_remote,
            'v_read_label': v_read_label,
            'i_read_label': i_read_label,
            'output_btn': output_btn,
        }
        
        return channel_group
        
    def _refresh_com_ports(self):
        """Aktualisiert die Liste der verfügbaren COM-Ports."""
        self.com_port_combo.clear()
        self.com_port_combo.addItems([port.device for port in list_ports.comports()])

    def _update_status_color(self, connected: bool):
        """Ändert die Farbe des Status-Labels."""
        palette = self.status_label.palette()
        color = QColor("green") if connected else QColor("red")
        palette.setColor(QPalette.ColorRole.WindowText, color)
        self.status_label.setPalette(palette)

    def _connect_keithley(self):
        """Stellt die Verbindung her und aktualisiert die GUI."""
        port = self.com_port_combo.currentText()
        if not port:
            QMessageBox.warning(self, "Verbindungsfehler", "Kein COM-Port ausgewählt.")
            return
            
        is_connected, message = self.keithley.connect(port)
        if is_connected:
            self.status_label.setText(f"Status: Verbunden mit {message.split(',')[1]}")
            self._update_status_color(True)
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            self.com_port_combo.setEnabled(False)
            self.refresh_button.setEnabled(False)
            self._set_channel_controls_enabled(True)
        else:
            self.status_label.setText("Status: Nicht verbunden")
            self._update_status_color(False)
            QMessageBox.critical(self, "Verbindungsfehler", message)
    
    def _disconnect_keithley(self):
        """Trennt die Verbindung und aktualisiert die GUI."""
        # Sicherheitshalber alle Ausgänge ausschalten
        try:
            self.keithley.set_output_state('a', TSP_SMU_OFF)
            self.keithley.set_output_state('b', TSP_SMU_OFF)
        except ConnectionError:
            pass # Verbindung ist vielleicht schon weg

        self.keithley.disconnect()
        self.status_label.setText("Status: Nicht verbunden")
        self._update_status_color(False)
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.com_port_combo.setEnabled(True)
        self.refresh_button.setEnabled(True)
        self._set_channel_controls_enabled(False)
        
        # Output-Buttons zurücksetzen
        for ch_id in ['a', 'b']:
            self.channel_widgets[ch_id]['output_btn'].setChecked(False)
            self.channel_widgets[ch_id]['output_btn'].setText("OUTPUT ON")
            self.channel_output_state[ch_id] = False


    def _set_channel_controls_enabled(self, enabled: bool):
        """Aktiviert oder deaktiviert alle Steuerelemente der Kanäle."""
        for channel in self.channel_widgets.values():
            channel['group'].setEnabled(enabled)

    def _apply_source_settings(self, channel_id: str):
        """Liest die GUI-Einstellungen und sendet sie an das Gerät."""
        widgets = self.channel_widgets[channel_id]
        
        # 1. Sense Mode
        sense_mode = TSP_SENSE_LOCAL if widgets['sense_local'].isChecked() else TSP_SENSE_REMOTE
        self.keithley.set_sense_mode(channel_id, sense_mode)

        # 2. Source Funktion, Level und Limit
        is_voltage_source = widgets['rb_voltage'].isChecked()
        func = TSP_DC_VOLTS if is_voltage_source else TSP_DC_AMPS
        self.keithley.set_source_function(channel_id, func)
        
        try:
            level = float(widgets['level_input'].text())
            limit = float(widgets['limit_input'].text())
            self.keithley.set_source_level(channel_id, func, level)
            self.keithley.set_source_limit(channel_id, func, limit)
        except (ValueError, ConnectionError) as e:
            QMessageBox.critical(self, "Eingabefehler", f"Ungültiger Wert oder Verbindungsfehler: {e}")
            return False
            
        return True

    def _toggle_output(self, channel_id: str):
        """Schaltet den Ausgang eines Kanals ein oder aus."""
        widgets = self.channel_widgets[channel_id]
        button = widgets['output_btn']
        
        # Neuer Zustand ist der Gegenteil des aktuellen
        new_state_on = not self.channel_output_state[channel_id]
        
        try:
            if new_state_on:
                # VOR dem Einschalten alle Einstellungen anwenden
                if not self._apply_source_settings(channel_id):
                    button.setChecked(False) # Toggle zurücksetzen
                    return
                self.keithley.set_output_state(channel_id, TSP_SMU_ON)
                button.setText("OUTPUT OFF")
            else:
                self.keithley.set_output_state(channel_id, TSP_SMU_OFF)
                button.setText("OUTPUT ON")
                
            self.channel_output_state[channel_id] = new_state_on
            button.setChecked(new_state_on)

        except ConnectionError as e:
            QMessageBox.critical(self, "Verbindungsfehler", str(e))
            self._disconnect_keithley()

    def _reset_channel(self, channel_id: str):
        """Setzt einen Kanal zurück und aktualisiert die GUI."""
        try:
            self.keithley.reset_channel(channel_id)
            # Nach dem Reset sind die Ausgänge aus
            self.channel_output_state[channel_id] = False
            btn = self.channel_widgets[channel_id]['output_btn']
            btn.setChecked(False)
            btn.setText("OUTPUT ON")
            QMessageBox.information(self, "Reset", f"Kanal {channel_id.upper()} wurde zurückgesetzt.")
        except ConnectionError as e:
            QMessageBox.critical(self, "Verbindungsfehler", str(e))
            self._disconnect_keithley()
            
    def _measure_voltage(self, channel_id: str):
        """Führt eine Spannungsmessung durch und zeigt das Ergebnis an."""
        try:
            voltage = self.keithley.measure_voltage(channel_id)
            self.channel_widgets[channel_id]['v_read_label'].setText(f"{voltage:.4e} V")
        except (ValueError, ConnectionError) as e:
            self.channel_widgets[channel_id]['v_read_label'].setText("Fehler")
            QMessageBox.warning(self, "Messfehler", f"Spannungsmessung fehlgeschlagen: {e}")

    def _measure_current(self, channel_id: str):
        """Führt eine Strommessung durch und zeigt das Ergebnis an."""
        try:
            current = self.keithley.measure_current(channel_id)
            self.channel_widgets[channel_id]['i_read_label'].setText(f"{current:.4e} A")
        except (ValueError, ConnectionError) as e:
            self.channel_widgets[channel_id]['i_read_label'].setText("Fehler")
            QMessageBox.warning(self, "Messfehler", f"Strommessung fehlgeschlagen: {e}")

    def _measure_iv(self, channel_id: str):
        """Führt eine kombinierte I/V-Messung durch."""
        try:
            current, voltage = self.keithley.measure_iv(channel_id)
            self.channel_widgets[channel_id]['i_read_label'].setText(f"{current:.4e} A")
            self.channel_widgets[channel_id]['v_read_label'].setText(f"{voltage:.4e} V")
        except (ValueError, ConnectionError) as e:
            self.channel_widgets[channel_id]['i_read_label'].setText("Fehler")
            self.channel_widgets[channel_id]['v_read_label'].setText("Fehler")
            QMessageBox.warning(self, "Messfehler", f"I/V-Messung fehlgeschlagen: {e}")

    def closeEvent(self, event):
        """Sicherstellen, dass die Verbindung beim Schließen getrennt wird."""
        if self.keithley.ser.is_open:
            self._disconnect_keithley()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = KeithleyGUI()
    window.show()
    sys.exit(app.exec())