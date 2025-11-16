"""
LED Animation Controller
========================

Manages LED animations based on predefined cues including start, stop, and update operations.

Features:
- Cue-based animation management
- SHOT cue animations
- RUN cue animations
- Animation start/stop control
- LED state updates
- Timing-based animations
- PySide6 integration

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

from PySide6.QtCore import QTimer, QObject
from typing import List, Dict


class LedAnimationController(QObject):
    def __init__(self, led_grid):
        super().__init__()
        self.led_grid = led_grid
        self.active_cue = None
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)  # Changed to public method
        self.animation_state = False
        self.current_output_index = 0
        self.active_outputs = {}  # {output: timer}

    def start_animation(self, cue_data):
        """Start animation for selected cue"""
        self.stop_animation()
        self.active_cue = cue_data

        cue_type = cue_data[1]
        self.outputs = [int(x.strip()) for x in cue_data[2].split(',')]
        self.delay = float(cue_data[3])

        if "SHOT" in cue_type:
            # For shot types, blink at 1 second intervals
            self.animation_timer.setInterval(1000)
            self.animation_state = True
            self._update_shot_animation()
        else:
            # For run types, trigger at the specified delay interval
            self.animation_timer.setInterval(int(self.delay * 1000))
            self.current_output_index = 0
            self.active_outputs = {}
            self._update_run_animation()

        self.animation_timer.start()

    def stop_animation(self):
        """Stop current animation and reset LEDs to static state"""
        self.animation_timer.stop()

        # Stop all active timers
        for timer in self.active_outputs.values():
            timer.stop()
        self.active_outputs.clear()
    
        # Preserve active state for all currently active LEDs
        if self.active_cue:
            cue_type = self.active_cue[1]
            for output in self.outputs:
                if output in self.led_grid.leds:
                    self.led_grid.leds[output].setState(cue_type)
    
        # Reset state
        self.active_cue = None
        self.current_output_index = 0
        self.animation_state = False
        
        # Force an update of the LED grid
        self.led_grid.update()

    def update_animation(self):  # Public method for timer connection
        """Update animation frame based on cue type"""
        if not self.active_cue:
            return

        if "SHOT" in self.active_cue[1]:
            self._update_shot_animation()
        else:
            self._update_run_animation()

    def _update_shot_animation(self):
        """Handle blinking animation for SHOT types"""
        self.animation_state = not self.animation_state
        for output in self.outputs:
            if self.animation_state:
                self.led_grid.leds[output].setState(self.active_cue[1])
            else:
                self.led_grid.leds[output].setState(None)

    def _update_run_animation(self):
        """Handle cascading animation for RUN types"""
        # Clear any finished outputs
        for output in list(self.active_outputs.keys()):
            if not self.active_outputs[output].isActive():
                self.led_grid.leds[output].setState(None)
                del self.active_outputs[output]

        # Reset if we've reached the end
        if self.current_output_index >= len(self.outputs):
            self.current_output_index = 0
            return  # Wait for the next timer interval

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
        """Activate an output with duration based on cue type"""
        self.led_grid.leds[output].setState(self.active_cue[1])
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self._cleanup_output(output))
        
        # Use the delay value for RUN types, 1 second for SHOT types
        if "RUN" in self.active_cue[1]:
            # Use the configured delay for run types
            timer.start(int(self.delay * 1000))
        else:
            # Keep using 1 second for shot types
            timer.start(1000)
            
        self.active_outputs[output] = timer

    def _cleanup_output(self, output):
        """Clean up a specific output"""
        if output in self.active_outputs:
            self.led_grid.leds[output].setState(None)
            del self.active_outputs[output]