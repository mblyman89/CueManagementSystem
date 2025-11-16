"""
SSH Terminal Session Manager
============================

Manages SSH connections, command execution, and persistent command history with PTY management.

Features:
- SSH connection handling
- Command execution
- Persistent command history
- PTY management
- Terminal emulation
- Session state management
- macOS Terminal.app functionality emulation

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

import json
import os
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from collections import deque

import paramiko
from PySide6.QtCore import QObject, Signal, QTimer, QSettings


class SSHConnection:
    """Manages a single SSH connection with keepalive and health monitoring"""

    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

        self.client: Optional[paramiko.SSHClient] = None
        self.channel: Optional[paramiko.Channel] = None
        self.connected = False
        self.last_activity = time.time()
        self.keepalive_interval = 30  # seconds
        self.connection_timeout = 10  # seconds

        # Lock for thread-safe operations
        self.lock = threading.Lock()

    def connect(self) -> Tuple[bool, str]:
        """
        Establish SSH connection with keepalive

        Returns:
            Tuple of (success: bool, message: str)
        """
        print(f"[DEBUG] SSHConnection.connect() called for {self.username}@{self.host}")

        try:
            # Close existing connection if any (without lock to avoid deadlock)
            if self.client:
                print("[DEBUG] Closing existing client")
                try:
                    self.client.close()
                except:
                    pass
                self.client = None

            # Create new SSH client
            print("[DEBUG] Creating new SSH client")
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect with timeout
            print(f"[DEBUG] Connecting to {self.host}:{self.port}")
            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=self.connection_timeout,
                banner_timeout=self.connection_timeout,
                auth_timeout=self.connection_timeout,
                look_for_keys=False,
                allow_agent=False
            )

            print("[DEBUG] Connection successful, enabling keepalive")

            # Enable keepalive
            transport = self.client.get_transport()
            if transport:
                transport.set_keepalive(self.keepalive_interval)

            self.connected = True
            self.last_activity = time.time()

            print(f"[DEBUG] Connected successfully to {self.username}@{self.host}")
            return True, f"Connected to {self.username}@{self.host}"

        except paramiko.AuthenticationException as e:
            print(f"[DEBUG] Authentication failed: {e}")
            return False, "Authentication failed - check username/password"
        except paramiko.SSHException as e:
            print(f"[DEBUG] SSH error: {e}")
            return False, f"SSH error: {str(e)}"
        except Exception as e:
            print(f"[DEBUG] Connection error: {e}")
            return False, f"Connection error: {str(e)}"

    def disconnect(self):
        """Close SSH connection"""
        print("[DEBUG] SSHConnection.disconnect() called")
        try:
            if self.channel:
                self.channel.close()
                self.channel = None

            if self.client:
                self.client.close()
                self.client = None

            self.connected = False
            print("[DEBUG] Disconnected successfully")

        except Exception as e:
            print(f"[DEBUG] Error during disconnect: {e}")
            pass  # Ignore errors during disconnect

    def is_alive(self) -> bool:
        """Check if connection is still alive"""
        if not self.connected or not self.client:
            return False

        try:
            transport = self.client.get_transport()
            if not transport or not transport.is_active():
                self.connected = False
                return False

            # Send keepalive if needed
            if time.time() - self.last_activity > self.keepalive_interval:
                transport.send_ignore()
                self.last_activity = time.time()

            return True

        except Exception:
            self.connected = False
            return False

    def execute_command(self, command: str, timeout: int = 30) -> Tuple[bool, str, str]:
        """
        Execute a command and return output

        Args:
            command: Command to execute
            timeout: Command timeout in seconds

        Returns:
            Tuple of (success: bool, stdout: str, stderr: str)
        """
        print(f"[DEBUG] SSHConnection.execute_command() called: {command}")

        if not self.is_alive():
            print("[DEBUG] Connection not alive")
            return False, "", "Not connected"

        try:
            print(f"[DEBUG] Executing command via SSH: {command}")
            stdin, stdout, stderr = self.client.exec_command(
                command,
                timeout=timeout,
                get_pty=False  # Don't allocate PTY for simple commands
            )

            print("[DEBUG] Reading stdout")
            stdout_data = stdout.read().decode('utf-8', errors='replace')
            print(f"[DEBUG] stdout: {stdout_data[:100]}...")

            print("[DEBUG] Reading stderr")
            stderr_data = stderr.read().decode('utf-8', errors='replace')
            if stderr_data:
                print(f"[DEBUG] stderr: {stderr_data[:100]}...")

            self.last_activity = time.time()

            print("[DEBUG] Command executed successfully")
            return True, stdout_data, stderr_data

        except Exception as e:
            print(f"[DEBUG] Command execution error: {e}")
            return False, "", str(e)

    def open_pty_channel(self, term: str = 'xterm', width: int = 80, height: int = 24) -> Tuple[bool, str]:
        """
        Open a PTY channel for interactive commands

        Args:
            term: Terminal type
            width: Terminal width in characters
            height: Terminal height in lines

        Returns:
            Tuple of (success: bool, message: str)
        """
        with self.lock:
            if not self.is_alive():
                return False, "Not connected"

            try:
                # Close existing channel if any
                if self.channel:
                    self.channel.close()

                # Open new channel with PTY
                self.channel = self.client.invoke_shell(
                    term=term,
                    width=width,
                    height=height
                )

                # Set non-blocking mode
                self.channel.setblocking(0)

                self.last_activity = time.time()

                return True, "PTY channel opened"

            except Exception as e:
                return False, f"Failed to open PTY: {str(e)}"

    def send_to_channel(self, data: str) -> bool:
        """
        Send data to PTY channel

        Args:
            data: Data to send

        Returns:
            Success status
        """
        with self.lock:
            if not self.channel or not self.channel.active:
                return False

            try:
                self.channel.send(data)
                self.last_activity = time.time()
                return True

            except Exception:
                return False

    def recv_from_channel(self, size: int = 4096) -> str:
        """
        Receive data from PTY channel

        Args:
            size: Maximum bytes to receive

        Returns:
            Received data as string
        """
        with self.lock:
            if not self.channel or not self.channel.active:
                return ""

            try:
                if self.channel.recv_ready():
                    data = self.channel.recv(size)
                    self.last_activity = time.time()
                    return data.decode('utf-8', errors='replace')
                return ""

            except Exception:
                return ""

    def resize_pty(self, width: int, height: int):
        """Resize PTY terminal"""
        with self.lock:
            if self.channel and self.channel.active:
                try:
                    self.channel.resize_pty(width=width, height=height)
                except Exception:
                    pass


class TerminalSessionManager(QObject):
    """
    Manages terminal sessions with persistent state and command history
    """

    # Signals
    output_received = Signal(str)  # Emitted when output is received
    connection_status_changed = Signal(bool, str)  # Emitted when connection status changes
    error_occurred = Signal(str)  # Emitted when an error occurs

    def __init__(self, parent=None):
        super().__init__(parent)

        # Connection settings
        self.host = ""
        self.port = 22
        self.username = ""
        self.password = ""

        # SSH connection
        self.connection: Optional[SSHConnection] = None

        # Command history
        self.command_history: deque = deque(maxlen=1000)  # Last 1000 commands
        self.history_file = Path.home() / ".firework_terminal_history"
        self.load_command_history()

        # Session state
        self.current_directory = "~"
        self.environment_vars: Dict[str, str] = {}

        # PTY mode
        self.pty_mode = False
        self.pty_buffer = ""

        # Connection monitoring - DISABLED to prevent deadlocks
        # TODO: Re-enable with proper thread-safe implementation
        self.monitor_timer = QTimer(self)
        self.monitor_timer.timeout.connect(self._monitor_connection)
        # self.monitor_timer.start(5000)  # Check every 5 seconds - DISABLED

        # Auto-reconnect
        self.auto_reconnect = True
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5

        # PTY reader timer
        self.pty_reader_timer = QTimer(self)
        self.pty_reader_timer.timeout.connect(self._read_pty_output)

    def set_connection_settings(self, host: str, port: int, username: str, password: str):
        """Update connection settings"""
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def connect(self) -> Tuple[bool, str]:
        """
        Connect to SSH server

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.host or not self.username:
            return False, "Host and username are required"

        # Create new connection
        self.connection = SSHConnection(
            self.host,
            self.port,
            self.username,
            self.password
        )

        success, message = self.connection.connect()

        if success:
            self.reconnect_attempts = 0
            self.connection_status_changed.emit(True, message)
        else:
            self.connection_status_changed.emit(False, message)

        return success, message

    def disconnect(self):
        """Disconnect from SSH server"""
        if self.connection:
            self.connection.disconnect()
            self.connection = None
            self.pty_mode = False
            self.pty_reader_timer.stop()
            self.connection_status_changed.emit(False, "Disconnected")

    def is_connected(self) -> bool:
        """Check if connected"""
        return self.connection and self.connection.is_alive()

    def execute_command(self, command: str, use_pty: bool = False) -> Tuple[bool, str]:
        """
        Execute a command

        Args:
            command: Command to execute
            use_pty: Whether to use PTY for interactive commands

        Returns:
            Tuple of (success: bool, message: str)
        """
        print(f"[DEBUG] TerminalSessionManager.execute_command() called: {command}")

        if not command.strip():
            return True, ""

        # Add to history
        self.add_to_history(command)

        # Check if connected
        print("[DEBUG] Checking connection status...")
        if not self.is_connected():
            print("[DEBUG] Not connected, attempting to connect...")
            # Try to reconnect
            success, msg = self.connect()
            print(f"[DEBUG] Connect result: {success}, {msg}")
            if not success:
                return False, f"Not connected: {msg}"
        else:
            print("[DEBUG] Already connected")

        # Determine if this is an interactive command
        # NOTE: nano is handled by custom file editor, not PTY
        interactive_commands = ['vi', 'vim', 'emacs', 'less', 'more', 'top', 'htop']
        is_interactive = any(cmd in command.split()[0] for cmd in interactive_commands)

        # Special handling for sudo - check if it's sudo nano
        if command.strip().startswith('sudo'):
            parts = command.split()
            if len(parts) > 1 and 'nano' in parts[1]:
                is_interactive = False  # Let custom editor handle sudo nano
            else:
                is_interactive = True  # Other sudo commands use PTY

        print(f"[DEBUG] is_interactive={is_interactive}, use_pty={use_pty}")

        if is_interactive or use_pty:
            print("[DEBUG] Using interactive command execution")
            return self._execute_interactive_command(command)
        else:
            print("[DEBUG] Using simple command execution")
            return self._execute_simple_command(command)

    def _execute_simple_command(self, command: str) -> Tuple[bool, str]:
        """Execute a simple non-interactive command"""
        success, stdout, stderr = self.connection.execute_command(command)

        if success:
            output = stdout
            if stderr:
                output += stderr
            return True, output
        else:
            return False, stderr

    def _execute_interactive_command(self, command: str) -> Tuple[bool, str]:
        """Execute an interactive command using PTY"""
        # Open PTY channel if not already open
        if not self.pty_mode:
            success, msg = self.connection.open_pty_channel()
            if not success:
                return False, msg

            self.pty_mode = True
            self.pty_buffer = ""

            # Start PTY reader
            self.pty_reader_timer.start(50)  # Read every 50ms

            # Wait for initial prompt
            time.sleep(0.5)
            self._read_pty_output()

        # Send command
        if not self.connection.send_to_channel(command + '\n'):
            return False, "Failed to send command"

        # Give command time to start
        time.sleep(0.1)

        return True, "Command sent to PTY"

    def send_to_pty(self, data: str) -> bool:
        """Send data to PTY channel"""
        if not self.pty_mode or not self.connection:
            return False

        return self.connection.send_to_channel(data)

    def _read_pty_output(self):
        """Read output from PTY channel"""
        if not self.pty_mode or not self.connection:
            return

        output = self.connection.recv_from_channel()
        if output:
            self.pty_buffer += output
            self.output_received.emit(output)

    def close_pty(self):
        """Close PTY channel"""
        if self.pty_mode and self.connection:
            self.connection.channel.close()
            self.pty_mode = False
            self.pty_reader_timer.stop()

    def _monitor_connection(self):
        """Monitor connection health and auto-reconnect if needed"""
        if not self.connection:
            return

        if not self.connection.is_alive():
            self.connection_status_changed.emit(False, "Connection lost")

            # Try to reconnect if enabled
            if self.auto_reconnect and self.reconnect_attempts < self.max_reconnect_attempts:
                self.reconnect_attempts += 1
                success, msg = self.connect()

                if success:
                    self.connection_status_changed.emit(True, "Reconnected")
                else:
                    self.error_occurred.emit(f"Reconnection attempt {self.reconnect_attempts} failed: {msg}")

    def add_to_history(self, command: str):
        """Add command to history"""
        if command and command.strip():
            # Don't add duplicate consecutive commands
            if not self.command_history or self.command_history[-1] != command:
                self.command_history.append(command)
                self.save_command_history()

    def get_history(self) -> List[str]:
        """Get command history"""
        return list(self.command_history)

    def load_command_history(self):
        """Load command history from file"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
                    self.command_history = deque(history, maxlen=1000)
        except Exception:
            pass  # Ignore errors loading history

    def save_command_history(self):
        """Save command history to file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(list(self.command_history), f)
        except Exception:
            pass  # Ignore errors saving history

    def clear_history(self):
        """Clear command history"""
        self.command_history.clear()
        self.save_command_history()

    def resize_terminal(self, width: int, height: int):
        """Resize terminal"""
        if self.connection and self.pty_mode:
            self.connection.resize_pty(width, height)