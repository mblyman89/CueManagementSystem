from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QRadioButton,
                               QGroupBox, QFormLayout, QLineEdit,
                               QSpinBox, QDialogButtonBox, QMessageBox,
                               QComboBox)
from PySide6.QtCore import Qt, Signal


class ModeSelector(QDialog):
    """
    Dialog for selecting system operation mode

    Features:
    - Toggle between simulation and hardware modes
    - Configure hardware connection settings for Raspberry Pi
    - Save and apply mode changes
    """

    # Signal emitted when mode is changed and applied
    mode_changed = Signal(str, dict, str)  # mode, connection_settings, communication_method

    def __init__(self, current_mode="simulation", connection_settings=None, communication_method="mqtt", parent=None):
        super().__init__(parent)

        # Initialize default settings
        self.current_mode = current_mode
        self.communication_method = communication_method
        self.connection_settings = connection_settings or {
            "host": "raspberrypi.local",
            "port": 22,
            "username": "pi",
            "password": "",
            "mqtt_port": 1883
        }

        # Set up UI
        self.setWindowTitle("System Mode Selection")
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI components"""
        main_layout = QVBoxLayout(self)

        # Mode selection group
        mode_group = QGroupBox("Operation Mode")
        mode_layout = QVBoxLayout(mode_group)

        # Mode radio buttons
        self.simulation_radio = QRadioButton("Simulation Mode")
        self.hardware_radio = QRadioButton("Hardware Mode (Raspberry Pi)")

        # Add tooltip explanations
        self.simulation_radio.setToolTip("Run in simulation mode without connecting to hardware")
        self.hardware_radio.setToolTip("Connect to Raspberry Pi and execute commands on the hardware")

        # Set checked state based on current mode
        if self.current_mode == "simulation":
            self.simulation_radio.setChecked(True)
        else:
            self.hardware_radio.setChecked(True)

        # Add radio buttons to layout
        mode_layout.addWidget(self.simulation_radio)
        mode_layout.addWidget(self.hardware_radio)

        # Connection settings group
        self.connection_group = QGroupBox("Raspberry Pi Connection Settings")
        connection_layout = QFormLayout(self.connection_group)

        # Create communication method selector
        self.communication_method_label = QLabel("Communication Method:")
        self.communication_method_combo = QComboBox()
        self.communication_method_combo.addItem("MQTT (Recommended)", "mqtt")
        self.communication_method_combo.addItem("SSH", "ssh")

        # Set current communication method
        index = self.communication_method_combo.findData(self.communication_method)
        if index >= 0:
            self.communication_method_combo.setCurrentIndex(index)

        # Connect signal to update UI based on selected method
        self.communication_method_combo.currentIndexChanged.connect(self.update_connection_ui)

        # Add communication method selector to layout
        connection_layout.addRow("Communication Method:", self.communication_method_combo)

        # Create connection fields
        self.host_input = QLineEdit(self.connection_settings.get("host", "raspberrypi.local"))

        # SSH port input
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(self.connection_settings.get("port", 22))

        # MQTT port input
        self.mqtt_port_input = QSpinBox()
        self.mqtt_port_input.setRange(1, 65535)
        self.mqtt_port_input.setValue(self.connection_settings.get("mqtt_port", 1883))

        self.username_input = QLineEdit(self.connection_settings.get("username", "pi"))
        self.password_input = QLineEdit(self.connection_settings.get("password", ""))
        self.password_input.setEchoMode(QLineEdit.Password)

        # Add fields to form layout
        connection_layout.addRow("Host:", self.host_input)
        self.ssh_port_label = QLabel("SSH Port:")
        connection_layout.addRow(self.ssh_port_label, self.port_input)
        self.mqtt_port_label = QLabel("MQTT Port:")
        connection_layout.addRow(self.mqtt_port_label, self.mqtt_port_input)
        connection_layout.addRow("Username:", self.username_input)
        connection_layout.addRow("Password:", self.password_input)

        # Create connection test button
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self.test_connection)
        connection_layout.addRow("", self.test_button)

        # Standard dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept_changes)
        button_box.rejected.connect(self.reject)

        # Add all components to main layout
        main_layout.addWidget(mode_group)
        main_layout.addWidget(self.connection_group)
        main_layout.addWidget(button_box)

        # Connect signals
        self.simulation_radio.toggled.connect(self.update_connection_ui)
        self.hardware_radio.toggled.connect(self.update_connection_ui)

        # Initial UI state update
        self.update_connection_ui()

    def update_connection_ui(self):
        """Update UI based on selected mode and communication method"""
        is_hardware_mode = self.hardware_radio.isChecked()

        # Store reference to connection_group when created
        if hasattr(self, 'connection_group'):
            self.connection_group.setEnabled(is_hardware_mode)

        # Update port visibility based on communication method
        if hasattr(self, 'communication_method_combo') and hasattr(self, 'ssh_port_label') and hasattr(self, 'mqtt_port_label'):
            current_method = self.communication_method_combo.currentData()

            # Show/hide appropriate port inputs
            is_ssh = current_method == "ssh"
            self.ssh_port_label.setVisible(is_ssh)
            self.port_input.setVisible(is_ssh)

            is_mqtt = current_method == "mqtt"
            self.mqtt_port_label.setVisible(is_mqtt)
            self.mqtt_port_input.setVisible(is_mqtt)

    def test_connection(self):
        """Test the SSH connection to Raspberry Pi"""
        # Placeholder for future SSH connection test
        # For now, just show a message that this will be implemented later
        QMessageBox.information(
            self,
            "Connection Test",
            "SSH connection testing will be implemented in a future update.\n\n"
            "Currently in development mode."
        )

    def accept_changes(self):
        """Accept and apply the mode changes"""
        # Determine selected mode
        selected_mode = "hardware" if self.hardware_radio.isChecked() else "simulation"

        # Get selected communication method
        selected_method = self.communication_method_combo.currentData()

        # Gather connection settings
        connection_settings = {
            "host": self.host_input.text(),
            "username": self.username_input.text(),
            "password": self.password_input.text()
        }

        # Add appropriate port based on communication method
        if selected_method == "ssh":
            connection_settings["port"] = self.port_input.value()
        else:  # MQTT
            connection_settings["mqtt_port"] = self.mqtt_port_input.value()
            # Still include SSH port for backward compatibility
            connection_settings["port"] = self.port_input.value()

        # Emit signal with new mode, settings, and communication method
        self.mode_changed.emit(selected_mode, connection_settings, selected_method)

        # Close dialog
        self.accept()
