#!/usr/bin/env python3
"""
GPIO Status Script for Raspberry Pi

This script reads the current status of all GPIO pins used in the CueShifter system
and outputs the data in JSON format for the GUI application to display.

Usage:
    python3 get_gpio_status.py

Output:
    JSON formatted data containing the state of all GPIO pins
"""

import json
import time

try:
    import RPi.GPIO as GPIO
except ImportError:
    # For testing on non-Pi systems
    print(json.dumps({"error": "RPi.GPIO module not available - not running on a Raspberry Pi"}))
    exit(1)

# Define GPIO pin assignments
GPIO_PINS = {
    # ARM/DISARM pin
    "arm_pin": 21,

    # DATA pins for each chain
    "data_pins": [7, 8, 12, 14, 15],

    # SCLK (Serial Clock) pins for each chain
    "sclk_pins": [17, 18, 22, 23, 27],

    # RCLK (Register Clock) pins for each chain
    "rclk_pins": [9, 10, 11, 24, 25],

    # OE (Output Enable) pins for each chain
    "oe_pins": [2, 3, 4, 5, 6],

    # SRCLR (Serial Clear) pins for each chain
    "srclr_pins": [13, 16, 19, 20, 26]
}


def get_gpio_status():
    """Read and return the status of all GPIO pins"""
    try:
        # Set up GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Initialize result dictionary
        result = {
            "timestamp": time.time(),
            "arm_pin": {},
            "data_pins": [],
            "sclk_pins": [],
            "rclk_pins": [],
            "oe_pins": [],
            "srclr_pins": []
        }

        # Read ARM/DISARM pin
        arm_pin = GPIO_PINS["arm_pin"]
        GPIO.setup(arm_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        result["arm_pin"] = {
            "pin": arm_pin,
            "state": GPIO.input(arm_pin)
        }

        # Read DATA pins
        for pin in GPIO_PINS["data_pins"]:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            result["data_pins"].append({
                "pin": pin,
                "state": GPIO.input(pin)
            })

        # Read SCLK pins
        for pin in GPIO_PINS["sclk_pins"]:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            result["sclk_pins"].append({
                "pin": pin,
                "state": GPIO.input(pin)
            })

        # Read RCLK pins
        for pin in GPIO_PINS["rclk_pins"]:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            result["rclk_pins"].append({
                "pin": pin,
                "state": GPIO.input(pin)
            })

        # Read OE pins
        for pin in GPIO_PINS["oe_pins"]:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            result["oe_pins"].append({
                "pin": pin,
                "state": GPIO.input(pin)
            })

        # Read SRCLR pins
        for pin in GPIO_PINS["srclr_pins"]:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            result["srclr_pins"].append({
                "pin": pin,
                "state": GPIO.input(pin)
            })

        return result

    except Exception as e:
        return {"error": str(e)}

    finally:
        # Clean up GPIO
        GPIO.cleanup()


if __name__ == "__main__":
    # Get GPIO status
    status = get_gpio_status()

    # Output as JSON
    print(json.dumps(status))