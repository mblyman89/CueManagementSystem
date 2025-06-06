#!/usr/bin/env python3
"""
Test script for MQTT communication with Raspberry Pi

This script tests the MQTT communication between the Cue Management System
and the Raspberry Pi by sending a test cue and command.

Usage:
    python3 test_mqtt_communication.py
"""

import asyncio
import json
import sys
import os
import time

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hardware.mqtt_client import MQTTClient
from hardware.shift_register import ShiftRegisterManager
from controllers.hardware_controller import HardwareController


async def test_mqtt_communication():
    """Test MQTT communication with Raspberry Pi"""
    print("Starting MQTT communication test...")
    
    # Create a hardware controller
    hardware_controller = HardwareController()
    
    # Set connection parameters (update these as needed)
    host = input("Enter MQTT broker host (default: raspberrypi.local): ") or "raspberrypi.local"
    port = int(input("Enter MQTT broker port (default: 1883): ") or "1883")
    username = input("Enter MQTT username (optional): ")
    password = input("Enter MQTT password (optional): ")
    
    # Set the connection parameters
    hardware_controller.set_connection_params(host, port, username, password)
    
    # Connect to the MQTT broker
    print(f"Connecting to MQTT broker at {host}:{port}...")
    success = hardware_controller.connect()
    
    if not success:
        print("Failed to initiate connection to MQTT broker")
        return
        
    print("Connection initiated. Waiting for connection to establish...")
    
    # Wait for connection to establish
    for _ in range(10):
        if hardware_controller.is_hardware_connected():
            print("Connected to MQTT broker")
            break
        await asyncio.sleep(1)
    else:
        print("Timed out waiting for connection")
        hardware_controller.disconnect()
        return
    
    # Create a test cue
    test_cue = {
        "cue_number": "TEST-001",
        "cue_type": "SHOT",
        "output_values": [1, 5, 9]  # This will activate outputs 1, 5, and 9
    }
    
    # Send the test cue
    print(f"Sending test cue: {test_cue}")
    success, message = await hardware_controller.send_cue(test_cue)
    
    if success:
        print(f"Test cue sent successfully: {message}")
    else:
        print(f"Failed to send test cue: {message}")
    
    # Wait a moment
    await asyncio.sleep(2)
    
    # Send a command to clear all outputs
    print("Sending command to clear all outputs...")
    success, message = await hardware_controller.clear_all_outputs()
    
    if success:
        print(f"Clear command sent successfully: {message}")
    else:
        print(f"Failed to send clear command: {message}")
    
    # Wait a moment
    await asyncio.sleep(2)
    
    # Disconnect
    print("Disconnecting from MQTT broker...")
    hardware_controller.disconnect()
    
    print("Test completed")


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_mqtt_communication())