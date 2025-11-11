#!/bin/bash
# setup-network-switching.sh - Initial setup script for network mode switching
# This script installs and configures everything needed for easy switching
# between ad-hoc and WiFi modes on Raspberry Pi Zero W2

set -e

echo "=========================================="
echo "Raspberry Pi Network Switching Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

# Detect Raspberry Pi OS version
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "Detected OS: $PRETTY_NAME"
else
    echo "Warning: Could not detect OS version"
fi

# Check if NetworkManager is installed
echo ""
echo "Checking NetworkManager installation..."
if ! command -v nmcli &> /dev/null; then
    echo "NetworkManager not found. Installing..."
    apt-get update
    apt-get install -y network-manager
else
    echo "NetworkManager is already installed"
fi

# Ensure NetworkManager is enabled and running
echo ""
echo "Ensuring NetworkManager is enabled..."
systemctl enable NetworkManager
systemctl start NetworkManager

# Install dnsmasq-base if not present (needed for hotspot DHCP)
echo ""
echo "Checking dnsmasq-base installation..."
if ! dpkg -l | grep -q dnsmasq-base; then
    echo "Installing dnsmasq-base for DHCP support..."
    apt-get install -y dnsmasq-base
else
    echo "dnsmasq-base is already installed"
fi

# Create scripts directory if it doesn't exist
SCRIPTS_DIR="/usr/local/bin"
echo ""
echo "Installing network switching scripts to $SCRIPTS_DIR..."

# Copy scripts to /usr/local/bin
if [ -f "adhoc-mode" ]; then
    cp adhoc-mode "$SCRIPTS_DIR/adhoc-mode"
    chmod +x "$SCRIPTS_DIR/adhoc-mode"
    echo "✓ Installed adhoc-mode"
else
    echo "Error: adhoc-mode script not found in current directory"
    exit 1
fi

if [ -f "wifi-mode" ]; then
    cp wifi-mode "$SCRIPTS_DIR/wifi-mode"
    chmod +x "$SCRIPTS_DIR/wifi-mode"
    echo "✓ Installed wifi-mode"
else
    echo "Error: wifi-mode script not found in current directory"
    exit 1
fi

# Create a status script
cat > "$SCRIPTS_DIR/network-status" << 'EOF'
#!/bin/bash
# network-status - Show current network mode and connection status

echo "=========================================="
echo "Network Status"
echo "=========================================="
echo ""

# Check active connections
ACTIVE_CONN=$(nmcli -t -f NAME,TYPE,DEVICE connection show --active | grep wlan0)

if [ -z "$ACTIVE_CONN" ]; then
    echo "Status: No active wireless connection"
else
    CONN_NAME=$(echo "$ACTIVE_CONN" | cut -d: -f1)
    CONN_TYPE=$(echo "$ACTIVE_CONN" | cut -d: -f2)
    
    if [[ "$CONN_NAME" == *"adhoc"* ]]; then
        echo "Mode: Ad-Hoc (Hotspot)"
        IP_ADDRESS=$(ip -4 addr show wlan0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
        echo "IP Address: $IP_ADDRESS"
        echo "SSID: cuepishifter"
    else
        echo "Mode: WiFi Client"
        IP_ADDRESS=$(ip -4 addr show wlan0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
        SSID=$(nmcli -t -f active,ssid dev wifi | grep '^yes' | cut -d: -f2)
        echo "Connected to: $SSID"
        echo "IP Address: $IP_ADDRESS"
    fi
fi

echo ""
echo "Available commands:"
echo "  sudo adhoc-mode  - Switch to ad-hoc mode"
echo "  sudo wifi-mode   - Switch to WiFi mode"
echo "=========================================="
EOF

chmod +x "$SCRIPTS_DIR/network-status"
echo "✓ Installed network-status"

# Install Python wrapper scripts for application compatibility
echo ""
echo "Installing Python wrapper scripts..."

if [ -f "switch_wifi_mode.py" ]; then
    cp switch_wifi_mode.py ~/switch_wifi_mode.py
    chmod +x ~/switch_wifi_mode.py
    echo "✓ Installed switch_wifi_mode.py"
else
    echo "Warning: switch_wifi_mode.py not found"
fi

if [ -f "get_network_status.py" ]; then
    cp get_network_status.py ~/get_network_status.py
    chmod +x ~/get_network_status.py
    echo "✓ Installed get_network_status.py"
else
    echo "Warning: get_network_status.py not found"
fi

# Configure boot behavior - default to ad-hoc mode
echo ""
echo "Configuring boot behavior..."
echo "The Pi will boot into ad-hoc mode by default"

# Create systemd service to start ad-hoc mode on boot
cat > /etc/systemd/system/adhoc-on-boot.service << 'EOF'
[Unit]
Description=Start Ad-Hoc Mode on Boot
After=NetworkManager.service
Wants=NetworkManager.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/adhoc-mode
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
systemctl daemon-reload
systemctl enable adhoc-on-boot.service

echo "✓ Ad-hoc mode will start automatically on boot"

# Summary
echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Available Commands:"
echo "  sudo adhoc-mode      - Switch to ad-hoc (hotspot) mode"
echo "  sudo wifi-mode       - Switch to WiFi client mode"
echo "  network-status       - Show current network status"
echo ""
echo "Ad-Hoc Network Details:"
echo "  SSID: cuepishifter"
echo "  Password: cuepishifter"
echo "  Pi IP: 192.168.42.1"
echo ""
echo "WiFi Network Details:"
echo "  SSID: Lyman"
echo "  Password: grandgiant902"
echo ""
echo "The Pi will boot into ad-hoc mode by default."
echo "After connecting, SSH to: ssh pi@192.168.42.1"
echo ""
echo "To test the setup, reboot your Pi:"
echo "  sudo reboot"
echo "=========================================="