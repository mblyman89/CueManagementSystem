"""
VR Preview Controller - Embedded Visualizer Version
===================================================

Controller for managing VR firework show previews with embedded visualization.
Handles countdown, music synchronization, and cue execution timing.

This version works with the embedded visualizer - no separate process needed!

Features:
- 10-second countdown before preview starts
- Perfect music and cue synchronization (T=0)
- Direct rendering to embedded canvas
- Fullscreen preview window
- Optional music playback
- Auto-server management

Author: SuperNinja AI
Version: 2.0.0 (Embedded Visualizer)
License: MIT
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QTimer


class VRPreviewController(QObject):
    """
    Controller for VR preview mode with embedded visualizer

    Manages the VR preview lifecycle including countdown, music sync,
    and cue execution timing. Renders directly to embedded canvas.
    """

    # Signals
    countdown_tick = Signal(int)  # Countdown number (10, 9, 8, ...)
    preview_started = Signal()  # Preview has started (T=0)
    preview_completed = Signal()  # Preview finished
    preview_error = Signal(str)  # Error occurred
    cue_executed = Signal(str)  # Cue ID executed

    def __init__(self, preview_window=None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        # Reference to the preview window (for direct rendering)
        self.preview_window = preview_window

        # Preview state
        self.is_previewing = False
        self.preview_cues: List[Dict[str, Any]] = []
        self.music_file: Optional[Dict[str, Any]] = None
        self.start_time: Optional[datetime] = None

        # Countdown timer
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self._countdown_tick)
        self.countdown_value = 10

        # Cue execution timer
        self.execution_timer = QTimer()
        self.execution_timer.timeout.connect(self._check_cue_execution)

        # Track executed cues to prevent duplicate execution
        self._executed_cues = set()

        self.logger.info("VRPreviewController initialized (Embedded Visualizer)")

    def set_preview_window(self, window):
        """Set the preview window reference"""
        self.preview_window = window

    def start_preview(self, cues: List[Dict[str, Any]], music_file: Optional[Dict[str, Any]] = None):
        """
        Start VR preview with countdown

        Args:
            cues: List of cue dictionaries to preview
            music_file: Optional music file info dictionary
        """
        if self.is_previewing:
            self.logger.warning("Preview already in progress")
            return

        try:
            self.preview_cues = cues
            self.music_file = music_file
            self._executed_cues.clear()  # Reset executed cues tracking
            self.is_previewing = True

            # Start countdown from 10
            self.countdown_value = 10
            self.countdown_tick.emit(self.countdown_value)
            self.countdown_timer.start(1000)  # 1 second intervals

            self.logger.info(f"Starting VR preview with {len(cues)} cues (Embedded Visualizer)")
            if music_file:
                self.logger.info(f"Music: {music_file.get('name', 'Unknown')}")

        except Exception as e:
            self.logger.error(f"Failed to start preview: {e}")
            self.preview_error.emit(str(e))
            self.is_previewing = False

    def _countdown_tick(self):
        """Handle countdown timer tick"""
        self.countdown_value -= 1

        if self.countdown_value > 0:
            # Continue countdown
            self.countdown_tick.emit(self.countdown_value)
        else:
            # Countdown finished, start preview at T=0
            self.countdown_timer.stop()
            self._start_preview_at_t0()

    def _start_preview_at_t0(self):
        """
        Start preview at T=0

        This is the critical synchronization point where:
        1. Music starts playing (if selected)
        2. Cue execution timer starts
        3. Preview officially begins
        """
        try:
            # Record start time (T=0)
            self.start_time = datetime.now()

            # Emit preview started signal (this will trigger music playback)
            self.preview_started.emit()

            # Start cue execution timer (check every 10ms for precise timing)
            self.execution_timer.start(10)

            self.logger.info("Preview started at T=0 (Embedded Visualizer)")

        except Exception as e:
            self.logger.error(f"Failed to start preview at T=0: {e}")
            self.preview_error.emit(str(e))
            self.stop_preview()

    def _check_cue_execution(self):
        """
        Check if any cues should be executed based on current time

        This runs every 10ms to ensure precise timing.
        Checks ALL cues on each tick instead of sequential execution.
        """
        if not self.is_previewing or not self.start_time:
            return

        # Calculate elapsed time since T=0
        elapsed = (datetime.now() - self.start_time).total_seconds()

        # Check ALL cues to see if any should be executed now
        all_cues_executed = True
        for i, cue_row in enumerate(self.preview_cues):
            # Skip already executed cues
            if i in self._executed_cues:
                continue

            # This cue hasn't been executed yet
            all_cues_executed = False

            # Convert list to dict format
            # _data[row] = [cue_number, type, outputs, delay, execute_time, visual_properties]
            if len(cue_row) < 5:
                # Mark invalid cues as executed to skip them
                self._executed_cues.add(i)
                continue

            cue_dict = {
                'cue_id': cue_row[0],
                'type': cue_row[1],
                'outputs': cue_row[2],
                'delay': cue_row[3],
                'execute_time': cue_row[4],
                'visual_properties': cue_row[5] if len(cue_row) > 5 else None
            }

            cue_time = self._parse_time_code(cue_dict.get('execute_time', '00:00.0000'))

            # Check if it's time to execute this cue
            if elapsed >= cue_time:
                self._execute_cue(cue_dict)
                # Mark this cue as executed
                self._executed_cues.add(i)
                self.logger.debug(
                    f"Executed cue {cue_dict.get('cue_id', 'unknown')} at {elapsed:.3f}s (scheduled: {cue_time:.3f}s)")

        # Check if all cues have been executed
        if all_cues_executed:
            # Wait a bit after last cue before completing
            if elapsed > self._get_last_cue_time() + 5.0:
                self.stop_preview()

    def _execute_cue(self, cue: Dict[str, Any]):
        """
        Execute a single cue in VR preview

        Args:
            cue: Cue dictionary to execute
        """
        try:
            # Check if cue has visual properties
            if 'visual_properties' not in cue or not cue['visual_properties']:
                self.logger.debug(f"Cue {cue.get('cue_id', 'unknown')} has no visual properties, skipping")
                return

            # Get visual properties
            visual_props = cue.get('visual_properties', {})

            # Extract firework parameters
            shell_name = visual_props.get('shell_name', 'Unknown')
            launch_angle = visual_props.get('launch_angle', 0)
            primary_color = visual_props.get('primary_color', (255, 215, 0))
            star_count = visual_props.get('star_count', 100)

            # Render directly to embedded canvas
            if self.preview_window:
                self.preview_window.add_firework(
                    launch_angle=launch_angle,
                    color=primary_color,
                    star_count=star_count,
                    shell_name=shell_name
                )

                self.logger.info(f"Executed cue {cue.get('cue_id', 'unknown')} - {shell_name} at {launch_angle}°")
                self.cue_executed.emit(cue.get('cue_id', 'unknown'))
            else:
                self.logger.warning("Preview window not set, cannot render firework")

        except Exception as e:
            self.logger.error(f"Failed to execute cue: {e}")
            import traceback
            traceback.print_exc()

    def stop_preview(self):
        """Stop the VR preview"""
        if not self.is_previewing:
            return

        try:
            # Stop timers
            self.countdown_timer.stop()
            self.execution_timer.stop()

            # Reset state
            self.is_previewing = False
            self.preview_cues = []
            self.music_file = None
            self.start_time = None
            self._executed_cues.clear()

            # Emit completion signal
            self.preview_completed.emit()

            self.logger.info("VR preview stopped (Embedded Visualizer)")

        except Exception as e:
            self.logger.error(f"Error stopping preview: {e}")

    def pause_preview(self):
        """Pause the VR preview"""
        if not self.is_previewing:
            return

        try:
            self.execution_timer.stop()
            self.logger.info("VR preview paused")

        except Exception as e:
            self.logger.error(f"Error pausing preview: {e}")

    def resume_preview(self):
        """Resume the VR preview"""
        if not self.is_previewing:
            return

        try:
            self.execution_timer.start(10)
            self.logger.info("VR preview resumed")

        except Exception as e:
            self.logger.error(f"Error resuming preview: {e}")

    def _parse_time_code(self, time_code: str) -> float:
        """
        Parse time code string to seconds

        Supports two formats:
        - MM:SS.SSSS (e.g., "00:01.0000" = 1 second)
        - HH:MM:SS.SSS (e.g., "00:01:30.500" = 90.5 seconds)

        Args:
            time_code: Time code string

        Returns:
            Time in seconds
        """
        try:
            parts = time_code.split(':')

            if len(parts) == 2:
                # Format: MM:SS.SSSS
                minutes = int(parts[0])
                seconds_parts = parts[1].split('.')
                seconds = int(seconds_parts[0])
                # Handle fractional seconds (could be .0000 or .000)
                if len(seconds_parts) > 1:
                    frac_str = seconds_parts[1]
                    # Normalize to milliseconds (pad or truncate to 3 digits)
                    if len(frac_str) > 3:
                        milliseconds = int(frac_str[:3])
                    else:
                        milliseconds = int(frac_str.ljust(3, '0'))
                else:
                    milliseconds = 0

                total_seconds = minutes * 60 + seconds + milliseconds / 1000.0
                return total_seconds

            elif len(parts) == 3:
                # Format: HH:MM:SS.SSS
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds_parts = parts[2].split('.')
                seconds = int(seconds_parts[0])
                milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0

                total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
                return total_seconds
            else:
                self.logger.warning(f"Invalid time code format '{time_code}' - expected MM:SS.SSSS or HH:MM:SS.SSS")
                return 0.0
        except Exception as e:
            self.logger.error(f"Failed to parse time code '{time_code}': {e}")
            return 0.0

    def _get_last_cue_time(self) -> float:
        """Get the execution time of the last cue"""
        if not self.preview_cues:
            return 0.0

        # Handle list format from table model
        last_cue_row = self.preview_cues[-1]
        if len(last_cue_row) < 5:
            return 0.0

        execute_time = last_cue_row[4]  # execute_time is at index 4
        return self._parse_time_code(execute_time)