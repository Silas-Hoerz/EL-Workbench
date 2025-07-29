# el-workbench/other/info.py
# -*- coding: utf-8 -*-
"""
============================================================================
 File:           info.py
 Author:         Team EL-Workbench
 Creation date:  2025-06-25
 Last modified:  2025-01-15
 Version:        1.1.0
============================================================================
 Description:
    Zentralisierte Logging- und Statusverwaltung für EL-Workbench.
    Stellt InfoManager für Statusmeldungen und InfoWidget für UI-Anzeige bereit.
============================================================================
 Change Log:
 - 2025-06-25: Erste Version erstellt.
 - 2025-01-15: Header-Format und Dokumentation für v1.1.0 aktualisiert.
               Doppelte Header entfernt und get_timestamp Methode hinzugefügt.
============================================================================
"""
import os
import datetime
from PyQt6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QTextEdit,
    QPushButton, QFrame, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QTextCursor



class InfoManager(QObject):
    message_signal = pyqtSignal(str, int)

    INFO, WARNING, ERROR = range(3)

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOG_DIR = os.path.join(BASE_DIR, "data/logs")
    MAX_LOG_AGE_YEARS = 10

    def __init__(self):
        super().__init__()
        self._last_message = ""
        self._last_message_type = self.INFO

        self._init_log_file()

    def _init_log_file(self):
        os.makedirs(self.LOG_DIR, exist_ok=True)
        self._cleanup_old_logs()

        now = datetime.datetime.now()
        filename = now.strftime("%Y-%m-%d_%H-%M-%S.log")
        self.log_path = os.path.join(self.LOG_DIR, filename)

        with open(self.log_path, "w", encoding="utf-8") as f:
            f.write(f"Log gestartet: {now.isoformat()}\n")

    def _cleanup_old_logs(self):
        cutoff = datetime.datetime.now() - datetime.timedelta(days=365 * self.MAX_LOG_AGE_YEARS)
        for fname in os.listdir(self.LOG_DIR):
            path = os.path.join(self.LOG_DIR, fname)
            try:
                timestamp = datetime.datetime.strptime(fname.split(".")[0], "%Y-%m-%d_%H-%M-%S")
                if timestamp < cutoff:
                    os.remove(path)
            except Exception:
                continue  # Ignoriere ungültige Dateinamen

    def status(self, msg_type: int, message: str):
        message = str(message)
        self._last_message = message
        self._last_message_type = msg_type

        self.message_signal.emit(message, msg_type)
        self._write_to_logfile(msg_type, message)

    def _write_to_logfile(self, msg_type: int, message: str):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = self.get_type_prefix(msg_type)
        line = f"[{now}] {prefix}: {message}\n"
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as e:
            print(f"[Logger] Fehler beim Schreiben in Logdatei: {e}")

    def get_last_message(self) -> str:
        return self._last_message

    def get_last_message_type(self) -> int:
        return self._last_message_type

    @staticmethod
    def get_type_prefix(msg_type: int) -> str:
        return {0: "Info", 1: "Warnung", 2: "FEHLER"}.get(msg_type, "Unbekannt")
    
    def get_timestamp(self):
        """
        Get current timestamp as formatted string.
        
        Returns:
            str: Current timestamp in ISO format
        """
        return datetime.datetime.now().isoformat()
    




class CollapsibleLogWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)  # Start hidden

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet("background-color: #1e1e1e; color: white; font-family: monospace;")
        self.log_box.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.log_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.clear_button = QPushButton("Clear")
        self.copy_button = QPushButton("Copy")
        for btn in (self.clear_button, self.copy_button):
            btn.setFixedWidth(60)

        self.clear_button.clicked.connect(self.log_box.clear)
        self.copy_button.clicked.connect(lambda: QApplication.clipboard().setText(self.log_box.toPlainText()))

        button_layout = QVBoxLayout()
        button_layout.setContentsMargins(5, 5, 5, 5)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.copy_button)
        button_layout.addStretch(1)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        layout.addWidget(self.log_box)
        layout.addLayout(button_layout)

    def append_message(self, timestamp: str, message: str, msg_type: int):
        color_map = {
            0: "#f4f3f1",  # Info (weiß)
            1: "#ffa000",  # Warnung (orange)
            2: "#d32f2f",  # Fehler (rot)
        }
        color = color_map.get(msg_type, "#f4f3f1")
        self.log_box.moveCursor(QTextCursor.MoveOperation.End)
        self.log_box.insertHtml(f'<span style="color:{color}">[{timestamp}] {message}</span><br>')
        self.log_box.moveCursor(QTextCursor.MoveOperation.End)

class InfoWidget(QWidget):
    DEFAULT_MESSAGE = "Bereit"
    STYLES = {
        0: "background-color: #282923; color: #f4f3f1;",
        1: "background-color: #fffacd; color: #ffa000;",
        2: "background-color: #ffe6e6; color: #d32f2f; font-weight: bold;",
    }

    def __init__(self, shared_data):
        super().__init__()
        self.shared_data = shared_data
        self.info_manager = shared_data.info_manager
        self.expanded = False

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._clear_message)
        
        # Status Leiste  

        self.toggle_button = QLabel("⏵")
        self.toggle_button.setFixedWidth(15)
        self.toggle_button.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.toggle_button.setStyleSheet("color: gray;")

        self.message_label = QLabel(self.DEFAULT_MESSAGE)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.message_label.setText(self.DEFAULT_MESSAGE)
        self.message_label.setStyleSheet("color: #f4f3f1;")

        # Profil- und Geräte-Tags
        self.profile_tag = QLabel("Profil: unbekannt")
        self.probe_tag = QLabel("Probe: unbekannt")
        self.device_tag = QLabel("Device: unbekannt")
        

        for tag in (self.profile_tag, self.device_tag, self.probe_tag):
            tag.setStyleSheet("""
                background-color: #3a3f4b;
                color: #d6d6d6;
                padding: 2px 8px;
                border-radius: 5px;
                font-size: 10px;
            """)
            tag.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        
        self.top_bar = QFrame()
        self.top_bar.setFixedHeight(25)
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(5, 0, 5, 0)
        top_layout.setSpacing(5)
        top_layout.addWidget(self.toggle_button)
        top_layout.addWidget(self.message_label)
        top_layout.addStretch(1)
        top_layout.addWidget(self.profile_tag)
        top_layout.addWidget(self.probe_tag)
        top_layout.addWidget(self.device_tag)
        

        self.log_widget = CollapsibleLogWidget(self)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.addWidget(self.top_bar)
        self.main_layout.addWidget(self.log_widget)

        self.top_bar.mousePressEvent = self.toggle_log  # Ganz oben klickbar
        self.info_manager.message_signal.connect(self._display_message)

        # Initial die Tags aktualisieren, falls schon Daten vorhanden sind
        self.update_tags()

    @pyqtSlot()
    def toggle_log(self, event):
        self.expanded = not self.expanded
        self.log_widget.setVisible(self.expanded)
        self.toggle_button.setText("⏷" if self.expanded else "⏵")

    def _display_message(self, message: str, msg_type: int):
        # Tags zuerst aktualisieren, da eine neue Nachricht den Kontext betreffen könnte
        self.update_tags() 
        
        prefix = InfoManager.get_type_prefix(msg_type)
        full_message = f"{prefix}: {message}"
        self.message_label.setText(full_message)

        # Style dynamisch setzen
        style = self.STYLES.get(msg_type, self.STYLES[0])
        self.setStyleSheet(f"""
            InfoWidget {{
                border-top: 1px solid #ccc;
                {style}
            }}
            QLabel {{
                color: inherit;
            }}
        """)

        # Log speichern
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_widget.append_message(timestamp, full_message, msg_type)

        self.timer.start(5000)

    def _clear_message(self):
        self.message_label.setText(self.DEFAULT_MESSAGE)
        self.setStyleSheet(f"""
            InfoWidget {{
                border-top: 0px;
                background-color: #282923;
            }}
            QLabel {{
                color: #f4f3f1;
            }}
        """)
    
    def update_tags(self):
        # Korrekter Zugriff auf Profil- und Gerätedaten
        profile_name = "Kein Profil"
        if self.shared_data.current_profile:
            profile_name = self.shared_data.current_profile.get("name", "Unbekanntes Profil")

        device_name = "Keine Geometrie"
        if self.shared_data.current_device:
            device_name = self.shared_data.current_device.get("device_name", "Unbekannte Geometrie")

        probe_name = "Keine Probe"
        if self.shared_data.current_profile:
            probe_name = self.shared_data.current_profile.get("last_sample_id", "Unbekannte Probe")

        self.profile_tag.setText(f"Profil: {profile_name}")
        self.device_tag.setText(f"Geometrie: {device_name}")
        self.probe_tag.setText(f"Probe: {probe_name}")