# Maintenance Guide for Raspberry Pi Zero W2 Access Point

This guide provides recommendations for maintaining your Raspberry Pi Zero W2 access point to ensure reliable operation over time.

## Regular Maintenance Tasks

### Weekly Maintenance

1. **Check System Updates**
   ```bash
   sudo apt update
   sudo apt list --upgradable
   ```
   
   Apply updates if needed:
   ```bash
   sudo apt upgrade -y
   ```

2. **Check Service Status**
   ```bash
   sudo systemctl status hostapd
   sudo systemctl status dnsmasq
   ```
   
   Restart services if needed:
   ```bash
   sudo systemctl restart hostapd
   sudo systemctl restart dnsmasq
   ```

3. **Check System Logs for Errors**
   ```bash
   sudo journalctl -p err -b
   ```
   
   Look for any recurring errors related to networking services.

4. **Monitor System Temperature**
   ```bash
   vcgencmd measure_temp
   ```
   
   If consistently above 70°C, consider improving cooling.

### Monthly Maintenance

1. **Check Disk Space**
   ```bash
   df -h
   ```
   
   If the filesystem is getting full:
   ```bash
   sudo apt clean
   sudo apt autoremove -y
   ```

2. **Check for Large Log Files**
   ```bash
   sudo find /var/log -type f -size +50M
   ```
   
   Rotate or clear large log files:
   ```bash
   sudo truncate -s 0 /var/log/large_log_file
   ```

3. **Check Connected Devices**
   ```bash
   sudo arp -a
   # or
   cat /var/lib/misc/dnsmasq.leases
   ```
   
   This helps identify any unauthorized devices.

4. **Update Firmware**
   ```bash
   sudo rpi-update
   ```
   
   Note: Only use rpi-update if you have a specific reason to do so, as it installs testing firmware.

5. **Backup Configuration Files**
   ```bash
   sudo mkdir -p /home/pi/backups/$(date +%Y-%m-%d)
   sudo cp /etc/hostapd/hostapd.conf /home/pi/backups/$(date +%Y-%m-%d)/
   sudo cp /etc/dnsmasq.conf /home/pi/backups/$(date +%Y-%m-%d)/
   sudo cp /etc/dhcpcd.conf /home/pi/backups/$(date +%Y-%m-%d)/
   ```

## Performance Optimization

### Reducing Power Consumption

1. **Disable HDMI Output** (if not using a display)
   ```bash
   sudo /usr/bin/tvservice -o
   ```
   
   Add to `/etc/rc.local` to make it persistent.

2. **Disable LEDs** (optional)
   ```bash
   echo 0 | sudo tee /sys/class/leds/led0/brightness
   ```
   
   To make it persistent, add to `/etc/rc.local`.

### Improving WiFi Performance

1. **Optimize Channel Selection**
   
   Scan for least congested channel:
   ```bash
   sudo iwlist wlan0 scan | grep -E "Channel|ESSID" | sort
   ```
   
   Update the channel in `/etc/hostapd/hostapd.conf`.

2. **Adjust Transmit Power** (if overheating is an issue)
   ```bash
   sudo iw dev wlan0 set txpower fixed 1000
   ```
   
   Values are in mBm (100 = 10 dBm). Default is usually around 3000 (30 dBm).

3. **Optimize WiFi Settings**
   
   Edit `/etc/hostapd/hostapd.conf` and try these settings:
   ```
   wmm_enabled=1
   ieee80211n=1
   ht_capab=[HT40][SHORT-GI-20][DSSS_CCK-40]
   ```

## Security Maintenance

### Change Passwords Regularly

1. **Change Access Point Password**
   
   Edit `/etc/hostapd/hostapd.conf`:
   ```bash
   sudo nano /etc/hostapd/hostapd.conf
   ```
   
   Update the `wpa_passphrase` value, then restart hostapd:
   ```bash
   sudo systemctl restart hostapd
   ```

2. **Change Raspberry Pi User Password**
   ```bash
   passwd
   ```

### Security Hardening

1. **Enable Automatic Security Updates**
   ```bash
   sudo apt install unattended-upgrades
   sudo dpkg-reconfigure unattended-upgrades
   ```

2. **Install Fail2ban to Protect SSH**
   ```bash
   sudo apt install fail2ban
   sudo systemctl enable fail2ban
   sudo systemctl start fail2ban
   ```

3. **Check for Open Ports**
   ```bash
   sudo apt install nmap
   sudo nmap -sT -p- localhost
   ```
   
   Close any unnecessary open ports.

4. **Enable MAC Filtering** (optional)
   
   Edit `/etc/hostapd/hostapd.conf`:
   ```
   macaddr_acl=1
   accept_mac_file=/etc/hostapd/allowed_macs
   ```
   
   Create the allowed MACs file:
   ```bash
   sudo nano /etc/hostapd/allowed_macs
   ```
   
   Add one MAC address per line:
   ```
   00:11:22:33:44:55
   AA:BB:CC:DD:EE:FF
   ```

## Backup and Recovery

### Creating System Backups

1. **Create a Full SD Card Backup**
   
   On another Linux machine or using a USB SD card reader:
   ```bash
   sudo dd if=/dev/mmcblk0 of=pi_ap_backup.img bs=1M status=progress
   ```
   
   Compress the image to save space:
   ```bash
   gzip -9 pi_ap_backup.img
   ```

2. **Backup Essential Configurations Only**
   ```bash
   mkdir -p ~/pi_configs
   sudo cp -r /etc/hostapd ~/pi_configs/
   sudo cp /etc/dnsmasq.conf ~/pi_configs/
   sudo cp /etc/dhcpcd.conf ~/pi_configs/
   sudo cp /usr/local/bin/ap-startup.sh ~/pi_configs/
   sudo cp /etc/rc.local ~/pi_configs/
   sudo cp /etc/iptables.ipv4.nat ~/pi_configs/
   tar -czvf pi_ap_configs.tar.gz ~/pi_configs
   ```

### Recovery Procedures

1. **Restore from Full Backup**
   
   On another Linux machine or using a USB SD card reader:
   ```bash
   gunzip -c pi_ap_backup.img.gz | sudo dd of=/dev/mmcblk0 bs=1M status=progress
   ```

2. **Restore Individual Configuration Files**
   ```bash
   tar -xzvf pi_ap_configs.tar.gz
   sudo cp ~/pi_configs/hostapd/hostapd.conf /etc/hostapd/
   sudo cp ~/pi_configs/dnsmasq.conf /etc/
   sudo cp ~/pi_configs/dhcpcd.conf /etc/
   sudo cp ~/pi_configs/ap-startup.sh /usr/local/bin/
   sudo chmod +x /usr/local/bin/ap-startup.sh
   ```

## Monitoring and Logging

### Setting Up Monitoring

1. **Install Monitoring Tools**
   ```bash
   sudo apt install htop iftop vnstat
   ```

2. **Monitor Network Usage**
   ```bash
   sudo vnstat -l -i wlan0
   ```
   
   For a graphical interface (if you have a display):
   ```bash
   sudo apt install vnstati
   sudo vnstati -s -i wlan0 -o /var/www/html/vnstat.png
   ```

3. **Set Up Log Rotation**
   
   Edit the logrotate configuration:
   ```bash
   sudo nano /etc/logrotate.d/custom
   ```
   
   Add:
   ```
   /var/log/hostapd.log {
       rotate 7
       daily
       compress
       missingok
       notifempty
   }
   ```

### Remote Monitoring

1. **Install Prometheus Node Exporter** (for advanced monitoring)
   ```bash
   sudo apt install prometheus-node-exporter
   sudo systemctl enable prometheus-node-exporter
   sudo systemctl start prometheus-node-exporter
   ```

2. **Set Up Remote Access via Wireguard VPN** (for secure remote management)
   ```bash
   sudo apt install wireguard
   ```
   
   Follow the Wireguard setup guide to configure a secure tunnel for remote management.

## Troubleshooting Recurring Issues

### Dealing with Frequent Disconnections

1. **Check for Interference**
   ```bash
   sudo apt install wavemon
   sudo wavemon
   ```
   
   Look for signal quality and noise levels.

2. **Monitor CPU Usage During Disconnections**
   ```bash
   htop
   ```
   
   If CPU is consistently at 100%, the Pi might be overheating or overloaded.

3. **Set Up a Watchdog**
   
   Create a script to monitor and restart services if needed:
   ```bash
   sudo nano /usr/local/bin/ap-watchdog.sh
   ```
   
   Add:
   ```bash
   #!/bin/bash
   
   # Check if hostapd is running
   if ! systemctl is-active --quiet hostapd; then
       echo "$(date): hostapd is down, restarting..." >> /var/log/ap-watchdog.log
       systemctl restart hostapd
   fi
   
   # Check if dnsmasq is running
   if ! systemctl is-active --quiet dnsmasq; then
       echo "$(date): dnsmasq is down, restarting..." >> /var/log/ap-watchdog.log
       systemctl restart dnsmasq
   fi
   ```
   
   Make it executable:
   ```bash
   sudo chmod +x /usr/local/bin/ap-watchdog.sh
   ```
   
   Add to crontab to run every 5 minutes:
   ```bash
   (crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/ap-watchdog.sh") | crontab -
   ```

## Upgrading and Migration

### Upgrading Raspberry Pi OS

1. **Before Upgrading**
   ```bash
   sudo apt update
   sudo apt full-upgrade
   sudo apt autoremove
   ```

2. **Backup Configuration**
   ```bash
   sudo cp /etc/hostapd/hostapd.conf /home/pi/hostapd.conf.backup
   sudo cp /etc/dnsmasq.conf /home/pi/dnsmasq.conf.backup
   sudo cp /etc/dhcpcd.conf /home/pi/dhcpcd.conf.backup
   ```

3. **Perform Distribution Upgrade**
   ```bash
   sudo apt update
   sudo apt dist-upgrade
   ```

4. **After Upgrading**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart dhcpcd
   sudo systemctl restart dnsmasq
   sudo systemctl restart hostapd
   ```

### Migrating to a New Raspberry Pi

1. **On the Old Pi**
   ```bash
   # Create a tarball of all configuration files
   sudo tar -czvf /home/pi/ap_migration.tar.gz /etc/hostapd /etc/dnsmasq.conf /etc/dhcpcd.conf /usr/local/bin/ap-startup.sh /etc/iptables.ipv4.nat
   ```

2. **Transfer to the New Pi**
   ```bash
   # Using SCP from the new Pi
   scp pi@old-pi-ip:/home/pi/ap_migration.tar.gz /home/pi/
   ```

3. **On the New Pi**
   ```bash
   # Install required packages
   sudo apt update
   sudo apt install hostapd dnsmasq
   
   # Extract configuration files
   sudo tar -xzvf /home/pi/ap_migration.tar.gz -C /
   
   # Set proper permissions
   sudo chmod +x /usr/local/bin/ap-startup.sh
   
   # Enable and start services
   sudo systemctl unmask hostapd
   sudo systemctl enable hostapd
   sudo systemctl enable dnsmasq
   sudo systemctl start hostapd
   sudo systemctl start dnsmasq
   ```

## Best Practices

1. **Keep the Raspberry Pi in a well-ventilated area** to prevent overheating
2. **Use a high-quality power supply** (minimum 2.5A recommended)
3. **Use a high-quality microSD card** from a reputable manufacturer
4. **Perform regular backups** of your configuration
5. **Document any changes** you make to the configuration
6. **Test changes in a controlled environment** before implementing in production
7. **Monitor system logs regularly** for early detection of issues
8. **Keep the system updated** but test major updates in a non-production environment first
9. **Implement proper security measures** including strong passwords and restricted access
10. **Consider using a UPS** (Uninterruptible Power Supply) for critical deployments