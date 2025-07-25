# other/device_dialog.py
import os
import json
import math
import uuid
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QMessageBox, QLabel, QDialog, QDialogButtonBox,
    QGroupBox, QRadioButton, QButtonGroup, QCheckBox
)
from PyQt6.QtCore import Qt, QSize, QPointF, QRectF, QLocale
from PyQt6.QtGui import QDoubleValidator, QPainter, QBrush, QPen, QColor, QFont, QPainterPath

# --- Constants for Unit Conversion ---
UM_TO_M = 1e-6
M_TO_UM = 1e6
UM2_TO_M2 = 1e-12
M2_TO_UM2 = 1e12

# --- DeviceDrawingWidget Class (Unchanged, as it was already robust) ---
class DeviceDrawingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(QSize(200, 200)) # Mindestgröße, um Platz zu gewährleisten

        self.shape_type = "rectangle" # "rectangle" or "circle"
        self.width_um = 0.0
        self.length_um = 0.0
        self.radius_um = 0.0
        self.calculated_area_um2 = 0.0 # The area based on width/length/radius
        self.display_area_um2 = 0.0 # The area used for filling (custom or calculated)
        self.custom_area_enabled = False

    def update_drawing_data(self, shape_type, width_um, length_um, radius_um, calculated_area_um2, display_area_um2, custom_area_enabled):
        """Aktualisiert die Daten für die Zeichnung. Alle Dimensionen in Mikrometern."""
        self.shape_type = shape_type
        self.width_um = width_um
        self.length_um = length_um
        self.radius_um = radius_um
        self.calculated_area_um2 = calculated_area_um2 # Area from input dimensions
        self.display_area_um2 = display_area_um2     # Area from custom input OR calculated
        self.custom_area_enabled = custom_area_enabled
        self.update() # Fordert eine Neuzeichnung an

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        widget_rect = self.rect()
        center_x = widget_rect.center().x()
        center_y = widget_rect.center().y()

        base_width_um = self.width_um
        base_length_um = self.length_um
        base_radius_um = self.radius_um

        fill_outer_width_um = base_width_um
        fill_outer_length_um = base_length_um
        fill_outer_radius_um = base_radius_um

        if self.custom_area_enabled and self.calculated_area_um2 > 0 and self.display_area_um2 > self.calculated_area_um2:
            if self.shape_type == "rectangle":
                aspect_ratio = base_length_um / base_width_um if base_width_um > 0 else 1.0
                fill_outer_width_um = math.sqrt(self.display_area_um2 / aspect_ratio) if aspect_ratio > 0 else 0
                fill_outer_length_um = fill_outer_width_um * aspect_ratio
            elif self.shape_type == "circle":
                fill_outer_radius_um = math.sqrt(self.display_area_um2 / math.pi) if math.pi > 0 else 0
        
        max_dim_x_um = 0.0
        max_dim_y_um = 0.0

        if self.shape_type == "rectangle":
            max_dim_x_um = max(base_width_um, fill_outer_width_um)
            max_dim_y_um = max(base_length_um, fill_outer_length_um)
        elif self.shape_type == "circle":
            max_dim_x_um = max(base_radius_um * 2, fill_outer_radius_um * 2) # Durchmesser
            max_dim_y_um = max(base_radius_um * 2, fill_outer_radius_um * 2) # Durchmesser
        
        if max_dim_x_um == 0 and max_dim_y_um == 0:
            max_dim_x_um = 100 # Standard 100 um
            max_dim_y_um = 100 # Standard 100 um

        padding_factor = 1.3 
        effective_max_x_um = max_dim_x_um * padding_factor
        effective_max_y_um = max_dim_y_um * padding_factor

        scale_x = widget_rect.width() / effective_max_x_um if effective_max_x_um > 0 else 1.0
        scale_y = widget_rect.height() / effective_max_y_um if effective_max_y_um > 0 else 1.0
        
        scale_factor = min(scale_x, scale_y)

        painter.save() 

        painter.translate(center_x, center_y)
        painter.scale(scale_factor, -scale_factor)

        axis_pen_thickness = 1.0 / scale_factor
        painter.setPen(QPen(QColor(150, 150, 150), axis_pen_thickness))
        
        font_size_px = max(6, int(10 / scale_factor)) 
        font = painter.font()
        font.setPointSize(font_size_px)
        painter.setFont(font)

        painter.setPen(Qt.PenStyle.NoPen) 

        if self.shape_type == "rectangle":
            outer_rect = QRectF(-base_width_um / 2, -base_length_um / 2, base_width_um, base_length_um)
            
            if self.custom_area_enabled and self.calculated_area_um2 > 0 and self.display_area_um2 < self.calculated_area_um2:
                area_to_cut_out_um2 = self.calculated_area_um2 - self.display_area_um2
                
                if self.calculated_area_um2 > 0 and base_width_um > 0 and base_length_um > 0:
                    aspect_ratio_base = base_length_um / base_width_um
                    if area_to_cut_out_um2 < 0: area_to_cut_out_um2 = 0
                    
                    if self.calculated_area_um2 > 0:
                        scale_factor_cutout = math.sqrt(area_to_cut_out_um2 / self.calculated_area_um2)
                    else:
                        scale_factor_cutout = 0 
                    
                    cutout_width_um = base_width_um * scale_factor_cutout
                    cutout_length_um = base_length_um * scale_factor_cutout
                else: 
                    cutout_width_um = 0
                    cutout_length_um = 0

                inner_rect = QRectF(-cutout_width_um / 2, -cutout_length_um / 2, cutout_width_um, cutout_length_um)

                path = QPainterPath()
                path.addRect(outer_rect) 
                path.addRect(inner_rect) 
                
                painter.setBrush(QBrush(QColor(255, 0, 0, 150))) 
                painter.setClipPath(path) 
                painter.drawRect(outer_rect.united(inner_rect)) 
                painter.setClipping(False) 

            elif self.custom_area_enabled and self.display_area_um2 > self.calculated_area_um2:
                painter.setBrush(QBrush(QColor(255, 0, 0, 150))) 
                
                aspect_ratio = base_length_um / base_width_um if base_width_um > 0 else 1.0
                draw_width = math.sqrt(self.display_area_um2 / aspect_ratio) if aspect_ratio > 0 else 0
                draw_length = draw_width * aspect_ratio
                
                painter.drawRect(
                    QRectF(-draw_width / 2, -draw_length / 2, draw_width, draw_length)
                )
            else: 
                if base_width_um > 0 and base_length_um > 0:
                    painter.setBrush(QBrush(QColor(0, 0, 255, 150))) 
                    painter.drawRect(outer_rect)
        
        elif self.shape_type == "circle":
            outer_radius = base_radius_um
            outer_ellipse_rect = QRectF(-outer_radius, -outer_radius, outer_radius * 2, outer_radius * 2)

            if self.custom_area_enabled and self.display_area_um2 < self.calculated_area_um2:
                area_to_cut_out_um2 = self.calculated_area_um2 - self.display_area_um2
                if area_to_cut_out_um2 < 0: area_to_cut_out_um2 = 0

                cutout_radius = math.sqrt(area_to_cut_out_um2 / math.pi) if math.pi > 0 and area_to_cut_out_um2 > 0 else 0
                inner_ellipse_rect = QRectF(-cutout_radius, -cutout_radius, cutout_radius * 2, cutout_radius * 2)
                
                path = QPainterPath()
                path.addEllipse(outer_ellipse_rect) 
                path.addEllipse(inner_ellipse_rect) 
                
                painter.setBrush(QBrush(QColor(255, 0, 0, 150))) 
                painter.setClipPath(path)
                painter.drawEllipse(outer_ellipse_rect.united(inner_ellipse_rect)) 
                painter.setClipping(False)

            elif self.custom_area_enabled and self.display_area_um2 > self.calculated_area_um2:
                painter.setBrush(QBrush(QColor(255, 0, 0, 150))) 
                draw_radius = math.sqrt(self.display_area_um2 / math.pi) if math.pi > 0 else 0
                painter.drawEllipse(
                    QRectF(-draw_radius, -draw_radius, draw_radius * 2, draw_radius * 2)
                )
            else: 
                if base_radius_um > 0:
                    painter.setBrush(QBrush(QColor(0, 0, 255, 150))) 
                    painter.drawEllipse(outer_ellipse_rect)
        
        painter.setBrush(Qt.BrushStyle.NoBrush) 
        outline_pen_thickness = 2.0 / scale_factor 
        painter.setPen(QPen(QColor(0, 0, 0), outline_pen_thickness))
        
        if self.shape_type == "rectangle":
            if base_width_um > 0 and base_length_um > 0:
                painter.drawRect(
                    QRectF(-base_width_um / 2, -base_length_um / 2,
                           base_width_um, base_length_um)
                )
        elif self.shape_type == "circle":
            if base_radius_um > 0:
                painter.drawEllipse(
                    QRectF(-base_radius_um, -base_radius_um,
                           base_radius_um * 2, base_radius_um * 2)
                )

        painter.restore() 
        painter.end()


# --- DeviceDialog Class: Re-implemented from scratch ---
class DeviceDialog(QDialog):
    def __init__(self, parent=None, device_data=None, existing_device_names=None):
        super().__init__(parent)
        self.setWindowTitle("Gerät bearbeiten/hinzufügen")
        self.setModal(True)
        
        # Internal data model for the dialog. All dimensions in micrometers (um).
        # This is where we store the values that the user is interacting with.
        self._device_data_um = {
            "device_name": device_data.get("device_name", "") if device_data else "",
            "shape_type": device_data.get("shape_type", "rectangle") if device_data else "rectangle",
            "width_um": (device_data.get("width", 0.0) * M_TO_UM) if device_data else 0.0,
            "length_um": (device_data.get("length", 0.0) * M_TO_UM) if device_data else 0.0,
            "radius_um": (device_data.get("radius", 0.0) * M_TO_UM) if device_data else 0.0,
            "custom_area_enabled": device_data.get("custom_area_enabled", False) if device_data else False,
            "area_um2": (device_data.get("Area", 0.0) * M2_TO_UM2) if device_data else 0.0,
            "uuid": device_data.get("uuid", str(uuid.uuid4())) if device_data else str(uuid.uuid4())
        }

        self.existing_device_names = existing_device_names if existing_device_names else []
        self.original_device_name = self._device_data_um["device_name"] # For name validation

        # Flag to prevent recursive signal handling during initial load and programmatic updates
        self._is_updating_ui = False 

        self.init_ui()
        self._update_ui_from_data_model() # Initial population of UI from internal data model
        self._update_drawing_and_area_display() # Initial drawing update

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # --- Left Side: Form ---
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)

        # Group box for shape selection
        shape_group_box = QGroupBox("Form")
        shape_layout = QVBoxLayout(shape_group_box)
        
        self.radio_rect = QRadioButton("Rechteck")
        self.radio_circle = QRadioButton("Kreis")
        
        self.shape_button_group = QButtonGroup(self)
        self.shape_button_group.addButton(self.radio_rect)
        self.shape_button_group.addButton(self.radio_circle)
        self.shape_button_group.buttonClicked.connect(self._on_shape_type_radio_changed)

        shape_layout.addWidget(self.radio_rect)
        shape_layout.addWidget(self.radio_circle)
        form_layout.addWidget(shape_group_box)

        self.fields = {} # To store references to QLineEdit widgets
        self.labels = {} # To store references to QLabel widgets

        # Device Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Gerätename:"))
        self.fields["device_name"] = QLineEdit()
        name_layout.addWidget(self.fields["device_name"])
        form_layout.addLayout(name_layout)

        # Dimensions: Width, Length, Radius
        # We connect textChanged AFTER initial UI population, but manage _is_updating_ui flag.
        self.labels["width"] = QLabel("Breite (um):") 
        self.fields["width"] = QLineEdit()
        self.fields["width"].setValidator(self._get_float_validator())
        self.fields["width"].textChanged.connect(self._on_dimension_input_changed)
        width_layout = QHBoxLayout()
        width_layout.addWidget(self.labels["width"])
        width_layout.addWidget(self.fields["width"])
        form_layout.addLayout(width_layout)

        self.labels["length"] = QLabel("Länge (um):") 
        self.fields["length"] = QLineEdit()
        self.fields["length"].setValidator(self._get_float_validator())
        self.fields["length"].textChanged.connect(self._on_dimension_input_changed)
        length_layout = QHBoxLayout()
        length_layout.addWidget(self.labels["length"])
        length_layout.addWidget(self.fields["length"])
        form_layout.addLayout(length_layout)

        self.labels["radius"] = QLabel("Radius (um):") 
        self.fields["radius"] = QLineEdit()
        self.fields["radius"].setValidator(self._get_float_validator())
        self.fields["radius"].textChanged.connect(self._on_dimension_input_changed)
        radius_layout = QHBoxLayout()
        radius_layout.addWidget(self.labels["radius"])
        radius_layout.addWidget(self.fields["radius"])
        form_layout.addLayout(radius_layout)
        
        # Custom Area Checkbox
        self.checkbox_custom_area = QCheckBox("Fläche manuell angeben")
        self.checkbox_custom_area.stateChanged.connect(self._on_custom_area_checkbox_changed)
        form_layout.addWidget(self.checkbox_custom_area)

        # Area (Display or Custom Input)
        self.labels["area"] = QLabel("Fläche (um²):") # Use "area" as key to avoid conflict with "Area" in data
        self.fields["area"] = QLineEdit()
        self.fields["area"].setValidator(self._get_float_validator())
        self.fields["area"].textChanged.connect(self._on_area_input_changed)
        area_layout = QHBoxLayout()
        area_layout.addWidget(self.labels["area"])
        area_layout.addWidget(self.fields["area"])
        form_layout.addLayout(area_layout)
        
        # Display of robustly calculated area (for info only)
        self.calculated_area_info_label = QLabel("Berechnete Fläche (um²): 0.0") 
        form_layout.addWidget(self.calculated_area_info_label)

        form_layout.addStretch()

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self._accept_dialog) # Changed to _accept_dialog
        button_box.rejected.connect(self.reject)

        self.delete_button = QPushButton("Gerät löschen")
        self.delete_button.clicked.connect(self._confirm_delete) # Changed to _confirm_delete
        if self._device_data_um.get("uuid") and self.original_device_name: # Only show delete for existing devices
            button_box.addButton(self.delete_button, QDialogButtonBox.ButtonRole.DestructiveRole)
        else:
            self.delete_button.hide()
  
        form_layout.addWidget(button_box)
        main_layout.addWidget(form_widget,1)

        # --- Right Side: Drawing Widget ---
        self.drawing_widget = DeviceDrawingWidget(self)
        main_layout.addWidget(self.drawing_widget,2)

    def _get_float_validator(self):
        """Returns a QDoubleValidator for numerical input, ensuring non-negative values."""
        validator = QDoubleValidator()
        validator.setLocale(QLocale(QLocale.Language.German, QLocale.Country.Germany)) # Explicitly set German locale
        validator.setBottom(0.0)
        return validator

    def _get_float_from_line_edit(self, line_edit):
        """Helper to safely get float value from QLineEdit, handling locale."""
        text = line_edit.text().strip()
        try:
            # Replace locale-specific decimal point (comma) with standard dot for float() conversion
            return float(text.replace(self.locale().decimalPoint(), '.')) if text else 0.0
        except ValueError:
            return 0.0 # Return 0.0 if conversion fails

    def _format_float_for_display(self, value, precision=4):
        """Formats a float for display in QLineEdit, handling trailing zeros and locale."""
        if value is None:
            value = 0.0
        # Format to desired precision, then strip trailing zeros and decimal point
        s = f"{value:.{precision}f}".rstrip('0')
        if s.endswith('.'):
            s = s.rstrip('.')
        # Replace standard dot with locale-specific decimal point
        return s.replace('.', self.locale().decimalPoint())

    def _calculate_area_um2(self):
        """Calculates the area based on current dimensions in the internal data model (um^2)."""
        if self._device_data_um["shape_type"] == "rectangle":
            return self._device_data_um["width_um"] * self._device_data_um["length_um"]
        elif self._device_data_um["shape_type"] == "circle":
            return math.pi * self._device_data_um["radius_um"]**2
        return 0.0

    # --- UI Update and Event Handlers ---

    def _update_ui_from_data_model(self):
        """
        Updates all UI elements (QLineEdits, RadioButtons, CheckBox) based on the
        current state of the internal self._device_data_um data model.
        This method is called during initialization and when the internal data is programmatically changed.
        Signals are temporarily blocked to prevent recursive calls.
        """
        self._is_updating_ui = True # Block signals

        # Device Name
        self.fields["device_name"].setText(self._device_data_um["device_name"])

        # Shape Type Radio Buttons
        if self._device_data_um["shape_type"] == "rectangle":
            self.radio_rect.setChecked(True)
        else:
            self.radio_circle.setChecked(True)
        # Manually call visibility update here, as radio button signal is potentially blocked
        self._update_dimension_field_visibility()

        # Dimension Fields
        self.fields["width"].setText(self._format_float_for_display(self._device_data_um["width_um"]))
        self.fields["length"].setText(self._format_float_for_display(self._device_data_um["length_um"]))
        self.fields["radius"].setText(self._format_float_for_display(self._device_data_um["radius_um"]))

        # Custom Area Checkbox
        self.checkbox_custom_area.setChecked(self._device_data_um["custom_area_enabled"])
        # Manually call visibility update for Area field
        self._update_area_field_visibility()

        # Area Field
        self.fields["area"].setText(self._format_float_for_display(self._device_data_um["area_um2"], precision=8))
        
        self._is_updating_ui = False # Unblock signals

    def _update_dimension_field_visibility(self):
        """Adjusts visibility of dimension fields based on selected shape type."""
        is_rectangle = (self._device_data_um["shape_type"] == "rectangle")
        self.labels["width"].setVisible(is_rectangle)
        self.fields["width"].setVisible(is_rectangle)
        self.labels["length"].setVisible(is_rectangle)
        self.fields["length"].setVisible(is_rectangle)
        
        self.labels["radius"].setVisible(not is_rectangle) # Visible if NOT rectangle (i.e., circle)
        self.fields["radius"].setVisible(not is_rectangle)

    def _update_area_field_visibility(self):
        """Adjusts visibility and enabled state of the custom area field."""
        is_custom_area = self._device_data_um["custom_area_enabled"]
        self.labels["area"].setVisible(is_custom_area)
        self.fields["area"].setVisible(is_custom_area)
        self.fields["area"].setEnabled(is_custom_area) # Only enable if custom area is checked

    def _update_drawing_and_area_display(self):
        """Calculates area and updates the drawing widget and info label."""
        calculated_area_for_info = self._calculate_area_um2()
        self.calculated_area_info_label.setText(
            f"Berechnete Fläche (um²): {self._format_float_for_display(calculated_area_for_info, precision=4)}"
        )

        # Determine which area value to use for drawing (custom if enabled, otherwise calculated)
        display_area_for_drawing_um2 = self._device_data_um["area_um2"] \
            if self._device_data_um["custom_area_enabled"] else calculated_area_for_info

        self.drawing_widget.update_drawing_data(
            self._device_data_um["shape_type"],
            self._device_data_um["width_um"],
            self._device_data_um["length_um"],
            self._device_data_um["radius_um"],
            calculated_area_for_info, # Pass calculated area for clipping logic
            display_area_for_drawing_um2,
            self._device_data_um["custom_area_enabled"]
        )

    # --- Signal Handlers (User Interaction) ---

    def _on_shape_type_radio_changed(self):
        """Handler for shape type radio button changes."""
        if self._is_updating_ui: return # Prevent re-entry if UI is being programmatically updated

        new_shape_type = "rectangle" if self.radio_rect.isChecked() else "circle"
        
        # Only update internal model and UI if shape type actually changed
        if new_shape_type != self._device_data_um["shape_type"]:
            self._device_data_um["shape_type"] = new_shape_type
            
            # When shape type changes via user interaction, reset the other dimension to 0.0
            # and update the corresponding QLineEdit.
            if new_shape_type == "rectangle":
                self._device_data_um["radius_um"] = 0.0
                self.fields["radius"].setText(self._format_float_for_display(0.0))
            else: # circle
                self._device_data_um["width_um"] = 0.0
                self._device_data_um["length_um"] = 0.0
                self.fields["width"].setText(self._format_float_for_display(0.0))
                self.fields["length"].setText(self._format_float_for_display(0.0))

            self._update_dimension_field_visibility() # Update visibility based on new shape type
            self._update_drawing_and_area_display() # Recalculate and update drawing

    def _on_dimension_input_changed(self):
        """Handler for dimension QLineEdit text changes."""
        if self._is_updating_ui: return # Prevent re-entry if UI is being programmatically updated

        # Read values from QLineEdits and update the internal data model
        if self._device_data_um["shape_type"] == "rectangle":
            self._device_data_um["width_um"] = self._get_float_from_line_edit(self.fields["width"])
            self._device_data_um["length_um"] = self._get_float_from_line_edit(self.fields["length"])
        else: # circle
            self._device_data_um["radius_um"] = self._get_float_from_line_edit(self.fields["radius"])
        
        # If custom area is not enabled, update the internal area model based on dimensions
        if not self._device_data_um["custom_area_enabled"]:
            self._device_data_um["area_um2"] = self._calculate_area_um2()
            # Update the area QLineEdit as well
            self._is_updating_ui = True # Block to prevent _on_area_input_changed from firing
            self.fields["area"].setText(self._format_float_for_display(self._device_data_um["area_um2"], precision=8))
            self._is_updating_ui = False # Unblock

        self._update_drawing_and_area_display()

    def _on_custom_area_checkbox_changed(self, state):
        """Handler for custom area checkbox state changes."""
        if self._is_updating_ui: return # Prevent re-entry

        self._device_data_um["custom_area_enabled"] = (state == Qt.CheckState.Checked.value)
        self._update_area_field_visibility() # Adjust visibility/enabled state

        # If custom area is just disabled, update internal area model from calculated value
        if not self._device_data_um["custom_area_enabled"]:
            self._device_data_um["area_um2"] = self._calculate_area_um2()
            # Update the area QLineEdit
            self._is_updating_ui = True # Block to prevent _on_area_input_changed from firing
            self.fields["area"].setText(self._format_float_for_display(self._device_data_um["area_um2"], precision=8))
            self._is_updating_ui = False # Unblock
        
        self._update_drawing_and_area_display()

    def _on_area_input_changed(self):
        """Handler for manual Area QLineEdit text changes."""
        if self._is_updating_ui: return # Prevent re-entry

        # Only update internal area model if custom area is enabled
        if self._device_data_um["custom_area_enabled"]:
            self._device_data_um["area_um2"] = self._get_float_from_line_edit(self.fields["area"])
            self._update_drawing_and_area_display()

    # --- Dialog Acceptance/Deletion ---

    def _accept_dialog(self):
        """Validates input and accepts the dialog. Converts data to meters for external use."""
        device_name = self.fields["device_name"].text().strip()
        if not device_name:
            QMessageBox.warning(self, "Eingabefehler", "Gerätename darf nicht leer sein.")
            return

        # Name validation (case-insensitive)
        # Check if the new name clashes with existing names (excluding the original name if editing)
        if device_name.lower() != self.original_device_name.lower() and \
           device_name.lower() in [n.lower() for n in self.existing_device_names]:
            QMessageBox.warning(self, "Eingabefehler", f"Ein Gerät mit dem Namen '{device_name}' existiert bereits. Bitte wählen Sie einen anderen Namen.")
            return

        # If we reach here, validation passed. Prepare self.device_data for return.
        # This is the data that will be returned to the calling ProfileTab.
        self.device_data = {
            "device_name": device_name,
            "shape_type": self._device_data_um["shape_type"],
            "custom_area_enabled": self._device_data_um["custom_area_enabled"],
            "uuid": self._device_data_um["uuid"]
        }

        # Convert dimensions back to meters for storage
        if self._device_data_um["shape_type"] == "rectangle":
            self.device_data["width"] = self._device_data_um["width_um"] * UM_TO_M
            self.device_data["length"] = self._device_data_um["length_um"] * UM_TO_M
            self.device_data["radius"] = 0.0 # Ensure radius is 0 for rectangles
        else: # circle
            self.device_data["radius"] = self._device_data_um["radius_um"] * UM_TO_M
            self.device_data["width"] = 0.0 # Ensure width/length are 0 for circles
            self.device_data["length"] = 0.0
        
        # Store the Area value (in meters squared)
        self.device_data["Area"] = self._device_data_um["area_um2"] * UM2_TO_M2

        self.accept()

    def _confirm_delete(self):
        """Confirms deletion of the device."""
        reply = QMessageBox.question(self, "Gerät löschen",
                                     f"Möchten Sie das Gerät '{self._device_data_um.get('device_name', '')}' wirklich löschen?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_confirmed = True # Custom flag for ProfileTab to check
            self.reject() # Close the dialog