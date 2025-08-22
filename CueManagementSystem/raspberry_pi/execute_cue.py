#!/usr/bin/env python3
"""
Execute Cue Script for Raspberry Pi

This script executes a single cue by controlling the appropriate GPIO pins
based on the cue data received.

Usage:
    python3 execute_cue.py --cue=1 --type="SINGLE SHOT" --outputs="1,2,3"
"""

import argparse
import RPi.GPIO as GPIO
import time
import sys
import json
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/home/pi/cue_execution.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("execute_cue")

# GPIO Pin Configuration
# Data pins for each chain (5 chains)
DATA_PINS = [7, 8, 12, 14, 15]

# Serial Clock pins (5 chains)
SCLK_PINS = [17, 18, 22, 23, 27]

# Register Clock pins (5 chains)
RCLK_PINS = [9, 10, 11, 24, 25]

# Default timing parameters
PULSE_DURATION_MS = 1000  # Changed from 100 to 1000 (1 second) as per requirements
REGISTER_DELAY_US = 10  # Delay between register operations in microseconds


def setup_gpio():
    """Initialize GPIO pins"""
    try:
        # Use BCM pin numbering
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Setup Data pins as outputs
        for pin in DATA_PINS:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

        # Setup Serial Clock pins as outputs
        for pin in SCLK_PINS:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

        # Setup Register Clock pins as outputs
        for pin in RCLK_PINS:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

        logger.info("GPIO pins initialized successfully")
        return True
    except Exception as e:
        logger.error(f"GPIO setup failed: {e}")
        return False


def determine_chain_for_output(output_number: int) -> int:
    """
    Determine which chain an output belongs to

    Args:
        output_number: The output number (1-1000)

    Returns:
        int: Chain number (0-4) or -1 if invalid
    """
    if output_number < 1 or output_number > 1000:
        return -1

    # Each chain handles 200 outputs (5 chains × 200 outputs = 1000 total)
    return (output_number - 1) // 200


def determine_register_for_output(output_number: int) -> int:
    """
    Determine which register within a chain an output belongs to

    Args:
        output_number: The output number (1-1000)

    Returns:
        int: Register number within chain (0-24) or -1 if invalid
    """
    if output_number < 1 or output_number > 1000:
        return -1

    # Each register handles 8 outputs, 25 registers per chain
    chain = determine_chain_for_output(output_number)
    if chain == -1:
        return -1

    # Calculate position within chain (0-199)
    position_in_chain = (output_number - 1) % 200

    # Calculate register number (0-24)
    return position_in_chain // 8


def determine_bit_for_output(output_number: int) -> int:
    """
    Determine which bit within a register an output belongs to

    Args:
        output_number: The output number (1-1000)

    Returns:
        int: Bit position (0-7) or -1 if invalid
    """
    if output_number < 1 or output_number > 1000:
        return -1

    # Calculate position within register (0-7)
    return (output_number - 1) % 8


def shift_out_data(chain: int, data_byte: int):
    """
    Shift out a byte of data to a specific chain

    Args:
        chain: Chain number (0-4)
        data_byte: Byte to shift out (0-255)
    """
    if chain < 0 or chain >= len(DATA_PINS):
        logger.error(f"Invalid chain number: {chain}")
        return

    # Get pins for this chain
    data_pin = DATA_PINS[chain]
    sclk_pin = SCLK_PINS[chain]

    # Shift out 8 bits, MSB first
    for i in range(7, -1, -1):
        # Set data bit
        bit = (data_byte >> i) & 1
        GPIO.output(data_pin, bit)

        # Pulse clock to shift in bit
        GPIO.output(sclk_pin, GPIO.HIGH)
        time.sleep(REGISTER_DELAY_US / 1000000.0)  # Convert to seconds
        GPIO.output(sclk_pin, GPIO.LOW)
        time.sleep(REGISTER_DELAY_US / 1000000.0)  # Convert to seconds


def latch_registers(chain: int):
    """
    Latch the shift register data to the storage register for a specific chain

    Args:
        chain: Chain number (0-4)
    """
    if chain < 0 or chain >= len(RCLK_PINS):
        logger.error(f"Invalid chain number: {chain}")
        return

    # Get register clock pin for this chain
    rclk_pin = RCLK_PINS[chain]

    # Pulse register clock to latch data
    GPIO.output(rclk_pin, GPIO.HIGH)
    time.sleep(REGISTER_DELAY_US / 1000000.0)  # Convert to seconds
    GPIO.output(rclk_pin, GPIO.LOW)


def execute_single_shot(output_number: int):
    """
    Execute a single shot cue

    Args:
        output_number: The output number to fire (1-1000)
    """
    # Determine chain, register, and bit
    chain = determine_chain_for_output(output_number)
    register = determine_register_for_output(output_number)
    bit = determine_bit_for_output(output_number)

    if chain == -1 or register == -1 or bit == -1:
        logger.error(f"Invalid output number: {output_number}")
        return False

    logger.info(
        f"Executing SINGLE SHOT for output {output_number} (Chain: {chain + 1}, Register: {register}, Bit: {bit})")

    try:
        # Create data byte with single bit set
        data_byte = 1 << bit

        # Clear all registers in the chain first
        for i in range(25):  # 25 registers per chain
            shift_out_data(chain, 0)
        latch_registers(chain)

        # Shift out data for the target register
        for i in range(24, -1, -1):  # Shift from last register to first
            if i == register:
                shift_out_data(chain, data_byte)  # Set the target register
            else:
                shift_out_data(chain, 0)  # Clear other registers

        # Latch the data
        latch_registers(chain)

        # Wait for pulse duration
        time.sleep(PULSE_DURATION_MS / 1000.0)  # Convert to seconds

        # Clear all registers
        for i in range(25):  # 25 registers per chain
            shift_out_data(chain, 0)
        latch_registers(chain)

        return True
    except Exception as e:
        logger.error(f"Error executing single shot: {e}")
        return False


def execute_double_shot(output1: int, output2: int):
    """
    Execute a double shot cue

    Args:
        output1: First output number to fire (1-1000)
        output2: Second output number to fire (1-1000)
    """
    # Determine chain, register, and bit for first output
    chain1 = determine_chain_for_output(output1)
    register1 = determine_register_for_output(output1)
    bit1 = determine_bit_for_output(output1)

    # Determine chain, register, and bit for second output
    chain2 = determine_chain_for_output(output2)
    register2 = determine_register_for_output(output2)
    bit2 = determine_bit_for_output(output2)

    if chain1 == -1 or register1 == -1 or bit1 == -1 or chain2 == -1 or register2 == -1 or bit2 == -1:
        logger.error(f"Invalid output numbers: {output1}, {output2}")
        return False

    logger.info(f"Executing DOUBLE SHOT for outputs {output1}, {output2}")

    try:
        # Handle case where outputs are on different chains
        if chain1 != chain2:
            # Execute each output separately
            execute_single_shot(output1)
            execute_single_shot(output2)
            return True

        # Handle case where outputs are on the same chain
        chain = chain1  # Same as chain2

        # Create data bytes
        data_byte1 = 1 << bit1
        data_byte2 = 1 << bit2

        # Clear all registers in the chain first
        for i in range(25):  # 25 registers per chain
            shift_out_data(chain, 0)
        latch_registers(chain)

        # Shift out data for the target registers
        for i in range(24, -1, -1):  # Shift from last register to first
            if i == register1 and i == register2:  # Same register
                shift_out_data(chain, data_byte1 | data_byte2)  # Combine bits
            elif i == register1:
                shift_out_data(chain, data_byte1)
            elif i == register2:
                shift_out_data(chain, data_byte2)
            else:
                shift_out_data(chain, 0)  # Clear other registers

        # Latch the data
        latch_registers(chain)

        # Wait for pulse duration
        time.sleep(PULSE_DURATION_MS / 1000.0)  # Convert to seconds

        # Clear all registers
        for i in range(25):  # 25 registers per chain
            shift_out_data(chain, 0)
        latch_registers(chain)

        return True
    except Exception as e:
        logger.error(f"Error executing double shot: {e}")
        return False


def execute_run(outputs: List[int], delay_ms: float):
    """
    Execute a run cue (sequential firing with delay)

    Args:
        outputs: List of output numbers to fire in sequence
        delay_ms: Delay between outputs in milliseconds
    """
    logger.info(f"Executing RUN for {len(outputs)} outputs with {delay_ms}ms delay")

    try:
        for output in outputs:
            # Fire each output
            execute_single_shot(output)

            # Wait for delay before next output
            if output != outputs[-1]:  # Don't delay after last output
                time.sleep(delay_ms / 1000.0)  # Convert to seconds

        return True
    except Exception as e:
        logger.error(f"Error executing run: {e}")
        return False


def execute_double_run(outputs: List[int], delay_ms: float):
    """
    Execute a double run cue (sequential firing of pairs with delay)

    Args:
        outputs: List of output numbers to fire in sequence (must be even length)
        delay_ms: Delay between pairs in milliseconds
    """
    if len(outputs) % 2 != 0:
        logger.error(f"Double run requires even number of outputs, got {len(outputs)}")
        return False

    logger.info(f"Executing DOUBLE RUN for {len(outputs)} outputs with {delay_ms}ms delay")

    try:
        # Process outputs in pairs
        for i in range(0, len(outputs), 2):
            if i + 1 < len(outputs):
                # Fire pair of outputs
                execute_double_shot(outputs[i], outputs[i + 1])

                # Wait for delay before next pair
                if i + 2 < len(outputs):  # Don't delay after last pair
                    time.sleep(delay_ms / 1000.0)  # Convert to seconds

        return True
    except Exception as e:
        logger.error(f"Error executing double run: {e}")
        return False


def execute_cue(cue_number: int, cue_type: str, outputs: List[int], delay: float = 0.0):
    """
    Execute a cue based on its type

    Args:
        cue_number: Cue number for identification
        cue_type: Type of cue (SINGLE SHOT, DOUBLE SHOT, SINGLE RUN, DOUBLE RUN)
        outputs: List of output numbers
        delay: Delay between outputs in seconds (for RUN types)
    """
    logger.info(f"Executing cue #{cue_number} of type {cue_type} with {len(outputs)} outputs")

    try:
        if not outputs:
            logger.error("No outputs specified")
            return False

        # Convert delay to milliseconds
        delay_ms = delay * 1000.0

        # Execute based on cue type
        if cue_type == "SINGLE SHOT":
            return execute_single_shot(outputs[0])
        elif cue_type == "DOUBLE SHOT":
            if len(outputs) < 2:
                logger.error(f"DOUBLE SHOT requires 2 outputs, got {len(outputs)}")
                return False
            return execute_double_shot(outputs[0], outputs[1])
        elif cue_type == "SINGLE RUN":
            return execute_run(outputs, delay_ms)
        elif cue_type == "DOUBLE RUN":
            return execute_double_run(outputs, delay_ms)
        else:
            logger.error(f"Unknown cue type: {cue_type}")
            return False
    except Exception as e:
        logger.error(f"Error executing cue: {e}")
        return False


def parse_outputs(outputs_str: str) -> List[int]:
    """
    Parse outputs string to list of integers

    Args:
        outputs_str: Comma-separated list of outputs

    Returns:
        List of output numbers
    """
    try:
        return [int(x.strip()) for x in outputs_str.split(',') if x.strip()]
    except Exception as e:
        logger.error(f"Error parsing outputs: {e}")
        return []


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Execute a cue for firework control system")
    parser.add_argument("--cue", type=int, required=True, help="Cue number")
    parser.add_argument("--type", type=str, required=True,
                        help="Cue type (SINGLE SHOT, DOUBLE SHOT, SINGLE RUN, DOUBLE RUN)")
    parser.add_argument("--outputs", type=str, required=True, help="Comma-separated list of outputs")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay between outputs in seconds (for RUN types)")
    parser.add_argument("--json", type=str, help="JSON string with cue data (alternative to individual arguments)")

    args = parser.parse_args()

    # Parse JSON if provided
    if args.json:
        try:
            cue_data = json.loads(args.json)
            cue_number = cue_data.get("cue_number", 0)
            cue_type = cue_data.get("cue_type", "")
            outputs = cue_data.get("output_values", [])
            delay = cue_data.get("delay", 0.0)
        except Exception as e:
            logger.error(f"Error parsing JSON: {e}")
            sys.exit(1)
    else:
        # Use command line arguments
        cue_number = args.cue
        cue_type = args.type
        outputs = parse_outputs(args.outputs)
        delay = args.delay

    if setup_gpio():
        success = execute_cue(cue_number, cue_type, outputs, delay)
        if success:
            print(f"Cue {cue_number} executed successfully")
            sys.exit(0)
        else:
            print(f"Failed to execute cue {cue_number}")
            sys.exit(1)
    else:
        print("GPIO setup failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
