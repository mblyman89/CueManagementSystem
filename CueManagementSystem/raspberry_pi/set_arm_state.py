#!/usr/bin/env python3
"""
Set ARM pin state for firework control system
"""
import RPi.GPIO as GPIO
import sys
import json

# GPIO Pin Definitions (BCM numbering)
ARM_PIN = 21  # Active HIGH (HIGH=armed, LOW=disarmed)

# State file location
STATE_FILE = "/tmp/gpio_state.json"

def setup_gpio():
    """Initialize GPIO pins"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(ARM_PIN, GPIO.OUT)

def save_state(armed):
    """Save current GPIO state to file"""
    try:
        # Read existing state to preserve outputs_enabled status
        state = {
            "outputs_enabled": False,
            "armed": armed,
            "pin_states": {
                "output_enable": [True] * 5,
                "serial_clear": [False] * 5,
                "data": [False] * 5,
                "serial_clock": [False] * 5,
                "register_clock": [False] * 5,
                "arm": armed
            }
        }
        
        # Try to read existing state to preserve outputs_enabled status
        try:
            with open(STATE_FILE, 'r') as f:
                existing_state = json.load(f)
                state["outputs_enabled"] = existing_state.get("outputs_enabled", False)
                state["pin_states"]["output_enable"] = existing_state.get("pin_states", {}).get("output_enable", [True] * 5)
                state["pin_states"]["serial_clear"] = existing_state.get("pin_states", {}).get("serial_clear", [False] * 5)
        except:
            pass
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
    except Exception as e:
        pass  # Don't fail if we can't write state file

def arm():
    """Arm the system"""
    GPIO.output(ARM_PIN, GPIO.HIGH)
    save_state(True)
    return {"status": "success", "armed": True}

def disarm():
    """Disarm the system"""
    GPIO.output(ARM_PIN, GPIO.LOW)
    save_state(False)
    return {"status": "success", "armed": False}

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Set arm state')
    parser.add_argument('--armed', type=int, choices=[0, 1], required=True,
                        help='Arm (1) or disarm (0) the system')
    
    try:
        args = parser.parse_args()
        setup_gpio()
        
        if args.armed == 1:
            result = arm()
        else:
            result = disarm()
        
        print(json.dumps(result))
        sys.exit(0 if result["status"] == "success" else 1)
        
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()