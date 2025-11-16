"""
Network Mode Switching Script
=============================

Command-line interface for switching between WiFi and ad-hoc network modes with JSON status output.

Features:
- WiFi mode switching
- Ad-hoc mode switching
- Bash script integration
- JSON status output
- Command-line interface
- Network configuration management

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

import sys
import subprocess
import json
import argparse

def switch_mode(mode):
    """
    Switch network mode using bash scripts
    
    Args:
        mode: Either 'wifi' or 'adhoc'
    
    Returns:
        dict: Status information
    """
    try:
        if mode == 'wifi':
            command = ['sudo', '/usr/local/bin/wifi-mode']
        elif mode == 'adhoc':
            command = ['sudo', '/usr/local/bin/adhoc-mode']
        else:
            return {
                'success': False,
                'error': f'Invalid mode: {mode}. Must be "wifi" or "adhoc"'
            }
        
        # Execute the command
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return {
                'success': True,
                'mode': mode,
                'message': f'Successfully switched to {mode} mode',
                'output': result.stdout
            }
        else:
            return {
                'success': False,
                'mode': mode,
                'error': result.stderr or result.stdout,
                'message': f'Failed to switch to {mode} mode'
            }
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Command timed out after 30 seconds'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def main():
    parser = argparse.ArgumentParser(description='Switch network mode')
    parser.add_argument('--mode', required=True, choices=['wifi', 'adhoc'],
                       help='Network mode to switch to')
    
    args = parser.parse_args()
    
    result = switch_mode(args.mode)
    
    # Print JSON output for application parsing
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)

if __name__ == '__main__':
    main()