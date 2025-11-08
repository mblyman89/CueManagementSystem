from PySide6.QtCore import QTimer, QObject
from typing import List, Dict


class PreviewLedAnimationController(QObject):
    """
    Special LED animation controller for preview mode.
    Similar to regular LED animations but LEDs stay on instead of blinking off.
    """

    def __init__(self, led_grid):
        super().__init__()
        self.led_grid = led_grid
        self.active_cue = None
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_state = True  # Always keep LEDs on in preview mode
        self.current_output_index = 0
        self.active_outputs = {}  # {output: timer}
        self.outputs = []
        self.delay = 0

    def start_animation(self, cue_data):
        """Start preview animation for selected cue"""
        self.stop_animation()
        self.active_cue = cue_data

        if not cue_data:
            return

        cue_type = cue_data[1]

        # Parse outputs, handling potential empty strings or invalid formats
        try:
            if cue_data[2]:
                self.outputs = [int(x.strip()) for x in cue_data[2].split(',') if x.strip().isdigit()]
            else:
                self.outputs = []
        except (ValueError, IndexError):
            self.outputs = []

        # Get delay value
        try:
            self.delay = float(cue_data[3]) if len(cue_data) > 3 else 0
        except (ValueError, TypeError):
            self.delay = 0

        if "SHOT" in cue_type:
            # For shot types in preview mode, just activate all at once and keep on
            self._preview_shot_animation()
        else:
            # For run types, use the specified delay interval but keep LEDs on
            self.animation_timer.setInterval(int(self.delay * 1000))
            self.current_output_index = 0
            self.active_outputs = {}
            self._preview_run_animation()
            self.animation_timer.start()

    def stop_animation(self):
        """Stop current animation"""
        self.animation_timer.stop()

        # Stop all active timers
        for timer in self.active_outputs.values():
            timer.stop()
        self.active_outputs.clear()

        # Reset state
        self.active_cue = None
        self.current_output_index = 0

        # Force an update of the LED grid
        self.led_grid.update()

    def update_animation(self):
        """Update animation frame based on cue type"""
        if not self.active_cue:
            return

        if "RUN" in self.active_cue[1]:
            self._preview_run_animation()

    def _preview_shot_animation(self):
        """
        Preview mode for SHOT types - activate all LEDs at once and keep on
        """
        cue_type = self.active_cue[1]
        for output in self.outputs:
            if output in self.led_grid.leds:
                # In preview mode, always set LEDs to active state
                self.led_grid.leds[output].setState(cue_type)

    def _preview_run_animation(self):
        """
        Preview mode for RUN types - activate LEDs sequentially with delay but keep on
        """
        # Reset if we've reached the end
        if self.current_output_index >= len(self.outputs):
            self.animation_timer.stop()
            return

        if "DOUBLE RUN" in self.active_cue[1]:
            # Activate pairs
            outputs = []
            for i in range(2):
                idx = self.current_output_index + i
                if idx < len(self.outputs):
                    outputs.append(self.outputs[idx])

            for output in outputs:
                self._activate_output(output)

            self.current_output_index += 2
        else:
            # Activate single
            output = self.outputs[self.current_output_index]
            self._activate_output(output)
            self.current_output_index += 1

    def _activate_output(self, output):
        """
        Activate an output and keep it on for preview mode
        """
        if output in self.led_grid.leds:
            self.led_grid.leds[output].setState(self.active_cue[1])

    def set_led_state_instant(self, cue):
        """
        Set LED state immediately without animation
        Used during scrubbing for instant feedback

        Args:
            cue: Cue data to display (format: [cue_number, type, outputs, delay, execute_time])
        """
        cue_type = cue[1]  # Type (e.g., "SINGLE SHOT", "DOUBLE RUN")
        outputs = cue[2]  # Outputs string (e.g., "1,2,3")

        # Parse outputs
        output_list = []
        if isinstance(outputs, str):
            output_list = [int(x.strip()) for x in outputs.split(',') if x.strip()]
        elif isinstance(outputs, (list, tuple)):
            output_list = [int(x) for x in outputs]

        # Set LED states directly without animation
        for output in output_list:
            if output in self.led_grid.leds:
                led = self.led_grid.leds[output]
                led.setState(cue_type)
                led.update()  # Force immediate repaint

    def clear_all_leds(self):
        """
        Clear all LED states
        Used before restoring state at a specific time
        """
        for led_number in self.led_grid.leds:
            self.led_grid.leds[led_number].setState(None)
            self.led_grid.leds[led_number].update()  # Force immediate repaint
