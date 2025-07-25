# -*- coding: utf-8 -*-
"""
============================================================================
 File:          dark_theme.py
 Author:        Silas Hörz
 Creation date: 2025-06-25
 Last modified: 2025-07-25
 Version:       1.1.0
============================================================================
 Description:
     Enthält ein dynamisches Farbsystem und das StyleSheet für das
     Dark-Theme des EL-Workbench.
============================================================================
"""

from PyQt6.QtGui import QColor


def hsl(h, s, l):
    """Gibt eine HSL-Farbe als Hex zurück"""
    color = QColor()
    color.setHslF(h / 360, s / 100, l / 100)
    return color.name()


def lighten(hex_color: str, factor=1.2) -> str:
    """Hellt eine hex-Farbe auf"""
    color = QColor(hex_color)
    h, s, v, a = color.getHsv()
    v = min(255, int(v * factor))
    color.setHsv(h, s, v, a)
    return color.name()


# === Farbschema definieren (HSL für bessere Kontrolle) === #
COLOR_SCHEME = {
    # Hintergrundebenen
    "bg_darkest": hsl(71, 8, 15),
    "bg_darker": hsl(71, 8, 18),
    "bg_mid": hsl(71, 8, 21),
    "bg_light": hsl(71, 8, 24),

    # Textfarben
    "text_primary":  hsl(49, 11, 95),
    "text_disabled": hsl(204, 30, 40),
    "text_inverse": hsl(49, 11, 95),

    # Akzentfarben (Buttons etc.)
    "accent": hsl(49, 11, 40),
    "accent_hover": hsl(49, 11, 50),
    "accent_pressed": hsl(49, 11, 50),

    # Info / Fortschritt
    "info": hsl(204, 90, 60),

    # Warnungen
    "error": hsl(0, 80, 60),
    "warning": hsl(40, 90, 60),
}

# === QSS-Vorlage mit Platzhaltern === #
STYLE_TEMPLATE = """
MainWindow {{
    background-color: {bg_darkest};
}}

QWidget {{
    background-color: {bg_darkest};
    color: {text_primary};
    font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
    font-size: 12px;
    font-weight: 600; 
}}

QTableWidget {{
    background-color: {bg_darkest};
    border-radius: 2px;
    border: 1px solid {accent};
}}

QTableWidget::item {{
    padding: 5px;
}}

QTableWidget::item:selected {{
    background-color: {accent};
    border-radius: 2px;
    border: 1px solid {accent_hover};
    color: {text_inverse};
}}

/* Entfernt die Fokusumrandung bei ausgewählten Items */
QTableWidget::item:focus {{
    outline: none;
}}

/* Optional: Verhindert auch, dass der ganze Table den Fokusstil zeigt */
QTableWidget:focus {{
    outline: none;
}}


QHeaderView::section {{
    background-color: {bg_darker};
    color: {text_primary};
    font-weight: bold;
    padding: 5px;
}}

QTableCornerButton::section {{
    background-color: {bg_darker};
}}

QScrollBar:vertical {{
    background: {bg_darker};
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {accent};
    min-height: 20px;
    border-radius: 4px;
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}

QPushButton {{
    background-color: {accent};
    color: {text_inverse};
    padding: 6px 12px;
    border-radius: 2px;
}}

QPushButton:hover {{
    background-color: {accent_hover};
}}

QPushButton:pressed {{
    background-color: {accent_pressed};
}}

QPushButton:disabled {{
    background-color: {bg_mid};
    color: {text_disabled};
}}

QLabel {{
    color: {text_primary};

}}

QLabel#Title {{
    color: {text_primary};
    padding: 0px 0px 20px 0px;  

    font-size: 28px;
}}

/* =======================
   QLineEdit
======================= */
QLineEdit {{
    background-color: {bg_light};
    color: {text_primary};
    border-radius: 2px;
    padding: 6px 8px;
    font-size: 14px;
}}

QLineEdit:focus {{
    border: 1px solid {accent_hover};
}}


QComboBox, QSpinBox {{
    background-color: {bg_light};
    color: {text_primary};
    border-radius: 6px;
    padding: 5px;
    border: 1px solid rgba(255, 255, 255, 0.05);
}}

QGroupBox {{
    padding: 10px;
}}

QProgressBar {{
    background-color: {bg_darkest};
    color: {text_primary};
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 5px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {info};
    color: {text_inverse};
    border-radius: 5px;
}}

QRadioButton {{
    border: none;
}}

QRadioButton::indicator {{
    border-radius: 8px;
    border: 1px solid {text_primary};
}}

QRadioButton::indicator:enabled {{
    background-color: {bg_mid};
}}

QRadioButton::indicator:enabled:checked {{
    background-color: {accent_hover};
}}

QRadioButton::indicator:disabled {{
    background-color: {bg_darkest};
    border: 1px solid {text_disabled};
}}

QRadioButton::indicator:disabled:checked {{
    background-color: {bg_mid};
    border: 1px solid {text_disabled};
}}

QTabBar::tab {{
    font-size: 13px;
    font-weight: 600;
    background: {bg_mid};
    color: {text_primary};
    padding: 8px;
    /*border-top-left-radius: 10px;
    border-top-right-radius: 10px;*/
}}

QTabBar::tab:selected {{
    background: {accent};
    color: {text_inverse};
}}

QTabBar::tab:hover {{
    background: {bg_light};
    color: {text_primary};
}}
"""

# === Generiere finalen Stylesheet-String === #
DARK_STYLESHEET = STYLE_TEMPLATE.format(**COLOR_SCHEME)


DARK_STYLESHEET_alt = """

    MainWindow {
        background-color: hsla(226, 10%, 10% , 1);
    }
    QWidget {
    background-color: hsla(226, 10%, 10%,1);
    
    color: hsl(204, 100%, 94%);
    font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
    font-size: 12px;       /* Schriftgröße erhöhen */
    font-weight: 600;     /* Schrift fetter machen */
    border-radius: 10px;
    border: 1px solid hsla(204, 100%, 70%, 0.1);
    }

    QTabWidget::pane { /* Der Bereich hinter den Tabs */
         background-color: hsla(226, 10%, 50% , 0.1);
    }

    QTabBar::tab {
        font-size: 13px;       /* Schriftgröße erhöhen */
        font-weight: 600;     /* Schrift fetter machen */

    background: hsla(226, 10%, 50% , 0.2);
    color: hsl(204, 100%, 90%);
    padding: 10px;

    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    border-bottom-left-radius: 0px;
    border-bottom-right-radius: 0px;
    }

    QTabBar::tab:selected{
         background: hsl(35, 70%, 60%);
         color: hsl(204, 100%, 10%);
    }
    QTabBar::tab:hover {
         background: hsla(226, 10%, 50% , 0.3);
         color: hsl(204, 100%, 90%);
    }

    QRadioButton{
        border: 0px solid hsl(204, 100%, 94%); 
    }

  QRadioButton::indicator {
                border-radius: 8px;
                border: 1px solid hsl(204, 100%, 94%); /* Standardrahmen */
            }

            QRadioButton::indicator:enabled {
                background-color: hsl(226, 20%, 20%); /* Hintergrundfarbe, wenn deaktiviert und ausgewählt */
                border: 1px solid hsl(204, 100%, 94%);
            }

            QRadioButton::indicator:enabled:checked {
                background-color: hsl(226, 50%, 80%); /* Hintergrundfarbe, wenn aktiviert und ausgewählt */
                border: 1px solid hsl(204, 100%, 94%);
            }

            QRadioButton::indicator:disabled {
                background-color: hsl(226, 20%, 10%); /* Hintergrundfarbe, wenn deaktiviert */
                border: 1px solid hsl(204, 100%, 35%); /* Rahmenfarbe, wenn deaktiviert */
            }

            QRadioButton::indicator:disabled:checked {
                background-color: hsl(226, 20%, 30%); /* Hintergrundfarbe, wenn deaktiviert und ausgewählt */
                border: 1px solid hsl(204, 100%, 35%);
            }


    QPushButton {
        background-color: hsl(226, 20%, 70%);
        color: hsl(204, 100%, 10%);
        padding: 5px;
        border: 1px solid hsla(204, 100%, 0%, 0.1);
    }

    QPushButton:hover {
        background-color: hsl(226, 50%, 80%);
        color: hsl(204, 100%, 6%);
    }

    QPushButton:pressed {
        background: hsl(35, 70%, 60%);
        color: hsl(204, 100%, 10%);
    }

    QPushButton:disabled {
        background-color: hsl(226, 20%, 30%);
    }

    QComboBox, QSpinBox {
        background-color: hsla(226, 10%, 50% , 0.07);
        color: hsl(204, 100%, 94%);
        font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
        border-radius: 10px;
        border: 1px solid hsla(204, 100%, 70%, 0.1);
        padding:5px;
    }

    QLabel {
        color: hsl(204, 100%, 94%);
        background: hsla(226, 10%, 50% , 0);
        border: none;
    }
    
    QMessageBox {
        background-color: hsla(226, 10%, 50% , 0.07);
        color: hsl(204, 100%, 94%);
    }

    QGroupBox {
        padding: 10px;
    }

    QProgressBar {

        background-color: hsla(226, 10%, 10%,0.1);
        color: hsl(204, 100%, 90%);
        padding: 0px;
        border: 1px solid hsla(204, 100%, 0%, 0.1);  
        border-radius: 5px;
        text-align: center;
    }

    QProgressBar::chunk {
        background-color: hsl(226, 40%, 50%);
        color: hsl(204, 100%, 10%);
        border-radius: 5px;
    }
"""