# Raspberry Pi Zero W2 Access Point Setup Guide

This guide provides step-by-step instructions for setting up a Raspberry Pi Zero W2 as a WiFi access point for connecting with a MacBook Pro.

## Prerequisites

- Raspberry Pi Zero W2
- MicroSD card (8GB or larger) with Raspberry Pi OS Lite installed
- Power supply for Raspberry Pi
- MacBook Pro with WiFi capability
- SSH access to the Raspberry Pi (either via USB OTG or initial WiFi setup)

## Initial Setup

1. Flash Raspberry Pi OS Lite to the microSD card using the Raspberry Pi Imager
2. For headless setup, create these files in the boot partition:
   - An empty file named `ssh` to enable SSH
   - A file named `wpa_supplicant.conf` with your WiFi credentials (for initial setup only)

```
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="YOUR_WIFI_SSID"
    psk="YOUR_WIFI_PASSWORD"
    key_mgmt=WPA-PSK
}
```

3. Insert the microSD card into the Raspberry Pi and power it on
4. Connect to the Raspberry Pi via SSH:
   ```
   ssh pi@raspberrypi.local
   ```
   Default password: raspberry

5. Update the system:
   ```
   sudo apt update
   sudo apt upgrade -y
   ```

6. Change the default password:
   ```
   passwd
   ```

## Installing Required Software

1. Install the necessary packages:
   ```
   sudo apt install hostapd dnsmasq -y
   ```

2. Stop the services initially:
   ```
   sudo systemctl stop hostapd
   sudo systemctl stop dnsmasq
   ```

3. Disable the services from starting automatically:
   ```
   sudo systemctl unmask hostapd
   sudo systemctl disable hostapd
   sudo systemctl disable dnsmasq
   ```

## Configuring the Network

1. Configure a static IP for the wireless interface by editing the dhcpcd configuration:
   ```
   sudo nano /etc/dhcpcd.conf
   ```

2. Add the following at the end of the file:
   ```
   interface wlan0
       static ip_address=192.168.4.1/24
       nohook wpa_supplicant
   ```

3. Save and exit (Ctrl+X, Y, Enter)

4. Restart the dhcpcd service:
   ```
   sudo systemctl restart dhcpcd
   ```

## Configuring the DHCP Server

1. Backup the original dnsmasq configuration:
   ```
   sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
   ```

2. Create a new configuration file:
   ```
   sudo nano /etc/dnsmasq.conf
   ```

3. Add the following configuration:
   ```
   interface=wlan0
   dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
   domain=wlan
   address=/gw.wlan/192.168.4.1
   ```

4. Save and exit (Ctrl+X, Y, Enter)

## Configuring the Access Point

1. Create the hostapd configuration file:
   ```
   sudo nano /etc/hostapd/hostapd.conf
   ```

2. Add the following configuration:
   ```
   interface=wlan0
   driver=nl80211
   ssid=PiZeroAP
   hw_mode=g
   channel=7
   wmm_enabled=0
   macaddr_acl=0
   auth_algs=1
   ignore_broadcast_ssid=0
   wpa=2
   wpa_passphrase=RaspberryPi2025
   wpa_key_mgmt=WPA-PSK
   wpa_pairwise=TKIP
   rsn_pairwise=CCMP
   country_code=US
   ieee80211n=1
   ht_capab=[HT40][SHORT-GI-20][DSSS_CCK-40]
   ```

   Note: Change the `ssid` and `wpa_passphrase` to your preferred values.

3. Save and exit (Ctrl+X, Y, Enter)

4. Specify the path to the configuration file:
   ```
   sudo nano /etc/default/hostapd
   ```

5. Find the line `#DAEMON_CONF=""` and replace it with:
   ```
   DAEMON_CONF="/etc/hostapd/hostapd.conf"
   ```

6. Save and exit (Ctrl+X, Y, Enter)

## Enabling IP Forwarding (Optional - for Internet Sharing)

If you want to share an internet connection from another interface (like eth0 when using USB OTG Ethernet):

1. Edit the sysctl.conf file:
   ```
   sudo nano /etc/sysctl.conf
   ```

2. Uncomment or add the following line:
   ```
   net.ipv4.ip_forward=1
   ```

3. Save and exit (Ctrl+X, Y, Enter)

4. Apply the changes:
   ```
   sudo sysctl -p
   ```

5. Set up NAT between interfaces (assuming eth0 is connected to the internet):
   ```
   sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
   sudo iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
   sudo iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT
   ```

6. Save the iptables rules:
   ```
   sudo sh -c "iptables-save > /etc/iptables.ipv4.nat"
   ```

7. Create a script to restore the rules on boot:
   ```
   sudo nano /etc/rc.local
   ```

8. Add the following line before `exit 0`:
   ```
   iptables-restore < /etc/iptables.ipv4.nat
   ```

9. Save and exit (Ctrl+X, Y, Enter)

## Starting the Services

1. Start the services:
   ```
   sudo systemctl start hostapd
   sudo systemctl start dnsmasq
   ```

2. Enable the services to start on boot:
   ```
   sudo systemctl enable hostapd
   sudo systemctl enable dnsmasq
   ```

## Creating a Startup Script (Optional)

For easier management, create a startup script:

1. Create the script file:
   ```
   sudo nano /usr/local/bin/ap-startup.sh
   ```

2. Add the following content:
   ```bash
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
   ```

3. Make the script executable:
   ```
   sudo chmod +x /usr/local/bin/ap-startup.sh
   ```

4. To run the script manually:
   ```
   sudo /usr/local/bin/ap-startup.sh
   ```

## Connecting from MacBook Pro

1. On your MacBook Pro, click on the WiFi icon in the menu bar
2. Select the "PiZeroAP" network from the list
3. Enter the password you configured (default: RaspberryPi2025)
4. Your MacBook should now be connected to the Raspberry Pi access point
5. You can SSH into the Raspberry Pi using its static IP:
   ```
   ssh pi@192.168.4.1
   ```

## Troubleshooting

### Access Point Not Appearing

1. Check if hostapd is running:
   ```
   sudo systemctl status hostapd
   ```

2. If there are errors, check the configuration:
   ```
   sudo nano /etc/hostapd/hostapd.conf
   ```

3. Restart the service:
   ```
   sudo systemctl restart hostapd
   ```

### No IP Address Assigned

1. Check if dnsmasq is running:
   ```
   sudo systemctl status dnsmasq
   ```

2. Check the configuration:
   ```
   sudo nano /etc/dnsmasq.conf
   ```

3. Restart the service:
   ```
   sudo systemctl restart dnsmasq
   ```

### Connection Drops

1. Check the system logs:
   ```
   sudo journalctl -u hostapd
   ```

2. Try changing the channel in the hostapd.conf file to avoid interference

### Cannot Access Internet (When Sharing)

1. Verify IP forwarding is enabled:
   ```
   cat /proc/sys/net/ipv4/ip_forward
   ```
   Should return 1

2. Check iptables rules:
   ```
   sudo iptables -L -t nat
   ```

3. Ensure the internet-connected interface (e.g., eth0) has a valid connection