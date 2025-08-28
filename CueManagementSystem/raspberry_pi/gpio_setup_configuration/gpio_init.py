#!/usr/bin/env python3
"""
Raspberry Pi Zero W2 GPIO Pin Initialization Script
This script initializes GPIO pins to specific states at boot:
- GPIO pins 2, 3, 4, 5, and 6 are set HIGH
- All other GPIO pins are set LOW
- Special handling for GPIO 9 to ensure it stays LOW
"""

import RPi.GPIO as GPIO
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/gpio_init.log"),
        logging.StreamHandler()
    ]
)

# List of all GPIO pins we want to manage
ALL_PINS = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]

# Pins that should be HIGH
HIGH_PINS = [2, 3, 4, 5, 6]

# Pins that should be LOW (all others)
LOW_PINS = [pin for pin in ALL_PINS if pin not in HIGH_PINS]

def initialize_gpio():
    """Initialize all GPIO pins to their desired states"""
    try:
        # Use BCM pin numbering
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Set up pins that should be HIGH
        for pin in HIGH_PINS:
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)
            logging.info(f"GPIO {pin} set to HIGH")
        
        # Set up pins that should be LOW
        for pin in LOW_PINS:
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
            logging.info(f"GPIO {pin} set to LOW")
        
        # Special handling for GPIO 9 - ensure it's LOW with pull-down
        GPIO.setup(9, GPIO.OUT, initial=GPIO.LOW)
        # Add extra pull-down configuration for GPIO 9
        GPIO.setup(9, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(9, GPIO.OUT, initial=GPIO.LOW)
        logging.info("GPIO 9 set to LOW with extra pull-down configuration")
        
        # Verify the states
        verify_gpio_states()
        
        # Keep the script running to maintain GPIO states
        logging.info("GPIO initialization complete. Pins will maintain their states.")
        
        # Sleep for a while to ensure states are stable before exiting
        time.sleep(5)
        
    except Exception as e:
        logging.error(f"Error initializing GPIO pins: {e}")
    finally:
        # Don't clean up GPIO as we want to maintain the states
        pass

def verify_gpio_states():
    """Verify that all GPIO pins are in their expected states"""
    all_correct = True
    
    # Check HIGH pins
    for pin in HIGH_PINS:
        state = GPIO.input(pin)
        if state != GPIO.HIGH:
            logging.error(f"GPIO {pin} should be HIGH but is LOW")
            all_correct = False
        else:
            logging.info(f"GPIO {pin} verified HIGH")
    
    # Check LOW pins
    for pin in LOW_PINS:
        state = GPIO.input(pin)
        if state != GPIO.LOW:
            logging.error(f"GPIO {pin} should be LOW but is HIGH")
            all_correct = False
        else:
            logging.info(f"GPIO {pin} verified LOW")
    
    if all_correct:
        logging.info("All GPIO pins are in their expected states")
    else:
        logging.warning("Some GPIO pins are not in their expected states")

if __name__ == "__main__":
    logging.info("Starting GPIO initialization")
    initialize_gpio()
    logging.info("GPIO initialization script completed")