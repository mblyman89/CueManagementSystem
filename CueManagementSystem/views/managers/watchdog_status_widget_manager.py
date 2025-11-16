"""
Watchdog Timer Status Widget
============================

Status bar widget that displays the health and status of the watchdog timer system with visual indicators.

Features:
- Real-time watchdog status display
- Active/inactive state indication
- Warning and critical state alerts
- Consecutive failure tracking
- Success rate monitoring
- Color-coded status indicators
- Status bar integration

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont


class WatchdogStatusWidget(QWidget):
    """Widget to display watchdog status in status bar."""

    def __init__(self, parent=None):
        super().__init__(parent)

        print("[WATCHDOG WIDGET] __init__ called")

        # State
        self.is_monitoring = False
        self.consecutive_failures = 0
        self.success_rate = 100.0

        # Setup UI
        self._setup_ui()

        # Update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(1000)  # Update every second

        print("[WATCHDOG WIDGET] Initialization complete")

    def _setup_ui(self):
        """Setup the UI components."""
        # Professional styling - transparent background, integrates with status bar
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                padding: 2px 8px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(6)

        # Separator line
        separator = QLabel("|")
        separator.setStyleSheet("color: #95a5a6; font-weight: bold;")
        layout.addWidget(separator)

        # Watchdog label - professional, no emoji
        self.watchdog_label = QLabel("WATCHDOG")
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        self.watchdog_label.setFont(font)
        self.watchdog_label.setStyleSheet("color: white;")
        layout.addWidget(self.watchdog_label)

        # Status indicator - using text instead of emoji
        self.status_indicator = QLabel("●")
        status_font = QFont()
        status_font.setPointSize(14)
        status_font.setBold(True)
        self.status_indicator.setFont(status_font)
        layout.addWidget(self.status_indicator)

        # Status text
        self.status_text = QLabel("Inactive")
        text_font = QFont()
        text_font.setPointSize(9)
        text_font.setBold(True)
        self.status_text.setFont(text_font)
        layout.addWidget(self.status_text)

        # Success rate
        self.success_rate_label = QLabel("")
        rate_font = QFont()
        rate_font.setPointSize(9)
        rate_font.setBold(False)
        self.success_rate_label.setFont(rate_font)
        layout.addWidget(self.success_rate_label)

        # Set initial state
        self._update_display()

    def update_status(self, status_dict):
        """
        Update watchdog status.

        Args:
            status_dict: Dictionary with watchdog status information
        """
        print(f"[WATCHDOG WIDGET] update_status called")
        print(f"[WATCHDOG WIDGET] status_dict = {status_dict}")

        if not status_dict:
            self.is_monitoring = False
            self.consecutive_failures = 0
            self.success_rate = 100.0
        else:
            self.is_monitoring = status_dict.get('is_monitoring', False)
            self.consecutive_failures = status_dict.get('consecutive_failures', 0)
            self.success_rate = status_dict.get('success_rate', 100.0)

        print(
            f"[WATCHDOG WIDGET] After update: monitoring={self.is_monitoring}, failures={self.consecutive_failures}, rate={self.success_rate:.1f}%")
        self._update_display()

    def _update_display(self):
        """Update the display based on current state."""
        print(
            f"[WATCHDOG WIDGET] _update_display called: monitoring={self.is_monitoring}, failures={self.consecutive_failures}")

        if not self.is_monitoring:
            # Inactive state - Gray
            print("[WATCHDOG WIDGET] Setting to INACTIVE (gray)")
            self.status_indicator.setText("●")
            self.status_indicator.setStyleSheet("color: #7f8c8d;")  # Medium gray
            self.status_text.setText("Inactive")
            self.status_text.setStyleSheet("color: #95a5a6; font-weight: bold;")  # Light gray
            self.success_rate_label.setText("")
            self.success_rate_label.setStyleSheet("")
        else:
            # Active state
            if self.consecutive_failures == 0:
                # All good - Bright Green
                print("[WATCHDOG WIDGET] Setting to ACTIVE GREEN")
                self.status_indicator.setText("●")
                self.status_indicator.setStyleSheet("color: #2ecc71;")  # Bright green
                self.status_text.setText("Active")
                self.status_text.setStyleSheet("color: #2ecc71; font-weight: bold;")  # Bright green
            elif self.consecutive_failures < 3:
                # Warning - Orange
                print("[WATCHDOG WIDGET] Setting to WARNING ORANGE")
                self.status_indicator.setText("●")
                self.status_indicator.setStyleSheet("color: #f39c12;")  # Orange
                self.status_text.setText(f"Warning")
                self.status_text.setStyleSheet("color: #f39c12; font-weight: bold;")  # Orange
            else:
                # Critical - Bright Red
                print("[WATCHDOG WIDGET] Setting to CRITICAL RED")
                self.status_indicator.setText("●")
                self.status_indicator.setStyleSheet("color: #e74c3c;")  # Bright red
                self.status_text.setText(f"Critical")
                self.status_text.setStyleSheet("color: #e74c3c; font-weight: bold;")  # Bright red

            # Show success rate with white text
            self.success_rate_label.setText(f"{self.success_rate:.1f}%")
            self.success_rate_label.setStyleSheet("color: white; font-weight: normal;")

    def set_monitoring(self, monitoring: bool):
        """Set monitoring state."""
        print(f"[WATCHDOG WIDGET] set_monitoring called: {monitoring}")
        self.is_monitoring = monitoring
        if not monitoring:
            self.consecutive_failures = 0
            self.success_rate = 100.0
        self._update_display()

    def set_failures(self, failures: int):
        """Set consecutive failures count."""
        print(f"[WATCHDOG WIDGET] set_failures called: {failures}")
        self.consecutive_failures = failures
        self._update_display()

    def set_success_rate(self, rate: float):
        """Set success rate percentage."""
        print(f"[WATCHDOG WIDGET] set_success_rate called: {rate}")
        self.success_rate = rate
        self._update_display()

    def cleanup(self):
        """Cleanup resources when widget is being destroyed."""
        print("[WATCHDOG WIDGET] cleanup called")
        if hasattr(self, 'update_timer') and self.update_timer:
            self.update_timer.stop()
            self.update_timer.deleteLater()
            self.update_timer = None

    def closeEvent(self, event):
        """Handle widget close event."""
        print("[WATCHDOG WIDGET] closeEvent called")
        self.cleanup()
        super().closeEvent(event)

    def __del__(self):
        """Destructor - ensure cleanup happens."""
        try:
            if hasattr(self, 'update_timer') and self.update_timer:
                self.update_timer.stop()
        except:
            pass
