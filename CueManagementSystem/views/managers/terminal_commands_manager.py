"""
Terminal Command Simulator
==========================

Simulates macOS terminal environment by providing predefined outputs for common terminal commands.

Features:
- Command output simulation
- Support for ls, pwd, date, ifconfig
- cd command handling
- echo command support
- macOS-specific outputs
- Testing and development support

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

import os
import time
from datetime import datetime

# Dictionary of simulated macOS commands and their outputs
MAC_COMMANDS = {
    "ls": """Applications    Documents    Library    Music    Public
Desktop         Downloads    Movies     Pictures   Projects""",

    "pwd": "/Users/michaellyman",

    "whoami": "michaellyman",

    "date": lambda: datetime.now().strftime("%a %b %d %H:%M:%S %Z %Y"),

    "hostname": "Michaels-MacBook-Pro.local",

    "uname": "Darwin Michaels-MacBook-Pro.local 22.5.0 Darwin Kernel Version 22.5.0: Mon Apr 24 20:52:24 PDT 2023; root:xnu-8796.121.2~5/RELEASE_ARM64_T6000 arm64",

    "uname -a": "Darwin Michaels-MacBook-Pro.local 22.5.0 Darwin Kernel Version 22.5.0: Mon Apr 24 20:52:24 PDT 2023; root:xnu-8796.121.2~5/RELEASE_ARM64_T6000 arm64",

    "ps": """  PID TTY           TIME CMD
 1234 ttys002    0:00.11 -zsh
 1256 ttys002    0:00.03 python3
 1278 ttys002    0:01.22 /Applications/PyCharm.app/Contents/MacOS/pycharm""",

    "top -l 1": """Processes: 342 total, 2 running, 340 sleeping, 1512 threads 
Load Avg: 1.43, 1.56, 1.59  CPU usage: 2.12% user, 1.56% sys, 96.31% idle 
SharedLibs: 269M resident, 46M data, 17M linkedit.
MemRegions: 77469 total, 1266M resident, 65M private, 455M shared.
PhysMem: 8192M used (1805M wired), 8192M unused.
VM: 184G vsize, 1122M framework vsize, 0(0) swapins, 0(0) swapouts.
Networks: packets: 452278/426M in, 452278/426M out.
Disks: 124567/2G read, 23456/1G written.""",

    "df -h": """Filesystem      Size   Used  Avail Capacity     iused      ifree %iused  Mounted on
/dev/disk1s1   466Gi  210Gi  242Gi    47%    1234567    2345678   35%   /
devfs          186Ki  186Ki    0Bi   100%        644          0  100%   /dev
/dev/disk1s2   466Gi  9.0Gi  242Gi     4%          3    2345678    0%   /System/Volumes/Preboot
/dev/disk1s3   466Gi  2.5Mi  242Gi     1%         74    2345678    0%   /System/Volumes/VM
/dev/disk1s5   466Gi  4.0Gi  242Gi     2%      12345    2345678    1%   /System/Volumes/Update
/dev/disk1s6   466Gi  210Gi  242Gi    47%    1234567    2345678   35%   /System/Volumes/Data""",

    "ifconfig": """en0: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500
	options=400<CHANNEL_IO>
	ether a4:83:e7:4e:a2:b1
	inet6 fe80::c45:7751:a3b1:a2c1%en0 prefixlen 64 secured scopeid 0x5 
	inet 192.168.1.123 netmask 0xffffff00 broadcast 192.168.1.255
	nd6 options=201<PERFORMNUD,DAD>
	media: autoselect
	status: active""",

    "ping -c 3 google.com": """PING google.com (142.250.190.78): 56 data bytes
64 bytes from 142.250.190.78: icmp_seq=0 ttl=116 time=14.919 ms
64 bytes from 142.250.190.78: icmp_seq=1 ttl=116 time=15.895 ms
64 bytes from 142.250.190.78: icmp_seq=2 ttl=116 time=13.990 ms

--- google.com ping statistics ---
3 packets transmitted, 3 packets received, 0.0% packet loss
round-trip min/avg/max/stddev = 13.990/14.935/15.895/0.778 ms""",

    "help": """This is a simulated macOS terminal.
You can use 'ssh username@hostname' to connect to your Pi.
Basic commands like ls, pwd, clear, etc. are simulated.

Available commands:
  ls          - List files and directories
  pwd         - Print working directory
  whoami      - Display current user
  date        - Display current date and time
  hostname    - Display system hostname
  uname       - Display system information
  ps          - Display process status
  top -l 1    - Display system statistics
  df -h       - Display disk usage
  ifconfig    - Display network interfaces
  ping        - Test network connectivity
  ssh         - Connect to remote system
  clear       - Clear the terminal screen
  help        - Display this help message""",

    "?": lambda: MAC_COMMANDS["help"]
}


# Function to get command output
def get_mac_command_output(command):
    """Get the output for a simulated macOS command"""
    # Check for exact command match
    if command in MAC_COMMANDS:
        result = MAC_COMMANDS[command]
        if callable(result):
            return result()
        return result

    # Check for command with arguments
    cmd_parts = command.split(None, 1)
    base_cmd = cmd_parts[0]

    # Handle cd command specially
    if base_cmd == "cd":
        if len(cmd_parts) > 1:
            return f"Changed directory to {cmd_parts[1]}"
        else:
            return "Changed directory to /Users/michaellyman"

    # Handle echo command specially
    if base_cmd == "echo":
        if len(cmd_parts) > 1:
            return cmd_parts[1]
        else:
            return ""

    # Handle other commands with arguments
    for cmd in MAC_COMMANDS:
        if cmd.startswith(base_cmd + " "):
            if command == cmd:
                result = MAC_COMMANDS[cmd]
                if callable(result):
                    return result()
                return result

    # Command not found
    return f"-zsh: command not found: {base_cmd}"