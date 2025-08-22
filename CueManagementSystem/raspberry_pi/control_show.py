#!/usr/bin/env python3
"""
Control Show Script for Raspberry Pi

This script provides control functions for a running show:
- Pause a running show
- Resume a paused show
- Abort a running show

Usage:
    python3 control_show.py --action=pause|resume|abort
"""

import argparse
import sys
import os
import logging
import json
import time
import signal
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/home/pi/show_control.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("control_show")

# Path to the show control file
CONTROL_FILE = "/home/pi/show_control.json"


def get_show_status():
    """
    Get the current show status

    Returns:
        dict: Show status information
    """
    try:
        if os.path.exists(CONTROL_FILE):
            with open(CONTROL_FILE, 'r') as f:
                return json.load(f)
        else:
            # Default status if file doesn't exist
            return {
                "running": False,
                "paused": False,
                "pid": None,
                "start_time": None,
                "last_update": time.time()
            }
    except Exception as e:
        logger.error(f"Error reading show status: {e}")
        return {
            "running": False,
            "paused": False,
            "pid": None,
            "start_time": None,
            "last_update": time.time()
        }


def update_show_status(status):
    """
    Update the show status file

    Args:
        status: Status dictionary to write
    """
    try:
        # Update the last_update timestamp
        status["last_update"] = time.time()

        with open(CONTROL_FILE, 'w') as f:
            json.dump(status, f)

        logger.debug(f"Updated show status: {status}")
        return True
    except Exception as e:
        logger.error(f"Error updating show status: {e}")
        return False


def is_process_running(pid):
    """
    Check if a process with the given PID is running

    Args:
        pid: Process ID to check

    Returns:
        bool: True if process is running
    """
    try:
        if pid is None:
            return False

        # Send signal 0 to check if process exists
        os.kill(pid, 0)
        return True
    except OSError:
        return False
    except Exception as e:
        logger.error(f"Error checking process status: {e}")
        return False


def pause_show():
    """
    Pause a running show

    Returns:
        bool: True if pause successful
    """
    status = get_show_status()

    if not status["running"]:
        logger.warning("No show is currently running")
        return False

    if status["paused"]:
        logger.warning("Show is already paused")
        return True

    try:
        # Update status to paused
        status["paused"] = True
        update_show_status(status)

        # Send SIGUSR1 to the show process to signal pause
        if status["pid"]:
            os.kill(status["pid"], signal.SIGUSR1)
            logger.info(f"Sent pause signal to show process (PID: {status['pid']})")

        # Also run execute_show.py with --pause flag as a backup method
        subprocess.run(["python3", "/home/pi/execute_show.py", "--pause"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        logger.info("Show paused successfully")
        return True
    except Exception as e:
        logger.error(f"Error pausing show: {e}")
        return False


def resume_show():
    """
    Resume a paused show

    Returns:
        bool: True if resume successful
    """
    status = get_show_status()

    if not status["running"]:
        logger.warning("No show is currently running")
        return False

    if not status["paused"]:
        logger.warning("Show is not paused")
        return True

    try:
        # Update status to not paused
        status["paused"] = False
        update_show_status(status)

        # Send SIGUSR2 to the show process to signal resume
        if status["pid"]:
            os.kill(status["pid"], signal.SIGUSR2)
            logger.info(f"Sent resume signal to show process (PID: {status['pid']})")

        # Also run execute_show.py with --resume flag as a backup method
        subprocess.run(["python3", "/home/pi/execute_show.py", "--resume"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        logger.info("Show resumed successfully")
        return True
    except Exception as e:
        logger.error(f"Error resuming show: {e}")
        return False


def abort_show():
    """
    Abort a running show

    Returns:
        bool: True if abort successful
    """
    status = get_show_status()

    if not status["running"]:
        logger.warning("No show is currently running")
        return False

    try:
        # Update status to not running
        status["running"] = False
        status["paused"] = False
        update_show_status(status)

        # Send SIGTERM to the show process to signal abort
        if status["pid"] and is_process_running(status["pid"]):
            os.kill(status["pid"], signal.SIGTERM)
            logger.info(f"Sent abort signal to show process (PID: {status['pid']})")

        # Also run execute_show.py with --abort flag as a backup method
        subprocess.run(["python3", "/home/pi/execute_show.py", "--abort"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Run emergency stop to ensure all outputs are disabled
        subprocess.run(["python3", "/home/pi/emergency_stop.py"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        logger.info("Show aborted successfully")
        return True
    except Exception as e:
        logger.error(f"Error aborting show: {e}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Control a running show")
    parser.add_argument("--action", type=str, required=True, choices=["pause", "resume", "abort"],
                        help="Action to perform (pause, resume, abort)")

    args = parser.parse_args()

    if args.action == "pause":
        success = pause_show()
        if success:
            print("Show paused successfully")
            sys.exit(0)
        else:
            print("Failed to pause show")
            sys.exit(1)

    elif args.action == "resume":
        success = resume_show()
        if success:
            print("Show resumed successfully")
            sys.exit(0)
        else:
            print("Failed to resume show")
            sys.exit(1)

    elif args.action == "abort":
        success = abort_show()
        if success:
            print("Show aborted successfully")
            sys.exit(0)
        else:
            print("Failed to abort show")
            sys.exit(1)


if __name__ == "__main__":
    main()