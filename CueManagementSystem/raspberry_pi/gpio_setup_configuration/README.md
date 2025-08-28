# Raspberry Pi Zero W2 GPIO Pin Initialization

This project provides solutions for initializing GPIO pins on a Raspberry Pi Zero W2 during boot-up. Specifically, it sets:

- GPIO pins 2, 3, 4, 5, and 6 to HIGH state
- All other GPIO pins to LOW state
- Special handling for GPIO pin 9 to ensure it stays LOW

## Background

The Raspberry Pi's GPIO pins have default states when the Pi boots up:
- All pins are initially set as inputs
- GPIO pins 0-8 have internal pull-up resistors enabled (they read HIGH when floating)
- GPIO pins 9-27 have internal pull-down resistors enabled (they read LOW when floating)

For projects requiring specific pin states at boot time, these default configurations may not be suitable. This project provides multiple methods to ensure your GPIO pins are in the correct state as early as possible in the boot process.

## Solution Methods

This repository includes three different methods to initialize GPIO pins:

1. **Python Script with Systemd Service** - The most flexible and maintainable approach
2. **Device Tree Overlay** - Sets pin states very early in the boot process
3. **Shell Script for rc.local** - A traditional approach that's easy to understand

Choose the method that best suits your needs based on when in the boot process you need the pins initialized and your comfort level with different technologies.

## File Structure

- `gpio_init.py` - Python script for GPIO initialization
- `gpio-init.service` - Systemd service file to run the Python script at boot
- `gpio-config.txt` - Device tree overlay configuration for /boot/config.txt
- `gpio_init.sh` - Shell script that can be called from /etc/rc.local
- `setup_instructions.md` - Detailed installation and setup instructions
- `gpio_README.md` - This file

## Requirements

- Raspberry Pi Zero W2
- Raspberry Pi OS (Bullseye or newer recommended)
- Python 3 with RPi.GPIO library (for Python method)

## Quick Start

See `setup_instructions.md` for detailed installation instructions for each method.

## License

This project is released under the MIT License.