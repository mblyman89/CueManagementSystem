from PySide6.QtWidgets import QPushButton, QSizePolicy
from PySide6.QtCore import Qt, Signal
from utils.color_utils import lighten_color, darken_color

from utils.color_utils import lighten_color, darken_color


class ButtonWidget(QPushButton):
    """
    Custom button widget for the application control panel

    Features:
    - Customizable colors
    - Active/inactive states
    - Consistent styling
    """

    def __init__(self, text, color="#333333", parent=None):
        super().__init__(text, parent)
        self.setText(text)
        self.base_color = color
        self.is_active = True

        # Set up button appearance
        self.setup_appearance()

    def setup_appearance(self):
        """Configure the button's visual appearance"""
        # Set default active state
        self.setProperty("isActive", True)

        # Set style sheet based on color
        self.setStyleSheet(self.generate_stylesheet())

        # Set cursor and size policy
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)

    def generate_stylesheet(self):
        """Generate stylesheet based on the button's color"""
        return f"""
            QPushButton {{
                background-color: {self.base_color};
                color: white;
                border: 2px solid black;
                border-radius: 6px;
                padding: 10px 10px;
                min-width: 120px;
                min-height: 40px;
                font-size: 20px;
                font-weight: bold;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {lighten_color(self.base_color, 20)};
                border: 2px solid #555;
            }}
            QPushButton:pressed {{
                background-color: {darken_color(self.base_color, 10)};
                padding-top: 14px;
                padding-bottom: 10px;
                border: 2px solid black;
            }}
            QPushButton[isActive="false"] {{
                background-color: #555555;
                color: #aaaaaa;
            }}
            QPushButton[isActive="false"]:hover {{
                background-color: #666666;
                border: 2px solid #555;
            }}
            QPushButton[isActive="false"]:pressed {{
                background-color: #444444;
                padding-top: 14px;
                padding-bottom: 10px;
                border: 2px solid black;
            }}
        """

    def set_active(self, active):
        """Set the active state of the button"""
        self.is_active = active
        self.setProperty("isActive", active)
        # Keep the button enabled for UI interactions, but visually indicate inactive state
        # Don't disable the button so hover and press effects still work
        self.style().unpolish(self)
        self.style().polish(self)

        # Change cursor appearance based on active state
        if active:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ForbiddenCursor)
    
    def get_active_state(self):
        """Get the active state of the button"""
        return self.is_active
        
    def mousePressEvent(self, event):
        """Override mouse press event to check active state"""
        if self.is_active:
            super().mousePressEvent(event)
        else:
            # Ignore the event if button is inactive
            event.ignore()
            
    def mouseReleaseEvent(self, event):
        """Override mouse release event to check active state"""
        if self.is_active:
            super().mouseReleaseEvent(event)
        else:
            # Ignore the event if button is inactive
            event.ignore()