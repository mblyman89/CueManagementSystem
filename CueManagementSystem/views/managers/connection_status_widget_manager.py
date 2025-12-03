"""
Connection Status Display Widget
================================

Widget and status bar for displaying connection status with visual indicators and quick actions.

Features:
- Visual connection indicators
- Connection details display
- Quick reconnect action
- Quick disconnect action
- Color-coded status
- Status bar integration
- Real-time updates

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                               QPushButton, QFrame)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from datetime import datetime

class ConnectionStatusWidget(QWidget):

    # Signals
    reconnect_requested = Signal()
    disconnect_requested = Signal()
    test_connection_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Connection state
        self.connected = False
        self.host = ""
        self.username = ""
        self.last_activity = None
        self.connecting = False

        # Setup UI
        self.setup_ui()

        # Update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # Update every second

    def setup_ui(self):
        """Setup the widget UI"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setSpacing(10)

        # Status indicator (colored circle) - LARGER
        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont("Arial", 32))  # Increased from 20 to 32
        self.status_indicator.setStyleSheet("color: #e74c3c;")  # Red by default
        self.status_indicator.setToolTip("Disconnected")
        main_layout.addWidget(self.status_indicator)

        # Status text layout
        status_text_layout = QVBoxLayout()
        status_text_layout.setSpacing(2)

        # Connection status label - LARGER
        self.status_label = QLabel("Disconnected")
        self.status_label.setFont(QFont("Arial", 12, QFont.Bold))  # Increased from 10 to 12
        status_text_layout.addWidget(self.status_label)

        # Connection details label - LARGER
        self.details_label = QLabel("No connection")
        self.details_label.setFont(QFont("Arial", 11))  # Increased from 9 to 11
        self.details_label.setStyleSheet("color: #555555;")  # Darker for better visibility
        status_text_layout.addWidget(self.details_label)

        main_layout.addLayout(status_text_layout)

        # Network mode label (WiFi/AdHoc indicator)
        self.mode_label = QLabel("Mode: WiFi")
        self.mode_label.setStyleSheet("""
            QLabel {
                padding: 4px 8px;
                border: 1px solid #2980b9;
                border-radius: 3px;
                background-color: #2980b9;
                color: white;
                font-weight: bold;
                font-size: 10pt;
            }
        """)
        self.mode_label.setToolTip("Network mode (WiFi or AdHoc)")
        main_layout.addWidget(self.mode_label)

        # Spacer
        main_layout.addStretch()

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        # Test connection button - BETTER STYLING
        self.test_button = QPushButton("Test")
        self.test_button.setFixedWidth(110)
        self.test_button.setFixedHeight(36)
        self.test_button.setToolTip("Test connection to Pi")
        self.test_button.clicked.connect(self.test_connection_requested.emit)
        button_layout.addWidget(self.test_button)

        # Reconnect button - BETTER STYLING
        self.reconnect_button = QPushButton("Reconnect")
        self.reconnect_button.setFixedWidth(110)
        self.reconnect_button.setFixedHeight(36)
        self.reconnect_button.setToolTip("Reconnect to Pi")
        self.reconnect_button.clicked.connect(self.reconnect_requested.emit)
        self.reconnect_button.setEnabled(False)
        button_layout.addWidget(self.reconnect_button)

        # Disconnect button - BETTER STYLING
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setFixedWidth(110)
        self.disconnect_button.setFixedHeight(36)
        self.disconnect_button.setToolTip("Disconnect from Pi")
        self.disconnect_button.clicked.connect(self.disconnect_requested.emit)
        self.disconnect_button.setEnabled(False)
        button_layout.addWidget(self.disconnect_button)

        main_layout.addLayout(button_layout)

        # Style the widget - IMPROVED BUTTON CONTRAST
        self.setStyleSheet("""
            ConnectionStatusWidget {
                background-color: #f5f5f5;
                border: 1px solid #cccccc;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #3498db;
                color: #ffffff;
                font-weight: bold;
                border: 1px solid #2980b9;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
                border: 1px solid #21618c;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
                border: 1px solid #95a5a6;
            }
        """)

    def set_connected(self, connected: bool, host: str = "", username: str = ""):
        """
        Update connection status

        Args:
            connected: Whether connected
            host: Host address (if empty when disconnecting, preserves current value)
            username: Username (if empty when disconnecting, preserves current value)
        """
        self.connected = connected

        # Only update host/username if provided, or if connecting
        # This preserves the values when disconnecting so reconnect button works
        if host or connected:
            self.host = host
        if username or connected:
            self.username = username

        self.connecting = False

        if connected:
            self.last_activity = datetime.now()

        self.update_display()

    def set_connecting(self, host: str = "", username: str = ""):
        """
        Set status to connecting

        Args:
            host: Host address
            username: Username
        """
        self.connecting = True
        self.connected = False
        self.host = host
        self.username = username
        self.update_display()

    def update_last_activity(self):
        """Update last activity timestamp"""
        if self.connected:
            self.last_activity = datetime.now()
            self.update_display()

    def set_network_mode(self, mode: str):
        """
        Set the network mode display

        Args:
            mode: "WiFi" or "AdHoc"
        """
        self.mode_label.setText(f"Mode: {mode}")

    def update_display(self):
        """Update the display based on current state"""
        if self.connecting:
            # Connecting state (yellow)
            self.status_indicator.setStyleSheet("color: #f39c12;")
            self.status_indicator.setToolTip("Connecting...")
            self.status_label.setText("Connecting...")
            self.details_label.setText(f"{self.username}@{self.host}")
            self.reconnect_button.setEnabled(False)
            self.disconnect_button.setEnabled(False)

        elif self.connected:
            # Connected state (green)
            self.status_indicator.setStyleSheet("color: #2ecc71;")
            self.status_indicator.setToolTip("Connected")
            self.status_label.setText("Connected")

            # Show last activity
            if self.last_activity:
                elapsed = (datetime.now() - self.last_activity).total_seconds()
                if elapsed < 60:
                    time_str = f"{int(elapsed)}s ago"
                elif elapsed < 3600:
                    time_str = f"{int(elapsed / 60)}m ago"
                else:
                    time_str = f"{int(elapsed / 3600)}h ago"

                self.details_label.setText(f"{self.username}@{self.host} • Last activity: {time_str}")
            else:
                self.details_label.setText(f"{self.username}@{self.host}")

            self.reconnect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)

        else:
            # Disconnected state (red)
            self.status_indicator.setStyleSheet("color: #e74c3c;")
            self.status_indicator.setToolTip("Disconnected")
            self.status_label.setText("Disconnected")

            if self.host:
                self.details_label.setText(f"Last: {self.username}@{self.host}")
            else:
                self.details_label.setText("No connection")

            self.reconnect_button.setEnabled(bool(self.host))
            self.disconnect_button.setEnabled(False)

    def get_status_text(self) -> str:
        """Get current status as text"""
        if self.connecting:
            return f"Connecting to {self.username}@{self.host}..."
        elif self.connected:
            return f"Connected to {self.username}@{self.host}"
        else:
            return "Disconnected"


class ConnectionStatusBar(QFrame):
    """
    Connection status bar that can be added to any window

    This is a styled frame containing the ConnectionStatusWidget
    """

    # Signals
    reconnect_requested = Signal()
    disconnect_requested = Signal()
    test_connection_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Setup frame style
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)

        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Add status widget
        self.status_widget = ConnectionStatusWidget(self)
        layout.addWidget(self.status_widget)

        # Connect signals
        self.status_widget.reconnect_requested.connect(self.reconnect_requested.emit)
        self.status_widget.disconnect_requested.connect(self.disconnect_requested.emit)
        self.status_widget.test_connection_requested.connect(self.test_connection_requested.emit)

    def set_connected(self, connected: bool, host: str = "", username: str = ""):
        """Update connection status"""
        self.status_widget.set_connected(connected, host, username)

    def set_connecting(self, host: str = "", username: str = ""):
        """Set status to connecting"""
        self.status_widget.set_connecting(host, username)

    def update_last_activity(self):
        """Update last activity timestamp"""
        self.status_widget.update_last_activity()

    def get_status_text(self) -> str:
        """Get current status as text"""
        return self.status_widget.get_status_text()

    def set_network_mode(self, mode: str):
        """Set the network mode display"""
        self.status_widget.set_network_mode(mode)

    @property
    def mode_label(self):
        """Access to the mode label for direct styling"""
        return self.status_widget.mode_label

    @property
    def host(self):
        """Access to host property"""
        return self.status_widget.host

    @host.setter
    def host(self, value):
        """Set host property"""
        self.status_widget.host = value

    @property
    def username(self):
        """Access to username property"""
        return self.status_widget.username

    @username.setter
    def username(self, value):
        """Set username property"""
        self.status_widget.username = value