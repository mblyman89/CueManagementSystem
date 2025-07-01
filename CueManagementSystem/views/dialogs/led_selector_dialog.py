from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QRadioButton,
                               QPushButton, QLabel, QGroupBox, QButtonGroup)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class LedSelectorDialog(QDialog):
    """Dialog for selecting LED panel view mode"""

    view_changed = Signal(str)  # Signal emitted when view selection changes

    def __init__(self, parent=None, current_view="traditional"):
        super().__init__(parent)
        self.current_view = current_view
        self.setup_ui()
        self.setWindowTitle("LED Panel View Selector")
        self.setModal(True)
        self.resize(400, 300)

    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Select LED Panel View Mode")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # View selection group
        view_group = QGroupBox("View Options")
        view_layout = QVBoxLayout(view_group)

        # Button group to ensure only one selection
        self.button_group = QButtonGroup(self)

        # Traditional view option
        self.traditional_radio = QRadioButton("Traditional View")
        self.traditional_radio.setToolTip("Standard 40x25 LED grid layout")
        traditional_desc = QLabel("• 40 rows × 25 columns\n• Sequential LED numbering\n• Compact display")
        traditional_desc.setStyleSheet("color: #666; margin-left: 20px; font-size: 10px;")

        # Grouped view option
        self.grouped_radio = QRadioButton("Grouped View")
        self.grouped_radio.setToolTip("LEDs organized in draggable groups of 50")
        grouped_desc = QLabel(
            "• 20 groups of 50 LEDs each\n• 5×10 LED arrangement per group\n• Drag and drop functionality\n• Visual group borders")
        grouped_desc.setStyleSheet("color: #666; margin-left: 20px; font-size: 10px;")

        # Add radio buttons to button group
        self.button_group.addButton(self.traditional_radio, 0)
        self.button_group.addButton(self.grouped_radio, 1)

        # Set current selection
        if self.current_view == "traditional":
            self.traditional_radio.setChecked(True)
        else:
            self.grouped_radio.setChecked(True)

        # Add to layout
        view_layout.addWidget(self.traditional_radio)
        view_layout.addWidget(traditional_desc)
        view_layout.addSpacing(10)
        view_layout.addWidget(self.grouped_radio)
        view_layout.addWidget(grouped_desc)

        layout.addWidget(view_group)

        # Button layout
        button_layout = QHBoxLayout()

        # Preview button
        self.preview_button = QPushButton("Preview")
        self.preview_button.setToolTip("Preview the selected view without applying")
        self.preview_button.clicked.connect(self.preview_selection)

        # Apply button
        self.apply_button = QPushButton("Apply")
        self.apply_button.setToolTip("Apply the selected view")
        self.apply_button.clicked.connect(self.apply_selection)
        self.apply_button.setDefault(True)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.preview_button)
        button_layout.addStretch()
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        # Connect signals
        self.traditional_radio.toggled.connect(self.on_selection_changed)
        self.grouped_radio.toggled.connect(self.on_selection_changed)

        # Style the dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QRadioButton {
                font-size: 12px;
                font-weight: bold;
                spacing: 10px;
            }
            QRadioButton::indicator {
                width: 15px;
                height: 15px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #555;
                border-radius: 8px;
                background-color: #333;
            }
            QRadioButton::indicator:checked {
                border: 2px solid #4CAF50;
                border-radius: 8px;
                background-color: #4CAF50;
            }
            QPushButton {
                background-color: #404040;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
            QPushButton:default {
                border: 2px solid #4CAF50;
            }
        """)

    def on_selection_changed(self):
        """Handle radio button selection changes"""
        # Enable/disable preview button based on whether selection changed
        if self.traditional_radio.isChecked():
            new_view = "traditional"
        else:
            new_view = "grouped"

        self.preview_button.setEnabled(new_view != self.current_view)

    def preview_selection(self):
        """Preview the selected view without applying permanently"""
        selected_view = "traditional" if self.traditional_radio.isChecked() else "grouped"
        self.view_changed.emit(f"preview_{selected_view}")

    def apply_selection(self):
        """Apply the selected view and close dialog"""
        selected_view = "traditional" if self.traditional_radio.isChecked() else "grouped"
        self.view_changed.emit(selected_view)
        self.accept()

    def get_selected_view(self):
        """Get the currently selected view"""
        return "traditional" if self.traditional_radio.isChecked() else "grouped"

    def set_current_view(self, view):
        """Set the current view selection"""
        self.current_view = view
        if view == "traditional":
            self.traditional_radio.setChecked(True)
        else:
            self.grouped_radio.setChecked(True)
        self.on_selection_changed()