# other/info.py

# -*- coding: utf-8 -*-
"""
============================================================================
 File:          info.py
 Author:        [Dein Name]
 Creation date: 2025-07-25
 Last modified: 2025-07-25 (Corrected InfoManager to QObject; InfoWidget handles UI)
 Version:       1.1.1
============================================================================
 Description:
     Modul zur zentralen Verwaltung und Anzeige von Status-, Informations-,
     Warn- und Fehlermeldungen in einer Anwendung.
     
     Die Klasse InfoManager fungiert als Single-Point-of-Truth für alle
     Nachrichten, die von verschiedenen Komponenten der Anwendung (Tabs, APIs)
     gesendet werden. Sie emittiert Signale, die von der UI-Komponente
     InfoWidget empfangen werden, um die Nachrichten darzustellen.
     
     InfoWidget ist die UI-Komponente, die eine einfache Statusleiste
     basierend auf den vom InfoManager erhaltenen Meldungen implementiert.
============================================================================
"""

from PyQt6.QtCore import pyqtSignal, QObject, Qt, QTimer
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QFrame, QApplication
import sys

class InfoManager(QObject): # <--- WICHTIG: Wieder von QObject erben!
    """
    Verwaltet Status-, Info-, Warn- und Fehlermeldungen zentral
    und sendet sie zur Anzeige an die UI.
    """
    # Signal, das von der InfoWidget-Instanz empfangen wird
    message_signal = pyqtSignal(str, int) # (message_text, message_type_int)

    # Konstanten für Nachrichtentypen
    INFO = 0
    WARNING = 1
    ERROR = 2

    def __init__(self):
        super().__init__()
        self._last_message = ""
        self._last_message_type = self.INFO

    def status(self, msg_type: int, message: str):
        """
        Sendet eine Statusmeldung zur Anzeige.

        :param msg_type: Der Typ der Nachricht (INFO, WARNING, ERROR).
        :param message: Die Textnachricht.
        """
        if not isinstance(message, str):
            message = str(message) # Sicherstellen, dass es ein String ist

        self._last_message = message
        self._last_message_type = msg_type
        
        # Sende das Signal an die verbundene InfoWidget-Instanz
        self.message_signal.emit(message, msg_type)
        print(f"[InfoManager] {self._get_type_prefix(msg_type)}: {message}") # Für Debugging im Konsolen-Output

    def get_last_message(self) -> str:
        """Gibt die letzte gesendete *unformatierte* Nachricht zurück."""
        return self._last_message

    def get_last_message_type(self) -> int:
        """Gibt den Typ der letzten gesendeten Nachricht zurück."""
        return self._last_message_type

    def _get_type_prefix(self, msg_type: int) -> str:
        """Gibt den Textpräfix für den Nachrichtentyp zurück."""
        if msg_type == self.INFO:
            return "Info"
        elif msg_type == self.WARNING:
            return "Warnung"
        elif msg_type == self.ERROR:
            return "FEHLER"
        else:
            return "Unbekannt"


class InfoWidget(QWidget): # <--- Dies ist das tatsächliche UI-Widget
    """
    Eine einfache UI-Komponente, die Status-, Info-, Warn- und Fehlermeldungen
    in einem QLabel anzeigt und visuelles Feedback basierend auf dem Nachrichtentyp gibt.
    """
    def __init__(self, info_manager: InfoManager, parent=None):
        super().__init__(parent)
        self.info_manager = info_manager # Referenz zum Logik-Manager
        self.timer = QTimer(self)
        self.timer.setSingleShot(True) # Timer läuft nur einmal
        self.timer.timeout.connect(self._clear_message) # Wenn Timer abläuft, Nachricht löschen

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """Initialisiert die UI-Elemente des InfoWidgets."""
        self.setFixedHeight(25) # Feste Höhe für die Statusleiste
        # KEINE setContentsMargins HIER! Das beeinflusst das Widget selbst, nicht das Layout
        # self.setContentsMargins(10, 10, 10, 10) # <-- Dies entfernen oder auf 0 setzen, da es sonst einen dicken Rand um das Widget legt.

        self.layout = QHBoxLayout(self) # Layout auf diesem Widget
        self.layout.setContentsMargins(5, 0, 5, 0) # Leichte Innenränder für den Inhalt
        self.layout.setSpacing(5)

        self.message_label = QLabel("Bereit")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.message_label.setStyleSheet("QLabel { color: #f4f3f1; }") # Standardtextfarbe
        self.layout.addWidget(self.message_label)
        
        self.layout.addStretch(1) # Sorgt dafür, dass der Text linksbündig bleibt

        # Standard-Styling für das Widget selbst (Rahmen, Hintergrund)
        self.setStyleSheet("""
            InfoWidget {
                border-top: 1px solid #ccc; /* Eine feine Linie oben */
                background-color: #282923;
            }
            QLabel {
                color: #f4f3f1;    
                padding: 0px; /* Kein Padding im Label selbst */
            }
        """)

    def _connect_signals(self):
        """Verbindet die Signale des InfoManagers mit diesem Widget."""
        self.info_manager.message_signal.connect(self._display_message)

    def _display_message(self, message: str, msg_type: int):
        """
        Slot, der Nachrichten vom InfoManager empfängt und im Label anzeigt.
        Formatiert die Nachricht und wendet Stile an.
        """
        # Nachricht formatieren
        formatted_message = f"{self.info_manager._get_type_prefix(msg_type)}: {message}"
        self.message_label.setText(formatted_message)

        # Visuelles Feedback basierend auf dem Nachrichtentyp
        if msg_type == InfoManager.ERROR:
            self.setStyleSheet("""
                InfoWidget {
                    border-top: 1px solid #ccc;
                    background-color: #ffe6e6; /* Hellrot */
                }
                QLabel {
                    color: #d32f2f; /* Dunkleres Rot */
                    font-weight: bold;
                }
            """)
        elif msg_type == InfoManager.WARNING:
            self.setStyleSheet("""
                InfoWidget {
                    border-top: 1px solid #ccc;
                    background-color: #fffacd; /* Hellgelb */
                }
                QLabel {
                    color: #ffa000; /* Orange */
                    font-weight: normal;
                }
            """)
        else: # INFO oder unbekannt
            self.setStyleSheet("""
                InfoWidget {
                    border-top: 1px solid #ccc;
                    background-color: #282923;
                }
                QLabel {
                    color: #f4f3f1; /* Standardfarbe */
                    font-weight: normal;
                }
            """)
        
        # Starte oder setze den Timer zurück, um die Nachricht nach 5 Sekunden zu löschen
        self.timer.start(5000) # Nachricht für 5 Sekunden anzeigen

    def _clear_message(self):
        """Löscht die Nachricht und setzt das Styling zurück."""
        self.message_label.setText("Bereit")
        self.setStyleSheet("""
            InfoWidget {
                border-top: 0px solid #ccc;
                background-color: #282923;
            }
            QLabel {
                color: #f4f3f1;    
            }
        """)
