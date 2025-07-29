# tabs/profile_tab.py
# -*- coding: utf-8 -*-
"""
============================================================================
File:           profile_tab.py
Author:         Silas Hörz
Creation date:  2025-07-25
Last modified:  2025-07-29
Version:        1.1.0
============================================================================
Description:
    Modul (Tab) für das Anlegen, Laden und Speichern von Profilen und zugehörigen Geometrien.
    Verwaltet Profileigenschaften und Geometriedaten direkt über SharedData.
============================================================================
Change Log:
- 2025-07-25: Initialversion erstellt.
- 2025-07-28: Für direkte SharedData-Nutzung angepasst, refaktoriert.
- 2025-07-29: Entfernung der dynamischen Attribut-Sektion, Anpassung an feste Profilattribute.
              Ersetzung von QGroupBox durch QLabel in der UI.
              Aktualisierung der Header und Sprachkonventionen (Code Englisch, UI/Kommentare Deutsch).
              Hinzufügen eines Buttons zum Auswählen eines Speicherorts über den Dateiexplorer.
============================================================================
"""

import os
import json
import uuid
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QAbstractItemView,
    QLineEdit, QMessageBox, QInputDialog, QLabel,
    QDialog, QHeaderView, QMenu, QSizePolicy, QFileDialog
)
from PyQt6.QtCore import QTimer, Qt, QSettings

# Importiere DeviceDialog und InfoManager.
from other.info import InfoManager
from other.device_dialog import DeviceDialog

# --- Globale Konstanten und Pfade ---
# Basisverzeichnis des Projekts.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Pfad zum Verzeichnis der Profildaten.
PROFIL_DIR = os.path.join(BASE_DIR, "data/profiles")
# Dateipfad für das zuletzt verwendete Profil.
LAST_USED_PROFILE_FILE = os.path.join(PROFIL_DIR, "last_profile.json")

# --- ProfileTab Class Definition ---
class ProfileTab(QWidget):
    """
    Verwaltet Benutzerprofile, einschließlich Profilattribute und zugehöriger Geometrie.
    Bietet Funktionen zum Hinzufügen, Bearbeiten und Löschen von Profilen und Geometrien.
    Diese Klasse ist primär für die Benutzeroberfläche und die zugrunde liegenden Dateivorgänge verantwortlich.
    Sie interagiert direkt mit dem SharedData-Objekt für den Datenaustausch.
    """
    def __init__(self, shared_data):
        """
        Initialisiert den ProfileTab.
        :param shared_data: Ein Objekt zum Teilen von Daten in der Anwendung.
                            Es sollte Attribute wie .current_profile und .current_device haben.
        """
        super().__init__()
        self.shared_data = shared_data
        # Speichert Profile: profile_id: {name: "...", path: "...", data: {...}}
        self.profiles = {}
        # UUID des aktuell ausgewählten Profils.
        self.current_profile_id = None
        
        # QSettings wird für persistente Anwendungseinstellungen verwendet, nicht für Profildaten.
        self.settings = QSettings("EL-Workbench", "ProfileTab")

        self.init_ui()
        # Verzögert das Laden der Profile, bis die UI angezeigt wird.
        QTimer.singleShot(0, self.load_profiles)

    # --- UI Initialisierung ---
    def init_ui(self):
        """Initialisiert die Benutzeroberflächenelemente für den ProfileTab."""
        main_layout = QHBoxLayout(self)

        # Linker Bereich: Profilverwaltung (Tabelle und Hinzufügen-Button)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Label als Überschrift für den Profilbereich
        self.button_add_profile = QPushButton("Profil hinzufügen")
        self.button_add_profile.clicked.connect(self.add_profile)
        self.button_add_profile.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        
        button_layout_add_profile = QHBoxLayout()
        button_layout_add_profile.addStretch(1)
        button_layout_add_profile.addWidget(self.button_add_profile)
        button_layout_add_profile.addStretch(1)
        left_layout.addLayout(button_layout_add_profile)

        self.profile_table = QTableWidget(0, 1)
        self.profile_table.verticalHeader().setVisible(False)
        self.profile_table.horizontalHeader().setVisible(False)
        self.profile_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.profile_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.profile_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.profile_table.cellClicked.connect(self.on_profile_change)
        self.profile_table.horizontalHeader().setStretchLastSection(True)
        self.profile_table.setMinimumWidth(150)
        left_layout.addWidget(self.profile_table)

        # Rechter Bereich: Profilattribute & Geometrieverwaltung
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Profilname & Verzeichnis
        profile_attr_layout = QVBoxLayout()
        
        self.label_profile_name_display = QLabel("Kein Profil ausgewählt") # Initialer Text, zeigt den Namen des ausgewählten Profils an
        self.label_profile_name_display.setObjectName("Title") # Für potenzielle CSS-Styling
        profile_attr_layout.addWidget(self.label_profile_name_display)

        profile_attr_layout.addWidget(QLabel("Name:"))
        self.name_field = QLineEdit()
        self.name_field.editingFinished.connect(self.save_profile_name_change)
        profile_attr_layout.addWidget(self.name_field)

        # Speicherort mit Button
        profile_attr_layout.addWidget(QLabel("Speicherort:"))
        storage_location_layout = QHBoxLayout()
        self.directory_field = QLineEdit()
        self.directory_field.setReadOnly(True) # Das Verzeichnis-Feld ist schreibgeschützt
        storage_location_layout.addWidget(self.directory_field)
        self.button_select_directory = QPushButton("🖿")
        self.button_select_directory.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.button_select_directory.clicked.connect(self._select_storage_location)
        storage_location_layout.addWidget(self.button_select_directory)
        profile_attr_layout.addLayout(storage_location_layout)

        # Festes Attribut: Letzte Probe ID
        profile_attr_layout.addWidget(QLabel("Probe:"))
        self.last_sample_id_field = QLineEdit()
        self.last_sample_id_field.editingFinished.connect(self.save_last_sample_id_change)
        profile_attr_layout.addWidget(self.last_sample_id_field)
        
        right_layout.addLayout(profile_attr_layout)

        # Überschrift für Geometrieverwaltung
        device_management_label = QLabel("Geometrie")
        device_management_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-top: 10px; margin-bottom: 5px;")
        right_layout.addWidget(device_management_label)

        # Geometrieverwaltung Sektion
        device_layout = QVBoxLayout()

        self.device_table = QTableWidget(0, 1) # Nur eine sichtbare Spalte für den Namen
        self.device_table.setHorizontalHeaderLabels(["Geometrie"])
        self.device_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.device_table.verticalHeader().setVisible(False)
        self.device_table.horizontalHeader().setVisible(False) # Header ausblenden wie ursprünglich
        self.device_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.device_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.device_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.device_table.cellDoubleClicked.connect(self.edit_device_from_table)
        self.device_table.cellClicked.connect(self.on_device_selection_changed)
        self.device_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.device_table.customContextMenuRequested.connect(self.show_device_context_menu)
        device_layout.addWidget(self.device_table)

        button_layout_add_device = QHBoxLayout()
        self.button_add_device = QPushButton("Neue Geometrie")
        self.button_add_device.clicked.connect(self.add_device)
        button_layout_add_device.addWidget(self.button_add_device)
        button_layout_add_device.addStretch(1)
        device_layout.addLayout(button_layout_add_device)
        
        right_layout.addLayout(device_layout)

        # Spacer und Profil Löschen Button
        right_layout.addStretch()

        delete_button_layout = QHBoxLayout()
        self.delete_profile_button = QPushButton("Profil löschen")
        self.delete_profile_button.clicked.connect(self.delete_profile)
        delete_button_layout.addWidget(self.delete_profile_button)
        delete_button_layout.addStretch(1)
        right_layout.addLayout(delete_button_layout)

        main_layout.addWidget(left_widget, 1)
        main_layout.addWidget(right_widget, 3)

    # --- Profilverwaltungsmethoden ---
    def generate_unique_id(self):
        """Generiert eine global eindeutige Kennung (UUID)."""
        return str(uuid.uuid4())

    def add_profile(self):
        """Fordert den Benutzer zur Eingabe eines neuen Profilnamens auf und erstellt die Profil-Datei und -Daten."""
        while True:
            name, ok = QInputDialog.getText(self, "Neues Profil", "Profilnamen eingeben:")
            if not ok:
                self.shared_data.info_manager.status(InfoManager.INFO, "Profil hinzufügen abgebrochen.")
                return

            name = name.strip()
            if not name:
                self.shared_data.info_manager.status(InfoManager.WARNING, "Profilname darf nicht leer sein.")
                QMessageBox.warning(self, "Fehler", "Profilname darf nicht leer sein.")
                continue

            if self._is_profile_name_unique(name):
                break
            else:
                self.shared_data.info_manager.status(InfoManager.WARNING, f"Profilname '{name}' existiert bereits.")
                QMessageBox.warning(self, "Fehler", f"Ein Profil mit dem Namen '{name}' existiert bereits. Bitte wählen Sie einen anderen Namen.")
                continue

        profile_id = self.generate_unique_id()
        profile_file_path = os.path.join(PROFIL_DIR, f"{profile_id}.json")
        new_profile_data = {
            "id": profile_id,
            "name": name,
            "storage_location": os.path.join(PROFIL_DIR, name), # Standard-Speicherort innerhalb von data/profiles
            "last_sample_id": "", # Initialisiert festes Attribut
            "devices": [],
            "last_selected_device_uuid": None
        }

        try:
            with open(profile_file_path, "w") as f:
                json.dump(new_profile_data, f, indent=4)
            self.shared_data.info_manager.status(InfoManager.INFO, f"Profil '{name}' erfolgreich erstellt.")
        except Exception as e:
            self.shared_data.info_manager.status(InfoManager.ERROR, f"Fehler beim Erstellen der Profildatei: {e}")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Erstellen der Profildatei: {e}")
            return

        self.profiles[profile_id] = {"name": name, "path": profile_file_path, "data": new_profile_data}
        self._add_profile_to_table(profile_id, name)

        row_position = self.profile_table.rowCount() - 1
        self.profile_table.selectRow(row_position)
        self.on_profile_change(row_position)
        self.shared_data.info_manager.status(InfoManager.INFO, f"Profil '{name}' ausgewählt.")

    def _add_profile_to_table(self, profile_id, name):
        """Fügt einen Profileintrag zur Profil-QTableWidget hinzu."""
        row_position = self.profile_table.rowCount()
        self.profile_table.insertRow(row_position)
        item = QTableWidgetItem(name)
        item.setData(Qt.ItemDataRole.UserRole, profile_id)
        self.profile_table.setItem(row_position, 0, item)
        self.profile_table.viewport().update()

    def _get_profile_id_from_row(self, row):
        """Ruft die Profil-ID aus einer gegebenen Zeile in der Profiltabelle ab."""
        item = self.profile_table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def on_profile_change(self, row, column=0):
        """
        Behandelt Änderungen der Profilauswahl in der Profiltabelle.
        Aktualisiert UI-Felder, lädt Geometrie und aktualisiert SharedData.
        """
        profile_id = self._get_profile_id_from_row(row)

        if profile_id and profile_id != self.current_profile_id:
            self.current_profile_id = profile_id
            profile_info = self.profiles.get(profile_id)
            if profile_info and "data" in profile_info:
                profile_data = profile_info["data"]
                self.name_field.setText(profile_data.get("name", ""))
                self.label_profile_name_display.setText(profile_data.get("name", ""))
                self.directory_field.setText(profile_data.get("storage_location", ""))
                
                # Aktualisiert das feste Attribut 'last_sample_id'
                self.last_sample_id_field.setText(str(profile_data.get("last_sample_id", "")))
                
                self._save_last_used_profile(profile_data.get("name"))
                
                # Aktualisiert SharedData direkt
                self.shared_data.current_profile = profile_data.copy()
                self.shared_data.current_device = None

                self._load_devices_into_table(profile_data.get("devices", []))
                self._select_last_used_device_in_profile()
                self.shared_data.info_manager.status(InfoManager.INFO, f"Profil '{profile_data.get('name')}' geladen.")
            else:
                self._clear_profile_fields()
                self._clear_device_table()
                self.shared_data.info_manager.status(InfoManager.ERROR, "Profilinformationen konnten nicht geladen werden.")
                QMessageBox.warning(self, "Fehler", "Profilinformationen konnten nicht geladen werden.")
                self.shared_data.current_profile = None
                self.shared_data.current_device = None
        elif not profile_id:
            self._clear_profile_fields()
            self._clear_device_table()
            self.shared_data.current_profile = None
            self.shared_data.current_device = None
            self.shared_data.info_manager.status(InfoManager.INFO, "Kein Profil ausgewählt.")

    def _clear_profile_fields(self):
        """Löscht alle angezeigten Profilfelder (UI) und den internen Zustand für das aktuelle Profil."""
        self.name_field.clear()
        self.label_profile_name_display.clear()
        self.directory_field.clear()
        self.last_sample_id_field.clear() # Löscht auch das Feld für 'last_sample_id'
        self.current_profile_id = None
        self._clear_device_table()

    def load_profiles(self):
        """Lädt alle vorhandenen Profile aus dem Profilverzeichnis in den Speicher und die UI-Tabelle."""
        if not os.path.exists(PROFIL_DIR):
            os.makedirs(PROFIL_DIR)
            self.shared_data.info_manager.status(InfoManager.INFO, f"Profilverzeichnis '{PROFIL_DIR}' erstellt.")

        self.profiles.clear()
        self.profile_table.setRowCount(0)

        for filename in os.listdir(PROFIL_DIR):
            if filename.endswith(".json") and filename != "last_profile.json":
                path = os.path.join(PROFIL_DIR, filename)
                try:
                    with open(path, "r") as f:
                        data = json.load(f)
                        profile_id = data.get("id")
                        name = data.get("name")
                        
                        # Sicherstellen, dass essentielle Schlüssel existieren
                        data.setdefault("devices", [])
                        data.setdefault("last_selected_device_uuid", None)
                        data.setdefault("storage_location", os.path.join(PROFIL_DIR, name)) # Setzt Standard, falls fehlt
                        data.setdefault("last_sample_id", "") # Setzt Standard für festes Attribut

                    if profile_id and name:
                        self.profiles[profile_id] = {"name": name, "path": path, "data": data}
                        self._add_profile_to_table(profile_id, name)
                except json.JSONDecodeError:
                    self.shared_data.info_manager.status(InfoManager.ERROR, f"Fehler beim Laden von Profil '{filename}': Ungültiges JSON-Format.")
                    QMessageBox.warning(self, "Fehler", f"Fehler beim Laden von Profil '{filename}': Ungültiges JSON-Format.")
                    continue
                except Exception as e:
                    self.shared_data.info_manager.status(InfoManager.ERROR, f"Fehler beim Laden von Profil '{filename}': {e}")
                    QMessageBox.warning(self, "Fehler", f"Fehler beim Laden von Profil '{filename}': {e}")
                    continue
        self.shared_data.info_manager.status(InfoManager.INFO, f"{len(self.profiles)} Profile geladen.")
        self._load_last_used_profile()

    def _load_last_used_profile(self):
        """
        Versucht, das zuletzt verwendete Profil basierend auf einem gespeicherten Namen zu laden und auszuwählen.
        Falls nicht gefunden oder keine Profile existieren, wählt es das erste Profil aus oder leert die UI.
        """
        last_used_profile_name = None
        if os.path.exists(LAST_USED_PROFILE_FILE):
            try:
                with open(LAST_USED_PROFILE_FILE, "r") as f:
                    last_used_profile_name = json.load(f)
            except json.JSONDecodeError:
                self.shared_data.info_manager.status(InfoManager.WARNING, f"Fehler beim Laden der letzten Profil-Info: Ungültiges JSON in '{LAST_USED_PROFILE_FILE}'.")
                pass

        selected_row = -1
        if last_used_profile_name:
            for row in range(self.profile_table.rowCount()):
                item = self.profile_table.item(row, 0)
                if item and item.text() == last_used_profile_name:
                    selected_row = row
                    break
        
        if selected_row == -1 and self.profile_table.rowCount() > 0:
            selected_row = 0
            self.shared_data.info_manager.status(InfoManager.INFO, "Zuletzt verwendetes Profil nicht gefunden, wähle erstes Profil aus.")
        
        if selected_row != -1:
            self.profile_table.selectRow(selected_row)
            self.on_profile_change(selected_row)
        else:
            self._clear_profile_fields()
            self._clear_device_table()
            self.shared_data.current_profile = None
            self.shared_data.current_device = None
            self.shared_data.info_manager.status(InfoManager.INFO, "Keine Profile verfügbar oder auswählbar.")
            if os.path.exists(LAST_USED_PROFILE_FILE):
                os.remove(LAST_USED_PROFILE_FILE)
                self.shared_data.info_manager.status(InfoManager.INFO, "Veraltete 'last_profile.json' entfernt.")

    def _save_last_used_profile(self, profile_name):
        """Speichert den Namen des aktuell aktiven Profils in einer Datei."""
        try:
            with open(LAST_USED_PROFILE_FILE, "w") as f:
                json.dump(profile_name, f)
        except Exception as e:
            self.shared_data.info_manager.status(InfoManager.ERROR, f"Fehler beim Speichern des letzten verwendeten Profils: {e}")

    def _is_profile_name_unique(self, name, exclude_current_profile_id=None):
        """Überprüft, ob ein Profilname eindeutig ist (Groß-/Kleinschreibung ignorierend) über alle Profile hinweg."""
        for profile_id, profile_info in self.profiles.items():
            if profile_info["name"].lower() == name.lower() and profile_id != exclude_current_profile_id:
                return False
        return True

    def save_profile_name_change(self):
        """Verarbeitet Änderungen im Profilnamensfeld und aktualisiert die Profildaten."""
        if not self.current_profile_id:
            return

        new_name = self.name_field.text().strip()
        current_profile_info = self.profiles[self.current_profile_id]
        old_name = current_profile_info["name"]

        if new_name == old_name:
            return

        if not new_name:
            self.shared_data.info_manager.status(InfoManager.WARNING, "Profilname darf nicht leer sein. Alter Name wiederhergestellt.")
            QMessageBox.warning(self, "Fehler", "Profilname darf nicht leer sein. Der alte Name wird wiederhergestellt.")
            self.name_field.setText(old_name)
            self.label_profile_name_display.setText(old_name)
            return

        if not self._is_profile_name_unique(new_name, exclude_current_profile_id=self.current_profile_id):
            self.shared_data.info_manager.status(InfoManager.WARNING, f"Profilname '{new_name}' existiert bereits. Alter Name wiederhergestellt.")
            QMessageBox.warning(self, "Fehler", f"Ein Profil mit dem Namen '{new_name}' existiert bereits. Der alte Name wird wiederhergestellt.")
            self.name_field.setText(old_name)
            self.label_profile_name_display.setText(old_name)
            return

        current_profile_info["name"] = new_name
        current_profile_info["data"]["name"] = new_name
        self._save_current_profile_data()

        for row in range(self.profile_table.rowCount()):
            item = self.profile_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == self.current_profile_id:
                item.setText(new_name)
                self.label_profile_name_display.setText(new_name)
                break
        
        self._save_last_used_profile(new_name)
        if self.shared_data.current_profile and self.shared_data.current_profile.get("id") == self.current_profile_id:
            self.shared_data.current_profile["name"] = new_name
        self.shared_data.info_manager.status(InfoManager.INFO, f"Profilname in '{new_name}' geändert.")

    def save_last_sample_id_change(self):
        """
        Aktualisiert das Attribut 'last_sample_id' des aktuellen Profils und speichert es.
        """
        if not self.current_profile_id:
            return

        profile_info = self.profiles.get(self.current_profile_id)
        if not profile_info:
            return

        new_value = self.last_sample_id_field.text().strip()
        profile_data = profile_info["data"]
        profile_data["last_sample_id"] = new_value
        
        self._save_current_profile_data() # Speichert das gesamte Profil
        self.shared_data.info_manager.status(InfoManager.INFO, f"Profil-Attribut 'Letzte Probe ID' zu '{new_value}' aktualisiert.")

    def _select_storage_location(self):
        """
        Öffnet einen Dateidialog, um einen neuen Speicherort für das aktuelle Profil auszuwählen.
        Aktualisiert das directory_field und speichert den Pfad im Profil.
        """
        if not self.current_profile_id:
            self.shared_data.info_manager.status(InfoManager.INFO, "Bitte wählen Sie zuerst ein Profil aus, dessen Speicherort Sie ändern möchten.")
            QMessageBox.information(self, "Hinweis", "Bitte wählen Sie zuerst ein Profil aus, dessen Speicherort Sie ändern möchten.")
            return

        current_path = self.directory_field.text() if self.directory_field.text() else os.path.expanduser("~")
        
        # Öffnet einen Dateidialog, um einen Ordner auszuwählen
        new_dir = QFileDialog.getExistingDirectory(self, "Speicherort auswählen", current_path)

        if new_dir: # Wenn ein Verzeichnis ausgewählt wurde (nicht abgebrochen)
            self.directory_field.setText(new_dir)
            profile_info = self.profiles.get(self.current_profile_id)
            if profile_info:
                profile_info["data"]["storage_location"] = new_dir
                self._save_current_profile_data()
                self.shared_data.info_manager.status(InfoManager.INFO, f"Speicherort für Profil '{profile_info['name']}' auf '{new_dir}' aktualisiert.")
            else:
                self.shared_data.info_manager.status(InfoManager.ERROR, "Fehler: Profilinformationen nicht gefunden, konnte Speicherort nicht aktualisieren.")
        else:
            self.shared_data.info_manager.status(InfoManager.INFO, "Auswahl des Speicherorts abgebrochen.")


    def _save_current_profile_data(self):
        """
        Speichert die Daten des aktuellen Profils in seiner JSON-Datei.
        Aktualisiert auch das SharedData-Objekt.
        """
        if not self.current_profile_id:
            return

        profile_info = self.profiles.get(self.current_profile_id)
        if not profile_info:
            return

        profile_data = profile_info["data"]
        # Sicherstellen, dass Name, storage_location und last_sample_id aus UI-Feldern aktuell sind, bevor gespeichert wird
        profile_data["name"] = self.name_field.text().strip()
        profile_data["storage_location"] = self.directory_field.text().strip()
        profile_data["last_sample_id"] = self.last_sample_id_field.text().strip()
        
        try:
            with open(profile_info["path"], "w") as f:
                json.dump(profile_data, f, indent=4)
            self.shared_data.info_manager.status(InfoManager.INFO, f"Profil '{profile_data['name']}' gespeichert.")
            
            # Aktualisiert SharedData mit einer Kopie der gespeicherten Daten
            if self.shared_data.current_profile and self.shared_data.current_profile.get("id") == self.current_profile_id:
                self.shared_data.current_profile = profile_data.copy()
        except Exception as e:
            self.shared_data.info_manager.status(InfoManager.ERROR, f"Fehler beim Speichern des Profils: {e}")
            QMessageBox.critical(self, "Speichern Fehler", f"Fehler beim Speichern des Profils: {e}")

    def delete_profile(self):
        """Löscht das aktuell ausgewählte Profil und seine zugehörige Datei."""
        if not self.current_profile_id:
            self.shared_data.info_manager.status(InfoManager.INFO, "Bitte wählen Sie ein Profil zum Löschen aus.")
            QMessageBox.information(self, "Hinweis", "Bitte wählen Sie ein Profil zum Löschen aus.")
            return

        profile_info = self.profiles.get(self.current_profile_id)
        if not profile_info:
            return

        profile_name = profile_info["name"]
        reply = QMessageBox.question(self, "Profil löschen",
                                     f"Möchten Sie das Profil '{profile_name}' wirklich löschen?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(profile_info["path"])
                del self.profiles[self.current_profile_id]

                for row in range(self.profile_table.rowCount()):
                    item = self.profile_table.item(row, 0)
                    if item and item.data(Qt.ItemDataRole.UserRole) == self.current_profile_id:
                        self.profile_table.removeRow(row)
                        break

                self._clear_profile_fields()
                self._clear_device_table()
                
                self.shared_data.info_manager.status(InfoManager.INFO, f"Profil '{profile_name}' wurde gelöscht.")

                self.shared_data.current_profile = None
                self.shared_data.current_device = None

                self._load_last_used_profile() # Versucht, ein anderes Profil zu laden
            except OSError as e:
                self.shared_data.info_manager.status(InfoManager.ERROR, f"Fehler beim Löschen der Datei: {e}")
                QMessageBox.critical(self, "Löschen Fehler", f"Fehler beim Löschen der Datei: {e}")
            except Exception as e:
                self.shared_data.info_manager.status(InfoManager.ERROR, f"Ein unerwarteter Fehler ist aufgetreten: {e}")
                QMessageBox.critical(self, "Löschen Fehler", f"Ein unerwarteter Fehler ist aufgetreten: {e}")
        else:
            self.shared_data.info_manager.status(InfoManager.INFO, f"Löschen von Profil '{profile_name}' abgebrochen.")

    # --- Geometriemanagement-Methoden ---
    def _clear_device_table(self):
        """Löscht alle Zeilen aus der Geometrietabelle und hebt die Auswahl des aktuellen Geometries in SharedData auf."""
        self.device_table.setRowCount(0)
        self.shared_data.current_device = None
        self.shared_data.info_manager.status(InfoManager.INFO, "Geometrietabelle geleert.")

    def _load_devices_into_table(self, devices):
        """
        Füllt die Geometrietabelle mit der gegebenen Liste von Geometrien.
        Stellt sicher, dass Geometriedaten für späteren Abruf in UserRole gespeichert werden.
        """
        self._clear_device_table()
        self.device_table.setRowCount(len(devices))
        for row, device in enumerate(devices):
            name_item = QTableWidgetItem(device.get("device_name", "Unbekanntes Geometrie"))
            name_item.setData(Qt.ItemDataRole.UserRole, device) # Speichert das vollständige Geometrie-Dictionary
            self.device_table.setItem(row, 0, name_item)
        self.device_table.viewport().update()
        self.shared_data.info_manager.status(InfoManager.INFO, f"{len(devices)} Geometrie geladen.")

    def _get_device_data_from_row(self, row):
        """Ruft das vollständige Geometrie-Daten-Dictionary aus der UserRole einer gegebenen Geometrietabellenzeile ab."""
        item = self.device_table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def on_device_selection_changed(self, row, column):
        """
        Behandelt die Geometrieauswahl in der Geometrietabelle.
        Aktualisiert shared_data.current_device und speichert die UUID des zuletzt ausgewählten Geometries.
        """
        device = self._get_device_data_from_row(row)
        if device:
            self.shared_data.current_device = device.copy()
            self._save_last_selected_device_in_profile(device.get("uuid"))
            self.shared_data.info_manager.status(InfoManager.INFO, f"Geometrie '{device.get('device_name')}' ausgewählt.")
        else:
            self.shared_data.current_device = None
            self._save_last_selected_device_in_profile(None)
            self.shared_data.info_manager.status(InfoManager.INFO, "Kein Geometrie ausgewählt oder Geometriedaten nicht gefunden.")

    def _select_last_used_device_in_profile(self):
        """
        Wählt das zuletzt verwendete Geometrie im aktuell aktiven Profil aus, falls verfügbar.
        """
        if not self.current_profile_id:
            return

        profile_data = self.profiles[self.current_profile_id]["data"]
        last_selected_uuid = profile_data.get("last_selected_device_uuid")

        if last_selected_uuid:
            for row in range(self.device_table.rowCount()):
                device = self._get_device_data_from_row(row)
                if device and device.get("uuid") == last_selected_uuid:
                    self.device_table.selectRow(row)
                    self.on_device_selection_changed(row, 0)
                    self.shared_data.info_manager.status(InfoManager.INFO, f"Zuletzt verwendetes Geometrie '{device.get('device_name')}' automatisch ausgewählt.")
                    return
            self.shared_data.info_manager.status(InfoManager.WARNING, "Zuletzt verwendetes Geometrie im Profil nicht gefunden.")
        
        if self.device_table.rowCount() > 0:
            self.device_table.selectRow(0)
            self.on_device_selection_changed(0, 0)
            self.shared_data.info_manager.status(InfoManager.INFO, "Kein zuletzt verwendetes Geometrie, erstes Geometrie ausgewählt.")
        else:
            self.shared_data.current_device = None
            self._save_last_selected_device_in_profile(None)
            self.shared_data.info_manager.status(InfoManager.INFO, "Keine Geometrie im aktuellen Profil vorhanden.")

    def _save_last_selected_device_in_profile(self, device_uuid):
        """
        Speichert die UUID des zuletzt ausgewählten Geometries in den Daten des aktuellen Profils.
        """
        if self.current_profile_id:
            profile_data = self.profiles[self.current_profile_id]["data"]
            profile_data["last_selected_device_uuid"] = device_uuid
            self._save_current_profile_data()

    def add_device(self):
        """Öffnet einen Dialog, um ein neues Geometrie zum aktuell ausgewählten Profil hinzuzufügen."""
        if not self.current_profile_id:
            self.shared_data.info_manager.status(InfoManager.INFO, "Bitte wählen Sie zuerst ein Profil aus, dem Sie ein Geometrie hinzufügen möchten.")
            QMessageBox.information(self, "Hinweis", "Bitte wählen Sie zuerst ein Profil aus, dem Sie ein Geometrie hinzufügen möchten.")
            return

        current_profile_data = self.profiles[self.current_profile_id]["data"]
        existing_device_names = [d.get("device_name", "").lower() for d in current_profile_data.get("devices", [])]

        dialog = DeviceDialog(self, existing_device_names=existing_device_names)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_device_data = dialog.device_data

            current_profile_data.setdefault("devices", []).append(new_device_data)
            
            self._save_current_profile_data()
            self._load_devices_into_table(current_profile_data["devices"])
            self.shared_data.info_manager.status(InfoManager.INFO, f"Geometrie '{new_device_data['device_name']}' wurde erfolgreich hinzugefügt.")
            
            self._select_device_by_uuid(new_device_data.get("uuid"))
        else:
            self.shared_data.info_manager.status(InfoManager.INFO, "Geometrie hinzufügen abgebrochen.")

    def edit_device_from_table(self, row, column):
        """Öffnet einen Dialog, um das Geometrie in der gegebenen Zeile der Geometrietabelle zu bearbeiten."""
        if not self.current_profile_id:
            self.shared_data.info_manager.status(InfoManager.WARNING, "Kein Profil zum Bearbeiten eines Geometries ausgewählt.")
            return

        device_to_edit = self._get_device_data_from_row(row)
        if not device_to_edit:
            self.shared_data.info_manager.status(InfoManager.WARNING, "Kein Geometrie in der Zeile gefunden.")
            return

        current_profile_data = self.profiles[self.current_profile_id]["data"]
        existing_device_names = [d.get("device_name", "").lower() for d in current_profile_data.get("devices", []) 
                                 if d.get("device_name") and d.get("uuid") != device_to_edit.get("uuid")]

        dialog = DeviceDialog(self, device_data=device_to_edit.copy(), existing_device_names=existing_device_names)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_device_data = dialog.device_data
            
            # Findet den Index des zu bearbeitenden Geometries und ersetzt es
            device_index = -1
            for i, dev in enumerate(current_profile_data["devices"]):
                if dev.get("uuid") == updated_device_data.get("uuid"):
                    device_index = i
                    break
            
            if device_index != -1:
                current_profile_data["devices"][device_index] = updated_device_data
                self._save_current_profile_data()
                self._load_devices_into_table(current_profile_data["devices"])
                self.shared_data.info_manager.status(InfoManager.INFO, f"Geometrie '{updated_device_data['device_name']}' erfolgreich aktualisiert.")
                self._select_device_by_uuid(updated_device_data.get("uuid"))
            else:
                self.shared_data.info_manager.status(InfoManager.ERROR, "Fehler: Geometrie zum Aktualisieren nicht gefunden.")
                QMessageBox.critical(self, "Fehler", "Geometrie zum Aktualisieren nicht gefunden.")
        else:
            self.shared_data.info_manager.status(InfoManager.INFO, "Geometrie bearbeiten abgebrochen.")

    def show_device_context_menu(self, pos):
        """Zeigt ein Kontextmenü für die Geometrietabelle an, das Bearbeiten und Löschen ermöglicht."""
        item = self.device_table.itemAt(pos)
        if not item:
            return

        context_menu = QMenu(self)
        edit_action = context_menu.addAction("Bearbeiten")
        delete_action = context_menu.addAction("Löschen")
        
        action = context_menu.exec(self.device_table.mapToGlobal(pos))
        
        if action == edit_action:
            self.edit_device_from_table(item.row(), 0)
        elif action == delete_action:
            # KORREKTUR: Hol dir die Daten aus der Zeile
            device_data = self._get_device_data_from_row(item.row())
            if not device_data:
                return

            # Frage nach Bestätigung
            device_name = device_data.get("device_name", "Unbekannt")
            reply = QMessageBox.question(self, "Geometrie löschen",
                                        f"Möchten Sie die Geometrie '{device_name}' wirklich löschen?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                # Rufe die Löschfunktion mit der korrekten UUID auf
                uuid_to_delete = device_data.get("uuid")
                if uuid_to_delete:
                    self.delete_device(uuid_to_delete)

    def delete_device(self, device_uuid):
        """Deletes a device from the current profile by its UUID."""
        if not self.current_profile_id:
            return
        current_profile_data = self.profiles[self.current_profile_id]["data"]
        devices = current_profile_data.get("devices", [])
        device_name_to_delete = ""
        initial_len = len(devices)
        
        # Filter out the device to delete and get its name
        updated_devices = []
        for d in devices:
            if d.get("uuid") == device_uuid:
                device_name_to_delete = d.get("device_name", "Unbekannt")
            else:
                updated_devices.append(d)
        
        if len(updated_devices) < initial_len: # If a device was actually removed
            current_profile_data["devices"] = updated_devices
            self._save_current_profile_data()
            self._load_devices_into_table(current_profile_data["devices"])
            self.shared_data.info_manager.status(InfoManager.INFO, f"Geometrie '{device_name_to_delete}' wurde erfolgreich gelöscht.")
            if self.shared_data.current_device and self.shared_data.current_device.get("uuid") == device_uuid:
                self.shared_data.current_device = None
            self._select_last_used_device_in_profile()
        else:
            self.shared_data.info_manager.status(InfoManager.ERROR, "Geometrie nicht gefunden oder konnte nicht gelöscht werden.")
            QMessageBox.warning(self, "Fehler", "Geometrie nicht gefunden oder konnte nicht gelöscht werden.")

    def _select_device_by_uuid(self, uuid_to_select):
        """
        Selects a device in the device table by its UUID.
        This also triggers on_device_selection_changed to update shared_data.
        """
        if not uuid_to_select:
            self.shared_data.info_manager.status(InfoManager.WARNING, "Keine UUID zum Auswählen des Geometries angegeben.")
            return
        for row in range(self.device_table.rowCount()):
            device = self._get_device_data_from_row(row)
            if device and device.get("uuid") == uuid_to_select:
                self.device_table.selectRow(row)
                self.on_device_selection_changed(row, 0)
                self.shared_data.info_manager.status(InfoManager.INFO, f"Geometrie mit UUID '{uuid_to_select}' ausgewählt.")
                return 
        
        self.shared_data.info_manager.status(InfoManager.WARNING, f"Geometrie mit UUID '{uuid_to_select}' nicht in der Tabelle gefunden.")
        self.shared_data.current_device = None