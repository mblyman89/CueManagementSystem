from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableView
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor
from views.table.cue_table import CueTableView


class CueTableWidget(QWidget):
    """
    Custom widget wrapper for the cue table that eliminates the white corner issue
    by providing complete control over the table's appearance and styling.
    """

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        # Create layout with no margins or spacing
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create the cue table
        self.cue_table = CueTableView()

        # Remove any conflicting background styling
        self.cue_table.setStyleSheet("")

        # Apply comprehensive styling that covers all elements including corner
        comprehensive_style = """
            QTableView {
                background-color: #1a1a2e;
                gridline-color: #333344;
                color: white;
                selection-background-color: #2d2d44;
                selection-color: white;
                border: none;
            }
            QTableView::item:selected {
                background-color: #2d2d44;
            }
            QTableView::item:focus {
                background-color: #3d3d54;
            }
            QTableView::drop-indicator {
                background-color: #4CAF50;
                border: 2px solid #45a049;
            }
            QHeaderView::section {
                background-color: #1a1a2e;
                color: white;
                padding: 5px;
                border: 1px solid #333344;
            }
            QTableCornerButton::section {
                background-color: #1a1a2e;
                border: 1px solid #333344;
            }
        """

        self.cue_table.setStyleSheet(comprehensive_style)

        # Force corner button to be enabled and styled
        self.cue_table.setCornerButtonEnabled(True)

        # Set widget background to match table
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a2e;
                border: none;
            }
        """)

        # Add table to layout
        layout.addWidget(self.cue_table)

    def paintEvent(self, event):
        """
        Custom paint event to ensure the entire widget background is consistent
        """
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#1a1a2e"))
        super().paintEvent(event)

    # Expose cue table properties and methods
    @property
    def model(self):
        return self.cue_table.model

    @property
    def selectionModel(self):
        return self.cue_table.selectionModel

    def doubleClicked(self):
        return self.cue_table.doubleClicked

    def delete_selected_cue(self):
        return self.cue_table.delete_selected_cue()

    def delete_all_cues(self):
        return self.cue_table.delete_all_cues()