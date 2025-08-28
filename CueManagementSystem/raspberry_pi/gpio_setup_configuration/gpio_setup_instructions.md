# Raspberry Pi Zero W2 GPIO Pin Initialization - Setup Instructions

This document provides detailed instructions for setting up GPIO pin initialization on your Raspberry Pi Zero W2 using three different methods. Choose the method that best suits your needs.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Method 1: Python Script with Systemd Service](#method-1-python-script-with-systemd-service)
3. [Method 2: Device Tree Overlay](#method-2-device-tree-overlay)
4. [Method 3: Shell Script with rc.local](#method-3-shell-script-with-rclocal)
5. [Testing Your Configuration](#testing-your-configuration)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

Before proceeding with any method, ensure you have:

- A Raspberry Pi Zero W2 with Raspberry Pi OS installed
- SSH access or direct terminal access to your Pi
- Internet connection for installing packages (if needed)
- Basic knowledge of Linux commands
- Root/sudo privileges

## Method 1: Python Script with Systemd Service

This method uses a Python script controlled by a systemd service to initialize GPIO pins at boot.

### Step 1: Install Required Packages

```bash
sudo apt update
sudo apt install -y python3-rpi.gpio
```

### Step 2: Create the Python Script

1. Create the script file:

```bash
sudo nano /home/pi/gpio_init.py
```

2. Copy the contents of the `gpio_init.py` file from this repository into the editor.

3. Save and exit (Ctrl+X, then Y, then Enter).

4. Make the script executable:

```bash
sudo chmod +x /home/pi/gpio_init.py
```

### Step 3: Create the Systemd Service

1. Create the service file:

```bash
sudo nano /etc/systemd/system/gpio-init.service
```

2. Copy the contents of the `gpio-init.service` file from this repository into the editor.

3. Save and exit.

### Step 4: Enable and Start the Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable gpio-init.service
sudo systemctl start gpio-init.service
```

### Step 5: Check Service Status

```bash
sudo systemctl status gpio-init.service
```

You should see "Active: active" in the output, indicating the service is running.

## Method 2: Device Tree Overlay

This method uses device tree overlays to configure GPIO pins very early in the boot process.

### Step 1: Edit the config.txt File

1. Open the config.txt file:

```bash
sudo nano /boot/config.txt
```

2. Add the following lines at the end of the file (or copy from `gpio-config.txt`):

```
# GPIO configuration
dtoverlay=gpio-hog,gpio2=op,dh,gpio3=op,dh,gpio4=op,dh,gpio5=op,dh,gpio6=op,dh,gpio9=op,dl,pd
```

3. Save and exit.

### Step 2: Reboot the Raspberry Pi

```bash
sudo reboot
```

## Method 3: Shell Script with rc.local

This method uses a shell script called from `/etc/rc.local` to initialize GPIO pins during boot.

### Step 1: Create the Shell Script

1. Create the script file:

```bash
sudo nano /home/pi/gpio_init.sh
```

2. Copy the contents of the `gpio_init.sh` file from this repository into the editor.

3. Save and exit.

4. Make the script executable:

```bash
sudo chmod +x /home/pi/gpio_init.sh
```

### Step 2: Edit rc.local

1. Open the rc.local file:

```bash
sudo nano /etc/rc.local
```

2. Add the following line before the `exit 0` line:

```bash
/home/pi/gpio_init.sh &
```

3. Save and exit.

### Step 3: Reboot the Raspberry Pi

```bash
sudo reboot
```

## Testing Your Configuration

After implementing any of the methods above, you can verify that the GPIO pins are set correctly:

### Using the GPIO Command Line Tool

1. Install the GPIO utility if not already installed:

```bash
sudo apt install -y raspi-gpio
```

2. Check the state of all GPIO pins:

```bash
raspi-gpio get
```

3. Verify that GPIO pins 2, 3, 4, 5, and 6 show `level=1` and all others show `level=0`.

### Using Python

You can also create a simple Python script to check the GPIO states:

```python
import RPi.GPIO as GPIO

# Use BCM pin numbering
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Pins to check
high_pins = [2, 3, 4, 5, 6]
low_pins = [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]

# Check high pins
print("Pins that should be HIGH:")
for pin in high_pins:
    GPIO.setup(pin, GPIO.IN)
    state = GPIO.input(pin)
    print(f"GPIO {pin}: {'HIGH' if state else 'LOW'}")

# Check low pins
print("\nPins that should be LOW:")
for pin in low_pins:
    GPIO.setup(pin, GPIO.IN)
    state = GPIO.input(pin)
    print(f"GPIO {pin}: {'HIGH' if state else 'LOW'}")

GPIO.cleanup()
```

Save this as `check_gpio.py` and run it with `python3 check_gpio.py`.

## Troubleshooting

### GPIO Pins Not Setting Correctly

1. **Check for Conflicts**: Ensure no other services or programs are controlling the same GPIO pins.

2. **Check Permissions**: Make sure your scripts have the necessary permissions to access GPIO.

3. **Hardware Issues**: Verify there are no hardware connections forcing pins to specific states.

4. **Log Files**: Check the log files for errors:
   - For Method 1: `sudo journalctl -u gpio-init.service`
   - For Method 3: `cat /var/log/gpio_init.log`

### Service Not Starting

If the systemd service isn't starting:

```bash
sudo systemctl status gpio-init.service
```

Look for error messages in the output and address them accordingly.

### External Pull-Down Resistors

If you're having trouble keeping GPIO 9 LOW, consider adding an external 10kΩ pull-down resistor between the pin and ground.