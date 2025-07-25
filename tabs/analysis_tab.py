# el-workbench/tabs/analysis_tab.py
# -*- coding: utf-8 -*-
"""
============================================================================
 File:          analysis_tab.py
 Author:        Silas Hörz
 Creation date: 2025-08-05
 Last modified: 2025-08-09
 Version:       0.1.1
============================================================================
 Description:
    Dieser Tab dient als zentrale Konfigurationsstelle für die Messung.
    Hier können SMU-, Spektrometer-, Kalibrierungs-, Analyse- und
    Export-Einstellungen vorgenommen werden.
============================================================================
 Change Log:
 - 2025-08-05: V0.1.0 Erste Version erstellt
 - 2025-08-09: V0.1.1 Variablennamen nach Blockkonvention vereinheitlicht
               und Code-Struktur optisch aufgeräumt (keine Logikänderung)
============================================================================
"""

import os
import math
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QSpacerItem, QSizePolicy, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import QTimer, QSize, QPoint, QPointF, Qt
from PyQt6.QtGui import QIcon, QPainter, QPen, QPainterPath, QColor

# Basisverzeichnis für Icons
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AnalysisTab(QWidget):
    def __init__(self, shared_data):
        """
        Initialisiert den Analyse-Tab.
        """
        super().__init__()
        self.shared_data = shared_data
        self._init_ui()

        # Initiale Statusmeldung
        self.shared_data.info_manager.status(
            self.shared_data.info_manager.INFO,
            "Analyse-Tab erfolgreich initialisiert"
        )

    # =========================================================
    # UI INITIALISIERUNG
    # =========================================================
    def _init_ui(self):
        main_layout = QHBoxLayout(self)

        # Gemeinsame exklusive Button-Gruppe
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        # Linker Bereich (Flowchart)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # ---------------------------------------------------
        # BLOCK 1: SMU KONFIGURATION
        # ---------------------------------------------------
        self.block1_widget = QWidget()
        self.block1_widget.setObjectName("FCBLOCK1")
        block1_layout = QVBoxLayout(self.block1_widget)

        # Block 1 Titelzeile (Header)
        block1_header_layout = QHBoxLayout()
        block1_title_label = QLabel("Source Measure Unit")
        block1_title_label.setObjectName("miniTitle")
        block1_settings_button = QPushButton()
        block1_settings_button.setIcon(QIcon(os.path.join(BASE_DIR, "icons", "b_options.svg")))
        block1_settings_button.setIconSize(QSize(20, 20))
        block1_settings_button.setFixedSize(22, 22)
        block1_header_layout.addWidget(block1_title_label)
        block1_header_layout.addStretch()
        block1_header_layout.addWidget(block1_settings_button)
        block1_layout.addLayout(block1_header_layout)

        # Block 1 Info (oben)
        block1_info_label = QLabel("Mehrzeilige Info\nZeile 2\nZeile 3")
        block1_layout.addWidget(block1_info_label)

        # *** Footer mit Button für Block 1 ***
        footer1 = QWidget()
        footer1_layout = QHBoxLayout(footer1)
        footer1_layout.setContentsMargins(0, 0, 0, 0)
        footer1_layout.setSpacing(0)

        footer1_info_label = QLabel("SMU Auswahl aktivieren")
        footer1_layout.addWidget(footer1_info_label, alignment=Qt.AlignmentFlag.AlignLeft)

        btn1 = QPushButton()
        btn1.setObjectName("selectButton")
        btn1.setCheckable(True)
        btn1.setIcon(QIcon(os.path.join(BASE_DIR, "icons", "magnifier.svg")))
        btn1.setIconSize(QSize(20, 20))
        btn1.setFixedSize(22, 22)
        footer1_layout.addWidget(btn1, alignment=Qt.AlignmentFlag.AlignRight)
        self.button_group.addButton(btn1)

        block1_layout.addWidget(footer1)

        # ---------------------------------------------------
        # BLOCK 1.1: SPEKTROMETER KONFIGURATION
        # ---------------------------------------------------
        content_block1_spectro_layout = QHBoxLayout()
        content_block1_spectro_layout.setContentsMargins(0, 20, 0, 20)
        content_block1_spectro_layout.addItem(QSpacerItem(16, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        self.block2_widget = QWidget()
        block2_layout = QVBoxLayout(self.block2_widget)
        block2_layout.setContentsMargins(0, 0, 0, 0)
        
        # Inneres Layout für Block 1.1 und 1.2
        inner_block2_layout = QVBoxLayout()
        inner_block2_layout.setContentsMargins(0, 0, 0, 0)
        inner_block2_layout.setSpacing(0)

        # Block 1.1 (Spektrometer)
        self.block2a_widget = QWidget()
        self.block2a_widget.setObjectName("FCBLOCK2")
        block2a_layout = QVBoxLayout(self.block2a_widget)

        block2a_header_layout = QHBoxLayout()
        block2a_title_label = QLabel("Spektrometer")
        block2a_title_label.setObjectName("miniTitle")
        block2a_settings_button = QPushButton()
        block2a_settings_button.setIcon(QIcon(os.path.join(BASE_DIR, "icons", "b_options.svg")))
        block2a_settings_button.setIconSize(QSize(20, 20))
        block2a_settings_button.setFixedSize(22, 22)
        block2a_header_layout.addWidget(block2a_title_label)
        block2a_header_layout.addStretch()
        block2a_header_layout.addWidget(block2a_settings_button)
        block2a_layout.addLayout(block2a_header_layout)

        block2a_info_label = QLabel("Mehrzeilige Info\nZeile 2\nZeile 3")
        block2a_layout.addWidget(block2a_info_label)

        # ---------------------------------------------------
        # BLOCK 1.1.1: SPEKTRUM ERFASSEN
        # ---------------------------------------------------
        content_block3_layout = QHBoxLayout()
        content_block3_layout.setContentsMargins(0, 20, 0, 20)
        content_block3_layout.addItem(QSpacerItem(16, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        self.block3_widget = QWidget()
        self.block3_widget.setObjectName("FCBLOCK2")
        block3_layout = QVBoxLayout(self.block3_widget)
        block3_title_label = QLabel("Spektrum erfassen")
        block3_layout.addWidget(block3_title_label)

        # Footer für Block 1.1.1 mit Button
        footer3 = QWidget()
        footer3_layout = QHBoxLayout(footer3)
        footer3_layout.setContentsMargins(0, 0, 0, 0)
        footer3_layout.setSpacing(0)

        footer3_info_label = QLabel("Spektrum erfassen aktivieren")
        footer3_layout.addWidget(footer3_info_label, alignment=Qt.AlignmentFlag.AlignLeft)

        btn3 = QPushButton()
        btn3.setObjectName("selectButton")
        btn3.setCheckable(True)
        btn3.setIcon(QIcon(os.path.join(BASE_DIR, "icons", "magnifier.svg")))
        btn3.setIconSize(QSize(20, 20))
        btn3.setFixedSize(22, 22)
        footer3_layout.addWidget(btn3, alignment=Qt.AlignmentFlag.AlignRight)
        self.button_group.addButton(btn3)

        block3_layout.addWidget(footer3)

        content_block3_layout.addWidget(self.block3_widget, alignment=Qt.AlignmentFlag.AlignRight)

        block2a_layout.addLayout(content_block3_layout)

        # Footer für Block 1.1 mit Button
        footer2a = QWidget()
        footer2a_layout = QHBoxLayout(footer2a)
        footer2a_layout.setContentsMargins(0, 0, 0, 0)
        footer2a_layout.setSpacing(0)

        footer2a_info_label = QLabel("Spektrometer Auswahl aktivieren")
        footer2a_layout.addWidget(footer2a_info_label, alignment=Qt.AlignmentFlag.AlignLeft)

        btn2a = QPushButton()
        btn2a.setObjectName("selectButton")
        btn2a.setCheckable(True)
        btn2a.setIcon(QIcon(os.path.join(BASE_DIR, "icons", "magnifier.svg")))
        btn2a.setIconSize(QSize(20, 20))
        btn2a.setFixedSize(22, 22)
        footer2a_layout.addWidget(btn2a, alignment=Qt.AlignmentFlag.AlignRight)
        self.button_group.addButton(btn2a)

        block2a_layout.addWidget(footer2a)

        self.arrow_1_2 = ArrowWidget(parent=self)
        self.arrow_1_2.setFixedHeight(40)
        self.arrow_1_2.setArrowType("vertical")
        self.arrow_1_2.setActive(True)

        # ---------------------------------------------------
        # BLOCK 1.2: KALIBRIERUNG KONFIGURATION
        # ---------------------------------------------------
        self.block2b_widget = QWidget()
        self.block2b_widget.setObjectName("FCBLOCK2")
        block2b_layout = QVBoxLayout(self.block2b_widget)

        block2b_header_layout = QHBoxLayout()
        block2b_title_label = QLabel("Kalibrierung")
        block2b_title_label.setObjectName("miniTitle")
        block2b_settings_button = QPushButton()
        block2b_settings_button.setIcon(QIcon(os.path.join(BASE_DIR, "icons", "b_options.svg")))
        block2b_settings_button.setIconSize(QSize(20, 20))
        block2b_settings_button.setFixedSize(22, 22)
        block2b_header_layout.addWidget(block2b_title_label)
        block2b_header_layout.addStretch()
        block2b_header_layout.addWidget(block2b_settings_button)
        block2b_layout.addLayout(block2b_header_layout)

        block2b_info_label = QLabel("Mehrzeilige Info\nZeile 2\nZeile 3")
        block2b_layout.addWidget(block2b_info_label)

        # Footer für Block 1.2 mit Button
        footer2b = QWidget()
        footer2b_layout = QHBoxLayout(footer2b)
        footer2b_layout.setContentsMargins(0, 0, 0, 0)
        footer2b_layout.setSpacing(0)

        footer2b_info_label = QLabel("Kalibrierung aktivieren")
        footer2b_layout.addWidget(footer2b_info_label, alignment=Qt.AlignmentFlag.AlignLeft)

        btn2b = QPushButton()
        btn2b.setObjectName("selectButton")
        btn2b.setCheckable(True)
        btn2b.setIcon(QIcon(os.path.join(BASE_DIR, "icons", "magnifier.svg")))
        btn2b.setIconSize(QSize(20, 20))
        btn2b.setFixedSize(22, 22)
        footer2b_layout.addWidget(btn2b, alignment=Qt.AlignmentFlag.AlignRight)
        self.button_group.addButton(btn2b)

        block2b_layout.addWidget(footer2b)

        # Zusammenfügen von Block 1.1 und 1.2
        inner_block2_layout.addWidget(self.block2a_widget)
        inner_block2_layout.addWidget(self.arrow_1_2)
        inner_block2_layout.addWidget(self.block2b_widget)
        block2_layout.addLayout(inner_block2_layout)

        content_block1_spectro_layout.addWidget(self.block2_widget, alignment=Qt.AlignmentFlag.AlignRight)
        block1_layout.addLayout(content_block1_spectro_layout)

        # Pfeil von Block 1 → Block 2
        self.arrow_1_4 = ArrowWidget(parent=self)
        self.arrow_1_4.setFixedHeight(40)
        self.arrow_1_4.setArrowType("vertical")
        self.arrow_1_4.setActive(True)

        # ---------------------------------------------------
        # BLOCK 2: ANALYSE KONFIGURATION
        # ---------------------------------------------------
        self.block4_widget = QWidget()
        self.block4_widget.setObjectName("FCBLOCK1")
        block4_layout = QVBoxLayout(self.block4_widget)
        block4_layout.setContentsMargins(10, 10, 10, 10)

        block4_header_layout = QHBoxLayout()
        block4_title_label = QLabel("Analyse")
        block4_title_label.setObjectName("miniTitle")
        block4_settings_button = QPushButton()
        block4_settings_button.setIcon(QIcon(os.path.join(BASE_DIR, "icons", "b_options.svg")))
        block4_settings_button.setIconSize(QSize(20, 20))
        block4_settings_button.setFixedSize(22, 22)
        block4_header_layout.addWidget(block4_title_label)
        block4_header_layout.addStretch()
        block4_header_layout.addWidget(block4_settings_button)
        block4_layout.addLayout(block4_header_layout)

        block4_info_label = QLabel("Mehrzeilige Info\nZeile 2\nZeile 3")
        block4_layout.addWidget(block4_info_label)

        # Footer für Block 2 mit Button
        footer4 = QWidget()
        footer4_layout = QHBoxLayout(footer4)
        footer4_layout.setContentsMargins(0, 0, 0, 0)
        footer4_layout.setSpacing(0)

        footer4_info_label = QLabel("Analyse aktivieren")
        footer4_layout.addWidget(footer4_info_label, alignment=Qt.AlignmentFlag.AlignLeft)

        btn4 = QPushButton()
        btn4.setObjectName("selectButton")
        btn4.setCheckable(True)
        btn4.setIcon(QIcon(os.path.join(BASE_DIR, "icons", "magnifier.svg")))
        btn4.setIconSize(QSize(20, 20))
        btn4.setFixedSize(22, 22)
        footer4_layout.addWidget(btn4, alignment=Qt.AlignmentFlag.AlignRight)
        self.button_group.addButton(btn4)

        block4_layout.addWidget(footer4)

        self.arrow_4_5 = ArrowWidget(parent=self)
        self.arrow_4_5.setFixedHeight(40)
        self.arrow_4_5.setArrowType("vertical")
        self.arrow_4_5.setActive(True)

        # ---------------------------------------------------
        # BLOCK 3: EXPORT KONFIGURATION
        # ---------------------------------------------------
        self.block5_widget = QWidget()
        self.block5_widget.setObjectName("FCBLOCK1")
        block5_layout = QVBoxLayout(self.block5_widget)
        block5_layout.setContentsMargins(10, 10, 10, 10)

        block5_header_layout = QHBoxLayout()
        block5_title_label = QLabel("Export")
        block5_title_label.setObjectName("miniTitle")
        block5_settings_button = QPushButton()
        block5_settings_button.setIcon(QIcon(os.path.join(BASE_DIR, "icons", "b_options.svg")))
        block5_settings_button.setIconSize(QSize(20, 20))
        block5_settings_button.setFixedSize(22, 22)
        block5_header_layout.addWidget(block5_title_label)
        block5_header_layout.addStretch()
        block5_header_layout.addWidget(block5_settings_button)
        block5_layout.addLayout(block5_header_layout)

        block5_info_label = QLabel("Mehrzeilige Info\nZeile 2\nZeile 3")
        block5_layout.addWidget(block5_info_label)

        # Footer für Block 3 mit Button
        footer5 = QWidget()
        footer5_layout = QHBoxLayout(footer5)
        footer5_layout.setContentsMargins(0, 0, 0, 0)
        footer5_layout.setSpacing(0)

        footer5_info_label = QLabel("Export aktivieren")
        footer5_layout.addWidget(footer5_info_label, alignment=Qt.AlignmentFlag.AlignLeft)

        btn5 = QPushButton()
        btn5.setObjectName("selectButton")
        btn5.setCheckable(True)
        btn5.setIcon(QIcon(os.path.join(BASE_DIR, "icons", "magnifier.svg")))
        btn5.setIconSize(QSize(20, 20))
        btn5.setFixedSize(22, 22)
        footer5_layout.addWidget(btn5, alignment=Qt.AlignmentFlag.AlignRight)
        self.button_group.addButton(btn5)

        block5_layout.addWidget(footer5)

        # ---------------------------------------------------
        # LINKES LAYOUT ZUSAMMENFÜGEN
        # ---------------------------------------------------
        left_layout.addWidget(self.block1_widget)
        left_layout.addWidget(self.arrow_1_4)
        left_layout.addWidget(self.block4_widget)
        left_layout.addWidget(self.arrow_4_5)
        left_layout.addWidget(self.block5_widget)
        left_layout.addStretch()

        # Hauptlayout
        main_layout.addLayout(left_layout)
        main_layout.addStretch(3)

        # Pfeil-Widgets (Loop)
        self.block3_arrow = ArrowWidget(parent=self, arrow_type="loop", radius=16)
        self.block2_arrow = ArrowWidget(parent=self, arrow_type="loop", radius=16)
        self.block3_arrow.setActive(True)
        self.block2_arrow.setActive(False)
        self.block3_arrow.setGeometry(self.rect())
        self.block2_arrow.setGeometry(self.rect())
        self.block3_arrow.raise_()
        self.block2_arrow.raise_()

        QTimer.singleShot(0, self.update_arrow_positions)






    # =========================================================
    # PFEIL-POSITIONSAKTUALISIERUNG
    # =========================================================
    def update_arrow_positions(self):
        if hasattr(self, 'block2_arrow') and self.block2_arrow and self.block2_widget:
            local_pos_b2 = self.block2_widget.mapTo(self, QPoint(0, 0))
            self.block2_arrow.setArrowGeometry(local_pos_b2, self.block2_widget.size())

        if hasattr(self, 'block3_arrow') and self.block3_arrow and self.block3_widget:
            local_pos_b3 = self.block3_widget.mapTo(self, QPoint(0, 0))
            self.block3_arrow.setArrowGeometry(local_pos_b3, self.block3_widget.size())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.block2_arrow.setGeometry(self.rect())
        self.block3_arrow.setGeometry(self.rect())
        self.update_arrow_positions()


# =========================================================
# ARROW WIDGET
# =========================================================
class ArrowWidget(QWidget):
    def __init__(self, parent=None, arrow_type="loop", radius=20):
        super().__init__(parent)
        self.arrow_type = arrow_type
        self.radius = radius
        self.block_pos = QPoint(0, 0)
        self.block_size = QSize(100, 100)
        self.active = False
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
        elif self.arrow_type == "vertical":
            self._draw_vertical_arrow(path)

        painter.drawPath(path)
        pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.setBrush(color)
        self._drawArrowHead(painter, path)

    def _draw_vertical_arrow(self, path: QPainterPath):
        x = self.width() / 2
        path.moveTo(QPointF(x, 0))
        path.lineTo(QPointF(x, self.height()))

    def _draw_loop_arrow(self, path: QPainterPath):
        r = self.radius
        offset = 20
        bx, by = self.block_pos.x(), self.block_pos.y()
        bw, bh = self.block_size.width(), self.block_size.height()

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
        return self.palette().color(self.foregroundRole())
