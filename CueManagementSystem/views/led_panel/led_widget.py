"""
LED Visual Widget
=================

Custom Qt widget representing a numbered LED with different states and colors based on cue type.

Features:
- Visual LED representation
- State management (active/inactive)
- Color coding by cue type
- Gradient rendering
- Number display
- Custom painting
- Hover effects

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

from PySide6.QtWidgets import QFrame
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import (QPainter, QColor, QLinearGradient, QPen,
                           QRadialGradient, QPainterPath)


class LedWidget(QFrame):
    # Define colors to match table with gradients
    LED_COLORS = {
        "SINGLE SHOT": {"main": QColor("#00FF00"), "dark": QColor("#008800"), "light": QColor("#80FF80")},  # Green
        "DOUBLE SHOT": {"main": QColor("#FF0000"), "dark": QColor("#880000"), "light": QColor("#FF8080")},  # Red
        "SINGLE RUN": {"main": QColor("#FFFF00"), "dark": QColor("#888800"), "light": QColor("#FFFF80")},  # Yellow
        "DOUBLE RUN": {"main": QColor("#FFA500"), "dark": QColor("#885500"), "light": QColor("#FFD280")}  # Orange
    }

    def __init__(self, number, parent=None):
        super().__init__(parent)
        self.number = number
        self.is_active = False
        self.cue_type = None
        self.setMinimumSize(30, 30)  # Ensure minimum size for detail visibility

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Get the rect with some margin for border
        rect = self.rect().adjusted(2, 2, -2, -2)

        # Create base gradient for inactive state
        if not self.is_active:
            self.drawInactiveLed(painter, rect)
        else:
            self.drawActiveLed(painter, rect)

        # Draw the number
        self.drawNumber(painter, rect)

    def drawInactiveLed(self, painter, rect):
        # Base gradient (top-left to bottom-right)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, QColor("#404040"))
        gradient.setColorAt(1, QColor("#202020"))

        # Draw main LED body
        painter.setPen(QPen(QColor("#151515"), 1))
        painter.setBrush(gradient)
        painter.drawRoundedRect(rect, 5, 5)

        # Add highlight effect
        highlight = QPainterPath()
        highlight.addRoundedRect(QRectF(rect.left() + 2, rect.top() + 2,
                                        rect.width() * 0.7, rect.height() * 0.7), 3, 3)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 20))
        painter.drawPath(highlight)

    def drawActiveLed(self, painter, rect):
        if not self.cue_type in self.LED_COLORS:
            return

        colors = self.LED_COLORS[self.cue_type]

        # Create main gradient
        gradient = QRadialGradient(rect.center(), rect.width() / 2)
        gradient.setColorAt(0, colors["light"])
        gradient.setColorAt(0.5, colors["main"])
        gradient.setColorAt(1, colors["dark"])

        # Draw main LED body
        painter.setPen(QPen(colors["dark"], 1))
        painter.setBrush(gradient)
        painter.drawRoundedRect(rect, 5, 5)

        # Add glossy highlight
        highlight_rect = QRectF(rect.left() + rect.width() * 0.2,
                                rect.top() + rect.height() * 0.2,
                                rect.width() * 0.6, rect.height() * 0.3)

        highlight = QLinearGradient(highlight_rect.topLeft(), highlight_rect.bottomRight())
        highlight.setColorAt(0, QColor(255, 255, 255, 180))
        highlight.setColorAt(1, QColor(255, 255, 255, 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(highlight)
        painter.drawRoundedRect(highlight_rect, 3, 3)

    def drawNumber(self, painter, rect):
        # Draw number with shadow for better visibility
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)

        # Draw shadow first
        painter.setPen(QColor(0, 0, 0, 100))
        painter.drawText(rect.adjusted(1, 1, 1, 1), Qt.AlignCenter, str(self.number))

        # Draw main number
        painter.setPen(Qt.black)
        painter.drawText(rect, Qt.AlignCenter, str(self.number))

    def setState(self, cue_type=None):
        """Set LED state based on cue type"""
        self.is_active = cue_type is not None
        self.cue_type = cue_type
        self.update()
        
        # Ensure the widget is properly repainted
        if not self.is_active:
            self.repaint()