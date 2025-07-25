# el-workbench/tabs/smu_tab.py

# -*- coding: utf-8 -*-
"""
============================================================================
 File:          smu_tab.py
 Author:        Silas Hörz
 Creation date: 2025-07-04
 Version:       1.0.0
============================================================================
 Description:
     Modul (Tab) für die Ansteuerung einer Keithley 26xx Source-Measure Unit
     (SMU) innerhalb des EL-Workbench.
============================================================================
"""
import sys
import time
import serial
from serial.tools import list_ports
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel,
    QLineEdit, QPushButton, QComboBox, QRadioButton, QMessageBox, QSplitter,
    QButtonGroup, QTextEdit, QSizePolicy, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QDoubleValidator, QFont, QPalette, QColor

# Konstanten für die Befehle
TSP_SMU_OFF = 'OUTPUT_OFF'
TSP_SMU_ON = 'OUTPUT_ON'
TSP_DC_VOLTS = 'OUTPUT_DCVOLTS'
TSP_DC_AMPS = 'OUTPUT_DCAMPS'
TSP_SENSE_LOCAL = 'SENSE_LOCAL'
TSP_SENSE_REMOTE = 'SENSE_REMOTE'


class Keithley2602(QObject):
    """Diese Klasse handhabt die RS-232 Kommunikation mit dem Keithley 2602."""
    
    # Define signals for logging
    data_sent = pyqtSignal(str)
    data_received = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.ser = serial.Serial()
        self.ser.timeout = 2

    # NEW: Add is_open property to reflect serial connection status
    @property
    def is_open(self) -> bool:
        return self.ser.is_open

    def connect(self, port: str, baudrate: int = 115200) -> tuple[bool, str]:
        if self.ser.is_open: self.disconnect()
        try:
            self.ser.port = port
            self.ser.baudrate = baudrate
            self.ser.open()
            time.sleep(0.1)
            self.ser.read_all() # Clear buffer
            self.data_sent.emit(f"Connecting to {port}...") # Log connection attempt

            self.send_command("*IDN?")
            response = self.read_response()
            
            # Additional commands, log them too
            self.send_command("display.smua.measure.func = display.MEASURE_DCAMPS") # Strom auf Display A
            self.send_command("display.smub.measure.func = display.MEASURE_DCVOLTS") # Spannung auf Display B
            
            return True, response.strip()
        except serial.SerialException as e:
            # Emit error message to log as well
            self.data_sent.emit(f"Connection failed: {e}")
            return False, f"Verbindungsfehler: {e}"

    def disconnect(self):
        if self.ser.is_open: 
            self.ser.close()
            self.data_sent.emit("Disconnected from Keithley SMU.") # Log disconnection

    def send_command(self, command: str):
        if not self.ser.is_open: raise ConnectionError("Keine Verbindung zum Gerät.")
        cmd_bytes = (command + '\n').encode('ascii')
        self.ser.write(cmd_bytes)
        self.data_sent.emit(f"TX: {command}") # Emit sent command
        time.sleep(0.05)

    def read_response(self) -> str:
        if self.ser.is_open: 
            response = self.ser.readline().decode('ascii').strip()
            self.data_received.emit(f"RX: {response}") # Emit received response
            return response
        return ""

    def query(self, command: str) -> str:
        self.send_command(command)
        return self.read_response()

    def reset_channel(self, channel: str): 
        self.send_command(f"smu{channel}.reset()")
    
    def set_source_function(self, channel: str, func: str): 
        self.send_command(f"smu{channel}.source.func = smu{channel}.{func}")
    
    def set_sense_mode(self, channel: str, mode: str): 
        self.send_command(f"smu{channel}.sense = smu{channel}.{mode}")
    
    def set_source_level(self, channel: str, func: str, level: float):
        level_cmd = 'levelv' if func == TSP_DC_VOLTS else 'leveli'
        self.send_command(f"smu{channel}.source.{level_cmd} = {level}")
    
    def set_source_limit(self, channel: str, func: str, limit: float):
        limit_cmd = 'limiti' if func == TSP_DC_VOLTS else 'limitv'
        self.send_command(f"smu{channel}.source.{limit_cmd} = {limit}")
    
    def set_output_state(self, channel: str, state: str): 
        self.send_command(f"smu{channel}.source.output = smu{channel}.{state}")
    
    def measure_iv(self, channel: str) -> tuple[float, float]:
        response = self.query(f"print(smu{channel}.measure.iv())")
        parts = response.split('\t')
        return float(parts[0]), float(parts[1])


class DummyKeithley2602(QObject):
    """
    Diese Klasse simuliert die RS-232 Kommunikation mit einem Keithley 2602
    für Debugging-Zwecke.
    """
    data_sent = pyqtSignal(str)
    data_received = pyqtSignal(str)

    def __init__(self, simulated_resistance: float = 100.0):
        super().__init__()
        self.simulated_resistance = simulated_resistance # Ohms
        self._is_open = False # Simuliert den seriellen Port-Status
        self.sim_channel_state = {
            'a': {'func': TSP_DC_VOLTS, 'level': 0.0, 'limit': 0.01, 'output': False},
            'b': {'func': TSP_DC_VOLTS, 'level': 0.0, 'limit': 0.01, 'output': False}
        }
        self.sim_idn_response = "KEITHLEY INSTRUMENTS INC., MODEL 2602, SIMULATED, 1.0.0"

    # NEW: is_open property for DummyKeithley2602
    @property
    def is_open(self) -> bool:
        return self._is_open

    def connect(self, port: str, baudrate: int = 115200) -> tuple[bool, str]:
        self.data_sent.emit(f"Simulating connection to {port}...")
        # Simulate a slight delay
        time.sleep(0.1)
        self._is_open = True # Set internal status
        self.data_received.emit(f"Simulated RX: {self.sim_idn_response}")
        return True, self.sim_idn_response

    def disconnect(self):
        if self._is_open:
            self._is_open = False # Set internal status
            self.data_sent.emit("Simulated disconnection from Keithley SMU.")

    def send_command(self, command: str):
        if not self._is_open:
            raise ConnectionError("Simulated: Keine Verbindung zum Gerät.")
        self.data_sent.emit(f"Simulated TX: {command}")
        # Update internal state based on command
        if "smua.source.func" in command:
            if "DCVOLTS" in command: self.sim_channel_state['a']['func'] = TSP_DC_VOLTS
            elif "DCAMPS" in command: self.sim_channel_state['a']['func'] = TSP_DC_AMPS
        elif "smub.source.func" in command:
            if "DCVOLTS" in command: self.sim_channel_state['b']['func'] = TSP_DC_VOLTS
            elif "DCAMPS" in command: self.sim_channel_state['b']['func'] = TSP_DC_AMPS
        
        # Source Level
        if "smua.source.levelv" in command:
            self.sim_channel_state['a']['level'] = float(command.split('=')[1].strip())
        elif "smua.source.leveli" in command:
            self.sim_channel_state['a']['level'] = float(command.split('=')[1].strip())
        elif "smub.source.levelv" in command:
            self.sim_channel_state['b']['level'] = float(command.split('=')[1].strip())
        elif "smub.source.leveli" in command:
            self.sim_channel_state['b']['level'] = float(command.split('=')[1].strip())

        # Source Limit (dummy for now, but could be used for more complex simulation)
        if "smua.source.limiti" in command or "smua.source.limitv" in command:
            self.sim_channel_state['a']['limit'] = float(command.split('=')[1].strip())
        elif "smub.source.limiti" in command or "smub.source.limitv" in command:
            self.sim_channel_state['b']['limit'] = float(command.split('=')[1].strip())

        # Output State
        if "smua.source.output" in command:
            self.sim_channel_state['a']['output'] = (TSP_SMU_ON in command)
        elif "smub.source.output" in command:
            self.sim_channel_state['b']['output'] = (TSP_SMU_ON in command)

        time.sleep(0.01) # Simulate a small command processing delay

    def read_response(self) -> str:
        if not self._is_open: return "" # Use _is_open
        # For dummy, responses are mostly handled by query or specific commands
        # For *IDN?, it's handled in connect.
        # For other commands, we might return empty or "OK"
        response = "OK"
        self.data_received.emit(f"Simulated RX: {response}")
        return response

    def query(self, command: str) -> str:
        self.send_command(command) # Log the command
        
        response = ""
        if command == "*IDN?":
            response = self.sim_idn_response
        elif "print(smu" in command and ".measure.iv())" in command:
            channel = command.split('smu')[1].split('.')[0]
            if channel in self.sim_channel_state:
                state = self.sim_channel_state[channel]
                if state['output']:
                    if state['func'] == TSP_DC_VOLTS:
                        voltage = state['level']
                        current = voltage / self.simulated_resistance
                    else: # TSP_DC_AMPS
                        current = state['level']
                        voltage = current * self.simulated_resistance
                else:
                    voltage = 0.0
                    current = 0.0
                response = f"{current}\t{voltage}"
            else:
                response = "0.0\t0.0" # Default for unknown channel
        else:
            response = "OK" # Generic response for other queries

        self.data_received.emit(f"Simulated RX: {response}")
        return response

    # The following methods just call send_command or query, which are already simulated
    def reset_channel(self, channel: str): self.send_command(f"smu{channel}.reset()")
    def set_source_function(self, channel: str, func: str): self.send_command(f"smu{channel}.source.func = smu{channel}.{func}")
    def set_sense_mode(self, channel: str, mode: str): self.send_command(f"smu{channel}.sense = smu{channel}.{mode}")
    def set_source_level(self, channel: str, func: str, level: float):
        level_cmd = 'levelv' if func == TSP_DC_VOLTS else 'leveli'
        self.send_command(f"smu{channel}.source.{level_cmd} = {level}")
    def set_source_limit(self, channel: str, func: str, limit: float):
        limit_cmd = 'limiti' if func == TSP_DC_VOLTS else 'limitv'
        self.send_command(f"smu{channel}.source.{limit_cmd} = {limit}")
    def set_output_state(self, channel: str, state: str): self.send_command(f"smu{channel}.source.output = smu{channel}.{state}")
    def measure_iv(self, channel: str) -> tuple[float, float]:
        response = self.query(f"print(smu{channel}.measure.iv())")
        parts = response.split('\t')
        return float(parts[0]), float(parts[1])


class SmuTab(QWidget):
    """Haupt-Widget für den SMU-Steuerungs-Tab."""
    def __init__(self, shared_data):
        super().__init__()
        self.shared_data = shared_data
        # self.keithley wird erst in _connect_keithley initialisiert
        self.keithley = None 
        self.channel_widgets = {}
        self.channel_output_state = {'a': False, 'b': False}

        # Hauptlayout für diesen Tab
        self.main_layout = QVBoxLayout(self)
        self._create_com_port_ui()
        self._create_channel_ui()
        self._set_channel_controls_enabled(False)
        
        # WICHTIG: Die High-Level-Funktion im SharedState registrieren
        self.shared_data.smu_apply_and_measure = self.apply_and_measure

        # Initialer Refresh der COM-Ports beim Start
        self._refresh_com_ports()
        
        # KEINE Verbindung der Signale hier, da self.keithley noch None ist.
        # Die Verbindung erfolgt in _connect_keithley, nachdem das Objekt erstellt wurde.

    def _create_com_port_ui(self):
        com_groupbox = QGroupBox("Geräteverbindung (Keithley SMU)")
        com_layout = QHBoxLayout()
        com_groupbox.setFixedHeight(100)
        com_layout.addWidget(QLabel("COM Port:"))
        self.com_port_combo = QComboBox()
        
        # Verbindung des Signals, das ausgelöst wird, wenn die ComboBox geöffnet wird
        self.com_port_combo.activated.connect(self._refresh_com_ports) 
        
        com_layout.addWidget(self.com_port_combo)
        
        # NEW: Dummy Mode Checkbox
        self.dummy_mode_checkbox = QCheckBox("Dummy Modus")
        self.dummy_mode_checkbox.stateChanged.connect(self._on_dummy_mode_changed)
        com_layout.addWidget(self.dummy_mode_checkbox)
        
        self.connect_button = QPushButton("Verbinden")
        self.connect_button.clicked.connect(self._connect_keithley)
        com_layout.addWidget(self.connect_button)
        
        self.disconnect_button = QPushButton("Trennen")
        self.disconnect_button.clicked.connect(self._disconnect_keithley)
        self.disconnect_button.setEnabled(False)
        com_layout.addWidget(self.disconnect_button)
        
        com_layout.addStretch()
        self.status_label = QLabel("Status: Nicht verbunden")
        font = QFont(); font.setBold(True); self.status_label.setFont(font)
        self._update_status_color(False)
        com_layout.addWidget(self.status_label)
        com_groupbox.setLayout(com_layout)
        self.main_layout.addWidget(com_groupbox)

        # Serial Log GroupBox and TextEdit
        log_groupbox = QGroupBox("Serielle Kommunikation Log")
        log_layout = QVBoxLayout()
        self.serial_log_textedit = QTextEdit()
        self.serial_log_textedit.setReadOnly(True) # Make it read-only
        self.serial_log_textedit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap) # No word wrap
        self.serial_log_textedit.setFont(QFont("Monospace", 9)) # Monospace font for better alignment

        # Enable vertical scrolling, disable horizontal scrolling (if no wrap)
        self.serial_log_textedit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.serial_log_textedit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded) # Enable horizontal scroll if NoWrap

        # Set a preferred size policy for the log
        self.serial_log_textedit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.serial_log_textedit.setMinimumHeight(100) # Give it some initial height

        log_layout.addWidget(self.serial_log_textedit)
        log_groupbox.setLayout(log_layout)
        
        self.main_layout.addWidget(log_groupbox)

    def _on_dummy_mode_changed(self, state):
        # Wenn der Dummy-Modus geändert wird und eine Verbindung besteht, trennen
        if self.keithley and self.keithley.is_open: # Now is_open works for both
            self._disconnect_keithley()
        
        # Deaktiviere/Aktiviere COM-Port Auswahl basierend auf Dummy-Modus
        self.com_port_combo.setEnabled(True) # Immer aktiv, es sei denn verbunden (handled in _connect_keithley)

        # Leere den Log, wenn der Modus gewechselt wird
        self.serial_log_textedit.clear()
        self.serial_log_textedit.append(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Dummy Modus: {'AKTIVIERT' if state == Qt.CheckState.Checked.value else 'DEAKTIVIERT'}")
        self._refresh_com_ports() # Refresh ports to show "COM_DUMMY" or real ones


    def _create_channel_ui(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._create_single_channel_ui('a'))
        splitter.addWidget(self._create_single_channel_ui('b'))
        splitter.setSizes([450, 450])
        self.main_layout.addWidget(splitter)


    def _create_single_channel_ui(self, channel_id: str) -> QGroupBox:
        channel_group = QGroupBox(f"Channel {channel_id.upper()}")
        main_v_layout = QVBoxLayout()
        source_group = QGroupBox("Source")
        source_layout = QGridLayout()
        
        # --- Source Function Radio Buttons ---
        source_layout.addWidget(QLabel("Funktion:"), 0, 0)
        rb_voltage = QRadioButton("Spannung (V)")
        rb_current = QRadioButton("Strom (A)")
        
        # Create a QButtonGroup for source function for THIS channel
        source_func_button_group = QButtonGroup(self) # Pass 'self' (SmuTab) as parent
        source_func_button_group.addButton(rb_voltage)
        source_func_button_group.addButton(rb_current)
        rb_voltage.setChecked(True) # Set default after adding to group
        
        source_layout.addWidget(rb_voltage, 0, 1); source_layout.addWidget(rb_current, 0, 2)
        
        source_layout.addWidget(QLabel("Source Level:"), 1, 0)
        level_input = QLineEdit("0"); level_input.setValidator(QDoubleValidator())
        source_layout.addWidget(level_input, 1, 1, 1, 2)
        
        source_layout.addWidget(QLabel("Limit:"), 2, 0)
        limit_input = QLineEdit("0.01"); limit_input.setValidator(QDoubleValidator())
        source_layout.addWidget(limit_input, 2, 1, 1, 2)
        
        # --- Sense Mode Radio Buttons ---
        source_layout.addWidget(QLabel("Sense Mode:"), 3, 0)
        sense_local = QRadioButton("Local (2-Draht)")
        sense_remote = QRadioButton("Remote (4-Draht)")
        
        # Create a QButtonGroup for sense mode for THIS channel
        sense_mode_button_group = QButtonGroup(self) # Pass 'self' (SmuTab) as parent
        sense_mode_button_group.addButton(sense_local)
        sense_mode_button_group.addButton(sense_remote)
        sense_local.setChecked(True) # Set default after adding to group
        
        source_layout.addWidget(sense_local, 3, 1); source_layout.addWidget(sense_remote, 3, 2)
        
        set_settings_btn = QPushButton("Einstellungen übernehmen")
        set_settings_btn.clicked.connect(lambda: self._apply_source_settings(channel_id))
        source_layout.addWidget(set_settings_btn, 4, 0, 1, 3)
        
        source_group.setLayout(source_layout)
        main_v_layout.addWidget(source_group)
        
        # Measure Group
        measure_group = QGroupBox("Messergebnisse")
        measure_layout = QGridLayout()
        measure_iv_btn = QPushButton("I & V messen")
        measure_iv_btn.clicked.connect(lambda: self._measure_iv(channel_id))
        measure_layout.addWidget(measure_iv_btn, 0, 0, 1, 2)
        
        # Define v_read_label and i_read_label BEFORE using them in the dictionary
        v_read_label = QLabel("--- V")
        i_read_label = QLabel("--- A")
        
        measure_layout.addWidget(QLabel("Spannung:"), 1, 0); measure_layout.addWidget(v_read_label, 1, 1)
        measure_layout.addWidget(QLabel("Strom:"), 2, 0); measure_layout.addWidget(i_read_label, 2, 1)
        measure_group.setLayout(measure_layout)
        main_v_layout.addWidget(measure_group)
        
        # Output Group
        output_group = QGroupBox("Steuerung")
        output_layout = QHBoxLayout()
        
        # Define output_btn BEFORE using it in the dictionary
        output_btn = QPushButton("OUTPUT ON"); output_btn.setCheckable(True)
        output_btn.clicked.connect(lambda: self._toggle_output(channel_id))
        
        output_layout.addWidget(output_btn)
        reset_btn = QPushButton("Reset Channel")
        reset_btn.clicked.connect(lambda: self._reset_channel(channel_id))
        output_layout.addWidget(reset_btn)
        output_group.setLayout(output_layout)
        main_v_layout.addWidget(output_group)
        
        main_v_layout.addStretch()
        channel_group.setLayout(main_v_layout)
        
        # Store all created widgets (including the local QButtonGroups) in the channel_widgets dictionary
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
            'source_func_button_group': source_func_button_group, # Store the button group
            'sense_mode_button_group': sense_mode_button_group   # Store the button group
        }
        return channel_group

    def _refresh_com_ports(self):
        # Speichere den aktuell ausgewählten Port, falls vorhanden
        current_port = self.com_port_combo.currentText()
        
        self.com_port_combo.clear()
        
        # Im Dummy-Modus zeigen wir keine echten COM-Ports an
        if not self.dummy_mode_checkbox.isChecked():
            available_ports = [port.device for port in list_ports.comports()]
            self.com_port_combo.addItems(available_ports)
            # Versuche, den zuvor ausgewählten Port wieder zu setzen
            if current_port and current_port in available_ports:
                self.com_port_combo.setCurrentText(current_port)
            elif available_ports:
                self.com_port_combo.setCurrentIndex(0)
        else:
            # Im Dummy-Modus einen Dummy-Port anzeigen
            self.com_port_combo.addItem("COM_DUMMY")
            self.com_port_combo.setCurrentText("COM_DUMMY")


    def _update_status_color(self, connected: bool):
        palette = self.status_label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor("green") if connected else QColor("red"))
        self.status_label.setPalette(palette)

    def _connect_keithley(self):
        port = self.com_port_combo.currentText()
        if not port:
            QMessageBox.warning(self, "Verbindungsfehler", "Kein COM-Port ausgewählt.")
            return

        # Entscheide, welche Keithley-Instanz erstellt werden soll
        if self.dummy_mode_checkbox.isChecked():
            self.keithley = DummyKeithley2602(simulated_resistance=100.0) # Simulierter Widerstand
        else:
            self.keithley = Keithley2602()
            
        # WICHTIG: Signale nach der Instanziierung verbinden!
        self.keithley.data_sent.connect(self._update_serial_log)
        self.keithley.data_received.connect(self._update_serial_log)

        # Zuerst verbinden
        is_connected, message = self.keithley.connect(port)

        if is_connected:
            # Prüfen, ob es wirklich eine Keithley SMU ist (oder der Dummy)
            if "KEITHLEY" in message.upper() and ("2602" in message or "26" in message or "SIMULATED" in message.upper()):
                try:
                    smu_info = message.split(',')[1].strip() # Holt den Modellnamen
                    self.status_label.setText(f"Status: Verbunden mit {smu_info}")
                except IndexError:
                    self.status_label.setText(f"Status: Verbunden mit Gerät ({message.strip()})")

                self._update_status_color(True)
                self.connect_button.setEnabled(False)
                self.disconnect_button.setEnabled(True)
                self.com_port_combo.setEnabled(False) # ComboBox nach dem Verbinden deaktivieren
                self.dummy_mode_checkbox.setEnabled(False) # Dummy-Checkbox auch deaktivieren
                self._set_channel_controls_enabled(True)
                self.shared_data.smu = self.keithley
            else:
                # Es ist verbunden, aber nicht das erwartete Keithley-Gerät
                self.keithley.disconnect() # Verbindung sofort wieder trennen
                QMessageBox.critical(self, "Verbindungsfehler", 
                                     f"Gerät an {port} ist keine Keithley SMU. Antwort: {message}")
                self.status_label.setText("Status: Nicht verbunden (Falsches Gerät)")
                self._update_status_color(False)
                self.dummy_mode_checkbox.setEnabled(True) # Re-enable checkbox on failure
        else:
            # Bei einem generellen Verbindungsfehler
            QMessageBox.critical(self, "Verbindungsfehler", message)
            self.status_label.setText(f"Status: {message}")
            self._update_status_color(False)
            self.dummy_mode_checkbox.setEnabled(True) # Re-enable checkbox on failure

    def _disconnect_keithley(self):
        if self.keithley: # Sicherstellen, dass ein Keithley-Objekt existiert
            try:
                # Nutze die is_open Eigenschaft, die jetzt in beiden Klassen existiert
                if self.keithley.is_open: 
                    self.keithley.set_output_state('a', TSP_SMU_OFF)
                    self.keithley.set_output_state('b', TSP_SMU_OFF)
            except ConnectionError:
                pass # Ignoriere Fehler, wenn die Verbindung ohnehin schon weg ist
            
            self.keithley.disconnect()
            # Trenne die Signale, um Speicherlecks zu vermeiden, falls das keithley-Objekt ersetzt wird
            try:
                self.keithley.data_sent.disconnect(self._update_serial_log)
                self.keithley.data_received.disconnect(self._update_serial_log)
            except TypeError: # Signal might already be disconnected if app is closing
                pass

        self.status_label.setText("Status: Nicht verbunden")
        self._update_status_color(False)
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.com_port_combo.setEnabled(True) # ComboBox nach dem Trennen wieder aktivieren
        self.dummy_mode_checkbox.setEnabled(True) # Dummy-Checkbox wieder aktivieren
        self._set_channel_controls_enabled(False)
        for ch_id in ['a', 'b']:
            widgets = self.channel_widgets[ch_id]
            widgets['output_btn'].setChecked(False)
            widgets['output_btn'].setText("OUTPUT ON")
            self.channel_output_state[ch_id] = False
        self.shared_data.smu = None
        self.keithley = None # Setze keithley auf None, da es nicht mehr gültig ist


    def _set_channel_controls_enabled(self, enabled: bool):
        for channel in self.channel_widgets.values():
            channel['group'].setEnabled(enabled)

    def _apply_source_settings(self, channel_id: str) -> bool:
        widgets = self.channel_widgets[channel_id]
        is_voltage_source = widgets['rb_voltage'].isChecked()
        func = TSP_DC_VOLTS if is_voltage_source else TSP_DC_AMPS
        sense_mode = TSP_SENSE_LOCAL if widgets['sense_local'].isChecked() else TSP_SENSE_REMOTE
        try:
            level = float(widgets['level_input'].text())
            limit = float(widgets['limit_input'].text())
            # Stellen Sie sicher, dass self.keithley existiert, bevor Sie Methoden aufrufen
            if self.keithley:
                self.keithley.set_sense_mode(channel_id, sense_mode)
                self.keithley.set_source_function(channel_id, func)
                self.keithley.set_source_level(channel_id, func, level)
                self.keithley.set_source_limit(channel_id, func, limit)
                return True
            else:
                QMessageBox.critical(self, "Fehler", "SMU-Objekt nicht initialisiert.")
                return False
        except (ValueError, ConnectionError) as e:
            QMessageBox.critical(self, "Eingabefehler", f"Fehler: {e}")
            return False

    def _toggle_output(self, channel_id: str):
        button = self.channel_widgets[channel_id]['output_btn']
        new_state_on = not self.channel_output_state[channel_id]
        try:
            if new_state_on and not self._apply_source_settings(channel_id):
                button.setChecked(False); return
            state_cmd = TSP_SMU_ON if new_state_on else TSP_SMU_OFF
            if self.keithley: # Sicherstellen, dass self.keithley existiert
                self.keithley.set_output_state(channel_id, state_cmd)
                button.setText("OUTPUT OFF" if new_state_on else "OUTPUT ON")
                self.channel_output_state[channel_id] = new_state_on
                button.setChecked(new_state_on)
            else:
                QMessageBox.critical(self, "Fehler", "SMU-Objekt nicht initialisiert.")
                button.setChecked(False)
        except ConnectionError as e:
            self._disconnect_keithley()

    def _reset_channel(self, channel_id: str):
        try:
            if self.keithley: # Sicherstellen, dass self.keithley existiert
                self.keithley.reset_channel(channel_id)
                self.channel_output_state[channel_id] = False
                btn = self.channel_widgets[channel_id]['output_btn']
                btn.setChecked(False); btn.setText("OUTPUT ON")
                QMessageBox.information(self, "Reset", f"Kanal {channel_id.upper()} wurde zurückgesetzt.")
            else:
                QMessageBox.critical(self, "Fehler", "SMU-Objekt nicht initialisiert.")
        except ConnectionError as e:
            self._disconnect_keithley()

    def _measure_iv(self, channel_id: str):
        try:
            if self.keithley: # Sicherstellen, dass self.keithley existiert
                current, voltage = self.keithley.measure_iv(channel_id)
                self.channel_widgets[channel_id]['i_read_label'].setText(f"{current:.4e} A")
                self.channel_widgets[channel_id]['v_read_label'].setText(f"{voltage:.4e} V")
            else:
                QMessageBox.critical(self, "Fehler", "SMU-Objekt nicht initialisiert.")
        except (ValueError, ConnectionError) as e:
            QMessageBox.warning(self, "Messfehler", f"I/V-Messung fehlgeschlagen: {e}")
    
    # NEU: Die High-Level-Funktion für die Fernsteuerung durch andere Tabs
    def apply_and_measure(self, channel: str, is_voltage_source: bool, level: float, limit: float) -> tuple[float, float] | None:
        """
        Setzt einen Wert, schaltet den Ausgang kurz an, misst I&V und schaltet wieder aus.
        Gibt (Strom, Spannung) oder None bei Fehler zurück.
        """
        if self.shared_data.smu is None:
            print("SMU nicht verbunden.")
            return None
        
        try:
            # 1. Einstellungen setzen
            func = TSP_DC_VOLTS if is_voltage_source else TSP_DC_AMPS
            # Sicherstellen, dass self.keithley existiert
            if self.keithley:
                self.keithley.set_source_function(channel, func)
                self.keithley.set_source_level(channel, func, level)
                self.keithley.set_source_limit(channel, func, limit)

                # 2. Ausgang an, messen, Ausgang aus
                self.keithley.set_output_state(channel, TSP_SMU_ON)
                time.sleep(0.1) # Kurze Wartezeit für stabile Werte
                current, voltage = self.keithley.measure_iv(channel)
                self.keithley.set_output_state(channel, TSP_SMU_OFF)

                # Optional: GUI im SMU-Tab aktualisieren
                self.channel_widgets[channel]['level_input'].setText(str(level))
                self.channel_widgets[channel]['limit_input'].setText(str(limit))
                self.channel_widgets[channel]['i_read_label'].setText(f"{current:.4e} A")
                self.channel_widgets[channel]['v_read_label'].setText(f"{voltage:.4e} V")
                
                return current, voltage
            else:
                QMessageBox.critical(self, "Fehler", "SMU-Objekt nicht initialisiert.")
                return None

        except (ValueError, ConnectionError) as e:
            QMessageBox.critical(self, "Fernsteuerungsfehler", f"Fehler bei apply_and_measure: {e}")
            self._disconnect_keithley()
            return None

    # Method to update the serial log
    def _update_serial_log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3] # HH:MM:SS.ms
        log_entry = f"[{timestamp}] {message}" # append adds newline automatically
        
        # Check if the scrollbar is at the bottom (auto-scroll behavior)
        scrollbar = self.serial_log_textedit.verticalScrollBar()
        # Get the current maximum value of the scrollbar
        max_value = scrollbar.maximum()
        # Check if the scrollbar is at or very near the bottom
        at_bottom = (scrollbar.value() >= (max_value - 4)) # Small buffer for "near bottom"

        self.serial_log_textedit.append(log_entry)

        # If it was at the bottom, keep it at the bottom (auto-scroll)
        if at_bottom:
            self.serial_log_textedit.verticalScrollBar().setValue(scrollbar.maximum())