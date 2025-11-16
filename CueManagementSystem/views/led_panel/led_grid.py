"""
Traditional LED Grid Widget
===========================

Custom Qt widget displaying a traditional grid of LEDs with state management and animations.

Features:
- 40x25 LED grid layout
- Sequential LED numbering
- LED state management
- Animation support
- Cue data integration
- Compact display design
- Custom painting

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

from PySide6.QtWidgets import QWidget, QGridLayout, QSizePolicy
from PySide6.QtCore import Qt, QSize
from views.led_panel.led_widget import LedWidget
from views.led_panel.led_animations import LedAnimationController

class LedGrid(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = 40
        self.cols = 25
        self.leds = {}
        self.animation_controller = LedAnimationController(self)
        self.setup_ui()

        # Set size policies
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Set minimum size to prevent collapse
        self.setMinimumSize(500, 400)

    def setup_ui(self):
        # Create main layout
        layout = QGridLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        # Create LED grid
        led_number = 1
        for row in range(self.rows):
            for col in range(self.cols):
                led = LedWidget(led_number)
                led.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                layout.addWidget(led, row, col)
                self.leds[led_number] = led
                led_number += 1

        # Set stretch factors
        for i in range(self.cols):
            layout.setColumnStretch(i, 1)
        for i in range(self.rows):
            layout.setRowStretch(i, 1)

        self.setLayout(layout)

        # Style the LED panel
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a2e;
                padding: 0px;
                margin: 0px;
            }
        """)

    def sizeHint(self):
        """Provide a reasonable default size"""
        return QSize(800, 600)

    def minimumSizeHint(self):
        """Provide a reasonable minimum size"""
        return QSize(500, 400)

    def resizeEvent(self, event):
        """Handle resize events to maintain LED aspect ratio"""
        super().resizeEvent(event)
        width = event.size().width() // self.cols
        height = event.size().height() // self.rows
        size = min(width, height)

        # Update minimum size for LEDs
        for led in self.leds.values():
            led.setMinimumSize(size, size)

    def updateFromCueData(self, cue_data, force_refresh=False):
        """Update LEDs based on cue data from table
        
        Args:
            cue_data: List of cues from the table model
            force_refresh: Force complete refresh of all LEDs (default: False)
        """
        # Reset all LEDs to inactive state - ensure ALL LEDs are properly cleared
        for led_number in self.leds:
            self.leds[led_number].setState(None)
            self.leds[led_number].is_active = False
            self.leds[led_number].cue_type = None
            
        # Force all LEDs to be redrawn
        self.update()
    
        # Update LEDs based on cue data
        for cue in cue_data:
            cue_type = cue[1]  # TYPE is still at index 1
            outputs = cue[2]  # OUTPUTS is now at index 2 (was 3)
    
            # Parse outputs string into list of numbers
            try:
                # Handle different output formats
                output_list = []
                if ";" in outputs:  # Handle double run format with semicolons
                    for pair in outputs.split(";"):
                        for value in pair.split(","):
                            if value.strip() and value.strip().isdigit():
                                output_list.append(int(value.strip()))
                else:  # Handle regular comma-separated format
                    output_list = [int(x.strip()) for x in outputs.split(',') if x.strip().isdigit()]
                
                # Set LEDs active based on outputs
                for output in output_list:
                    if output in self.leds:
                        self.leds[output].setState(cue_type)
            except (ValueError, AttributeError) as e:
                print(f"Error processing outputs: {e}")
                continue

    def handle_cue_selection(self, cue_data=None):
        """Handle cue selection from table"""
        if cue_data:
            self.animation_controller.start_animation(cue_data)
        else:
            self.animation_controller.stop_animation()
            
    def reset_all_leds(self):
        """Reset all LEDs to inactive state"""
        # Stop any active animations
        self.animation_controller.stop_animation()
        
        # Reset all LEDs
        for led_number in self.leds:
            self.leds[led_number].setState(None)
            self.leds[led_number].is_active = False
            self.leds[led_number].cue_type = None
            
        # Force update
        self.update()