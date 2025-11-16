"""
Raspberry Pi Script Upload Utility
==================================

Uploads specified Python scripts to remote Raspberry Pi via SSH and makes them executable.

Features:
- SSH file transfer
- Multiple script upload
- Automatic executable permissions
- Remote deployment
- Error handling

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

import paramiko
import os
import sys

def upload_scripts(host, username, password, port=22):
    """Upload all scripts to the Raspberry Pi"""
    
    scripts = [
        'toggle_outputs.py',
        'set_arm_state.py',
        'get_gpio_status.py',
        'emergency_stop.py',
        'execute_cue.py',
        'execute_show.py'
    ]
    
    try:
        print(f"Connecting to {host}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=host, port=port, username=username, password=password)
        print("✅ Connected via SSH")
        
        sftp = ssh.open_sftp()
        
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        for script in scripts:
            local_path = os.path.join(script_dir, script)
            remote_path = f'/home/{username}/{script}'
            
            if not os.path.exists(local_path):
                print(f"⚠️  Warning: {script} not found locally, skipping...")
                continue
            
            print(f"📤 Uploading {script}...")
            sftp.put(local_path, remote_path)
            
            # Make executable
            ssh.exec_command(f'chmod +x {remote_path}')
            print(f"✅ {script} uploaded and made executable")
        
        sftp.close()
        ssh.close()
        
        print("\n✅ All scripts uploaded successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python upload_scripts.py <host> <username> <password>")
        sys.exit(1)
    
    host = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    
    success = upload_scripts(host, username, password)
    sys.exit(0 if success else 1)