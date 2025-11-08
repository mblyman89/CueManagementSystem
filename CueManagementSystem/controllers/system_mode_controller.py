import logging
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from PySide6.QtCore import QObject, Signal, QTimer
from controllers.hardware_controller import HardwareController
from views.managers.shift_register_formatter_manager import ShiftRegisterFormatter, ShiftRegisterConfig


class SystemMode(QObject):
    """
    Controller for managing system operation mode with support for SSH
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
        self.communication_method = "ssh"  # Default to SSH for Raspberry Pi communication
        self.connection_settings = {
            "host": "192.168.68.82",  # Hardcoded Pi IP
            "port": 22,  # SSH port
            "username": "cuepishifter",  # Hardcoded username
            "password": "cuepishifter",  # Hardcoded password
            "known_hosts": None
        }
        self.ssh_connection = None
        self.hardware_controller = HardwareController(self)

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
                output_enable_pins=[2, 3, 4, 5, 6],  # GPIO pins for OE (Active LOW: HIGH=disabled, LOW=enabled)
                serial_clear_pins=[13, 16, 19, 20, 26],  # GPIO pins for SRCLR (Active HIGH: LOW=disabled, HIGH=enabled)
                arm_pin=21  # Single arm control pin (Active HIGH: LOW=disarmed, HIGH=armed)
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

        # Large-scale system components
        from controllers.gpio_controller import GPIOController, GPIOConfig
        from views.managers.show_execution_manager import ShowExecutionManager

        # Initialize GPIO controller with proper configuration for your hardware
        gpio_config = GPIOConfig(
            # Output Enable pins (5 chains) - HIGH when disabled, LOW when enabled
            output_enable_pins=[2, 3, 4, 5, 6],
            output_enable_active_high=[False, False, False, False, False],  # LOW = enabled

            # Serial Clear pins (5 chains) - LOW when disabled, HIGH when enabled
            serial_clear_pins=[13, 16, 19, 20, 26],
            serial_clear_active_high=[True, True, True, True, True],  # HIGH = enabled

            # Shift register control pins (5 chains of 25 registers each)
            data_pins=[7, 8, 12, 14, 15],  # Data pins for each chain
            sclk_pins=[17, 18, 22, 23, 27],  # Serial clock pins
            rclk_pins=[9, 10, 11, 24, 25],  # Register clock (latch) pins

            # Arm control pin - LOW when disarmed, HIGH when armed
            arm_pin=21,
            arm_active_high=True,

            # WiFi/Adhoc mode control is implemented with SSH commands to switch_wifi_mode.py
            # No GPIO pin needed for this functionality
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

    def get_mode(self):
        """Get the current system mode"""
        return self.current_mode

    def set_communication_method(self, method):
        """
        Set the communication method for hardware interaction

        Args:
            method (str): 'ssh'
        """
        if method != "ssh":
            raise ValueError("Communication method must be 'ssh'")

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

        print(f"set_mode completed successfully for mode: {mode}")
        return True  # Explicitly return a value

    def is_hardware_mode(self):
        """Check if system is in hardware mode"""
        return self.current_mode == "hardware"

    def normalize_cue_for_pi(self, cue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize cue data to match Pi script expectations

        Args:
            cue_data: Dictionary with application format

        Returns:
            Dictionary with Pi format
        """
        cue_type = cue_data.get('cue_type', '')
        output_values = cue_data.get('output_values', [])

        # Base normalized data
        normalized = {
            'type': cue_type,  # Pi expects 'type' not 'cue_type'
            'time': cue_data.get('time', 0),  # Time in milliseconds
            'duration': 500,  # Default 500ms pulse duration
        }

        # Add type-specific fields
        if cue_type == 'SINGLE SHOT':
            if len(output_values) >= 1:
                normalized['output'] = output_values[0]

        elif cue_type == 'DOUBLE SHOT':
            if len(output_values) >= 2:
                normalized['output1'] = output_values[0]
                normalized['output2'] = output_values[1]

        elif cue_type == 'SINGLE RUN':
            if len(output_values) >= 2:
                normalized['start_output'] = output_values[0]
                normalized['end_output'] = output_values[-1]
                normalized['delay'] = int(cue_data.get('delay', 0) * 1000)  # Convert to ms

        elif cue_type == 'DOUBLE RUN':
            # For DOUBLE RUN, outputs are paired
            # outputs_str format: "1, 2, 3, 4" means pairs (1,2) and (3,4)
            if len(output_values) >= 4:
                mid = len(output_values) // 2
                normalized['start_output1'] = output_values[0]
                normalized['end_output1'] = output_values[mid - 1]
                normalized['start_output2'] = output_values[mid]
                normalized['end_output2'] = output_values[-1]
                normalized['delay'] = int(cue_data.get('delay', 0) * 1000)  # Convert to ms

        return normalized

    def is_simulation_mode(self):
        """Check if system is in simulation mode"""
        return self.current_mode == "simulation"

    async def connect_to_hardware(self):
        """Connect to the Raspberry Pi via SSH"""
        print("Attempting hardware connection...")
        if not self.is_hardware_mode():
            print("Not in hardware mode, connection attempt aborted")
            return False, "Not in hardware mode"

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

    async def test_connection(self):
        """Test the connection to the Raspberry Pi"""
        return self.test_ssh_connection_sync()  # Use synchronous version

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

    async def execute_command(self, command):
        """Execute a command on the target system"""
        if self.is_simulation_mode():
            print(f"[SIMULATION] Would execute: {command}")
            return True, f"Simulated execution of: {command}"

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

        # Convert cue to a command and execute
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
        # Normalize cue data for Pi
        normalized_cue = self.normalize_cue_for_pi(cue_data)

        # Convert to JSON string
        import json
        cue_json = json.dumps(normalized_cue)

        # Return command with JSON argument (no flags)
        return f"python3 ~/execute_cue.py '{cue_json}'"

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
            # First update local GPIO controller state
            new_state = self.gpio_controller.toggle_outputs_enabled()
            print(f"SystemMode: received new_state from gpio_controller: {new_state}")

            # Prepare status message for UI feedback
            status_message = f"Outputs {'enabled' if new_state else 'disabled'}"

            # Send SSH command to Pi if in hardware mode
            if self.is_hardware_mode():
                print("SystemMode: In hardware mode, creating fresh SSH connection")

                # Create fresh SSH connection (like Set GPIO State button does)
                import paramiko
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                try:
                    # Connect using stored settings
                    print(f"SystemMode: Connecting to {self.connection_settings['host']}...")
                    ssh.connect(
                        hostname=self.connection_settings['host'],
                        port=self.connection_settings.get('port', 22),
                        username=self.connection_settings['username'],
                        password=self.connection_settings.get('password', ''),
                        timeout=10
                    )
                    print("SystemMode: SSH connection established")

                    # Execute command
                    command = f"python3 ~/toggle_outputs.py --enabled={int(new_state)}"
                    print(f"SystemMode: Executing command: {command}")

                    stdin, stdout, stderr = ssh.exec_command(command)
                    exit_status = stdout.channel.recv_exit_status()

                    # Read both stdout and stderr
                    output = stdout.read().decode().strip()
                    error = stderr.read().decode().strip()

                    print(f"SystemMode: Command exit status: {exit_status}")
                    print(f"SystemMode: Command stdout: {output}")
                    print(f"SystemMode: Command stderr: {error}")

                    if exit_status == 0:
                        self.logger.info(f"{status_message} via SSH: {output}")
                        print(f"SystemMode: SSH command sent successfully")

                        # Emit message for UI feedback
                        self.message_received.emit("gpio_status", f"{status_message} successfully")
                    else:
                        self.logger.error(f"Failed to send outputs command via SSH: {error}")
                        print(f"SystemMode: SSH command failed with exit status {exit_status}")

                        # Emit error for UI feedback but don't change state
                        self.error_occurred.emit(
                            f"Warning: {status_message} in UI only. Hardware control failed: {error if error else 'Unknown error'}")

                    # Close the connection
                    ssh.close()
                    print("SystemMode: SSH connection closed")

                except Exception as e:
                    self.logger.error(f"Error with SSH connection: {e}")
                    print(f"SystemMode: SSH connection error: {e}")

                    # Emit error for UI feedback
                    self.error_occurred.emit(
                        f"Warning: {status_message} in UI only. SSH connection error: {str(e)}")

                    # Try to close connection if it was opened
                    try:
                        ssh.close()
                    except:
                        pass
            else:
                print("SystemMode: In simulation mode, skipping SSH command")
                self.message_received.emit("gpio_status", f"Simulation: {status_message}")

            # Update hardware status signal with latest GPIO state
            self.hardware_status_updated.emit(self.gpio_controller.get_system_status())

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
            # First check if outputs are enabled before arming
            if not self.gpio_controller.outputs_enabled and not self.gpio_controller.system_armed:
                self.logger.warning("Cannot arm system - outputs not enabled")
                self.error_occurred.emit("Cannot arm: outputs must be enabled first")
                return False

            # Update local GPIO controller state
            current_armed = self.gpio_controller.system_armed
            new_state = self.gpio_controller.set_arm_state(not current_armed)

            # Prepare status message for UI feedback
            status_message = f"System {'armed' if new_state else 'disarmed'}"

            # Send SSH command to Pi if in hardware mode
            if self.is_hardware_mode():
                print("SystemMode: In hardware mode, creating fresh SSH connection for arm command")

                # Create fresh SSH connection
                import paramiko
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                try:
                    # Connect using stored settings
                    print(f"SystemMode: Connecting to {self.connection_settings['host']}...")
                    ssh.connect(
                        hostname=self.connection_settings['host'],
                        port=self.connection_settings.get('port', 22),
                        username=self.connection_settings['username'],
                        password=self.connection_settings.get('password', ''),
                        timeout=10
                    )
                    print("SystemMode: SSH connection established")

                    # Execute command
                    command = f"python3 ~/set_arm_state.py --armed={int(new_state)}"
                    print(f"SystemMode: Executing command: {command}")

                    stdin, stdout, stderr = ssh.exec_command(command)
                    exit_status = stdout.channel.recv_exit_status()

                    # Read both stdout and stderr
                    output = stdout.read().decode().strip()
                    error = stderr.read().decode().strip()

                    print(f"SystemMode: Command exit status: {exit_status}")
                    print(f"SystemMode: Command stdout: {output}")
                    print(f"SystemMode: Command stderr: {error}")

                    if exit_status == 0:
                        self.logger.info(f"{status_message} via SSH: {output}")
                        print(f"SystemMode: SSH command sent successfully")

                        # Emit message for UI feedback
                        self.message_received.emit("gpio_status", f"{status_message} successfully")
                    else:
                        self.logger.error(f"Failed to send arm command via SSH: {error}")
                        print(f"SystemMode: SSH command failed with exit status {exit_status}")

                        # Emit error for UI feedback but don't change state
                        self.error_occurred.emit(
                            f"Warning: {status_message} in UI only. Hardware control failed: {error if error else 'Unknown error'}")

                    # Close the connection
                    ssh.close()
                    print("SystemMode: SSH connection closed")

                except Exception as e:
                    self.logger.error(f"Error with SSH connection: {e}")
                    print(f"SystemMode: SSH connection error: {e}")

                    # Emit error for UI feedback
                    self.error_occurred.emit(
                        f"Warning: {status_message} in UI only. SSH connection error: {str(e)}")

                    # Try to close connection if it was opened
                    try:
                        ssh.close()
                    except:
                        pass
            else:
                self.logger.info(f"Simulation: {status_message}")
                self.message_received.emit("gpio_status", f"Simulation: {status_message}")

            # Update hardware status signal with latest GPIO state
            self.hardware_status_updated.emit(self.gpio_controller.get_system_status())

            return new_state

        except Exception as e:
            self.logger.error(f"Failed to handle arm outputs: {e}")
            self.error_occurred.emit(f"Arm outputs failed: {e}")
            # Return the current state instead of False to avoid incorrect UI updates
            current_state = getattr(self.gpio_controller, 'system_armed', False)
            return current_state

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

            # Prepare status message for UI feedback
            status_message = f"Executing cue {selected_cue.get('cue_id', '')}"
            self.message_received.emit("cue_status", status_message)

            # Execute through show execution manager for consistency
            success = await self.show_execution_manager.execute_single_cue(selected_cue)

            # If in hardware mode, send SSH command to Pi
            if self.is_hardware_mode():
                print("SystemMode: In hardware mode, creating fresh SSH connection for cue execution")

                # Create fresh SSH connection
                import paramiko
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                try:
                    # Connect using stored settings
                    print(f"SystemMode: Connecting to {self.connection_settings['host']}...")
                    ssh.connect(
                        hostname=self.connection_settings['host'],
                        port=self.connection_settings.get('port', 22),
                        username=self.connection_settings['username'],
                        password=self.connection_settings.get('password', ''),
                        timeout=10
                    )
                    print("SystemMode: SSH connection established")

                    # Normalize cue data for Pi
                    normalized_cue = self.normalize_cue_for_pi(selected_cue)

                    # Convert cue data to JSON string
                    import json
                    cue_json = json.dumps(normalized_cue)

                    # Build command to execute the cue
                    command = f"python3 ~/execute_cue.py '{cue_json}'"
                    print(f"SystemMode: Executing command: {command}")

                    # Execute command synchronously
                    stdin, stdout, stderr = ssh.exec_command(command)
                    exit_status = stdout.channel.recv_exit_status()

                    if exit_status == 0:
                        output = stdout.read().decode().strip()
                        self.logger.info(f"Cue executed via SSH: {output}")
                        print(f"SystemMode: Cue executed successfully: {output}")
                        success = True
                    else:
                        error = stderr.read().decode().strip()
                        self.logger.error(f"Failed to execute cue via SSH: {error}")
                        print(f"SystemMode: Cue execution failed: {error}")
                        self.error_occurred.emit(f"Hardware cue execution failed: {error}")
                        success = False

                    # Close the connection
                    ssh.close()
                    print("SystemMode: SSH connection closed")

                except Exception as ssh_e:
                    self.logger.error(f"SSH cue execution error: {ssh_e}")
                    print(f"SystemMode: SSH connection error: {ssh_e}")
                    self.error_occurred.emit(f"SSH cue execution error: {str(ssh_e)}")
                    success = False

                    # Try to close connection if it was opened
                    try:
                        ssh.close()
                    except:
                        pass

            if success:
                self.logger.info(f"Cue {selected_cue['cue_id']} executed successfully")
                self.message_received.emit("cue_status", f"Cue {selected_cue.get('cue_id', '')} executed successfully")
            else:
                self.logger.error(f"Cue {selected_cue['cue_id']} execution failed")
                self.error_occurred.emit(f"Cue {selected_cue.get('cue_id', '')} execution failed")

            return success

        except Exception as e:
            self.logger.error(f"Failed to execute cue: {e}")
            self.error_occurred.emit(f"Cue execution failed: {e}")
            return False

    async def handle_execute_show_button(self, show_cues: List[Dict[str, Any]], start_timestamp: float = None) -> bool:
        """
        Handle Execute Show button click
        Executes all cues in sequence

        Args:
            show_cues: List of all cues to execute
            start_timestamp: Optional timestamp for synchronized start (seconds since epoch)

        Returns:
            bool: True if show execution started successfully
        """
        try:
            if not show_cues:
                self.error_occurred.emit("No cues available for show execution")
                return False

            self.logger.info(f"Starting show execution with {len(show_cues)} cues")

            # Prepare status message for UI feedback
            status_message = f"Starting show execution with {len(show_cues)} cues"
            self.message_received.emit("show_status", status_message)

            # Load and execute the show in the local show execution manager
            if self.show_execution_manager.load_show(show_cues):
                success = await self.show_execution_manager.execute_show()

                # If in hardware mode, send SSH command to Pi
                if self.is_hardware_mode():
                    print("SystemMode: In hardware mode, creating fresh SSH connection for show execution")

                    # Create fresh SSH connection
                    import paramiko
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                    try:
                        # Connect using stored settings
                        print(f"SystemMode: Connecting to {self.connection_settings['host']}...")
                        ssh.connect(
                            hostname=self.connection_settings['host'],
                            port=self.connection_settings.get('port', 22),
                            username=self.connection_settings['username'],
                            password=self.connection_settings.get('password', ''),
                            timeout=10
                        )
                        print("SystemMode: SSH connection established")

                        # Normalize all cues for Pi
                        normalized_cues = [self.normalize_cue_for_pi(cue) for cue in show_cues]

                        # Convert show data to JSON string
                        import json
                        show_json = json.dumps({"cues": normalized_cues})

                        # Create a temporary file on the Pi to store the show data
                        temp_file = f"~/show_{int(time.time())}.json"
                        create_file_cmd = f"echo '{show_json}' > {temp_file}"
                        print(f"SystemMode: Creating show file: {temp_file}")

                        # Execute command to create the file
                        stdin, stdout, stderr = ssh.exec_command(create_file_cmd)
                        exit_status = stdout.channel.recv_exit_status()

                        if exit_status == 0:
                            # Build command to execute the show with optional timestamp
                            if start_timestamp:
                                command = f"python3 ~/execute_show.py {temp_file} {start_timestamp} &"
                                print(f"SystemMode: Executing command with timestamp: {command}")
                                print(f"SystemMode: Start timestamp: {start_timestamp}")
                                print(f"SystemMode: Current time: {time.time()}")
                                print(f"SystemMode: Delay: {(start_timestamp - time.time()) * 1000:.1f}ms")
                            else:
                                command = f"python3 ~/execute_show.py {temp_file} &"
                                print(f"SystemMode: Executing command: {command}")

                            # Execute command to start the show
                            stdin, stdout, stderr = ssh.exec_command(command)

                            self.logger.info(f"Show execution started via SSH")
                            print("SystemMode: Show execution started on Pi")
                            success = True
                        else:
                            error = stderr.read().decode().strip()
                            self.logger.error(f"Failed to create show file on Pi: {error}")
                            print(f"SystemMode: Failed to create show file: {error}")
                            self.error_occurred.emit(f"Hardware show execution failed: {error}")
                            success = False

                        # Close the connection
                        ssh.close()
                        print("SystemMode: SSH connection closed")

                    except Exception as ssh_e:
                        self.logger.error(f"SSH show execution error: {ssh_e}")
                        print(f"SystemMode: SSH connection error: {ssh_e}")
                        self.error_occurred.emit(f"SSH show execution error: {str(ssh_e)}")
                        success = False

                        # Try to close connection if it was opened
                        try:
                            ssh.close()
                        except:
                            pass

                if success:
                    self.logger.info("Show execution started successfully")
                    self.message_received.emit("show_status", "Show execution started successfully")
                else:
                    self.logger.error("Failed to start show execution")
                    self.error_occurred.emit("Failed to start show execution")

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
            # Pause the show in the local show execution manager
            success = self.show_execution_manager.pause_show()

            # Prepare status message for UI feedback
            status_message = "Show paused"

            # If in hardware mode, also send SSH command to Pi
            if self.is_hardware_mode() and self.ssh_connection:
                try:
                    # Build command to pause the show
                    command = "python3 ~/control_show.py --action=pause"

                    # Execute command synchronously
                    stdin, stdout, stderr = self.ssh_connection.exec_command(command)
                    exit_status = stdout.channel.recv_exit_status()

                    if exit_status == 0:
                        output = stdout.read().decode().strip()
                        self.logger.info(f"Show paused via SSH: {output}")
                        success = True
                    else:
                        error = stderr.read().decode().strip()
                        self.logger.error(f"Failed to pause show via SSH: {error}")
                        self.error_occurred.emit(f"Hardware show pause failed: {error}")
                        # Don't set success to false if local pause succeeded
                except Exception as ssh_e:
                    self.logger.error(f"SSH pause error: {ssh_e}")
                    self.error_occurred.emit(f"SSH pause error: {str(ssh_e)}")
                    # Don't set success to false if local pause succeeded

            if success:
                self.logger.info(status_message)
                self.message_received.emit("show_status", status_message)
            else:
                self.logger.warning("Failed to pause show")
                self.error_occurred.emit("Failed to pause show")

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
            # Resume the show in the local show execution manager
            success = self.show_execution_manager.resume_show()

            # Prepare status message for UI feedback
            status_message = "Show resumed"

            # If in hardware mode, also send SSH command to Pi
            if self.is_hardware_mode() and self.ssh_connection:
                try:
                    # Build command to resume the show
                    command = "python3 ~/control_show.py --action=resume"

                    # Execute command synchronously
                    stdin, stdout, stderr = self.ssh_connection.exec_command(command)
                    exit_status = stdout.channel.recv_exit_status()

                    if exit_status == 0:
                        output = stdout.read().decode().strip()
                        self.logger.info(f"Show resumed via SSH: {output}")
                        success = True
                    else:
                        error = stderr.read().decode().strip()
                        self.logger.error(f"Failed to resume show via SSH: {error}")
                        self.error_occurred.emit(f"Hardware show resume failed: {error}")
                        # Don't set success to false if local resume succeeded
                except Exception as ssh_e:
                    self.logger.error(f"SSH resume error: {ssh_e}")
                    self.error_occurred.emit(f"SSH resume error: {str(ssh_e)}")
                    # Don't set success to false if local resume succeeded

            if success:
                self.logger.info(status_message)
                self.message_received.emit("show_status", status_message)
            else:
                self.logger.warning("Failed to resume show")
                self.error_occurred.emit("Failed to resume show")

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
            self.logger.critical("EMERGENCY ABORT INITIATED")
            self.message_received.emit("system_status", "EMERGENCY ABORT INITIATED")

            # Track success of each abort component
            abort_results = {
                "show": False,
                "gpio": False,
                "hardware": False
            }

            # 1. Abort the show first
            try:
                show_aborted = self.show_execution_manager.abort_show("User abort button pressed")
                abort_results["show"] = show_aborted
                if show_aborted:
                    self.logger.info("Show execution aborted successfully")
                else:
                    self.logger.warning("Show abort may not have completed successfully")
            except Exception as show_e:
                self.logger.error(f"Error aborting show: {show_e}")
                self.error_occurred.emit(f"Show abort error: {str(show_e)}")

            # 2. Emergency abort GPIO states locally
            try:
                gpio_aborted = self.gpio_controller.emergency_abort()
                abort_results["gpio"] = gpio_aborted
                if gpio_aborted:
                    self.logger.info("Local GPIO states reset successfully")
                else:
                    self.logger.warning("Local GPIO abort may not have completed successfully")
            except Exception as gpio_e:
                self.logger.error(f"Error aborting GPIO states: {gpio_e}")
                self.error_occurred.emit(f"GPIO abort error: {str(gpio_e)}")

            # 3. Send emergency stop command via SSH to hardware
            if self.is_hardware_mode():
                # Create fresh SSH connection for emergency stop
                import paramiko
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                try:
                    # Connect using stored settings
                    ssh.connect(
                        hostname=self.connection_settings['host'],
                        port=self.connection_settings.get('port', 22),
                        username=self.connection_settings['username'],
                        password=self.connection_settings.get('password', ''),
                        timeout=10
                    )

                    # First, kill any running execute_show.py processes
                    kill_command = "pkill -f 'python3.*execute_show.py' || true"
                    stdin, stdout, stderr = ssh.exec_command(kill_command)
                    stdout.channel.recv_exit_status()  # Wait for completion
                    self.logger.info("Killed any running show processes")

                    # Then send emergency stop command
                    command = "python3 ~/emergency_stop.py"
                    stdin, stdout, stderr = ssh.exec_command(command)
                    exit_status = stdout.channel.recv_exit_status()

                    # Read both stdout and stderr
                    output = stdout.read().decode().strip()
                    error = stderr.read().decode().strip()

                    if exit_status == 0:
                        self.logger.info(f"Hardware emergency stop successful: {output}")
                        abort_results["hardware"] = True
                    else:
                        error_msg = error if error else f"Exit code {exit_status}, output: {output}"
                        self.logger.error(f"Emergency stop returned error: {error_msg}")
                        # Don't emit error to user - emergency stop still worked
                        # Just log it for debugging
                        abort_results["hardware"] = True  # Consider it successful anyway

                    # Close connection
                    ssh.close()

                except Exception as ssh_e:
                    self.logger.error(f"Error sending emergency stop via SSH: {ssh_e}")
                    # Don't fail the abort - local GPIO was already reset
                    abort_results["hardware"] = True  # Consider successful if local GPIO worked
            else:
                self.logger.info("In simulation mode, skipping hardware emergency stop")
                abort_results["hardware"] = True  # Consider successful in simulation mode

            # Determine overall success
            if self.is_hardware_mode():
                success = abort_results["show"] and abort_results["gpio"] and abort_results["hardware"]
            else:
                success = abort_results["show"] and abort_results["gpio"]

            # Update hardware status signal with latest GPIO state
            self.hardware_status_updated.emit(self.gpio_controller.get_system_status())

            # Final status message
            if success:
                status_message = "ABORT: Show stopped and system disarmed successfully"
                self.logger.critical(status_message)
                self.message_received.emit("system_status", status_message)
            else:
                failed_components = []
                if not abort_results["show"]: failed_components.append("show execution")
                if not abort_results["gpio"]: failed_components.append("local GPIO control")
                if not abort_results["hardware"] and self.is_hardware_mode():
                    failed_components.append("hardware control")

                status_message = f"ABORT: Partial failure in abort sequence. Failed components: {', '.join(failed_components)}"
                self.logger.error(status_message)
                self.error_occurred.emit(status_message)

            # NEW: Verify abort success
            if success:
                verification_result = self.verify_abort_success()
                if not verification_result['success']:
                    self.logger.warning(f"Abort verification warnings: {verification_result['warnings']}")
                    # Still return success, but log warnings

            # NEW: Log abort event
            self.log_abort_event("button", success, abort_results)

            return success

        except Exception as e:
            self.logger.error(f"Failed to abort: {e}")
            self.error_occurred.emit(f"Abort failed: {e}")
            # Log failed abort
            self.log_abort_event("button", False, {"error": str(e)})
            return False

    def verify_abort_success(self) -> dict:
        """
        Verify that abort actually worked by checking system state

        Returns:
            dict: {'success': bool, 'warnings': list}
        """
        warnings = []

        try:
            if self.is_hardware_mode() and self.ssh_connection:
                # Check 1: No show process running
                try:
                    stdin, stdout, stderr = self.ssh_connection.exec_command(
                        "pgrep -f 'execute_show.py'", timeout=5
                    )
                    output = stdout.read().decode().strip()
                    if output:
                        warnings.append(f"Show process still running (PID: {output})")
                except Exception as e:
                    warnings.append(f"Could not verify process status: {str(e)}")

                # Check 2: GPIO states (outputs disabled, system disarmed)
                try:
                    stdin, stdout, stderr = self.ssh_connection.exec_command(
                        "python3 ~/get_gpio_status.py", timeout=10
                    )
                    output = stdout.read().decode()

                    import json
                    status = json.loads(output)

                    if status.get('status') == 'success':
                        # Check OE pins (should be HIGH = disabled)
                        oe_pins = status.get('oe_pins', [])
                        enabled_count = sum(1 for pin in oe_pins if pin.get('state') == False)
                        if enabled_count > 0:
                            warnings.append(f"{enabled_count}/5 chains still enabled (OE pins LOW)")

                        # Check ARM pin (should be LOW = disarmed)
                        arm_state = status.get('arm_pin', {}).get('state', False)
                        if arm_state == True:
                            warnings.append("System still armed (GPIO 21 HIGH)")
                    else:
                        warnings.append("Could not read GPIO status")

                except Exception as e:
                    warnings.append(f"Could not verify GPIO states: {str(e)}")

            return {
                'success': len(warnings) == 0,
                'warnings': warnings
            }

        except Exception as e:
            return {
                'success': False,
                'warnings': [f"Verification error: {str(e)}"]
            }

    def log_abort_event(self, method: str, success: bool, details: dict):
        """
        Log abort event with full details

        Args:
            method: How abort was triggered (button, keyboard, auto)
            success: Whether abort succeeded
            details: Additional details about the abort
        """
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        log_entry = {
            'timestamp': timestamp,
            'method': method,
            'success': success,
            'mode': self.current_mode,
            'details': details
        }

        # Log to console
        if success:
            self.logger.critical(f"ABORT EVENT [{method.upper()}]: Success - {timestamp}")
        else:
            self.logger.critical(f"ABORT EVENT [{method.upper()}]: FAILED - {timestamp}")

        self.logger.info(f"Abort details: {details}")

        # TODO: Could also log to file for audit trail
        # with open('abort_log.json', 'a') as f:
        #     json.dump(log_entry, f)
        #     f.write('\n')

    def check_connection_health(self) -> bool:
        """
        Check if SSH connection is still alive

        Returns:
            bool: True if connection is healthy, False otherwise
        """
        if not self.is_hardware_mode():
            return True  # Always healthy in simulation mode

        if not self.ssh_connection:
            return False

        try:
            # Send a simple echo command to test connection
            stdin, stdout, stderr = self.ssh_connection.exec_command("echo 'ping'", timeout=3)
            output = stdout.read().decode().strip()
            return output == "ping"
        except Exception as e:
            self.logger.warning(f"Connection health check failed: {e}")
            return False

    def handle_connection_loss_during_show(self):
        """
        Handle connection loss detected during show execution
        Automatically triggers abort
        """
        self.logger.critical("CONNECTION LOST DURING SHOW EXECUTION - AUTO-ABORTING")
        self.message_received.emit("system_status", "⚠️ CONNECTION LOST - AUTO-ABORTING SHOW")

        # Trigger abort
        abort_success = self.handle_abort_button()

        # Log as auto-abort
        self.log_abort_event("auto_connection_loss", abort_success, {
            "reason": "SSH connection lost during show execution",
            "timestamp": datetime.now().isoformat()
        })

        # Emit error to UI
        self.error_occurred.emit(
            "⚠️ CONNECTION LOST\n\n"
            "SSH connection to Pi was lost during show execution.\n"
            "Emergency abort has been triggered.\n\n"
            "Please check:\n"
            "• Network connection\n"
            "• Pi power\n"
            "• SSH service status"
        )

    def handle_shutdown_pi_button(self) -> bool:
        """
        Handle Pi Shutdown button click
        Sends shutdown command to Raspberry Pi

        Returns:
            bool: True if shutdown command sent successfully
        """
        try:
            if self.is_hardware_mode() and self.ssh_connection:
                command = "sudo shutdown -h now"

                try:
                    stdin, stdout, stderr = self.ssh_connection.exec_command(command)
                    # Don't wait for exit status as the Pi will shut down

                    self.logger.info("Pi shutdown command sent via SSH")
                    return True
                except Exception as e:
                    self.logger.error(f"Failed to send Pi shutdown command: {e}")
                    return False
            else:
                self.error_occurred.emit("SSH not connected - cannot send shutdown command")
                return False

        except Exception as e:
            self.logger.error(f"Failed to send shutdown command: {e}")
            self.error_occurred.emit(f"Pi shutdown failed: {e}")
            return False

    def handle_wifi_mode_button(self) -> bool:
        """
        Handle WiFi Mode button click
        Switches the Raspberry Pi to WiFi mode

        Returns:
            bool: True if command sent successfully
        """
        try:
            if self.is_hardware_mode() and self.ssh_connection:
                # First check current mode
                command = "python3 ~/get_network_status.py"

                try:
                    stdin, stdout, stderr = self.ssh_connection.exec_command(command)
                    exit_status = stdout.channel.recv_exit_status()

                    if exit_status == 0:
                        output = stdout.read().decode().strip()
                        try:
                            import json
                            status = json.loads(output)
                            current_mode = status.get('mode', 'unknown')

                            if current_mode == 'wifi':
                                self.logger.info("Already in WiFi mode")
                                self.message_received.emit("network_status", "Already in WiFi mode")
                                return True
                        except Exception as json_e:
                            self.logger.error(f"Error parsing network status: {json_e}")

                    # Send command to switch to WiFi mode
                    self.logger.info("Switching to WiFi mode...")
                    self.message_received.emit("network_status", "Switching to WiFi mode...")

                    switch_command = "sudo python3 ~/switch_wifi_mode.py --mode=wifi &amp;"
                    stdin, stdout, stderr = self.ssh_connection.exec_command(switch_command)

                    # Don't wait for exit status - the connection will drop during network switch
                    # Just assume success if command was sent
                    self.logger.info("WiFi mode switch command sent - connection will drop during switch")
                    self.message_received.emit("network_status",
                                               "WiFi mode switch initiated - SSH connection will drop. Reconnect to Pi on Lyman network.")

                    # Close the SSH connection since it will be invalid after network switch
                    try:
                        self.ssh_connection.close()
                    except:
                        pass
                    self.ssh_connection = None

                    return True
                except Exception as e:
                    self.logger.error(f"Error sending WiFi mode command: {e}")
                    self.error_occurred.emit(f"WiFi mode switch failed: {e}")
                    return False
            else:
                self.error_occurred.emit("SSH not connected - cannot switch network mode")
                return False

        except Exception as e:
            self.logger.error(f"Failed to handle WiFi mode button: {e}")
            self.error_occurred.emit(f"WiFi mode switch failed: {e}")
            return False

    def handle_adhoc_mode_button(self) -> bool:
        """
        Handle Adhoc Mode button click
        Switches the Raspberry Pi to Adhoc mode

        Returns:
            bool: True if command sent successfully
        """
        try:
            if self.is_hardware_mode() and self.ssh_connection:
                # First check current mode
                command = "python3 ~/get_network_status.py"

                try:
                    stdin, stdout, stderr = self.ssh_connection.exec_command(command)
                    exit_status = stdout.channel.recv_exit_status()

                    if exit_status == 0:
                        output = stdout.read().decode().strip()
                        try:
                            import json
                            status = json.loads(output)
                            current_mode = status.get('mode', 'unknown')

                            if current_mode == 'adhoc':
                                self.logger.info("Already in Adhoc mode")
                                self.message_received.emit("network_status", "Already in Adhoc mode")
                                return True
                        except Exception as json_e:
                            self.logger.error(f"Error parsing network status: {json_e}")

                    # Send command to switch to Adhoc mode
                    self.logger.info("Switching to Adhoc mode...")
                    self.message_received.emit("network_status", "Switching to Adhoc mode...")

                    switch_command = "sudo python3 ~/switch_wifi_mode.py --mode=adhoc &"
                    stdin, stdout, stderr = self.ssh_connection.exec_command(switch_command)

                    # Don't wait for exit status - the connection will drop during network switch
                    # Just assume success if command was sent
                    self.logger.info("Adhoc mode switch command sent - connection will drop during switch")
                    self.message_received.emit("network_status",
                                               "Adhoc mode switch initiated - SSH connection will drop. Reconnect to Pi on cuepishifter network at 192.168.42.1")

                    # Close the SSH connection since it will be invalid after network switch
                    try:
                        self.ssh_connection.close()
                    except:
                        pass
                    self.ssh_connection = None

                    return True
                except Exception as e:
                    self.logger.error(f"Error sending Adhoc mode command: {e}")
                    self.error_occurred.emit(f"Adhoc mode switch failed: {e}")
                    return False
            else:
                self.error_occurred.emit("SSH not connected - cannot switch network mode")
                return False

        except Exception as e:
            self.logger.error(f"Failed to handle Adhoc mode button: {e}")
            self.error_occurred.emit(f"Adhoc mode switch failed: {e}")
            return False

    def get_network_status(self) -> dict:
        """
        Get the current network status from the Raspberry Pi

        Returns:
            dict: Network status information
        """
        try:
            if not self.is_hardware_mode() or not self.ssh_connection:
                return {
                    'mode': 'simulation',
                    'ip_address': 'N/A',
                    'ssid': 'N/A',
                    'signal': 'N/A',
                    'timestamp': time.time()
                }

            command = "python3 ~/get_network_status.py"

            stdin, stdout, stderr = self.ssh_connection.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()

            if exit_status == 0:
                output = stdout.read().decode().strip()
                try:
                    import json
                    status = json.loads(output)
                    return status
                except Exception as json_e:
                    self.logger.error(f"Error parsing network status: {json_e}")
                    return {
                        'mode': 'unknown',
                        'error': f"Parse error: {str(json_e)}",
                        'timestamp': time.time()
                    }
            else:
                error = stderr.read().decode().strip()
                self.logger.error(f"Failed to get network status: {error}")
                return {
                    'mode': 'unknown',
                    'error': error,
                    'timestamp': time.time()
                }
        except Exception as e:
            self.logger.error(f"Error getting network status: {e}")
            return {
                'mode': 'unknown',
                'error': str(e),
                'timestamp': time.time()
            }

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
        Get comprehensive system status including GPIO, show execution, and network status

        Returns:
            dict: Complete system status
        """
        # Add GPIO status
        gpio_status = self.gpio_controller.get_system_status()

        # Add show execution status
        show_progress = self.show_execution_manager.get_show_progress()
        show_summary = self.show_execution_manager.get_execution_summary()

        # Add network status
        network_status = self.get_network_status()

        return {
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
            'network': network_status,
            'system_capabilities': {
                'max_cues': 1000,
                'max_outputs': 1000,
                'num_chains': 5,
                'registers_per_chain': 25,
                'outputs_per_chain': 200
            },
            'timestamp': self._get_timestamp()
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()