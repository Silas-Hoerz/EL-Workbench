# tabs/profile_tab.py
# -*- coding: utf-8 -*-
"""
============================================================================
 File:          profile_tab.py
 Author:        Silas Hörz
 Creation date: 2025-07-25
 Last modified: 2025-07-28 (Adapted for direct SharedState usage, refactored)
 Version:       1.1.0
============================================================================
 Description:
    Modul (Tab) für das Anlegen, Laden und Speichern von Profilen.
============================================================================
"""

import os
import json
import uuid
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QAbstractItemView,
    QLineEdit, QMessageBox, QInputDialog, QLabel,
    QDialog, QGroupBox, QHeaderView, QMenu, QSizePolicy
)
from PyQt6.QtCore import QTimer, Qt, QSettings

# Import the DeviceDialog and InfoManager.
from other.info import InfoManager
from other.device_dialog import DeviceDialog

# --- Global Constants and Paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFIL_DIR = os.path.join(BASE_DIR, "data/profiles")
LAST_USED_PROFILE_FILE = os.path.join(PROFIL_DIR, "last_profile.json")

# --- ProfileTab Class Definition ---
class ProfileTab(QWidget):
    """
    Manages user profiles, including profile attributes and associated devices.
    Provides functionality to add, edit, delete profiles and devices.
    This class is primarily responsible for the UI and the underlying file operations.
    It interacts directly with the SharedState object for data sharing.
    """
    def __init__(self, shared_data):
        """
        Initializes the ProfileTab.
        :param shared_data: An object to share data across different parts of the application.
                            It should have attributes like .current_profile and .current_device.
        """
        super().__init__()
        self.shared_data = shared_data
        self.profiles = {}  # Stores profile_id: {name: "...", path: "...", data: {...}}
        self.current_profile_id = None # UUID of the currently selected profile
        self.profile_widgets = {} # Stores QLineEdit widgets for dynamic profile attributes (e.g., storage_location, last_sample_id)
        
        self.settings = QSettings("EL-Workbench", "ProfileTab") # QSettings is used for persistent application settings, not profile data

        self.init_ui()
        QTimer.singleShot(0, self.load_profiles) # Defer loading until UI is shown

    # --- UI Initialization ---
    def init_ui(self):
        """Initializes the user interface elements for the ProfileTab."""
        main_layout = QHBoxLayout(self)

        # Left Panel: Profile Management (Table and Add Button)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        self.button_profile = QPushButton("Profil hinzufügen")
        self.button_profile.clicked.connect(self.add_profile)
        self.button_profile.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        
        button_layout_add_profile = QHBoxLayout()
        button_layout_add_profile.addStretch(1)
        button_layout_add_profile.addWidget(self.button_profile)
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

        # Right Panel: Profile Attributes & Device Management
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Profile Name & Directory
        profile_attr_group = QGroupBox("Profil Details")
        profile_attr_layout = QVBoxLayout(profile_attr_group)
        
        self.label_name = QLabel("Kein Profil ausgewählt") # Initial text
        self.label_name.setObjectName("Title") # For potential CSS styling
        profile_attr_layout.addWidget(self.label_name)

        profile_attr_layout.addWidget(QLabel("Name:"))
        self.name_field = QLineEdit()
        self.name_field.editingFinished.connect(self.save_profile_name_change)
        profile_attr_layout.addWidget(self.name_field)

        profile_attr_layout.addWidget(QLabel("Speicherort:"))
        self.directory_field = QLineEdit()
        self.directory_field.setReadOnly(True) # Directory field is read-only
        profile_attr_layout.addWidget(self.directory_field)

        # Dynamic profile attributes section
        self.profile_attributes_layout = QVBoxLayout()
        profile_attr_layout.addLayout(self.profile_attributes_layout)

        # Add predefined dynamic attributes (moved here for compactness)
        self.add_profile_attribute_field("Letzte Probe ID", "last_sample_id")
        
        right_layout.addWidget(profile_attr_group)

        # Device Management Section
        device_group = QGroupBox("Geräte")
        device_layout = QVBoxLayout(device_group)

        self.device_table = QTableWidget(0, 1) # Only one visible column for name
        self.device_table.setHorizontalHeaderLabels(["Gerätename"])
        self.device_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.device_table.verticalHeader().setVisible(False)
        self.device_table.horizontalHeader().setVisible(False) # Hide header as per original
        self.device_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.device_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.device_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.device_table.cellDoubleClicked.connect(self.edit_device_from_table)
        self.device_table.cellClicked.connect(self.on_device_selection_changed)
        self.device_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.device_table.customContextMenuRequested.connect(self.show_device_context_menu)
        device_layout.addWidget(self.device_table)

        button_layout_add_device = QHBoxLayout()
        self.button_add_device = QPushButton("Gerät hinzufügen")
        self.button_add_device.clicked.connect(self.add_device)
        button_layout_add_device.addWidget(self.button_add_device)
        button_layout_add_device.addStretch(1)
        device_layout.addLayout(button_layout_add_device)
        
        right_layout.addWidget(device_group)

        # Spacer and Delete Profile Button
        right_layout.addStretch()

        delete_button_layout = QHBoxLayout()
        self.delete_profile_button = QPushButton("Profil löschen")
        self.delete_profile_button.clicked.connect(self.delete_profile)
        delete_button_layout.addWidget(self.delete_profile_button)
        delete_button_layout.addStretch(1)
        right_layout.addLayout(delete_button_layout)

        main_layout.addWidget(left_widget, 1)
        main_layout.addWidget(right_widget, 3)

    def add_profile_attribute_field(self, label_text, attribute_key):
        """
        Adds a QLabel and QLineEdit for a profile attribute to the UI.
        The QLineEdit's 'editingFinished' signal is connected to save the attribute.
        """
        h_layout = QHBoxLayout()
        label = QLabel(label_text + ":")
        line_edit = QLineEdit()
        line_edit.editingFinished.connect(lambda: self._save_specific_profile_attribute(attribute_key, line_edit.text()))
        h_layout.addWidget(label)
        h_layout.addWidget(line_edit)
        self.profile_attributes_layout.addLayout(h_layout)
        self.profile_widgets[attribute_key] = line_edit

    # --- Profile Management Methods ---
    def generate_unique_id(self):
        """Generates a globally unique identifier (UUID)."""
        return str(uuid.uuid4())

    def add_profile(self):
        """Prompts the user for a new profile name and creates the profile file and data."""
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
            "storage_location": os.path.join(PROFIL_DIR, name), # Default storage location within data/profiles
            "last_sample_id": "",
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
        """Adds a profile entry to the profile QTableWidget."""
        row_position = self.profile_table.rowCount()
        self.profile_table.insertRow(row_position)
        item = QTableWidgetItem(name)
        item.setData(Qt.ItemDataRole.UserRole, profile_id)
        self.profile_table.setItem(row_position, 0, item)
        self.profile_table.viewport().update()

    def _get_profile_id_from_row(self, row):
        """Retrieves the profile ID from a given row in the profile table."""
        item = self.profile_table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def on_profile_change(self, row, column=0):
        """
        Handles profile selection changes in the profile table.
        Updates UI fields, loads devices, and updates shared data.
        """
        profile_id = self._get_profile_id_from_row(row)

        if profile_id and profile_id != self.current_profile_id:
            self.current_profile_id = profile_id
            profile_info = self.profiles.get(profile_id)
            if profile_info and "data" in profile_info:
                profile_data = profile_info["data"]
                self.name_field.setText(profile_data.get("name", ""))
                self.label_name.setText(profile_data.get("name", ""))
                self.directory_field.setText(profile_data.get("storage_location", ""))
                
                for key, line_edit in self.profile_widgets.items():
                    line_edit.setText(str(profile_data.get(key, "")))
                
                self._save_last_used_profile(profile_data.get("name"))
                
                # Update shared_data directly
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
        """Clears all displayed profile fields (UI) and internal state for current profile."""
        self.name_field.clear()
        self.label_name.clear()
        self.directory_field.clear()
        for line_edit in self.profile_widgets.values():
            line_edit.clear()
        self.current_profile_id = None
        self._clear_device_table()

    def load_profiles(self):
        """Loads all existing profiles from the profiles directory into memory and the UI table."""
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
                        
                        # Ensure essential keys exist
                        data.setdefault("devices", [])
                        data.setdefault("last_selected_device_uuid", None)
                        data.setdefault("storage_location", os.path.join(PROFIL_DIR, name)) # Set default if missing

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
        Attempts to load and select the last used profile based on a stored name.
        If not found or no profiles exist, selects the first profile or clears UI.
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
        """Saves the name of the currently active profile to a file."""
        try:
            with open(LAST_USED_PROFILE_FILE, "w") as f:
                json.dump(profile_name, f)
        except Exception as e:
            self.shared_data.info_manager.status(InfoManager.ERROR, f"Fehler beim Speichern des letzten verwendeten Profils: {e}")

    def _is_profile_name_unique(self, name, exclude_current_profile_id=None):
        """Checks if a profile name is unique (case-insensitive) across all profiles."""
        for profile_id, profile_info in self.profiles.items():
            if profile_info["name"].lower() == name.lower() and profile_id != exclude_current_profile_id:
                return False
        return True

    def save_profile_name_change(self):
        """Handles changes to the profile name field and updates the profile data."""
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
            self.label_name.setText(old_name)
            return

        if not self._is_profile_name_unique(new_name, exclude_current_profile_id=self.current_profile_id):
            self.shared_data.info_manager.status(InfoManager.WARNING, f"Profilname '{new_name}' existiert bereits. Alter Name wiederhergestellt.")
            QMessageBox.warning(self, "Fehler", f"Ein Profil mit dem Namen '{new_name}' existiert bereits. Der alte Name wird wiederhergestellt.")
            self.name_field.setText(old_name)
            self.label_name.setText(old_name)
            return

        current_profile_info["name"] = new_name
        current_profile_info["data"]["name"] = new_name
        self._save_current_profile_data()

        for row in range(self.profile_table.rowCount()):
            item = self.profile_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == self.current_profile_id:
                item.setText(new_name)
                self.label_name.setText(new_name)
                break
        
        self._save_last_used_profile(new_name)
        if self.shared_data.current_profile and self.shared_data.current_profile.get("id") == self.current_profile_id:
            self.shared_data.current_profile["name"] = new_name
        self.shared_data.info_manager.status(InfoManager.INFO, f"Profilname in '{new_name}' geändert.")

    def _save_specific_profile_attribute(self, attribute_key, new_value):
        """
        Updates a specific attribute of the current profile and saves it.
        This is a helper for dynamic QLineEdits.
        """
        if not self.current_profile_id:
            return

        profile_info = self.profiles.get(self.current_profile_id)
        if not profile_info:
            return

        profile_data = profile_info["data"]
        profile_data[attribute_key] = new_value
        
        self._save_current_profile_data() # Save the whole profile
        self.shared_data.info_manager.status(InfoManager.INFO, f"Profil-Attribut '{attribute_key}' zu '{new_value}' aktualisiert.")

    def _save_current_profile_data(self):
        """
        Saves the current profile's data to its JSON file.
        Also updates the shared_data object.
        """
        if not self.current_profile_id:
            return

        profile_info = self.profiles.get(self.current_profile_id)
        if not profile_info:
            return

        profile_data = profile_info["data"]
        # Ensure name and storage_location are up-to-date from UI fields before saving
        profile_data["name"] = self.name_field.text().strip()
        profile_data["storage_location"] = self.directory_field.text().strip() # This should be set elsewhere or directly reflect the file path
        
        try:
            with open(profile_info["path"], "w") as f:
                json.dump(profile_data, f, indent=4)
            self.shared_data.info_manager.status(InfoManager.INFO, f"Profil '{profile_data['name']}' gespeichert.")
            
            # Update shared_data with a copy of the saved data
            if self.shared_data.current_profile and self.shared_data.current_profile.get("id") == self.current_profile_id:
                self.shared_data.current_profile = profile_data.copy()
        except Exception as e:
            self.shared_data.info_manager.status(InfoManager.ERROR, f"Fehler beim Speichern des Profils: {e}")
            QMessageBox.critical(self, "Speichern Fehler", f"Fehler beim Speichern des Profils: {e}")

    def delete_profile(self):
        """Deletes the currently selected profile and its associated file."""
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

                self._load_last_used_profile() # Try to load another profile
            except OSError as e:
                self.shared_data.info_manager.status(InfoManager.ERROR, f"Fehler beim Löschen der Datei: {e}")
                QMessageBox.critical(self, "Löschen Fehler", f"Fehler beim Löschen der Datei: {e}")
            except Exception as e:
                self.shared_data.info_manager.status(InfoManager.ERROR, f"Ein unerwarteter Fehler ist aufgetreten: {e}")
                QMessageBox.critical(self, "Löschen Fehler", f"Ein unerwarteter Fehler ist aufgetreten: {e}")
        else:
            self.shared_data.info_manager.status(InfoManager.INFO, f"Löschen von Profil '{profile_name}' abgebrochen.")

    # --- Device Management Methods ---
    def _clear_device_table(self):
        """Clears all rows from the device table and unselects current device in shared data."""
        self.device_table.setRowCount(0)
        self.shared_data.current_device = None
        self.shared_data.info_manager.status(InfoManager.INFO, "Gerätetabelle geleert.")

    def _load_devices_into_table(self, devices):
        """
        Populates the device table with the given list of devices.
        Ensures device data is stored in UserRole for later retrieval.
        """
        self._clear_device_table()
        self.device_table.setRowCount(len(devices))
        for row, device in enumerate(devices):
            name_item = QTableWidgetItem(device.get("device_name", "Unbekanntes Gerät"))
            name_item.setData(Qt.ItemDataRole.UserRole, device) # Store full device dict
            self.device_table.setItem(row, 0, name_item)
            # Removed column 1 (UUID) as it's hidden and not strictly needed for display
        self.device_table.viewport().update()
        self.shared_data.info_manager.status(InfoManager.INFO, f"{len(devices)} Geräte geladen.")

    def _get_device_data_from_row(self, row):
        """Retrieves the full device data dictionary from a given device table row's UserRole."""
        item = self.device_table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def on_device_selection_changed(self, row, column):
        """
        Handles device selection in the device table.
        Updates shared_data.current_device and saves the last selected device UUID.
        """
        device = self._get_device_data_from_row(row)
        if device:
            self.shared_data.current_device = device.copy()
            self._save_last_selected_device_in_profile(device.get("uuid"))
            self.shared_data.info_manager.status(InfoManager.INFO, f"Gerät '{device.get('device_name')}' ausgewählt.")
        else:
            self.shared_data.current_device = None
            self._save_last_selected_device_in_profile(None)
            self.shared_data.info_manager.status(InfoManager.INFO, "Kein Gerät ausgewählt oder Gerätedaten nicht gefunden.")

    def _select_last_used_device_in_profile(self):
        """
        Selects the last used device in the currently active profile, if available.
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
                    self.shared_data.info_manager.status(InfoManager.INFO, f"Zuletzt verwendetes Gerät '{device.get('device_name')}' automatisch ausgewählt.")
                    return
            self.shared_data.info_manager.status(InfoManager.WARNING, "Zuletzt verwendetes Gerät im Profil nicht gefunden.")
        
        if self.device_table.rowCount() > 0:
            self.device_table.selectRow(0)
            self.on_device_selection_changed(0, 0)
            self.shared_data.info_manager.status(InfoManager.INFO, "Kein zuletzt verwendetes Gerät, erstes Gerät ausgewählt.")
        else:
            self.shared_data.current_device = None
            self._save_last_selected_device_in_profile(None)
            self.shared_data.info_manager.status(InfoManager.INFO, "Keine Geräte im aktuellen Profil vorhanden.")

    def _save_last_selected_device_in_profile(self, device_uuid):
        """
        Saves the UUID of the last selected device within the current profile's data.
        """
        if self.current_profile_id:
            profile_data = self.profiles[self.current_profile_id]["data"]
            profile_data["last_selected_device_uuid"] = device_uuid
            self._save_current_profile_data()

    def add_device(self):
        """Opens a dialog to add a new device to the currently selected profile."""
        if not self.current_profile_id:
            self.shared_data.info_manager.status(InfoManager.INFO, "Bitte wählen Sie zuerst ein Profil aus, dem Sie ein Gerät hinzufügen möchten.")
            QMessageBox.information(self, "Hinweis", "Bitte wählen Sie zuerst ein Profil aus, dem Sie ein Gerät hinzufügen möchten.")
            return

        current_profile_data = self.profiles[self.current_profile_id]["data"]
        existing_device_names = [d.get("device_name", "").lower() for d in current_profile_data.get("devices", [])]

        dialog = DeviceDialog(self, existing_device_names=existing_device_names)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_device_data = dialog.device_data

            current_profile_data.setdefault("devices", []).append(new_device_data)
            
            self._save_current_profile_data()
            self._load_devices_into_table(current_profile_data["devices"])
            self.shared_data.info_manager.status(InfoManager.INFO, f"Gerät '{new_device_data['device_name']}' wurde erfolgreich hinzugefügt.")
            
            self._select_device_by_uuid(new_device_data.get("uuid"))
        else:
            self.shared_data.info_manager.status(InfoManager.INFO, "Gerät hinzufügen abgebrochen.")

    def edit_device_from_table(self, row, column):
        """Opens a dialog to edit the device at the given row in the device table."""
        if not self.current_profile_id:
            self.shared_data.info_manager.status(InfoManager.WARNING, "Kein Profil zum Bearbeiten eines Geräts ausgewählt.")
            return

        device_to_edit = self._get_device_data_from_row(row)
        if not device_to_edit:
            self.shared_data.info_manager.status(InfoManager.WARNING, "Kein Gerät in der Zeile gefunden.")
            return

        current_profile_data = self.profiles[self.current_profile_id]["data"]
        existing_device_names = [d.get("device_name", "").lower() for d in current_profile_data.get("devices", []) 
                                 if d.get("device_name") and d.get("uuid") != device_to_edit.get("uuid")]

        dialog = DeviceDialog(self, device_data=device_to_edit.copy(), existing_device_names=existing_device_names)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_device_data = dialog.device_data
            
            device_found = False
            for i, device in enumerate(current_profile_data["devices"]):
                if device.get("uuid") == updated_device_data.get("uuid"):
                    current_profile_data["devices"][i] = updated_device_data
                    device_found = True
                    break
            
            if device_found:
                self._save_current_profile_data()
                self._load_devices_into_table(current_profile_data["devices"])
                self.shared_data.info_manager.status(InfoManager.INFO, f"Gerät '{updated_device_data['device_name']}' wurde erfolgreich aktualisiert.")
                self._select_device_by_uuid(updated_device_data.get("uuid")) 
            else:
                self.shared_data.info_manager.status(InfoManager.ERROR, "Gerät zur Aktualisierung im Profil nicht gefunden.")
                QMessageBox.warning(self, "Fehler", "Gerät zur Aktualisierung im Profil nicht gefunden.")

        elif getattr(dialog, 'delete_confirmed', False): # Check if delete was confirmed in dialog
            self.delete_device(device_to_edit.get("uuid"))
        else:
            self.shared_data.info_manager.status(InfoManager.INFO, "Gerät bearbeiten abgebrochen.")

    def show_device_context_menu(self, pos):
        """Shows a context menu (Bearbeiten, Löschen) for the device table."""
        if not self.current_profile_id:
            self.shared_data.info_manager.status(InfoManager.INFO, "Kein Profil ausgewählt, Kontextmenü für Gerät ist nicht verfügbar.")
            return
        item = self.device_table.itemAt(pos)
        if item:
            row = item.row()
            menu = QMenu(self)
            edit_action = menu.addAction("Bearbeiten")
            delete_action = menu.addAction("Löschen")
            action = menu.exec(self.device_table.mapToGlobal(pos))
            if action == edit_action:
                self.edit_device_from_table(row, 0)
            elif action == delete_action:
                device_to_delete = self._get_device_data_from_row(row)
                if device_to_delete:
                    reply = QMessageBox.question(self, "Gerät löschen",
                                                 f"Möchten Sie das Gerät '{device_to_delete.get('device_name', 'Unbekannt')}' wirklich löschen?",
                                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if reply == QMessageBox.StandardButton.Yes:
                        self.delete_device(device_to_delete.get("uuid"))
                    else:
                        self.shared_data.info_manager.status(InfoManager.INFO, f"Löschen von Gerät '{device_to_delete.get('device_name', 'Unbekannt')}' abgebrochen.")

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
            self.shared_data.info_manager.status(InfoManager.INFO, f"Gerät '{device_name_to_delete}' wurde erfolgreich gelöscht.")
            if self.shared_data.current_device and self.shared_data.current_device.get("uuid") == device_uuid:
                self.shared_data.current_device = None
            self._select_last_used_device_in_profile()
        else:
            self.shared_data.info_manager.status(InfoManager.ERROR, "Gerät nicht gefunden oder konnte nicht gelöscht werden.")
            QMessageBox.warning(self, "Fehler", "Gerät nicht gefunden oder konnte nicht gelöscht werden.")

    def _select_device_by_uuid(self, uuid_to_select):
        """
        Selects a device in the device table by its UUID.
        This also triggers on_device_selection_changed to update shared_data.
        """
        if not uuid_to_select:
            self.shared_data.info_manager.status(InfoManager.WARNING, "Keine UUID zum Auswählen des Geräts angegeben.")
            return
        for row in range(self.device_table.rowCount()):
            device = self._get_device_data_from_row(row)
            if device and device.get("uuid") == uuid_to_select:
                self.device_table.selectRow(row)
                self.on_device_selection_changed(row, 0)
                self.shared_data.info_manager.status(InfoManager.INFO, f"Gerät mit UUID '{uuid_to_select}' ausgewählt.")
                return 
        
        self.shared_data.info_manager.status(InfoManager.WARNING, f"Gerät mit UUID '{uuid_to_select}' nicht in der Tabelle gefunden.")
        self.shared_data.current_device = None