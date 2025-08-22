#!/usr/bin/env python3
"""
Toggle Outputs Script for Raspberry Pi

This script controls the Output Enable (OE) and Serial Clear (SRCLR) pins
for 5 chains of shift registers.

Usage:
    python3 toggle_outputs.py --enabled=1  # Enable outputs
    python3 toggle_outputs.py --enabled=0  # Disable outputs
"""

import argparse
import RPi.GPIO as GPIO
import time
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/home/pi/gpio_control.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("toggle_outputs")

# GPIO Pin Configuration
# Output Enable pins (5 chains) - HIGH when disabled, LOW when enabled
OUTPUT_ENABLE_PINS = [2, 3, 4, 5, 6]
OUTPUT_ENABLE_ACTIVE_LOW = [True, True, True, True, True]  # LOW = enabled

# Serial Clear pins (5 chains) - LOW when disabled, HIGH when enabled
SERIAL_CLEAR_PINS = [13, 16, 19, 20, 26]
SERIAL_CLEAR_ACTIVE_HIGH = [True, True, True, True, True]  # HIGH = enabled


def setup_gpio():
    """Initialize GPIO pins"""
    try:
        # Use BCM pin numbering
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Setup Output Enable pins as outputs
        for pin in OUTPUT_ENABLE_PINS:
            GPIO.setup(pin, GPIO.OUT)

        # Setup Serial Clear pins as outputs
        for pin in SERIAL_CLEAR_PINS:
            GPIO.setup(pin, GPIO.OUT)

        logger.info("GPIO pins initialized successfully")
        return True
    except Exception as e:
        logger.error(f"GPIO setup failed: {e}")
        return False


def enable_outputs(enabled):
    """
    Enable or disable outputs by controlling OE and SRCLR pins

    Args:
        enabled (bool): True to enable outputs, False to disable
    """
    try:
        # Set Output Enable pins
        for i, pin in enumerate(OUTPUT_ENABLE_PINS):
            # OE pins are active LOW (LOW = enabled)
            pin_state = GPIO.LOW if enabled else GPIO.HIGH
            GPIO.output(pin, pin_state)
            logger.info(f"OE pin {pin} (chain {i + 1}) set to {pin_state}")

        # Set Serial Clear pins
        for i, pin in enumerate(SERIAL_CLEAR_PINS):
            # SRCLR pins are active HIGH (HIGH = enabled/not clearing)
            pin_state = GPIO.HIGH if enabled else GPIO.LOW
            GPIO.output(pin, pin_state)
            logger.info(f"SRCLR pin {pin} (chain {i + 1}) set to {pin_state}")

        status = "ENABLED" if enabled else "DISABLED"
        logger.info(f"All outputs {status}")
        return True
    except Exception as e:
        logger.error(f"Failed to {'enable' if enabled else 'disable'} outputs: {e}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Toggle outputs for firework control system")
    parser.add_argument("--enabled", type=int, required=True, choices=[0, 1],
                        help="1 to enable outputs, 0 to disable")

    args = parser.parse_args()
    enabled = bool(args.enabled)

    if setup_gpio():
        success = enable_outputs(enabled)
        if success:
            print(f"Outputs {'enabled' if enabled else 'disabled'} successfully")
            sys.exit(0)
        else:
            print(f"Failed to {'enable' if enabled else 'disable'} outputs")
            sys.exit(1)
    else:
        print("GPIO setup failed")
        sys.exit(1)


if __name__ == "__main__":
    main()