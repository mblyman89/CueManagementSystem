# MQTT Communication with Raspberry Pi

This document provides instructions for setting up and using the MQTT communication between the Cue Management System and a Raspberry Pi for controlling shift registers.

## Overview

The Cue Management System can communicate with a Raspberry Pi using either SSH or MQTT. MQTT is the recommended method for real-time cue data transmission as it is:

- More robust and reliable for real-time communication
- Non-blocking (doesn't interfere with the UI)
- Designed for IoT applications
- Supports automatic reconnection
- Lightweight and efficient

## Requirements

### On the Cue Management System (PC/Mac)

- Python 3.6+
- PySide6
- paho-mqtt (`pip install paho-mqtt`)

### On the Raspberry Pi

- Python 3.6+
- paho-mqtt (`pip install paho-mqtt`)
- RPi.GPIO (`pip install RPi.GPIO`)
- Mosquitto MQTT broker (`sudo apt install mosquitto mosquitto-clients`)

## Setting Up the Raspberry Pi

1. Install the required packages:

```bash
sudo apt update
sudo apt install -y mosquitto mosquitto-clients python3-pip
pip3 install paho-mqtt RPi.GPIO
```

2. Configure Mosquitto MQTT broker to accept connections:

```bash
sudo nano /etc/mosquitto/mosquitto.conf
```

Add the following lines:

```
listener 1883
allow_anonymous true
```

3. Restart the Mosquitto service:

```bash
sudo systemctl restart mosquitto
```

4. Copy the `raspberry_pi_mqtt_client.py` script to the Raspberry Pi:

```bash
scp CueManagementSystem/hardware/raspberry_pi_mqtt_client.py pi@raspberrypi.local:~/
```

5. Make the script executable:

```bash
ssh pi@raspberrypi.local "chmod +x ~/raspberry_pi_mqtt_client.py"
```

6. Set up the script to run on boot (optional):

```bash
ssh pi@raspberrypi.local "echo '@reboot python3 ~/raspberry_pi_mqtt_client.py' | crontab -"
```

## Wiring the Shift Registers

Connect the shift registers to the Raspberry Pi GPIO pins as follows:

- Data Pin (DS): GPIO 17
- Latch Pin (ST_CP): GPIO 27
- Clock Pin (SH_CP): GPIO 22
- Clear Pin (MR): GPIO 23 (optional)
- Output Enable Pin (OE): GPIO 24 (optional)

For multiple shift registers, connect them in a daisy chain:
- Connect the first shift register's Q7' (serial output) to the second shift register's DS (serial input)
- Connect all shift registers' ST_CP pins together to the Raspberry Pi's Latch Pin
- Connect all shift registers' SH_CP pins together to the Raspberry Pi's Clock Pin

## Using MQTT Communication in the Cue Management System

1. Launch the Cue Management System
2. Click the "MODE" button to open the Mode Selector dialog
3. Select "Hardware Mode"
4. Select "MQTT (Recommended)" as the communication method
5. Enter the Raspberry Pi's hostname or IP address
6. Enter the MQTT port (default: 1883)
7. Enter username and password if required
8. Click "OK" to apply the settings

## Testing the Communication

You can test the MQTT communication using the provided test script:

```bash
python3 CueManagementSystem/tests/test_mqtt_communication.py
```

This script will:
1. Connect to the MQTT broker
2. Send a test cue that activates outputs 1, 5, and 9
3. Send a command to clear all outputs
4. Disconnect from the MQTT broker

## Troubleshooting

### Connection Issues

- Ensure the Raspberry Pi is powered on and connected to the network
- Verify that the Mosquitto MQTT broker is running on the Raspberry Pi:
  ```bash
  sudo systemctl status mosquitto
  ```
- Check that the hostname or IP address is correct
- Ensure the MQTT port (default: 1883) is not blocked by a firewall

### Shift Register Issues

- Verify the wiring connections between the Raspberry Pi and shift registers
- Check that the GPIO pins are correctly defined in the `raspberry_pi_mqtt_client.py` script
- Ensure the shift registers are powered correctly

### Debugging

- Check the logs on the Raspberry Pi:
  ```bash
  tail -f /tmp/cue_system.log
  ```
- Run the Raspberry Pi client in the foreground for more verbose output:
  ```bash
  python3 ~/raspberry_pi_mqtt_client.py --host localhost
  ```

## Advanced Configuration

### Securing MQTT Communication

For production use, it's recommended to secure the MQTT broker:

1. Create a password file:
   ```bash
   sudo mosquitto_passwd -c /etc/mosquitto/passwd username
   ```

2. Update the Mosquitto configuration:
   ```bash
   sudo nano /etc/mosquitto/mosquitto.conf
   ```

   Add/modify the following lines:
   ```
   listener 1883
   allow_anonymous false
   password_file /etc/mosquitto/passwd
   ```

3. Restart Mosquitto:
   ```bash
   sudo systemctl restart mosquitto
   ```

4. Update the connection settings in the Cue Management System to include the username and password.

### Using TLS/SSL

For encrypted communication, you can set up TLS/SSL. Refer to the Mosquitto documentation for details.