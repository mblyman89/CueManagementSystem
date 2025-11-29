"""
Test script for the Excalibur Shell Selector Dialog
====================================================

This script demonstrates the new simplified, user-friendly dialog
for selecting Excalibur artillery shells.

Usage:
    python test_excalibur_selector.py

Features Demonstrated:
- Single dropdown with 24 authentic Excalibur shells
- Automatic configuration of all parameters
- Random launch angle assignment
- Shell name displayed in cue table
- No tabs, no manual configuration!

Author: Michael Lyman
"""

import sys
import os

# Add the CueManagementSystem directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CueManagementSystem_Full/CueManagementSystem'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QMessageBox
from PySide6.QtCore import Qt
from views.table.cue_table_widget import CueTableWidget
import json


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Excalibur Shell Selector Test")
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
            "<h2>🎆 Excalibur Shell Selector - Simplified Interface</h2>"
            "<p><b>Instructions:</b></p>"
            "<ul>"
            "<li><b>Right-click</b> on any cue row to select an Excalibur shell</li>"
            "<li>Choose from 24 authentic Excalibur artillery shells</li>"
            "<li>All physics, colors, timing, and audio configured automatically!</li>"
            "<li>Launch angle randomly assigned from 5 options (-30°, -15°, 0°, +15°, +30°)</li>"
            "<li>Shell name appears in the 'VISUAL EFFECT' column</li>"
            "<li><b>No tabs, no manual configuration - just pick and go!</b></li>"
            "</ul>"
            "<p><i>Based on authentic Excalibur specifications: 60g shells, 250ft burst height, very loud!</i></p>"
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
        self.cue_table_widget.visual_effect_configured().connect(self.on_shell_configured)

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

    def on_shell_configured(self, row, visual_properties):
        """Handle shell configuration"""
        shell_name = visual_properties.get('shell_name', 'Unknown')
        launch_angle = visual_properties.get('launch_angle', 0)
        star_count = visual_properties.get('star_count', 0)
        explosion_volume = visual_properties.get('explosion_volume', 0)

        # Show confirmation message
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Excalibur Shell Configured")
        msg.setText(f"<h3>🎆 {shell_name}</h3>")
        msg.setInformativeText(
            f"<b>Cue:</b> #{row + 1}<br>"
            f"<b>Shell:</b> {shell_name}<br>"
            f"<b>Launch Angle:</b> {launch_angle}° {'(straight up)' if launch_angle == 0 else '(angled)'}<br>"
            f"<b>Star Count:</b> {star_count} particles<br>"
            f"<b>Explosion Volume:</b> {explosion_volume}x (Excalibur loud!)<br>"
            f"<br>"
            f"<i>All parameters configured automatically based on<br>"
            f"authentic Excalibur specifications!</i>"
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

        print(f"\n=== Excalibur Shell Configured for Cue {row + 1} ===")
        print(f"Shell: {shell_name}")
        print(f"Launch Angle: {launch_angle}°")
        print(f"Configuration:")
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