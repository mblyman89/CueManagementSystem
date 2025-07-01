from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import Qt


class CustomCornerWidget(QWidget):
    """
    Custom corner widget to replace the problematic white corner button
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 30)  # Adjust size as needed

    def paintEvent(self, event):
        """Paint the corner with the desired dark blue color"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#1a1a2e"))

        # Draw border to match headers
        painter.setPen(QColor("#333344"))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))