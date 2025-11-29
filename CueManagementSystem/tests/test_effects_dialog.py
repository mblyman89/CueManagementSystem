"""
Test script for the Firework Effects Dialog
============================================

This script demonstrates the new visual effects configuration dialog
integrated with the cue table via right-click context menu.

Usage:
    python test_effects_dialog.py

Features Demonstrated:
- Right-click on any cue to open effects dialog
- Configure 30+ Excalibur shell effects
- Set colors, physics, timing, and audio parameters
- Visual effect column shows configured effect
- Clear effects option in context menu

Author: Michael Lyman
"""

import sys
import os

# Add the CueManagementSystem directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CueManagementSystem'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QMessageBox
from PySide6.QtCore import Qt
from views.table.cue_table_widget import CueTableWidget
import json


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Firework Effects Dialog Test")
        self.setGeometry(100, 100, 1200, 600)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Add instructions
        instructions = QLabel(
            "<h2>Firework Visual Effects Configuration Test</h2>"
            "<p><b>Instructions:</b></p>"
            "<ul>"
            "<li><b>Right-click</b> on any cue row to open the Visual Effects dialog</li>"
            "<li>Configure shell type, colors, physics, timing, and audio</li>"
            "<li>Click 'Apply' to save the configuration</li>"
            "<li>The 'VISUAL EFFECT' column will show the configured effect</li>"
            "<li>Right-click again to modify or clear effects</li>"
            "</ul>"
            "<p><i>Note: Preview functionality requires Unreal Engine 5 connection</i></p>"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                color: white;
                padding: 15px;
                border-radius: 5px;
                border: 2px solid #4CAF50;
            }
        """)
        layout.addWidget(instructions)

        # Create cue table
        self.cue_table_widget = CueTableWidget()
        layout.addWidget(self.cue_table_widget)

        # Connect to visual effect signal
        self.cue_table_widget.visual_effect_configured().connect(self.on_visual_effect_configured)

        # Add some sample cues
        self.add_sample_cues()

        # Apply dark theme
        self.apply_dark_theme()

    def add_sample_cues(self):
        """Add sample cues to the table for testing"""
        sample_cues = [
            [1, "SINGLE SHOT", "1,2,3", 0.5, "0:00.00"],
            [2, "DOUBLE SHOT", "4,5", 0.3, "0:01.50"],
            [3, "SINGLE RUN", "6,7,8,9", 0.2, "0:03.00"],
            [4, "DOUBLE RUN", "10,11,12", 0.25, "0:05.00"],
            [5, "SINGLE SHOT", "13", 0.0, "0:07.00"],
            [6, "SINGLE SHOT", "14,15", 0.4, "0:09.00"],
            [7, "SINGLE RUN", "16,17,18,19,20", 0.15, "0:11.00"],
            [8, "DOUBLE SHOT", "21,22,23", 0.35, "0:13.00"],
        ]

        for cue in sample_cues:
            self.cue_table_widget.model._data.append(cue)

        self.cue_table_widget.model.layoutChanged.emit()

    def on_visual_effect_configured(self, row, visual_properties):
        """Handle visual effect configuration"""
        effect_type = visual_properties.get('effect_type', 'Unknown')
        effect_name = effect_type.replace('_', ' ').title()

        # Show confirmation message
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Visual Effect Configured")
        msg.setText(f"<h3>Effect configured for Cue #{row + 1}</h3>")
        msg.setInformativeText(
            f"<b>Effect:</b> {effect_name}<br>"
            f"<b>Size:</b> {visual_properties.get('size', 'N/A')}<br>"
            f"<b>Primary Color:</b> RGB{visual_properties.get('primary_color', 'N/A')}<br>"
            f"<b>Star Count:</b> {visual_properties.get('star_count', 'N/A')}<br>"
            f"<b>Master Volume:</b> {visual_properties.get('master_volume', 'N/A')}"
        )
        msg.setDetailedText(json.dumps(visual_properties, indent=2))
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #2d2d2d;
            }
            QLabel {
                color: white;
            }
        """)
        msg.exec()

        print(f"\n=== Visual Effect Configured for Row {row} ===")
        print(json.dumps(visual_properties, indent=2))

    def apply_dark_theme(self):
        """Apply dark theme to the window"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
            QWidget {
                background-color: #1a1a1a;
                color: white;
            }
        """)


def main():
    app = QApplication(sys.argv)

    # Set application-wide dark theme
    app.setStyle("Fusion")

    window = TestWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()