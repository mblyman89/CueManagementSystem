#!/usr/bin/env python3
"""
Execute Show Script for Raspberry Pi

This script executes a complete show by sequentially firing cues
based on their execution times.

Usage:
    python3 execute_show.py --show=/path/to/show.json
    python3 execute_show.py --json='{"cues": [...]}'
"""

import argparse
import RPi.GPIO as GPIO
import time
import sys
import json
import logging
import threading
import os
from typing import List, Dict, Any, Set
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/home/pi/show_execution.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("execute_show")

# Show execution state
SHOW_RUNNING = True
SHOW_PAUSED = False
SHOW_ABORT = False

# Path to the execute_cue.py script
EXECUTE_CUE_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "execute_cue.py")

# GPIO Pin Configuration
# Data pins for each chain (5 chains)
DATA_PINS = [7, 8, 12, 14, 15]

# Serial Clock pins (5 chains)
SCLK_PINS = [17, 18, 22, 23, 27]

# Register Clock pins (5 chains)
RCLK_PINS = [9, 10, 11, 24, 25]

# Default timing parameters
PULSE_DURATION_MS = 1000  # Duration of output pulse in milliseconds
REGISTER_DELAY_US = 10  # Delay between register operations in microseconds

# Track active outputs across the entire show
ACTIVE_OUTPUTS: Set[int] = set()
# Track active outputs by chain and register
ACTIVE_REGISTERS: Dict[int, Dict[int, int]] = {}  # chain -> register -> byte value


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

        # Initialize active registers dictionary
        for chain in range(len(DATA_PINS)):
            ACTIVE_REGISTERS[chain] = {}

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


def activate_output(output_number: int) -> bool:
    """
    Activate a single output and keep it on for the show

    Args:
        output_number: The output number to activate (1-1000)

    Returns:
        bool: True if successful, False otherwise
    """
    # Determine chain, register, and bit
    chain = determine_chain_for_output(output_number)
    register = determine_register_for_output(output_number)
    bit = determine_bit_for_output(output_number)

    if chain == -1 or register == -1 or bit == -1:
        logger.error(f"Invalid output number: {output_number}")
        return False

    logger.info(
        f"Activating output {output_number} (Chain: {chain + 1}, Register: {register}, Bit: {bit})")

    try:
        # Add to active outputs set
        ACTIVE_OUTPUTS.add(output_number)

        # Update active registers
        if register not in ACTIVE_REGISTERS[chain]:
            ACTIVE_REGISTERS[chain][register] = 0

        # Set the bit in the register
        ACTIVE_REGISTERS[chain][register] |= (1 << bit)

        # Update the shift registers for this chain
        update_chain_registers(chain)

        return True
    except Exception as e:
        logger.error(f"Error activating output: {e}")
        return False


def update_chain_registers(chain: int):
    """
    Update all registers in a chain based on active outputs

    Args:
        chain: Chain number (0-4)
    """
    try:
        # Clear all registers in the chain first
        for i in range(25):  # 25 registers per chain
            shift_out_data(chain, 0)
        latch_registers(chain)

        # Shift out data for all registers in the chain
        for i in range(24, -1, -1):  # Shift from last register to first
            if i in ACTIVE_REGISTERS[chain]:
                shift_out_data(chain, ACTIVE_REGISTERS[chain][i])
            else:
                shift_out_data(chain, 0)

        # Latch the data
        latch_registers(chain)

    except Exception as e:
        logger.error(f"Error updating chain registers: {e}")


def clear_all_outputs():
    """Turn off all outputs and clear tracking data"""
    try:
        # Clear all active outputs tracking
        ACTIVE_OUTPUTS.clear()
        for chain in ACTIVE_REGISTERS:
            ACTIVE_REGISTERS[chain].clear()

        # Clear all registers in all chains
        for chain in range(len(DATA_PINS)):
            for i in range(25):  # 25 registers per chain
                shift_out_data(chain, 0)
            latch_registers(chain)

        logger.info("All outputs cleared")
        return True
    except Exception as e:
        logger.error(f"Error clearing outputs: {e}")
        return False


def execute_cue_for_show(cue_data: Dict[str, Any]) -> bool:
    """
    Execute a single cue as part of a show, keeping outputs on

    Args:
        cue_data: Dictionary containing cue data

    Returns:
        bool: True if execution successful
    """
    try:
        cue_number = cue_data.get("cue_number", 0)
        cue_type = cue_data.get("cue_type", "")
        outputs_str = cue_data.get("outputs", "")
        delay = float(cue_data.get("delay_ms", 0)) / 1000.0  # Convert to seconds

        # Parse outputs
        outputs = parse_outputs(outputs_str)
        if not outputs:
            logger.error(f"No outputs specified for cue {cue_number}")
            return False

        logger.info(f"Executing cue #{cue_number} of type {cue_type} with {len(outputs)} outputs")

        # Execute based on cue type
        if cue_type == "SINGLE SHOT":
            if outputs:
                return activate_output(outputs[0])
            return False
        elif cue_type == "DOUBLE SHOT":
            if len(outputs) >= 2:
                success1 = activate_output(outputs[0])
                success2 = activate_output(outputs[1])
                return success1 and success2
            return False
        elif cue_type == "SINGLE RUN":
            success = True
            for i, output in enumerate(outputs):
                # Activate output
                success = success and activate_output(output)

                # Wait for delay before next output
                if i < len(outputs) - 1:
                    time.sleep(delay)
            return success
        elif cue_type == "DOUBLE RUN":
            if len(outputs) % 2 != 0:
                logger.error(f"Double run requires even number of outputs, got {len(outputs)}")
                return False

            success = True
            for i in range(0, len(outputs), 2):
                if i + 1 < len(outputs):
                    # Activate pair of outputs
                    success1 = activate_output(outputs[i])
                    success2 = activate_output(outputs[i + 1])
                    success = success and success1 and success2

                    # Wait for delay before next pair
                    if i + 2 < len(outputs):
                        time.sleep(delay)
            return success
        else:
            logger.error(f"Unknown cue type: {cue_type}")
            return False

    except Exception as e:
        logger.error(f"Error executing cue for show: {e}")
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
        if isinstance(outputs_str, list):
            # Already a list of integers
            return [int(x) for x in outputs_str]
        return [int(x.strip()) for x in outputs_str.split(',') if x.strip()]
    except Exception as e:
        logger.error(f"Error parsing outputs: {e}")
        return []


def time_to_seconds(time_str: str) -> float:
    """
    Convert time string (MM:SS.SS) to seconds

    Args:
        time_str: Time string to convert

    Returns:
        Time in seconds as float
    """
    try:
        minutes, seconds = time_str.split(':')
        return int(minutes) * 60 + float(seconds)
    except (ValueError, TypeError):
        return 0.0


def execute_show(cues: List[Dict[str, Any]]) -> bool:
    """
    Execute a complete show

    Args:
        cues: List of cue dictionaries

    Returns:
        bool: True if show executed successfully
    """
    global SHOW_RUNNING, SHOW_PAUSED, SHOW_ABORT

    if not cues:
        logger.error("No cues to execute")
        return False

    # Sort cues by execution time
    sorted_cues = sorted(cues, key=lambda x: time_to_seconds(x.get('execute_time', '0:00')))

    logger.info(f"Starting show execution with {len(sorted_cues)} cues")

    # Reset show state
    SHOW_RUNNING = True
    SHOW_PAUSED = False
    SHOW_ABORT = False

    # Clear all outputs before starting
    clear_all_outputs()

    # Track show progress
    start_time = time.time()
    completed_cues = 0
    total_cues = len(sorted_cues)

    # Start progress reporting thread
    progress_thread = threading.Thread(target=report_progress, args=(start_time, total_cues))
    progress_thread.daemon = True
    progress_thread.start()

    try:
        # Execute each cue at its scheduled time
        for i, cue in enumerate(sorted_cues):
            # Check for abort
            if SHOW_ABORT:
                logger.warning("Show aborted")
                clear_all_outputs()
                return False

            # Get execution time in seconds
            cue_time = time_to_seconds(cue.get('execute_time', '0:00'))

            # Calculate elapsed time
            elapsed_time = time.time() - start_time

            # Wait until it's time to execute this cue
            while elapsed_time < cue_time:
                # Check for abort
                if SHOW_ABORT:
                    logger.warning("Show aborted while waiting for next cue")
                    clear_all_outputs()
                    return False

                # Handle pause
                if SHOW_PAUSED:
                    pause_start = time.time()
                    logger.info(f"Show paused at {elapsed_time:.2f} seconds")

                    # Wait while paused
                    while SHOW_PAUSED and not SHOW_ABORT:
                        time.sleep(0.1)

                    # Adjust start time to account for pause duration
                    pause_duration = time.time() - pause_start
                    start_time += pause_duration
                    logger.info(f"Show resumed after {pause_duration:.2f} seconds pause")

                # Sleep briefly to avoid CPU hogging
                time.sleep(0.01)

                # Recalculate elapsed time
                elapsed_time = time.time() - start_time

            # Execute the cue
            success = execute_cue_for_show(cue)
            completed_cues += 1

            # Log progress
            logger.info(f"Completed {completed_cues}/{total_cues} cues")

        # Show completed - keep outputs on for 1 second, then clear
        logger.info("Show execution completed, keeping outputs on for 1 second")
        time.sleep(1.0)
        clear_all_outputs()

        logger.info("Show execution completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error executing show: {e}")
        clear_all_outputs()
        return False

    finally:
        # Reset show state
        SHOW_RUNNING = False
        SHOW_PAUSED = False


def report_progress(start_time: float, total_cues: int):
    """
    Report show progress periodically

    Args:
        start_time: Show start time in seconds
        total_cues: Total number of cues in the show
    """
    global SHOW_RUNNING, SHOW_PAUSED, SHOW_ABORT

    while SHOW_RUNNING and not SHOW_ABORT:
        # Calculate elapsed time
        elapsed_time = time.time() - start_time

        # Log progress
        status = "PAUSED" if SHOW_PAUSED else "RUNNING"
        logger.debug(f"Show {status} - Elapsed time: {elapsed_time:.2f} seconds")

        # Sleep for a second
        time.sleep(1)


def pause_show():
    """Pause the show execution"""
    global SHOW_PAUSED

    if SHOW_RUNNING and not SHOW_PAUSED:
        SHOW_PAUSED = True
        logger.info("Show paused")
        return True
    return False


def resume_show():
    """Resume the paused show"""
    global SHOW_PAUSED

    if SHOW_RUNNING and SHOW_PAUSED:
        SHOW_PAUSED = False
        logger.info("Show resumed")
        return True
    return False


def abort_show():
    """Abort the show execution"""
    global SHOW_ABORT

    if SHOW_RUNNING:
        SHOW_ABORT = True
        logger.warning("Show abort requested")
        return True
    return False


def load_show_from_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load show data from a JSON file

    Args:
        file_path: Path to the JSON file

    Returns:
        List of cue dictionaries
    """
    try:
        with open(file_path, 'r') as f:
            show_data = json.load(f)

        # Extract cues from show data
        if isinstance(show_data, dict) and 'cues' in show_data:
            return show_data['cues']
        elif isinstance(show_data, list):
            return show_data
        else:
            logger.error("Invalid show data format")
            return []
    except Exception as e:
        logger.error(f"Error loading show from file: {e}")
        return []


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Execute a show for firework control system")
    parser.add_argument("--show", type=str, help="Path to show JSON file")
    parser.add_argument("--json", type=str, help="JSON string with show data")

    # Control arguments
    parser.add_argument("--pause", action="store_true", help="Pause a running show")
    parser.add_argument("--resume", action="store_true", help="Resume a paused show")
    parser.add_argument("--abort", action="store_true", help="Abort a running show")

    args = parser.parse_args()

    # Handle control commands
    if args.pause:
        if pause_show():
            print("Show paused successfully")
            sys.exit(0)
        else:
            print("Failed to pause show")
            sys.exit(1)

    if args.resume:
        if resume_show():
            print("Show resumed successfully")
            sys.exit(0)
        else:
            print("Failed to resume show")
            sys.exit(1)

    if args.abort:
        if abort_show():
            print("Show abort requested successfully")
            sys.exit(0)
        else:
            print("Failed to abort show")
            sys.exit(1)

    # Load show data
    cues = []

    if args.show:
        cues = load_show_from_file(args.show)
    elif args.json:
        try:
            show_data = json.loads(args.json)
            if isinstance(show_data, dict) and 'cues' in show_data:
                cues = show_data['cues']
            elif isinstance(show_data, list):
                cues = show_data
        except Exception as e:
            logger.error(f"Error parsing JSON: {e}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

    if not cues:
        print("No cues to execute")
        sys.exit(1)

    if setup_gpio():
        success = execute_show(cues)
        if success:
            print("Show executed successfully")
            sys.exit(0)
        else:
            print("Show execution failed")
            sys.exit(1)
    else:
        print("GPIO setup failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
