"""
GPIO Status Reporter
====================

Retrieves and formats current GPIO pin states from JSON state file for GUI display.

Features:
- GPIO state retrieval from JSON
- Pin state formatting
- Arm state reporting
- Data, serial clock, register clock status
- Output enable status
- Serial clear status
- GUI integration support

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

import sys
import json
import os

# State file location
STATE_FILE = "/tmp/gpio_state.json"

# GPIO Pin Assignments (BCM numbering)
OUTPUT_ENABLE_PINS = [2, 3, 4, 5, 6]      # Active LOW
SERIAL_CLEAR_PINS = [13, 16, 19, 20, 26]  # Active HIGH
DATA_PINS = [7, 8, 12, 14, 15]
SCLK_PINS = [17, 18, 22, 23, 27]
RCLK_PINS = [9, 10, 11, 24, 25]
ARM_PIN = 21                               # Active HIGH

# Default state (safe state)
DEFAULT_STATE = {
    "outputs_enabled": False,
    "armed": False,
    "pin_states": {
        "output_enable": [True, True, True, True, True],  # HIGH = disabled
        "serial_clear": [False, False, False, False, False],  # LOW = disabled
        "data": [False, False, False, False, False],
        "serial_clock": [False, False, False, False, False],
        "register_clock": [False, False, False, False, False],
        "arm": False
    }
}

def get_all_states():
    """Get states from the state file and format for GUI"""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
        else:
            # Return default state if file doesn't exist
            state = DEFAULT_STATE
        
        # Convert to GUI-expected format
        pin_states = state.get("pin_states", DEFAULT_STATE["pin_states"])
        
        result = {
            "status": "success",
            "timestamp": os.path.getmtime(STATE_FILE) if os.path.exists(STATE_FILE) else 0,
            
            # ARM pin
            "arm_pin": {
                "pin": ARM_PIN,
                "state": pin_states.get("arm", False)
            },
            
            # Data pins (5 chains)
            "data_pins": [
                {"pin": DATA_PINS[i], "state": pin_states.get("data", [False]*5)[i]}
                for i in range(5)
            ],
            
            # Serial Clock pins (5 chains)
            "sclk_pins": [
                {"pin": SCLK_PINS[i], "state": pin_states.get("serial_clock", [False]*5)[i]}
                for i in range(5)
            ],
            
            # Register Clock pins (5 chains)
            "rclk_pins": [
                {"pin": RCLK_PINS[i], "state": pin_states.get("register_clock", [False]*5)[i]}
                for i in range(5)
            ],
            
            # Output Enable pins (5 chains) - Active LOW
            "oe_pins": [
                {"pin": OUTPUT_ENABLE_PINS[i], "state": pin_states.get("output_enable", [True]*5)[i]}
                for i in range(5)
            ],
            
            # Serial Clear pins (5 chains) - Active HIGH
            "srclr_pins": [
                {"pin": SERIAL_CLEAR_PINS[i], "state": pin_states.get("serial_clear", [False]*5)[i]}
                for i in range(5)
            ]
        }
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to read GPIO state: {str(e)}"
        }

def main():
    try:
        result = get_all_states()
        print(json.dumps(result))
        sys.exit(0 if result["status"] == "success" else 1)
        
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()