#!/usr/bin/env python3
"""
GPIO Pin State Checker for Raspberry Pi Zero W2
This script checks the current state of all GPIO pins and reports their status.
"""

import RPi.GPIO as GPIO
import time

# Use BCM pin numbering
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Pins that should be HIGH
HIGH_PINS = [2, 3, 4, 5, 6]

# Pins that should be LOW (all others)
LOW_PINS = [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]

def check_pins():
    """Check the state of all GPIO pins"""
    print("\n=== GPIO Pin State Checker ===\n")
    
    # Check pins that should be HIGH
    print("Pins that should be HIGH:")
    high_correct = 0
    for pin in HIGH_PINS:
        GPIO.setup(pin, GPIO.IN)
        state = GPIO.input(pin)
        status = "✓ CORRECT" if state else "✗ WRONG"
        if state:
            high_correct += 1
        print(f"GPIO {pin}: {'HIGH' if state else 'LOW'} - {status}")
    
    high_percentage = (high_correct / len(HIGH_PINS)) * 100 if HIGH_PINS else 100
    print(f"\nHIGH pins correct: {high_correct}/{len(HIGH_PINS)} ({high_percentage:.1f}%)")
    
    # Check pins that should be LOW
    print("\nPins that should be LOW:")
    low_correct = 0
    for pin in LOW_PINS:
        GPIO.setup(pin, GPIO.IN)
        state = GPIO.input(pin)
        status = "✓ CORRECT" if not state else "✗ WRONG"
        if not state:
            low_correct += 1
        print(f"GPIO {pin}: {'HIGH' if state else 'LOW'} - {status}")
    
    low_percentage = (low_correct / len(LOW_PINS)) * 100 if LOW_PINS else 100
    print(f"\nLOW pins correct: {low_correct}/{len(LOW_PINS)} ({low_percentage:.1f}%)")
    
    # Overall result
    total_correct = high_correct + low_correct
    total_pins = len(HIGH_PINS) + len(LOW_PINS)
    total_percentage = (total_correct / total_pins) * 100 if total_pins else 100
    
    print(f"\nOverall: {total_correct}/{total_pins} pins in correct state ({total_percentage:.1f}%)")
    
    # Special check for GPIO 9
    GPIO.setup(9, GPIO.IN)
    state = GPIO.input(9)
    print(f"\nSpecial check for GPIO 9: {'HIGH' if state else 'LOW'} - {'✗ WRONG' if state else '✓ CORRECT'}")
    
    print("\n=== End of GPIO Check ===\n")

if __name__ == "__main__":
    try:
        check_pins()
    finally:
        GPIO.cleanup()