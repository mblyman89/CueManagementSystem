"""
MQTT Integration Module for Firework Control System

This module provides integration between the existing firework control system
and the new professional MQTT implementation. It handles:

- Integration with existing SystemMode controller
- Backward compatibility with current codebase
- Seamless transition between simulation and hardware modes
- Event handling and signal routing
- Configuration management
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from PySide6.QtCore import QObject, Signal

from mqtt_client import MQTTClient, ConnectionConfig, ConnectionState
from controllers.hardware_controller import HardwareController, HardwareState
from hardware.shift_register_formatter import ShiftRegisterFormatter, ShiftRegisterConfig


class MQTTIntegration(QObject):
    """
    Integration layer between existing system and new MQTT implementation

    This class provides a bridge between the existing SystemMode controller
    and the new professional MQTT system, ensuring backward compatibility
    while adding advanced features.
    """

    # Signals for integration with existing system
    connection_status_changed = Signal(bool, str)  # connected, status_message
    hardware_command_sent = Signal(str, dict)  # command_type, data
    hardware_response_received = Signal(str, bool, str)  # command_id, success, message
    emergency_stop_triggered = Signal(str)  # reason

    def __init__(self, system_mode_controller=None):
        super().__init__()

        self.system_mode = system_mode_controller
        self.logger = self._setup_logging()

        # Core components
        self.hardware_controller: Optional[HardwareController] = None
        self.mqtt_client: Optional[MQTTClient] = None
        self.shift_formatter: Optional[ShiftRegisterFormatter] = None

        # Current configuration
        self.current_config: Optional[Dict[str, Any]] = None
        self.is_hardware_mode = False

        self.logger.info("MQTT Integration initialized")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for integration module"""
        logger = logging.getLogger(f"MQTTIntegration_{id(self)}")
        logger.setLevel(logging.DEBUG)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def initialize_mqtt_system(self, config: Dict[str, Any]) -> bool:
        """
        Initialize the MQTT system with given configuration

        Args:
            config: Complete configuration dictionary

        Returns:
            bool: True if initialization successful
        """
        try:
            self.current_config = config
            self.is_hardware_mode = config.get("mode", "simulation") == "hardware"

            if not self.is_hardware_mode:
                self.logger.info("Simulation mode - MQTT system not initialized")
                return True

            # Create hardware controller
            self.hardware_controller = HardwareController(self.system_mode)

            # Connect hardware controller signals
            self._connect_hardware_signals()

            # Set connection parameters
            conn_config = config.get("connection", {})
            self.hardware_controller.set_connection_params(
                host=conn_config.get("host", "raspberrypi.local"),
                port=conn_config.get("port", 8883),
                username=conn_config.get("username"),
                password=conn_config.get("password")
            )

            self.logger.info("MQTT system initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize MQTT system: {e}")
            return False

    def _connect_hardware_signals(self):
        """Connect hardware controller signals to integration layer"""
        if not self.hardware_controller:
            return

        self.hardware_controller.hardware_state_changed.connect(self._on_hardware_state_changed)
        self.hardware_controller.command_acknowledged.connect(self._on_command_acknowledged)
        self.hardware_controller.emergency_stop_activated.connect(self._on_emergency_stop)
        self.hardware_controller.error_occurred.connect(self._on_hardware_error)

    def connect_to_hardware(self) -> tuple[bool, str]:
        """
        Connect to hardware (for compatibility with existing SystemMode)

        Returns:
            tuple: (success, message)
        """
        if not self.is_hardware_mode:
            return True, "Simulation mode - no hardware connection needed"

        if not self.hardware_controller:
            return False, "Hardware controller not initialized"

        try:
            success = self.hardware_controller.connect()
            if success:
                return True, "Hardware connection initiated"
            else:
                return False, "Failed to initiate hardware connection"

        except Exception as e:
            self.logger.error(f"Hardware connection failed: {e}")
            return False, f"Connection error: {e}"

    def disconnect_from_hardware(self):
        """Disconnect from hardware"""
        if self.hardware_controller:
            self.hardware_controller.disconnect()
            self.logger.info("Hardware disconnected")

    def is_connected(self) -> bool:
        """Check if connected to hardware"""
        if not self.is_hardware_mode:
            return True  # Always "connected" in simulation mode

        return self.hardware_controller.is_hardware_connected() if self.hardware_controller else False

    async def send_cue_command(self, cue_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Send cue command to hardware

        Args:
            cue_data: Cue data dictionary

        Returns:
            tuple: (success, message)
        """
        if not self.is_hardware_mode:
            # Simulate command in simulation mode
            self.logger.info(f"[SIMULATION] Cue command: {cue_data.get('cue_number', 'unknown')}")
            return True, "Simulated cue execution"

        if not self.hardware_controller:
            return False, "Hardware controller not available"

        try:
            success, message = await self.hardware_controller.send_cue(cue_data)

            # Emit signal for integration
            if success:
                self.hardware_command_sent.emit("cue_execute", cue_data)

            return success, message

        except Exception as e:
            self.logger.error(f"Failed to send cue command: {e}")
            return False, f"Command error: {e}"

    async def send_emergency_stop(self, reason: str = "Manual activation") -> bool:
        """
        Send emergency stop command

        Args:
            reason: Reason for emergency stop

        Returns:
            bool: True if emergency stop sent successfully
        """
        if not self.is_hardware_mode:
            self.logger.warning(f"[SIMULATION] Emergency stop: {reason}")
            self.emergency_stop_triggered.emit(reason)
            return True

        if not self.hardware_controller:
            return False

        try:
            success = self.hardware_controller.emergency_stop(reason)
            if success:
                self.emergency_stop_triggered.emit(reason)
            return success

        except Exception as e:
            self.logger.error(f"Failed to send emergency stop: {e}")
            return False

    def get_hardware_status(self) -> Dict[str, Any]:
        """
        Get current hardware status

        Returns:
            dict: Hardware status information
        """
        if not self.is_hardware_mode:
            return {
                "mode": "simulation",
                "connected": True,
                "status": "Simulation mode active"
            }

        if not self.hardware_controller:
            return {
                "mode": "hardware",
                "connected": False,
                "status": "Hardware controller not initialized"
            }

        try:
            hw_status = self.hardware_controller.get_hardware_status()
            connection_info = self.hardware_controller.get_connection_info()

            return {
                "mode": "hardware",
                "connected": self.hardware_controller.is_hardware_connected(),
                "state": hw_status.state.value,
                "voltage": hw_status.voltage,
                "temperature": hw_status.temperature,
                "active_outputs": hw_status.active_outputs,
                "error_count": hw_status.error_count,
                "connection_info": connection_info,
                "emergency_stop_active": self.hardware_controller.is_emergency_stop_active()
            }

        except Exception as e:
            self.logger.error(f"Failed to get hardware status: {e}")
            return {
                "mode": "hardware",
                "connected": False,
                "status": f"Status error: {e}"
            }

    def test_hardware_connection(self) -> tuple[bool, str]:
        """
        Test hardware connection

        Returns:
            tuple: (success, message)
        """
        if not self.is_hardware_mode:
            return True, "Simulation mode - no hardware to test"

        if not self.hardware_controller:
            return False, "Hardware controller not available"

        # For now, just check if we're connected
        # In the future, this could send a test command
        if self.hardware_controller.is_hardware_connected():
            return True, "Hardware connection is active"
        else:
            return False, "Hardware not connected"

    def send_test_pattern(self, pattern_type: str = "sequential") -> bool:
        """
        Send test pattern to hardware

        Args:
            pattern_type: Type of test pattern

        Returns:
            bool: True if test pattern sent successfully
        """
        if not self.is_hardware_mode:
            self.logger.info(f"[SIMULATION] Test pattern: {pattern_type}")
            return True

        if not self.hardware_controller:
            return False

        return self.hardware_controller.send_test_pattern(pattern_type)

    # Event handlers for hardware controller signals
    def _on_hardware_state_changed(self, state: HardwareState):
        """Handle hardware state changes"""
        connected = state == HardwareState.CONNECTED
        status_message = f"Hardware state: {state.value}"

        self.connection_status_changed.emit(connected, status_message)
        self.logger.info(f"Hardware state changed: {state.value}")

    def _on_command_acknowledged(self, command_id: str, success: bool, message: str):
        """Handle command acknowledgments"""
        self.hardware_response_received.emit(command_id, success, message)

        if success:
            self.logger.info(f"Command acknowledged: {command_id}")
        else:
            self.logger.warning(f"Command failed: {command_id} - {message}")

    def _on_emergency_stop(self, reason: str):
        """Handle emergency stop activation"""
        self.emergency_stop_triggered.emit(reason)
        self.logger.critical(f"Emergency stop activated: {reason}")

    def _on_hardware_error(self, error_type: str, message: str):
        """Handle hardware errors"""
        self.logger.error(f"Hardware error ({error_type}): {message}")

        # For critical errors, trigger emergency stop
        if error_type in ["SAFETY_VIOLATION", "HARDWARE_FAULT"]:
            asyncio.create_task(self.send_emergency_stop(f"Hardware error: {message}"))

    def get_configuration(self) -> Optional[Dict[str, Any]]:
        """Get current configuration"""
        return self.current_config

    def update_configuration(self, config: Dict[str, Any]) -> bool:
        """
        Update configuration

        Args:
            config: New configuration dictionary

        Returns:
            bool: True if update successful
        """
        try:
            # If mode changed, reinitialize
            old_mode = self.current_config.get("mode") if self.current_config else "simulation"
            new_mode = config.get("mode", "simulation")

            if old_mode != new_mode:
                # Disconnect from current hardware if needed
                if self.hardware_controller:
                    self.hardware_controller.disconnect()

                # Reinitialize with new configuration
                return self.initialize_mqtt_system(config)
            else:
                # Update existing configuration
                self.current_config = config

                # Update hardware controller if in hardware mode
                if self.is_hardware_mode and self.hardware_controller:
                    conn_config = config.get("connection", {})
                    self.hardware_controller.set_connection_params(
                        host=conn_config.get("host", "raspberrypi.local"),
                        port=conn_config.get("port", 8883),
                        username=conn_config.get("username"),
                        password=conn_config.get("password")
                    )

                return True

        except Exception as e:
            self.logger.error(f"Failed to update configuration: {e}")
            return False

    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.hardware_controller:
                self.hardware_controller.disconnect()

            self.logger.info("MQTT integration cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# Utility functions for easy integration
def create_mqtt_integration(system_mode_controller=None) -> MQTTIntegration:
    """
    Create and return an MQTT integration instance

    Args:
        system_mode_controller: Existing SystemMode controller

    Returns:
        MQTTIntegration: Configured integration instance
    """
    return MQTTIntegration(system_mode_controller)


def get_default_mqtt_config() -> Dict[str, Any]:
    """
    Get default MQTT configuration

    Returns:
        dict: Default configuration dictionary
    """
    return {
        "mode": "simulation",
        "connection": {
            "host": "raspberrypi.local",
            "port": 8883,
            "username": "fireworks",
            "password": "",
            "client_id": "",
        },
        "security": {
            "use_ssl": True,
            "ca_cert_path": "",
            "cert_file_path": "",
            "key_file_path": "",
            "insecure": False,
        },
        "mqtt": {
            "default_qos": 2,
            "status_qos": 1,
            "base_topic": "fireworks",
            "command_topic": "commands",
            "status_topic": "status",
            "emergency_topic": "emergency",
            "heartbeat_topic": "heartbeat",
            "keepalive": 60,
            "clean_session": False,
            "reconnect_delay_min": 1.0,
            "reconnect_delay_max": 60.0,
        },
        "hardware": {
            "num_registers": 8,
            "max_simultaneous_outputs": 4,
            "pulse_duration_ms": 100,
            "voltage_check_enabled": True,
            "continuity_check_enabled": True,
        },
        "safety": {
            "emergency_stop_timeout": 5.0,
            "command_timeout": 30.0,
            "heartbeat_interval": 10.0,
            "connection_monitor_enabled": True,
        }
    }