import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from views.table.cue_table import CueTableModel, CueTableView
from PySide6.QtWidgets import QApplication


def create_test_data():
    return [
        [1, "SINGLE SHOT", 1, "1", 0.0, 0.0, "0:00"],
        [2, "DOUBLE SHOT", 2, "2,3", 0.0, 0.0, "1:00"],
        [3, "SINGLE RUN", 6, "4,5,6,7,8,9", 0.5, 2.5, "2:00"],
        [4, "DOUBLE RUN", 6, "10,11,12,13,14,15", 0.25, 4.0, "5:00"]
    ]


def test_table_with_data():
    app = QApplication(sys.argv)

    # Create the table view
    table_view = CueTableView()

    # Load test data
    table_view.model._data = create_test_data()

    # Show the table
    table_view.show()

    return app, table_view


if __name__ == "__main__":
    app, table = test_table_with_data()
    sys.exit(app.exec())