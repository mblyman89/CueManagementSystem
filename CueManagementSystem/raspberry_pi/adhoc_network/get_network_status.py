#!/usr/bin/env python3
"""
Python wrapper for network status checking
This script maintains compatibility with the existing application
while using NetworkManager for actual status checking
"""

import subprocess
import json
import re

def get_network_status():
    """
    Get current network status using nmcli
    
    Returns:
        dict: Network status information
    """
    try:
        # Get active connections
        result = subprocess.run(
            ['nmcli', '-t', '-f', 'NAME,TYPE,DEVICE', 'connection', 'show', '--active'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return {
                'success': False,
                'mode': 'unknown',
                'error': 'Failed to get network status'
            }
        
        # Parse output
        active_connections = result.stdout.strip().split('\n')
        wlan_connection = None
        
        for conn in active_connections:
            if 'wlan0' in conn:
                wlan_connection = conn
                break
        
        if not wlan_connection:
            return {
                'success': True,
                'mode': 'disconnected',
                'message': 'No active wireless connection',
                'connected': False
            }
        
        # Parse connection details
        conn_parts = wlan_connection.split(':')
        conn_name = conn_parts[0] if len(conn_parts) > 0 else 'unknown'
        
        # Determine mode based on connection name
        if 'adhoc' in conn_name.lower():
            mode = 'adhoc'
            ssid = 'cuepishifter'
        else:
            mode = 'wifi'
            # Get SSID for wifi mode
            ssid_result = subprocess.run(
                ['nmcli', '-t', '-f', 'active,ssid', 'dev', 'wifi'],
                capture_output=True,
                text=True,
                timeout=5
            )
            ssid = 'unknown'
            for line in ssid_result.stdout.split('\n'):
                if line.startswith('yes:'):
                    ssid = line.split(':', 1)[1]
                    break
        
        # Get IP address
        ip_result = subprocess.run(
            ['ip', '-4', 'addr', 'show', 'wlan0'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        ip_address = 'unknown'
        ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', ip_result.stdout)
        if ip_match:
            ip_address = ip_match.group(1)
        
        return {
            'success': True,
            'mode': mode,
            'connected': True,
            'connection_name': conn_name,
            'ssid': ssid,
            'ip_address': ip_address,
            'message': f'Connected in {mode} mode'
        }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'mode': 'unknown',
            'error': 'Command timed out'
        }
    except Exception as e:
        return {
            'success': False,
            'mode': 'unknown',
            'error': str(e)
        }

def main():
    status = get_network_status()
    print(json.dumps(status, indent=2))

if __name__ == '__main__':
    main()