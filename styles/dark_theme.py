# el-workbench/styles/dark_theme.py

# -*- coding: utf-8 -*-
"""
============================================================================
 File:          dark_theme.py
 Author:        Silas Hörz
 Creation date: 2025-06-25
 Last modified: 2025-06-25
 Version:       1.0.0
============================================================================
 Description:
     Enthält den QSS (Qt Style Sheet) String für das Dark-Theme des
     EL-Workbench.
============================================================================
 Change Log:
 - 2025-06-25: Initial version created as part of the EL-Workbench project.
============================================================================
"""

DARK_STYLESHEET = """

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