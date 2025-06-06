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
    execute_cue_clicked = Signal()
    execute_all_clicked = Signal()
    stop_clicked = Signal()
    pause_clicked = Signal()
    resume_clicked = Signal()
    mode_clicked = Signal()
    create_cue_clicked = Signal()
    edit_cue_clicked = Signal()
    delete_cue_clicked = Signal()
    delete_all_clicked = Signal()
    music_clicked = Signal()
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
            ("EXECUTE\n CUE", "#1e5631"),
            ("EXECUTE\n SHOW", "#1e5631"),
            ("STOP", "#8b0000"),
            ("PAUSE", "#1e3d6e"),
            ("RESUME", "#1e3d6e"),
            ("MODE", "#cc5500"),
            ("CREATE\n CUE", "#333333"),
            ("EDIT\n CUE", "#333333"),
            ("DELETE\n CUE", "#333333"),
            ("DELETE\n ALL", "#333333"),
            ("MUSIC", "#333333"),
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
        signal_map = {
            "EXECUTE CUE": self.execute_cue_clicked,
            "EXECUTE SHOW": self.execute_all_clicked,
            "PREVIEW SHOW": self.execute_all_clicked,
            "STOP": self.stop_clicked,
            "ABORT": self.stop_clicked,
            "PAUSE": self.pause_clicked,
            "RESUME": self.resume_clicked,
            "MODE": self.mode_clicked,
            "CREATE CUE": self.create_cue_clicked,
            "EDIT CUE": self.edit_cue_clicked,
            "DELETE CUE": self.delete_cue_clicked,
            "DELETE ALL": self.delete_all_clicked,
            "MUSIC": self.music_clicked,
            "GENERATE SHOW": self.generate_show_clicked,
            "LOAD SHOW": self.load_show_clicked,
            "IMPORT SHOW": self.import_show_clicked,
            "EXPORT SHOW": self.export_show_clicked,
            "SAVE SHOW": self.save_show_clicked,
            "EXIT": self.exit_clicked
        }

        if button_name in signal_map:
            button.clicked.connect(signal_map[button_name].emit)

    def initialize_playback_buttons(self):
        """Initialize playback control buttons to correct states"""
        # Disable control buttons initially
        control_buttons = ["STOP", "ABORT", "PAUSE", "RESUME"]
        for button_name in control_buttons:
            if button_name in self.buttons:
                self.buttons[button_name].set_active(False)

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

    def update_mode_buttons(self, is_simulation_mode):
        """Update buttons based on current system mode"""
        # Update MODE button
        if "MODE" in self.buttons:
            if is_simulation_mode:
                # For simulation mode - orange color
                new_button = ButtonWidget("SIMULATION\nMODE", "#cc5500")
                self.replace_button("MODE", new_button)

                # Disable EXECUTE CUE button in simulation mode
                if "EXECUTE CUE" in self.buttons:
                    self.buttons["EXECUTE CUE"].set_active(False)

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


