# el-workbench/tabs/analysis_tab.py
# -*- coding: utf-8 -*-
"""
============================================================================
 File:          analysis_tab.py
 Author:        Silas Hörz
 Creation date: 2025-08-05
 Last modified: 2025-08-05
 Version:       0.1.0
============================================================================
 Description:
    Mit Hilfes dieses Tabs soll großer Teil der benötigten Datenverarbeitung stattfinden.
    Es soll als Zentrale Konfigurationsstelle für die gewünschte Messung dienen.
    Hier lässt sich der Ablauf der Messung konfigurieren. Dabei kann zu jedem
    Zeitpunkt der Messung das aktuelle Spektrometer angezeigt werden.
============================================================================
 Change Log:
 - 2025-08-05: V0.1.0 Erste Version erstellt. Anweisungen für EL-Workbench aktualisiert.
============================================================================
"""


import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QMessageBox, QLineEdit, QTextEdit, QGridLayout, QSizePolicy,
    QSpacerItem
)
from PyQt6.QtCore import QTimer, QSize, QPoint, QPointF, Qt, QCoreApplication
from PyQt6.QtGui import QIcon, QPainter, QPen, QPainterPath, QColor
import numpy as np
import math

# Für Icons
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AnalysisTab(QWidget):
    def __init__(self, shared_data):
        """
        Initialisiert den Beispiel-Tab.
        
        Args:
            shared_data: SharedData Instanz die Zugriff auf Anwendungsdaten bietet
        """
        super().__init__()
        self.shared_data = shared_data
        
        self.init_ui()
        
        # Sende initiale Statusmeldung
        self.shared_data.info_manager.status(
            self.shared_data.info_manager.INFO,
            "Analyse-Tab erfolgreich initialisiert"
        )

    def init_ui(self):
        """Erstellt die Benutzeroberfläche."""
        main_layout = QHBoxLayout(self)

        # ---------------------------------------------------
        # Flowchart 
        # ---------------------------------------------------
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        ### -----------------------------------------------
        ### Block 1 - SMU 
        ### -----------------------------------------------

        self.block1_widget = QWidget()
        self.block1_widget.setObjectName("FCBLOCK1")
        block1_layout = QVBoxLayout(self.block1_widget)
     
        # Name | Einstellungen
        headline_layout = QHBoxLayout()
        name = QLabel("Source Measure Unit")
        name.setObjectName("miniTitle")
        settings_btn = QPushButton()
        settings_btn.setIcon(QIcon(os.path.join(BASE_DIR, "icons", "options.svg")))
        settings_btn.setIconSize(QSize(20, 20)) 
        settings_btn.setFixedSize(22,22)

        headline_layout.addWidget(name)
        headline_layout.addStretch()
        headline_layout.addWidget(settings_btn)
        block1_layout.addLayout(headline_layout)

        # Info Block
        info_label1 = QLabel("Mehrzeilige Info\nZeile 2\nZeile 3")
        block1_layout.addWidget(info_label1)

        ##### -------------------------------------------
        ##### Block 2 - Spektrometer 
        ##### -------------------------------------------

        content2_layout = QHBoxLayout()
        # Setze die Margins hier auf 0, um den Abstand zu entfernen
        content2_layout.setContentsMargins(0, 20, 0, 20)
        content2_layout.addItem(QSpacerItem(40, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        self.block2_widget = QWidget()
        self.block2_widget.setObjectName("FCBLOCK2")
        block2_layout = QVBoxLayout(self.block2_widget)

        # Name | Einstellungen
        headline_layout = QHBoxLayout()
        name = QLabel("Spektrometer")
        #name.setStyleSheet("padding-top: 10px;")
        name.setObjectName("miniTitle")
        settings_btn = QPushButton()
        settings_btn.setIcon(QIcon(os.path.join(BASE_DIR, "icons", "options.svg")))
        settings_btn.setIconSize(QSize(20, 20)) 
        settings_btn.setFixedSize(22,22)

        headline_layout.addWidget(name)
        headline_layout.addStretch()
        headline_layout.addWidget(settings_btn)
        block2_layout.addLayout(headline_layout)

        # Info Block
        info_label1 = QLabel("Mehrzeilige Info\nZeidfsdfsle 2\nZeile 3")
        block2_layout.addWidget(info_label1)


       

        # --- Block 3 ---
        content3_layout = QHBoxLayout()
        # Setze die Margins hier ebenfalls auf 0
        content3_layout.setContentsMargins(0, 20, 0, 20)
        content3_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        

        self.block3_widget = QWidget()
        self.block3_widget.setObjectName("FCBLOCK3")
        block3_layout = QVBoxLayout(self.block3_widget)
        #block3_layout.setContentsMargins(10,10,0,10)
        label3 = QLabel("Spektrum erfassen")
        block3_layout.addWidget(label3)
        
        content3_layout.addWidget(self.block3_widget,alignment=Qt.AlignmentFlag.AlignRight)
        block2_layout.addLayout(content3_layout)

        content2_layout.addWidget(self.block2_widget,alignment=Qt.AlignmentFlag.AlignRight)
        block1_layout.addLayout(content2_layout)

        # Hinzufügen von Spacern für den oberen und unteren Abstand
        left_layout.addItem(QSpacerItem(0, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        left_layout.addWidget(self.block1_widget)
        left_layout.addItem(QSpacerItem(0, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        left_layout.addStretch()

        # -------------------- Main Layout --------------------
        main_layout.addLayout(left_layout)
        main_layout.addStretch(3)
        
        # Pfeil-Widgets als Children von AnalysisTab erstellen
        self.block3_arrow = ArrowWidget(parent=self, arrow_type="loop", radius=16)
        self.block2_arrow = ArrowWidget(parent=self, arrow_type="loop", radius=20)

        # Setze die Aktivierung *vor* dem Setzen der Geometrie
        self.block3_arrow.setActive(True)
        self.block2_arrow.setActive(False)

        self.block3_arrow.setGeometry(self.rect())
        self.block2_arrow.setGeometry(self.rect())

        self.block3_arrow.raise_()
        self.block2_arrow.raise_()

        # Initialer Aufruf der Pfeil-Positionierung nach der vollständigen Initialisierung
        QTimer.singleShot(0, self.update_arrow_positions)
    
    def update_arrow_positions(self):
        """Aktualisiert die Positionen aller Pfeil-Widgets."""
        if hasattr(self, 'block2_arrow') and self.block2_arrow and self.block2_widget:
            local_pos_b2 = self.block2_widget.mapTo(self, QPoint(0,0))
            self.block2_arrow.setArrowGeometry(local_pos_b2, self.block2_widget.size())
        
        if hasattr(self, 'block3_arrow') and self.block3_arrow and self.block3_widget:
            local_pos_b3 = self.block3_widget.mapTo(self, QPoint(0,0))
            self.block3_arrow.setArrowGeometry(local_pos_b3, self.block3_widget.size())

    def resizeEvent(self, event):
        """Wird aufgerufen, wenn sich die Größe des Fensters ändert."""
        super().resizeEvent(event)
        self.block2_arrow.setGeometry(self.rect())
        self.block3_arrow.setGeometry(self.rect())
        self.update_arrow_positions()


class ArrowWidget(QWidget):
    def __init__(self, parent=None, arrow_type="loop", radius=20):
        super().__init__(parent)
        self.arrow_type = arrow_type
        self.radius = radius
        self.block_pos = QPoint(0, 0)
        self.block_size = QSize(100, 100)
        self.active = False # Default-Zustand ist jetzt False
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setObjectName("ArrowWidget") 
        self.setProperty("active", False) 

    def setActive(self, active: bool):
        if self.active != active:
            self.active = active
            self.setProperty("active", self.active)
            self.style().polish(self)
            self.update()

    def setArrowGeometry(self, block_pos: QPoint, block_size: QSize):
        self.block_pos = block_pos
        self.block_size = block_size
        self.update()

    def setArrowType(self, arrow_type: str):
        self.arrow_type = arrow_type
        self.update()

    def setRadius(self, radius: int):
        self.radius = radius
        self.update()

    def paintEvent(self, event):
        if not self.block_size.isValid():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = self._getEffectiveColor()
        pen = QPen(color, 2)

        if not self.active:
            pen.setStyle(Qt.PenStyle.DotLine)

        painter.setPen(pen)

        path = QPainterPath()

        if self.arrow_type == "loop":
            self._draw_loop_arrow(path)

        painter.drawPath(path) 
        

        pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.setBrush(color) # Setze die Brush-Farbe direkt

        self._drawArrowHead(painter, path)

    def _draw_loop_arrow(self, path: QPainterPath):
        r = self.radius
        offset = 20
        bx = self.block_pos.x()
        by = self.block_pos.y()
        bw = self.block_size.width()
        bh = self.block_size.height()

        start = QPointF(bx + offset, by + bh)
        mid = QPointF(bx + offset, by)
        path.moveTo(start)

        path.arcTo(start.x() - r * 2, start.y() - r, 2 * r, 2 * r, 0, -180)
        path.arcTo(mid.x() - r * 2, mid.y() - r, 2 * r, 2 * r, 180, -180)
        path.lineTo(mid)

    def _drawArrowHead(self, painter, path: QPainterPath):
        if path.isEmpty():
            return
        toPt = path.currentPosition()
        fromPt = QPointF(toPt.x(), toPt.y() - 1)

        angle = math.atan2(toPt.y() - fromPt.y(), toPt.x() - fromPt.x())
        size = 7
        p1 = QPointF(
            toPt.x() - size * math.cos(angle - math.pi / 6),
            toPt.y() - size * math.sin(angle - math.pi / 6)
        )
        p2 = QPointF(
            toPt.x() - size * math.cos(angle + math.pi / 6),
            toPt.y() - size * math.sin(angle + math.pi / 6)
        )

        head = QPainterPath()
        head.moveTo(toPt)
        head.lineTo(p1)
        head.lineTo(p2)
        head.closeSubpath()

        painter.drawPath(head)

    def _getEffectiveColor(self) -> QColor:
        # Fragt die Farbe direkt über das Stylesheet-System ab
        return self.palette().color(self.foregroundRole())