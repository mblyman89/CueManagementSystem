"""
UE5 Manager
===========

Manages Unreal Engine 5 installation detection, project launching,
and communication with the UE5 firework visualizer.

Features:
- Auto-detect UE5 installation
- Launch UE5 project
- Manage UE5 process
- WebSocket communication
- Settings management

Author: SuperNinja AI
Version: 1.0.0
License: MIT
"""

import os
import json
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from PySide6.QtCore import QObject, Signal, QTimer


class UE5Manager(QObject):
    """Manager for UE5 installation and project launching"""

    # Signals
    ue5_launched = Signal()  # UE5 project launched successfully
    ue5_closed = Signal()  # UE5 project closed
    ue5_error = Signal(str)  # Error occurred
    connection_status_changed = Signal(bool)  # Connection status changed

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        # UE5 settings
        self.settings_file = Path.home() / ".cuemanagement" / "ue5_settings.json"
        self.settings = self._load_settings()

        # UE5 process
        self.ue5_process = None
        self.is_running = False

        # Connection monitoring
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self._check_connection)
        self.is_connected = False

        self.logger.info("UE5Manager initialized")

    def _load_settings(self) -> Dict[str, Any]:
        """Load UE5 settings from file"""
        default_settings = {
            'ue5_engine_path': '',
            'ue5_project_path': '',
            'auto_launch': True,
            'launch_timeout': 60,
            'websocket_port': 8765
        }

        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults
                    default_settings.update(loaded)
                    self.logger.info("Loaded UE5 settings")
            else:
                # Create settings directory if it doesn't exist
                self.settings_file.parent.mkdir(parents=True, exist_ok=True)
                self._save_settings(default_settings)
        except Exception as e:
            self.logger.error(f"Failed to load UE5 settings: {e}")

        return default_settings

    def _save_settings(self, settings: Dict[str, Any] = None):
        """Save UE5 settings to file"""
        if settings is None:
            settings = self.settings

        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            self.logger.info("Saved UE5 settings")
        except Exception as e:
            self.logger.error(f"Failed to save UE5 settings: {e}")

    def update_settings(self, **kwargs):
        """Update UE5 settings"""
        self.settings.update(kwargs)
        self._save_settings()
        self.logger.info(f"Updated UE5 settings: {kwargs}")

    def is_ue5_available(self) -> bool:
        """Check if UE5 is properly configured and available"""
        engine_path = self.settings.get('ue5_engine_path', '')
        project_path = self.settings.get('ue5_project_path', '')

        # Check if paths are set
        if not engine_path or not project_path:
            return False

        # Check if paths exist
        if not os.path.exists(engine_path):
            self.logger.warning(f"UE5 engine path does not exist: {engine_path}")
            return False

        if not os.path.exists(project_path):
            self.logger.warning(f"UE5 project path does not exist: {project_path}")
            return False

        return True

    def detect_ue5_installation(self) -> Optional[str]:
        """
        Auto-detect UE5 installation on the system

        Returns:
            Path to UE5 engine executable, or None if not found
        """
        possible_paths = []

        # macOS paths
        if os.name == 'posix':
            possible_paths.extend([
                '/Users/Shared/Epic Games/UE_5.4/Engine/Binaries/Mac/UnrealEditor.app',
                '/Users/Shared/Epic Games/UE_5.3/Engine/Binaries/Mac/UnrealEditor.app',
                str(Path.home() / 'Library/Epic Games/UE_5.4/Engine/Binaries/Mac/UnrealEditor.app'),
                str(Path.home() / 'Library/Epic Games/UE_5.3/Engine/Binaries/Mac/UnrealEditor.app'),
            ])

        # Windows paths
        elif os.name == 'nt':
            possible_paths.extend([
                'C:/Program Files/Epic Games/UE_5.4/Engine/Binaries/Win64/UnrealEditor.exe',
                'C:/Program Files/Epic Games/UE_5.3/Engine/Binaries/Win64/UnrealEditor.exe',
            ])

        # Check each path
        for path in possible_paths:
            if os.path.exists(path):
                self.logger.info(f"Found UE5 installation: {path}")
                return path

        self.logger.warning("Could not auto-detect UE5 installation")
        return None

    def launch_ue5_project(self) -> bool:
        """
        Launch the UE5 firework visualizer project

        Returns:
            True if launched successfully, False otherwise
        """
        if not self.is_ue5_available():
            self.logger.error("UE5 is not available")
            self.ue5_error.emit("UE5 is not configured. Please set up UE5 in Preferences.")
            return False

        if self.is_running:
            self.logger.warning("UE5 is already running")
            return True

        try:
            engine_path = self.settings['ue5_engine_path']
            project_path = self.settings['ue5_project_path']

            self.logger.info(f"Launching UE5 project: {project_path}")

            # Build command
            if os.name == 'posix':  # macOS
                cmd = ['open', engine_path, '--args', project_path]
            else:  # Windows
                cmd = [engine_path, project_path]

            # Launch process
            self.ue5_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            self.is_running = True
            self.ue5_launched.emit()

            # Start connection monitoring
            self.connection_timer.start(2000)  # Check every 2 seconds

            self.logger.info("UE5 project launched successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to launch UE5: {e}")
            self.ue5_error.emit(f"Failed to launch UE5: {str(e)}")
            return False

    def close_ue5_project(self):
        """Close the UE5 project"""
        if self.ue5_process and self.is_running:
            try:
                self.ue5_process.terminate()
                self.ue5_process.wait(timeout=10)
                self.logger.info("UE5 project closed")
            except Exception as e:
                self.logger.error(f"Error closing UE5: {e}")
                try:
                    self.ue5_process.kill()
                except:
                    pass

            self.ue5_process = None
            self.is_running = False
            self.is_connected = False
            self.connection_timer.stop()
            self.ue5_closed.emit()
            self.connection_status_changed.emit(False)

    def _check_connection(self):
        """Check if UE5 is still running and connected"""
        if not self.is_running:
            return

        # Check if process is still alive
        if self.ue5_process and self.ue5_process.poll() is not None:
            # Process has terminated
            self.logger.info("UE5 process has terminated")
            self.is_running = False
            self.is_connected = False
            self.connection_timer.stop()
            self.ue5_closed.emit()
            self.connection_status_changed.emit(False)
            return

        # TODO: Check WebSocket connection status
        # For now, assume connected if process is running
        if not self.is_connected:
            self.is_connected = True
            self.connection_status_changed.emit(True)

    def get_ue5_status(self) -> Dict[str, Any]:
        """Get current UE5 status"""
        return {
            'available': self.is_ue5_available(),
            'running': self.is_running,
            'connected': self.is_connected,
            'engine_path': self.settings.get('ue5_engine_path', ''),
            'project_path': self.settings.get('ue5_project_path', '')
        }