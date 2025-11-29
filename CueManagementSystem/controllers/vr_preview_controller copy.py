"""
VR Preview Controller
=====================

Controller for managing VR firework show previews in simulation mode.
Handles countdown, music synchronization, and cue execution timing.

This is completely separate from hardware show execution and only used
for simulation mode VR previews.

Features:
- 10-second countdown before preview starts
- Perfect music and cue synchronization (T=0)
- WebSocket communication with UE5
- Fullscreen preview window
- Optional music playback

Author: SuperNinja AI
Version: 1.0.0
License: MIT
"""
import asyncio
# asyncio not needed - using synchronous visualization bridge methods
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from PySide6.QtCore import QObject, Signal, QTimer
from controllers.visualization_bridge import VisualizationBridge
from models.cue_visual_model import EnhancedCue


class VRPreviewController(QObject):
    """
    Controller for VR preview mode

    Manages the VR preview lifecycle including countdown, music sync,
    and cue execution timing.
    """

    # Signals
    countdown_tick = Signal(int)  # Countdown number (10, 9, 8, ...)
    preview_started = Signal()  # Preview has started (T=0)
    preview_completed = Signal()  # Preview finished
    preview_error = Signal(str)  # Error occurred
    cue_executed = Signal(str)  # Cue ID executed

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        # Visualization bridge for UE5 communication
        self.visualization_bridge = VisualizationBridge()

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
        self.current_cue_index = 0

        self.logger.info("VRPreviewController initialized")

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
            self.current_cue_index = 0
            self.is_previewing = True

            # Start countdown from 10
            self.countdown_value = 10
            self.countdown_tick.emit(self.countdown_value)
            self.countdown_timer.start(1000)  # 1 second intervals

            self.logger.info(f"Starting VR preview with {len(cues)} cues")
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
            # Reset visualization
            if self.visualization_bridge.is_connected():
                self.visualization_bridge.reset()

            # Record start time (T=0)
            self.start_time = datetime.now()

            # Emit preview started signal (this will trigger music playback)
            self.preview_started.emit()

            # Start cue execution timer (check every 10ms for precise timing)
            self.execution_timer.start(10)

            self.logger.info("Preview started at T=0")

        except Exception as e:
            self.logger.error(f"Failed to start preview at T=0: {e}")
            self.preview_error.emit(str(e))
            self.stop_preview()

    def _check_cue_execution(self):
        """
        Check if any cues should be executed based on current time

        This runs every 10ms to ensure precise timing
        """
        if not self.is_previewing or not self.start_time:
            return

        # Calculate elapsed time since T=0
        elapsed = (datetime.now() - self.start_time).total_seconds()

        # Check if we've finished all cues
        if self.current_cue_index >= len(self.preview_cues):
            # Wait a bit after last cue before completing
            if elapsed > self._get_last_cue_time() + 5.0:
                self.stop_preview()
            return

        # Get current cue (list format from table model)
        cue_row = self.preview_cues[self.current_cue_index]

        # Convert list to dict format
        # _data[row] = [cue_number, type, outputs, delay, execute_time, visual_properties]
        if len(cue_row) < 5:
            self.current_cue_index += 1
            return

        cue_dict = {
            'cue_id': cue_row[0],
            'type': cue_row[1],
            'outputs': cue_row[2],
            'delay': cue_row[3],
            'execute_time': cue_row[4],
            'visual_properties': cue_row[5] if len(cue_row) > 5 else None
        }

        cue_time = self._parse_time_code(cue_dict.get('execute_time', '00:00:00.000'))

        # Check if it's time to execute this cue
        if elapsed >= cue_time:
            self._execute_cue(cue_dict)
            self.current_cue_index += 1

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

            # Send to UE5 if connected
            if self.visualization_bridge.is_connected():
                # Get visual properties
                visual_props = cue.get('visual_properties', {})

                # Prepare cue data for visualization
                cue_data = {
                    'cue_number': cue.get('cue_id', 'unknown'),
                    'shell_name': visual_props.get('shell_name', 'Unknown'),
                    'effect_type': visual_props.get('effect_type', 'peony'),
                    'colors': {
                        'primary': {
                            'r': visual_props.get('primary_color', (255, 215, 0))[0],
                            'g': visual_props.get('primary_color', (255, 215, 0))[1],
                            'b': visual_props.get('primary_color', (255, 215, 0))[2]
                        }
                    },
                    'physics': {
                        'launch_angle': visual_props.get('launch_angle', 0),
                        'velocity_multiplier': visual_props.get('velocity_multiplier', 1.0),
                        'position': {'x': 0, 'y': 0, 'z': 0}
                    },
                    'timing': {
                        'time_to_burst': visual_props.get('time_to_burst', 2.5),
                        'fade_duration': visual_props.get('fade_duration', 3.0)
                    },
                    'visual': {
                        'star_count': visual_props.get('star_count', 100)
                    },
                    'audio': {
                        'explosion_volume': visual_props.get('explosion_volume', 1.0)
                    }
                }

                # Send to visualization bridge
                self.visualization_bridge.send_launch_command(cue_data)

                self.logger.info(
                    f"Executed cue {cue.get('cue_id', 'unknown')} - {visual_props.get('shell_name', 'Unknown')} at {visual_props.get('launch_angle', 0)}°")
                self.cue_executed.emit(cue.get('cue_id', 'unknown'))
            else:
                self.logger.warning("UE5 not connected, cannot execute cue")

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

            # Stop visualization
            if self.visualization_bridge.is_connected():
                self.visualization_bridge.stop()

            # Reset state
            self.is_previewing = False
            self.preview_cues = []
            self.music_file = None
            self.start_time = None
            self.current_cue_index = 0

            # Emit completion signal
            self.preview_completed.emit()

            self.logger.info("VR preview stopped")

        except Exception as e:
            self.logger.error(f"Error stopping preview: {e}")

    def pause_preview(self):
        """Pause the VR preview"""
        if not self.is_previewing:
            return

        try:
            self.execution_timer.stop()

            if self.visualization_bridge.is_connected():
                asyncio.create_task(self.visualization_bridge.pause_show())

            self.logger.info("VR preview paused")

        except Exception as e:
            self.logger.error(f"Error pausing preview: {e}")

    def resume_preview(self):
        """Resume the VR preview"""
        if not self.is_previewing:
            return

        try:
            self.execution_timer.start(10)

            if self.visualization_bridge.is_connected():
                asyncio.create_task(self.visualization_bridge.resume_show())

            self.logger.info("VR preview resumed")

        except Exception as e:
            self.logger.error(f"Error resuming preview: {e}")

    def _parse_time_code(self, time_code: str) -> float:
        """
        Parse time code string to seconds

        Args:
            time_code: Time code string (e.g., "00:01:30.500")

        Returns:
            Time in seconds
        """
        try:
            parts = time_code.split(':')
            if len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds_parts = parts[2].split('.')
                seconds = int(seconds_parts[0])
                milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0

                total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
                return total_seconds
            else:
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

    def is_connected_to_ue5(self) -> bool:
        """Check if connected to UE5"""
        return self.visualization_bridge.is_connected()

    def get_visualization_bridge(self) -> VisualizationBridge:
        """Get the visualization bridge instance"""
        return self.visualization_bridge