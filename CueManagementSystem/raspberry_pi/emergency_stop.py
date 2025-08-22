#!/usr/bin/env python3
"""
Emergency Stop Script for Raspberry Pi

This script immediately disables all outputs and disarms the system
in case of emergency.

Usage:
    python3 emergency_stop.py
"""

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
logger = logging.getLogger("emergency_stop")

# GPIO Pin Configuration
# Output Enable pins (5 chains) - HIGH when disabled, LOW when enabled
OUTPUT_ENABLE_PINS = [2, 3, 4, 5, 6]
OUTPUT_ENABLE_ACTIVE_LOW = [True, True, True, True, True]  # LOW = enabled

# Serial Clear pins (5 chains) - LOW when disabled, HIGH when enabled
SERIAL_CLEAR_PINS = [13, 16, 19, 20, 26]
SERIAL_CLEAR_ACTIVE_HIGH = [True, True, True, True, True]  # HIGH = enabled

# Arm control pin - Active HIGH (LOW when disarmed, HIGH when armed)
ARM_PIN = 21
ARM_ACTIVE_HIGH = True  # HIGH = armed


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

        # Setup ARM pin as output
        GPIO.setup(ARM_PIN, GPIO.OUT)

        logger.info("GPIO pins initialized successfully")
        return True
    except Exception as e:
        logger.error(f"GPIO setup failed: {e}")
        return False


def emergency_stop():
    """
    Emergency stop - immediately disable all outputs and disarm system
    """
    try:
        logger.critical("EMERGENCY STOP ACTIVATED")

        # First disarm the system
        disarm_state = GPIO.LOW if ARM_ACTIVE_HIGH else GPIO.HIGH
        GPIO.output(ARM_PIN, disarm_state)
        logger.info(f"System DISARMED - ARM pin {ARM_PIN} set to {disarm_state}")

        # Disable all outputs by setting OE pins to HIGH (disabled)
        for i, pin in enumerate(OUTPUT_ENABLE_PINS):
            GPIO.output(pin, GPIO.HIGH)  # HIGH = disabled for OE pins
            logger.info(f"OE pin {pin} (chain {i + 1}) set to HIGH (disabled)")

        # Clear all shift registers by setting SRCLR pins to LOW (clearing)
        for i, pin in enumerate(SERIAL_CLEAR_PINS):
            GPIO.output(pin, GPIO.LOW)  # LOW = clearing for SRCLR pins
            logger.info(f"SRCLR pin {pin} (chain {i + 1}) set to LOW (clearing)")

        logger.critical("EMERGENCY STOP COMPLETED - All outputs disabled and system disarmed")
        return True
    except Exception as e:
        logger.error(f"Emergency stop failed: {e}")
        return False


def main():
    """Main function"""
    print("EMERGENCY STOP INITIATED")

    if setup_gpio():
        success = emergency_stop()
        if success:
            print("Emergency stop completed successfully")
            sys.exit(0)
        else:
            print("Emergency stop failed")
            sys.exit(1)
    else:
        print("GPIO setup failed")
        sys.exit(1)


if __name__ == "__main__":
    main()