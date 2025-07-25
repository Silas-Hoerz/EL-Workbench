import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QAbstractItemView,
    QLineEdit, QMessageBox, QInputDialog, QLabel,
    QDialog, QDialogButtonBox, QGroupBox, QHeaderView, QMenu
)
from PyQt6.QtCore import QTimer, Qt
import uuid

from other.device_dialog import DeviceDialog

# Re-import DeviceDialog here or ensure it's in the same file
# from .device_dialog import DeviceDialog # If in a separate file
# Assuming DeviceDialog is defined above or in this file for simplicity

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFIL_DIR = os.path.join(BASE_DIR, "profiles")
LAST_USED_PROFILE_FILE = os.path.join(PROFIL_DIR, "last_profile.json")

class ProfileTab(QWidget):
    def __init__(self, shared_data):
        super().__init__()
        self.shared_data = shared_data
        self.profiles = {}  # Stores profile_id: {name: "...", path: "...", data: {...}}
        self.current_profile_id = None
        self.profile_widgets = {} # Stores QLineEdit widgets for profile attributes

        self.init_ui()

    def init_ui(self):
        # Hauptlayout
        layout = QHBoxLayout(self)

        # *********************************************************************************
        # Linker Bereich (Profile Management)
        # *********************************************************************************
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Button "Add Profile"
        self.button_profile = QPushButton("Profil hinzufügen")
        self.button_profile.clicked.connect(self.add_profile)
        left_layout.addWidget(self.button_profile)

        # Tabelle für Profile
        self.profile_table = QTableWidget(0, 1)
        self.profile_table.setHorizontalHeaderLabels(["Profilname"])
        self.profile_table.verticalHeader().setVisible(False)
        self.profile_table.horizontalHeader().setVisible(True)
        self.profile_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.profile_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.profile_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.profile_table.cellClicked.connect(self.on_profile_change)
        self.profile_table.horizontalHeader().setStretchLastSection(True)
        self.profile_table.setAlternatingRowColors(True)

        self.profile_table.setMinimumWidth(150)
        left_layout.addWidget(self.profile_table)

        # *********************************************************************************
        # Rechter Bereich (Profile Attributes & Device Management)
        # *********************************************************************************
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        profile_attr_layout = QVBoxLayout() 

        # Profilname
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_field = QLineEdit()
        self.name_field.editingFinished.connect(self.save_profile_name_change)
        name_layout.addWidget(self.name_field)
        profile_attr_layout.addLayout(name_layout)

        # Dynamische Felder für Profileigenschaften
        self.profile_attributes_layout = QVBoxLayout()
        profile_attr_layout.addLayout(self.profile_attributes_layout)

        # Example attributes (you can extend this as needed)
        self.add_profile_attribute_field("Speicherort", "storage_location")
        self.add_profile_attribute_field("Last Sample ID", "last_sample_id")

        right_layout.addLayout(profile_attr_layout)

        # --- Device Management Section ---
        device_layout = QVBoxLayout()

        self.device_table = QTableWidget(0, 2) # 2 columns: Device Name, UUID (hidden)
        self.device_table.setHorizontalHeaderLabels(["Gerätename", "UUID"])
        self.device_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) # Stretch name column
        self.device_table.setColumnHidden(1, True) # Hide UUID column
        self.device_table.verticalHeader().setVisible(False)
        self.device_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.device_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.device_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.device_table.cellDoubleClicked.connect(self.edit_device_from_table) # Double click to edit
        self.device_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu) # For right-click
        self.device_table.customContextMenuRequested.connect(self.show_device_context_menu)

        device_layout.addWidget(self.device_table)

        self.button_add_device = QPushButton("Gerät hinzufügen")
        self.button_add_device.clicked.connect(self.add_device)
        device_layout.addWidget(self.button_add_device)

        right_layout.addLayout(device_layout)
        # --- End Device Management Section ---


        right_layout.addStretch() # Pushes content to the top

        # Delete Profile Button
        self.delete_profile_button = QPushButton("Profil löschen")
        self.delete_profile_button.clicked.connect(self.delete_profile)
        right_layout.addWidget(self.delete_profile_button)

        # Layouts zusammenführen
        layout.addWidget(left_widget)
        layout.addWidget(right_widget)
        layout.addStretch() # Pushes content to the left side

        QTimer.singleShot(0, self.load_profiles)  # Lädt beim ersten Anzeigen

    def add_profile_attribute_field(self, label_text, attribute_key):
        """Adds a QLabel and QLineEdit for a profile attribute."""
        h_layout = QHBoxLayout()
        label = QLabel(label_text + ":")
        line_edit = QLineEdit()
        line_edit.editingFinished.connect(lambda: self.save_current_profile_data(attribute_key, line_edit.text()))
        h_layout.addWidget(label)
        h_layout.addWidget(line_edit)
        self.profile_attributes_layout.addLayout(h_layout)
        self.profile_widgets[attribute_key] = line_edit

    def generate_unique_id(self):
        """Generates a simple unique ID."""
        return str(uuid.uuid4())

    def add_profile(self):
        """Prompts for a new profile name and creates the profile."""
        while True:
            name, ok = QInputDialog.getText(self, "Neues Profil", "Profilnamen eingeben:")
            if not ok:
                return  # User cancelled

            name = name.strip()
            if not name:
                QMessageBox.warning(self, "Fehler", "Profilname darf nicht leer sein.")
                continue

            if self.is_profile_name_unique(name):
                break
            else:
                QMessageBox.warning(self, "Fehler", f"Ein Profil mit dem Namen '{name}' existiert bereits. Bitte wählen Sie einen anderen Namen.")

        profile_id = self.generate_unique_id()
        profile_file_path = os.path.join(PROFIL_DIR, f"{profile_id}.json")
        new_profile_data = {
            "id": profile_id,
            "name": name,
            "storage_location": "",
            "last_sample_id": "",
            "devices": [] # Initialize with an empty list for devices
        }

        with open(profile_file_path, "w") as f:
            json.dump(new_profile_data, f, indent=4)

        self.profiles[profile_id] = {"name": name, "path": profile_file_path, "data": new_profile_data}
        self.add_profile_to_table(profile_id, name)

        # Select the newly created profile
        row_position = self.profile_table.rowCount() - 1
        self.profile_table.selectRow(row_position)
        self.on_profile_change(row_position, 0) # Call with column 0 as it's a cell click

    def add_profile_to_table(self, profile_id, name):
        """Adds a profile to the QTableWidget."""
        row_position = self.profile_table.rowCount()
        self.profile_table.insertRow(row_position)
        item = QTableWidgetItem(name)
        item.setData(Qt.ItemDataRole.UserRole, profile_id)  # Store profile_id in item's UserRole
        self.profile_table.setItem(row_position, 0, item)
        self.profile_table.viewport().update()

    def get_profile_id_from_row(self, row):
        """Retrieves the profile ID from a given table row."""
        item = self.profile_table.item(row, 0)
        if item:
            return item.data(Qt.ItemDataRole.UserRole) # Get data from UserRole
        return None

    def on_profile_change(self, row, column=0):
        """Event: Profile selection changed in the profile table."""
        profile_id = self.get_profile_id_from_row(row)

        if profile_id and profile_id != self.current_profile_id:
            self.current_profile_id = profile_id
            profile_info = self.profiles.get(profile_id)
            if profile_info and "data" in profile_info:
                profile_data = profile_info["data"]
                self.name_field.setText(profile_data.get("name", ""))
                
                # Update dynamic profile attribute fields
                for key, line_edit in self.profile_widgets.items():
                    line_edit.setText(str(profile_data.get(key, "")))
                
                self.save_last_used_profile(profile_data.get("name"))
                
                # Update the shared_data object with the full profile data
                self.shared_data.current_profile = profile_data.copy()

                # Load and display devices for the selected profile
                self.load_devices_into_table(profile_data.get("devices", []))

            else:
                self.clear_profile_fields()
                self.clear_device_table()
                QMessageBox.warning(self, "Fehler", "Profilinformationen konnten nicht geladen werden.")
                self.shared_data.current_profile = None
        elif not profile_id:
            self.clear_profile_fields()
            self.clear_device_table()
            self.shared_data.current_profile = None

    def clear_profile_fields(self):
        """Clears all displayed profile fields."""
        self.name_field.clear()
        for line_edit in self.profile_widgets.values():
            line_edit.clear()
        self.current_profile_id = None
        self.clear_device_table() # Also clear device table when no profile is selected

    def load_profiles(self):
        """Loads all existing profiles from the profiles directory."""
        if not os.path.exists(PROFIL_DIR):
            os.makedirs(PROFIL_DIR)

        self.profiles.clear()
        self.profile_table.setRowCount(0) # Clear existing profile table rows

        for filename in os.listdir(PROFIL_DIR):
            if filename.endswith(".json") and filename != "last_profile.json":
                path = os.path.join(PROFIL_DIR, filename)
                try:
                    with open(path, "r") as f:
                        data = json.load(f)
                        profile_id = data.get("id")
                        name = data.get("name")
                        # Ensure 'devices' key exists, if not, add an empty list
                        if "devices" not in data:
                            data["devices"] = []
                            # Optionally save immediately to update file, but it will be saved on next attribute change anyway
                            # with open(path, "w") as fw:
                            #     json.dump(data, fw, indent=4)

                        if profile_id and name:
                            self.profiles[profile_id] = {"name": name, "path": path, "data": data}
                            self.add_profile_to_table(profile_id, name)
                except json.JSONDecodeError:
                    QMessageBox.warning(self, "Fehler", f"Fehler beim Laden von Profil '{filename}': Ungültiges JSON-Format.")
                    continue
                except Exception as e:
                    QMessageBox.warning(self, "Fehler", f"Fehler beim Laden von Profil '{filename}': {e}")
                    continue

        self.load_last_used_profile()

    def load_last_used_profile(self):
        """Loads and selects the last used profile."""
        if os.path.exists(LAST_USED_PROFILE_FILE):
            with open(LAST_USED_PROFILE_FILE, "r") as f:
                try:
                    last_used_profile_name = json.load(f)
                    # Find the row by profile name
                    for row in range(self.profile_table.rowCount()):
                        item = self.profile_table.item(row, 0)
                        if item and item.text() == last_used_profile_name:
                            self.profile_table.selectRow(row)
                            self.on_profile_change(row, 0)
                            return
                except json.JSONDecodeError:
                    pass  # File might be empty or corrupted, just ignore

        # If no last profile or not found, select the first profile if available
        if self.profile_table.rowCount() > 0:
            self.profile_table.selectRow(0)
            self.on_profile_change(0, 0)
        else:
            # If no profiles exist at all, ensure shared_data.current_profile is None
            self.shared_data.current_profile = None

    def save_last_used_profile(self, profile_name):
        """Saves the name of the currently active profile as the last used."""
        try:
            with open(LAST_USED_PROFILE_FILE, "w") as f:
                json.dump(profile_name, f)
        except Exception as e:
            print(f"Error saving last used profile: {e}")

    def is_profile_name_unique(self, name, exclude_current_profile_id=None):
        """Checks if a profile name is unique across all profiles."""
        for profile_id, profile_info in self.profiles.items():
            if profile_info["name"].lower() == name.lower() and profile_id != exclude_current_profile_id:
                return False
        return True

    def save_profile_name_change(self):
        """Handles changes to the profile name field."""
        if not self.current_profile_id:
            return

        new_name = self.name_field.text().strip()
        current_profile_info = self.profiles[self.current_profile_id]
        old_name = current_profile_info["name"]

        if new_name == old_name:
            return # No change

        if not new_name:
            QMessageBox.warning(self, "Fehler", "Profilname darf nicht leer sein. Der alte Name wird wiederhergestellt.")
            self.name_field.setText(old_name)
            return

        if not self.is_profile_name_unique(new_name, exclude_current_profile_id=self.current_profile_id):
            QMessageBox.warning(self, "Fehler", f"Ein Profil mit dem Namen '{new_name}' existiert bereits. Der alte Name wird wiederhergestellt.")
            self.name_field.setText(old_name)
            return

        # Update profile name in memory and file
        current_profile_info["name"] = new_name
        current_profile_info["data"]["name"] = new_name
        self.save_current_profile_data()

        # Update profile table item
        for row in range(self.profile_table.rowCount()):
            item = self.profile_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == self.current_profile_id:
                item.setText(new_name)
                break
        
        self.save_last_used_profile(new_name)
        # Update shared_data if the name was changed
        if self.shared_data.current_profile and self.shared_data.current_profile.get("id") == self.current_profile_id:
            self.shared_data.current_profile["name"] = new_name


    def save_current_profile_data(self, attribute_key=None, new_value=None):
        """Saves the current profile's data to its JSON file.
        If attribute_key and new_value are provided, updates that specific attribute."""
        if not self.current_profile_id:
            return

        profile_info = self.profiles.get(self.current_profile_id)
        if not profile_info:
            return

        profile_data = profile_info["data"]

        if attribute_key and new_value is not None:
            profile_data[attribute_key] = new_value
        
        # Ensure the name field is also reflected in the data
        profile_data["name"] = self.name_field.text().strip()

        try:
            with open(profile_info["path"], "w") as f:
                json.dump(profile_data, f, indent=4)
            
            # Update the shared_data object after saving
            if self.shared_data.current_profile and self.shared_data.current_profile.get("id") == self.current_profile_id:
                self.shared_data.current_profile = profile_data.copy() # Make a copy to avoid direct modification issues
        except Exception as e:
            QMessageBox.critical(self, "Speichern Fehler", f"Fehler beim Speichern des Profils: {e}")

    def delete_profile(self):
        """Deletes the currently selected profile."""
        if not self.current_profile_id:
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

                # Remove from profile table
                for row in range(self.profile_table.rowCount()):
                    item = self.profile_table.item(row, 0)
                    if item and item.data(Qt.ItemDataRole.UserRole) == self.current_profile_id:
                        self.profile_table.removeRow(row)
                        break

                self.clear_profile_fields()
                self.clear_device_table() # Also clear device table
                QMessageBox.information(self, "Erfolg", f"Profil '{profile_name}' wurde gelöscht.")
                
                # Set shared_data.current_profile to None as the profile is deleted
                self.shared_data.current_profile = None

                # Try to load the last used profile or the first one after deletion
                self.load_last_used_profile()
                if not self.current_profile_id and self.profile_table.rowCount() > 0:
                    self.profile_table.selectRow(0)
                    self.on_profile_change(0, 0)
                elif self.profile_table.rowCount() == 0:
                    # If no profiles left, clear last used profile file
                    if os.path.exists(LAST_USED_PROFILE_FILE):
                        os.remove(LAST_USED_PROFILE_FILE)

            except OSError as e:
                QMessageBox.critical(self, "Löschen Fehler", f"Fehler beim Löschen der Datei: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Löschen Fehler", f"Ein unerwarteter Fehler ist aufgetreten: {e}")

    # --- Device Management Methods ---
    def clear_device_table(self):
        """Clears all rows from the device table."""
        self.device_table.setRowCount(0)

    def load_devices_into_table(self, devices):
        """Populates the device table with the given list of devices."""
        self.clear_device_table()
        self.device_table.setRowCount(len(devices))
        for row, device in enumerate(devices):
            name_item = QTableWidgetItem(device.get("device_name", "Unbekanntes Gerät"))
            uuid_item = QTableWidgetItem(device.get("uuid", ""))
            
            # Store full device data in UserRole for easy retrieval
            name_item.setData(Qt.ItemDataRole.UserRole, device)
            
            self.device_table.setItem(row, 0, name_item)
            self.device_table.setItem(row, 1, uuid_item) # UUID is hidden
        self.device_table.viewport().update()


    def get_device_data_from_row(self, row):
        """Retrieves the full device data dictionary from a given device table row."""
        item = self.device_table.item(row, 0)
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None

    def add_device(self):
        """Opens a dialog to add a new device to the current profile."""
        if not self.current_profile_id:
            QMessageBox.information(self, "Hinweis", "Bitte wählen Sie zuerst ein Profil aus, dem Sie ein Gerät hinzufügen möchten.")
            return

        current_profile_data = self.profiles[self.current_profile_id]["data"]
        # Convert existing names to lowercase for case-insensitive uniqueness check
        existing_device_names = [d.get("device_name", "").lower() for d in current_profile_data.get("devices", [])]

        dialog = DeviceDialog(self, existing_device_names=existing_device_names)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_device_data = dialog.device_data # This now contains shape_type, custom_area_enabled etc.

            if "devices" not in current_profile_data:
                current_profile_data["devices"] = []
            current_profile_data["devices"].append(new_device_data)
            
            self.save_current_profile_data() # Save the profile with the new device
            self.load_devices_into_table(current_profile_data["devices"]) # Refresh device table
            QMessageBox.information(self, "Gerät hinzugefügt", f"Gerät '{new_device_data['device_name']}' wurde erfolgreich hinzugefügt.")
        
    def edit_device_from_table(self, row, column):
        """Opens a dialog to edit the device at the given row in the device table."""
        if not self.current_profile_id:
            return

        device_to_edit = self.get_device_data_from_row(row)
        if not device_to_edit:
            return

        current_profile_data = self.profiles[self.current_profile_id]["data"]
        # Get existing names, excluding the one we are currently editing, and convert to lowercase
        existing_device_names = [d.get("device_name", "").lower() for d in current_profile_data.get("devices", []) 
                                 if d.get("device_name") and d.get("uuid") != device_to_edit.get("uuid")]

        dialog = DeviceDialog(self, device_data=device_to_edit.copy(), existing_device_names=existing_device_names)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_device_data = dialog.device_data # This contains the updated data
            
            # --- START OF REQUIRED CHANGES ---
            # Find and update the device in the profile's data list
            device_found = False
            for i, device in enumerate(current_profile_data["devices"]):
                if device.get("uuid") == updated_device_data.get("uuid"):
                    current_profile_data["devices"][i] = updated_device_data
                    device_found = True
                    break
            
            if device_found:
                self.save_current_profile_data() # <<< THIS IS THE CRUCIAL LINE
                self.load_devices_into_table(current_profile_data["devices"]) # Refresh device table
                QMessageBox.information(self, "Gerät aktualisiert", f"Gerät '{updated_device_data['device_name']}' wurde erfolgreich aktualisiert.")
            else:
                QMessageBox.warning(self, "Fehler", "Gerät zur Aktualisierung im Profil nicht gefunden.")
            # --- END OF REQUIRED CHANGES ---

        elif getattr(dialog, 'delete_confirmed', False): # Check custom flag for delete action
            self.delete_device(device_to_edit.get("uuid"))


    def show_device_context_menu(self, pos):
        """Shows a context menu for the device table."""
        if not self.current_profile_id:
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
                device_to_delete = self.get_device_data_from_row(row)
                if device_to_delete:
                    self.delete_device(device_to_delete.get("uuid"))

    def delete_device(self, device_uuid):
        """Deletes a device from the current profile by its UUID."""
        if not self.current_profile_id:
            return

        current_profile_data = self.profiles[self.current_profile_id]["data"]
        devices = current_profile_data.get("devices", [])

        device_name_to_delete = ""
        initial_len = len(devices)
        # Filter out the device to delete
        updated_devices = [d for d in devices if d.get("uuid") != device_uuid]
        
        for d in devices:
            if d.get("uuid") == device_uuid:
                device_name_to_delete = d.get("device_name", "Unbekannt")
                break

        if len(updated_devices) < initial_len: # If a device was actually removed
            current_profile_data["devices"] = updated_devices
            self.save_current_profile_data() # Save the profile after deletion
            self.load_devices_into_table(current_profile_data["devices"]) # Refresh device table
            QMessageBox.information(self, "Gerät gelöscht", f"Gerät '{device_name_to_delete}' wurde erfolgreich gelöscht.")
        else:
            QMessageBox.warning(self, "Fehler", "Gerät nicht gefunden oder konnte nicht gelöscht werden.")