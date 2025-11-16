"""
Application Button Bar
======================

A horizontal scrollable button bar widget that provides application-wide controls and mode-specific button configurations.

Features:
- Horizontal scrollable layout
- Dynamic button state management
- Mode-specific button visibility
- Signal emission on button clicks
- Custom styling and appearance
- Button enable/disable control
- Scroll area integration

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

from PySide6.QtWidgets import (QWidget, QScrollArea, QHBoxLayout,
                               QSizePolicy)
from PySide6.QtCore import Qt, Signal, QObject

from views.button_bar.button_widget import ButtonWidget


class ButtonBar(QScrollArea):
    """
    Button bar for application controls

    Features:
    - Horizontal scrollable bar of buttons
    - Manages button states and interactions
    - Emits signals when buttons are clicked
    """

    # Define signals for button clicks
    enable_outputs = Signal()
    arm_outputs = Signal()
    execute_cue_clicked = Signal()
    stop_clicked = Signal()
    pause_clicked = Signal()
    resume_clicked = Signal()
    execute_all_clicked = Signal()
    mode_clicked = Signal()
    led_panel_clicked = Signal()  # New signal for LED panel button
    create_cue_clicked = Signal()
    edit_cue_clicked = Signal()
    delete_cue_clicked = Signal()
    delete_all_clicked = Signal()
    import_music_clicked = Signal()
    generate_show_clicked = Signal()
    load_show_clicked = Signal()
    import_show_clicked = Signal()
    export_show_clicked = Signal()
    save_show_clicked = Signal()
    exit_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setFixedHeight(100)

        # Store buttons in a dictionary for easy access
        self.buttons = {}

        # Initialize UI
        self.setup_ui()

        # Initialize buttons
        self.initialize_playback_buttons()

    def setup_ui(self):
        """Set up the button bar UI"""
        # Button container
        button_container = QWidget()
        button_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(10, 10, 10, 10)
        button_layout.setSpacing(10)

        # Button definitions with colors
        button_defs = [
            ("ENABLE\n OUTPUTS", "#1e5631"),
            ("ARM\n OUTPUTS", "#1e5631"),
            ("EXECUTE\n CUE", "#1e5631"),
            ("STOP", "#8b0000"),
            ("PAUSE", "#1e3d6e"),
            ("RESUME", "#1e3d6e"),
            ("EXECUTE\n SHOW", "#1e5631"),
            ("MODE", "#cc5500"),
            ("LED\n PANEL", "#333333"),
            ("CREATE\n CUE", "#333333"),
            ("EDIT\n CUE", "#333333"),
            ("DELETE\n CUE", "#333333"),
            ("DELETE\n ALL", "#333333"),
            ("IMPORT\n MUSIC", "#333333"),
            ("GENERATE\n SHOW", "#333333"),
            ("LOAD\n SHOW", "#333333"),
            ("IMPORT\n SHOW", "#333333"),
            ("EXPORT\n SHOW", "#333333"),
            ("SAVE\n SHOW", "#333333"),
            ("EXIT", "#8b0000")
        ]

        # Create buttons
        for text, color in button_defs:
            button = ButtonWidget(text, color)
            button_layout.addWidget(button)

            # Store button reference with simplified name
            self.buttons[text.replace("\n", "").strip()] = button

            # Connect button signals
            self.connect_button_signals(button, text.replace("\n", "").strip())

        # Set the container as the scroll area's widget
        self.setWidget(button_container)

    def connect_button_signals(self, button, button_name):
        """Connect button signals to corresponding class signals"""
        # Special handling for toggle buttons
        if button_name == "ENABLE OUTPUTS":
            button.clicked.connect(self.toggle_enable_outputs)
            return
        elif button_name == "ARM OUTPUTS":
            button.clicked.connect(self.toggle_arm_outputs)
            return

        # Standard signal mapping for other buttons
        signal_map = {
            "EXECUTE CUE": self.execute_cue_clicked,
            "EXECUTE SHOW": self.execute_all_clicked,
            "PREVIEW SHOW": self.execute_all_clicked,
            "STOP": self.stop_clicked,
            "ABORT": self.stop_clicked,
            "PAUSE": self.pause_clicked,
            "RESUME": self.resume_clicked,
            "MODE": self.mode_clicked,
            "LED PANEL": self.led_panel_clicked,
            "CREATE CUE": self.create_cue_clicked,
            "EDIT CUE": self.edit_cue_clicked,
            "DELETE CUE": self.delete_cue_clicked,
            "DELETE ALL": self.delete_all_clicked,
            "IMPORT MUSIC": self.import_music_clicked,
            "GENERATE SHOW": self.generate_show_clicked,
            "LOAD SHOW": self.load_show_clicked,
            "IMPORT SHOW": self.import_show_clicked,
            "EXPORT SHOW": self.export_show_clicked,
            "SAVE SHOW": self.save_show_clicked,
            "EXIT": self.exit_clicked
        }

        if button_name in signal_map:
            button.clicked.connect(signal_map[button_name].emit)

    def toggle_enable_outputs(self):
        """Toggle the selected state of the ENABLE OUTPUTS button"""
        import time
        timestamp = time.time()
        print(f"ButtonBar: toggle_enable_outputs called at {timestamp}")
        if "ENABLE OUTPUTS" in self.buttons:
            print(f"ButtonBar: emitting enable_outputs signal at {timestamp}")
            # Just emit the signal - let the backend handle state and UI will be updated after
            self.enable_outputs.emit()
        else:
            print("ButtonBar: ENABLE OUTPUTS button not found")

    def toggle_arm_outputs(self):
        """Toggle the selected state of the ARM OUTPUTS button"""
        if "ARM OUTPUTS" in self.buttons:
            print("ButtonBar: toggle_arm_outputs called, emitting signal")
            # Just emit the signal - let the backend handle state and UI will be updated after
            self.arm_outputs.emit()
        else:
            print("ButtonBar: ARM OUTPUTS button not found")

    def update_enable_outputs_state(self, enabled_state):
        """Update the enable outputs button to reflect the actual backend state"""
        print(f"ButtonBar: update_enable_outputs_state called with state: {enabled_state}")
        if "ENABLE OUTPUTS" in self.buttons:
            button = self.buttons["ENABLE OUTPUTS"]
            print(f"ButtonBar: Setting button selected state to: {enabled_state}")
            button.set_selected(enabled_state)
            if enabled_state:
                print("ButtonBar: Setting button text to 'DISABLE OUTPUTS'")
                button.setText("DISABLE\n OUTPUTS")
            else:
                print("ButtonBar: Setting button text to 'ENABLE OUTPUTS'")
                button.setText("ENABLE\n OUTPUTS")
        else:
            print("ButtonBar: ENABLE OUTPUTS button not found in buttons dict")

    def update_arm_outputs_state(self, armed_state):
        """Update the arm outputs button to reflect the actual backend state"""
        if "ARM OUTPUTS" in self.buttons:
            button = self.buttons["ARM OUTPUTS"]
            button.set_selected(armed_state)
            if armed_state:
                button.setText("DISARM\n OUTPUTS")
            else:
                button.setText("ARM\n OUTPUTS")

    def initialize_playback_buttons(self):
        """Initialize playback control buttons to correct states"""
        # Disable control buttons initially
        control_buttons = ["STOP", "ABORT", "PAUSE", "RESUME"]
        for button_name in control_buttons:
            if button_name in self.buttons:
                self.buttons[button_name].set_active(False)

        # Initialize toggle buttons to unselected state
        toggle_buttons = ["ENABLE OUTPUTS", "ARM OUTPUTS"]
        for button_name in toggle_buttons:
            if button_name in self.buttons:
                self.buttons[button_name].set_selected(False)
                # Ensure correct text for unselected state
                if button_name == "ENABLE OUTPUTS":
                    self.buttons[button_name].setText("ENABLE\n OUTPUTS")
                elif button_name == "ARM OUTPUTS":
                    self.buttons[button_name].setText("ARM\n OUTPUTS")

        # Update buttons in the UI
        self.update_playback_button_states()

    def update_playback_button_states(self):
        """Update button states based on current playback state"""
        # This method can be called whenever button states need to be refreshed
        # It ensures the buttons are visually and functionally in sync with their active state
        control_buttons = ["STOP", "ABORT", "PAUSE", "RESUME"]
        for button_name in control_buttons:
            if button_name in self.buttons:
                button = self.buttons[button_name]
                # Use get_active_state() method instead of is_active()
                if hasattr(button, 'get_active_state'):
                    is_active = button.get_active_state()
                    # Set proper cursor and visual state
                    button.set_active(is_active)

    def handle_preview_started(self):
        """Update button states when preview starts"""
        # Disable execute buttons
        self.buttons["EXECUTE SHOW"].set_active(False)

        # Enable control buttons
        if "STOP" in self.buttons:
            self.buttons["STOP"].set_active(True)
        if "ABORT" in self.buttons:
            self.buttons["ABORT"].set_active(True)
        self.buttons["PAUSE"].set_active(True)
        self.buttons["RESUME"].set_active(False)

    def handle_preview_ended(self):
        """Update button states when preview ends"""
        # Enable execute buttons
        self.buttons["EXECUTE SHOW"].set_active(True)

        # Disable control buttons
        if "STOP" in self.buttons:
            self.buttons["STOP"].set_active(False)
        if "ABORT" in self.buttons:
            self.buttons["ABORT"].set_active(False)
        self.buttons["PAUSE"].set_active(False)
        self.buttons["RESUME"].set_active(False)

    def handle_preview_paused(self):
        """Update button states when preview is paused"""
        self.buttons["PAUSE"].set_active(False)
        self.buttons["RESUME"].set_active(True)

    def handle_preview_resumed(self):
        """Update button states when preview is resumed"""
        self.buttons["PAUSE"].set_active(True)
        self.buttons["RESUME"].set_active(False)

    def replace_button(self, button_name, new_button):
        """Replace an existing button with a new one while preserving connections"""
        if button_name in self.buttons:
            old_button = self.buttons[button_name]

            # Find the old button's parent and position in layout
            parent_widget = old_button.parent()
            parent_layout = parent_widget.layout()

            # Find the index of the old button in the layout
            index = -1
            for i in range(parent_layout.count()):
                if parent_layout.itemAt(i).widget() is old_button:
                    index = i
                    break

            if index >= 0:
                # Remove the old button from layout
                parent_layout.removeWidget(old_button)
                old_button.deleteLater()

                # Add the new button at the same position
                parent_layout.insertWidget(index, new_button)

                # Store reference to the new button
                self.buttons[button_name] = new_button

                # Connect the new button to the signal
                self.connect_button_signals(new_button, button_name)

    def update_led_panel_button(self, current_view):
        """Update LED PANEL button text based on current view"""
        if "LED PANEL" in self.buttons:
            button = self.buttons["LED PANEL"]
            if current_view == "traditional":
                button.setText("LED\nSTANDARD")
            else:
                button.setText("LED\nGROUPED")

    def update_mode_buttons(self, is_simulation_mode):
        """Update buttons based on current system mode"""
        # Update MODE button
        if "MODE" in self.buttons:
            if is_simulation_mode:
                # For simulation mode - orange color
                new_button = ButtonWidget("SIMULATION\nMODE", "#cc5500")
                self.replace_button("MODE", new_button)

                # Disable hardware-only buttons in simulation mode
                hardware_buttons = ["EXECUTE CUE", "ENABLE OUTPUTS", "ARM OUTPUTS"]
                for button_name in hardware_buttons:
                    if button_name in self.buttons:
                        self.buttons[button_name].set_active(False)
                        self.buttons[button_name].set_selected(False)
                        # Reset text to default state
                        if button_name == "ENABLE OUTPUTS":
                            self.buttons[button_name].setText("ENABLE\n OUTPUTS")
                        elif button_name == "ARM OUTPUTS":
                            self.buttons[button_name].setText("ARM\n OUTPUTS")

                # Ensure STOP button is present and properly configured
                if "STOP" in self.buttons:
                    new_button = ButtonWidget("STOP", "#8b0000")
                    self.replace_button("STOP", new_button)
                    self.buttons["STOP"].set_active(False)  # Ensure it starts inactive

            else:
                # For hardware mode - purple color
                new_button = ButtonWidget("HARDWARE\nMODE", "#800080")
                self.replace_button("MODE", new_button)

                # Enable EXECUTE CUE button in hardware mode
                if "EXECUTE CUE" in self.buttons:
                    self.buttons["EXECUTE CUE"].set_active(True)

                # Enable ENABLE OUTPUTS and ARM OUTPUTS buttons in hardware mode
                # and reset their selected state
                if "ENABLE OUTPUTS" in self.buttons:
                    self.buttons["ENABLE OUTPUTS"].set_active(True)
                    self.buttons["ENABLE OUTPUTS"].set_selected(False)
                    self.buttons["ENABLE OUTPUTS"].setText("ENABLE\n OUTPUTS")

                if "ARM OUTPUTS" in self.buttons:
                    self.buttons["ARM OUTPUTS"].set_active(True)
                    self.buttons["ARM OUTPUTS"].set_selected(False)
                    self.buttons["ARM OUTPUTS"].setText("ARM\n OUTPUTS")

                # Replace STOP with ABORT button
                if "STOP" in self.buttons:
                    new_button = ButtonWidget("ABORT", "#8b0000")  # Same red color as STOP
                    self.replace_button("STOP", new_button)
                    self.buttons["STOP"].set_active(False)  # Ensure it starts inactive
                    # Initialize the new ABORT button's state
                    self.initialize_playback_buttons()
                    self.update_playback_button_states()

        # Update EXECUTE ALL button - same green color (#1e5631) for both modes
        if "EXECUTE SHOW" in self.buttons:
            if is_simulation_mode:
                # In simulation mode, change text to PREVIEW
                new_button = ButtonWidget("PREVIEW\nSHOW", "#1e5631")
                self.replace_button("EXECUTE SHOW", new_button)
            else:
                # In hardware mode, use original EXECUTE ALL text
                new_button = ButtonWidget("EXECUTE\nSHOW", "#1e5631")
                self.replace_button("EXECUTE SHOW", new_button)
