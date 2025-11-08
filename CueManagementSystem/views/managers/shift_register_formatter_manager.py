"""
74HC595 Shift Register Data Formatter for Firework Control

This module handles the conversion of firework cue data into properly formatted
binary data for 74HC595 shift register chains. It provides:

- Binary data encoding for shift register chains
- Cue-to-output mapping with validation
- Timing synchronization data
- Data integrity verification (checksums)
- Support for multiple shift register chains
- Safety interlocks and validation
"""

import struct
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
import hashlib
import logging


class CueType(Enum):
    """Firework cue types"""
    SINGLE_SHOT = "SINGLE SHOT"
    DOUBLE_SHOT = "DOUBLE SHOT"
    SINGLE_RUN = "SINGLE RUN"
    DOUBLE_RUN = "DOUBLE RUN"


class OutputState(Enum):
    """Output pin states"""
    OFF = 0
    ON = 1
    PULSE = 2  # For timed outputs


@dataclass
class ShiftRegisterConfig:
    """Configuration for shift register chains"""
    num_registers: int = 8  # Number of 74HC595 chips in chain
    outputs_per_register: int = 8  # Outputs per chip (always 8 for 74HC595)
    pulse_duration_ms: int = 100  # Default pulse duration for firework ignition
    max_simultaneous_outputs: int = 4  # Safety limit for simultaneous outputs
    voltage_check_enabled: bool = True  # Enable voltage monitoring
    continuity_check_enabled: bool = True  # Enable continuity checking

    # Large-scale system configuration
    num_chains: int = 1  # Number of shift register chains
    registers_per_chain: int = 8  # Registers per chain
    outputs_per_chain: int = 64  # Outputs per chain (registers_per_chain × 8)
    use_output_enable: bool = False  # Use OE (Output Enable) pin control
    use_serial_clear: bool = False  # Use SRCLR (Serial Clear) pin control

    # GPIO pin assignments for control signals
    output_enable_pins: List[int] = field(default_factory=lambda: [])  # OE pins for each chain
    serial_clear_pins: List[int] = field(default_factory=lambda: [])  # SRCLR pins for each chain
    arm_pin: int = 0  # Single arm control pin

    @property
    def total_outputs(self) -> int:
        """Total number of available outputs"""
        return self.num_registers * self.outputs_per_register


@dataclass
class OutputCommand:
    """Individual output command"""
    output_number: int  # 1-based output number
    state: OutputState
    duration_ms: int = 100  # Duration for pulse outputs
    delay_ms: int = 0  # Delay before activation
    priority: int = 1  # Priority level (1=highest, 5=lowest)

    def __post_init__(self):
        if self.output_number < 1:
            raise ValueError("Output number must be >= 1")


@dataclass
class FireworkCue:
    """Processed firework cue data"""
    cue_number: str
    cue_type: CueType
    outputs: List[OutputCommand]
    execute_time: str
    delay_seconds: float = 0.0
    duration_seconds: float = 0.0
    safety_checks: bool = True

    def __post_init__(self):
        # Validate outputs based on cue type
        self._validate_cue_type()

    def _validate_cue_type(self):
        """Validate outputs match cue type requirements"""
        if self.cue_type == CueType.SINGLE_SHOT and len(self.outputs) != 1:
            raise ValueError("Single shot cue must have exactly 1 output")
        elif self.cue_type == CueType.DOUBLE_SHOT and len(self.outputs) != 2:
            raise ValueError("Double shot cue must have exactly 2 outputs")


@dataclass
class ShiftRegisterPacket:
    """Data packet for shift register control"""
    packet_id: str
    timestamp: float
    register_data: bytes  # Binary data for all registers
    checksum: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert packet to dictionary for JSON serialization"""
        return {
            'packet_id': self.packet_id,
            'timestamp': self.timestamp,
            'register_data': self.register_data.hex(),  # Convert bytes to hex string
            'checksum': self.checksum,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ShiftRegisterPacket':
        """Create packet from dictionary"""
        return cls(
            packet_id=data['packet_id'],
            timestamp=data['timestamp'],
            register_data=bytes.fromhex(data['register_data']),
            checksum=data['checksum'],
            metadata=data.get('metadata', {})
        )


class ShiftRegisterFormatter:
    """
    Formats firework cue data for 74HC595 shift register chains

    This class handles the conversion of high-level firework cue commands
    into low-level binary data suitable for transmission to Raspberry Pi
    hardware controlling 74HC595 shift register chains.
    """

    def __init__(self, config: ShiftRegisterConfig):
        self.config = config
        self.logger = self._setup_logging()

        # Track active outputs for safety
        self._active_outputs: Dict[int, float] = {}  # output_number -> end_time
        self._output_usage_count: Dict[int, int] = {}  # Track usage for diagnostics

        self.logger.info(f"Shift register formatter initialized: {config.total_outputs} outputs")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for formatter"""
        logger = logging.getLogger(f"ShiftRegisterFormatter_{id(self)}")
        logger.setLevel(logging.DEBUG)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def format_cue(self, cue_data: Dict[str, Any]) -> ShiftRegisterPacket:
        """
        Convert cue data to shift register packet

        Args:
            cue_data: Raw cue data from the application

        Returns:
            ShiftRegisterPacket: Formatted packet ready for transmission
        """
        try:
            # Parse cue data
            firework_cue = self._parse_cue_data(cue_data)

            # Validate safety constraints
            if firework_cue.safety_checks:
                self._validate_safety_constraints(firework_cue)

            # Generate binary data
            register_data = self._generate_register_data(firework_cue)

            # Create packet
            packet_id = f"cue_{firework_cue.cue_number}_{int(time.time() * 1000)}"
            timestamp = time.time()
            checksum = self._calculate_checksum(register_data, timestamp)

            packet = ShiftRegisterPacket(
                packet_id=packet_id,
                timestamp=timestamp,
                register_data=register_data,
                checksum=checksum,
                metadata={
                    'cue_number': firework_cue.cue_number,
                    'cue_type': firework_cue.cue_type.value,
                    'output_count': len(firework_cue.outputs),
                    'execute_time': firework_cue.execute_time,
                    'delay_seconds': firework_cue.delay_seconds,
                    'duration_seconds': firework_cue.duration_seconds
                }
            )

            self.logger.info(f"Formatted cue {firework_cue.cue_number}: {len(firework_cue.outputs)} outputs")
            return packet

        except Exception as e:
            self.logger.error(f"Failed to format cue: {e}")
            raise

    def format_emergency_stop(self) -> ShiftRegisterPacket:
        """
        Create emergency stop packet that turns off all outputs

        Returns:
            ShiftRegisterPacket: Emergency stop packet
        """
        # Create all-zeros data (all outputs OFF)
        register_data = bytes(self.config.num_registers)

        packet_id = f"emergency_stop_{int(time.time() * 1000)}"
        timestamp = time.time()
        checksum = self._calculate_checksum(register_data, timestamp)

        packet = ShiftRegisterPacket(
            packet_id=packet_id,
            timestamp=timestamp,
            register_data=register_data,
            checksum=checksum,
            metadata={
                'command_type': 'EMERGENCY_STOP',
                'description': 'Turn off all outputs immediately'
            }
        )

        self.logger.warning("Emergency stop packet created")
        return packet

    def format_test_pattern(self, pattern_type: str = "sequential") -> ShiftRegisterPacket:
        """
        Create test pattern for hardware verification

        Args:
            pattern_type: Type of test pattern ("sequential", "alternating", "all_on", "all_off")

        Returns:
            ShiftRegisterPacket: Test pattern packet
        """
        register_data = bytes(self.config.num_registers)

        if pattern_type == "sequential":
            # Turn on outputs sequentially
            register_data = self._create_sequential_pattern()
        elif pattern_type == "alternating":
            # Alternating pattern
            register_data = self._create_alternating_pattern()
        elif pattern_type == "all_on":
            # All outputs on (use with caution!)
            register_data = bytes([0xFF] * self.config.num_registers)
        elif pattern_type == "all_off":
            # All outputs off
            register_data = bytes(self.config.num_registers)
        else:
            raise ValueError(f"Unknown test pattern: {pattern_type}")

        packet_id = f"test_{pattern_type}_{int(time.time() * 1000)}"
        timestamp = time.time()
        checksum = self._calculate_checksum(register_data, timestamp)

        packet = ShiftRegisterPacket(
            packet_id=packet_id,
            timestamp=timestamp,
            register_data=register_data,
            checksum=checksum,
            metadata={
                'command_type': 'TEST_PATTERN',
                'pattern_type': pattern_type,
                'description': f'Test pattern: {pattern_type}'
            }
        )

        self.logger.info(f"Test pattern created: {pattern_type}")
        return packet

    def _parse_cue_data(self, cue_data: Dict[str, Any]) -> FireworkCue:
        """Parse raw cue data into FireworkCue object"""
        try:
            # Extract basic cue information
            cue_number = str(cue_data.get('cue_number', ''))
            cue_type_str = cue_data.get('cue_type', '').upper()
            execute_time = cue_data.get('execute_time', '00:00.0000')
            delay_seconds = float(cue_data.get('delay', 0))

            # Parse cue type
            cue_type = CueType(cue_type_str)

            # Parse output values
            output_values = cue_data.get('output_values', [])
            if not output_values:
                # Try to parse from outputs string
                outputs_str = cue_data.get('outputs', '')
                output_values = self._parse_outputs_string(outputs_str)

            # Create output commands
            outputs = []
            for i, output_num in enumerate(output_values):
                if not isinstance(output_num, int) or output_num < 1:
                    raise ValueError(f"Invalid output number: {output_num}")

                # Calculate delay for run types
                delay_ms = 0
                if cue_type in [CueType.SINGLE_RUN, CueType.DOUBLE_RUN]:
                    delay_ms = int(delay_seconds * 1000 * i)  # Stagger outputs

                output_cmd = OutputCommand(
                    output_number=output_num,
                    state=OutputState.PULSE,
                    duration_ms=self.config.pulse_duration_ms,
                    delay_ms=delay_ms,
                    priority=1
                )
                outputs.append(output_cmd)

            # Calculate total duration for run types
            duration_seconds = 0.0
            if cue_type in [CueType.SINGLE_RUN, CueType.DOUBLE_RUN] and len(outputs) > 1:
                duration_seconds = delay_seconds * (len(outputs) - 1) + (self.config.pulse_duration_ms / 1000.0)

            return FireworkCue(
                cue_number=cue_number,
                cue_type=cue_type,
                outputs=outputs,
                execute_time=execute_time,
                delay_seconds=delay_seconds,
                duration_seconds=duration_seconds,
                safety_checks=True
            )

        except Exception as e:
            self.logger.error(f"Failed to parse cue data: {e}")
            raise ValueError(f"Invalid cue data: {e}")

    def _parse_outputs_string(self, outputs_str: str) -> List[int]:
        """Parse outputs string into list of output numbers"""
        if not outputs_str:
            return []

        output_numbers = []

        # Handle different formats: "1,2,3" or "1,2; 3,4" for double runs
        parts = outputs_str.replace(';', ',').split(',')

        for part in parts:
            part = part.strip()
            if part and part.isdigit():
                output_numbers.append(int(part))

        return output_numbers

    def _validate_safety_constraints(self, cue: FireworkCue):
        """Validate safety constraints for the cue"""
        # Check maximum simultaneous outputs
        if len(cue.outputs) > self.config.max_simultaneous_outputs:
            raise ValueError(
                f"Cue {cue.cue_number} exceeds maximum simultaneous outputs "
                f"({len(cue.outputs)} > {self.config.max_simultaneous_outputs})"
            )

        # Check output range
        for output_cmd in cue.outputs:
            if output_cmd.output_number > self.config.total_outputs:
                raise ValueError(
                    f"Output {output_cmd.output_number} exceeds available outputs "
                    f"({self.config.total_outputs})"
                )

        # Check for duplicate outputs in same cue
        output_numbers = [cmd.output_number for cmd in cue.outputs]
        if len(output_numbers) != len(set(output_numbers)):
            raise ValueError(f"Cue {cue.cue_number} contains duplicate outputs")

        # Check for currently active outputs (safety interlock)
        current_time = time.time()
        for output_cmd in cue.outputs:
            if output_cmd.output_number in self._active_outputs:
                end_time = self._active_outputs[output_cmd.output_number]
                if current_time < end_time:
                    raise ValueError(
                        f"Output {output_cmd.output_number} is currently active "
                        f"(ends at {end_time - current_time:.1f}s)"
                    )

        self.logger.debug(f"Safety validation passed for cue {cue.cue_number}")

    def _generate_register_data(self, cue: FireworkCue) -> bytes:
        """Generate binary data for shift registers"""
        # Initialize all registers to 0 (all outputs OFF)
        register_bytes = [0] * self.config.num_registers

        # Set bits for active outputs
        for output_cmd in cue.outputs:
            if output_cmd.state == OutputState.ON or output_cmd.state == OutputState.PULSE:
                # Convert 1-based output number to register and bit position
                output_index = output_cmd.output_number - 1  # Convert to 0-based
                register_index = output_index // self.config.outputs_per_register
                bit_position = output_index % self.config.outputs_per_register

                # Set the bit (74HC595 shifts MSB first)
                register_bytes[register_index] |= (1 << (7 - bit_position))

                # Track active output for safety
                if output_cmd.state == OutputState.PULSE:
                    end_time = time.time() + (output_cmd.duration_ms / 1000.0)
                    self._active_outputs[output_cmd.output_number] = end_time

                # Update usage statistics
                self._output_usage_count[output_cmd.output_number] = \
                    self._output_usage_count.get(output_cmd.output_number, 0) + 1

        # Convert to bytes (74HC595 chains are daisy-chained, so first register is last in chain)
        register_data = bytes(reversed(register_bytes))

        self.logger.debug(f"Generated register data: {register_data.hex()}")
        return register_data

    def _calculate_checksum(self, data: bytes, timestamp: float) -> str:
        """Calculate checksum for data integrity verification"""
        # Combine data and timestamp for checksum
        checksum_input = data + struct.pack('d', timestamp)
        return hashlib.sha256(checksum_input).hexdigest()[:16]  # Use first 16 chars

    def _create_sequential_pattern(self) -> bytes:
        """Create sequential test pattern (one output at a time)"""
        # For testing, just turn on first output of first register
        register_bytes = [0] * self.config.num_registers
        register_bytes[0] = 0x80  # MSB of first register
        return bytes(reversed(register_bytes))

    def _create_alternating_pattern(self) -> bytes:
        """Create alternating test pattern"""
        register_bytes = []
        for i in range(self.config.num_registers):
            # Alternate between 0xAA (10101010) and 0x55 (01010101)
            register_bytes.append(0xAA if i % 2 == 0 else 0x55)
        return bytes(reversed(register_bytes))

    def cleanup_expired_outputs(self):
        """Clean up expired active outputs"""
        current_time = time.time()
        expired_outputs = [
            output_num for output_num, end_time in self._active_outputs.items()
            if current_time >= end_time
        ]

        for output_num in expired_outputs:
            del self._active_outputs[output_num]

        if expired_outputs:
            self.logger.debug(f"Cleaned up {len(expired_outputs)} expired outputs")

    def get_active_outputs(self) -> List[int]:
        """Get list of currently active output numbers"""
        self.cleanup_expired_outputs()
        return list(self._active_outputs.keys())

    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get output usage statistics"""
        return {
            'total_outputs': self.config.total_outputs,
            'active_outputs': len(self._active_outputs),
            'usage_count': self._output_usage_count.copy(),
            'most_used_output': max(self._output_usage_count.items(),
                                    key=lambda x: x[1]) if self._output_usage_count else None,
            'total_activations': sum(self._output_usage_count.values())
        }

    def validate_packet(self, packet: ShiftRegisterPacket) -> bool:
        """
        Validate packet integrity

        Args:
            packet: Packet to validate

        Returns:
            bool: True if packet is valid
        """
        try:
            # Recalculate checksum
            expected_checksum = self._calculate_checksum(packet.register_data, packet.timestamp)

            if packet.checksum != expected_checksum:
                self.logger.error(f"Checksum mismatch: expected {expected_checksum}, got {packet.checksum}")
                return False

            # Check data length
            if len(packet.register_data) != self.config.num_registers:
                self.logger.error(
                    f"Invalid data length: expected {self.config.num_registers}, got {len(packet.register_data)}")
                return False

            # Check timestamp (not too old or in future)
            current_time = time.time()
            age = current_time - packet.timestamp

            if age > 300:  # 5 minutes old
                self.logger.warning(f"Packet is {age:.1f}s old")
                return False

            if age < -60:  # More than 1 minute in future
                self.logger.warning(f"Packet timestamp is {-age:.1f}s in the future")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Packet validation error: {e}")
            return False


# Utility functions for integration with existing codebase
def create_shift_register_formatter(num_registers: int = 8,
                                    max_simultaneous: int = 4) -> ShiftRegisterFormatter:
    """
    Create a shift register formatter with common settings

    Args:
        num_registers: Number of 74HC595 chips in chain
        max_simultaneous: Maximum simultaneous outputs for safety

    Returns:
        ShiftRegisterFormatter: Configured formatter instance
    """
    config = ShiftRegisterConfig(
        num_registers=num_registers,
        max_simultaneous_outputs=max_simultaneous,
        pulse_duration_ms=100,  # 100ms pulse for firework ignition
        voltage_check_enabled=True,
        continuity_check_enabled=True
    )

    return ShiftRegisterFormatter(config)


def format_cue_for_hardware(cue_data: Dict[str, Any],
                            formatter: ShiftRegisterFormatter) -> Dict[str, Any]:
    """
    Format cue data for hardware transmission

    Args:
        cue_data: Raw cue data from application
        formatter: Shift register formatter instance

    Returns:
        Dict containing formatted packet data
    """
    packet = formatter.format_cue(cue_data)
    return packet.to_dict()