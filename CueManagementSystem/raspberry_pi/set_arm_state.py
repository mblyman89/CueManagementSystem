#!/usr/bin/env python3
"""
Arm/Disarm Control Script for Raspberry Pi

This script controls the ARM pin for the firework control system.

Usage:
    python3 set_arm_state.py --armed=1  # Arm the system
    python3 set_arm_state.py --armed=0  # Disarm the system
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
logger = logging.getLogger("arm_control")

# GPIO Pin Configuration
# Arm control pin - Active HIGH (LOW when disarmed, HIGH when armed)
ARM_PIN = 21
ARM_ACTIVE_HIGH = True  # HIGH = armed


def setup_gpio():
    """Initialize GPIO pins"""
    try:
        # Use BCM pin numbering
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Setup ARM pin as output
        GPIO.setup(ARM_PIN, GPIO.OUT)

        logger.info("GPIO pins initialized successfully")
        return True
    except Exception as e:
        logger.error(f"GPIO setup failed: {e}")
        return False


def set_arm_state(armed):
    """
    Set the arm state of the system

    Args:
        armed (bool): True to arm, False to disarm
    """
    try:
        # Set ARM pin state based on active high/low configuration
        pin_state = GPIO.HIGH if (armed and ARM_ACTIVE_HIGH) or (not armed and not ARM_ACTIVE_HIGH) else GPIO.LOW
        GPIO.output(ARM_PIN, pin_state)

        status = "ARMED" if armed else "DISARMED"
        logger.info(f"System {status} - ARM pin {ARM_PIN} set to {pin_state}")
        return True
    except Exception as e:
        logger.error(f"Failed to {'arm' if armed else 'disarm'} system: {e}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Arm/disarm firework control system")
    parser.add_argument("--armed", type=int, required=True, choices=[0, 1],
                        help="1 to arm the system, 0 to disarm")

    args = parser.parse_args()
    armed = bool(args.armed)

    if setup_gpio():
        success = set_arm_state(armed)
        if success:
            print(f"System {'armed' if armed else 'disarmed'} successfully")
            sys.exit(0)
        else:
            print(f"Failed to {'arm' if armed else 'disarm'} system")
            sys.exit(1)
    else:
        print("GPIO setup failed")
        sys.exit(1)


if __name__ == "__main__":
    main()