"""
Output Toggle Control Script
============================

Controls shift register outputs on Raspberry Pi by toggling Output Enable and Serial Clear pins.

Features:
- Output Enable pin control
- Serial Clear pin control
- Output enabling/disabling
- State persistence to JSON
- GPIO pin management
- Command-line interface

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

import RPi.GPIO as GPIO
import sys
import json

# GPIO Pin Definitions (BCM numbering)
OUTPUT_ENABLE_PINS = [2, 3, 4, 5, 6]      # Active LOW (LOW=enabled, HIGH=disabled)
SERIAL_CLEAR_PINS = [13, 16, 19, 20, 26]  # Active HIGH (HIGH=enabled, LOW=disabled)

# State file location
STATE_FILE = "/tmp/gpio_state.json"

def setup_gpio():
    """Initialize GPIO pins"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # Setup Output Enable pins
    for pin in OUTPUT_ENABLE_PINS:
        GPIO.setup(pin, GPIO.OUT)
    
    # Setup Serial Clear pins
    for pin in SERIAL_CLEAR_PINS:
        GPIO.setup(pin, GPIO.OUT)

def save_state(outputs_enabled, armed=None):
    """Save current GPIO state to file"""
    try:
        # Read existing state to preserve arm status if not specified
        state = {
            "outputs_enabled": outputs_enabled,
            "armed": False,
            "pin_states": {
                "output_enable": [not outputs_enabled] * 5,  # Inverted because active LOW
                "serial_clear": [outputs_enabled] * 5,
                "data": [False] * 5,
                "serial_clock": [False] * 5,
                "register_clock": [False] * 5,
                "arm": False
            }
        }
        
        # Try to read existing state to preserve arm status
        try:
            with open(STATE_FILE, 'r') as f:
                existing_state = json.load(f)
                if armed is None:
                    state["armed"] = existing_state.get("armed", False)
                    state["pin_states"]["arm"] = existing_state.get("pin_states", {}).get("arm", False)
                else:
                    state["armed"] = armed
                    state["pin_states"]["arm"] = armed
        except:
            pass
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
    except Exception as e:
        pass  # Don't fail if we can't write state file

def enable_outputs():
    """Enable shift register outputs"""
    # Set OE pins LOW (active LOW - enables outputs)
    for pin in OUTPUT_ENABLE_PINS:
        GPIO.output(pin, GPIO.LOW)
    
    # Set SRCLR pins HIGH (active HIGH - enables shift registers)
    for pin in SERIAL_CLEAR_PINS:
        GPIO.output(pin, GPIO.HIGH)
    
    save_state(True)
    return {"status": "success", "outputs_enabled": True}

def disable_outputs():
    """Disable shift register outputs"""
    # Set OE pins HIGH (active LOW - disables outputs)
    for pin in OUTPUT_ENABLE_PINS:
        GPIO.output(pin, GPIO.HIGH)
    
    # Set SRCLR pins LOW (active HIGH - disables/clears shift registers)
    for pin in SERIAL_CLEAR_PINS:
        GPIO.output(pin, GPIO.LOW)
    
    save_state(False)
    return {"status": "success", "outputs_enabled": False}

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Toggle shift register outputs')
    parser.add_argument('--enabled', type=int, choices=[0, 1], required=True,
                        help='Enable (1) or disable (0) outputs')
    
    try:
        args = parser.parse_args()
        setup_gpio()
        
        if args.enabled == 1:
            result = enable_outputs()
        else:
            result = disable_outputs()
        
        print(json.dumps(result))
        sys.exit(0 if result["status"] == "success" else 1)
        
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()