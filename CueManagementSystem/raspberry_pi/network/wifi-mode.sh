#!/bin/bash
"""
WiFi Mode Switching Script
==========================

Bash script to configure Raspberry Pi to connect to a specified WiFi network, disconnecting from ad-hoc mode.

Features:
- WiFi network connection
- Ad-hoc disconnection
- NetworkManager integration
- Connection creation if needed
- Root privilege checking
- Error handling
- Status reporting

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

# wifi-mode - Switch Raspberry Pi to WiFi Mode
# Usage: sudo wifi-mode

set -e

WIFI_SSID="Lyman"
WIFI_PASSWORD="grandgiant902"
CONNECTION_NAME="wifi-lyman"
ADHOC_CONNECTION="adhoc-cuepishifter"

echo "=========================================="
echo "Switching to WiFi Mode"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

# Check if NetworkManager is running
if ! systemctl is-active --quiet NetworkManager; then
    echo "Error: NetworkManager is not running"
    exit 1
fi

# Disconnect ad-hoc connection if active
echo "Disconnecting from ad-hoc mode..."
if nmcli connection show --active | grep -q "$ADHOC_CONNECTION"; then
    nmcli connection down "$ADHOC_CONNECTION" 2>/dev/null || true
fi

# Check if WiFi connection already exists
if nmcli connection show "$CONNECTION_NAME" &>/dev/null; then
    echo "WiFi connection '$CONNECTION_NAME' already exists, bringing it up..."
    nmcli connection up "$CONNECTION_NAME"
else
    echo "Creating new WiFi connection '$CONNECTION_NAME'..."
    
    # Create the WiFi connection
    nmcli connection add type wifi \
        ifname wlan0 \
        con-name "$CONNECTION_NAME" \
        autoconnect yes \
        ssid "$WIFI_SSID" \
        wifi-sec.key-mgmt wpa-psk \
        wifi-sec.psk "$WIFI_PASSWORD"
    
    echo "Connecting to WiFi..."
    nmcli connection up "$CONNECTION_NAME"
fi

# Wait a moment for the connection to stabilize
sleep 3

# Verify the connection is up and get IP address
if nmcli connection show --active | grep -q "$CONNECTION_NAME"; then
    IP_ADDRESS=$(ip -4 addr show wlan0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
    echo ""
    echo "=========================================="
    echo "WiFi Mode Active!"
    echo "=========================================="
    echo "Connected to: $WIFI_SSID"
    echo "Pi IP Address: $IP_ADDRESS"
    echo ""
    echo "SSH to: ssh pi@$IP_ADDRESS"
    echo "=========================================="
else
    echo "Error: Failed to connect to WiFi"
    echo "Please check your WiFi credentials and try again"
    exit 1
fi