#!/bin/bash
# GPIO initialization script for Raspberry Pi Zero W2
# This script sets GPIO pins 2, 3, 4, 5, and 6 to HIGH
# and all other GPIO pins to LOW, with special handling for GPIO 9

# Log file
LOG_FILE="/var/log/gpio_init.log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Create log file if it doesn't exist
touch "$LOG_FILE"
log_message "Starting GPIO initialization"

# Check if GPIO sysfs interface is available
if [ ! -d "/sys/class/gpio" ]; then
    log_message "ERROR: GPIO sysfs interface not available"
    exit 1
fi

# Function to set a GPIO pin
set_gpio() {
    PIN=$1
    DIRECTION=$2
    VALUE=$3
    
    # Export the GPIO pin if not already exported
    if [ ! -d "/sys/class/gpio/gpio$PIN" ]; then
        echo "$PIN" > /sys/class/gpio/export
        sleep 0.1
    fi
    
    # Set direction
    echo "$DIRECTION" > /sys/class/gpio/gpio$PIN/direction
    
    # Set value if output
    if [ "$DIRECTION" = "out" ]; then
        echo "$VALUE" > /sys/class/gpio/gpio$PIN/value
        log_message "GPIO $PIN set to $VALUE"
    fi
}

# Set GPIO pins 2, 3, 4, 5, and 6 to HIGH
for PIN in 2 3 4 5 6; do
    set_gpio $PIN "out" "1"
done

# Set all other GPIO pins to LOW
for PIN in 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27; do
    set_gpio $PIN "out" "0"
done

# Special handling for GPIO 9 to ensure it stays LOW
set_gpio 9 "out" "0"
# Set pull-down for GPIO 9 using raspi-gpio utility if available
if command -v raspi-gpio &> /dev/null; then
    raspi-gpio set 9 pd
    log_message "Set pull-down resistor for GPIO 9"
fi

log_message "GPIO initialization complete"
exit 0