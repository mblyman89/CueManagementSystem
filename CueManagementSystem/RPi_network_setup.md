# Raspberry Pi Zero W2 Network Mode Switching

This setup allows your Raspberry Pi Zero W2 to easily switch between **Ad-Hoc (Hotspot) Mode** and **WiFi Client Mode** with simple commands.

## Features

- **Ad-Hoc Mode**: Creates a WiFi hotspot that your MacBook can connect to directly
- **WiFi Mode**: Connects to your home WiFi network
- **Simple Commands**: Just type `sudo adhoc-mode` or `sudo wifi-mode`
- **Boot Default**: Automatically starts in ad-hoc mode on boot
- **Status Check**: Use `network-status` to see current mode

## Network Details

### Ad-Hoc (Hotspot) Mode
- **SSID**: cuepishifter
- **Password**: cuepishifter
- **Pi IP Address**: 192.168.42.1
- **Your Mac IP**: Will be assigned automatically (192.168.42.x)

### WiFi Client Mode
- **SSID**: Lyman
- **Password**: grandgiant902
- **Pi IP Address**: Assigned by your router (check with `network-status`)

## Installation Instructions

### Step 1: Transfer Scripts to Your Pi

From your Mac, copy the scripts to your Pi:

```bash
# Make sure you're in the pi-scripts directory
cd /path/to/your/project/pi-scripts

# Copy scripts to your Pi (replace 'pi' with your username if different)
# If you're already connected via SSH:
scp adhoc-mode wifi-mode setup-network-switching.sh pi@raspberrypi.local:~/
```

### Step 2: Run Setup on Your Pi

SSH into your Pi and run the setup:

```bash
# SSH to your Pi
ssh pi@raspberrypi.local

# Make the setup script executable
chmod +x setup-network-switching.sh

# Run the setup (requires sudo)
sudo ./setup-network-switching.sh
```

The setup script will:
1. Install NetworkManager (if not already installed)
2. Install dnsmasq-base (for DHCP in ad-hoc mode)
3. Copy the mode-switching scripts to `/usr/local/bin`
4. Configure the Pi to boot into ad-hoc mode by default
5. Create a systemd service for automatic ad-hoc mode on boot

### Step 3: Reboot and Test

```bash
sudo reboot
```

After reboot:
1. Wait about 30 seconds for the Pi to boot
2. On your Mac, open WiFi settings
3. Look for network "cuepishifter"
4. Connect using password "cuepishifter"
5. SSH to the Pi: `ssh pi@192.168.42.1`

## Usage

### Switch to Ad-Hoc Mode

```bash
sudo adhoc-mode
```

This will:
- Disconnect from any WiFi networks
- Create/activate the ad-hoc hotspot
- Display connection information

### Switch to WiFi Mode

```bash
sudo wifi-mode
```

This will:
- Disconnect from ad-hoc mode
- Connect to your WiFi network (Lyman)
- Display the assigned IP address

### Check Network Status

```bash
network-status
```

This shows:
- Current mode (Ad-Hoc or WiFi)
- IP address
- Connected network name
- Available commands

## Connecting from Your Mac

### Ad-Hoc Mode Connection

1. **Open WiFi Settings** on your Mac
2. **Select "cuepishifter"** from available networks
3. **Enter password**: cuepishifter
4. **Wait for connection** (should take 5-10 seconds)
5. **SSH to Pi**: `ssh pi@192.168.42.1`

### WiFi Mode Connection

1. **Ensure your Mac is on the same WiFi** (Lyman)
2. **Find Pi's IP address** by running `network-status` on the Pi
3. **SSH to Pi**: `ssh pi@<IP_ADDRESS>`

## Application Integration

Your `mode_selector_dialog.py` should send these SSH commands:

### For Ad-Hoc Mode Button
```python
ssh_command = "sudo adhoc-mode"
```

### For WiFi Mode Button
```python
ssh_command = "sudo wifi-mode"
```

The application should:
1. Send the command via SSH
2. Wait for completion (may take 5-10 seconds)
3. Display the output to the user
4. Update connection status

## Troubleshooting

### Ad-Hoc Mode Not Working

```bash
# Check NetworkManager status
sudo systemctl status NetworkManager

# Check if connection exists
nmcli connection show

# Try recreating the connection
sudo nmcli connection delete adhoc-cuepishifter
sudo adhoc-mode
```

### WiFi Mode Not Connecting

```bash
# Check WiFi credentials
sudo nmcli connection show wifi-lyman

# Delete and recreate
sudo nmcli connection delete wifi-lyman
sudo wifi-mode

# Check available networks
nmcli device wifi list
```

### Can't Connect from Mac

**For Ad-Hoc Mode:**
1. Make sure you're connecting to "cuepishifter" (not another network)
2. Verify password is exactly "cuepishifter"
3. Try forgetting the network on Mac and reconnecting
4. Check Pi is in ad-hoc mode: `network-status`

**For WiFi Mode:**
1. Ensure Mac is on the same WiFi network (Lyman)
2. Find Pi's IP: `network-status` on Pi
3. Try pinging the Pi: `ping <IP_ADDRESS>`
4. Check router's connected devices list

### Boot Issues

```bash
# Check if service is enabled
sudo systemctl status adhoc-on-boot.service

# View service logs
sudo journalctl -u adhoc-on-boot.service

# Disable auto-start if needed
sudo systemctl disable adhoc-on-boot.service
```

### Manual Network Reset

If everything fails:

```bash
# Stop NetworkManager
sudo systemctl stop NetworkManager

# Remove all connections
sudo rm /etc/NetworkManager/system-connections/*

# Restart NetworkManager
sudo systemctl start NetworkManager

# Run setup again
sudo ./setup-network-switching.sh
```

## Advanced Configuration

### Change Ad-Hoc Network Name/Password

Edit `/usr/local/bin/adhoc-mode`:

```bash
sudo nano /usr/local/bin/adhoc-mode
```

Change these lines:
```bash
ADHOC_SSID="your-new-name"
ADHOC_PASSWORD="your-new-password"
```

### Change WiFi Network

Edit `/usr/local/bin/wifi-mode`:

```bash
sudo nano /usr/local/bin/wifi-mode
```

Change these lines:
```bash
WIFI_SSID="your-wifi-name"
WIFI_PASSWORD="your-wifi-password"
```

### Change Default Boot Mode

To boot into WiFi mode instead:

```bash
# Disable ad-hoc on boot
sudo systemctl disable adhoc-on-boot.service

# Create wifi on boot service
sudo nano /etc/systemd/system/wifi-on-boot.service
```

Add:
```ini
[Unit]
Description=Start WiFi Mode on Boot
After=NetworkManager.service
Wants=NetworkManager.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/wifi-mode
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

Enable it:
```bash
sudo systemctl daemon-reload
sudo systemctl enable wifi-on-boot.service
```

## Technical Details

### How It Works

1. **NetworkManager (nmcli)**: Modern network management for Raspberry Pi OS Bookworm
2. **Connection Profiles**: Stores WiFi and ad-hoc configurations
3. **Systemd Service**: Automatically starts ad-hoc mode on boot
4. **Bash Scripts**: Simple commands to switch between modes

### Files Created

- `/usr/local/bin/adhoc-mode` - Ad-hoc mode script
- `/usr/local/bin/wifi-mode` - WiFi mode script
- `/usr/local/bin/network-status` - Status checker
- `/etc/systemd/system/adhoc-on-boot.service` - Boot service
- `/etc/NetworkManager/system-connections/adhoc-cuepishifter.nmconnection` - Ad-hoc profile
- `/etc/NetworkManager/system-connections/wifi-lyman.nmconnection` - WiFi profile

### Network Architecture

**Ad-Hoc Mode:**
```
Mac (192.168.42.x) <--WiFi--> Pi (192.168.42.1)
```

**WiFi Mode:**
```
Mac <--WiFi--> Router <--WiFi--> Pi
```

## Security Notes

1. **Passwords in Scripts**: The scripts contain WiFi passwords in plain text. Ensure proper file permissions.
2. **Ad-Hoc Security**: Uses WPA2-PSK encryption
3. **SSH Access**: Always use strong passwords for SSH
4. **Network Isolation**: Ad-hoc mode creates an isolated network

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Run `network-status` to see current state
3. Check logs: `sudo journalctl -u NetworkManager`
4. Verify NetworkManager is running: `sudo systemctl status NetworkManager`

## Credits

Based on NetworkManager (nmcli) best practices for Raspberry Pi OS Bookworm and modern Linux distributions.