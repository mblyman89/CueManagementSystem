from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, 
                             QLabel, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt

class WelcomePage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Main layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(50, 170, 50, 50)  # Top margin increased to 170px (5 inches ≈ 120px + original 50px)

        # Welcome label
        welcome_label = QLabel("Welcome to\nFirework Cue Management System")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 48px;
                font-weight: bold;
                margin-bottom: 30px;
            }
        """)
        layout.addWidget(welcome_label)

        # Create a container widget for buttons
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setAlignment(Qt.AlignHCenter)
        button_layout.setSpacing(15)

        # Button styling
        button_style = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px;
                font-size: 20px;
                min-width: 250px;
                max-width: 250px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2573a7;
                padding-top: 17px;
                padding-bottom: 13px;
            }
        """

        # Create and style buttons
        buttons = [
            ("New Show", self.on_new_show),
            ("Load Show", self.on_load_show),
            ("Import Show", self.on_import_show)
        ]

        for button_text, callback in buttons:
            button = QPushButton(button_text)
            button.setStyleSheet(button_style)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(callback)
            button_layout.addWidget(button)

        # Add button container to main layout
        layout.addWidget(button_container)

        # Add flexible space at the bottom (reduced since we already added top margin)
        layout.addStretch(1)  # Reduced stretch factor

        self.setLayout(layout)

    def on_new_show(self):
        # To be implemented
        pass