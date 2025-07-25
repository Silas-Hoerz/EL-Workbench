# api/profile_api.py

"""
ANLEITUNG FÜR DEN ZUGRIFF AUF PROFIL- UND GERÄTEDATEN (Profil-API)

Für einen robusten und konsistenten Zugriff auf die Daten des aktuell
ausgewählten Profils und Geräts aus anderen Programmteilen (z.B. anderen Tabs
oder dem MainWindow) wird die 'ProfileApi'-Klasse empfohlen.

Die 'ProfileApi' kapselt die Interaktion mit diesem ProfileTab und dem
zentralen 'shared_data'-Objekt und bietet klare Getter und Setter.

--- WICHTIG: Setup in Ihrer Hauptanwendung (z.B. main.py oder main_window.py) ---

1.  Importieren Sie die notwendigen Klassen:
    from PyQt6.QtCore import QObject
    from tabs.profile_tab import ProfileTab # Pfad zu dieser Datei
    from api.profile_api import ProfileApi  # Pfad zu Ihrer neuen API-Datei

2.  Erstellen Sie ein 'shared_data'-Objekt (dieses sollte global für Ihre Anwendung sein):
    class SharedData(QObject): # Erbt von QObject, falls Sie Signals/Slots verwenden möchten
        def __init__(self):
            super().__init__()
            self.current_profile = None # Wird ein dict des ausgewählten Profils halten
            self.current_device = None  # Wird ein dict des ausgewählten Geräts halten

    # ... in Ihrer MainWindow- oder Anwendungs-Klasse ...
    self.shared_data = SharedData()

3.  Instanziieren Sie den ProfileTab und übergeben Sie 'shared_data':
    self.profile_tab = ProfileTab(self.shared_data)

4.  Instanziieren Sie die ProfileApi und übergeben Sie 'shared_data' UND die 'profile_tab_instance':
    self.profile_api = ProfileApi(self.shared_data, self.profile_tab)

5.  Geben Sie 'self.profile_api' an andere Tabs oder Module weiter, die Daten benötigen.
    Beispiel für einen anderen Tab:
    self.other_tab = MyOtherTab(self.shared_data, self.profile_api)
    # Beachten Sie, dass MyOtherTab nun beide Objekte für maximale Flexibilität erhält.

--- ZUGRIFF AUF DATEN VON ANDEREN PROGRAMMTEILEN (z.B. MyOtherTab) ---

Angenommen, Sie haben 'self.profile_api' in Ihrem Tab verfügbar:

A. Attribut eines Profils auslesen:
   profile_name = self.profile_api.get_profile_attribute("name")
   storage_loc = self.profile_api.get_profile_attribute("storage_location", "Nicht definiert")
   print(f"Profilname: {profile_name}, Speicherort: {storage_loc}")

B. Attribut eines Profils setzen/ändern (wird automatisch gespeichert und in shared_data aktualisiert):
   self.profile_api.set_profile_attribute("last_sample_id", "SAMPLE-007")
   self.profile_api.set_profile_attribute("new_custom_setting", 123.45) # Wenn nicht vorhanden, wird es angelegt

C. Attribut eines Geräts auslesen (Gerätedaten sind read-only über die API für Konsistenz):
   device_name = self.profile_api.get_device_attribute("device_name")
   device_area = self.profile_api.get_device_area_m2() # Spezifische Helferfunktion für Fläche
   print(f"Gerätename: {device_name}, Fläche: {device_area} m²")

D. Prüfen, ob Profil/Gerät ausgewählt ist:
   if self.profile_api.is_profile_selected():
       print("Ein Profil ist ausgewählt.")
   if self.profile_api.is_device_selected():
       print("Ein Gerät ist ausgewählt.")

"""
from PyQt6.QtWidgets import QMessageBox

class ProfileApi:
    """
    Stellt eine Schnittstelle für den robusten und konsistenten Zugriff auf
    die Daten des aktuell ausgewählten Profils und Geräts bereit.
    Diese Klasse kapselt die Interaktion mit dem ProfileTab und dem shared_data-Objekt.
    """
    def __init__(self, shared_data, profile_tab_instance):
        """
        Initialisiert die ProfileApi.
        :param shared_data: Das globale shared_data-Objekt.
        :param profile_tab_instance: Eine Referenz zur Instanz des ProfileTab.
                                     Diese ist notwendig, um Änderungen zu speichern.
        """
        self.shared_data = shared_data
        self._profile_tab = profile_tab_instance # Interne Referenz zum ProfileTab

    # --- Zugriff auf das aktuelle Profil ---
    def get_current_profile_data(self):
        """
        Gibt eine Kopie der vollständigen Daten des aktuell ausgewählten Profils zurück.
        Gibt None zurück, wenn kein Profil ausgewählt ist.
        """
        if self.shared_data.current_profile:
            return self.shared_data.current_profile.copy()
        return None

    def get_profile_attribute(self, key, default=None):
        """
        Liest ein spezifisches Attribut aus dem aktuell ausgewählten Profil.
        :param key: Der Schlüssel des Attributs (z.B. "name", "storage_location").
        :param default: Der Standardwert, der zurückgegeben wird, wenn das Attribut nicht existiert.
        :return: Der Wert des Attributs oder der Standardwert.
        """
        profile_data = self.get_current_profile_data()
        if profile_data:
            return profile_data.get(key, default)
        return default # Kein Profil ausgewählt

    def set_profile_attribute(self, key, value):
        """
        Setzt oder aktualisiert ein Attribut für das aktuell ausgewählte Profil.
        Falls das Attribut nicht existiert, wird es neu angelegt.
        Diese Methode speichert die Änderung automatisch in der Profildatei
        und aktualisiert shared_data.
        :param key: Der Schlüssel des Attributs (z.B. "new_setting", "storage_location").
        :param value: Der neue Wert des Attributs.
        """
        if not self._profile_tab:
            QMessageBox.critical(None, "API Fehler", "ProfileTab Instanz nicht verfügbar für Speicherung.")
            return

        if not self.shared_data.current_profile:
            QMessageBox.warning(None, "Profil API", "Kein Profil ausgewählt, um Attribut zu setzen.")
            return

        # Delegiere die Aufgabe an die update_profile_attribute Methode im ProfileTab
        # Diese Methode kümmert sich um die Speicherung und UI-Aktualisierung (falls Attribut ein UI-Feld hat)
        self._profile_tab.update_profile_attribute(key, value)
        print(f"Profil-Attribut '{key}' auf '{value}' gesetzt/aktualisiert.")

    # --- Zugriff auf das aktuell ausgewählte Gerät ---
    def get_current_device_data(self):
        """
        Gibt eine Kopie der vollständigen Daten des aktuell ausgewählten Geräts zurück.
        Gibt None zurück, wenn kein Gerät ausgewählt ist.
        """
        if self.shared_data.current_device:
            return self.shared_data.current_device.copy()
        return None

    def get_device_attribute(self, key, default=None):
        """
        Liest ein spezifisches Attribut aus dem aktuell ausgewählten Gerät.
        :param key: Der Schlüssel des Attributs (z.B. "device_name", "Area").
        :param default: Der Standardwert, der zurückgegeben wird, wenn das Attribut nicht existiert.
        :return: Der Wert des Attributs oder der Standardwert.
        """
        device_data = self.get_current_device_data()
        if device_data:
            return device_data.get(key, default)
        return default # Kein Gerät ausgewählt

    def get_device_area_m2(self):
        """
        Gibt die Fläche des aktuell ausgewählten Geräts in Quadratmetern (m²) zurück.
        """
        return self.get_device_attribute("Area", 0.0)

    # --- Nützliche Funktionen ---
    def is_profile_selected(self):
        """Überprüft, ob aktuell ein Profil ausgewählt ist."""
        return self.shared_data.current_profile is not None

    def is_device_selected(self):
        """Überprüft, ob aktuell ein Gerät ausgewählt ist."""
        return self.shared_data.current_device is not None

    def get_profile_name(self):
        """Gibt den Namen des aktuell ausgewählten Profils zurück."""
        return self.get_profile_attribute("name", "Kein Profil")

    def get_device_name(self):
        """Gibt den Namen des aktuell ausgewählten Geräts zurück."""
        return self.get_device_attribute("device_name", "Kein Gerät")

    # Weitere nützliche Funktionen könnten hier hinzugefügt werden, z.B.:
    # def get_all_devices_in_current_profile(self):
    #     profile_data = self.get_current_profile_data()
    #     return profile_data.get("devices", []) if profile_data else []