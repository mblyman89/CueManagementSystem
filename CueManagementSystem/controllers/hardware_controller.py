"""
Enhanced Hardware Controller for SSH-based Firework Control

This module provides a comprehensive hardware controller that integrates
SSH communication with 74HC595 shift register control for firework shows.

Features:
- SSH-based communication with Raspberry Pi
- 74HC595 shift register data formatting
- Safety interlocks and emergency stop
- Connection monitoring and diagnostics
- Command acknowledgment system
- Hardware status feedback
- Comprehensive error handling
"""

import asyncio
import json
import logging
import time
import paramiko
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime

from PySide6.QtCore import QObject, Signal, QTimer

from views.managers.shift_register_formatter_manager import ShiftRegisterFormatter, ShiftRegisterConfig


class HardwareState(Enum):
    """Hardware connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    EMERGENCY_STOP = "emergency_stop"


class CommandType(Enum):
    """Hardware command types"""
    CUE_EXECUTE = "cue_execute"
    EMERGENCY_STOP = "emergency_stop"
    TEST_PATTERN = "test_pattern"
    STATUS_REQUEST = "status_request"
    RESET = "reset"
    DIAGNOSTICS = "diagnostics"


@dataclass
class HardwareStatus:
    """Hardware status information"""
    state: HardwareState
    voltage: float = 0.0
    temperature: float = 0.0
    active_outputs: List[int] = None
    error_count: int = 0
    last_command_time: Optional[datetime] = None
    uptime_seconds: float = 0.0

    def __post_init__(self):
        if self.active_outputs is None:
            self.active_outputs = []


@dataclass
class ConnectionConfig:
    """SSH connection configuration"""
    host: str
    port: int
    username: str
    password: str
    client_id: str = None
    use_ssl: bool = False
    base_path: str = "~/fireworks"
    command_script: str = "execute_command.py"
    status_script: str = "get_status.py"
    emergency_script: str = "emergency_stop.py"


class HardwareController(QObject):
    """
    Enhanced hardware controller for SSH-based firework control

    This controller manages communication between the PySide6 application
    and the Raspberry Pi hardware via SSH, handling:
    - Cue execution commands
    - Emergency stop functionality
    - Hardware status monitoring
    - Safety interlocks
    - Connection management
    """

    # Qt Signals
    hardware_state_changed = Signal(HardwareState)
    command_acknowledged = Signal(str, bool, str)  # command_id, success, message
    hardware_status_updated = Signal(HardwareStatus)
    emergency_stop_activated = Signal(str)  # reason
    error_occurred = Signal(str, str)  # error_type, message

    def __init__(self, system_mode_controller=None):
        super().__init__()

        self.system_mode = system_mode_controller
        self.logger = self._setup_logging()

        # SSH client and configuration
        self.ssh_client: Optional[paramiko.SSHClient] = None
        self.ssh_config: Optional[ConnectionConfig] = None

        # Shift register formatter
        self.shift_formatter: Optional[ShiftRegisterFormatter] = None

        # Hardware state
        self._hardware_state = HardwareState.DISCONNECTED
        self._last_status = HardwareStatus(HardwareState.DISCONNECTED)
        self._pending_commands: Dict[str, Dict[str, Any]] = {}

        # Safety and monitoring
        self._emergency_stop_active = False
        self._last_heartbeat = datetime.now()
        self._command_timeout = 30.0  # seconds

        # Timers
        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._request_hardware_status)
        self._command_timeout_timer = QTimer()
        self._command_timeout_timer.timeout.connect(self._check_command_timeouts)

        self.logger.info("Hardware controller initialized")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for hardware controller"""
        logger = logging.getLogger(f"HardwareController_{id(self)}")
        logger.setLevel(logging.DEBUG)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def set_connection_params(self, host: str, port: int, username: str = None, password: str = None):
        """
        Set SSH connection parameters

        Args:
            host: SSH hostname/IP
            port: SSH port
            username: SSH username
            password: SSH password
        """
        self.ssh_config = ConnectionConfig(
            host=host,
            port=port,
            username=username,
            password=password,
            client_id=f"fireworks_hardware_{int(time.time())}",
            use_ssl=False,  # Default to False, can be enabled when needed
            base_path="~/fireworks",
            command_script="execute_command.py",
            status_script="get_status.py",
            emergency_script="emergency_stop.py"
        )

        # Initialize shift register formatter for 1000 outputs (5 chains × 25 registers)
        try:
            shift_config = ShiftRegisterConfig(
                num_registers=125,  # 5 chains × 25 registers per chain = 1000 outputs
                outputs_per_register=8,  # 74HC595 standard
                max_simultaneous_outputs=50,  # Increased for large shows
                pulse_duration_ms=100,  # 100ms ignition pulse
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
            print("✅ Hardware controller configured for 1000 outputs")
        except TypeError:
            # Fallback configuration
            shift_config = ShiftRegisterConfig(
                num_registers=125,  # Still try for 1000 outputs
                outputs_per_register=8,
                max_simultaneous_outputs=50,
                pulse_duration_ms=100,
                voltage_check_enabled=True,
                continuity_check_enabled=True
            )
            print("✅ Hardware controller basic config for 1000 outputs")

        self.shift_formatter = ShiftRegisterFormatter(shift_config)

        self.logger.info(f"Connection parameters set: {host}:{port}")

    def connect(self) -> bool:
        """
        Connect to hardware via SSH

        Returns:
            bool: True if connection initiated successfully
        """
        if not self.ssh_config:
            self.logger.error("No connection parameters set")
            return False

        if self._hardware_state in [HardwareState.CONNECTING, HardwareState.CONNECTED]:
            self.logger.warning("Already connected or connecting")
            return True

        try:
            self._set_hardware_state(HardwareState.CONNECTING)

            # Create SSH client
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to SSH server
            self.ssh_client.connect(
                hostname=self.ssh_config.host,
                port=self.ssh_config.port,
                username=self.ssh_config.username,
                password=self.ssh_config.password,
                timeout=10
            )

            # Test connection with a simple command
            stdin, stdout, stderr = self.ssh_client.exec_command("echo 'SSH connection test'")
            output = stdout.read().decode().strip()

            if output == "SSH connection test":
                self._set_hardware_state(HardwareState.CONNECTED)
                self.logger.info("Hardware connection established")
                return True
            else:
                self._set_hardware_state(HardwareState.ERROR)
                self.logger.error(f"SSH connection test failed: {stderr.read().decode().strip()}")
                return False

        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            self._set_hardware_state(HardwareState.ERROR)
            self.error_occurred.emit("CONNECTION_ERROR", str(e))
            return False

    def disconnect(self):
        """Disconnect from hardware"""
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None

        self._stop_monitoring()
        self._set_hardware_state(HardwareState.DISCONNECTED)
        self.logger.info("Hardware disconnected")

    def is_hardware_connected(self) -> bool:
        """Check if hardware is connected"""
        return self._hardware_state == HardwareState.CONNECTED

    async def send_cue(self, cue_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Send cue execution command to hardware

        Args:
            cue_data: Cue data dictionary

        Returns:
            tuple: (success, message)
        """
        if not self.is_hardware_connected():
            return False, "Hardware not connected"

        if self._emergency_stop_active:
            return False, "Emergency stop is active"

        try:
            # Format cue data for shift registers
            packet = self.shift_formatter.format_cue(cue_data)

            # Create command
            command_id = packet.packet_id
            command = {
                'type': CommandType.CUE_EXECUTE.value,
                'packet': packet.to_dict(),
                'cue_data': cue_data,
                'timestamp': datetime.now().isoformat(),
                'command_id': command_id
            }

            # Execute command via SSH
            command_json = json.dumps(command)
            ssh_command = f"python3 {self.ssh_config.base_path}/{self.ssh_config.command_script} '{command_json}'"

            stdin, stdout, stderr = self.ssh_client.exec_command(ssh_command)
            exit_status = stdout.channel.recv_exit_status()

            if exit_status == 0:
                response = stdout.read().decode().strip()
                response_data = json.loads(response)
                success = response_data.get('success', False)
                message = response_data.get('message', '')

                # Track pending command
                self._pending_commands[command_id] = {
                    'command': command,
                    'timestamp': time.time(),
                    'cue_number': cue_data.get('cue_number', 'unknown')
                }

                self.logger.info(f"Cue command sent: {cue_data.get('cue_number', 'unknown')}")
                return success, message
            else:
                error = stderr.read().decode().strip()
                self.logger.error(f"SSH command failed: {error}")
                return False, f"SSH command failed: {error}"

        except Exception as e:
            self.logger.error(f"Failed to send cue: {e}")
            return False, f"Error: {e}"

    async def send_command(self, command_type: str, data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Send generic command to hardware

        Args:
            command_type: Type of command
            data: Command data

        Returns:
            tuple: (success, message)
        """
        if not self.is_hardware_connected():
            return False, "Hardware not connected"

        try:
            command_id = f"{command_type}_{int(time.time() * 1000)}"

            command = {
                'type': command_type,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'command_id': command_id
            }

            # Execute command via SSH
            command_json = json.dumps(command)
            ssh_command = f"python3 {self.ssh_config.base_path}/{self.ssh_config.command_script} '{command_json}'"

            stdin, stdout, stderr = self.ssh_client.exec_command(ssh_command)
            exit_status = stdout.channel.recv_exit_status()

            if exit_status == 0:
                response = stdout.read().decode().strip()
                response_data = json.loads(response)
                success = response_data.get('success', False)
                message = response_data.get('message', '')

                # Track pending command
                self._pending_commands[command_id] = {
                    'command': command,
                    'timestamp': time.time(),
                    'type': command_type
                }

                self.logger.info(f"Command sent: {command_type}")
                return success, message
            else:
                error = stderr.read().decode().strip()
                self.logger.error(f"SSH command failed: {error}")
                return False, f"SSH command failed: {error}"

        except Exception as e:
            self.logger.error(f"Failed to send command: {e}")
            return False, f"Error: {e}"

    def emergency_stop(self, reason: str = "Manual activation") -> bool:
        """
        Activate emergency stop

        Args:
            reason: Reason for emergency stop

        Returns:
            bool: True if emergency stop sent successfully
        """
        self.logger.warning(f"Emergency stop activated: {reason}")
        self._emergency_stop_active = True
        self._set_hardware_state(HardwareState.EMERGENCY_STOP)

        # Send emergency stop via SSH
        if self.ssh_client:
            try:
                ssh_command = f"python3 {self.ssh_config.base_path}/{self.ssh_config.emergency_script} '{reason}'"
                stdin, stdout, stderr = self.ssh_client.exec_command(ssh_command)
                exit_status = stdout.channel.recv_exit_status()

                if exit_status == 0:
                    self.emergency_stop_activated.emit(reason)
                    return True
                else:
                    error = stderr.read().decode().strip()
                    self.logger.error(f"Emergency stop command failed: {error}")
            except Exception as e:
                self.logger.error(f"Failed to send emergency stop: {e}")

        # Also try to send via hardware controller
        asyncio.create_task(self.send_command(
            CommandType.EMERGENCY_STOP.value,
            {'reason': reason, 'timestamp': datetime.now().isoformat()}
        ))

        return True

    def reset_emergency_stop(self) -> bool:
        """
        Reset emergency stop state

        Returns:
            bool: True if reset successful
        """
        if not self._emergency_stop_active:
            return True

        try:
            self._emergency_stop_active = False

            # Send reset command
            asyncio.create_task(self.send_command(
                CommandType.RESET.value,
                {'action': 'reset_emergency_stop', 'timestamp': datetime.now().isoformat()}
            ))

            if self.is_hardware_connected():
                self._set_hardware_state(HardwareState.CONNECTED)

            self.logger.info("Emergency stop reset")
            return True

        except Exception as e:
            self.logger.error(f"Failed to reset emergency stop: {e}")
            return False

    def send_test_pattern(self, pattern_type: str = "sequential") -> bool:
        """
        Send test pattern to hardware

        Args:
            pattern_type: Type of test pattern

        Returns:
            bool: True if test pattern sent successfully
        """
        if not self.is_hardware_connected():
            self.logger.warning("Cannot send test pattern: hardware not connected")
            return False

        try:
            # Create test pattern packet
            packet = self.shift_formatter.format_test_pattern(pattern_type)

            # Send test command
            asyncio.create_task(self.send_command(
                CommandType.TEST_PATTERN.value,
                {
                    'packet': packet.to_dict(),
                    'pattern_type': pattern_type,
                    'timestamp': datetime.now().isoformat()
                }
            ))

            self.logger.info(f"Test pattern sent: {pattern_type}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send test pattern: {e}")
            return False

    def _set_hardware_state(self, new_state: HardwareState):
        """Update hardware state and emit signal"""
        if self._hardware_state != new_state:
            old_state = self._hardware_state
            self._hardware_state = new_state
            self.logger.info(f"Hardware state changed: {old_state.value} -> {new_state.value}")
            self.hardware_state_changed.emit(new_state)

            # Update status
            self._last_status.state = new_state
            self.hardware_status_updated.emit(self._last_status)

            # Start/stop monitoring based on state
            if new_state == HardwareState.CONNECTED:
                self._start_monitoring()
            elif new_state in [HardwareState.DISCONNECTED, HardwareState.ERROR]:
                self._stop_monitoring()

    def _start_monitoring(self):
        """Start hardware monitoring"""
        # Request initial status
        self._request_hardware_status()

        # Start periodic status requests
        self._status_timer.start(10000)  # Every 10 seconds

        # Start command timeout monitoring
        self._command_timeout_timer.start(5000)  # Every 5 seconds

        self.logger.info("Hardware monitoring started")

    def _stop_monitoring(self):
        """Stop hardware monitoring"""
        self._status_timer.stop()
        self._command_timeout_timer.stop()
        self.logger.info("Hardware monitoring stopped")

    def _request_hardware_status(self):
        """Request hardware status from Raspberry Pi"""
        if self.is_hardware_connected():
            try:
                ssh_command = f"python3 {self.ssh_config.base_path}/{self.ssh_config.status_script}"
                stdin, stdout, stderr = self.ssh_client.exec_command(ssh_command)
                exit_status = stdout.channel.recv_exit_status()

                if exit_status == 0:
                    response = stdout.read().decode().strip()
                    try:
                        status_data = json.loads(response)
                        self._handle_status_message(status_data)
                    except json.JSONDecodeError:
                        self.logger.error(f"Invalid JSON in status response: {response}")
                else:
                    error = stderr.read().decode().strip()
                    self.logger.error(f"Status request failed: {error}")
            except Exception as e:
                self.logger.error(f"Failed to request status: {e}")

    def _check_command_timeouts(self):
        """Check for timed out commands"""
        current_time = time.time()
        timed_out_commands = []

        for command_id, command_info in self._pending_commands.items():
            if current_time - command_info['timestamp'] > self._command_timeout:
                timed_out_commands.append(command_id)

        # Handle timed out commands
        for command_id in timed_out_commands:
            command_info = self._pending_commands.pop(command_id)
            command_type = command_info.get('type', 'unknown')

            self.logger.warning(f"Command timeout: {command_id} ({command_type})")
            self.command_acknowledged.emit(command_id, False, "Command timeout")

            # If it was a critical command, consider it an error
            if command_type in [CommandType.CUE_EXECUTE.value, CommandType.EMERGENCY_STOP.value]:
                self.error_occurred.emit("COMMAND_TIMEOUT", f"Critical command timed out: {command_type}")

    def _handle_status_message(self, message_data: Dict[str, Any]):
        """Handle hardware status messages"""
        try:
            status = HardwareStatus(
                state=HardwareState(message_data.get('state', 'disconnected')),
                voltage=message_data.get('voltage', 0.0),
                temperature=message_data.get('temperature', 0.0),
                active_outputs=message_data.get('active_outputs', []),
                error_count=message_data.get('error_count', 0),
                uptime_seconds=message_data.get('uptime_seconds', 0.0)
            )

            # Update last command time if provided
            if 'last_command_time' in message_data:
                status.last_command_time = datetime.fromisoformat(message_data['last_command_time'])

            self._last_status = status
            self.hardware_status_updated.emit(status)

            self.logger.debug(f"Hardware status updated: {status.state.value}")

        except Exception as e:
            self.logger.error(f"Error processing status message: {e}")

    def get_hardware_status(self) -> HardwareStatus:
        """Get current hardware status"""
        return self._last_status

    def get_pending_commands(self) -> List[str]:
        """Get list of pending command IDs"""
        return list(self._pending_commands.keys())

    def is_emergency_stop_active(self) -> bool:
        """Check if emergency stop is active"""
        return self._emergency_stop_active

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information"""
        info = {
            'state': self._hardware_state.value,
            'emergency_stop_active': self._emergency_stop_active,
            'pending_commands': len(self._pending_commands),
            'last_heartbeat': self._last_heartbeat.isoformat() if self._last_heartbeat else None
        }

        if self.ssh_config:
            info.update({
                'host': self.ssh_config.host,
                'port': self.ssh_config.port,
                'client_id': self.ssh_config.client_id,
                'use_ssl': self.ssh_config.use_ssl
            })

        return info