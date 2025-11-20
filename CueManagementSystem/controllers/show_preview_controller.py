"""
Show Preview Controller
=======================

Controller for managing the preview playback of complete firework shows on the LED panel.
This controller handles precise timing, cue sequencing, and synchronization with the
preview animation system to provide accurate visual representation of show execution.

Features:
- Sequential cue playback with precise timing
- Play, pause, resume, and stop controls
- Time-based seeking and scrubbing
- Real-time time updates (10Hz refresh rate)
- Cue triggering at exact execution times
- Integration with preview LED animation controller
- Active cue tracking at any given time
- Total show duration calculation
- Music file synchronization support
- Automatic LED state clearing on start
- Pause time compensation for accurate timing

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

from PySide6.QtCore import QObject, QTimer, Signal
from typing import List, Dict, Any
import time
from views.led_panel.preview_led_animations import PreviewLedAnimationController


class ShowPreviewController(QObject):
    """
    Controller for previewing a complete show on the LED panel
    Handles timing and playback of cues in order
    """

    # Signals
    preview_started = Signal()
    preview_ended = Signal()
    cue_triggered = Signal(object)  # Emits cue data when it's time to execute
    time_updated = Signal(float)  # Emits current show time in seconds

    def __init__(self, led_panel=None):
        super().__init__()
        self.led_panel = led_panel
        self.cues = []
        self.sorted_cues = []

        # Create preview animation controller if we have an LED panel
        self.preview_animation_controller = None
        if self.led_panel:
            self.preview_animation_controller = PreviewLedAnimationController(self.led_panel)

        # Timing control
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_preview)
        self.timer.setInterval(100)  # Update at 10Hz (100ms)

        # Playback state
        self.is_playing = False
        self.is_paused = False
        self.start_time = 0
        self.elapsed_time = 0
        self.pause_time = 0
        self.current_cue_index = 0

    def load_cues(self, cues: List[Any]):
        """
        Load cues for preview playback

        Args:
            cues: List of cue data from the cue table
        """
        self.cues = cues
        if not cues:
            return

        # Sort cues by execution time
        self.sorted_cues = sorted(self.cues, key=lambda x: self._time_to_seconds(x[4]))
        self.current_cue_index = 0

    def start_preview(self):
        """Start preview playback of all cues"""
        if not self.sorted_cues:
            return False

        # Reset state
        if not self.is_paused:
            self.current_cue_index = 0
            self.elapsed_time = 0

            # Clear all LEDs before starting
            if self.led_panel:
                # Stop any regular animations
                self.led_panel.animation_controller.stop_animation()
                # Also stop any preview animations
                if self.preview_animation_controller:
                    self.preview_animation_controller.stop_animation()
                # Clear all LEDs
                for led_number in self.led_panel.leds:
                    self.led_panel.leds[led_number].setState(None)

        # Set starting time
        self.start_time = time.time()
        if self.is_paused:
            # Adjust for time spent paused
            self.start_time -= self.elapsed_time
            self.is_paused = False

        # Notify LED panel manager of preview mode
        if hasattr(self.led_panel, 'set_preview_mode'):
            self.led_panel.set_preview_mode(True)

        # Start timer
        self.is_playing = True
        self.timer.start()
        self.preview_started.emit()

        return True

    def stop_preview(self):
        """Stop preview and reset state"""
        self.timer.stop()
        self.is_playing = False
        self.is_paused = False
        self.elapsed_time = 0
        self.current_cue_index = 0

        # Stop animations and restore LED panel to reflect all cues
        if self.led_panel:
            # Stop regular animations
            self.led_panel.animation_controller.stop_animation()
            # Also stop preview animations
            if self.preview_animation_controller:
                self.preview_animation_controller.stop_animation()

            # Clear all LEDs first
            for led_number in self.led_panel.leds:
                self.led_panel.leds[led_number].setState(None)

            # Restore the LED panel with all cues from the cue table
            if hasattr(self.led_panel, 'updateFromCueData') and self.cues:
                # Use the original cues (not sorted) to update the LED panel
                self.led_panel.updateFromCueData(self.cues, force_refresh=True)

        # Notify LED panel manager that preview mode ended
        if hasattr(self.led_panel, 'set_preview_mode'):
            self.led_panel.set_preview_mode(False)

        self.preview_ended.emit()

    def pause_preview(self):
        """Pause the preview"""
        if not self.is_playing:
            return

        self.timer.stop()
        self.is_paused = True
        self.is_playing = False
        self.pause_time = time.time()

        # Store the elapsed time at pause
        self.elapsed_time = self.pause_time - self.start_time

    def resume_preview(self):
        """Resume the preview from pause"""
        if not self.is_paused:
            return

        self.start_preview()

    def set_music_file(self, file_path):
        """
        Set the music file path for the preview

        Args:
            file_path: Path to the music file
        """
        self.music_file_path = file_path

    def _update_preview(self):
        """Update the preview state based on elapsed time"""
        if not self.is_playing or not self.sorted_cues:
            return

        # Calculate current elapsed time
        current_time = time.time()
        self.elapsed_time = current_time - self.start_time

        # Emit current time for UI updates
        self.time_updated.emit(self.elapsed_time)

        # Check if we've reached the end of all cues
        if self.current_cue_index >= len(self.sorted_cues):
            self.stop_preview()
            return

        # Check if it's time to trigger the next cue
        while (self.current_cue_index < len(self.sorted_cues)):
            next_cue = self.sorted_cues[self.current_cue_index]
            next_cue_time = self._time_to_seconds(next_cue[4])

            if self.elapsed_time >= next_cue_time:
                # Time to trigger this cue
                self._trigger_cue(next_cue)
                self.current_cue_index += 1
            else:
                # Not time for this cue yet
                break

    def _trigger_cue(self, cue):
        """
        Trigger a cue for display on the LED panel

        Args:
            cue: Cue data to trigger
        """
        self.cue_triggered.emit(cue)

        # If we have access to the LED panel and preview animation controller, show the animation
        if self.led_panel and self.preview_animation_controller:
            # Use the preview animation controller instead of standard handle_cue_selection
            self.preview_animation_controller.start_animation(cue)

    def seek_to_time(self, target_time: float):
        """
        Seek preview to specific time
        Updates elapsed time and cue index to match target time

        Args:
            target_time: Time in seconds to seek to
        """
        # Update elapsed time
        self.elapsed_time = target_time

        # Find appropriate cue index for this time
        # This determines which cue should be triggered next
        self.current_cue_index = 0
        for i, cue in enumerate(self.sorted_cues):
            cue_time = self._time_to_seconds(cue[4])
            if cue_time <= target_time:
                self.current_cue_index = i + 1
            else:
                break

        # Adjust start time to maintain correct elapsed time
        # This ensures the timer continues correctly from this point
        self.start_time = time.time() - self.elapsed_time

        # Emit time update
        self.time_updated.emit(self.elapsed_time)

    def get_active_cues_at_time(self, time: float) -> List[Any]:
        """
        Get all cues that should be active (LEDs lit) at given time

        In preview mode, LEDs stay lit after being triggered, so any cue
        with execution_time <= time should be active.

        Args:
            time: Time in seconds

        Returns:
            List of cues that should be active
        """
        active_cues = []
        for cue in self.sorted_cues:
            cue_time = self._time_to_seconds(cue[4])
            if cue_time <= time:
                active_cues.append(cue)
            else:
                # Since cues are sorted, we can break early
                break
        return active_cues

    def get_total_duration(self) -> float:
        """
        Get total duration of the show based on last cue time

        Returns:
            Duration in seconds, or 0.0 if no cues
        """
        if not self.sorted_cues:
            return 0.0

        last_cue = self.sorted_cues[-1]
        return self._time_to_seconds(last_cue[4])

    def _time_to_seconds(self, time_str):
        """
        Convert time string (MM:SS.SS) to seconds

        Args:
            time_str: Time string to convert

        Returns:
            Time in seconds as float
        """
        try:
            minutes, seconds = time_str.split(':')
            return int(minutes) * 60 + float(seconds)
        except (ValueError, TypeError):
            return 0.0
