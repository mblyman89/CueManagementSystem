import asyncssh
import logging
from controllers.hardware_controller import HardwareController


class SystemMode:
    """
    Controller for managing system operation mode with support for both SSH and MQTT
    """

    def __init__(self):
        print("Initializing SystemMode")
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
            method (str): Either 'ssh' or 'mqtt'
        """
        if method not in ["ssh", "mqtt"]:
            raise ValueError("Communication method must be either 'ssh' or 'mqtt'")

        self.communication_method = method
        print(f"Communication method set to: {self.communication_method}")

        # Update hardware controller settings if using MQTT
        if method == "mqtt":
            self._update_hardware_controller_settings()

    async def set_mode(self, mode, connection_settings=None):
        """Set the system mode and optional connection settings"""
        print(f"Setting mode to: {mode}")
        if mode not in ["simulation", "hardware"]:
            raise ValueError("Mode must be either 'simulation' or 'hardware'")

        # Close any existing connections when switching modes
        await self.close_connection()

        self.current_mode = mode
        print(f"Mode set to: {self.current_mode}")

        # Update connection settings if provided
        if connection_settings and mode == "hardware":
            print(f"Updating connection settings: {connection_settings}")
            self.connection_settings.update(connection_settings)

            # Update hardware controller settings
            self._update_hardware_controller_settings()

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
        else:  # MQTT
            return await self._connect_via_mqtt()

    async def _connect_via_ssh(self):
        """Connect to the Raspberry Pi via SSH"""
        try:
            if self.ssh_connection is None:
                print(f"Connecting to: {self.connection_settings['host']} via SSH")

                # Create connection with explicit options
                self.ssh_connection = await asyncssh.connect(
                    host=self.connection_settings['host'],
                    port=self.connection_settings['port'],
                    username=self.connection_settings['username'],
                    password=self.connection_settings['password'],
                    known_hosts=None,
                    keepalive_interval=30,
                    keepalive_count_max=5,
                    login_timeout=30
                )
                print("SSH connection established successfully")
            return True, "Successfully connected to Raspberry Pi via SSH"

        except asyncssh.Error as e:
            print(f"SSH connection failed: {str(e)}")
            self.ssh_connection = None
            return False, f"Failed to connect via SSH: {str(e)}"
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
                return True, "Successfully initiated connection to Raspberry Pi via MQTT"
            else:
                print("MQTT connection failed to initiate")
                return False, "Failed to initiate MQTT connection"

        except Exception as e:
            print(f"Unexpected error during MQTT connection: {str(e)}")
            return False, f"Unexpected error during MQTT connection: {str(e)}"

    async def close_connection(self):
        """Close any active connections"""
        # Close SSH connection if it exists
        if self.ssh_connection:
            print("Closing SSH connection")
            self.ssh_connection.close()
            await self.ssh_connection.wait_closed()
            self.ssh_connection = None
            print("SSH connection closed")

        # Disconnect MQTT client if using MQTT
        if self.communication_method == "mqtt":
            print("Disconnecting MQTT client")
            self.hardware_controller.disconnect()
            print("MQTT client disconnected")

    async def execute_command(self, command):
        """Execute a command on the target system"""
        if self.is_simulation_mode():
            print(f"[SIMULATION] Would execute: {command}")
            return True, f"Simulated execution of: {command}"

        # Use the appropriate communication method
        if self.communication_method == "ssh":
            return await self._execute_via_ssh(command)
        else:  # MQTT
            return await self._execute_via_mqtt(command)

    async def _execute_via_ssh(self, command):
        """Execute a command via SSH"""
        if not self.ssh_connection:
            success, message = await self._connect_via_ssh()
            if not success:
                return False, message

        try:
            print(f"Executing command via SSH: {command}")
            result = await self.ssh_connection.run(command)

            if result.exit_status == 0:
                return True, result.stdout
            else:
                return False, f"Command failed: {result.stderr}"

        except asyncssh.Error as e:
            print(f"SSH command execution failed: {str(e)}")
            return False, f"Command execution failed: {str(e)}"

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
        else:  # MQTT
            # For MQTT, use the hardware controller to send the cue
            return await self.hardware_controller.send_cue(cue_data)

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
