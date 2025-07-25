# el-workbench/tabs/smu_tab.py

# -*- coding: utf-8 -*-
"""
============================================================================
 File:          smu_tab.py
 Author:        Silas Hörz
 Creation date: 2025-07-04
 Last modified: 2025-07-25 (Adapted to new API-centric design rules)
 Version:       2.0.0
============================================================================
 Description:
     Modul (Tab) für die Ansteuerung einer Keithley 26xx Source-Measure Unit
     (SMU) innerhalb des EL-Workbench. Verantwortlich für UI, die
     Instanziierung des SMU-Treibers und die Bereitstellung einer
     High-Level-API für andere Module.
============================================================================
"""
import sys
import time
import serial
import numpy
from serial.tools import list_ports
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel,
    QLineEdit, QPushButton, QComboBox, QRadioButton, QMessageBox, QSplitter,
    QButtonGroup, QTextEdit, QSizePolicy, QCheckBox, QScrollBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QDoubleValidator, QFont, QPalette, QColor

# Konstanten für die TSP-Befehle (Keithley specific)
TSP_SMU_OFF = 'OUTPUT_OFF'
TSP_SMU_ON = 'OUTPUT_ON'
TSP_DC_VOLTS = 'OUTPUT_DCVOLTS'
TSP_DC_AMPS = 'OUTPUT_DCAMPS'
TSP_SENSE_LOCAL = 'SENSE_LOCAL'
TSP_SENSE_REMOTE = 'SENSE_REMOTE'


class Keithley2602(QObject):
    """
    Diese Klasse handhabt die RS-232 Kommunikation mit dem Keithley 2602.
    Sie dient als Low-Level-Treiber (Gerätespezifische API gemäß Regel 2.4).
    """
    # Define signals for logging serial communication
    data_sent = pyqtSignal(str)
    data_received = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._ser = serial.Serial() # Use _ser for internal serial object
        self._ser.timeout = 2

    @property
    def is_open(self) -> bool:
        """Gibt den Verbindungsstatus des seriellen Ports zurück."""
        return self._ser.is_open

    def connect(self, port: str, baudrate: int = 115200) -> tuple[bool, str]:
        """Versucht, eine Verbindung zum Keithley SMU herzustellen."""
        if self._ser.is_open:
            self.disconnect() # Ensure previous connection is closed
        try:
            self._ser.port = port
            self._ser.baudrate = baudrate
            self._ser.open()
            time.sleep(0.1)
            self._ser.read_all() # Clear buffer
            self.data_sent.emit(f"Connecting to {port}...")

            # Query IDN and set display functions upon successful connection
            idn_response = self.query("*IDN?") # Use query for IDN
            self.send_command("display.smua.measure.func = display.MEASURE_DCAMPS") # Current on Display A
            self.send_command("display.smub.measure.func = display.MEASURE_DCVOLTS") # Voltage on Display B

            return True, idn_response.strip()
        except serial.SerialException as e:
            self.data_sent.emit(f"Connection failed: {e}")
            return False, f"Verbindungsfehler: {e}"
        except Exception as e:
            self.data_sent.emit(f"Unexpected error during connection: {e}")
            return False, f"Unerwarteter Fehler: {e}"

    def disconnect(self):
        """Schließt die serielle Verbindung."""
        if self._ser.is_open:
            self._ser.close()
            self.data_sent.emit("Disconnected from Keithley SMU.")

    def send_command(self, command: str):
        """Sendet einen TSP-Befehl an das Gerät."""
        if not self._ser.is_open:
            raise ConnectionError("Keine Verbindung zum Gerät.")
        cmd_bytes = (command + '\n').encode('ascii')
        self._ser.write(cmd_bytes)
        self.data_sent.emit(f"TX: {command}")
        time.sleep(0.05) # Small delay for command processing

    def read_response(self) -> str:
        """Liest eine Antwort vom Gerät."""
        if self._ser.is_open:
            response = self._ser.readline().decode('ascii').strip()
            self.data_received.emit(f"RX: {response}")
            return response
        return ""

    def query(self, command: str) -> str:
        """Sendet einen Befehl und liest die Antwort."""
        self.send_command(command)
        return self.read_response()

    def reset_channel(self, channel: str):
        """Setzt einen spezifischen SMU-Kanal zurück."""
        self.send_command(f"smu{channel}.reset()")

    def set_source_function(self, channel: str, func: str):
        """Stellt die Source-Funktion (Spannung/Strom) für einen Kanal ein."""
        self.send_command(f"smu{channel}.source.func = smu{channel}.{func}")

    def set_sense_mode(self, channel: str, mode: str):
        """Stellt den Sense-Modus (2- oder 4-Draht) für einen Kanal ein."""
        self.send_command(f"smu{channel}.sense = smu{channel}.{mode}")

    def set_source_level(self, channel: str, func: str, level: float):
        """Stellt das Source-Level (Spannung oder Strom) für einen Kanal ein."""
        level_cmd = 'levelv' if func == TSP_DC_VOLTS else 'leveli'
        self.send_command(f"smu{channel}.source.{level_cmd} = {level}")

    def set_source_limit(self, channel: str, func: str, limit: float):
        """Stellt den Source-Limit (Strom- oder Spannungslimit) für einen Kanal ein."""
        limit_cmd = 'limiti' if func == TSP_DC_VOLTS else 'limitv'
        self.send_command(f"smu{channel}.source.{limit_cmd} = {limit}")

    def set_output_state(self, channel: str, state: str):
        """Schaltet den Ausgang eines Kanals ein oder aus."""
        self.send_command(f"smu{channel}.source.output = smu{channel}.{state}")

    def measure_iv(self, channel: str) -> tuple[float, float]:
        """Misst Strom und Spannung für einen Kanal und gibt sie zurück."""
        response = self.query(f"print(smu{channel}.measure.iv())")
        try:
            parts = response.split('\t')
            return float(parts[0]), float(parts[1])
        except (ValueError, IndexError):
            raise ValueError(f"Ungültige Antwort von SMU beim Messen: '{response}'")


class DummyKeithley2602(QObject):
    """
    Diese Klasse simuliert die RS-232 Kommunikation mit einem Keithley 2602
    für Debugging-Zwecke. Sie agiert als Dummy-Low-Level-Treiber.
    """
    data_sent = pyqtSignal(str)
    data_received = pyqtSignal(str)

    def __init__(self, simulated_resistance: float = 100.0):
        super().__init__()
        self.simulated_resistance = simulated_resistance # Ohms
        self._is_open = False # Simuliert den seriellen Port-Status
        self.sim_channel_state = { # Simulate internal state of SMU channels
            'a': {'func': TSP_DC_VOLTS, 'level': 0.0, 'limit': 0.01, 'output': False},
            'b': {'func': TSP_DC_VOLTS, 'level': 0.0, 'limit': 0.01, 'output': False}
        }
        self.sim_idn_response = "KEITHLEY INSTRUMENTS INC., MODEL 2602, SIMULATED, 1.0.0"

    @property
    def is_open(self) -> bool:
        """Gibt den simulierten Verbindungsstatus zurück."""
        return self._is_open

    def connect(self, port: str, baudrate: int = 115200) -> tuple[bool, str]:
        """Simuliert eine Verbindung."""
        self.data_sent.emit(f"Simulating connection to {port}...")
        time.sleep(0.1) # Simulate a slight delay
        self._is_open = True
        self.data_received.emit(f"Simulated RX: {self.sim_idn_response}")
        return True, self.sim_idn_response

    def disconnect(self):
        """Simuliert das Trennen der Verbindung."""
        if self._is_open:
            self._is_open = False
            self.data_sent.emit("Simulated disconnection from Keithley SMU.")

    def send_command(self, command: str):
        """Simuliert das Senden eines Befehls und aktualisiert den internen Zustand."""
        if not self._is_open:
            raise ConnectionError("Simulated: Keine Verbindung zum Gerät.")
        self.data_sent.emit(f"Simulated TX: {command}")

        # Update internal state based on command (simplified for common commands)
        if "smua.source.func" in command:
            if "DCVOLTS" in command: self.sim_channel_state['a']['func'] = TSP_DC_VOLTS
            elif "DCAMPS" in command: self.sim_channel_state['a']['func'] = TSP_DC_AMPS
        elif "smub.source.func" in command:
            if "DCVOLTS" in command: self.sim_channel_state['b']['func'] = TSP_DC_VOLTS
            elif "DCAMPS" in command: self.sim_channel_state['b']['func'] = TSP_DC_AMPS

        if "smua.source.levelv" in command:
            self.sim_channel_state['a']['level'] = float(command.split('=')[1].strip())
        elif "smua.source.leveli" in command:
            self.sim_channel_state['a']['level'] = float(command.split('=')[1].strip())
        elif "smub.source.levelv" in command:
            self.sim_channel_state['b']['level'] = float(command.split('=')[1].strip())
        elif "smub.source.leveli" in command:
            self.sim_channel_state['b']['level'] = float(command.split('=')[1].strip())

        if "smua.source.output" in command:
            self.sim_channel_state['a']['output'] = (TSP_SMU_ON in command)
        elif "smub.source.output" in command:
            self.sim_channel_state['b']['output'] = (TSP_SMU_ON in command)

        time.sleep(0.01) # Simulate a small command processing delay

    def read_response(self) -> str:
        """Simuliert das Lesen einer Antwort."""
        if not self._is_open: return ""
        response = "OK" # Generic OK response for most non-query commands
        self.data_received.emit(f"Simulated RX: {response}")
        return response

    def query(self, command: str) -> str:
        """Simuliert das Senden eines Befehls und die Rückgabe einer Antwort."""
        self.send_command(command) # Log the command first

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
                        current = voltage / self.simulated_resistance + numpy.random.normal(0, state['limit'] * 0.1) # Add some noise based on limit
                        # Ensure current doesn't exceed limit
                        current = numpy.sign(current) * min(abs(current), state['limit'])
                    else: # TSP_DC_AMPS
                        current = state['level']
                        voltage = current * self.simulated_resistance + numpy.random.normal(0, state['limit'] * 0.1) # Add some noise based on limit
                        # Ensure voltage doesn't exceed limit
                        voltage = numpy.sign(voltage) * min(abs(voltage), state['limit'])
                else: # Output is off
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
        try:
            parts = response.split('\t')
            return float(parts[0]), float(parts[1])
        except (ValueError, IndexError):
            raise ValueError(f"Simulated: Ungültige Antwort beim Messen: '{response}'")


class SmuTab(QWidget):
    """
    Haupt-Widget für den SMU-Steuerungs-Tab.
    Dieser Tab ist für die direkte Interaktion mit dem SMU-Gerät verantwortlich,
    instanziiert den entsprechenden Treiber (echt oder Dummy) und stellt
    eine High-Level-API-Methode für andere Module im Workbench bereit.
    """
    def __init__(self, shared_data):
        super().__init__()
        self.shared_data = shared_data
        self.smu_driver = None # Renamed from 'keithley' for clarity (can be real or dummy)
        self.channel_widgets = {}
        self.channel_output_state = {'a': False, 'b': False}

        # Hauptlayout für diesen Tab
        self.main_layout = QVBoxLayout(self)
        self._create_com_port_ui()
        self._create_channel_ui()
        self._set_channel_controls_enabled(False)

        # WICHTIG: Die High-Level-Funktion im SharedState registrieren
        # Dies ist die High-Level-API des SMU-Moduls (Regel 2.2)
        self.shared_data.smu_apply_and_measure = self.apply_and_measure

        # Initialer Refresh der COM-Ports beim Start
        self._refresh_com_ports()

    def _create_com_port_ui(self):
        """Erstellt den UI-Bereich für die COM-Port-Auswahl und Verbindung."""
        com_groupbox = QGroupBox("Geräteverbindung (Keithley SMU)")
        com_layout = QHBoxLayout()
        com_groupbox.setFixedHeight(100) # Fixed height for consistency

        com_layout.addWidget(QLabel("COM Port:"))
        self.com_port_combo = QComboBox()
        # Connect the signal that is emitted when the ComboBox is opened
        self.com_port_combo.activated.connect(self._refresh_com_ports)
        com_layout.addWidget(self.com_port_combo)

        self.dummy_mode_checkbox = QCheckBox("Dummy Modus")
        self.dummy_mode_checkbox.stateChanged.connect(self._on_dummy_mode_changed)
        com_layout.addWidget(self.dummy_mode_checkbox)

        self.connect_button = QPushButton("Verbinden")
        self.connect_button.clicked.connect(self._connect_smu)
        com_layout.addWidget(self.connect_button)

        self.disconnect_button = QPushButton("Trennen")
        self.disconnect_button.clicked.connect(self._disconnect_smu)
        self.disconnect_button.setEnabled(False)
        com_layout.addWidget(self.disconnect_button)

        self.status_label = QLabel("Status: Nicht verbunden")
        font = QFont(); font.setBold(True); self.status_label.setFont(font)
        self._update_status_color(False)
        com_layout.addStretch() # Push status label to the right
        com_layout.addWidget(self.status_label)
        com_groupbox.setLayout(com_layout)
        self.main_layout.addWidget(com_groupbox)

        # Serial Log GroupBox and TextEdit
        log_groupbox = QGroupBox("Serielle Kommunikation Log")
        log_layout = QVBoxLayout()
        self.serial_log_textedit = QTextEdit()
        self.serial_log_textedit.setReadOnly(True)
        self.serial_log_textedit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.serial_log_textedit.setFont(QFont("Monospace", 9))

        self.serial_log_textedit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.serial_log_textedit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.serial_log_textedit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.serial_log_textedit.setMinimumHeight(100)

        log_layout.addWidget(self.serial_log_textedit)
        log_groupbox.setLayout(log_layout)
        self.main_layout.addWidget(log_groupbox)

    def _on_dummy_mode_changed(self, state):
        """Reagiert auf Änderungen des Dummy-Modus-Checkboxes."""
        # If dummy mode is changed and there's an active connection, disconnect it.
        if self.smu_driver and self.smu_driver.is_open:
            self._disconnect_smu()

        # Clear log on mode change
        self.serial_log_textedit.clear()
        self.serial_log_textedit.append(
            f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] "
            f"Dummy Modus: {'AKTIVIERT' if state == Qt.CheckState.Checked.value else 'DEAKTIVIERT'}"
        )
        self._refresh_com_ports() # Refresh ports to show "COM_DUMMY" or real ones

    def _create_channel_ui(self):
        """Erstellt die UI für die beiden SMU-Kanäle (A und B)."""
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._create_single_channel_ui('a'))
        splitter.addWidget(self._create_single_channel_ui('b'))
        splitter.setSizes([450, 450]) # Set initial sizes
        self.main_layout.addWidget(splitter)

    def _create_single_channel_ui(self, channel_id: str) -> QGroupBox:
        """Erstellt die UI-Elemente für einen einzelnen SMU-Kanal."""
        channel_group = QGroupBox(f"Channel {channel_id.upper()}")
        main_v_layout = QVBoxLayout()
        
        # Source Group
        source_group = QGroupBox("Source")
        source_layout = QGridLayout()

        source_layout.addWidget(QLabel("Funktion:"), 0, 0)
        rb_voltage = QRadioButton("Spannung (V)")
        rb_current = QRadioButton("Strom (A)")
        source_func_button_group = QButtonGroup(self)
        source_func_button_group.addButton(rb_voltage)
        source_func_button_group.addButton(rb_current)
        rb_voltage.setChecked(True)
        source_layout.addWidget(rb_voltage, 0, 1)
        source_layout.addWidget(rb_current, 0, 2)

        source_layout.addWidget(QLabel("Source Level:"), 1, 0)
        level_input = QLineEdit("0")
        level_input.setValidator(QDoubleValidator())
        source_layout.addWidget(level_input, 1, 1, 1, 2)

        source_layout.addWidget(QLabel("Limit:"), 2, 0)
        limit_input = QLineEdit("0.01")
        limit_input.setValidator(QDoubleValidator())
        source_layout.addWidget(limit_input, 2, 1, 1, 2)

        source_layout.addWidget(QLabel("Sense Mode:"), 3, 0)
        sense_local = QRadioButton("Local (2-Draht)")
        sense_remote = QRadioButton("Remote (4-Draht)")
        sense_mode_button_group = QButtonGroup(self)
        sense_mode_button_group.addButton(sense_local)
        sense_mode_button_group.addButton(sense_remote)
        sense_local.setChecked(True)
        source_layout.addWidget(sense_local, 3, 1)
        source_layout.addWidget(sense_remote, 3, 2)

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

        v_read_label = QLabel("--- V")
        i_read_label = QLabel("--- A")
        measure_layout.addWidget(QLabel("Spannung:"), 1, 0)
        measure_layout.addWidget(v_read_label, 1, 1)
        measure_layout.addWidget(QLabel("Strom:"), 2, 0)
        measure_layout.addWidget(i_read_label, 2, 1)
        measure_group.setLayout(measure_layout)
        main_v_layout.addWidget(measure_group)

        # Output Group
        output_group = QGroupBox("Steuerung")
        output_layout = QHBoxLayout()

        output_btn = QPushButton("OUTPUT ON")
        output_btn.setCheckable(True)
        output_btn.clicked.connect(lambda: self._toggle_output(channel_id))

        output_layout.addWidget(output_btn)
        reset_btn = QPushButton("Reset Channel")
        reset_btn.clicked.connect(lambda: self._reset_channel(channel_id))
        output_layout.addWidget(reset_btn)
        output_group.setLayout(output_layout)
        main_v_layout.addWidget(output_group)

        main_v_layout.addStretch() # Pushes content to the top
        channel_group.setLayout(main_v_layout)

        # Store all created widgets in the channel_widgets dictionary
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
            'source_func_button_group': source_func_button_group,
            'sense_mode_button_group': sense_mode_button_group
        }
        return channel_group

    def _refresh_com_ports(self):
        """Aktualisiert die Liste der verfügbaren COM-Ports in der Combobox."""
        current_port = self.com_port_combo.currentText()
        self.com_port_combo.clear()

        if not self.dummy_mode_checkbox.isChecked():
            available_ports = [port.device for port in list_ports.comports()]
            self.com_port_combo.addItems(available_ports)
            if current_port and current_port in available_ports:
                self.com_port_combo.setCurrentText(current_port)
            elif available_ports:
                self.com_port_combo.setCurrentIndex(0)
        else:
            self.com_port_combo.addItem("COM_DUMMY")
            self.com_port_combo.setCurrentText("COM_DUMMY")

    def _update_status_color(self, connected: bool):
        """Aktualisiert die Farbe des Status-Labels."""
        palette = self.status_label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor("green") if connected else QColor("red"))
        self.status_label.setPalette(palette)

    def _connect_smu(self):
        """Stellt eine Verbindung zum SMU (echt oder Dummy) her."""
        port = self.com_port_combo.currentText()
        if not port:
            QMessageBox.warning(self, "Verbindungsfehler", "Kein COM-Port ausgewählt.")
            return

        # Instantiate the correct SMU driver based on dummy mode
        if self.dummy_mode_checkbox.isChecked():
            self.smu_driver = DummyKeithley2602(simulated_resistance=100.0)
        else:
            self.smu_driver = Keithley2602()

        # IMPORTANT: Connect signals AFTER driver instantiation
        self.smu_driver.data_sent.connect(self._update_serial_log)
        self.smu_driver.data_received.connect(self._update_serial_log)

        # Attempt to connect
        is_connected, message = self.smu_driver.connect(port)

        if is_connected:
            # Check if it's the expected Keithley SMU (or dummy)
            if "KEITHLEY" in message.upper() and ("2602" in message or "26" in message or "SIMULATED" in message.upper()):
                try:
                    smu_info = message.split(',')[1].strip() # Get model name
                    self.status_label.setText(f"Status: Verbunden mit {smu_info}")
                except IndexError:
                    self.status_label.setText(f"Status: Verbunden mit Gerät ({message.strip()})")

                self._update_status_color(True)
                self.connect_button.setEnabled(False)
                self.disconnect_button.setEnabled(True)
                self.com_port_combo.setEnabled(False)
                self.dummy_mode_checkbox.setEnabled(False)
                self._set_channel_controls_enabled(True)
                # Store the connected SMU driver instance in SharedState (Rule 2.1)
                self.shared_data.smu_device = self.smu_driver
            else:
                # Connected, but not the expected device
                self.smu_driver.disconnect() # Disconnect immediately
                QMessageBox.critical(self, "Verbindungsfehler",
                                     f"Gerät an {port} ist keine Keithley SMU. Antwort: {message}")
                self.status_label.setText("Status: Nicht verbunden (Falsches Gerät)")
                self._update_status_color(False)
                self.dummy_mode_checkbox.setEnabled(True) # Re-enable checkbox on failure
        else:
            # Generic connection error
            QMessageBox.critical(self, "Verbindungsfehler", message)
            self.status_label.setText(f"Status: {message}")
            self._update_status_color(False)
            self.dummy_mode_checkbox.setEnabled(True) # Re-enable checkbox on failure

    def _disconnect_smu(self):
        """Trennt die Verbindung zum SMU."""
        if self.smu_driver:
            try:
                if self.smu_driver.is_open:
                    # Ensure outputs are turned off before disconnecting
                    self.smu_driver.set_output_state('a', TSP_SMU_OFF)
                    self.smu_driver.set_output_state('b', TSP_SMU_OFF)
            except ConnectionError:
                pass # Ignore if connection is already lost

            self.smu_driver.disconnect()
            # Disconnect signals to prevent memory leaks, especially if driver object is replaced
            try:
                self.smu_driver.data_sent.disconnect(self._update_serial_log)
                self.smu_driver.data_received.disconnect(self._update_serial_log)
            except TypeError: # Signal might already be disconnected if app is closing
                pass

        self.status_label.setText("Status: Nicht verbunden")
        self._update_status_color(False)
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.com_port_combo.setEnabled(True)
        self.dummy_mode_checkbox.setEnabled(True)
        self._set_channel_controls_enabled(False)

        # Reset UI elements for channels
        for ch_id in ['a', 'b']:
            widgets = self.channel_widgets[ch_id]
            widgets['output_btn'].setChecked(False)
            widgets['output_btn'].setText("OUTPUT ON")
            self.channel_output_state[ch_id] = False
            widgets['v_read_label'].setText("--- V")
            widgets['i_read_label'].setText("--- A")

        # Clear the SMU driver instance from SharedState (Rule 2.1)
        self.shared_data.smu_device = None
        self.smu_driver = None # Clear local reference

    def _set_channel_controls_enabled(self, enabled: bool):
        """Aktiviert oder deaktiviert die Steuerelemente der Kanäle."""
        for channel in self.channel_widgets.values():
            channel['group'].setEnabled(enabled)

    def _apply_source_settings(self, channel_id: str) -> bool:
        """Wendet die eingestellten Source-Parameter auf den SMU-Kanal an."""
        widgets = self.channel_widgets[channel_id]
        is_voltage_source = widgets['rb_voltage'].isChecked()
        func = TSP_DC_VOLTS if is_voltage_source else TSP_DC_AMPS
        sense_mode = TSP_SENSE_LOCAL if widgets['sense_local'].isChecked() else TSP_SENSE_REMOTE
        try:
            level = float(widgets['level_input'].text())
            limit = float(widgets['limit_input'].text())

            if self.smu_driver and self.smu_driver.is_open:
                self.smu_driver.set_sense_mode(channel_id, sense_mode)
                self.smu_driver.set_source_function(channel_id, func)
                self.smu_driver.set_source_level(channel_id, func, level)
                self.smu_driver.set_source_limit(channel_id, func, limit)
                return True
            else:
                QMessageBox.critical(self, "Fehler", "SMU ist nicht verbunden.")
                return False
        except (ValueError, ConnectionError) as e:
            QMessageBox.critical(self, "Eingabefehler", f"Fehler beim Anwenden der Einstellungen: {e}")
            if isinstance(e, ConnectionError):
                self._disconnect_smu() # Disconnect on connection error
            return False

    def _toggle_output(self, channel_id: str):
        """Schaltet den Ausgang eines SMU-Kanals ein oder aus."""
        button = self.channel_widgets[channel_id]['output_btn']
        new_state_on = not self.channel_output_state[channel_id] # Desired state

        try:
            if new_state_on: # If turning ON, apply settings first
                if not self._apply_source_settings(channel_id):
                    button.setChecked(False) # Keep button off if settings failed
                    return

            state_cmd = TSP_SMU_ON if new_state_on else TSP_SMU_OFF
            if self.smu_driver and self.smu_driver.is_open:
                self.smu_driver.set_output_state(channel_id, state_cmd)
                button.setText("OUTPUT OFF" if new_state_on else "OUTPUT ON")
                self.channel_output_state[channel_id] = new_state_on
                button.setChecked(new_state_on) # Update button state
            else:
                QMessageBox.critical(self, "Fehler", "SMU ist nicht verbunden.")
                button.setChecked(False)
        except ConnectionError as e:
            QMessageBox.critical(self, "Verbindungsfehler", f"Fehler beim Schalten des Outputs: {e}")
            self._disconnect_smu() # Disconnect on connection error
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Unerwarteter Fehler beim Schalten des Outputs: {e}")
            button.setChecked(not new_state_on) # Revert button state on unexpected error

    def _reset_channel(self, channel_id: str):
        """Setzt den ausgewählten SMU-Kanal zurück."""
        try:
            if self.smu_driver and self.smu_driver.is_open:
                self.smu_driver.reset_channel(channel_id)
                self.channel_output_state[channel_id] = False
                btn = self.channel_widgets[channel_id]['output_btn']
                btn.setChecked(False)
                btn.setText("OUTPUT ON")
                self.channel_widgets[channel_id]['v_read_label'].setText("--- V")
                self.channel_widgets[channel_id]['i_read_label'].setText("--- A")
                QMessageBox.information(self, "Reset", f"Kanal {channel_id.upper()} wurde zurückgesetzt.")
            else:
                QMessageBox.critical(self, "Fehler", "SMU ist nicht verbunden.")
        except ConnectionError as e:
            QMessageBox.critical(self, "Verbindungsfehler", f"Fehler beim Zurücksetzen des Kanals: {e}")
            self._disconnect_smu()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Unerwarteter Fehler beim Zurücksetzen: {e}")

    def _measure_iv(self, channel_id: str):
        """Führt eine I/V-Messung für den ausgewählten SMU-Kanal durch."""
        try:
            if self.smu_driver and self.smu_driver.is_open:
                current, voltage = self.smu_driver.measure_iv(channel_id)
                self.channel_widgets[channel_id]['i_read_label'].setText(f"{current:.4e} A")
                self.channel_widgets[channel_id]['v_read_label'].setText(f"{voltage:.4e} V")
            else:
                QMessageBox.critical(self, "Fehler", "SMU ist nicht verbunden.")
        except (ValueError, ConnectionError) as e:
            QMessageBox.warning(self, "Messfehler", f"I/V-Messung fehlgeschlagen: {e}")
            if isinstance(e, ConnectionError):
                self._disconnect_smu() # Disconnect on connection error
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Unerwarteter Fehler bei der Messung: {e}")

    def apply_and_measure(self, channel: str, is_voltage_source: bool, level: float, limit: float) -> tuple[float, float] | None:
        """
        High-Level-API-Methode (Regel 2.2): Setzt einen Wert auf dem SMU, schaltet den Ausgang kurz an,
        misst Strom und Spannung und schaltet den Ausgang wieder aus.
        Gibt (Strom, Spannung) oder None bei Fehler zurück.
        """
        if self.shared_data.smu_device is None or not self.shared_data.smu_device.is_open:
            # Do not use QMessageBox here, as this method might be called from non-UI threads
            # or in automated processes where a pop-up is undesirable. Log instead.
            self._update_serial_log("SMU nicht verbunden für apply_and_measure.")
            return None

        smu = self.shared_data.smu_device # Get the active SMU driver instance

        try:
            # 1. Apply settings
            func = TSP_DC_VOLTS if is_voltage_source else TSP_DC_AMPS
            smu.set_source_function(channel, func)
            smu.set_source_level(channel, func, level)
            smu.set_source_limit(channel, func, limit)

            # 2. Turn output on, measure, turn output off
            smu.set_output_state(channel, TSP_SMU_ON)
            time.sleep(0.1) # Short delay for stable readings
            current, voltage = smu.measure_iv(channel)
            smu.set_output_state(channel, TSP_SMU_OFF)

            # Optional: Update the GUI of the SMU tab for the current channel
            # This is specific to the UI, so it stays here.
            widgets = self.channel_widgets.get(channel)
            if widgets:
                widgets['level_input'].setText(str(level))
                widgets['limit_input'].setText(str(limit))
                widgets['i_read_label'].setText(f"{current:.4e} A")
                widgets['v_read_label'].setText(f"{voltage:.4e} V")
                # Also ensure the output button is correctly reflected as OFF
                widgets['output_btn'].setChecked(False)
                widgets['output_btn'].setText("OUTPUT ON")
                self.channel_output_state[channel] = False

            return current, voltage

        except (ValueError, ConnectionError) as e:
            # Log the error, but don't show QMessageBox for an API call
            self._update_serial_log(f"Fehler in apply_and_measure für Kanal {channel.upper()}: {e}")
            # If a connection error occurs during an API call, trigger a disconnect
            if isinstance(e, ConnectionError):
                self._disconnect_smu()
            return None
        except Exception as e:
            self._update_serial_log(f"Unerwarteter Fehler in apply_and_measure für Kanal {channel.upper()}: {e}")
            return None

    def _update_serial_log(self, message: str):
        """Aktualisiert das serielle Kommunikations-Log."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3] # HH:MM:SS.ms
        log_entry = f"[{timestamp}] {message}"

        # Check if the scrollbar is at the bottom before appending
        # This ensures auto-scrolling only if the user hasn't scrolled up
        scrollbar = self.serial_log_textedit.verticalScrollBar()
        should_scroll = scrollbar.value() == scrollbar.maximum()

        self.serial_log_textedit.append(log_entry)

        if should_scroll:
            self.serial_log_textedit.verticalScrollBar().setValue(self.serial_log_textedit.verticalScrollBar().maximum())