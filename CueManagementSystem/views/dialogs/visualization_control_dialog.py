"""
Visualization Control Dialog
=============================

Dialog for controlling the UE5 visualization system, including:
- WebSocket server start/stop
- Connection status monitoring
- Visualization enable/disable
- Statistics display
- Test firework launch

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QPushButton, QLabel, QSpinBox, QCheckBox,
                               QTextEdit, QComboBox, QMessageBox)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from typing import Optional
import asyncio


class VisualizationControlDialog(QDialog):
    """
    Control panel for UE5 visualization system

    Features:
    - Start/stop WebSocket server
    - Monitor connection status
    - Enable/disable visualization
    - View statistics
    - Test firework effects
    """

    # Signals
    visualization_enabled_changed = Signal(bool)
    server_started = Signal(int)  # port
    server_stopped = Signal()

    def __init__(self, vr_preview_controller, parent=None):
        super().__init__(parent)
        self.vr_preview_controller = vr_preview_controller
        self.visualization_bridge = vr_preview_controller.get_visualization_bridge()

        self.setWindowTitle("Visualization Control Panel")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        # Make dialog non-modal and allow it to be minimized/hidden
        from PySide6.QtCore import Qt
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)

        self.init_ui()

        # Update timer for statistics
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_statistics)
        self.update_timer.start(1000)  # Update every second

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()

        # Server Control Group
        server_group = self.create_server_control_group()
        layout.addWidget(server_group)

        # Connection Status Group
        status_group = self.create_status_group()
        layout.addWidget(status_group)

        # Visualization Control Group
        viz_group = self.create_visualization_control_group()
        layout.addWidget(viz_group)

        # Test Controls Group
        test_group = self.create_test_group()
        layout.addWidget(test_group)

        # Statistics Group
        stats_group = self.create_statistics_group()
        layout.addWidget(stats_group)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def create_server_control_group(self) -> QGroupBox:
        """Create server control group"""
        group = QGroupBox("WebSocket Server")
        layout = QVBoxLayout()

        # Port selection
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.port_spinbox = QSpinBox()
        self.port_spinbox.setRange(1024, 65535)
        self.port_spinbox.setValue(8765)
        port_layout.addWidget(self.port_spinbox)
        port_layout.addStretch()
        layout.addLayout(port_layout)

        # Start/Stop buttons
        btn_layout = QHBoxLayout()
        self.start_server_btn = QPushButton("Start Server")
        self.start_server_btn.clicked.connect(self.start_server)
        btn_layout.addWidget(self.start_server_btn)

        self.stop_server_btn = QPushButton("Stop Server")
        self.stop_server_btn.clicked.connect(self.stop_server)
        self.stop_server_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_server_btn)

        layout.addLayout(btn_layout)

        # Server status
        self.server_status_label = QLabel("Status: Not Running")
        self.server_status_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.server_status_label)

        group.setLayout(layout)
        return group

    def create_status_group(self) -> QGroupBox:
        """Create connection status group"""
        group = QGroupBox("Connection Status")
        layout = QVBoxLayout()

        # Connection status
        self.connection_status_label = QLabel("UE5 Client: Not Connected")
        self.connection_status_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.connection_status_label)

        # Client info
        self.client_info_label = QLabel("No client information")
        layout.addWidget(self.client_info_label)

        group.setLayout(layout)
        return group

    def create_visualization_control_group(self) -> QGroupBox:
        """Create visualization control group"""
        group = QGroupBox("Visualization Info")
        layout = QVBoxLayout()

        # Info label
        info_label = QLabel(
            "VR Preview is integrated into the Preview Show workflow.\n\n"
            "To use VR preview:\n"
            "1. Start the WebSocket server above\n"
            "2. Connect UE5 to the server\n"
            "3. Click 'Preview Show' button\n"
            "4. Select 'Preview VR' in the music dialog\n\n"
            "VR preview will show a fullscreen countdown and execute your show in UE5."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #333; font-size: 11px;")
        layout.addWidget(info_label)

        group.setLayout(layout)
        return group

    def create_test_group(self) -> QGroupBox:
        """Create test controls group"""
        group = QGroupBox("Test Controls")
        layout = QVBoxLayout()

        # Effect selector
        effect_layout = QHBoxLayout()
        effect_layout.addWidget(QLabel("Test Effect:"))
        self.test_effect_combo = QComboBox()
        self.test_effect_combo.addItems([
            "Red Peony",
            "Blue Chrysanthemum",
            "Gold Brocade Crown",
            "Silver Willow",
            "Purple Dahlia",
            "Silver Crackling Palm",
            "Jumbo Crackling",
            "Brocade to Blue Whirlwind"
        ])
        effect_layout.addWidget(self.test_effect_combo)
        layout.addLayout(effect_layout)

        # Launch test button
        self.launch_test_btn = QPushButton("Launch Test Firework")
        self.launch_test_btn.clicked.connect(self.launch_test_firework)
        layout.addWidget(self.launch_test_btn)

        # Test status
        self.test_status_label = QLabel("")
        layout.addWidget(self.test_status_label)

        group.setLayout(layout)
        return group

    def create_statistics_group(self) -> QGroupBox:
        """Create statistics display group"""
        group = QGroupBox("Statistics")
        layout = QVBoxLayout()

        # Statistics text
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(150)
        font = QFont("Courier New", 9)
        self.stats_text.setFont(font)
        layout.addWidget(self.stats_text)

        group.setLayout(layout)
        return group

    def start_server(self):
        """Start the WebSocket server"""
        try:
            port = self.port_spinbox.value()

            # Start server using visualization bridge (runs in its own thread)
            success = self.visualization_bridge.start_server()

            if success:
                self.start_server_btn.setEnabled(False)
                self.stop_server_btn.setEnabled(True)
                self.port_spinbox.setEnabled(False)

                self.server_status_label.setText(f"Status: Running on port {port}")
                self.server_status_label.setStyleSheet("color: green; font-weight: bold;")

                self.server_started.emit(port)
            else:
                self.server_status_label.setText("Status: Failed to start")
                self.server_status_label.setStyleSheet("color: red; font-weight: bold;")

            QMessageBox.information(
                self,
                "Server Started",
                f"WebSocket server started on port {port}\n\n"
                f"UE5 should connect to: ws://localhost:{port}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Server Start Failed",
                f"Failed to start server: {str(e)}"
            )

    def stop_server(self):
        """Stop the WebSocket server"""
        try:
            # Stop server using visualization bridge
            import asyncio
            asyncio.create_task(self.visualization_bridge.stop_server())

            self.start_server_btn.setEnabled(True)
            self.stop_server_btn.setEnabled(False)
            self.port_spinbox.setEnabled(True)

            self.server_status_label.setText("Status: Not Running")
            self.server_status_label.setStyleSheet("color: red; font-weight: bold;")

            self.server_stopped.emit()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Server Stop Failed",
                f"Failed to stop server: {str(e)}"
            )

    def launch_test_firework(self):
        """Launch a test firework effect"""
        if not self.visualization_bridge.is_connected():
            QMessageBox.warning(
                self,
                "Not Connected",
                "UE5 client is not connected. Please start the server and connect UE5 first."
            )
            return

        try:
            # Get selected effect
            effect_name = self.test_effect_combo.currentText()

            # Create a test cue with the selected effect
            from models.cue_visual_model import EnhancedCue
            from models.excalibur_effects_model import ExcaliburEffects

            # Get the effect configuration
            effect_config = None
            for category_effects in ExcaliburEffects.EFFECTS.values():
                if effect_name in category_effects:
                    effect_config = category_effects[effect_name]
                    break

            if not effect_config:
                self.test_status_label.setText(f"Error: Effect '{effect_name}' not found")
                return

            # Create enhanced cue
            test_cue = EnhancedCue(
                cue_id="TEST_001",
                cue_number=1,
                time_code="00:00:00.000",
                channel=1,
                duration=1000,
                visual_properties=effect_config
            )

            # Launch the firework
            asyncio.create_task(self.visualization_bridge.launch_firework(test_cue))

            self.test_status_label.setText(f"✓ Launched: {effect_name}")
            self.test_status_label.setStyleSheet("color: green;")

        except Exception as e:
            self.test_status_label.setText(f"Error: {str(e)}")
            self.test_status_label.setStyleSheet("color: red;")

    def update_statistics(self):
        """Update statistics display"""
        try:
            # Update connection status
            if self.visualization_bridge.is_connected():
                self.connection_status_label.setText("UE5 Client: Connected")
                self.connection_status_label.setStyleSheet("color: green; font-weight: bold;")

                # Get client info
                stats = self.show_execution_manager.get_visualization_stats()
                if stats.get('connected_clients'):
                    client = stats['connected_clients'][0]
                    self.client_info_label.setText(
                        f"Client: {client.get('address', 'Unknown')} | "
                        f"Connected: {client.get('connected_at', 'Unknown')}"
                    )
            else:
                self.connection_status_label.setText("UE5 Client: Not Connected")
                self.connection_status_label.setStyleSheet("color: red; font-weight: bold;")
                self.client_info_label.setText("No client information")

            # Update statistics
            stats = self.visualization_bridge.get_statistics()
            stats_text = self.format_statistics(stats)
            self.stats_text.setPlainText(stats_text)

        except Exception as e:
            pass  # Silently ignore update errors

    def format_statistics(self, stats: dict) -> str:
        """Format statistics for display"""
        lines = []
        lines.append("=== Visualization Statistics ===")
        lines.append("")
        lines.append(f"Server Running:     {stats.get('server_running', False)}")
        lines.append(f"Connected Clients:  {stats.get('client_count', 0)}")
        lines.append(f"Messages Sent:      {stats.get('messages_sent', 0)}")
        lines.append(f"Messages Queued:    {stats.get('messages_queued', 0)}")
        lines.append(f"Errors:             {stats.get('errors', 0)}")
        lines.append("")
        lines.append("Message Types:")
        for msg_type, count in stats.get('message_types', {}).items():
            lines.append(f"  {msg_type:20s}: {count}")

        return "\n".join(lines)

    def closeEvent(self, event):
        """Handle dialog close"""
        self.update_timer.stop()
        super().closeEvent(event)