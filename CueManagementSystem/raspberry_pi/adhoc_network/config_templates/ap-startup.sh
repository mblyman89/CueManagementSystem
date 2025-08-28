#!/bin/bash
# Startup script for Raspberry Pi Zero W2 Access Point

# Load IP forwarding setting
sysctl -p /etc/sysctl.conf

# If you want to share internet from eth0 to wlan0 (if using USB OTG Ethernet)
# Uncomment the following lines:
# iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
# iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
# iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT

# Restart networking services
systemctl restart dhcpcd
systemctl restart dnsmasq
systemctl restart hostapd

echo "Access Point services started successfully"