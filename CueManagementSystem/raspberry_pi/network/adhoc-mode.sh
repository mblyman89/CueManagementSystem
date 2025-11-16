#!/bin/bash
"""
Ad-Hoc Mode Switching Script
============================
Bash script to configure Raspberry Pi to operate in ad-hoc (hotspot) mode with specified SSID and IP.

Features:
- Ad-hoc network creation
- Hotspot mode configuration
- WiFi disconnection
- Static IP assignment (192.168.42.1)
- NetworkManager integration
- Root privilege checking
- Connection management

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""
# adhoc-mode - Switch Raspberry Pi to Ad-Hoc (Hotspot) Mode
# Usage: sudo adhoc-mode

set -e

ADHOC_SSID="cuepishifter"
ADHOC_PASSWORD="cuepishifter"
ADHOC_IP="192.168.42.1"
CONNECTION_NAME="adhoc-cuepishifter"

echo "=========================================="
echo "Switching to Ad-Hoc Mode"
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

# Disconnect any active WiFi connections
echo "Disconnecting from WiFi networks..."
ACTIVE_WIFI=$(nmcli -t -f NAME,TYPE,DEVICE connection show --active | grep wifi | grep wlan0 | cut -d: -f1)
if [ ! -z "$ACTIVE_WIFI" ]; then
    nmcli connection down "$ACTIVE_WIFI" 2>/dev/null || true
fi

# Check if ad-hoc connection already exists
if nmcli connection show "$CONNECTION_NAME" &>/dev/null; then
    echo "Ad-hoc connection '$CONNECTION_NAME' already exists, bringing it up..."
    nmcli connection up "$CONNECTION_NAME"
else
    echo "Creating new ad-hoc connection '$CONNECTION_NAME'..."
    
    # Create the ad-hoc hotspot connection
    nmcli connection add type wifi \
        ifname wlan0 \
        con-name "$CONNECTION_NAME" \
        autoconnect no \
        ssid "$ADHOC_SSID" \
        802-11-wireless.mode ap \
        802-11-wireless.band bg \
        ipv4.method shared \
        ipv4.addresses "$ADHOC_IP/24" \
        wifi-sec.key-mgmt wpa-psk \
        wifi-sec.psk "$ADHOC_PASSWORD" \
        802-11-wireless-security.pmf 1
    
    echo "Bringing up ad-hoc connection..."
    nmcli connection up "$CONNECTION_NAME"
fi

# Wait a moment for the connection to stabilize
sleep 2

# Verify the connection is up
if nmcli connection show --active | grep -q "$CONNECTION_NAME"; then
    echo ""
    echo "=========================================="
    echo "Ad-Hoc Mode Active!"
    echo "=========================================="
    echo "Network Name (SSID): $ADHOC_SSID"
    echo "Password: $ADHOC_PASSWORD"
    echo "Pi IP Address: $ADHOC_IP"
    echo ""
    echo "Connect from your Mac:"
    echo "1. Open WiFi settings"
    echo "2. Connect to '$ADHOC_SSID'"
    echo "3. Enter password: $ADHOC_PASSWORD"
    echo "4. SSH to: ssh pi@$ADHOC_IP"
    echo "=========================================="
else
    echo "Error: Failed to activate ad-hoc mode"
    exit 1
fi