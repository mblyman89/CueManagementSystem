import logging
import json
from typing import Optional, Dict, Any, List
from PySide6.QtCore import QObject, Signal, QTimer
from controllers.hardware_controller import HardwareController
from hardware.mqtt_client import MQTTClient
from hardware.shift_register_formatter import ShiftRegisterFormatter, ShiftRegisterConfig


class SystemMode(QObject):
    """
    Controller for managing system operation mode with support for SSH, MQTT, and Professional MQTT
    """

    # Signals for UI updates
    connection_status_changed = Signal(bool, str)  # connected, status_message
    message_received = Signal(str, str)  # topic, message
    error_occurred = Signal(str)  # error_message
    hardware_status_updated = Signal(dict)  # status_data

    def __init__(self, parent=None):
        super().__init__(parent)
        print("Initializing SystemMode")
        self.logger = logging.getLogger(__name__)

        self.current_mode = "simulation"
        self.communication_method = "mqtt"  # Default to MQTT for Raspberry Pi communication
        self.connection_settings = {
            "host": "raspberrypi.local",
            "port": 22,  # SSH port (will be overridden for MQTT)
            "username": "pi",
            "password": "",
            "known_hosts": None,
            "mqtt_port": 1883  # Default MQTT port
        }
        self.ssh_connection = None
        self.hardware_controller = HardwareController(self)

        # Professional MQTT components
        self.professional_mqtt_client: Optional[MQTTClient] = None

        # Create shift register configuration for large-scale system (1000 outputs)
        # Configure for 5 chains of 25 registers each = 125 total registers = 1000 outputs
        try:
            # Try with full 1000-output configuration
            default_shift_config = ShiftRegisterConfig(
                num_registers=125,  # 5 chains × 25 registers per chain
                outputs_per_register=8,  # Standard 74HC595
                max_simultaneous_outputs=50,  # Increased for large shows
                pulse_duration_ms=100,
                voltage_check_enabled=True,
                continuity_check_enabled=True,
                # Large-scale system configuration
                num_chains=5,  # 5 chains
                registers_per_chain=25,  # 25 registers per chain
                outputs_per_chain=200,  # 25 × 8 = 200 outputs per chain
                use_output_enable=True,
                use_serial_clear=True,
                output_enable_pins=[18, 19, 20, 21, 22],  # GPIO pins for OE
                serial_clear_pins=[23, 24, 25, 26, 27],  # GPIO pins for SRCLR
                arm_pin=17  # Single arm control pin
            )
            print("✅ Configured for 1000 outputs (5 chains × 25 registers × 8 outputs)")
        except TypeError as e:
            print(f"Advanced config failed: {e}")
            # Try with basic parameters but correct count
            try:
                default_shift_config = ShiftRegisterConfig(
                    num_registers=125,  # Still try for 1000 outputs
                    outputs_per_register=8,
                    max_simultaneous_outputs=50,
                    pulse_duration_ms=100,
                    voltage_check_enabled=True,
                    continuity_check_enabled=True
                )
                print("✅ Basic config with 1000 outputs")
            except TypeError:
                # Last resort - modify default config
                default_shift_config = ShiftRegisterConfig()
                default_shift_config.num_registers = 125
                default_shift_config.num_chains = 5
                default_shift_config.registers_per_chain = 25
                default_shift_config.outputs_per_chain = 200
                print("✅ Modified default config for 1000 outputs")

        self.shift_register_formatter = ShiftRegisterFormatter(default_shift_config)
        self.use_professional_mqtt = False  # Flag to enable professional MQTT mode

        # Large-scale system components
        from controllers.gpio_controller import GPIOController, GPIOConfig
        from views.managers.show_execution_manager import ShowExecutionManager

        # Initialize GPIO controller with proper configuration for your hardware
        gpio_config = GPIOConfig(
            # Output Enable pins (5 chains) - HIGH when disabled, LOW when enabled
            output_enable_pins=[5, 6, 7, 8, 12],
            output_enable_active_high=[False, False, False, False, False],  # LOW = enabled

            # Serial Clear pins (5 chains) - LOW when disabled, HIGH when enabled
            serial_clear_pins=[13, 16, 19, 20, 26],
            serial_clear_active_high=[True, True, True, True, True],  # HIGH = enabled

            # Shift register control pins (5 chains of 25 registers each)
            data_pins=[2, 3, 4, 14, 15],  # Data pins for each chain
            sclk_pins=[17, 18, 22, 23, 27],  # Serial clock pins
            rclk_pins=[9, 10, 11, 24, 25],  # Register clock (latch) pins

            # Arm control pin - LOW when disarmed, HIGH when armed
            arm_pin=21,
            arm_active_high=True,

            # WiFi/Adhoc mode control pin (disabled - no GPIO functionality yet)
            # wifi_mode_pin=1,  # Will be implemented later with SSH commands
            # wifi_mode_active_high=True
        )
        self.gpio_controller = GPIOController(gpio_config)

        # Initialize show execution manager
        self.show_execution_manager = ShowExecutionManager(self, self.gpio_controller)

        # Connect GPIO controller signals
        self.gpio_controller.gpio_state_changed.connect(self._on_gpio_state_changed)
        self.gpio_controller.system_state_changed.connect(self._on_system_state_changed)
        self.gpio_controller.error_occurred.connect(self._on_gpio_error)

        # Connect show execution manager signals
        self.show_execution_manager.show_started.connect(self._on_show_started)
        self.show_execution_manager.show_completed.connect(self._on_show_completed)
        self.show_execution_manager.show_paused.connect(self._on_show_paused)
        self.show_execution_manager.show_resumed.connect(self._on_show_resumed)
        self.show_execution_manager.show_aborted.connect(self._on_show_aborted)
        self.show_execution_manager.cue_executed.connect(self._on_cue_executed)
        self.show_execution_manager.progress_updated.connect(self._on_show_progress_updated)
        self.show_execution_manager.error_occurred.connect(self._on_show_execution_error)

        # Professional MQTT Configuration
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
            'qos_level': 2,  # Exactly once for safety
            'topics': {
                'command': 'firework/command',
                'status': 'firework/status',
                'emergency': 'firework/emergency',
                'heartbeat': 'firework/heartbeat'
            }
        }

        # Status monitoring
        self.heartbeat_timer = QTimer()
        self.heartbeat_timer.timeout.connect(self._send_heartbeat)
        self.heartbeat_timer.setInterval(30000)  # 30 seconds

        # Connection state
        self.is_professional_mqtt_connected = False
        self.last_error = ""

        # Set up hardware controller connection parameters
        self._update_hardware_controller_settings()

    def get_mode(self):
        """Get the current system mode"""
        return self.current_mode

    def _update_hardware_controller_settings(self):
        """Update the hardware controller with current connection settings"""
        host = self.connection_settings.get("host", "raspberrypi.local")
        mqtt_port = self.connection_settings.get("mqtt_port", 1883)
        username = self.connection_settings.get("username")
        password = self.connection_settings.get("password")

        # Update hardware controller connection parameters
        self.hardware_controller.set_connection_params(host, mqtt_port, username, password)

    def set_communication_method(self, method):
        """
        Set the communication method for hardware interaction

        Args:
            method (str): Either 'ssh', 'mqtt', or 'both'
        """
        if method not in ["ssh", "mqtt", "both"]:
            raise ValueError("Communication method must be either 'ssh', 'mqtt', or 'both'")

        print(f"Setting communication method to: {method}")

        # If switching away from SSH, close any existing SSH connection
        if self.communication_method == "ssh" and method != "ssh" and self.ssh_connection:
            print("Switching away from SSH - closing existing SSH connection")
            try:
                self.ssh_connection.close()
                self.ssh_connection = None
                print("SSH connection closed during method switch")
            except Exception as e:
                print(f"Error closing SSH connection during method switch: {e}")
                self.ssh_connection = None

        self.communication_method = method
        print(f"Communication method set to: {self.communication_method}")

        # Update hardware controller settings if using MQTT or both
        if method in ["mqtt", "both"]:
            self._update_hardware_controller_settings()

    async def set_mode(self, mode, connection_settings=None):
        """Set the system mode and optional connection settings"""
        print(f"Setting mode to: {mode}")
        if mode not in ["simulation", "hardware"]:
            raise ValueError("Mode must be either 'simulation' or 'hardware'")

        # Close any existing connections when switching modes
        print("Closing existing connections...")
        await self.close_connection()
        print("Connections closed successfully")

        self.current_mode = mode
        print(f"Mode set to: {self.current_mode}")

        # Update connection settings if provided
        if connection_settings and mode == "hardware":
            print(f"Updating connection settings: {connection_settings}")
            self.connection_settings.update(connection_settings)

            # Update hardware controller settings
            print("Updating hardware controller settings...")
            self._update_hardware_controller_settings()
            print("Hardware controller settings updated")

        print(f"set_mode completed successfully for mode: {mode}")
        return True  # Explicitly return a value

    def is_hardware_mode(self):
        """Check if system is in hardware mode"""
        return self.current_mode == "hardware"

    def is_simulation_mode(self):
        """Check if system is in simulation mode"""
        return self.current_mode == "simulation"

    async def connect_to_hardware(self):
        """Connect to the Raspberry Pi via SSH or MQTT"""
        print("Attempting hardware connection...")
        if not self.is_hardware_mode():
            print("Not in hardware mode, connection attempt aborted")
            return False, "Not in hardware mode"

        # Use the appropriate connection method
        if self.communication_method == "ssh":
            return await self._connect_via_ssh()
        elif self.communication_method == "mqtt":
            return await self._connect_via_mqtt()
        else:  # both
            # Try MQTT first, then SSH as fallback
            mqtt_success, mqtt_message = await self._connect_via_mqtt()
            if mqtt_success:
                return mqtt_success, mqtt_message
            else:
                print("MQTT connection failed, trying SSH as fallback")
                return await self._connect_via_ssh()

    async def _connect_via_ssh(self):
        """Connect to the Raspberry Pi via SSH (using synchronous method)"""
        try:
            if self.ssh_connection is None:
                print(f"Connecting to: {self.connection_settings['host']} via SSH")

                # Use synchronous SSH connection to avoid event loop conflicts
                import paramiko
                import socket

                # First test basic connectivity
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)

                result = sock.connect_ex((self.connection_settings['host'], self.connection_settings['port']))
                sock.close()

                if result != 0:
                    return False, f"Cannot reach SSH port {self.connection_settings['port']}"

                # Create SSH connection using paramiko
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                ssh.connect(
                    hostname=self.connection_settings['host'],
                    port=self.connection_settings['port'],
                    username=self.connection_settings['username'],
                    password=self.connection_settings['password'],
                    timeout=30
                )

                # Store the connection
                self.ssh_connection = ssh
                print("SSH connection established successfully")

            return True, "Successfully connected to Raspberry Pi via SSH"

        except ImportError:
            return False, "SSH connection requires paramiko library"
        except paramiko.AuthenticationException:
            print("SSH authentication failed")
            self.ssh_connection = None
            return False, "SSH authentication failed - check username and password"
        except paramiko.SSHException as e:
            print(f"SSH connection failed: {str(e)}")
            self.ssh_connection = None
            return False, f"SSH connection failed: {str(e)}"
        except Exception as e:
            print(f"Unexpected error during SSH connection: {str(e)}")
            self.ssh_connection = None
            return False, f"Unexpected error during SSH connection: {str(e)}"

    async def _connect_via_mqtt(self):
        """Connect to the Raspberry Pi via MQTT"""
        try:
            print(f"Connecting to: {self.connection_settings['host']} via MQTT")

            # Update hardware controller settings
            self._update_hardware_controller_settings()

            # Connect to MQTT broker
            success = self.hardware_controller.connect()

            if success:
                print("MQTT connection initiated successfully")

                # Also configure professional MQTT for hardware control
                try:
                    professional_config = {
                        'host': self.connection_settings['host'],
                        'port': self.connection_settings.get('mqtt_port', 1883),
                        'use_ssl': False,
                        'topics': {
                            'command': 'fireworks/command',
                            'status': 'fireworks/status',
                            'response': 'fireworks/response',
                            'heartbeat': 'fireworks/heartbeat'
                        }
                    }
                    print("Configuring professional MQTT for hardware control...")
                    self.configure_professional_mqtt(professional_config)
                except Exception as mqtt_error:
                    print(f"Professional MQTT configuration failed: {mqtt_error}")
                    # Don't fail the main connection for this

                return True, "Successfully initiated connection to Raspberry Pi via MQTT"
            else:
                print("MQTT connection failed to initiate")
                return False, "Failed to initiate MQTT connection"

        except Exception as e:
            print(f"Unexpected error during MQTT connection: {str(e)}")
            return False, f"Unexpected error during MQTT connection: {str(e)}"

    async def close_connection(self):
        """Close any active connections"""
        try:
            self.close_connection_sync()
            print("close_connection completed successfully")
            return True
        except Exception as e:
            print(f"Error in close_connection: {e}")
            return False

    def close_connection_sync(self):
        """Close any active connections (synchronous version for shutdown)"""
        # Close SSH connection if it exists
        if self.ssh_connection:
            print("Closing SSH connection")
            try:
                # Properly close paramiko SSH connection
                import paramiko
                if isinstance(self.ssh_connection, paramiko.SSHClient):
                    # Close any active channels first
                    transport = self.ssh_connection.get_transport()
                    if transport and transport.is_active():
                        transport.close()
                    # Close the SSH client
                    self.ssh_connection.close()
                else:
                    # Fallback for other SSH connection types
                    self.ssh_connection.close()

                self.ssh_connection = None
                print("SSH connection closed successfully")
            except Exception as e:
                print(f"Error closing SSH connection: {e}")
                self.ssh_connection = None

        # Disconnect MQTT client if using MQTT or both
        if self.communication_method in ["mqtt", "both"]:
            print("Disconnecting MQTT client")
            try:
                self.hardware_controller.disconnect()
                print("MQTT client disconnected")
            except Exception as e:
                print(f"Error disconnecting MQTT client: {e}")

        # Disconnect professional MQTT client if it exists
        if self.professional_mqtt_client:
            print("Disconnecting professional MQTT client")
            try:
                self.professional_mqtt_client.disconnect()
                self.professional_mqtt_client = None
                print("Professional MQTT client disconnected")
            except Exception as e:
                print(f"Error disconnecting professional MQTT client: {e}")

    async def test_connection(self):
        """Test the connection to the Raspberry Pi"""
        if self.communication_method == "ssh":
            return self.test_ssh_connection_sync()  # Use synchronous version
        elif self.communication_method == "mqtt":
            return await self.test_mqtt_connection()
        else:  # both
            # Test both connections
            mqtt_success, mqtt_message = await self.test_mqtt_connection()
            ssh_success, ssh_message = self.test_ssh_connection_sync()

            if mqtt_success and ssh_success:
                return True, "Both SSH and MQTT connections successful"
            elif mqtt_success:
                return True, f"MQTT connection successful. SSH failed: {ssh_message}"
            elif ssh_success:
                return True, f"SSH connection successful. MQTT failed: {mqtt_message}"
            else:
                return False, f"Both connections failed. SSH: {ssh_message}, MQTT: {mqtt_message}"

    def test_ssh_connection_sync(self):
        """Test SSH connection to the Raspberry Pi (synchronous version)"""
        try:
            print(f"Testing SSH connection to {self.connection_settings['host']}")

            # Use paramiko for synchronous SSH testing (Qt-friendly)
            import paramiko
            import socket

            # First test basic connectivity
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)

            result = sock.connect_ex((self.connection_settings['host'], self.connection_settings['port']))
            sock.close()

            if result != 0:
                return False, f"Cannot reach SSH port {self.connection_settings['port']}"

            # Try SSH authentication
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            ssh.connect(
                hostname=self.connection_settings['host'],
                port=self.connection_settings['port'],
                username=self.connection_settings['username'],
                password=self.connection_settings['password'],
                timeout=10
            )

            # Test a simple command
            stdin, stdout, stderr = ssh.exec_command("echo 'SSH test successful'")
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()

            # Properly close streams
            stdin.close()
            stdout.close()
            stderr.close()

            ssh.close()

            if output == "SSH test successful":
                print("SSH connection test successful")
                return True, "SSH connection successful!"
            else:
                print(f"SSH command failed: {error}")
                return False, f"SSH command failed: {error}"

        except ImportError:
            return False, "SSH testing requires paramiko library"
        except paramiko.AuthenticationException:
            return False, "SSH authentication failed - check username and password"
        except paramiko.SSHException as e:
            return False, f"SSH connection failed: {str(e)}"
        except Exception as e:
            print(f"SSH test error: {str(e)}")
            return False, f"Connection error: {str(e)}"

    async def test_ssh_connection(self):
        """Test SSH connection (async wrapper for compatibility)"""
        return self.test_ssh_connection_sync()

    async def test_mqtt_connection(self):
        """Test MQTT connection to the Raspberry Pi"""
        try:
            print(f"Testing MQTT connection to {self.connection_settings['host']}")

            # Test basic connectivity first
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)

            mqtt_port = self.connection_settings.get('mqtt_port', 1883)
            result = sock.connect_ex((self.connection_settings['host'], mqtt_port))
            sock.close()

            if result == 0:
                print("MQTT port is reachable")

                # Try to test actual MQTT connection if hardware controller supports it
                if hasattr(self.hardware_controller, 'test_connection'):
                    return await self.hardware_controller.test_connection()
                else:
                    return True, f"MQTT port {mqtt_port} is reachable!"
            else:
                print(f"Cannot reach MQTT port {mqtt_port}")
                return False, f"Cannot reach MQTT port {mqtt_port}"

        except Exception as e:
            print(f"MQTT connection test failed: {str(e)}")
            return False, f"MQTT connection test failed: {str(e)}"

    async def execute_command(self, command):
        """Execute a command on the target system"""
        if self.is_simulation_mode():
            print(f"[SIMULATION] Would execute: {command}")
            return True, f"Simulated execution of: {command}"

        # Use the appropriate communication method
        if self.communication_method == "ssh":
            return await self._execute_via_ssh(command)
        elif self.communication_method == "mqtt":
            return await self._execute_via_mqtt(command)
        else:  # both
            # Try MQTT first, then SSH as fallback
            mqtt_success, mqtt_message = await self._execute_via_mqtt(command)
            if mqtt_success:
                return mqtt_success, mqtt_message
            else:
                print("MQTT execution failed, trying SSH as fallback")
                return await self._execute_via_ssh(command)

    async def _execute_via_ssh(self, command):
        """Execute a command via SSH"""
        if not self.ssh_connection:
            success, message = await self._connect_via_ssh()
            if not success:
                return False, message

        stdin, stdout, stderr = None, None, None
        try:
            print(f"Executing command via SSH: {command}")

            # Execute command using paramiko
            stdin, stdout, stderr = self.ssh_connection.exec_command(command)

            # Read the results
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            exit_status = stdout.channel.recv_exit_status()

            # Properly close the streams to prevent BufferedFile cleanup errors
            stdin.close()
            stdout.close()
            stderr.close()

            if exit_status == 0:
                return True, output
            else:
                return False, f"Command failed: {error}"

        except Exception as e:
            print(f"SSH command execution failed: {str(e)}")
            return False, f"Command execution failed: {str(e)}"
        finally:
            # Ensure streams are closed even if an exception occurs
            try:
                if stdin:
                    stdin.close()
                if stdout:
                    stdout.close()
                if stderr:
                    stderr.close()
            except Exception as cleanup_error:
                print(f"Error closing SSH streams: {cleanup_error}")

    async def _execute_via_mqtt(self, command):
        """Execute a command via MQTT"""
        # Ensure we're connected
        if not self.hardware_controller.is_hardware_connected():
            success, message = await self._connect_via_mqtt()
            if not success:
                return False, message

        try:
            print(f"Executing command via MQTT: {command}")

            # Convert command to a format suitable for MQTT
            command_data = {"command_text": command}

            # Send the command
            success, message = await self.hardware_controller.send_command("execute", command_data)

            return success, message

        except Exception as e:
            print(f"MQTT command execution failed: {str(e)}")
            return False, f"Command execution failed: {str(e)}"

    async def send_cue(self, cue_data):
        """
        Send a cue to the Raspberry Pi

        Args:
            cue_data (dict): The cue data to send

        Returns:
            tuple: (success, message)
        """
        if self.is_simulation_mode():
            print(f"[SIMULATION] Would send cue: {cue_data}")
            return True, f"Simulated sending of cue: {cue_data.get('cue_number', '')}"

        # Use the appropriate communication method
        if self.communication_method == "ssh":
            # For SSH, convert cue to a command and execute
            command = self._convert_cue_to_command(cue_data)
            return await self._execute_via_ssh(command)
        elif self.communication_method == "mqtt":
            # For MQTT, use the hardware controller to send the cue
            return await self.hardware_controller.send_cue(cue_data)
        else:  # both
            # Try MQTT first, then SSH as fallback
            mqtt_success, mqtt_message = await self.hardware_controller.send_cue(cue_data)
            if mqtt_success:
                return mqtt_success, mqtt_message
            else:
                print("MQTT cue sending failed, trying SSH as fallback")
                command = self._convert_cue_to_command(cue_data)
                return await self._execute_via_ssh(command)

    def _convert_cue_to_command(self, cue_data):
        """
        Convert cue data to a command string for SSH execution

        Args:
            cue_data (dict): The cue data to convert

        Returns:
            str: The command string
        """
        # This is a simple example - you may need to customize this based on your needs
        cue_number = cue_data.get("cue_number", "")
        cue_type = cue_data.get("cue_type", "")
        outputs = ",".join(map(str, cue_data.get("output_values", [])))

        return f"python3 /home/pi/execute_cue.py --cue={cue_number} --type={cue_type} --outputs={outputs}"

    # Professional MQTT Methods
    def enable_professional_mqtt(self, enable: bool = True):
        """Enable or disable professional MQTT mode"""
        self.use_professional_mqtt = enable
        if enable:
            print("Professional MQTT mode enabled")
        else:
            print("Professional MQTT mode disabled")
            if self.professional_mqtt_client:
                self.disconnect_professional_mqtt()

    def initialize_professional_mqtt(self, config: Dict[str, Any] = None) -> bool:
        """Initialize professional MQTT connection with given configuration"""
        try:
            if config:
                self.professional_mqtt_config.update(config)

            # Create professional MQTT client with proper ConnectionConfig
            from hardware.mqtt_client import ConnectionConfig

            mqtt_config = ConnectionConfig(
                host=self.professional_mqtt_config['broker_host'],
                port=self.professional_mqtt_config['broker_port'],
                client_id=self.professional_mqtt_config['client_id'],
                username=self.professional_mqtt_config.get('username'),
                password=self.professional_mqtt_config.get('password'),
                use_ssl=self.professional_mqtt_config.get('use_ssl', False),
                ca_cert_path=self.professional_mqtt_config.get('ssl_ca_path'),
                cert_file_path=self.professional_mqtt_config.get('ssl_cert_path'),
                key_file_path=self.professional_mqtt_config.get('ssl_key_path'),
                keepalive=self.professional_mqtt_config.get('keepalive', 60)
            )

            self.professional_mqtt_client = MQTTClient(mqtt_config)

            # Connect signals
            self.professional_mqtt_client.connection_state_changed.connect(self._on_professional_mqtt_state_changed)
            self.professional_mqtt_client.message_received.connect(self._on_professional_mqtt_message_received)
            self.professional_mqtt_client.error_occurred.connect(self._on_professional_mqtt_error)

            # Connect to broker
            success = self.professional_mqtt_client.connect()
            if success:
                self._subscribe_to_professional_topics()
                self.heartbeat_timer.start()

            return success

        except Exception as e:
            self.logger.error(f"Failed to initialize professional MQTT: {e}")
            self.error_occurred.emit(f"Professional MQTT initialization failed: {e}")
            return False

    def disconnect_professional_mqtt(self):
        """Disconnect from professional MQTT broker"""
        try:
            self.heartbeat_timer.stop()
            if self.professional_mqtt_client:
                self.professional_mqtt_client.disconnect()
                self.professional_mqtt_client = None
            self.is_professional_mqtt_connected = False
            self.connection_status_changed.emit(False, "Disconnected from professional MQTT")
        except Exception as e:
            self.logger.error(f"Error disconnecting professional MQTT: {e}")

    async def send_professional_cue(self, cue_data: Dict[str, Any]) -> tuple:
        """Send firework cue command via professional MQTT"""
        try:
            if not self.use_professional_mqtt:
                # Fall back to regular cue sending
                return await self.send_cue(cue_data)

            if not self.is_professional_mqtt_connected or not self.professional_mqtt_client:
                return False, "Professional MQTT not connected"

            # Format data for shift registers
            shift_data = self.shift_register_formatter.format_cue_data(cue_data)

            # Create command message
            command = {
                'type': 'firework_cue',
                'timestamp': self._get_timestamp(),
                'cue_id': cue_data.get('cue_id'),
                'cue_number': cue_data.get('cue_number'),
                'shift_register_data': shift_data,
                'safety_check': True
            }

            # Send with QoS 2 for exactly-once delivery
            success = self.professional_mqtt_client.publish(
                self.professional_mqtt_config['topics']['command'],
                json.dumps(command),
                qos=2
            )

            if success:
                self.logger.info(f"Sent professional firework command for cue {cue_data.get('cue_number')}")
                return True, f"Professional cue {cue_data.get('cue_number')} sent successfully"
            else:
                return False, "Failed to send professional firework command"

        except Exception as e:
            self.logger.error(f"Error sending professional firework command: {e}")
            return False, f"Professional command send error: {e}"

    def send_emergency_stop(self) -> bool:
        """Send emergency stop command via professional MQTT"""
        try:
            if not self.use_professional_mqtt or not self.is_professional_mqtt_connected or not self.professional_mqtt_client:
                return False

            emergency_command = {
                'type': 'emergency_stop',
                'timestamp': self._get_timestamp(),
                'priority': 'critical'
            }

            # Send with highest priority
            success = self.professional_mqtt_client.publish(
                self.professional_mqtt_config['topics']['emergency'],
                json.dumps(emergency_command),
                qos=2
            )

            if success:
                self.logger.critical("Emergency stop command sent via professional MQTT")

            return success

        except Exception as e:
            self.logger.error(f"Error sending emergency stop: {e}")
            return False

    def get_professional_mqtt_status(self) -> Dict[str, Any]:
        """Get current professional MQTT connection status and metrics"""
        if not self.professional_mqtt_client:
            return {
                'connected': False,
                'status': 'Not initialized',
                'broker': 'N/A',
                'client_id': 'N/A',
                'last_error': self.last_error,
                'enabled': self.use_professional_mqtt
            }

        return {
            'connected': self.is_professional_mqtt_connected,
            'status': 'Connected' if self.is_professional_mqtt_connected else 'Disconnected',
            'broker': f"{self.professional_mqtt_config['broker_host']}:{self.professional_mqtt_config['broker_port']}",
            'client_id': self.professional_mqtt_config['client_id'],
            'ssl_enabled': self.professional_mqtt_config.get('use_ssl', False),
            'qos_level': self.professional_mqtt_config.get('qos_level', 2),
            'last_error': self.last_error,
            'enabled': self.use_professional_mqtt,
            'connection_quality': self.professional_mqtt_client.get_connection_quality() if self.professional_mqtt_client else {}
        }

    def configure_professional_mqtt(self, config: Dict[str, Any]):
        """Configure and initialize professional MQTT with given configuration"""
        try:
            print(f"Configuring professional MQTT with config: {config}")

            # Update configuration
            self.professional_mqtt_config.update(config)

            # Enable professional MQTT mode
            self.enable_professional_mqtt(True)

            # Initialize with new configuration
            success = self.initialize_professional_mqtt(config)

            if success:
                print("Professional MQTT configured and connected successfully")
            else:
                print("Professional MQTT configuration failed")

            return success

        except Exception as e:
            print(f"Error configuring professional MQTT: {e}")
            return False

    def update_professional_mqtt_config(self, new_config: Dict[str, Any]):
        """Update professional MQTT configuration"""
        self.professional_mqtt_config.update(new_config)

        # If connected, reconnect with new config
        if self.is_professional_mqtt_connected:
            self.disconnect_professional_mqtt()
            self.initialize_professional_mqtt()

    def test_professional_mqtt_connection(self) -> Dict[str, Any]:
        """Test professional MQTT connection and return results"""
        try:
            # Create temporary client for testing
            from hardware.mqtt_client import ConnectionConfig

            test_config = ConnectionConfig(
                host=self.professional_mqtt_config['broker_host'],
                port=self.professional_mqtt_config['broker_port'],
                client_id=f"{self.professional_mqtt_config['client_id']}_test",
                username=self.professional_mqtt_config.get('username'),
                password=self.professional_mqtt_config.get('password'),
                use_ssl=self.professional_mqtt_config.get('use_ssl', False),
                ca_cert_path=self.professional_mqtt_config.get('ssl_ca_path'),
                cert_file_path=self.professional_mqtt_config.get('ssl_cert_path'),
                key_file_path=self.professional_mqtt_config.get('ssl_key_path')
            )

            test_client = MQTTClient(test_config)

            success = test_client.connect()
            if success:
                test_client.disconnect()
                return {
                    'success': True,
                    'message': 'Professional MQTT connection test successful',
                    'broker': f"{self.professional_mqtt_config['broker_host']}:{self.professional_mqtt_config['broker_port']}"
                }
            else:
                return {
                    'success': False,
                    'message': 'Professional MQTT connection test failed',
                    'error': 'Unable to connect to broker'
                }

        except Exception as e:
            return {
                'success': False,
                'message': 'Professional MQTT connection test failed',
                'error': str(e)
            }

    # Private methods for professional MQTT
    def _subscribe_to_professional_topics(self):
        """Subscribe to required professional MQTT topics"""
        if not self.professional_mqtt_client:
            return

        topics = [
            (self.professional_mqtt_config['topics']['status'], 1),
            (self.professional_mqtt_config['topics']['emergency'], 2),
            (self.professional_mqtt_config['topics']['heartbeat'], 0)
        ]

        for topic, qos in topics:
            self.professional_mqtt_client.subscribe(topic, qos)

    def _on_professional_mqtt_state_changed(self, state):
        """Handle professional MQTT connection state changes"""
        from hardware.mqtt_client import ConnectionState

        if state == ConnectionState.CONNECTED:
            self.is_professional_mqtt_connected = True
            self.last_error = ""
            self.connection_status_changed.emit(True, "Connected to professional MQTT broker")
            self.logger.info("Professional MQTT connection established")
        elif state == ConnectionState.DISCONNECTED:
            self.is_professional_mqtt_connected = False
            self.connection_status_changed.emit(False, "Disconnected from professional MQTT broker")
            self.logger.warning("Professional MQTT connection lost")
        elif state == ConnectionState.CONNECTING:
            self.logger.info("Professional MQTT connecting...")
        elif state == ConnectionState.ERROR:
            self.is_professional_mqtt_connected = False
            self.connection_status_changed.emit(False, "Professional MQTT connection error")
            self.logger.error("Professional MQTT connection error")

    def _on_professional_mqtt_message_received(self, topic: str, message: str):
        """Handle received professional MQTT message"""
        try:
            self.message_received.emit(topic, message)

            # Handle specific message types
            if topic == self.professional_mqtt_config['topics']['status']:
                self._handle_professional_status_message(message)
            elif topic == self.professional_mqtt_config['topics']['emergency']:
                self._handle_professional_emergency_message(message)

        except Exception as e:
            self.logger.error(f"Error processing received professional MQTT message: {e}")

    def _on_professional_mqtt_error(self, error_message: str):
        """Handle professional MQTT error"""
        self.last_error = error_message
        self.error_occurred.emit(f"Professional MQTT: {error_message}")
        self.logger.error(f"Professional MQTT error: {error_message}")

    def _handle_professional_status_message(self, message: str):
        """Handle professional hardware status message"""
        try:
            status_data = json.loads(message)
            self.hardware_status_updated.emit(status_data)
        except json.JSONDecodeError:
            self.logger.error("Invalid professional status message format")

    def _handle_professional_emergency_message(self, message: str):
        """Handle professional emergency message"""
        try:
            emergency_data = json.loads(message)
            self.logger.critical(f"Professional emergency message received: {emergency_data}")
            # Trigger emergency procedures
        except json.JSONDecodeError:
            self.logger.error("Invalid professional emergency message format")

    def _send_heartbeat(self):
        """Send heartbeat message via professional MQTT"""
        if self.use_professional_mqtt and self.is_professional_mqtt_connected and self.professional_mqtt_client:
            heartbeat = {
                'timestamp': self._get_timestamp(),
                'status': 'alive',
                'client_id': self.professional_mqtt_config['client_id']
            }

            self.professional_mqtt_client.publish(
                self.professional_mqtt_config['topics']['heartbeat'],
                json.dumps(heartbeat),
                qos=0
            )

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    # Button Integration Methods for Large-Scale System

    def handle_enable_outputs_button(self) -> bool:
        """
        Handle Enable/Disable Outputs button click
        Toggles 10 GPIO pins (5 active high, 5 active low)

        Returns:
            bool: New enabled state
        """
        import traceback
        import time
        timestamp = time.time()
        print(f"SystemMode: handle_enable_outputs_button called at {timestamp}")
        print("SystemMode: Call stack:")
        for line in traceback.format_stack()[-3:-1]:  # Show last 2 stack frames
            print(f"  {line.strip()}")

        try:
            new_state = self.gpio_controller.toggle_outputs_enabled()
            print(f"SystemMode: received new_state from gpio_controller: {new_state}")

            # Send MQTT command to Pi
            if self.use_professional_mqtt and self.is_professional_mqtt_connected:
                print("SystemMode: Sending MQTT command")
                command = self.gpio_controller.create_gpio_command(
                    "toggle_outputs",
                    enabled=new_state
                )

                success = self.professional_mqtt_client.publish(
                    self.professional_mqtt_config['topics']['command'],
                    json.dumps(command),
                    qos=2
                )

                if success:
                    self.logger.info(f"Outputs {'enabled' if new_state else 'disabled'} via MQTT")
                    print(f"SystemMode: MQTT command sent successfully")
                else:
                    self.logger.error("Failed to send outputs command via MQTT")
                    print("SystemMode: MQTT command failed")
            else:
                print("SystemMode: Professional MQTT not connected, skipping MQTT command")

            print(f"SystemMode: returning new_state: {new_state}")
            return new_state

        except Exception as e:
            print(f"SystemMode: Exception in handle_enable_outputs_button: {e}")
            self.logger.error(f"Failed to handle enable outputs: {e}")
            self.error_occurred.emit(f"Enable outputs failed: {e}")
            # Return the current state instead of False to avoid incorrect UI updates
            current_state = getattr(self.gpio_controller, 'outputs_enabled', False)
            print(f"SystemMode: Exception occurred, returning current state: {current_state}")
            return current_state

    def handle_arm_outputs_button(self) -> bool:
        """
        Handle Arm/Disarm Outputs button click
        Controls 1 GPIO pin state

        Returns:
            bool: New armed state
        """
        try:
            current_armed = self.gpio_controller.system_armed
            new_state = self.gpio_controller.set_arm_state(not current_armed)

            # Send MQTT command to Pi
            if self.use_professional_mqtt and self.is_professional_mqtt_connected:
                command = self.gpio_controller.create_gpio_command(
                    "set_arm_state",
                    armed=new_state
                )

                success = self.professional_mqtt_client.publish(
                    self.professional_mqtt_config['topics']['command'],
                    json.dumps(command),
                    qos=2
                )

                if success:
                    self.logger.info(f"System {'armed' if new_state else 'disarmed'} via MQTT")
                else:
                    self.logger.error("Failed to send arm command via MQTT")

            return new_state

        except Exception as e:
            self.logger.error(f"Failed to handle arm outputs: {e}")
            self.error_occurred.emit(f"Arm outputs failed: {e}")
            return False

    async def handle_execute_cue_button(self, selected_cue: Dict[str, Any]) -> bool:
        """
        Handle Execute Cue button click
        Executes a single selected cue

        Args:
            selected_cue: The cue data to execute

        Returns:
            bool: True if execution successful
        """
        try:
            if not selected_cue:
                self.error_occurred.emit("No cue selected for execution")
                return False

            # Validate cue has required fields
            if 'cue_id' not in selected_cue:
                self.error_occurred.emit("Selected cue missing cue_id")
                return False

            self.logger.info(f"Executing single cue: {selected_cue['cue_id']}")

            # Execute through show execution manager for consistency
            success = await self.show_execution_manager.execute_single_cue(selected_cue)

            if success:
                self.logger.info(f"Cue {selected_cue['cue_id']} executed successfully")
            else:
                self.logger.error(f"Cue {selected_cue['cue_id']} execution failed")

            return success

        except Exception as e:
            self.logger.error(f"Failed to execute cue: {e}")
            self.error_occurred.emit(f"Cue execution failed: {e}")
            return False

    async def handle_execute_show_button(self, show_cues: List[Dict[str, Any]]) -> bool:
        """
        Handle Execute Show button click
        Executes all cues in sequence

        Args:
            show_cues: List of all cues to execute

        Returns:
            bool: True if show execution started successfully
        """
        try:
            if not show_cues:
                self.error_occurred.emit("No cues available for show execution")
                return False

            self.logger.info(f"Starting show execution with {len(show_cues)} cues")

            # Load and execute the show
            if self.show_execution_manager.load_show(show_cues):
                success = await self.show_execution_manager.execute_show()

                if success:
                    self.logger.info("Show execution started successfully")
                else:
                    self.logger.error("Failed to start show execution")

                return success
            else:
                self.error_occurred.emit("Failed to load show for execution")
                return False

        except Exception as e:
            self.logger.error(f"Failed to execute show: {e}")
            self.error_occurred.emit(f"Show execution failed: {e}")
            return False

    def handle_pause_button(self) -> bool:
        """
        Handle Pause button click
        Pauses the currently running show

        Returns:
            bool: True if paused successfully
        """
        try:
            success = self.show_execution_manager.pause_show()

            if success:
                self.logger.info("Show paused")
            else:
                self.logger.warning("Failed to pause show")

            return success

        except Exception as e:
            self.logger.error(f"Failed to pause show: {e}")
            self.error_occurred.emit(f"Show pause failed: {e}")
            return False

    def handle_resume_button(self) -> bool:
        """
        Handle Resume button click
        Resumes the paused show

        Returns:
            bool: True if resumed successfully
        """
        try:
            success = self.show_execution_manager.resume_show()

            if success:
                self.logger.info("Show resumed")
            else:
                self.logger.warning("Failed to resume show")

            return success

        except Exception as e:
            self.logger.error(f"Failed to resume show: {e}")
            self.error_occurred.emit(f"Show resume failed: {e}")
            return False

    def handle_abort_button(self) -> bool:
        """
        Handle Abort button click
        Immediately stops show and resets all GPIO states

        Returns:
            bool: True if aborted successfully
        """
        try:
            # Abort the show
            show_aborted = self.show_execution_manager.abort_show("User abort button pressed")

            # Emergency abort GPIO states
            gpio_aborted = self.gpio_controller.emergency_abort()

            # Send emergency stop via MQTT
            if self.use_professional_mqtt and self.is_professional_mqtt_connected:
                emergency_command = {
                    'type': 'emergency_stop',
                    'timestamp': self._get_timestamp(),
                    'reason': 'Abort button pressed',
                    'priority': 'critical'
                }

                self.professional_mqtt_client.publish(
                    self.professional_mqtt_config['topics']['emergency'],
                    json.dumps(emergency_command),
                    qos=2
                )

            success = show_aborted and gpio_aborted

            if success:
                self.logger.critical("ABORT: Show stopped and system disarmed")
            else:
                self.logger.error("ABORT: Partial failure in abort sequence")

            return success

        except Exception as e:
            self.logger.error(f"Failed to abort: {e}")
            self.error_occurred.emit(f"Abort failed: {e}")
            return False

    # WiFi/Adhoc mode functionality disabled for now
    # def handle_wifi_mode_button(self) -> str:
    #     """
    #     Handle WiFi/Adhoc mode toggle button (DISABLED)
    #     Future: Will send SSH command to Pi to switch network modes
    #     """
    #     pass

    def handle_shutdown_pi_button(self) -> bool:
        """
        Handle Pi Shutdown button click
        Sends shutdown command to Raspberry Pi

        Returns:
            bool: True if shutdown command sent successfully
        """
        try:
            if self.use_professional_mqtt and self.is_professional_mqtt_connected:
                shutdown_command = {
                    'type': 'system_command',
                    'command': 'shutdown',
                    'timestamp': self._get_timestamp(),
                    'parameters': {
                        'delay_seconds': 10,  # Give time for acknowledgment
                        'reason': 'User requested shutdown'
                    }
                }

                success = self.professional_mqtt_client.publish(
                    self.professional_mqtt_config['topics']['command'],
                    json.dumps(shutdown_command),
                    qos=2
                )

                if success:
                    self.logger.info("Pi shutdown command sent via MQTT")
                else:
                    self.logger.error("Failed to send Pi shutdown command")

                return success
            else:
                self.error_occurred.emit("MQTT not connected - cannot send shutdown command")
                return False

        except Exception as e:
            self.logger.error(f"Failed to send shutdown command: {e}")
            self.error_occurred.emit(f"Pi shutdown failed: {e}")
            return False

    # Event handlers for GPIO and show execution signals

    def _on_gpio_state_changed(self, pin_name: str, state: bool):
        """Handle GPIO state changes"""
        self.logger.debug(f"GPIO {pin_name} changed to {'HIGH' if state else 'LOW'}")

    def _on_system_state_changed(self, new_state: str):
        """Handle system state changes"""
        self.logger.info(f"System state changed to: {new_state}")

    def _on_gpio_error(self, error_message: str):
        """Handle GPIO errors"""
        self.logger.error(f"GPIO error: {error_message}")
        self.error_occurred.emit(f"GPIO: {error_message}")

    def _on_show_started(self, total_cues: int):
        """Handle show started event"""
        self.logger.info(f"Show started with {total_cues} cues")

    def _on_show_completed(self):
        """Handle show completed event"""
        self.logger.info("Show execution completed")

    def _on_show_paused(self, current_cue_index: int):
        """Handle show paused event"""
        self.logger.info(f"Show paused at cue index {current_cue_index}")

    def _on_show_resumed(self, current_cue_index: int):
        """Handle show resumed event"""
        self.logger.info(f"Show resumed at cue index {current_cue_index}")

    def _on_show_aborted(self, reason: str):
        """Handle show aborted event"""
        self.logger.warning(f"Show aborted: {reason}")

    def _on_cue_executed(self, cue_id: str, success: bool, message: str):
        """Handle individual cue execution"""
        if success:
            self.logger.info(f"Cue {cue_id} executed successfully")
        else:
            self.logger.error(f"Cue {cue_id} failed: {message}")

    def _on_show_progress_updated(self, progress_info: dict):
        """Handle show progress updates"""
        self.logger.debug(f"Show progress: {progress_info['completed_cues']}/{progress_info['total_cues']} cues")

    def _on_show_execution_error(self, error_message: str):
        """Handle show execution errors"""
        self.logger.error(f"Show execution error: {error_message}")
        self.error_occurred.emit(f"Show: {error_message}")

    # Status and monitoring methods

    def get_comprehensive_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status including GPIO and show execution

        Returns:
            dict: Complete system status
        """
        base_status = self.get_professional_mqtt_status()

        # Add GPIO status
        gpio_status = self.gpio_controller.get_system_status()

        # Add show execution status
        show_progress = self.show_execution_manager.get_show_progress()
        show_summary = self.show_execution_manager.get_execution_summary()

        return {
            'mqtt': base_status,
            'gpio': gpio_status,
            'show_execution': {
                'progress': {
                    'total_cues': show_progress.total_cues,
                    'completed_cues': show_progress.completed_cues,
                    'current_cue_index': show_progress.current_cue_index,
                    'current_cue_id': show_progress.current_cue_id,
                    'elapsed_seconds': int(show_progress.elapsed_time.total_seconds()),
                    'estimated_remaining_seconds': int(show_progress.estimated_remaining.total_seconds()),
                    'state': show_progress.state.value
                },
                'summary': show_summary
            },
            'system_capabilities': {
                'max_cues': 1000,
                'max_outputs': 1000,
                'num_chains': 5,
                'registers_per_chain': 25,
                'outputs_per_chain': 200
            },
            'timestamp': self._get_timestamp()
        }
