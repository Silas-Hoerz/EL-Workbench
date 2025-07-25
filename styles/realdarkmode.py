# realdarkmode.py
from PyQt6 import QtWidgets, QtCore, QtGui


class RealDarkmodeOverlay(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.WindowStaysOnTopHint |
            QtCore.Qt.WindowType.Tool
        )

        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_NoSystemBackground, True)

        self.radius = 50  # 100px Durchmesser

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(16)

        screen = QtWidgets.QApplication.primaryScreen()
        self.setGeometry(screen.geometry())

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        pos = QtGui.QCursor.pos()
        local_pos = self.mapFromGlobal(pos)

        painter.setBrush(QtGui.QColor(0, 0, 0, 250))
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())

        painter.setCompositionMode(QtGui.QPainter.CompositionMode.CompositionMode_Clear)
        painter.setBrush(QtCore.Qt.GlobalColor.transparent)
        painter.drawEllipse(local_pos, self.radius, self.radius)

        painter.end()
