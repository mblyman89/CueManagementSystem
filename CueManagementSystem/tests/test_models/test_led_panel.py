import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from views.led_panel.led_grid import LedGrid
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt, QSize


def create_test_led_data():
    """
    Returns test data specifically formatted to test LED panel functionality
    This matches the table data structure for consistency
    """
    return [
        [1, "SINGLE SHOT", 1, "1", 0.0, 0.0, "0:00"],
        [2, "DOUBLE SHOT", 2, "2,3", 0.0, 0.0, "1:00"],
        [3, "SINGLE RUN", 6, "4,5,6,7,8,9", 0.5, 2.5, "2:00"],
        [4, "DOUBLE RUN", 6, "10,11,12,13,14,15", 0.25, 4.0, "5:00"]
    ]


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LED Panel Test")

        # Create the LED panel
        self.led_panel = LedGrid()
        self.setCentralWidget(self.led_panel)

        # Set a reasonable fixed size for testing
        self.setMinimumSize(800, 600)
        self.setMaximumSize(1200, 900)

        # Load test data
        test_data = create_test_led_data()
        self.led_panel.updateFromCueData(test_data)


def test_led_panel():
    app = QApplication(sys.argv)

    # Create and show the test window
    window = TestWindow()
    window.show()

    return app, window


if __name__ == "__main__":
    app, window = test_led_panel()
    sys.exit(app.exec())
