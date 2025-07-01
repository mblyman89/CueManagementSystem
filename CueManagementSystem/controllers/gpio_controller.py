"""
GPIO Controller for Large-Scale Firework Control System

This module handles GPIO control for:
- 5 chains of 25 shift registers (1000 outputs total)
- Output Enable (OE) pins for each chain
- Serial Clear (SRCLR) pins for each chain
- Arm control pin
- WiFi/Adhoc mode switching
"""

import json
import logging
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from PySide6.QtCore import QObject, Signal


class GPIOState(Enum):
    """GPIO pin states"""
    LOW = 0
    HIGH = 1


class SystemState(Enum):
    """System operational states"""
    DISARMED = "disarmed"
    ARMED = "armed"
    EXECUTING = "executing"
    ABORTED = "aborted"
    PAUSED = "paused"


@dataclass
class GPIOConfig:
    """GPIO pin configuration for the system"""
    # Output Enable pins (5 chains) - HIGH when disabled, LOW when enabled
    output_enable_pins: List[int] = None  # Will be set to [5, 6, 7, 8, 12]
    output_enable_active_high: List[bool] = None  # [False, False, False, False, False] (LOW = enabled)

    # Serial Clear pins (5 chains) - LOW when disabled, HIGH when enabled
    serial_clear_pins: List[int] = None  # Will be set to [13, 16, 19, 20, 26]
    serial_clear_active_high: List[bool] = None  # [True, True, True, True, True] (HIGH = enabled)

    # Shift register control pins (5 chains of 25 registers each)
    data_pins: List[int] = None  # Will be set to [2, 3, 4, 14, 15] - Data pins for each chain
    sclk_pins: List[int] = None  # Will be set to [17, 18, 22, 23, 27] - Serial clock pins
    rclk_pins: List[int] = None  # Will be set to [9, 10, 11, 24, 25] - Register clock (latch) pins

    # Arm control pin - Active HIGH (LOW when disarmed, HIGH when armed)
    arm_pin: int = 21
    arm_active_high: bool = True

    # WiFi/Adhoc mode control pin (disabled - no GPIO functionality yet)
    # wifi_mode_pin: int = 16
    # wifi_mode_active_high: bool = True

    def __post_init__(self):
        """Initialize default values"""
        if self.output_enable_pins is None:
            self.output_enable_pins = [5, 6, 7, 8, 12]
        if self.output_enable_active_high is None:
            self.output_enable_active_high = [False, False, False, False, False]
        if self.serial_clear_pins is None:
            self.serial_clear_pins = [13, 16, 19, 20, 26]
        if self.serial_clear_active_high is None:
            self.serial_clear_active_high = [True, True, True, True, True]
        if self.data_pins is None:
            self.data_pins = [2, 3, 4, 14, 15]
        if self.sclk_pins is None:
            self.sclk_pins = [17, 18, 22, 23, 27]
        if self.rclk_pins is None:
            self.rclk_pins = [9, 10, 11, 24, 25]


class GPIOController(QObject):
    """
    GPIO Controller for large-scale firework control system

    Manages:
    - 10 GPIO pins for output enable/disable (5 active high, 5 active low)
    - 1 GPIO pin for arm/disarm control
    - WiFi/Adhoc mode switching
    - System state management
    """

    # Signals for system state changes
    gpio_state_changed = Signal(str, bool)  # pin_name, state
    system_state_changed = Signal(str)  # new_state
    error_occurred = Signal(str)  # error_message

    def __init__(self, config: GPIOConfig = None):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # Configuration
        self.config = config or GPIOConfig()

        # Current system state
        self.system_state = SystemState.DISARMED
        self.outputs_enabled = False
        self.system_armed = False
        # self.wifi_mode = True  # True = WiFi, False = Adhoc (disabled for now)

        # GPIO state tracking
        self.gpio_states = {}

        # Initialize GPIO states
        self._initialize_gpio_states()

        self.logger.info("GPIO Controller initialized for large-scale system")

    def _initialize_gpio_states(self):
        """Initialize all GPIO pins to safe states"""
        try:
            # Initialize Output Enable pins (disabled state = HIGH)
            for i, pin in enumerate(self.config.output_enable_pins):
                # Set to disabled state (HIGH = disabled for OE pins)
                safe_state = True  # HIGH = disabled
                self.gpio_states[f"oe_chain_{i + 1}"] = safe_state

            # Initialize Serial Clear pins (disabled state = LOW)
            for i, pin in enumerate(self.config.serial_clear_pins):
                # Set to disabled state (LOW = disabled for SRCLR pins)
                safe_state = False  # LOW = disabled
                self.gpio_states[f"srclr_chain_{i + 1}"] = safe_state

            # Initialize Arm pin (disarmed state)
            safe_state = not self.config.arm_active_high
            self.gpio_states["arm"] = safe_state

            # Initialize WiFi mode pin (WiFi mode) - DISABLED
            # self.gpio_states["wifi_mode"] = self.config.wifi_mode_active_high

            self.logger.info("GPIO states initialized to safe defaults")

        except Exception as e:
            self.logger.error(f"Failed to initialize GPIO states: {e}")
            self.error_occurred.emit(f"GPIO initialization failed: {e}")

    def toggle_outputs_enabled(self) -> bool:
        """
        Toggle output enable state for all 5 chains

        When enabling: OE pins go LOW (active), SRCLR pins go HIGH (not clearing)
        When disabling: OE pins go HIGH (inactive), SRCLR pins go LOW (clearing/disabled)

        Returns:
            bool: New enabled state
        """
        try:
            self.outputs_enabled = not self.outputs_enabled

            # Update all Output Enable pins (OE)
            for i, pin in enumerate(self.config.output_enable_pins):
                if self.outputs_enabled:
                    # Enable outputs - OE pins go LOW (active)
                    new_state = False  # LOW = enabled for OE pins
                else:
                    # Disable outputs - OE pins go HIGH (inactive)
                    new_state = True  # HIGH = disabled for OE pins

                self.gpio_states[f"oe_chain_{i + 1}"] = new_state
                self.gpio_state_changed.emit(f"oe_chain_{i + 1}", new_state)

            # Update all Serial Clear pins (SRCLR)
            for i, pin in enumerate(self.config.serial_clear_pins):
                if self.outputs_enabled:
                    # Enable outputs - SRCLR pins go HIGH (not clearing)
                    new_state = True  # HIGH = not clearing/enabled
                else:
                    # Disable outputs - SRCLR pins go LOW (clearing/disabled)
                    new_state = False  # LOW = clearing/disabled

                self.gpio_states[f"srclr_chain_{i + 1}"] = new_state
                self.gpio_state_changed.emit(f"srclr_chain_{i + 1}", new_state)

            # Update system state
            if self.outputs_enabled:
                self.logger.info("Outputs ENABLED for all 5 chains (OE=LOW, SRCLR=HIGH)")
            else:
                self.logger.info("Outputs DISABLED for all 5 chains (OE=HIGH, SRCLR=LOW)")
                # If disabling outputs, also disarm the system
                if self.system_armed:
                    self.set_arm_state(False)

            return self.outputs_enabled

        except Exception as e:
            self.logger.error(f"Failed to toggle outputs: {e}")
            self.error_occurred.emit(f"Output toggle failed: {e}")
            return self.outputs_enabled

    def set_arm_state(self, armed: bool) -> bool:
        """
        Set the arm state of the system

        Args:
            armed: True to arm, False to disarm

        Returns:
            bool: New armed state
        """
        try:
            # Can only arm if outputs are enabled
            if armed and not self.outputs_enabled:
                self.logger.warning("Cannot arm system - outputs not enabled")
                self.error_occurred.emit("Cannot arm: outputs must be enabled first")
                return False

            self.system_armed = armed

            # Set arm pin state
            if armed:
                new_state = self.config.arm_active_high
                self.system_state = SystemState.ARMED
            else:
                new_state = not self.config.arm_active_high
                self.system_state = SystemState.DISARMED

            self.gpio_states["arm"] = new_state
            self.gpio_state_changed.emit("arm", new_state)
            self.system_state_changed.emit(self.system_state.value)

            if armed:
                self.logger.info("System ARMED")
            else:
                self.logger.info("System DISARMED")

            return self.system_armed

        except Exception as e:
            self.logger.error(f"Failed to set arm state: {e}")
            self.error_occurred.emit(f"Arm state change failed: {e}")
            return self.system_armed

    def emergency_abort(self) -> bool:
        """
        Emergency abort - immediately disable all outputs and disarm system

        Returns:
            bool: True if abort successful
        """
        try:
            self.logger.critical("EMERGENCY ABORT ACTIVATED")

            # Disable all outputs immediately
            for i, pin in enumerate(self.config.output_enable_pins):
                # Set OE pins to disabled state (HIGH = disabled)
                safe_state = True  # HIGH = disabled for OE pins
                self.gpio_states[f"oe_chain_{i + 1}"] = safe_state
                self.gpio_state_changed.emit(f"oe_chain_{i + 1}", safe_state)

            # Clear all shift registers immediately
            for i, pin in enumerate(self.config.serial_clear_pins):
                # Set SRCLR pins to disabled state (LOW = disabled/clearing)
                safe_state = False  # LOW = disabled/clearing for SRCLR pins
                self.gpio_states[f"srclr_chain_{i + 1}"] = safe_state
                self.gpio_state_changed.emit(f"srclr_chain_{i + 1}", safe_state)

            # Disarm the system
            safe_state = not self.config.arm_active_high
            self.gpio_states["arm"] = safe_state
            self.gpio_state_changed.emit("arm", safe_state)

            # Update internal states
            self.outputs_enabled = False
            self.system_armed = False
            self.system_state = SystemState.ABORTED

            self.system_state_changed.emit(self.system_state.value)

            self.logger.critical("Emergency abort completed - all outputs disabled and disarmed")
            return True

        except Exception as e:
            self.logger.error(f"Emergency abort failed: {e}")
            self.error_occurred.emit(f"Emergency abort failed: {e}")
            return False

    def clear_shift_registers(self, chain_numbers: List[int] = None) -> bool:
        """
        Clear specific shift register chains using SRCLR pins

        Args:
            chain_numbers: List of chain numbers to clear (1-5), None for all chains

        Returns:
            bool: True if successful
        """
        try:
            if chain_numbers is None:
                chain_numbers = [1, 2, 3, 4, 5]  # All chains

            for chain_num in chain_numbers:
                if 1 <= chain_num <= 5:
                    i = chain_num - 1  # Convert to 0-based index

                    # Pulse the SRCLR pin (LOW to clear, then back to HIGH)
                    # For clearing: pulse LOW briefly, then back to HIGH

                    # Set to clearing state (LOW = clear)
                    self.gpio_states[f"srclr_chain_{chain_num}"] = False
                    self.gpio_state_changed.emit(f"srclr_chain_{chain_num}", False)

                    # Note: In real implementation, you'd add a small delay here
                    # then set back to normal state (HIGH = not clearing)
                    if self.outputs_enabled:
                        # If outputs are enabled, return to HIGH (not clearing)
                        self.gpio_states[f"srclr_chain_{chain_num}"] = True
                        self.gpio_state_changed.emit(f"srclr_chain_{chain_num}", True)
                    else:
                        # If outputs are disabled, keep LOW (disabled state)
                        self.gpio_states[f"srclr_chain_{chain_num}"] = False
                        self.gpio_state_changed.emit(f"srclr_chain_{chain_num}", False)

            self.logger.info(f"Cleared shift register chains: {chain_numbers}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to clear shift registers: {e}")
            self.error_occurred.emit(f"Shift register clear failed: {e}")
            return False

    # WiFi/Adhoc mode toggle functionality disabled for now
    # def toggle_wifi_mode(self) -> bool:
    #     """
    #     Toggle between WiFi and Adhoc modes (DISABLED - no GPIO functionality yet)
    #     Future: Will send SSH command to Pi to switch network modes
    #     """
    #     pass

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status

        Returns:
            dict: Complete system status
        """
        return {
            "system_state": self.system_state.value,
            "outputs_enabled": self.outputs_enabled,
            "system_armed": self.system_armed,
            # "wifi_mode": "WiFi" if self.wifi_mode else "Adhoc",  # Disabled
            "gpio_states": self.gpio_states.copy(),
            "timestamp": datetime.now().isoformat(),
            "total_outputs": 1000,  # 5 chains × 200 outputs each
            "total_chains": 5,
            "registers_per_chain": 25
        }

    def create_gpio_command(self, command_type: str, **kwargs) -> Dict[str, Any]:
        """
        Create GPIO command for MQTT transmission

        Args:
            command_type: Type of GPIO command
            **kwargs: Additional command parameters

        Returns:
            dict: GPIO command message
        """
        return {
            "type": "gpio_command",
            "command": command_type,
            "timestamp": datetime.now().isoformat(),
            "parameters": kwargs,
            "current_state": self.get_system_status()
        }

    def validate_system_ready_for_execution(self) -> tuple[bool, str]:
        """
        Validate that system is ready for cue execution

        Returns:
            tuple: (is_ready, status_message)
        """
        if not self.outputs_enabled:
            return False, "Outputs not enabled"

        if not self.system_armed:
            return False, "System not armed"

        if self.system_state == SystemState.ABORTED:
            return False, "System in aborted state"

        if self.system_state == SystemState.EXECUTING:
            return False, "System already executing"

        return True, "System ready for execution"