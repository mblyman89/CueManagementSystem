"""
Preview State Manager
Manages synchronization between audio playback, LED panel state, and timeline during preview.
Handles real-time scrubbing with optimized LED state updates.
"""

from PySide6.QtCore import QObject, Signal
from typing import List, Any, Optional
import time


class PreviewStateManager(QObject):
    """
    Manages the state synchronization between audio, LEDs, and timeline during preview.
    Coordinates seeking, scrubbing, and state restoration.
    """

    # Signals
    state_restored = Signal()  # Emitted when LED state has been restored after seeking

    def __init__(self, preview_controller, music_manager, led_panel):
        """
        Initialize the preview state manager

        Args:
            preview_controller: ShowPreviewController instance
            music_manager: MusicManager instance
            led_panel: LED panel widget instance
        """
        super().__init__()

        self.preview_controller = preview_controller
        self.music_manager = music_manager
        self.led_panel = led_panel

        # Scrubbing state
        self.is_scrubbing = False
        self.was_playing_before_scrub = False

        # Performance optimization - throttle updates during scrubbing
        self.last_led_update = 0
        self.last_audio_update = 0
        self.led_update_interval = 0.05  # Update LEDs max 20 times per second
        self.audio_update_interval = 0.1  # Update audio max 10 times per second

    def start_scrubbing(self):
        """
        Called when user starts dragging the playhead
        Pauses playback and prepares for real-time updates
        """
        self.is_scrubbing = True
        self.was_playing_before_scrub = self.preview_controller.is_playing

        # Pause playback during scrubbing
        if self.was_playing_before_scrub:
            self.preview_controller.pause_preview()
            self.music_manager.pause_preview()

        # Reset throttle timers
        self.last_led_update = 0
        self.last_audio_update = 0

    def update_scrubbing_position(self, target_time: float):
        """
        Called continuously as user drags the playhead
        Updates LED state and audio position with throttling for performance

        Args:
            target_time: Target time in seconds
        """
        if not self.is_scrubbing:
            return

        current_time = time.time()

        # Always update preview controller time (lightweight)
        self.preview_controller.elapsed_time = target_time

        # Throttle LED updates (expensive operation)
        if current_time - self.last_led_update >= self.led_update_interval:
            self.restore_led_state_at_time(target_time, instant=True)
            self.last_led_update = current_time

        # Throttle audio updates (can cause audio glitches if too frequent)
        if current_time - self.last_audio_update >= self.audio_update_interval:
            self.music_manager.set_playback_position(int(target_time * 1000))
            self.last_audio_update = current_time

    def end_scrubbing(self, final_time: float):
        """
        Called when user releases the playhead
        Finalizes position and resumes playback if needed

        Args:
            final_time: Final time position in seconds
        """
        self.is_scrubbing = False

        # Perform final seek to exact position
        self.seek_to_time(final_time, is_final=True)

        # Resume playback if it was playing before scrubbing
        if self.was_playing_before_scrub:
            self.preview_controller.resume_preview()
            self.music_manager.resume_preview()

        self.state_restored.emit()

    def seek_to_time(self, target_time: float, is_final: bool = False):
        """
        Seek to a specific time in the preview
        Updates preview controller, audio position, and LED state

        Args:
            target_time: Time in seconds to seek to
            is_final: If True, this is a final seek (not during scrubbing)
        """
        # Update preview controller state
        self.preview_controller.seek_to_time(target_time)

        # Seek audio to position
        self.music_manager.set_playback_position(int(target_time * 1000))

        # Restore LED state
        self.restore_led_state_at_time(target_time, instant=True)

        if is_final:
            self.state_restored.emit()

    def restore_led_state_at_time(self, time: float, instant: bool = True):
        """
        Restore LED panel to correct state for given time
        Determines which cues should be active and updates LEDs accordingly

        Args:
            time: Time in seconds
            instant: If True, skip animations (for scrubbing)
        """
        # Get preview animation controller
        preview_anim_controller = self.preview_controller.preview_animation_controller
        if not preview_anim_controller:
            return

        # Clear all LEDs first
        preview_anim_controller.clear_all_leds()

        # Get all cues that should be active at this time
        active_cues = self.preview_controller.get_active_cues_at_time(time)

        # Light up LEDs for active cues
        for cue in active_cues:
            if instant:
                # Set state directly without animation (for scrubbing)
                preview_anim_controller.set_led_state_instant(cue)
            else:
                # Use normal animation (for regular playback)
                preview_anim_controller.start_animation(cue)

    def calculate_active_cues_at_time(self, time: float) -> List[Any]:
        """
        Calculate which cues should be active at given time
        This is a convenience method that delegates to preview controller

        Args:
            time: Time in seconds

        Returns:
            List of cues that should be active
        """
        return self.preview_controller.get_active_cues_at_time(time)

    def get_total_duration(self) -> float:
        """
        Get total duration of the show

        Returns:
            Duration in seconds
        """
        return self.preview_controller.get_total_duration()

    def reset(self):
        """Reset the state manager"""
        self.is_scrubbing = False
        self.was_playing_before_scrub = False
        self.last_led_update = 0
        self.last_audio_update = 0