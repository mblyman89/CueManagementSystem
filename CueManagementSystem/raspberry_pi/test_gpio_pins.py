#!/usr/bin/env python3
"""
Test script to check GPIO pin behavior with lgpio
"""
import RPi.GPIO as GPIO
import lgpio
import time
import sys

OUTPUT_ENABLE_PINS = [2, 3, 4, 5, 6]

print("Testing GPIO pins...")
print(f"Python version: {sys.version}")

try:
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    print("\n=== STEP 1: Setting up pins as outputs ===")
    for pin in OUTPUT_ENABLE_PINS:
        GPIO.setup(pin, GPIO.OUT)
        print(f"  ✓ Pin {pin} setup as OUTPUT")
    
    print("\n=== STEP 2: Setting all pins HIGH ===")
    for pin in OUTPUT_ENABLE_PINS:
        GPIO.output(pin, GPIO.HIGH)
        print(f"  ✓ Pin {pin} set to HIGH")
    
    print("\n=== STEP 3: Reading pin states using lgpio ===")
    handle = lgpio.gpiochip_open(0)
    for pin in OUTPUT_ENABLE_PINS:
        try:
            value = lgpio.gpio_read(handle, pin)
            print(f"  Pin {pin}: {value} ({'HIGH' if value == 1 else 'LOW'})")
        except Exception as e:
            print(f"  Pin {pin}: Error reading - {e}")
    lgpio.gpiochip_close(handle)
    
    print("\n=== STEP 4: Waiting 2 seconds ===")
    time.sleep(2)
    
    print("\n=== STEP 5: Reading again with lgpio ===")
    handle = lgpio.gpiochip_open(0)
    for pin in OUTPUT_ENABLE_PINS:
        try:
            value = lgpio.gpio_read(handle, pin)
            print(f"  Pin {pin}: {value} ({'HIGH' if value == 1 else 'LOW'})")
        except Exception as e:
            print(f"  Pin {pin}: Error reading - {e}")
    lgpio.gpiochip_close(handle)
    
    print("\n=== STEP 6: Script will exit WITHOUT calling GPIO.cleanup() ===")
    print("Check with voltmeter - pins should maintain their HIGH state")
    print("\nAfter this script exits, run:")
    print("  sudo python3 get_gpio_status.py")
    print("to verify the pins can be read correctly")
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()