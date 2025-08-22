#!/usr/bin/env python3
"""
WiFi Mode Switching Script for Raspberry Pi

This script switches the Raspberry Pi between WiFi and Adhoc modes.

Usage:
    python3 switch_wifi_mode.py --mode=wifi|adhoc
"""

import argparse
import subprocess
import sys
import os
import logging
import time
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/home/pi/network_mode.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("wifi_mode")

# Path to store current mode
MODE_FILE = "/home/pi/network_mode.json"

# Network configuration files
WIFI_CONFIG = "/etc/wpa_supplicant/wpa_supplicant.conf"
DHCPCD_CONFIG = "/etc/dhcpcd.conf"
DNSMASQ_CONFIG = "/etc/dnsmasq.conf"
HOSTAPD_CONFIG = "/etc/hostapd/hostapd.conf"

# Backup files
WIFI_CONFIG_BACKUP = "/home/pi/wpa_supplicant.conf.backup"
DHCPCD_CONFIG_BACKUP = "/home/pi/dhcpcd.conf.backup"

# Default WiFi credentials (modify these for your network)
DEFAULT_WIFI_SSID = "YourWiFiNetwork"
DEFAULT_WIFI_PASSWORD = "YourWiFiPassword"

# Default Adhoc settings
ADHOC_SSID = "FireworkControlAP"
ADHOC_PASSWORD = "firework123"
ADHOC_IP = "192.168.4.1/24"


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
        logger.error(f"Error reading mode file: {e}")
        return 'wifi'  # Default to WiFi mode on error


def save_current_mode(mode):
    """
    Save the current network mode

    Args:
        mode: 'wifi' or 'adhoc'
    """
    try:
        with open(MODE_FILE, 'w') as f:
            json.dump({'mode': mode, 'timestamp': time.time()}, f)
        logger.info(f"Saved current mode: {mode}")
        return True
    except Exception as e:
        logger.error(f"Error saving mode file: {e}")
        return False


def backup_config_files():
    """
    Backup network configuration files

    Returns:
        bool: True if backup successful
    """
    try:
        # Backup wpa_supplicant.conf
        if os.path.exists(WIFI_CONFIG):
            subprocess.run(f"sudo cp {WIFI_CONFIG} {WIFI_CONFIG_BACKUP}", shell=True, check=True)
            logger.info(f"Backed up {WIFI_CONFIG}")

        # Backup dhcpcd.conf
        if os.path.exists(DHCPCD_CONFIG):
            subprocess.run(f"sudo cp {DHCPCD_CONFIG} {DHCPCD_CONFIG_BACKUP}", shell=True, check=True)
            logger.info(f"Backed up {DHCPCD_CONFIG}")

        return True
    except Exception as e:
        logger.error(f"Error backing up config files: {e}")
        return False


def restore_config_files():
    """
    Restore network configuration files from backup

    Returns:
        bool: True if restore successful
    """
    try:
        # Restore wpa_supplicant.conf
        if os.path.exists(WIFI_CONFIG_BACKUP):
            subprocess.run(f"sudo cp {WIFI_CONFIG_BACKUP} {WIFI_CONFIG}", shell=True, check=True)
            logger.info(f"Restored {WIFI_CONFIG}")

        # Restore dhcpcd.conf
        if os.path.exists(DHCPCD_CONFIG_BACKUP):
            subprocess.run(f"sudo cp {DHCPCD_CONFIG_BACKUP} {DHCPCD_CONFIG}", shell=True, check=True)
            logger.info(f"Restored {DHCPCD_CONFIG}")

        return True
    except Exception as e:
        logger.error(f"Error restoring config files: {e}")
        return False


def setup_wifi_mode():
    """
    Configure the Raspberry Pi for WiFi mode

    Returns:
        bool: True if setup successful
    """
    try:
        logger.info("Setting up WiFi mode...")

        # Stop hostapd and dnsmasq services
        subprocess.run("sudo systemctl stop hostapd", shell=True, check=False)
        subprocess.run("sudo systemctl stop dnsmasq", shell=True, check=False)

        # Disable services on boot
        subprocess.run("sudo systemctl disable hostapd", shell=True, check=False)
        subprocess.run("sudo systemctl disable dnsmasq", shell=True, check=False)

        # Restore original configuration files if they exist
        restore_config_files()

        # Ensure wpa_supplicant.conf exists with correct settings
        if not os.path.exists(WIFI_CONFIG):
            # Create a basic wpa_supplicant.conf file
            wifi_config = f"""ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=US

network={{
    ssid="{DEFAULT_WIFI_SSID}"
    psk="{DEFAULT_WIFI_PASSWORD}"
    key_mgmt=WPA-PSK
}}
"""
            with open("/tmp/wpa_supplicant.conf", "w") as f:
                f.write(wifi_config)

            subprocess.run("sudo mv /tmp/wpa_supplicant.conf " + WIFI_CONFIG, shell=True, check=True)
            subprocess.run(f"sudo chmod 600 {WIFI_CONFIG}", shell=True, check=True)

        # Restart networking services
        subprocess.run("sudo systemctl daemon-reload", shell=True, check=True)
        subprocess.run("sudo systemctl restart dhcpcd", shell=True, check=True)
        subprocess.run("sudo systemctl restart networking", shell=True, check=True)
        subprocess.run("sudo wpa_cli -i wlan0 reconfigure", shell=True, check=False)

        # Save current mode
        save_current_mode('wifi')

        logger.info("WiFi mode setup completed")
        return True
    except Exception as e:
        logger.error(f"Error setting up WiFi mode: {e}")
        return False


def setup_adhoc_mode():
    """
    Configure the Raspberry Pi for Adhoc (Access Point) mode

    Returns:
        bool: True if setup successful
    """
    try:
        logger.info("Setting up Adhoc (Access Point) mode...")

        # Backup current configuration files
        backup_config_files()

        # Install required packages if not already installed
        subprocess.run("sudo apt-get update", shell=True, check=False)
        subprocess.run("sudo apt-get install -y hostapd dnsmasq", shell=True, check=False)

        # Stop services during configuration
        subprocess.run("sudo systemctl stop hostapd", shell=True, check=False)
        subprocess.run("sudo systemctl stop dnsmasq", shell=True, check=False)

        # Configure static IP for wlan0
        dhcpcd_config = f"""interface wlan0
    static ip_address={ADHOC_IP}
    nohook wpa_supplicant
"""
        with open("/tmp/dhcpcd.conf", "w") as f:
            f.write(dhcpcd_config)

        subprocess.run("sudo cp /tmp/dhcpcd.conf " + DHCPCD_CONFIG, shell=True, check=True)

        # Configure DHCP server (dnsmasq)
        dnsmasq_config = """interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
domain=wlan
address=/gw.wlan/192.168.4.1
"""
        with open("/tmp/dnsmasq.conf", "w") as f:
            f.write(dnsmasq_config)

        subprocess.run("sudo cp /tmp/dnsmasq.conf " + DNSMASQ_CONFIG, shell=True, check=True)

        # Configure access point (hostapd)
        hostapd_config = f"""interface=wlan0
driver=nl80211
ssid={ADHOC_SSID}
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase={ADHOC_PASSWORD}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
"""
        with open("/tmp/hostapd.conf", "w") as f:
            f.write(hostapd_config)

        subprocess.run("sudo cp /tmp/hostapd.conf " + HOSTAPD_CONFIG, shell=True, check=True)

        # Configure hostapd to use this config file
        with open("/tmp/hostapd", "w") as f:
            f.write('DAEMON_CONF="/etc/hostapd/hostapd.conf"')

        subprocess.run("sudo cp /tmp/hostapd /etc/default/hostapd", shell=True, check=True)

        # Enable IP forwarding
        subprocess.run("sudo sh -c 'echo 1 > /proc/sys/net/ipv4/ip_forward'", shell=True, check=True)

        # Enable services on boot
        subprocess.run("sudo systemctl unmask hostapd", shell=True, check=True)
        subprocess.run("sudo systemctl enable hostapd", shell=True, check=True)
        subprocess.run("sudo systemctl enable dnsmasq", shell=True, check=True)

        # Restart networking services
        subprocess.run("sudo systemctl daemon-reload", shell=True, check=True)
        subprocess.run("sudo systemctl restart dhcpcd", shell=True, check=True)
        subprocess.run("sudo systemctl restart hostapd", shell=True, check=True)
        subprocess.run("sudo systemctl restart dnsmasq", shell=True, check=True)

        # Save current mode
        save_current_mode('adhoc')

        logger.info("Adhoc mode setup completed")
        return True
    except Exception as e:
        logger.error(f"Error setting up Adhoc mode: {e}")
        return False


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

        return {
            'mode': mode,
            'ip_address': ip_address,
            'ssid': ssid,
            'signal': signal,
            'timestamp': time.time()
        }
    except Exception as e:
        logger.error(f"Error getting network info: {e}")
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
    parser = argparse.ArgumentParser(description="Switch Raspberry Pi between WiFi and Adhoc modes")
    parser.add_argument("--mode", type=str, required=True, choices=["wifi", "adhoc"],
                        help="Network mode to switch to (wifi or adhoc)")
    parser.add_argument("--info", action="store_true", help="Get current network information")

    args = parser.parse_args()

    # Get network info if requested
    if args.info:
        info = get_network_info()
        print(json.dumps(info, indent=2))
        sys.exit(0)

    # Check current mode
    current_mode = get_current_mode()
    if current_mode == args.mode:
        logger.info(f"Already in {args.mode} mode")
        print(f"Already in {args.mode} mode")
        sys.exit(0)

    # Switch mode
    if args.mode == "wifi":
        success = setup_wifi_mode()
    else:  # adhoc
        success = setup_adhoc_mode()

    if success:
        print(f"Successfully switched to {args.mode} mode")
        sys.exit(0)
    else:
        print(f"Failed to switch to {args.mode} mode")
        sys.exit(1)


if __name__ == "__main__":
    main()