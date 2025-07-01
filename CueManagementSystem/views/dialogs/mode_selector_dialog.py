from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QRadioButton,
                               QGroupBox, QFormLayout, QLineEdit,
                               QSpinBox, QDialogButtonBox, QMessageBox,
                               QComboBox, QTabWidget, QCheckBox,
                               QFileDialog, QTextEdit, QProgressBar,
                               QScrollArea, QWidget, QSizePolicy,
                               QProgressDialog)
from PySide6.QtCore import Qt, Signal, QTimer
import json
import os


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
    professional_mqtt_config_changed = Signal(dict)  # professional_mqtt_config

    def __init__(self, current_mode="simulation", connection_settings=None, communication_method="mqtt", parent=None):
        super().__init__(parent)

        # Store parent reference for MQTT access
        self.main_window = parent

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

        # Professional MQTT configuration
        self.professional_mqtt_config = {
            'broker_host': 'localhost',
            'broker_port': 1883,
            'username': '',
            'password': '',
            'use_ssl': False,
            'ssl_cert_path': '',
            'ssl_key_path': '',
            'ssl_ca_path': '',
            'client_id': 'firework_controller',
            'keepalive': 60,
            'qos_level': 2,
            'topics': {
                'command': 'firework/command',
                'status': 'firework/status',
                'emergency': 'firework/emergency',
                'heartbeat': 'firework/heartbeat'
            }
        }

        self.use_professional_mqtt = False

        # Connection status tracking
        self.ssh_connected = False
        self.mqtt_connected = False

        # Set up UI
        self.setWindowTitle("System Mode Selection")
        self.setMinimumWidth(1000)
        self.setMinimumHeight(900)
        self.resize(1100, 950)
        self.setup_ui()

        # Connect to MQTT messages if parent has MQTT integration
        self.connect_mqtt_messages()

    def setup_ui(self):
        """Set up the dialog UI components"""
        main_layout = QVBoxLayout(self)

        # Mode selection group - centered
        mode_group = QGroupBox("Operation Mode")
        mode_layout = QHBoxLayout(mode_group)

        # Add stretch before buttons
        mode_layout.addStretch()

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

        # Add radio buttons to centered layout
        mode_layout.addWidget(self.simulation_radio)
        mode_layout.addWidget(self.hardware_radio)

        # Add stretch after buttons
        mode_layout.addStretch()

        # Create tabbed interface for settings
        self.tab_widget = QTabWidget()

        # Basic Connection Tab
        self.basic_tab = self.create_basic_connection_tab()
        self.tab_widget.addTab(self.basic_tab, "Basic Connection")

        # Professional MQTT Tab
        self.professional_tab = self.create_professional_mqtt_tab()
        self.tab_widget.addTab(self.professional_tab, "Professional MQTT")

        # GPIO Pin Assignments Tab
        self.gpio_tab = self.create_gpio_assignments_tab()
        self.tab_widget.addTab(self.gpio_tab, "GPIO Pins")

        # GPIO Status Monitoring Tab
        self.gpio_status_tab = self.create_gpio_status_tab()
        self.tab_widget.addTab(self.gpio_status_tab, "GPIO Status")

        # Standard dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Close)
        button_box.button(QDialogButtonBox.Apply).setText("Apply Settings")
        button_box.button(QDialogButtonBox.Close).setText("Close Dialog")
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.accept_changes)
        button_box.button(QDialogButtonBox.Close).clicked.connect(self.reject)

        # Pi control buttons - moved from basic tab to main dialog
        pi_controls_group = QGroupBox("Pi Control")
        pi_controls_layout = QHBoxLayout(pi_controls_group)
        pi_controls_layout.addStretch()

        # Create the buttons (moved from basic tab)
        self.shutdown_button = QPushButton("Shut Down Pi")
        self.shutdown_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """)
        self.shutdown_button.clicked.connect(self.shutdown_pi)

        self.wifi_button = QPushButton("WiFi Mode")
        self.wifi_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """)
        self.wifi_button.clicked.connect(self.set_wifi_mode)

        self.adhoc_button = QPushButton("Adhoc Mode")
        self.adhoc_button.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """)
        self.adhoc_button.clicked.connect(self.set_adhoc_mode)

        pi_controls_layout.addWidget(self.shutdown_button)
        pi_controls_layout.addWidget(self.wifi_button)
        pi_controls_layout.addWidget(self.adhoc_button)
        pi_controls_layout.addStretch()

        # Add all components to main layout
        main_layout.addWidget(mode_group)
        main_layout.addWidget(self.tab_widget)
        main_layout.addWidget(pi_controls_group)
        main_layout.addWidget(button_box)

        # Connect signals
        self.simulation_radio.toggled.connect(self.update_connection_ui)
        self.hardware_radio.toggled.connect(self.update_connection_ui)

        # Initial UI state update
        self.update_connection_ui()

    def create_basic_connection_tab(self):
        """Create the basic connection settings tab"""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)

        # Connection status indicators (compact)
        requirements_group = QGroupBox("Connection Status")
        requirements_layout = QVBoxLayout(requirements_group)

        # Connection status indicators
        status_layout = QHBoxLayout()
        status_layout.addStretch()

        self.ssh_status_label = QLabel("SSH: ❌ Not Connected")
        self.mqtt_status_label = QLabel("MQTT: ❌ Not Connected")

        self.ssh_status_label.setStyleSheet(
            "padding: 8px; border: 2px solid #a93226; border-radius: 5px; background-color: #a93226; color: white; font-weight: bold;")
        self.mqtt_status_label.setStyleSheet(
            "padding: 8px; border: 2px solid #a93226; border-radius: 5px; background-color: #a93226; color: white; font-weight: bold;")

        status_layout.addWidget(self.ssh_status_label)
        status_layout.addWidget(self.mqtt_status_label)
        status_layout.addStretch()

        requirements_layout.addLayout(status_layout)
        main_layout.addWidget(requirements_group)

        # Connection settings - centered
        connection_group = QGroupBox("Connection Settings")
        connection_layout = QVBoxLayout(connection_group)

        # Create form layout for connection fields
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)

        # Create connection fields
        self.host_input = QLineEdit(self.connection_settings.get("host", "raspberrypi.local"))
        self.username_input = QLineEdit(self.connection_settings.get("username", "pi"))
        self.password_input = QLineEdit(self.connection_settings.get("password", ""))
        self.password_input.setEchoMode(QLineEdit.Password)

        # SSH port input
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(self.connection_settings.get("port", 22))

        # MQTT port input
        self.mqtt_port_input = QSpinBox()
        self.mqtt_port_input.setRange(1, 65535)
        self.mqtt_port_input.setValue(self.connection_settings.get("mqtt_port", 1883))

        # Add fields to form layout
        form_layout.addRow("Host:", self.host_input)
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", self.password_input)
        form_layout.addRow("SSH Port:", self.port_input)
        form_layout.addRow("MQTT Port:", self.mqtt_port_input)

        # Center the form
        center_layout = QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(form_widget)
        center_layout.addStretch()

        connection_layout.addLayout(center_layout)

        # Test connection buttons - centered
        test_layout = QHBoxLayout()
        test_layout.addStretch()

        self.test_ssh_button = QPushButton("Test SSH Connection")
        self.test_mqtt_button = QPushButton("Test MQTT Connection")
        self.test_both_button = QPushButton("Test Both Connections")

        self.test_ssh_button.clicked.connect(self.test_ssh_connection)
        self.test_mqtt_button.clicked.connect(self.test_mqtt_connection)
        self.test_both_button.clicked.connect(self.test_both_connections)

        test_layout.addWidget(self.test_ssh_button)
        test_layout.addWidget(self.test_mqtt_button)
        test_layout.addWidget(self.test_both_button)
        test_layout.addStretch()

        connection_layout.addLayout(test_layout)
        main_layout.addWidget(connection_group)

        # Terminal window - full width
        terminal_group = QGroupBox("Terminal")
        terminal_layout = QVBoxLayout(terminal_group)

        # Terminal output area
        self.terminal_output = QTextEdit()
        self.terminal_output.setMinimumHeight(400)
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.terminal_output.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.terminal_output.setLineWrapMode(QTextEdit.WidgetWidth)

        self.terminal_output.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Courier New', monospace;
                font-size: 11pt;
                border: 2px solid #555555;
                border-radius: 5px;
                padding: 8px;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #777777;
            }
        """)
        self.terminal_output.setPlaceholderText("Terminal ready - type commands below and press Enter...")

        # Command input area
        self.command_input = QLineEdit()
        self.command_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                font-family: 'Courier New', monospace;
                font-size: 10pt;
                border: 1px solid #555555;
                padding: 5px;
            }
        """)
        self.command_input.setPlaceholderText("Enter command here and press Enter...")
        self.command_input.returnPressed.connect(self.execute_terminal_command)

        terminal_layout.addWidget(self.terminal_output)
        terminal_layout.addWidget(self.command_input)
        main_layout.addWidget(terminal_group)

        return tab

    def create_professional_mqtt_tab(self):
        """Create the professional MQTT settings tab with scroll area"""
        # Create main tab widget
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(5, 5, 5, 5)

        # Enable Professional MQTT checkbox at the top
        self.enable_professional_mqtt = QCheckBox("Enable Professional MQTT Mode")
        self.enable_professional_mqtt.setChecked(self.use_professional_mqtt)
        self.enable_professional_mqtt.toggled.connect(self.toggle_professional_mqtt)
        self.enable_professional_mqtt.setStyleSheet("font-weight: bold; margin: 5px;")
        tab_layout.addWidget(self.enable_professional_mqtt)

        # Create scroll area for the content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Create scrollable content widget
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        scroll_layout.setContentsMargins(10, 10, 10, 10)

        # Create sections in a more organized way
        self.create_broker_settings_section(scroll_layout)
        self.create_ssl_settings_section(scroll_layout)
        self.create_topics_settings_section(scroll_layout)
        self.create_testing_section(scroll_layout)
        self.create_config_management_section(scroll_layout)

        # Set the scroll content
        scroll_area.setWidget(scroll_content)
        tab_layout.addWidget(scroll_area)

        # Initial state
        self.toggle_professional_mqtt()
        self.toggle_ssl_settings()

        return tab

    def create_gpio_assignments_tab(self):
        """Create the GPIO pin assignments reference tab"""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Title and description
        title_label = QLabel("🔌 GPIO Pin Assignments Reference")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                text-align: center;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        description_label = QLabel(
            "Complete GPIO pin assignments for your Raspberry Pi Zero W2 firework control system")
        description_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #7f8c8d;
                padding: 5px;
                text-align: center;
            }
        """)
        description_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(description_label)

        # Create scrollable area for GPIO pins
        gpio_scroll = QScrollArea()
        gpio_scroll.setWidgetResizable(True)

        gpio_content = QWidget()
        gpio_content_layout = QVBoxLayout(gpio_content)

        # Create organized GPIO reference with color coding
        gpio_html = """
        <div style='background-color: #2c3e50; color: white; padding: 20px; font-family: Consolas, Monaco, monospace; font-size: 13px; line-height: 1.6;'>

            <table style='width: 100%; border-collapse: collapse; margin-bottom: 20px;'>
                <tr style='background-color: #3498db; color: white;'>
                    <th colspan='6' style='padding: 12px; text-align: center; font-size: 16px; font-weight: bold;'>
                        🔧 SHIFT REGISTER CONTROL PINS (15 pins)
                    </th>
                </tr>
                <tr style='background-color: #e74c3c; color: white;'>
                    <th style='padding: 8px; text-align: center; width: 16.66%;'>Chain 1</th>
                    <th style='padding: 8px; text-align: center; width: 16.66%;'>Chain 2</th>
                    <th style='padding: 8px; text-align: center; width: 16.66%;'>Chain 3</th>
                    <th style='padding: 8px; text-align: center; width: 16.66%;'>Chain 4</th>
                    <th style='padding: 8px; text-align: center; width: 16.66%;'>Chain 5</th>
                    <th style='padding: 8px; text-align: center; width: 16.66%;'>Function</th>
                </tr>
                <tr style='background-color: #27ae60; color: white;'>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 2</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 3</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 4</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 14</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 15</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>DATA</td>
                </tr>
                <tr style='background-color: #f39c12; color: white;'>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 17</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 18</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 22</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 23</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 27</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>SCLK</td>
                </tr>
                <tr style='background-color: #9b59b6; color: white;'>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 9</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 10</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 11</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 24</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 25</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>RCLK</td>
                </tr>
            </table>

            <table style='width: 100%; border-collapse: collapse; margin-bottom: 20px;'>
                <tr style='background-color: #e67e22; color: white;'>
                    <th colspan='6' style='padding: 12px; text-align: center; font-size: 16px; font-weight: bold;'>
                        ⚡ OUTPUT CONTROL PINS (10 pins)
                    </th>
                </tr>
                <tr style='background-color: #c0392b; color: white;'>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 5</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 6</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 7</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 8</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 12</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>OE (Output Enable)</td>
                </tr>
                <tr style='background-color: #8e44ad; color: white;'>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 13</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 16</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 19</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 20</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 26</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>SRCLR (Serial Clear)</td>
                </tr>
            </table>

            <table style='width: 100%; border-collapse: collapse; margin-bottom: 20px;'>
                <tr style='background-color: #d35400; color: white;'>
                    <th colspan='2' style='padding: 12px; text-align: center; font-size: 16px; font-weight: bold;'>
                        🎯 SYSTEM CONTROL PIN (1 pin)
                    </th>
                </tr>
                <tr style='background-color: #2c3e50; color: white;'>
                    <td style='padding: 12px; text-align: center; font-weight: bold; font-size: 16px;'>GPIO 21</td>
                    <td style='padding: 12px; text-align: center; font-weight: bold; font-size: 16px;'>ARM/DISARM</td>
                </tr>
            </table>

            <div style='background-color: #34495e; padding: 15px; border-radius: 8px; margin-top: 15px;'>
                <div style='color: #ecf0f1; font-weight: bold; margin-bottom: 12px; font-size: 15px;'>📊 PIN STATE LOGIC:</div>
                <div style='color: #e74c3c; font-weight: bold; font-size: 14px; margin-bottom: 6px;'>• OE Pins: HIGH = Disabled, LOW = Enabled</div>
                <div style='color: #9b59b6; font-weight: bold; font-size: 14px; margin-bottom: 6px;'>• SRCLR Pins: LOW = Disabled, HIGH = Enabled</div>
                <div style='color: #f39c12; font-weight: bold; font-size: 14px; margin-bottom: 10px;'>• ARM Pin: LOW = Disarmed, HIGH = Armed</div>
                <div style='color: #27ae60; font-weight: bold; font-size: 15px;'>📈 SYSTEM: 5 chains × 25 registers × 8 outputs = 1000 total outputs</div>
            </div>

            <div style='background-color: #1a252f; padding: 15px; border-radius: 8px; margin-top: 15px; border: 2px solid #3498db;'>
                <div style='color: #3498db; font-weight: bold; margin-bottom: 10px; font-size: 15px;'>💡 WIRING TIPS:</div>
                <div style='color: #ecf0f1; font-size: 13px; line-height: 1.5;'>
                    • Use different colored wires for each function (DATA, SCLK, RCLK, OE, SRCLR)<br>
                    • Label each wire at both ends with GPIO number and chain number<br>
                    • Test continuity before powering up the system<br>
                    • Keep power and signal wires separated to reduce noise<br>
                    • Use proper gauge wire for power connections (12-14 AWG recommended)
                </div>
            </div>
        </div>
        """

        gpio_text = QLabel(gpio_html)
        gpio_text.setWordWrap(True)
        gpio_text.setTextFormat(Qt.RichText)

        gpio_content_layout.addWidget(gpio_text)
        gpio_scroll.setWidget(gpio_content)
        main_layout.addWidget(gpio_scroll)

        return tab

    def create_gpio_status_tab(self):
        """Create the GPIO status monitoring tab"""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title_label = QLabel("Real-Time GPIO Pin Status")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # Status indicator
        self.gpio_connection_status = QLabel("Not Connected")
        self.gpio_connection_status.setStyleSheet("color: red; font-weight: bold;")
        main_layout.addWidget(self.gpio_connection_status)

        # Refresh button
        refresh_layout = QHBoxLayout()
        self.refresh_gpio_button = QPushButton("Refresh GPIO Status")
        self.refresh_gpio_button.clicked.connect(self.request_gpio_status)
        self.refresh_gpio_button.setEnabled(False)
        refresh_layout.addWidget(self.refresh_gpio_button)
        refresh_layout.addStretch()
        main_layout.addLayout(refresh_layout)

        # Auto-refresh checkbox
        self.auto_refresh_gpio = QCheckBox("Auto-refresh every 2 seconds")
        self.auto_refresh_gpio.setChecked(True)
        self.auto_refresh_gpio.toggled.connect(self.toggle_gpio_auto_refresh)
        main_layout.addWidget(self.auto_refresh_gpio)

        # Scroll area for GPIO status
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(400)

        # GPIO status content widget
        self.gpio_status_content = QWidget()
        self.gpio_status_layout = QVBoxLayout(self.gpio_status_content)

        # Initialize with placeholder
        placeholder_label = QLabel("Connect to Pi and click 'Refresh GPIO Status' to view pin states")
        placeholder_label.setStyleSheet("color: gray; font-style: italic; padding: 20px;")
        placeholder_label.setAlignment(Qt.AlignCenter)
        self.gpio_status_layout.addWidget(placeholder_label)

        scroll_area.setWidget(self.gpio_status_content)
        main_layout.addWidget(scroll_area)

        # GPIO auto-refresh timer
        self.gpio_refresh_timer = QTimer()
        self.gpio_refresh_timer.timeout.connect(self.request_gpio_status)
        self.gpio_refresh_timer.setInterval(2000)  # 2 seconds

        return tab

    def create_broker_settings_section(self, parent_layout):
        """Create broker and connection settings section"""
        self.professional_settings_group = QGroupBox("Broker & Connection Settings")
        settings_layout = QFormLayout(self.professional_settings_group)
        settings_layout.setSpacing(8)

        # Broker settings
        self.prof_broker_host = QLineEdit(self.professional_mqtt_config['broker_host'])
        self.prof_broker_port = QSpinBox()
        self.prof_broker_port.setRange(1, 65535)
        self.prof_broker_port.setValue(self.professional_mqtt_config['broker_port'])

        settings_layout.addRow("Broker Host:", self.prof_broker_host)
        settings_layout.addRow("Broker Port:", self.prof_broker_port)

        # Authentication
        self.prof_username = QLineEdit(self.professional_mqtt_config['username'])
        self.prof_password = QLineEdit(self.professional_mqtt_config['password'])
        self.prof_password.setEchoMode(QLineEdit.Password)

        settings_layout.addRow("Username:", self.prof_username)
        settings_layout.addRow("Password:", self.prof_password)

        # Client settings
        self.prof_client_id = QLineEdit(self.professional_mqtt_config['client_id'])
        self.prof_keepalive = QSpinBox()
        self.prof_keepalive.setRange(10, 300)
        self.prof_keepalive.setValue(self.professional_mqtt_config['keepalive'])

        settings_layout.addRow("Client ID:", self.prof_client_id)
        settings_layout.addRow("Keepalive (seconds):", self.prof_keepalive)

        # QoS Level
        self.prof_qos = QComboBox()
        self.prof_qos.addItem("QoS 0 - At most once", 0)
        self.prof_qos.addItem("QoS 1 - At least once", 1)
        self.prof_qos.addItem("QoS 2 - Exactly once (Recommended)", 2)
        self.prof_qos.setCurrentIndex(self.professional_mqtt_config['qos_level'])

        settings_layout.addRow("QoS Level:", self.prof_qos)

        parent_layout.addWidget(self.professional_settings_group)

    def create_ssl_settings_section(self, parent_layout):
        """Create SSL/TLS settings section"""
        ssl_group = QGroupBox("SSL/TLS Security")
        ssl_layout = QVBoxLayout(ssl_group)
        ssl_layout.setSpacing(8)

        # SSL Enable checkbox
        self.prof_use_ssl = QCheckBox("Enable SSL/TLS Encryption")
        self.prof_use_ssl.setChecked(self.professional_mqtt_config['use_ssl'])
        self.prof_use_ssl.toggled.connect(self.toggle_ssl_settings)
        self.prof_use_ssl.setStyleSheet("font-weight: bold;")
        ssl_layout.addWidget(self.prof_use_ssl)

        # SSL Certificate settings in a form
        ssl_form_layout = QFormLayout()
        ssl_form_layout.setSpacing(5)

        # SSL Certificate paths
        self.prof_ssl_cert = QLineEdit(self.professional_mqtt_config['ssl_cert_path'])
        self.prof_ssl_key = QLineEdit(self.professional_mqtt_config['ssl_key_path'])
        self.prof_ssl_ca = QLineEdit(self.professional_mqtt_config['ssl_ca_path'])

        # SSL file selection buttons
        cert_button = QPushButton("Browse...")
        cert_button.setMaximumWidth(80)
        cert_button.clicked.connect(lambda: self.browse_ssl_file(self.prof_ssl_cert, "Certificate"))

        key_button = QPushButton("Browse...")
        key_button.setMaximumWidth(80)
        key_button.clicked.connect(lambda: self.browse_ssl_file(self.prof_ssl_key, "Private Key"))

        ca_button = QPushButton("Browse...")
        ca_button.setMaximumWidth(80)
        ca_button.clicked.connect(lambda: self.browse_ssl_file(self.prof_ssl_ca, "CA Certificate"))

        # Create horizontal layouts for certificate fields
        cert_layout = QHBoxLayout()
        cert_layout.addWidget(self.prof_ssl_cert)
        cert_layout.addWidget(cert_button)

        key_layout = QHBoxLayout()
        key_layout.addWidget(self.prof_ssl_key)
        key_layout.addWidget(key_button)

        ca_layout = QHBoxLayout()
        ca_layout.addWidget(self.prof_ssl_ca)
        ca_layout.addWidget(ca_button)

        ssl_form_layout.addRow("Client Certificate:", cert_layout)
        ssl_form_layout.addRow("Private Key:", key_layout)
        ssl_form_layout.addRow("CA Certificate:", ca_layout)

        ssl_layout.addLayout(ssl_form_layout)

        # Store SSL widgets for enabling/disabling
        self.ssl_widgets = [self.prof_ssl_cert, self.prof_ssl_key, self.prof_ssl_ca,
                            cert_button, key_button, ca_button]

        parent_layout.addWidget(ssl_group)

    def create_topics_settings_section(self, parent_layout):
        """Create MQTT topics settings section"""
        topics_group = QGroupBox("MQTT Topics Configuration")
        topics_layout = QFormLayout(topics_group)
        topics_layout.setSpacing(5)

        self.prof_topic_command = QLineEdit(self.professional_mqtt_config['topics']['command'])
        self.prof_topic_status = QLineEdit(self.professional_mqtt_config['topics']['status'])
        self.prof_topic_emergency = QLineEdit(self.professional_mqtt_config['topics']['emergency'])
        self.prof_topic_heartbeat = QLineEdit(self.professional_mqtt_config['topics']['heartbeat'])

        topics_layout.addRow("Command Topic:", self.prof_topic_command)
        topics_layout.addRow("Status Topic:", self.prof_topic_status)
        topics_layout.addRow("Emergency Topic:", self.prof_topic_emergency)
        topics_layout.addRow("Heartbeat Topic:", self.prof_topic_heartbeat)

        parent_layout.addWidget(topics_group)

    def create_testing_section(self, parent_layout):
        """Create connection testing section"""
        test_group = QGroupBox("Connection Testing & Diagnostics")
        test_layout = QVBoxLayout(test_group)
        test_layout.setSpacing(8)

        self.prof_test_button = QPushButton("Test Professional MQTT Connection")
        self.prof_test_button.setMinimumHeight(35)
        self.prof_test_button.clicked.connect(self.test_professional_mqtt)

        self.prof_test_progress = QProgressBar()
        self.prof_test_progress.setVisible(False)

        self.prof_test_result = QTextEdit()
        self.prof_test_result.setMaximumHeight(80)
        self.prof_test_result.setReadOnly(True)
        self.prof_test_result.setPlaceholderText("Connection test results will appear here...")

        test_layout.addWidget(self.prof_test_button)
        test_layout.addWidget(self.prof_test_progress)
        test_layout.addWidget(self.prof_test_result)

        parent_layout.addWidget(test_group)

    def create_config_management_section(self, parent_layout):
        """Create configuration management section"""
        config_group = QGroupBox("Configuration Management")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(10)

        # Configuration save/load buttons - centered
        config_buttons_layout = QHBoxLayout()
        config_buttons_layout.addStretch()

        save_config_button = QPushButton("Save Configuration")
        save_config_button.setMinimumHeight(35)
        save_config_button.clicked.connect(self.save_professional_config)

        load_config_button = QPushButton("Load Configuration")
        load_config_button.setMinimumHeight(35)
        load_config_button.clicked.connect(self.load_professional_config)

        config_buttons_layout.addWidget(save_config_button)
        config_buttons_layout.addWidget(load_config_button)
        config_buttons_layout.addStretch()

        config_layout.addLayout(config_buttons_layout)
        parent_layout.addWidget(config_group)

    def update_connection_ui(self):
        """Update UI based on selected mode"""
        is_hardware_mode = self.hardware_radio.isChecked()

        # Enable/disable tabs based on hardware mode
        if hasattr(self, 'tab_widget'):
            self.tab_widget.setEnabled(is_hardware_mode)

    def toggle_professional_mqtt(self):
        """Toggle professional MQTT settings visibility"""
        enabled = self.enable_professional_mqtt.isChecked()
        self.use_professional_mqtt = enabled
        if hasattr(self, 'professional_settings_group'):
            self.professional_settings_group.setEnabled(enabled)

    def toggle_ssl_settings(self):
        """Toggle SSL settings visibility"""
        enabled = self.prof_use_ssl.isChecked()
        if hasattr(self, 'ssl_widgets'):
            for widget in self.ssl_widgets:
                widget.setEnabled(enabled)

    def browse_ssl_file(self, line_edit, file_type):
        """Browse for SSL certificate files"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select {file_type} File",
            "",
            "Certificate Files (*.pem *.crt *.key);;All Files (*)"
        )
        if file_path:
            line_edit.setText(file_path)

    def update_connection_status(self, ssh_status, mqtt_status):
        """Update connection status indicators"""
        self.ssh_connected = ssh_status
        self.mqtt_connected = mqtt_status

        # Enable/disable GPIO status functionality
        if hasattr(self, 'refresh_gpio_button'):
            self.refresh_gpio_button.setEnabled(mqtt_status)

        # Start/stop auto-refresh based on connection
        if hasattr(self, 'auto_refresh_gpio') and hasattr(self, 'gpio_refresh_timer'):
            if mqtt_status and self.auto_refresh_gpio.isChecked():
                self.gpio_refresh_timer.start()
            else:
                self.gpio_refresh_timer.stop()

        # Update SSH status
        if ssh_status:
            self.ssh_status_label.setText("SSH: ✅ Connected")
            self.ssh_status_label.setStyleSheet(
                "padding: 8px; border: 2px solid #1e8449; border-radius: 5px; background-color: #1e8449; color: white; font-weight: bold;")
        else:
            self.ssh_status_label.setText("SSH: ❌ Not Connected")
            self.ssh_status_label.setStyleSheet(
                "padding: 8px; border: 2px solid #a93226; border-radius: 5px; background-color: #a93226; color: white; font-weight: bold;")

        # Update MQTT status
        if mqtt_status:
            self.mqtt_status_label.setText("MQTT: ✅ Connected")
            self.mqtt_status_label.setStyleSheet(
                "padding: 8px; border: 2px solid #1e8449; border-radius: 5px; background-color: #1e8449; color: white; font-weight: bold;")
        else:
            self.mqtt_status_label.setText("MQTT: ❌ Not Connected")
            self.mqtt_status_label.setStyleSheet(
                "padding: 8px; border: 2px solid #a93226; border-radius: 5px; background-color: #a93226; color: white; font-weight: bold;")

    def test_ssh_connection(self):
        """Test SSH connection to Raspberry Pi"""
        self.test_ssh_connection_simple(self.get_connection_settings())

    def test_ssh_connection_simple(self, connection_settings):
        """Simple SSH connection test using basic socket connectivity"""
        # Disable the test button during testing
        self.test_ssh_button.setEnabled(False)
        self.test_ssh_button.setText("Testing SSH...")

        try:
            import socket
            import paramiko

            # First test basic connectivity
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)

            result = sock.connect_ex((connection_settings["host"], connection_settings["port"]))
            sock.close()

            if result != 0:
                self.handle_ssh_test_result(False, f"Cannot reach SSH port {connection_settings['port']}")
                return

            # Try SSH authentication using paramiko (simpler than asyncssh)
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                ssh.connect(
                    hostname=connection_settings["host"],
                    port=connection_settings["port"],
                    username=connection_settings["username"],
                    password=connection_settings["password"],
                    timeout=10
                )

                # Test a simple command
                stdin, stdout, stderr = ssh.exec_command("echo 'SSH test successful'")
                output = stdout.read().decode().strip()
                error = stderr.read().decode().strip()

                ssh.close()

                if output == "SSH test successful":
                    self.handle_ssh_test_result(True, "SSH connection and authentication successful!")
                else:
                    self.handle_ssh_test_result(False, f"SSH command failed: {error}")

            except paramiko.AuthenticationException:
                self.handle_ssh_test_result(False, "SSH authentication failed - check username and password")
            except paramiko.SSHException as e:
                self.handle_ssh_test_result(False, f"SSH connection failed: {str(e)}")
            except Exception as e:
                self.handle_ssh_test_result(False, f"SSH error: {str(e)}")

        except ImportError:
            # Fallback to basic connectivity test if paramiko not available
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)

                result = sock.connect_ex((connection_settings["host"], connection_settings["port"]))
                sock.close()

                if result == 0:
                    self.handle_ssh_test_result(True, "SSH port is reachable (install paramiko for full SSH test)")
                else:
                    self.handle_ssh_test_result(False, f"Cannot reach SSH port {connection_settings['port']}")

            except Exception as e:
                self.handle_ssh_test_result(False, f"Connection test failed: {str(e)}")

        except Exception as e:
            self.handle_ssh_test_result(False, f"Connection test error: {str(e)}")

    def get_connection_settings(self):
        """Get current connection settings from UI"""
        return {
            "host": self.host_input.text(),
            "port": self.port_input.value(),
            "username": self.username_input.text(),
            "password": self.password_input.text(),
            "mqtt_port": self.mqtt_port_input.value()
        }

    def test_mqtt_connection(self):
        """Test MQTT connection to Raspberry Pi"""
        connection_settings = self.get_connection_settings()
        self.test_mqtt_connection_simple(connection_settings)

    def test_mqtt_connection_simple(self, connection_settings):
        """Test MQTT connection with enhanced error handling"""
        self.test_mqtt_button.setEnabled(False)
        self.test_mqtt_button.setText("Testing MQTT...")

        try:
            import socket

            # Test if we can reach the host on the MQTT port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)

            result = sock.connect_ex((connection_settings["host"], connection_settings["mqtt_port"]))
            sock.close()

            if result == 0:
                self.handle_mqtt_test_result(True, "MQTT port is reachable!")
            else:
                self.handle_mqtt_test_result(False, f"Cannot reach MQTT port {connection_settings['mqtt_port']}")

        except socket.gaierror as e:
            self.handle_mqtt_test_result(False, f"DNS resolution failed for {connection_settings['host']}: {str(e)}")
        except socket.timeout:
            self.handle_mqtt_test_result(False,
                                         f"Connection timeout to {connection_settings['host']}:{connection_settings['mqtt_port']}")
        except Exception as e:
            self.handle_mqtt_test_result(False, f"MQTT connection test failed: {str(e)}")

    def test_both_connections(self):
        """Test both SSH and MQTT connections with progress dialog"""
        # Create a progress dialog
        self.progress_dialog = QProgressDialog("Testing connections...", "Cancel", 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.show()

        self.test_both_button.setEnabled(False)
        self.test_both_button.setText("Testing Both...")

        # Test SSH first, then MQTT
        self.test_ssh_connection()
        QTimer.singleShot(1000, self.test_mqtt_connection)  # Delay MQTT test slightly

        # Close progress dialog and re-enable button after both tests
        QTimer.singleShot(3000, self.finish_both_connection_tests)

    def finish_both_connection_tests(self):
        """Finish both connection tests and update UI"""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()

        self.test_both_button.setEnabled(True)
        self.test_both_button.setText("Test Both Connections")

        # Show summary of both connection results
        ssh_status = "✅ Connected" if self.ssh_connected else "❌ Failed"
        mqtt_status = "✅ Connected" if self.mqtt_connected else "❌ Failed"

        QMessageBox.information(
            self,
            "Connection Test Results",
            f"Connection Test Summary:\n\n"
            f"SSH: {ssh_status}\n"
            f"MQTT: {mqtt_status}\n\n"
            f"Hardware Mode: {'✅ Available' if (self.ssh_connected and self.mqtt_connected) else '❌ Requires both connections'}"
        )

    def handle_ssh_test_result(self, success, message):
        """Handle SSH connection test result"""
        self.test_ssh_button.setEnabled(True)
        self.test_ssh_button.setText("Test SSH Connection")

        self.update_connection_status(success, self.mqtt_connected)

        if success:
            self.append_to_terminal(f"✅ SSH: {message}")
        else:
            self.append_to_terminal(f"❌ SSH: {message}")

    def handle_mqtt_test_result(self, success, message):
        """Handle MQTT connection test result"""
        self.test_mqtt_button.setEnabled(True)
        self.test_mqtt_button.setText("Test MQTT Connection")

        self.update_connection_status(self.ssh_connected, success)

        if success:
            self.append_to_terminal(f"✅ MQTT: {message}")
        else:
            self.append_to_terminal(f"❌ MQTT: {message}")

    def test_professional_mqtt(self):
        """Test professional MQTT connection"""
        self.prof_test_progress.setVisible(True)
        self.prof_test_progress.setRange(0, 0)
        self.prof_test_button.setEnabled(False)
        self.prof_test_result.clear()

        config = self.get_professional_mqtt_config()
        QTimer.singleShot(2000, lambda: self.finish_professional_mqtt_test(config))

    def finish_professional_mqtt_test(self, config):
        """Finish professional MQTT connection test"""
        self.prof_test_progress.setVisible(False)
        self.prof_test_button.setEnabled(True)

        result_text = f"Professional MQTT Connection Test Results:\n"
        result_text += f"Broker: {config['broker_host']}:{config['broker_port']}\n"
        result_text += f"SSL/TLS: {'Enabled' if config['use_ssl'] else 'Disabled'}\n"
        result_text += f"QoS Level: {config['qos_level']}\n"
        result_text += f"Client ID: {config['client_id']}\n"
        result_text += f"Status: Connection test successful (simulated)\n"

        self.prof_test_result.setText(result_text)

    def get_professional_mqtt_config(self):
        """Get current professional MQTT configuration from UI"""
        return {
            'broker_host': self.prof_broker_host.text(),
            'broker_port': self.prof_broker_port.value(),
            'username': self.prof_username.text(),
            'password': self.prof_password.text(),
            'use_ssl': self.prof_use_ssl.isChecked(),
            'ssl_cert_path': self.prof_ssl_cert.text(),
            'ssl_key_path': self.prof_ssl_key.text(),
            'ssl_ca_path': self.prof_ssl_ca.text(),
            'client_id': self.prof_client_id.text(),
            'keepalive': self.prof_keepalive.value(),
            'qos_level': self.prof_qos.currentData(),
            'topics': {
                'command': self.prof_topic_command.text(),
                'status': self.prof_topic_status.text(),
                'emergency': self.prof_topic_emergency.text(),
                'heartbeat': self.prof_topic_heartbeat.text()
            }
        }

    def save_professional_config(self):
        """Save professional MQTT configuration to file"""
        config = self.get_professional_mqtt_config()

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Professional MQTT Configuration",
            "professional_mqtt_config.json",
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(config, f, indent=4)
                QMessageBox.information(
                    self,
                    "Configuration Saved",
                    f"Professional MQTT configuration saved to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Save Error",
                    f"Failed to save configuration:\n{str(e)}"
                )

    def load_professional_config(self):
        """Load professional MQTT configuration from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Professional MQTT Configuration",
            "",
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)

                # Update UI with loaded configuration
                self.prof_broker_host.setText(config.get('broker_host', ''))
                self.prof_broker_port.setValue(config.get('broker_port', 1883))
                self.prof_username.setText(config.get('username', ''))
                self.prof_password.setText(config.get('password', ''))
                self.prof_use_ssl.setChecked(config.get('use_ssl', False))
                self.prof_ssl_cert.setText(config.get('ssl_cert_path', ''))
                self.prof_ssl_key.setText(config.get('ssl_key_path', ''))
                self.prof_ssl_ca.setText(config.get('ssl_ca_path', ''))
                self.prof_client_id.setText(config.get('client_id', 'firework_controller'))
                self.prof_keepalive.setValue(config.get('keepalive', 60))

                qos_index = config.get('qos_level', 2)
                self.prof_qos.setCurrentIndex(qos_index)

                topics = config.get('topics', {})
                self.prof_topic_command.setText(topics.get('command', 'firework/command'))
                self.prof_topic_status.setText(topics.get('status', 'firework/status'))
                self.prof_topic_emergency.setText(topics.get('emergency', 'firework/emergency'))
                self.prof_topic_heartbeat.setText(topics.get('heartbeat', 'firework/heartbeat'))

                self.toggle_ssl_settings()

                QMessageBox.information(
                    self,
                    "Configuration Loaded",
                    f"Professional MQTT configuration loaded from:\n{file_path}"
                )

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Load Error",
                    f"Failed to load configuration:\n{str(e)}"
                )

    def append_to_terminal(self, text):
        """Append text to terminal output with enhanced scrolling"""
        if hasattr(self, 'terminal_output'):
            # Move cursor to end before appending
            cursor = self.terminal_output.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.terminal_output.setTextCursor(cursor)

            # Append the text
            self.terminal_output.append(text)

            # Ensure auto-scroll to bottom
            scrollbar = self.terminal_output.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

            # Also ensure the cursor is visible
            self.terminal_output.ensureCursorVisible()

    def shutdown_pi(self):
        """Safely shutdown the Raspberry Pi"""
        reply = QMessageBox.question(
            self,
            "Confirm Shutdown",
            "Are you sure you want to shut down the Raspberry Pi?\n\n"
            "This will safely power off the Pi and you will need to\n"
            "physically power it back on to use it again.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.append_to_terminal("🔄 Initiating Pi shutdown...")
            self.shutdown_button.setEnabled(False)
            self.shutdown_button.setText("Shutting Down...")
            self.execute_pi_command("sudo shutdown -h now", "shutdown")

    def set_wifi_mode(self):
        """Set Pi to WiFi mode"""
        self.append_to_terminal("📶 WiFi Mode - Feature coming soon...")
        QMessageBox.information(
            self,
            "WiFi Mode",
            "WiFi Mode functionality will be implemented in a future update."
        )

    def set_adhoc_mode(self):
        """Set Pi to Adhoc mode"""
        self.append_to_terminal("📡 Adhoc Mode - Feature coming soon...")
        QMessageBox.information(
            self,
            "Adhoc Mode",
            "Adhoc Mode functionality will be implemented in a future update."
        )

    def execute_pi_command(self, command, operation_name):
        """Execute a command on the Raspberry Pi"""
        try:
            connection_settings = {
                "host": self.host_input.text(),
                "username": self.username_input.text(),
                "password": self.password_input.text(),
                "port": self.port_input.value()
            }
            self.execute_ssh_command(connection_settings, command, operation_name)
        except Exception as e:
            self.append_to_terminal(f"❌ Error executing {operation_name}: {str(e)}")

    def execute_ssh_command(self, connection_settings, command, operation_name):
        """Execute SSH command on Pi"""
        try:
            import paramiko
            import socket

            # For terminal commands, don't show connection messages every time
            if operation_name != "terminal_command":
                self.append_to_terminal(f"🔗 Connecting to {connection_settings['host']}...")

            # Test basic connectivity
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)

            result = sock.connect_ex((connection_settings["host"], connection_settings["port"]))
            sock.close()

            if result != 0:
                self.append_to_terminal(f"❌ Cannot reach SSH port {connection_settings['port']}")
                if operation_name == "shutdown":
                    self.reset_shutdown_button()
                return

            # SSH connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            ssh.connect(
                hostname=connection_settings["host"],
                port=connection_settings["port"],
                username=connection_settings["username"],
                password=connection_settings["password"],
                timeout=10
            )

            # For terminal commands, don't show connection success every time
            if operation_name != "terminal_command":
                self.append_to_terminal(f"✅ Connected via SSH")
                self.append_to_terminal(f"⚡ Executing: {command}")

            # Execute command
            stdin, stdout, stderr = ssh.exec_command(command)

            # Handle different operation types
            if operation_name == "shutdown":
                self.append_to_terminal("✅ Shutdown command sent successfully")
                self.append_to_terminal("🔌 Pi is shutting down...")
                self.append_to_terminal("   You can safely close this dialog")
            elif operation_name == "terminal_command":
                # For terminal commands, show output immediately
                output = stdout.read().decode().strip()
                error = stderr.read().decode().strip()
                exit_status = stdout.channel.recv_exit_status()

                if output:
                    # Split output into lines and display each
                    for line in output.split('\n'):
                        if line.strip():
                            self.append_to_terminal(line)

                if error:
                    # Display errors in red-ish color (we'll use a prefix)
                    for line in error.split('\n'):
                        if line.strip():
                            self.append_to_terminal(f"❌ {line}")

                if exit_status != 0 and not output and not error:
                    self.append_to_terminal(f"❌ Command exited with status {exit_status}")

            else:
                # For other commands, show standard output
                output = stdout.read().decode().strip()
                error = stderr.read().decode().strip()

                if output:
                    self.append_to_terminal(f"📤 Output: {output}")
                if error:
                    self.append_to_terminal(f"⚠️ Error: {error}")

            ssh.close()

        except ImportError:
            self.append_to_terminal("❌ SSH functionality requires paramiko library")
            if operation_name == "shutdown":
                self.reset_shutdown_button()
        except paramiko.AuthenticationException:
            self.append_to_terminal("❌ SSH authentication failed - check username and password")
            if operation_name == "shutdown":
                self.reset_shutdown_button()
        except Exception as e:
            self.append_to_terminal(f"❌ SSH error: {str(e)}")
            if operation_name == "shutdown":
                self.reset_shutdown_button()

    def execute_terminal_command(self):
        """Execute command entered in terminal input"""
        command = self.command_input.text().strip()
        if not command:
            return

        # Display the command in terminal
        self.append_to_terminal(f"pi@raspberrypi:~$ {command}")

        # Clear the input
        self.command_input.clear()

        # Check if we have connection settings
        if not self.host_input.text():
            self.append_to_terminal("❌ Error: No host specified")
            self.append_to_terminal("   Please configure connection settings first")
            return

        # Execute the command directly without triggering connection dialog
        self.execute_terminal_command_direct(command)

    def execute_terminal_command_direct(self, command):
        """Execute terminal command directly without connection popups"""
        try:
            # Get connection settings
            connection_settings = {
                "host": self.host_input.text(),
                "username": self.username_input.text(),
                "password": self.password_input.text(),
                "port": self.port_input.value()
            }

            # Execute SSH command directly
            self.execute_ssh_command_silent(connection_settings, command)

        except Exception as e:
            self.append_to_terminal(f"❌ Error executing command: {str(e)}")

    def execute_ssh_command_silent(self, connection_settings, command):
        """Execute SSH command silently without connection messages"""
        try:
            import paramiko
            import socket

            # Test basic connectivity (silent)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)

            result = sock.connect_ex((connection_settings["host"], connection_settings["port"]))
            sock.close()

            if result != 0:
                self.append_to_terminal(f"❌ Cannot reach SSH port {connection_settings['port']}")
                return

            # SSH connection (silent)
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            ssh.connect(
                hostname=connection_settings["host"],
                port=connection_settings["port"],
                username=connection_settings["username"],
                password=connection_settings["password"],
                timeout=10
            )

            # Execute command
            stdin, stdout, stderr = ssh.exec_command(command)

            # Show output immediately
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            exit_status = stdout.channel.recv_exit_status()

            if output:
                # Split output into lines and display each
                for line in output.split('\n'):
                    if line.strip():
                        self.append_to_terminal(line)

            if error:
                # Display errors
                for line in error.split('\n'):
                    if line.strip():
                        self.append_to_terminal(f"❌ {line}")

            if exit_status != 0 and not output and not error:
                self.append_to_terminal(f"❌ Command exited with status {exit_status}")

            ssh.close()

        except ImportError:
            self.append_to_terminal("❌ SSH functionality requires paramiko library")
        except paramiko.AuthenticationException:
            self.append_to_terminal("❌ SSH authentication failed - check username and password")
        except Exception as e:
            self.append_to_terminal(f"❌ SSH error: {str(e)}")

    def reset_shutdown_button(self):
        """Reset shutdown button to normal state"""
        if hasattr(self, 'shutdown_button'):
            self.shutdown_button.setEnabled(True)
            self.shutdown_button.setText("Shut Down Pi")

    def shutdown_raspberry_pi(self):
        """Handle Raspberry Pi shutdown button click"""
        try:
            # Confirm shutdown with user
            reply = QMessageBox.question(
                self,
                "Confirm Shutdown",
                "Are you sure you want to shutdown the Raspberry Pi?\n\n"
                "This will stop all firework control operations and require "
                "physical access to restart the Pi.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Import system mode to send shutdown command
                try:
                    # This would need to be connected to your main system
                    # For now, show a message that the command would be sent
                    QMessageBox.information(
                        self,
                        "Shutdown Command",
                        "Raspberry Pi shutdown command would be sent via MQTT.\n\n"
                        "In the actual implementation, this will:\n"
                        "1. Send shutdown command via professional MQTT\n"
                        "2. Give the Pi 10 seconds to acknowledge\n"
                        "3. Safely shutdown the Pi system"
                    )

                    # TODO: Connect to actual system mode instance
                    # system_mode.handle_shutdown_pi_button()

                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Shutdown Error",
                        f"Failed to send shutdown command:\n{str(e)}"
                    )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Shutdown Error",
                f"Shutdown operation failed:\n{str(e)}"
            )

    def toggle_wifi_mode(self):
        """Handle WiFi/Adhoc mode toggle button click"""
        try:
            current_text = self.wifi_button.text()

            if current_text == "WiFi Mode":
                # Switch to Adhoc mode
                new_text = "Adhoc Mode"
                new_color = "#cc5500"  # Orange for Adhoc
                mode_message = "Switching to Adhoc (Access Point) mode.\n\n" \
                               "The Pi will create its own WiFi network that you can connect to directly."
            else:
                # Switch to WiFi mode
                new_text = "WiFi Mode"
                new_color = "#1e3d6e"  # Blue for WiFi
                mode_message = "Switching to WiFi (Station) mode.\n\n" \
                               "The Pi will connect to your existing WiFi network."

            # Confirm mode change with user
            reply = QMessageBox.question(
                self,
                "Confirm Mode Change",
                f"{mode_message}\n\nThis may temporarily disconnect the Pi. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Update button appearance
                self.wifi_button.setText(new_text)
                self.wifi_button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {new_color};
                        color: white;
                        font-weight: bold;
                        border: 2px solid #555;
                        border-radius: 5px;
                        padding: 5px;
                    }}
                    QPushButton:hover {{
                        background-color: {new_color}aa;
                    }}
                    QPushButton:pressed {{
                        background-color: {new_color}77;
                    }}
                """)

                # TODO: Connect to actual system mode instance
                # mode_name = system_mode.handle_wifi_mode_button()

                QMessageBox.information(
                    self,
                    "Mode Change",
                    f"WiFi mode change command sent.\n\n"
                    f"The Pi is switching to {new_text.replace(' Mode', '')} mode.\n"
                    f"Please wait for the Pi to reconnect."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Mode Change Error",
                f"Failed to change WiFi mode:\n{str(e)}"
            )

    def accept_changes(self):
        """Accept and apply the mode changes with validation"""
        selected_mode = "hardware" if self.hardware_radio.isChecked() else "simulation"

        # If hardware mode is selected, validate connections
        if selected_mode == "hardware":
            if not (self.ssh_connected and self.mqtt_connected):
                QMessageBox.warning(
                    self,
                    "Connection Required",
                    "Hardware mode requires both SSH and MQTT connections to be successful.\n\n"
                    "Current status:\n"
                    f"SSH: {'✅ Connected' if self.ssh_connected else '❌ Not Connected'}\n"
                    f"MQTT: {'✅ Connected' if self.mqtt_connected else '❌ Not Connected'}\n\n"
                    "Please test and establish both connections before switching to hardware mode.\n"
                    "The system will remain in simulation mode."
                )
                # Force simulation mode
                self.simulation_radio.setChecked(True)
                selected_mode = "simulation"

        # Gather connection settings
        connection_settings = {
            "host": self.host_input.text(),
            "username": self.username_input.text(),
            "password": self.password_input.text(),
            "port": self.port_input.value(),
            "mqtt_port": self.mqtt_port_input.value()
        }

        # Emit signal with new mode and settings
        self.mode_changed.emit(selected_mode, connection_settings, "both")

        # Emit professional MQTT configuration if enabled
        if self.use_professional_mqtt:
            professional_config = self.get_professional_mqtt_config()
            self.professional_mqtt_config_changed.emit(professional_config)

        # Store the current mode
        self.current_mode = selected_mode

        # Show confirmation message instead of closing
        status_msg = "✅ Both SSH and MQTT connected" if (
                self.ssh_connected and self.mqtt_connected) else "⚠️ Connection validation required"
        QMessageBox.information(
            self,
            "Settings Applied",
            f"Mode changed to: {selected_mode.title()}\n"
            f"Communication: Both SSH and MQTT\n\n"
            f"Status: {status_msg}\n\n"
            "Settings have been applied successfully.\n"
            "You can continue using the terminal or close this dialog."
        )

        # Do NOT close the dialog - let user close it manually
        # self.accept()  # Removed this line

    def request_gpio_status(self):
        """Request GPIO status from Pi via MQTT"""
        try:
            if hasattr(self, 'mqtt_client') and self.mqtt_client and self.mqtt_connected:
                # Send GPIO status request
                import json
                import time
                request_data = {
                    'command': 'get_gpio_status',
                    'timestamp': time.time()
                }
                payload = json.dumps(request_data)
                self.mqtt_client.publish('firework/system', payload, qos=1)

                # Update status
                self.gpio_connection_status.setText("Requesting GPIO status...")
                self.gpio_connection_status.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.gpio_connection_status.setText("MQTT not connected")
                self.gpio_connection_status.setStyleSheet("color: red; font-weight: bold;")
        except Exception as e:
            print(f"Error requesting GPIO status: {e}")
            self.gpio_connection_status.setText(f"Error: {e}")
            self.gpio_connection_status.setStyleSheet("color: red; font-weight: bold;")

    def toggle_gpio_auto_refresh(self, enabled):
        """Toggle GPIO auto-refresh timer"""
        if enabled and hasattr(self, 'gpio_refresh_timer'):
            if hasattr(self, 'mqtt_client') and self.mqtt_client and self.mqtt_connected:
                self.gpio_refresh_timer.start()
            else:
                self.auto_refresh_gpio.setChecked(False)
        elif hasattr(self, 'gpio_refresh_timer'):
            self.gpio_refresh_timer.stop()

    def update_gpio_status_display(self, gpio_data):
        """Update the GPIO status display with received data"""
        try:
            # Clear existing content
            for i in reversed(range(self.gpio_status_layout.count())):
                child = self.gpio_status_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)

            if 'error' in gpio_data:
                error_label = QLabel(f"Error reading GPIO: {gpio_data['error']}")
                error_label.setStyleSheet("color: red; font-weight: bold; padding: 10px;")
                self.gpio_status_layout.addWidget(error_label)
                return

            # Update connection status
            self.gpio_connection_status.setText("✅ GPIO Status Updated")
            self.gpio_connection_status.setStyleSheet("color: green; font-weight: bold;")

            # ARM/DISARM Pin Status
            arm_group = QGroupBox("ARM/DISARM Control")
            arm_layout = QVBoxLayout(arm_group)

            arm_pin = gpio_data.get('arm_pin', {})
            arm_state = "🔴 ARMED" if arm_pin.get('state') else "🟢 DISARMED"
            arm_color = "red" if arm_pin.get('state') else "green"

            arm_label = QLabel(f"GPIO {arm_pin.get('pin', 'N/A')}: {arm_state}")
            arm_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {arm_color}; padding: 5px;")
            arm_layout.addWidget(arm_label)

            self.gpio_status_layout.addWidget(arm_group)

            # Chain Status
            for chain_idx in range(5):
                chain_group = QGroupBox(f"Chain {chain_idx} GPIO Pins")
                chain_layout = QVBoxLayout(chain_group)

                # Data pin
                data_pins = gpio_data.get('data_pins', [])
                if chain_idx < len(data_pins):
                    data_pin = data_pins[chain_idx]
                    data_state = "HIGH" if data_pin.get('state') else "LOW"
                    data_color = "#2196F3" if data_pin.get('state') else "#757575"
                    data_label = QLabel(f"Data (GPIO {data_pin.get('pin')}): {data_state}")
                    data_label.setStyleSheet(f"color: {data_color}; padding: 2px;")
                    chain_layout.addWidget(data_label)

                # Serial Clock pin
                sclk_pins = gpio_data.get('sclk_pins', [])
                if chain_idx < len(sclk_pins):
                    sclk_pin = sclk_pins[chain_idx]
                    sclk_state = "HIGH" if sclk_pin.get('state') else "LOW"
                    sclk_color = "#2196F3" if sclk_pin.get('state') else "#757575"
                    sclk_label = QLabel(f"Serial Clock (GPIO {sclk_pin.get('pin')}): {sclk_state}")
                    sclk_label.setStyleSheet(f"color: {sclk_color}; padding: 2px;")
                    chain_layout.addWidget(sclk_label)

                # Register Clock pin
                rclk_pins = gpio_data.get('rclk_pins', [])
                if chain_idx < len(rclk_pins):
                    rclk_pin = rclk_pins[chain_idx]
                    rclk_state = "HIGH" if rclk_pin.get('state') else "LOW"
                    rclk_color = "#2196F3" if rclk_pin.get('state') else "#757575"
                    rclk_label = QLabel(f"Register Clock (GPIO {rclk_pin.get('pin')}): {rclk_state}")
                    rclk_label.setStyleSheet(f"color: {rclk_color}; padding: 2px;")
                    chain_layout.addWidget(rclk_label)

                # Output Enable pin
                oe_pins = gpio_data.get('oe_pins', [])
                if chain_idx < len(oe_pins):
                    oe_pin = oe_pins[chain_idx]
                    oe_state = "🔴 DISABLED" if oe_pin.get('state') else "🟢 ENABLED"
                    oe_color = "red" if oe_pin.get('state') else "green"
                    oe_label = QLabel(f"Output Enable (GPIO {oe_pin.get('pin')}): {oe_state}")
                    oe_label.setStyleSheet(f"color: {oe_color}; font-weight: bold; padding: 2px;")
                    chain_layout.addWidget(oe_label)

                # Serial Clear pin
                srclr_pins = gpio_data.get('srclr_pins', [])
                if chain_idx < len(srclr_pins):
                    srclr_pin = srclr_pins[chain_idx]
                    srclr_state = "🟢 NORMAL" if srclr_pin.get('state') else "🔴 CLEARED"
                    srclr_color = "green" if srclr_pin.get('state') else "red"
                    srclr_label = QLabel(f"Serial Clear (GPIO {srclr_pin.get('pin')}): {srclr_state}")
                    srclr_label.setStyleSheet(f"color: {srclr_color}; font-weight: bold; padding: 2px;")
                    chain_layout.addWidget(srclr_label)

                self.gpio_status_layout.addWidget(chain_group)

            # Timestamp
            import datetime
            timestamp = datetime.datetime.fromtimestamp(gpio_data.get('timestamp', 0))
            time_label = QLabel(f"Last Updated: {timestamp.strftime('%H:%M:%S')}")
            time_label.setStyleSheet("color: gray; font-size: 10px; padding: 5px;")
            self.gpio_status_layout.addWidget(time_label)

        except Exception as e:
            print(f"Error updating GPIO display: {e}")
            error_label = QLabel(f"Display Error: {e}")
            error_label.setStyleSheet("color: red; padding: 10px;")
            self.gpio_status_layout.addWidget(error_label)

    def connect_mqtt_messages(self):
        """Connect to MQTT messages from parent window"""
        try:
            if self.main_window and hasattr(self.main_window, 'system_mode'):
                system_mode = self.main_window.system_mode
                if hasattr(system_mode, 'mqtt_client') and system_mode.mqtt_client:
                    # Connect to MQTT message received signal
                    system_mode.mqtt_client.message_received.connect(self.handle_mqtt_message)
                    print("✓ Connected mode selector to MQTT messages")
                else:
                    print("⚠ No MQTT client available in system_mode")
            else:
                print("⚠ No parent window or system_mode available")
        except Exception as e:
            print(f"Error connecting to MQTT messages: {e}")

    def handle_mqtt_message(self, topic: str, payload: bytes):
        """Handle incoming MQTT messages"""
        try:
            # Handle GPIO status messages
            if topic == "firework/gpio":
                payload_str = payload.decode('utf-8')
                gpio_data = json.loads(payload_str)
                self.update_gpio_status_display(gpio_data)
                print(f"✓ Received GPIO status update")

        except Exception as e:
            print(f"Error handling MQTT message: {e}")

