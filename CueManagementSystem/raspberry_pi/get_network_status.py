#!/usr/bin/env python3
"""
Network Status Script for Raspberry Pi

This script returns the current network mode and status information.

Usage:
    python3 get_network_status.py
"""

import subprocess
import sys
import os
import json
import time

# Path to store current mode
MODE_FILE = "/home/pi/network_mode.json"

# Default Adhoc settings
ADHOC_SSID = "FireworkControlAP"


def get_current_mode():
    """
    Get the current network mode

    Returns:
        str: 'wifi' or 'adhoc'
    """
    try:
        if os.path.exists(MODE_FILE):
            with open(MODE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('mode', 'wifi')
        else:
            # Default to WiFi mode if file doesn't exist
            return 'wifi'
    except Exception as e:
        print(f"Error reading mode file: {e}", file=sys.stderr)
        return 'wifi'  # Default to WiFi mode on error


def get_network_info():
    """
    Get current network information

    Returns:
        dict: Network information
    """
    try:
        # Get current mode
        mode = get_current_mode()

        # Get IP address
        ip_cmd = subprocess.run("hostname -I | awk '{print $1}'", shell=True, capture_output=True, text=True)
        ip_address = ip_cmd.stdout.strip() if ip_cmd.returncode == 0 else "Unknown"

        # Get WiFi SSID if in WiFi mode
        ssid = "N/A"
        if mode == 'wifi':
            ssid_cmd = subprocess.run("iwgetid -r", shell=True, capture_output=True, text=True)
            ssid = ssid_cmd.stdout.strip() if ssid_cmd.returncode == 0 and ssid_cmd.stdout.strip() else "Not connected"
        elif mode == 'adhoc':
            ssid = ADHOC_SSID

        # Get signal strength if in WiFi mode
        signal = "N/A"
        if mode == 'wifi':
            signal_cmd = subprocess.run("iwconfig wlan0 | grep -i --color 'signal level'", shell=True,
                                        capture_output=True, text=True)
            if signal_cmd.returncode == 0 and signal_cmd.stdout:
                signal = signal_cmd.stdout.strip()
            else:
                signal = "Unknown"

        # Check if hostapd is running (for adhoc mode)
        hostapd_running = False
        if mode == 'adhoc':
            hostapd_cmd = subprocess.run("sudo systemctl is-active hostapd", shell=True, capture_output=True, text=True)
            hostapd_running = hostapd_cmd.stdout.strip() == "active"

        # Get connected clients in adhoc mode
        connected_clients = []
        if mode == 'adhoc' and hostapd_running:
            try:
                # Get connected clients from hostapd
                clients_cmd = subprocess.run("sudo iw dev wlan0 station dump | grep Station", shell=True,
                                             capture_output=True, text=True)
                if clients_cmd.returncode == 0 and clients_cmd.stdout:
                    for line in clients_cmd.stdout.strip().split('\n'):
                        if "Station" in line:
                            mac = line.split()[1]
                            connected_clients.append(mac)
            except Exception as e:
                print(f"Error getting connected clients: {e}", file=sys.stderr)

        return {
            'mode': mode,
            'ip_address': ip_address,
            'ssid': ssid,
            'signal': signal,
            'hostapd_running': hostapd_running if mode == 'adhoc' else None,
            'connected_clients': connected_clients if mode == 'adhoc' else [],
            'timestamp': time.time()
        }
    except Exception as e:
        print(f"Error getting network info: {e}", file=sys.stderr)
        return {
            'mode': get_current_mode(),
            'ip_address': 'Error',
            'ssid': 'Error',
            'signal': 'Error',
            'timestamp': time.time(),
            'error': str(e)
        }


def main():
    """Main function"""
    try:
        # Get network information
        info = get_network_info()

        # Print as JSON
        print(json.dumps(info, indent=2))

        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()