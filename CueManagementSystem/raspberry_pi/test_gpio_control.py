#!/usr/bin/env python3
"""
Test Script for GPIO Control via SSH

This script tests the SSH command execution for GPIO control by:
1. Testing SSH connection to the Raspberry Pi
2. Testing enable/disable outputs functionality
3. Testing arm/disarm functionality
4. Testing emergency abort functionality

Usage:
    python3 test_gpio_control.py
"""

import asyncio
import sys
import time
from controllers.system_mode_controller import SystemMode


async def test_ssh_connection(system_mode):
    """Test SSH connection to the Raspberry Pi"""
    print("\n=== Testing SSH Connection ===")

    # Test connection
    success, message = await system_mode.test_connection()
    print(f"Connection test result: {success}")
    print(f"Message: {message}")

    return success


async def test_enable_outputs(system_mode):
    """Test enable/disable outputs functionality"""
    print("\n=== Testing Enable/Disable Outputs ===")

    # First enable outputs
    print("Enabling outputs...")
    new_state = system_mode.handle_enable_outputs_button()
    print(f"Outputs enabled: {new_state}")

    # Wait a moment
    await asyncio.sleep(2)

    # Then disable outputs
    print("Disabling outputs...")
    new_state = system_mode.handle_enable_outputs_button()
    print(f"Outputs enabled: {new_state}")

    return True


async def test_arm_disarm(system_mode):
    """Test arm/disarm functionality"""
    print("\n=== Testing Arm/Disarm ===")

    # First enable outputs (required before arming)
    print("Enabling outputs (required before arming)...")
    system_mode.handle_enable_outputs_button()

    # Wait a moment
    await asyncio.sleep(1)

    # Arm the system
    print("Arming system...")
    new_state = system_mode.handle_arm_outputs_button()
    print(f"System armed: {new_state}")

    # Wait a moment
    await asyncio.sleep(2)

    # Disarm the system
    print("Disarming system...")
    new_state = system_mode.handle_arm_outputs_button()
    print(f"System armed: {new_state}")

    return True


async def test_emergency_abort(system_mode):
    """Test emergency abort functionality"""
    print("\n=== Testing Emergency Abort ===")

    # First enable outputs and arm the system
    print("Enabling outputs...")
    system_mode.handle_enable_outputs_button()

    await asyncio.sleep(1)

    print("Arming system...")
    system_mode.handle_arm_outputs_button()

    await asyncio.sleep(1)

    # Then trigger emergency abort
    print("Triggering emergency abort...")
    success = system_mode.handle_abort_button()
    print(f"Emergency abort successful: {success}")

    return success


async def main():
    """Main function"""
    print("=== GPIO Control Test Script ===")

    # Create SystemMode instance
    system_mode = SystemMode()

    # Set to hardware mode with connection settings
    connection_settings = {
        "host": "raspberrypi.local",  # Change this to your Pi's hostname or IP
        "port": 22,
        "username": "pi",
        "password": "raspberry"  # Change this to your Pi's password
    }

    # Set mode to hardware
    print("Setting mode to hardware...")
    await system_mode.set_mode("hardware", connection_settings)

    # Connect to hardware
    print("Connecting to hardware...")
    success, message = await system_mode.connect_to_hardware()
    if not success:
        print(f"Failed to connect to hardware: {message}")
        return

    print(f"Connected to hardware: {message}")

    # Run tests
    tests = [
        ("SSH Connection", test_ssh_connection),
        ("Enable/Disable Outputs", test_enable_outputs),
        ("Arm/Disarm", test_arm_disarm),
        ("Emergency Abort", test_emergency_abort)
    ]

    results = {}

    for name, test_func in tests:
        print(f"\nRunning test: {name}")
        try:
            success = await test_func(system_mode)
            results[name] = "PASS" if success else "FAIL"
        except Exception as e:
            print(f"Error during test {name}: {e}")
            results[name] = f"ERROR: {str(e)}"

    # Print test results
    print("\n=== Test Results ===")
    for name, result in results.items():
        print(f"{name}: {result}")

    # Close connection
    print("\nClosing connection...")
    await system_mode.close_connection()
    print("Connection closed")


if __name__ == "__main__":
    asyncio.run(main())