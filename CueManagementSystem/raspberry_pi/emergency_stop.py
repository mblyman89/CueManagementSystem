"""
Emergency Stop Function
=======================

Critical safety function for Raspberry Pi that immediately disables all outputs and disarms the system.

Features:
- Immediate output disabling
- System disarming
- GPIO pin safety state setting
- State persistence to file
- Emergency shutdown protocol
- Hardware safety interlock

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

import RPi.GPIO as GPIO
import sys
import json

# GPIO Pin Definitions (BCM numbering)
OUTPUT_ENABLE_PINS = [2, 3, 4, 5, 6]
SERIAL_CLEAR_PINS = [13, 16, 19, 20, 26]
DATA_PINS = [7, 8, 12, 14, 15]
SCLK_PINS = [17, 18, 22, 23, 27]
RCLK_PINS = [9, 10, 11, 24, 25]
ARM_PIN = 21

# State file location
STATE_FILE = "/tmp/gpio_state.json"

def save_state():
    """Save safe state to file"""
    try:
        state = {
            "outputs_enabled": False,
            "armed": False,
            "pin_states": {
                "output_enable": [True] * 5,  # HIGH = disabled
                "serial_clear": [False] * 5,  # LOW = disabled
                "data": [False] * 5,
                "serial_clock": [False] * 5,
                "register_clock": [False] * 5,
                "arm": False
            }
        }
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
    except Exception as e:
        pass  # Don't fail if we can't write state file

def emergency_stop():
    """Immediately set all pins to safe state"""
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Disable outputs (OE HIGH - active LOW)
        for pin in OUTPUT_ENABLE_PINS:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)
        
        # Clear shift registers (SRCLR LOW - active HIGH)
        for pin in SERIAL_CLEAR_PINS:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
        
        # Set all data/clock pins LOW
        for pin in DATA_PINS + SCLK_PINS + RCLK_PINS:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
        
        # Disarm (ARM LOW)
        GPIO.setup(ARM_PIN, GPIO.OUT)
        GPIO.output(ARM_PIN, GPIO.LOW)
        
        # Save state
        save_state()
        
        return {
            "status": "success",
            "message": "Emergency stop executed - all outputs disabled and disarmed"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Emergency stop failed: {str(e)}"
        }

def main():
    result = emergency_stop()
    print(json.dumps(result))
    sys.exit(0 if result["status"] == "success" else 1)

if __name__ == "__main__":
    main()