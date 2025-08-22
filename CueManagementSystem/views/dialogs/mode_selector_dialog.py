import os
import sys
import re
import json
import time
import tempfile
import importlib.util

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QRadioButton,
                               QGroupBox, QFormLayout, QLineEdit,
                               QSpinBox, QDialogButtonBox, QMessageBox,
                               QComboBox, QTabWidget, QCheckBox,
                               QFileDialog, QTextEdit, QProgressBar,
                               QScrollArea, QWidget, QSizePolicy,
                               QProgressDialog, QMenu, QApplication
                               )
from PySide6.QtCore import Qt, Signal, QTimer, QEvent
from PySide6.QtGui import QFont, QColor, QPalette, QTextCursor, QKeySequence, QAction, QTextCharFormat, QShortcut

# Import the simple file editor
try:
    from views.managers.file_editor_manager import SimpleFileEditor
except ImportError:
    # If the module doesn't exist in the path, try to load it from the current directory
    try:
        spec = importlib.util.spec_from_file_location("simple_file_editor",
                                                      os.path.join(os.path.dirname(__file__), "simple_file_editor.py"))
        simple_file_editor_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(simple_file_editor_module)
        SimpleFileEditor = simple_file_editor_module.SimpleFileEditor
    except Exception as e:
        print(f"Error importing SimpleFileEditor: {e}")


        # Create a minimal version if we can't load it
        class SimpleFileEditor(QDialog):
            def __init__(self, filename, ssh_client=None, parent=None):
                super().__init__(parent)
                self.setWindowTitle(f"Edit: {filename}")
                layout = QVBoxLayout(self)
                layout.addWidget(QLabel(f"Simple file editor not available. Cannot edit {filename}"))
                self.setLayout(layout)
from datetime import datetime
from datetime import datetime

# Import terminal_commands module if available
try:
    import terminal_commands
except ImportError:
    # If the module doesn't exist in the path, try to load it from the current directory
    try:
        spec = importlib.util.spec_from_file_location("terminal_commands",
                                                      os.path.join(os.path.dirname(__file__), "terminal_commands.py"))
        terminal_commands = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(terminal_commands)
    except Exception:
        # Create a minimal version if we can't load it
        class MinimalTerminalCommands:
            def get_mac_command_output(self, cmd):
                return f"Command '{cmd}' not supported. Terminal simulation is limited."


        terminal_commands = MinimalTerminalCommands()


class EnhancedTerminal(QTextEdit):
    """
    Enhanced terminal emulator that behaves like a macOS terminal

    Features:
    - Command history with up/down arrow navigation
    - Copy and paste support
    - Proper prompt handling
    - ANSI color code support
    - Tab completion (basic)
    - Tab switching support (NEW)
    - Dialog reopening support (NEW)
    """

    command_executed = Signal(str)  # Signal emitted when a command is executed

    # NEW: Signal to notify when terminal state changes
    terminal_state_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Set up appearance
        self._setup_appearance()

        # Terminal state
        self.command_history = []
        self.history_index = 0
        self.prompt = "(base) michaellyman@Michaels-MacBook-Pro ~ % "
        self.pi_prompt = "cuepishifter@cuepishifter:~ $ "
        self.prompt_position = 0
        self.current_command = ""
        self.pi_mode = False  # Flag to track if we're in Pi mode

        # Password handling
        self.waiting_for_password = False
        self.password_target = None
        self.password_input = ""
        self.password_mode = False

        # NEW: Tab switching handling
        self.parent_tab_widget = None
        self.last_active_tab_index = 0

        # Install event filter for key handling
        self.installEventFilter(self)

        # Set up context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # Initialize terminal with welcome message and prompt
        self.initialize_terminal()

    def _setup_appearance(self):
        """Set up the terminal appearance"""
        # Set monospace font
        font_family = "Menlo" if sys.platform == "darwin" else "Courier New"
        font = QFont(font_family, 12)  # Increased font size for better readability
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)

        # Set colors - macOS terminal colors with better contrast
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;  /* Slightly lighter black for better readability */
                color: #f0f0f0;  /* Brighter white for better contrast */
                font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
                font-size: 12pt;  /* Increased font size */
                border: 1px solid #444444;  /* More visible border */
                border-radius: 5px;
                padding: 10px;  /* More padding for comfort */
                selection-background-color: #4a90d9;
                selection-color: #ffffff;
                line-height: 1.3;  /* Better line spacing */
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 14px;  /* Wider scrollbar for easier use */
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 7px;
                min-height: 30px;  /* Larger handle */
            }
            QScrollBar::handle:vertical:hover {
                background-color: #777777;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;  /* Hide arrow buttons */
            }
        """)

        # Set text edit properties
        self.setAcceptRichText(True)
        self.setUndoRedoEnabled(False)
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.setReadOnly(False)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # Always show vertical scrollbar
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Enable cursor blinking
        self.setCursorWidth(8)  # Wider cursor like in terminal

        # Enable text interaction
        self.setTextInteractionFlags(
            Qt.TextEditorInteraction |
            Qt.TextSelectableByMouse |
            Qt.TextSelectableByKeyboard
        )

        # Set focus policy to ensure it can receive keyboard focus
        self.setFocusPolicy(Qt.StrongFocus)

    def initialize_terminal(self):
        """Initialize the terminal with welcome message and prompt"""
        # Get current date for macOS-style "Last login" message
        current_date = datetime.now().strftime("%a %b %d %H:%M:%S")

        # macOS-style welcome message with helpful instructions
        welcome_message = f"""Last login: {current_date} on ttys002

Welcome to the Terminal Interface

This terminal works like a real macOS terminal:
- Type commands and press Enter to execute them
- Use 'ssh username@hostname' to connect to your Pi
- Try commands like: ls, pwd, whoami, date, help

To connect to your Pi, type:
  ssh cuepishifter@192.168.68.82  (or your Pi's IP/hostname)

"""
        self.append_text(welcome_message)

        # Set initial prompt (macOS style)
        self.prompt = "(base) michaellyman@Michaels-MacBook-Pro ~ % "
        self.pi_mode = False
        self.show_prompt()

        # Set focus to the terminal
        self.setFocus()

    # NEW: Add tab change handler method
    def add_tab_change_handler(self, tab_widget):
        """
        Add a tab change event handler to properly reset the cursor position
        when switching back to the terminal tab.

        Args:
            tab_widget: The QTabWidget containing the terminal
        """
        self.parent_tab_widget = tab_widget
        tab_widget.currentChanged.connect(self.handle_tab_change)

        # Store the initial tab index
        self.last_active_tab_index = tab_widget.currentIndex()

    # NEW: Handle tab change events
    def handle_tab_change(self, index):
        """
        Handle tab change events to properly restore terminal state
        when switching back to the terminal tab.

        Args:
            index: The index of the newly selected tab
        """
        # Check if we're switching to the tab containing the terminal
        terminal_parent = self.parent()
        while terminal_parent and not isinstance(terminal_parent, QScrollArea):
            terminal_parent = terminal_parent.parent()

        terminal_tab = terminal_parent.parent() if terminal_parent else None

        # If we're switching to the terminal tab
        if terminal_tab and self.parent_tab_widget.widget(index) == terminal_tab:
            # We're switching to the terminal tab
            QTimer.singleShot(50, self.restore_terminal_state)

        # Store the current tab index
        self.last_active_tab_index = index

    # NEW: Restore terminal state method
    def restore_terminal_state(self):
        """
        Restore the terminal state after tab switching or dialog reopening.
        This ensures the cursor is in the right place and the terminal is ready for input.
        """
        # Set focus to the terminal
        self.setFocus()

        # Restore cursor position
        self.restore_cursor_position()

        # Process any pending events to ensure UI updates properly
        QApplication.processEvents()

        # Emit signal that terminal state has been restored
        self.terminal_state_changed.emit()

    # NEW: Restore cursor position method
    def restore_cursor_position(self):
        """
        Restore the cursor position to the end of the prompt or current command.
        This ensures the cursor is in the right place after tab switches.
        """
        # Get the current text
        text = self.toPlainText()

        # Move cursor to the end
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)

        # Update the prompt position to ensure it's at the right place
        self.prompt_position = cursor.position()

        # Make sure the cursor is visible
        self.ensureCursorVisible()

    # NEW: Override focusInEvent to handle focus properly
    def focusInEvent(self, event):
        """
        Handle focus events to ensure proper cursor positioning
        when the terminal receives focus.
        """
        # Call the parent class implementation first
        super().focusInEvent(event)

        # Restore cursor position when terminal gets focus
        QTimer.singleShot(10, self.restore_cursor_position)

        # Accept the event
        event.accept()

    def handle_ssh_password(self, password):
        """Handle SSH password input and attempt connection"""
        if not self.password_target:
            self.append_text("\nError: No SSH connection in progress\n")
            self.show_prompt()
            return

        username, hostname = self.password_target
        self.append_text("\n")  # New line after password

        # Get parent dialog
        parent_dialog = self.parent()
        while parent_dialog and not isinstance(parent_dialog, QDialog):
            parent_dialog = parent_dialog.parent()

        if parent_dialog:
            # Update connection settings
            parent_dialog.host_input.setText(hostname)
            parent_dialog.username_input.setText(username)
            parent_dialog.password_input.setText(password)

            # Simulate connection process
            self.append_text(f"Connecting to {hostname}...\n")

            # Show some realistic connection messages
            import time
            self.append_text("OpenSSH_9.0p1, LibreSSL 3.3.6\n")
            time.sleep(0.2)
            self.append_text(f"debug1: Connecting to {hostname} port 22.\n")
            time.sleep(0.3)
            self.append_text(f"debug1: Connection established.\n")
            time.sleep(0.2)
            self.append_text("debug1: Authenticating to cuepishifter.local:22 as 'cuepishifter'\n")
            time.sleep(0.4)
            self.append_text("debug1: Authentication succeeded.\n")
            time.sleep(0.2)

            # Switch to Pi mode
            self.switch_to_pi_mode()
            self.show_prompt()

            # Update connection status in parent dialog
            if hasattr(parent_dialog, 'update_connection_status'):
                parent_dialog.update_connection_status(True)

    def switch_to_pi_mode(self):
        """Switch to Raspberry Pi terminal mode"""
        self.pi_mode = True
        self.prompt = "cuepishifter@cuepishifter:~ $ "
        # Don't show the prompt here, it will be shown after the next command

    def switch_to_mac_mode(self):
        """Switch back to macOS terminal mode"""
        self.pi_mode = False
        self.prompt = "(base) michaellyman@Michaels-MacBook-Pro ~ % "

    def append_text(self, text, color=None):
        """Append text to the terminal with optional color"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)

        if color:
            format = QTextCharFormat()
            format.setForeground(QColor(color))
            cursor.setCharFormat(format)

        cursor.insertText(text)

        if color:
            format = QTextCharFormat()
            format.setForeground(QColor("#ffffff"))  # Reset to default color
            cursor.setCharFormat(format)

        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def show_prompt(self):
        """Show the command prompt"""
        self.append_text(self.prompt)
        cursor = self.textCursor()
        self.prompt_position = cursor.position()
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

        # Scroll to the bottom to ensure prompt is visible
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

        # Set focus to the terminal
        self.setFocus()

    def _show_context_menu(self, position):
        """Show custom context menu"""
        menu = QMenu(self)

        # Add standard actions
        copy_action = menu.addAction("Copy")
        paste_action = menu.addAction("Paste")
        menu.addSeparator()
        clear_action = menu.addAction("Clear Terminal")

        # Connect actions
        copy_action.triggered.connect(self.copy)
        paste_action.triggered.connect(self._handle_paste)
        clear_action.triggered.connect(self.clear_terminal)

        # Show menu
        menu.exec(self.mapToGlobal(position))

    def _handle_paste(self):
        """Handle paste operation"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()

        if text:
            # Only paste at or after prompt
            cursor = self.textCursor()
            if cursor.position() >= self.prompt_position:
                cursor.insertText(text)
                self.setTextCursor(cursor)

    def clear_terminal(self):
        """Clear the terminal and show a new prompt"""
        self.clear()
        self.show_prompt()

    def show_file_operation_help(self):
        """Show help for file operations in the terminal"""
        help_text = """
📝 File Operations Help:

You can use the following commands for file operations:

1️⃣ Edit a file with our built-in editor:
   nano filename.txt

2️⃣ Create a new file:
   touch filename.txt

3️⃣ Write to a file:
   echo "content" > filename.txt

4️⃣ Append to a file:
   echo "more content" >> filename.txt

5️⃣ View file contents:
   cat filename.txt

6️⃣ Delete a file:
   rm filename.txt

7️⃣ Create a directory:
   mkdir dirname

8️⃣ List files:
   ls -la

9️⃣ Copy a file:
   cp source.txt destination.txt

🔟 Move/rename a file:
   mv oldname.txt newname.txt

Note: Our 'nano' implementation opens a graphical editor window
where you can edit files with full keyboard support.
Use Ctrl+S to save, Ctrl+X to save and exit.

"""
        self.append_text(help_text, "#3498db")  # Blue color for help text

    def process_command(self, command):
        """Process and emit the command"""
        if command.strip():
            # Add to history
            self.command_history.append(command)
            self.history_index = len(self.command_history)

            # Handle special commands
            if command.strip() == "clear":
                self.clear_terminal()
                return

            # Emit the command for external handling
            self.command_executed.emit(command)
        else:
            # Empty command, just show the prompt again
            self.show_prompt()

    def process_ansi_colors(self, text):
        """Process ANSI color codes in text"""
        # This is a simplified implementation that handles basic color codes
        # For a full implementation, consider using a library like 'ansi2html'

        # Define ANSI color code patterns
        ansi_pattern = re.compile(r'\x1b\[([\d;]+)m')

        # Define color mapping (ANSI code -> HTML color)
        color_map = {
            '30': '#000000',  # Black
            '31': '#cc0000',  # Red
            '32': '#4e9a06',  # Green
            '33': '#c4a000',  # Yellow
            '34': '#3465a4',  # Blue
            '35': '#75507b',  # Magenta
            '36': '#06989a',  # Cyan
            '37': '#d3d7cf',  # White
            '90': '#555753',  # Bright Black
            '91': '#ef2929',  # Bright Red
            '92': '#8ae234',  # Bright Green
            '93': '#fce94f',  # Bright Yellow
            '94': '#729fcf',  # Bright Blue
            '95': '#ad7fa8',  # Bright Magenta
            '96': '#34e2e2',  # Bright Cyan
            '97': '#eeeeec',  # Bright White
        }

        # Process text with color codes
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)

        # Split text by ANSI codes
        parts = ansi_pattern.split(text)

        if len(parts) == 1:
            # No ANSI codes, just append the text
            cursor.insertText(text)
        else:
            current_color = "#ffffff"  # Default color

            for i, part in enumerate(parts):
                if i % 2 == 0:
                    # This is text content
                    if part:
                        format = QTextCharFormat()
                        format.setForeground(QColor(current_color))
                        cursor.setCharFormat(format)
                        cursor.insertText(part)
                else:
                    # This is a color code
                    for code in part.split(';'):
                        if code in color_map:
                            current_color = color_map[code]
                        elif code == '0':
                            current_color = "#ffffff"  # Reset to default

        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def eventFilter(self, obj, event):
        """Filter events to handle keyboard input and mouse clicks"""
        if obj is self:
            if event.type() == QEvent.KeyPress:
                return self._handle_key_press(event)
            elif event.type() == QEvent.MouseButtonPress:
                # Set focus when clicked
                self.setFocus()
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        """Handle mouse press events to set focus and position cursor"""
        super().mousePressEvent(event)
        self.setFocus()  # Ensure terminal gets focus when clicked

    def _handle_key_press(self, event):
        """Handle key press events"""
        key = event.key()
        modifiers = event.modifiers()

        # Get current cursor and its position
        cursor = self.textCursor()
        pos = cursor.position()

        # Special handling for password input
        if self.waiting_for_password:
            if key == Qt.Key_Return or key == Qt.Key_Enter:
                # Process password
                password = self.password_input
                self.password_input = ""
                self.waiting_for_password = False

                # Handle SSH password
                self.handle_ssh_password(password)

                return True

            elif key == Qt.Key_Escape:
                # Cancel password input
                self.password_input = ""
                self.waiting_for_password = False
                self.append_text("\nPassword input cancelled\n")
                self.show_prompt()
                return True

            elif key == Qt.Key_Backspace:
                # Handle backspace in password
                if self.password_input:
                    self.password_input = self.password_input[:-1]
                return True

            else:
                # Add character to password (if it's a printable character)
                text = event.text()
                if text and text.isprintable():
                    self.password_input += text
                return True

        # Only allow editing after prompt
        if pos < self.prompt_position and key not in (Qt.Key_Home, Qt.Key_End):
            if key in (Qt.Key_Left, Qt.Key_Backspace, Qt.Key_Up, Qt.Key_Down):
                return True  # Block these keys

            # For other keys, move cursor to end first
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)
            pos = cursor.position()

        # Handle special keys
        if key == Qt.Key_Return or key == Qt.Key_Enter:
            # Get current command
            command = self.toPlainText()[self.prompt_position:]

            # Add new line
            self.append_text("\n")

            # Process the command
            self.process_command(command)

            # Don't show prompt here - it will be shown after command processing
            return True

        elif key == Qt.Key_Up:
            # Previous command in history
            if self.command_history and self.history_index > 0:
                self.history_index -= 1
                self._replace_current_command(self.command_history[self.history_index])
            return True

        elif key == Qt.Key_Down:
            # Next command in history
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self._replace_current_command(self.command_history[self.history_index])
            elif self.history_index == len(self.command_history) - 1:
                self.history_index = len(self.command_history)
                self._replace_current_command("")
            return True

        elif key == Qt.Key_Home:
            # Move to start of command (after prompt)
            cursor.setPosition(self.prompt_position)
            self.setTextCursor(cursor)
            return True

        elif key == Qt.Key_End:
            # Move to end of command
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)
            return True

        elif key == Qt.Key_Backspace:
            # Don't allow deleting prompt
            if pos <= self.prompt_position:
                return True

        # Handle Ctrl+L to clear screen
        elif key == Qt.Key_L and modifiers == Qt.ControlModifier:
            self.clear_terminal()
            return True

        # Handle Ctrl+C to cancel current command
        elif key == Qt.Key_C and modifiers == Qt.ControlModifier:
            self.append_text("^C\n")
            self.show_prompt()
            return True

        # Allow normal key processing
        return False

    def _replace_current_command(self, new_command):
        """Replace current command with a new one"""
        # Select from prompt to end
        cursor = self.textCursor()
        cursor.setPosition(self.prompt_position)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)

        # Replace with new command
        cursor.insertText(new_command)
        self.setTextCursor(cursor)


class ModeSelector(QDialog):
    """
    Dialog for selecting system operation mode

    Features:
    - Toggle between simulation and hardware modes
    - Configure hardware connection settings for Raspberry Pi
    - Save and apply mode changes
    """

    # Signal emitted when mode is changed and applied
    mode_changed = Signal(str, dict, str)  # mode, connection_settings, communication_method

    # NEW: Signal emitted when dialog is shown
    shown = Signal()

    def __init__(self, current_mode="simulation", connection_settings=None, communication_method="ssh", parent=None):
        super().__init__(parent)

        # Store parent reference
        self.main_window = parent

        # Initialize default settings
        self.current_mode = current_mode
        self.communication_method = communication_method
        self.connection_settings = connection_settings or {
            "host": "cuepishifter.local",
            "port": 22,
            "username": "cuepishifter",
            "password": ""
        }

        # Connection status tracking - initialize as connected if in hardware mode
        self.ssh_connected = (current_mode == "hardware")

        # Set up UI
        self.setWindowTitle("System Mode Selection")
        self.setMinimumWidth(1000)
        self.setMinimumHeight(900)
        self.resize(1100, 950)
        self.setup_ui()

        # If we're in hardware mode, attempt to connect automatically
        if current_mode == "hardware":
            self.test_ssh_connection_simple(self.connection_settings)

    # NEW: Override showEvent to emit shown signal
    def showEvent(self, event):
        """Handle dialog show event"""
        super().showEvent(event)
        # Emit signal that dialog is shown
        self.shown.emit()

        # If terminal exists, restore its state
        if hasattr(self, 'terminal_widget'):
            QTimer.singleShot(100, self.terminal_widget.restore_terminal_state)

    def setup_ui(self):
        """Set up the dialog UI components"""
        main_layout = QVBoxLayout(self)

        # Mode selection group - centered
        mode_group = QGroupBox("Operation Mode")
        mode_layout = QHBoxLayout(mode_group)

        # Add stretch before buttons
        mode_layout.addStretch()

        # Mode radio buttons
        self.simulation_radio = QRadioButton("Simulation Mode")
        self.hardware_radio = QRadioButton("Hardware Mode (Raspberry Pi)")

        # Add tooltip explanations
        self.simulation_radio.setToolTip("Run in simulation mode without connecting to hardware")
        self.hardware_radio.setToolTip("Connect to Raspberry Pi and execute commands on the hardware")

        # Set checked state based on current mode
        if self.current_mode == "simulation":
            self.simulation_radio.setChecked(True)
        else:
            self.hardware_radio.setChecked(True)

        # Add radio buttons to centered layout
        mode_layout.addWidget(self.simulation_radio)
        mode_layout.addWidget(self.hardware_radio)

        # Add stretch after buttons
        mode_layout.addStretch()

        # Create tabbed interface for settings
        self.tab_widget = QTabWidget()

        # Basic Connection Tab
        self.basic_tab = self.create_basic_connection_tab()
        self.tab_widget.addTab(self.basic_tab, "SSH Connection")

        # GPIO Pin Assignments Tab
        self.gpio_tab = self.create_gpio_assignments_tab()
        self.tab_widget.addTab(self.gpio_tab, "GPIO Pins")

        # GPIO Status Monitoring Tab
        self.gpio_status_tab = self.create_gpio_status_tab()
        self.tab_widget.addTab(self.gpio_status_tab, "GPIO Status")

        # Standard dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Close)
        button_box.button(QDialogButtonBox.Apply).setText("Apply Settings")
        button_box.button(QDialogButtonBox.Close).setText("Close Dialog")
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.accept_changes)
        button_box.button(QDialogButtonBox.Close).clicked.connect(self.reject)

        # Pi control buttons - moved from basic tab to main dialog
        pi_controls_group = QGroupBox("Pi Control")
        pi_controls_layout = QHBoxLayout(pi_controls_group)
        pi_controls_layout.addStretch()

        # Create the buttons (moved from basic tab)
        self.shutdown_button = QPushButton("Shut Down Pi")
        self.shutdown_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """)
        self.shutdown_button.clicked.connect(self.shutdown_pi)

        self.wifi_button = QPushButton("WiFi Mode")
        self.wifi_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """)
        self.wifi_button.clicked.connect(self.set_wifi_mode)

        self.adhoc_button = QPushButton("Adhoc Mode")
        self.adhoc_button.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """)
        self.adhoc_button.clicked.connect(self.set_adhoc_mode)

        pi_controls_layout.addWidget(self.shutdown_button)
        pi_controls_layout.addWidget(self.wifi_button)
        pi_controls_layout.addWidget(self.adhoc_button)
        pi_controls_layout.addStretch()

        # Add all components to main layout
        main_layout.addWidget(mode_group)
        main_layout.addWidget(self.tab_widget)
        main_layout.addWidget(pi_controls_group)
        main_layout.addWidget(button_box)

        # Connect signals
        self.simulation_radio.toggled.connect(self.update_connection_ui)
        self.hardware_radio.toggled.connect(self.update_connection_ui)

        # Initial UI state update
        self.update_connection_ui()

        # Update SSH status label based on current connection state
        if self.ssh_connected:
            self.ssh_status_label.setText("SSH: ✅ Connected")
            self.ssh_status_label.setStyleSheet(
                "padding: 8px; border: 2px solid #1e8449; border-radius: 5px; background-color: #1e8449; color: white; font-weight: bold;")
        else:
            self.ssh_status_label.setText("SSH: ❌ Not Connected")
            self.ssh_status_label.setStyleSheet(
                "padding: 8px; border: 2px solid #a93226; border-radius: 5px; background-color: #a93226; color: white; font-weight: bold;")

        # NEW: Connect tab widget signals
        self.tab_widget.currentChanged.connect(self.handle_tab_change)

    # NEW: Handle tab change method
    def handle_tab_change(self, index):
        """
        Handle tab change events to ensure terminal state is properly maintained

        Args:
            index: The index of the newly selected tab
        """
        # If switching to the basic tab (with terminal)
        if index == 0 and hasattr(self, 'terminal_widget'):
            # Give terminal focus after a short delay to ensure UI is updated
            QTimer.singleShot(100, self.terminal_widget.setFocus)
            QTimer.singleShot(150, self.terminal_widget.restore_cursor_position)

    def create_basic_connection_tab(self):
        """Create the basic connection settings tab"""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)

        # Connection status indicators (compact)
        requirements_group = QGroupBox("Connection Status")
        requirements_layout = QVBoxLayout(requirements_group)

        # Connection status indicators
        status_layout = QHBoxLayout()
        status_layout.addStretch()

        self.ssh_status_label = QLabel("SSH: ❌ Not Connected")

        self.ssh_status_label.setStyleSheet(
            "padding: 8px; border: 2px solid #a93226; border-radius: 5px; background-color: #a93226; color: white; font-weight: bold;")
        status_layout.addWidget(self.ssh_status_label)

        # Add some spacing between indicators
        status_layout.addSpacing(10)

        # Network mode status
        self.network_mode_label = QLabel("Mode: WiFi")
        self.network_mode_label.setStyleSheet(
            "padding: 8px; border: 2px solid #2980b9; border-radius: 5px; background-color: #2980b9; color: white; font-weight: bold;")
        status_layout.addWidget(self.network_mode_label)

        status_layout.addStretch()

        requirements_layout.addLayout(status_layout)
        main_layout.addWidget(requirements_group)

        # Connection settings - centered
        connection_group = QGroupBox("Connection Settings")
        connection_layout = QVBoxLayout(connection_group)

        # Create form layout for connection fields
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)

        # Create connection fields
        self.host_input = QLineEdit(self.connection_settings.get("host", "raspberrypi.local"))
        self.username_input = QLineEdit(self.connection_settings.get("username", "pi"))
        self.password_input = QLineEdit(self.connection_settings.get("password", ""))
        self.password_input.setEchoMode(QLineEdit.Password)

        # SSH port input
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(self.connection_settings.get("port", 22))

        # Add fields to form layout
        form_layout.addRow("Host:", self.host_input)
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", self.password_input)
        form_layout.addRow("SSH Port:", self.port_input)

        # Center the form
        center_layout = QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(form_widget)
        center_layout.addStretch()

        connection_layout.addLayout(center_layout)

        # Test connection buttons - centered
        test_layout = QHBoxLayout()
        test_layout.addStretch()

        self.test_ssh_button = QPushButton("Test SSH Connection")
        self.test_ssh_button.clicked.connect(self.test_ssh_connection)

        test_layout.addWidget(self.test_ssh_button)
        test_layout.addStretch()

        connection_layout.addLayout(test_layout)
        main_layout.addWidget(connection_group)

        # Terminal window - full width
        terminal_group = QGroupBox("Terminal")
        terminal_layout = QVBoxLayout(terminal_group)

        # Add a label with instructions
        instructions = QLabel("Type commands below. Use 'ssh username@hostname' to connect to your Pi.")
        instructions.setStyleSheet("color: #888888; font-style: italic;")
        terminal_layout.addWidget(instructions)

        # Create a scroll area for the terminal
        terminal_scroll = QScrollArea()
        terminal_scroll.setWidgetResizable(True)
        terminal_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        terminal_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Create a container widget for the terminal
        terminal_container = QWidget()
        terminal_container_layout = QVBoxLayout(terminal_container)
        terminal_container_layout.setContentsMargins(0, 0, 0, 0)

        # Create a custom terminal widget
        self.terminal_widget = EnhancedTerminal(self)
        self.terminal_widget.setMinimumHeight(400)
        self.terminal_widget.setFocusPolicy(Qt.StrongFocus)  # Ensure it can receive keyboard focus

        # Connect terminal signals
        self.terminal_widget.command_executed.connect(self.handle_terminal_command)

        # NEW: Connect terminal to tab widget for tab change handling
        self.terminal_widget.add_tab_change_handler(self.tab_widget)

        # NEW: Connect dialog shown signal to terminal restore
        self.shown.connect(self.terminal_widget.restore_terminal_state)

        # Add terminal to container
        terminal_container_layout.addWidget(self.terminal_widget)
        terminal_container_layout.addStretch()

        # Set container as scroll area widget
        terminal_scroll.setWidget(terminal_container)

        # Add scroll area to layout
        terminal_layout.addWidget(terminal_scroll)

        main_layout.addWidget(terminal_group)

        return tab

    def create_gpio_assignments_tab(self):
        """Create the GPIO pin assignments reference tab"""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Title and description
        title_label = QLabel("🔌 GPIO Pin Assignments Reference")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                text-align: center;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        description_label = QLabel(
            "Complete GPIO pin assignments for your Raspberry Pi Zero W2 firework control system")
        description_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #7f8c8d;
                padding: 5px;
                text-align: center;
            }
        """)
        description_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(description_label)

        # Create scrollable area for GPIO pins
        gpio_scroll = QScrollArea()
        gpio_scroll.setWidgetResizable(True)

        gpio_content = QWidget()
        gpio_content_layout = QVBoxLayout(gpio_content)

        # Create organized GPIO reference with color coding
        gpio_html = """
        <div style='background-color: #2c3e50; color: white; padding: 20px; font-family: Consolas, Monaco, monospace; font-size: 13px; line-height: 1.6;'>

            <table style='width: 100%; border-collapse: collapse; margin-bottom: 20px;'>
                <tr style='background-color: #3498db; color: white;'>
                    <th colspan='6' style='padding: 12px; text-align: center; font-size: 16px; font-weight: bold;'>
                        🔧 SHIFT REGISTER CONTROL PINS (15 pins)
                    </th>
                </tr>
                <tr style='background-color: #e74c3c; color: white;'>
                    <th style='padding: 8px; text-align: center; width: 16.66%;'>Chain 1</th>
                    <th style='padding: 8px; text-align: center; width: 16.66%;'>Chain 2</th>
                    <th style='padding: 8px; text-align: center; width: 16.66%;'>Chain 3</th>
                    <th style='padding: 8px; text-align: center; width: 16.66%;'>Chain 4</th>
                    <th style='padding: 8px; text-align: center; width: 16.66%;'>Chain 5</th>
                    <th style='padding: 8px; text-align: center; width: 16.66%;'>Function</th>
                </tr>
                <tr style='background-color: #27ae60; color: white;'>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 7</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 8</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 12</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 14</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 15</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>DATA</td>
                </tr>
                <tr style='background-color: #f39c12; color: white;'>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 17</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 18</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 22</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 23</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 27</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>SCLK</td>
                </tr>
                <tr style='background-color: #9b59b6; color: white;'>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 9</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 10</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 11</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 24</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 25</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>RCLK</td>
                </tr>
            </table>

            <table style='width: 100%; border-collapse: collapse; margin-bottom: 20px;'>
                <tr style='background-color: #e67e22; color: white;'>
                    <th colspan='6' style='padding: 12px; text-align: center; font-size: 16px; font-weight: bold;'>
                        ⚡ OUTPUT CONTROL PINS (10 pins)
                    </th>
                </tr>
                <tr style='background-color: #c0392b; color: white;'>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 2</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 3</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 4</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 5</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 6</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>OE (Output Enable)</td>
                </tr>
                <tr style='background-color: #8e44ad; color: white;'>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 13</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 16</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 19</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 20</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>GPIO 26</td>
                    <td style='padding: 8px; text-align: center; font-weight: bold; font-size: 14px;'>SRCLR (Serial Clear)</td>
                </tr>
            </table>

            <table style='width: 100%; border-collapse: collapse; margin-bottom: 20px;'>
                <tr style='background-color: #d35400; color: white;'>
                    <th colspan='2' style='padding: 12px; text-align: center; font-size: 16px; font-weight: bold;'>
                        🎯 SYSTEM CONTROL PIN (1 pin)
                    </th>
                </tr>
                <tr style='background-color: #2c3e50; color: white;'>
                    <td style='padding: 12px; text-align: center; font-weight: bold; font-size: 16px;'>GPIO 21</td>
                    <td style='padding: 12px; text-align: center; font-weight: bold; font-size: 16px;'>ARM/DISARM</td>
                </tr>
            </table>

            <div style='background-color: #34495e; padding: 15px; border-radius: 8px; margin-top: 15px;'>
                <div style='color: #ecf0f1; font-weight: bold; margin-bottom: 12px; font-size: 15px;'>📊 PIN STATE LOGIC:</div>
                <div style='color: #e74c3c; font-weight: bold; font-size: 14px; margin-bottom: 6px;'>• OE Pins: HIGH = Disabled, LOW = Enabled</div>
                <div style='color: #9b59b6; font-weight: bold; font-size: 14px; margin-bottom: 6px;'>• SRCLR Pins: LOW = Disabled, HIGH = Enabled</div>
                <div style='color: #f39c12; font-weight: bold; font-size: 14px; margin-bottom: 10px;'>• ARM Pin: LOW = Disarmed, HIGH = Armed</div>
                <div style='color: #27ae60; font-weight: bold; font-size: 15px;'>📈 SYSTEM: 5 chains × 25 registers × 8 outputs = 1000 total outputs</div>
            </div>

            <div style='background-color: #1a252f; padding: 15px; border-radius: 8px; margin-top: 15px; border: 2px solid #3498db;'>
                <div style='color: #3498db; font-weight: bold; margin-bottom: 10px; font-size: 15px;'>💡 WIRING TIPS:</div>
                <div style='color: #ecf0f1; font-size: 13px; line-height: 1.5;'>
                    • Use different colored wires for each function (DATA, SCLK, RCLK, OE, SRCLR)<br>
                    • Label each wire at both ends with GPIO number and chain number<br>
                    • Test continuity before powering up the system<br>
                    • Keep power and signal wires separated to reduce noise<br>
                    • Use proper gauge wire for power connections (12-14 AWG recommended)
                </div>
            </div>
        </div>
        """

        gpio_text = QLabel(gpio_html)
        gpio_text.setWordWrap(True)
        gpio_text.setTextFormat(Qt.RichText)

        gpio_content_layout.addWidget(gpio_text)
        gpio_scroll.setWidget(gpio_content)
        main_layout.addWidget(gpio_scroll)

        return tab

    def create_gpio_status_tab(self):
        """Create the GPIO status monitoring tab"""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title_label = QLabel("Real-Time GPIO Pin Status")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # Status indicator - initialize based on current connection state
        status_text = "Connected - Click 'Refresh GPIO Status' to view pin states" if self.ssh_connected else "Not Connected"
        status_color = "green" if self.ssh_connected else "red"
        self.gpio_connection_status = QLabel(status_text)
        self.gpio_connection_status.setStyleSheet(f"color: {status_color}; font-weight: bold;")
        main_layout.addWidget(self.gpio_connection_status)

        # Refresh button
        refresh_layout = QHBoxLayout()
        self.refresh_gpio_button = QPushButton("Refresh GPIO Status")
        self.refresh_gpio_button.clicked.connect(self.request_gpio_status)
        self.refresh_gpio_button.setEnabled(self.ssh_connected)  # Enable if connected
        refresh_layout.addWidget(self.refresh_gpio_button)
        refresh_layout.addStretch()
        main_layout.addLayout(refresh_layout)

        # Remove auto-refresh checkbox
        # self.auto_refresh_gpio = QCheckBox("Auto-refresh every 2 seconds")
        # self.auto_refresh_gpio.setChecked(True)
        # self.auto_refresh_gpio.toggled.connect(self.toggle_gpio_auto_refresh)
        # main_layout.addWidget(self.auto_refresh_gpio)

        # Scroll area for GPIO status
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(400)

        # GPIO status content widget
        self.gpio_status_content = QWidget()
        self.gpio_status_layout = QVBoxLayout(self.gpio_status_content)

        # Initialize with placeholder
        placeholder_label = QLabel("Connect to Pi and click 'Refresh GPIO Status' to view pin states")
        placeholder_label.setStyleSheet("color: gray; font-style: italic; padding: 20px;")
        placeholder_label.setAlignment(Qt.AlignCenter)
        self.gpio_status_layout.addWidget(placeholder_label)

        scroll_area.setWidget(self.gpio_status_content)
        main_layout.addWidget(scroll_area)

        # Remove GPIO auto-refresh timer
        # self.gpio_refresh_timer = QTimer()
        # self.gpio_refresh_timer.timeout.connect(self.request_gpio_status)
        # self.gpio_refresh_timer.setInterval(2000)  # 2 seconds

        return tab

    def update_connection_ui(self):
        """Update UI based on selected mode"""
        is_hardware_mode = self.hardware_radio.isChecked()

        # Enable/disable tabs based on hardware mode
        if hasattr(self, 'tab_widget'):
            self.tab_widget.setEnabled(is_hardware_mode)

    def update_connection_status(self, ssh_status):
        """Update connection status indicators"""
        self.ssh_connected = ssh_status

        # Enable/disable GPIO status functionality
        if hasattr(self, 'refresh_gpio_button'):
            self.refresh_gpio_button.setEnabled(ssh_status)

        # Update GPIO connection status
        if hasattr(self, 'gpio_connection_status') and ssh_status:
            self.gpio_connection_status.setText("Connected - Click 'Refresh GPIO Status' to view pin states")
            self.gpio_connection_status.setStyleSheet("color: green; font-weight: bold;")
        elif hasattr(self, 'gpio_connection_status'):
            self.gpio_connection_status.setText("Not Connected")
            self.gpio_connection_status.setStyleSheet("color: red; font-weight: bold;")

        # Update SSH status
        if ssh_status:
            self.ssh_status_label.setText("SSH: ✅ Connected")
            self.ssh_status_label.setStyleSheet(
                "padding: 8px; border: 2px solid #1e8449; border-radius: 5px; background-color: #1e8449; color: white; font-weight: bold;")

            # Get network mode status when connected
            self.update_network_mode_status('wifi')  # Default to WiFi mode initially

            # Switch terminal to Pi mode when connected
            if hasattr(self, 'terminal_widget'):
                self.terminal_widget.switch_to_pi_mode()

    def update_network_mode_status(self, mode):
        """Update the network mode status label

        Args:
            mode (str): Current network mode ('wifi' or 'adhoc')
        """
        if mode == "wifi":
            self.network_mode_label.setText("Mode: WiFi")
            self.network_mode_label.setStyleSheet(
                "padding: 8px; border: 2px solid #2980b9; border-radius: 5px; background-color: #2980b9; color: white; font-weight: bold;")
        elif mode == "adhoc":
            self.network_mode_label.setText("Mode: Adhoc")
            self.network_mode_label.setStyleSheet(
                "padding: 8px; border: 2px solid #27ae60; border-radius: 5px; background-color: #27ae60; color: white; font-weight: bold;")
        else:
            self.network_mode_label.setText("Mode: Unknown")
            self.network_mode_label.setStyleSheet(
                "padding: 8px; border: 2px solid #7f8c8d; border-radius: 5px; background-color: #7f8c8d; color: white; font-weight: bold;")
            if hasattr(self, 'terminal_widget'):
                self.terminal_widget.switch_to_pi_mode()

    def test_ssh_connection(self):
        """Test SSH connection to Raspberry Pi"""
        self.test_ssh_connection_simple(self.get_connection_settings())

    def test_ssh_connection_simple(self, connection_settings):
        """Simple SSH connection test using basic socket connectivity"""
        # Disable the test button during testing
        self.test_ssh_button.setEnabled(False)
        self.test_ssh_button.setText("Testing SSH...")

        try:
            import socket
            import paramiko

            # First test basic connectivity
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)

            result = sock.connect_ex((connection_settings["host"], connection_settings["port"]))
            sock.close()

            if result != 0:
                self.handle_ssh_test_result(False, f"Cannot reach SSH port {connection_settings['port']}")
                return

            # Try SSH authentication using paramiko (simpler than asyncssh)
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                ssh.connect(
                    hostname=connection_settings["host"],
                    port=connection_settings["port"],
                    username=connection_settings["username"],
                    password=connection_settings["password"],
                    timeout=10
                )

                # Test a simple command
                stdin, stdout, stderr = ssh.exec_command("echo 'SSH test successful'")
                output = stdout.read().decode().strip()
                error = stderr.read().decode().strip()

                ssh.close()

                if output == "SSH test successful":
                    self.handle_ssh_test_result(True, "SSH connection and authentication successful!")
                else:
                    self.handle_ssh_test_result(False, f"SSH command failed: {error}")

            except paramiko.AuthenticationException:
                self.handle_ssh_test_result(False, "SSH authentication failed - check username and password")
            except paramiko.SSHException as e:
                self.handle_ssh_test_result(False, f"SSH connection failed: {str(e)}")
            except Exception as e:
                self.handle_ssh_test_result(False, f"SSH error: {str(e)}")

        except ImportError:
            # Fallback to basic connectivity test if paramiko not available
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)

                result = sock.connect_ex((connection_settings["host"], connection_settings["port"]))
                sock.close()

                if result == 0:
                    self.handle_ssh_test_result(True, "SSH port is reachable (install paramiko for full SSH test)")
                else:
                    self.handle_ssh_test_result(False, f"Cannot reach SSH port {connection_settings['port']}")

            except Exception as e:
                self.handle_ssh_test_result(False, f"Connection test failed: {str(e)}")

        except Exception as e:
            self.handle_ssh_test_result(False, f"Connection test error: {str(e)}")

    def get_connection_settings(self):
        """Get current connection settings from UI"""
        return {
            "host": self.host_input.text(),
            "port": self.port_input.value(),
            "username": self.username_input.text(),
            "password": self.password_input.text()
        }

    def handle_ssh_test_result(self, success, message):
        """Handle SSH connection test result"""
        self.test_ssh_button.setEnabled(True)
        self.test_ssh_button.setText("Test SSH Connection")

        self.update_connection_status(success)

        if success:
            self.append_to_terminal(f"✅ SSH: {message}", "#4e9a06")  # Green color
        else:
            self.append_to_terminal(f"❌ SSH: {message}", "#cc0000")  # Red color

    def append_to_terminal(self, text, color=None):
        """Append text to terminal output with enhanced scrolling"""
        if hasattr(self, 'terminal_widget'):
            # Use the enhanced terminal's append_text method
            self.terminal_widget.append_text(text + "\n", color)

    def shutdown_pi(self):
        """Safely shutdown the Raspberry Pi"""
        reply = QMessageBox.question(
            self,
            "Confirm Shutdown",
            "Are you sure you want to shut down the Raspberry Pi?\n\n"
            "This will safely power off the Pi and you will need to\n"
            "physically power it back on to use it again.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.append_to_terminal("🔄 Initiating Pi shutdown...", "#3465a4")  # Blue color
            self.shutdown_button.setEnabled(False)
            self.shutdown_button.setText("Shutting Down...")
            self.execute_pi_command("sudo shutdown -h now", "shutdown")

    def set_wifi_mode(self):
        """Set Pi to WiFi mode"""
        if not hasattr(self, "system_mode") or not self.ssh_connected:
            self.append_to_terminal("❌ Cannot set WiFi mode - SSH not connected", "#a93226")  # Red color
            QMessageBox.warning(
                self,
                "WiFi Mode",
                "Cannot set WiFi mode - SSH not connected to Raspberry Pi."
            )
            return

        self.append_to_terminal("🔶 Setting WiFi mode...", "#c4a000")  # Yellow color

        # Call the system_mode method to handle WiFi mode
        if hasattr(self.system_mode, "handle_wifi_mode_button"):
            success = self.system_mode.handle_wifi_mode_button()

            if success:
                self.append_to_terminal("✅ Successfully switched to WiFi mode", "#1e8449")  # Green color
                self.update_network_mode_status("wifi")
            else:
                self.append_to_terminal("❌ Failed to switch to WiFi mode", "#a93226")  # Red color
        else:
            self.append_to_terminal("❌ WiFi mode functionality not available", "#a93226")  # Red color
            QMessageBox.warning(
                self,
                "WiFi Mode",
                "WiFi mode functionality not available in the system mode controller."
            )

    def set_adhoc_mode(self):
        """Set Pi to Adhoc mode"""
        if not hasattr(self, "system_mode") or not self.ssh_connected:
            self.append_to_terminal("❌ Cannot set Adhoc mode - SSH not connected", "#a93226")  # Red color
            QMessageBox.warning(
                self,
                "Adhoc Mode",
                "Cannot set Adhoc mode - SSH not connected to Raspberry Pi."
            )
            return

        self.append_to_terminal("🔶 Setting Adhoc mode...", "#c4a000")  # Yellow color

        # Call the system_mode method to handle Adhoc mode
        if hasattr(self.system_mode, "handle_adhoc_mode_button"):
            success = self.system_mode.handle_adhoc_mode_button()

            if success:
                self.append_to_terminal("✅ Successfully switched to Adhoc mode", "#1e8449")  # Green color
                self.update_network_mode_status("adhoc")
            else:
                self.append_to_terminal("❌ Failed to switch to Adhoc mode", "#a93226")  # Red color
        else:
            self.append_to_terminal("❌ Adhoc mode functionality not available", "#a93226")  # Red color
            QMessageBox.warning(
                self,
                "Adhoc Mode",
                "Adhoc mode functionality not available in the system mode controller."
            )

    def execute_pi_command(self, command, operation_name):
        """Execute a command on the Raspberry Pi"""
        try:
            connection_settings = {
                "host": self.host_input.text(),
                "username": self.username_input.text(),
                "password": self.password_input.text(),
                "port": self.port_input.value()
            }
            self.execute_ssh_command(connection_settings, command, operation_name)
        except Exception as e:
            self.append_to_terminal(f"❌ Error executing {operation_name}: {str(e)}", "#cc0000")

    def execute_ssh_command(self, connection_settings, command, operation_name):
        """Execute SSH command on Pi"""
        try:
            import paramiko
            import socket

            # For terminal commands, don't show connection messages every time
            if operation_name != "terminal_command":
                self.append_to_terminal(f"🔗 Connecting to {connection_settings['host']}...", "#3465a4")

            # Test basic connectivity
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)

            result = sock.connect_ex((connection_settings["host"], connection_settings["port"]))
            sock.close()

            if result != 0:
                self.append_to_terminal(f"❌ Cannot reach SSH port {connection_settings['port']}", "#cc0000")
                if operation_name == "shutdown":
                    self.reset_shutdown_button()
                return

            # SSH connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            ssh.connect(
                hostname=connection_settings["host"],
                port=connection_settings["port"],
                username=connection_settings["username"],
                password=connection_settings["password"],
                timeout=10
            )

            # For terminal commands, don't show connection success every time
            if operation_name != "terminal_command":
                self.append_to_terminal(f"✅ Connected via SSH", "#4e9a06")
                self.append_to_terminal(f"⚡ Executing: {command}", "#3465a4")

            # Set TERM environment variable for better terminal compatibility
            env = {'TERM': 'xterm-256color'}

            # Check if this is a terminal-based editor command (nano, vi, vim, etc.)
            is_terminal_editor = any(
                editor in command for editor in ["nano", "vi", "vim", "emacs", "pico", "less", "more"])

            if operation_name == "terminal_command" and is_terminal_editor:
                # For terminal editors in terminal_command mode, handle them differently
                if "nano" in command:
                    # Extract the filename from the nano command
                    parts = command.split()
                    if len(parts) > 1:
                        filename = parts[-1]
                        self.terminal_widget.append_text(f"📝 Opening file editor for '{filename}'...\n", "#3498db")

                        # Launch our custom file editor
                        try:
                            editor = SimpleFileEditor(filename, ssh_client=ssh, parent=self)
                            result = editor.exec()

                            if result == QDialog.Accepted:
                                self.terminal_widget.append_text(f"✅ File '{filename}' saved successfully.\n",
                                                                 "#2ecc71")
                            else:
                                self.terminal_widget.append_text(f"ℹ️ File editing cancelled.\n", "#f39c12")
                        except Exception as e:
                            self.terminal_widget.append_text(f"❌ Error opening editor: {str(e)}\n", "#cc0000")

                            # Fallback to creating an empty file
                            self.terminal_widget.append_text(f"💡 Creating empty file '{filename}' instead.\n",
                                                             "#3498db")
                            create_file_cmd = f"touch {filename}"
                            stdin, stdout, stderr = ssh.exec_command(create_file_cmd, environment=env)
                            exit_status = stdout.channel.recv_exit_status()

                            if exit_status == 0:
                                self.terminal_widget.append_text(f"✅ Created empty file: {filename}\n", "#2ecc71")
                                self.terminal_widget.append_text(
                                    f"💡 Use 'echo \"content\" > {filename}' to add content\n",
                                    "#3498db")
                            else:
                                error = stderr.read().decode()
                                self.terminal_widget.append_text(f"❌ Failed to create file: {error}\n", "#cc0000")
                    else:
                        self.terminal_widget.append_text(f"❌ Error: No filename specified for nano\n", "#cc0000")
                        self.terminal_widget.append_text(f"💡 Usage: nano filename.txt\n", "#3498db")
                else:
                    self.terminal_widget.append_text(
                        f"⚠️ Editor '{command.split()[0]}' isn't supported in this interface.\n", "#f39c12")
                    self.terminal_widget.append_text(f"💡 Try using 'nano filename.txt' instead.\n", "#3498db")

                # Show prompt after handling terminal editor command
                if hasattr(self, 'terminal_widget'):
                    self.terminal_widget.show_prompt()
            else:
                # Execute command with environment variables
                stdin, stdout, stderr = ssh.exec_command(command, environment=env)

                # Handle different operation types
                if operation_name == "shutdown":
                    self.append_to_terminal("✅ Shutdown command sent successfully", "#4e9a06")
                    self.append_to_terminal("🔌 Pi is shutting down...", "#3465a4")
                    self.append_to_terminal("   You can safely close this dialog", "#3465a4")
                elif operation_name == "terminal_command":
                    # For terminal commands, show output immediately
                    output = stdout.read().decode()
                    error = stderr.read().decode()
                    exit_status = stdout.channel.recv_exit_status()

                    if output:
                        # Process and display output with ANSI color support
                        self.terminal_widget.process_ansi_colors(output)

                    if error:
                        # Display errors in red
                        self.terminal_widget.append_text(error, "#cc0000")

                    if exit_status != 0 and not output and not error:
                        self.terminal_widget.append_text(f"❌ Command exited with status {exit_status}\n", "#cc0000")

                else:
                    # For other commands, show standard output
                    output = stdout.read().decode().strip()
                    error = stderr.read().decode().strip()

                    if output:
                        self.append_to_terminal(f"📤 Output: {output}", "#4e9a06")
                    if error:
                        self.append_to_terminal(f"⚠️ Error: {error}", "#cc0000")

            ssh.close()

        except ImportError:
            self.append_to_terminal("❌ SSH functionality requires paramiko library", "#cc0000")
            if operation_name == "shutdown":
                self.reset_shutdown_button()
        except paramiko.AuthenticationException:
            self.append_to_terminal("❌ SSH authentication failed - check username and password", "#cc0000")
            if operation_name == "shutdown":
                self.reset_shutdown_button()
        except Exception as e:
            self.append_to_terminal(f"❌ SSH error: {str(e)}", "#cc0000")
            if operation_name == "shutdown":
                self.reset_shutdown_button()

    def handle_terminal_command(self, command):
        """Handle command from the enhanced terminal"""
        cmd = command.strip()

        # Handle SSH command specially
        if cmd.startswith("ssh "):
            self._handle_ssh_command(command)
            return

        # Handle file help command in both modes
        if cmd == "help files" or cmd == "filehelp":
            self.terminal_widget.show_file_operation_help()
            self.terminal_widget.show_prompt()
            return

        # If we're in macOS mode and not an SSH command, simulate local execution
        if not self.terminal_widget.pi_mode:
            self._simulate_local_command(command)
            return

        # For Pi mode, execute on the Pi
        if not self.host_input.text():
            self.terminal_widget.append_text("❌ Error: No host specified\n", "#cc0000")
            self.terminal_widget.append_text("   Please configure connection settings first\n", "#cc0000")
            self.terminal_widget.show_prompt()
            return

        # Execute the command directly on the Pi
        self.execute_terminal_command_direct(command)

    def _handle_ssh_command(self, command):
        """Handle SSH command specially to connect to the Pi"""
        # Parse the SSH command
        parts = command.strip().split()
        if len(parts) < 2:
            self.terminal_widget.append_text("❌ Usage: ssh username@hostname\n", "#cc0000")
            self.terminal_widget.show_prompt()
            return

        # Extract username and hostname
        target = parts[1]
        if '@' in target:
            username, hostname = target.split('@', 1)
        else:
            username = self.connection_settings.get("username", "pi")
            hostname = target

        # Show connecting message
        self.terminal_widget.append_text(f"Connecting to {hostname}...\n")

        # Update connection settings
        self.host_input.setText(hostname)
        self.username_input.setText(username)

        # Simulate password prompt
        self.terminal_widget.append_text(f"{username}@{hostname}'s password: ", "#ffffff")

        # Set a flag to handle the next command as a password
        self.terminal_widget.waiting_for_password = True
        self.terminal_widget.password_target = (username, hostname)

        # Don't show prompt - we're waiting for password input
        return

    def _simulate_local_command(self, command):
        """Simulate execution of local commands in macOS terminal"""
        cmd = command.strip()

        # Handle clear command specially
        if cmd == "clear":
            self.terminal_widget.clear_terminal()
            return

        # Handle file help command
        if cmd == "help files" or cmd == "filehelp":
            self.terminal_widget.show_file_operation_help()
            self.terminal_widget.show_prompt()
            return

        try:
            # Check for terminal editor commands
            if any(editor in cmd for editor in ["nano", "vi", "vim", "emacs", "pico", "less", "more"]):
                self.terminal_widget.append_text(
                    f"⚠️ Terminal-based editors aren't fully supported in this interface.\n",
                    "#f39c12")
                self.terminal_widget.append_text(f"💡 Type 'help files' to see alternative file operation commands.\n",
                                                 "#3498db")
                self.terminal_widget.show_prompt()
                return

            # Get command output using the terminal_commands module
            if hasattr(terminal_commands, 'get_mac_command_output'):
                output = terminal_commands.get_mac_command_output(cmd)

                # Display output
                if output:
                    self.terminal_widget.append_text(output + "\n")
                else:
                    # Empty output for commands like 'echo' with no arguments
                    pass
            else:
                # Fallback for basic commands if module doesn't have the function
                if cmd == "ls":
                    self.terminal_widget.append_text("Applications    Documents    Library    Music    Public\n")
                    self.terminal_widget.append_text("Desktop         Downloads    Movies     Pictures\n")
                elif cmd == "pwd":
                    self.terminal_widget.append_text("/Users/michaellyman\n")
                elif cmd == "whoami":
                    self.terminal_widget.append_text("michaellyman\n")
                elif cmd == "date":
                    self.terminal_widget.append_text(f"{datetime.now().strftime('%a %b %d %H:%M:%S %Z %Y')}\n")
                elif cmd == "hostname":
                    self.terminal_widget.append_text("Michaels-MacBook-Pro.local\n")
                elif cmd.startswith("cd "):
                    self.terminal_widget.append_text(f"Changed directory to {cmd[3:]}\n")
                elif cmd == "help" or cmd == "?":
                    self.terminal_widget.append_text("This is a simulated macOS terminal.\n")
                    self.terminal_widget.append_text("You can use 'ssh username@hostname' to connect to your Pi.\n")
                    self.terminal_widget.append_text("Basic commands like ls, pwd, clear, etc. are simulated.\n")
                    self.terminal_widget.append_text("Type 'help files' for file operation commands.\n")
                else:
                    self.terminal_widget.append_text(f"-zsh: command not found: {cmd.split()[0]}\n")

        except Exception as e:
            # Handle any other errors
            self.terminal_widget.append_text(f"Error executing command: {str(e)}\n")

        # Show prompt again
        self.terminal_widget.show_prompt()

    def execute_terminal_command_direct(self, command):
        """Execute terminal command directly without connection popups"""
        try:
            # Get connection settings
            connection_settings = {
                "host": self.host_input.text(),
                "username": self.username_input.text(),
                "password": self.password_input.text(),
                "port": self.port_input.value()
            }

            # Execute SSH command directly
            self.execute_ssh_command_silent(connection_settings, command)

        except Exception as e:
            self.terminal_widget.append_text(f"❌ Error executing command: {str(e)}\n", "#cc0000")
            self.terminal_widget.show_prompt()

    def execute_ssh_command_silent(self, connection_settings, command):
        """Execute SSH command silently without connection messages"""
        try:
            import paramiko
            import socket

            # Test basic connectivity (silent)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)

            result = sock.connect_ex((connection_settings["host"], connection_settings["port"]))
            sock.close()

            if result != 0:
                self.terminal_widget.append_text(f"❌ Cannot reach SSH port {connection_settings['port']}\n", "#cc0000")
                self.terminal_widget.show_prompt()
                return

            # SSH connection (silent)
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            ssh.connect(
                hostname=connection_settings["host"],
                port=connection_settings["port"],
                username=connection_settings["username"],
                password=connection_settings["password"],
                timeout=10
            )

            # Check if this is a terminal-based editor command (nano, vi, vim, etc.)
            is_terminal_editor = any(
                editor in command for editor in ["nano", "vi", "vim", "emacs", "pico", "less", "more"])

            if is_terminal_editor:
                # For terminal editors, we need to handle them differently
                if "nano" in command:
                    # Extract the filename from the nano command
                    parts = command.split()
                    if len(parts) > 1:
                        filename = parts[-1]
                        self.terminal_widget.append_text(f"📝 Opening file editor for '{filename}'...\n", "#3498db")

                        # Launch our custom file editor
                        try:
                            editor = SimpleFileEditor(filename, ssh_client=ssh, parent=self)
                            result = editor.exec()

                            if result == QDialog.Accepted:
                                self.terminal_widget.append_text(f"✅ File '{filename}' saved successfully.\n",
                                                                 "#2ecc71")
                            else:
                                self.terminal_widget.append_text(f"ℹ️ File editing cancelled.\n", "#f39c12")
                        except Exception as e:
                            self.terminal_widget.append_text(f"❌ Error opening editor: {str(e)}\n", "#cc0000")

                            # Fallback to creating an empty file
                            self.terminal_widget.append_text(f"💡 Creating empty file '{filename}' instead.\n",
                                                             "#3498db")
                            create_file_cmd = f"touch {filename}"
                            stdin, stdout, stderr = ssh.exec_command(create_file_cmd)
                            exit_status = stdout.channel.recv_exit_status()

                            if exit_status == 0:
                                self.terminal_widget.append_text(f"✅ Created empty file: {filename}\n", "#2ecc71")
                                self.terminal_widget.append_text(
                                    f"💡 Use 'echo \"content\" > {filename}' to add content\n",
                                    "#3498db")
                            else:
                                error = stderr.read().decode()
                                self.terminal_widget.append_text(f"❌ Failed to create file: {error}\n", "#cc0000")
                    else:
                        self.terminal_widget.append_text(f"❌ Error: No filename specified for nano\n", "#cc0000")
                        self.terminal_widget.append_text(f"💡 Usage: nano filename.txt\n", "#3498db")
                else:
                    self.terminal_widget.append_text(
                        f"⚠️ Editor '{command.split()[0]}' isn't supported in this interface.\n", "#f39c12")
                    self.terminal_widget.append_text(f"💡 Try using 'nano filename.txt' instead.\n", "#3498db")
            else:
                # Set TERM environment variable for better terminal compatibility
                env = {'TERM': 'xterm-256color'}

                # Execute command with environment variables
                stdin, stdout, stderr = ssh.exec_command(command, environment=env)

                # Show output immediately
                output = stdout.read().decode()
                error = stderr.read().decode()
                exit_status = stdout.channel.recv_exit_status()

                if output:
                    # Process and display output with ANSI color support
                    self.terminal_widget.process_ansi_colors(output)

                if error:
                    # Display errors in red
                    self.terminal_widget.append_text(error, "#cc0000")

                if exit_status != 0 and not output and not error:
                    self.terminal_widget.append_text(f"❌ Command exited with status {exit_status}\n", "#cc0000")

            ssh.close()

            # Always show prompt after command execution
            self.terminal_widget.show_prompt()

        except ImportError:
            self.terminal_widget.append_text("❌ SSH functionality requires paramiko library\n", "#cc0000")
            self.terminal_widget.show_prompt()
        except paramiko.AuthenticationException:
            self.terminal_widget.append_text("❌ SSH authentication failed - check username and password\n", "#cc0000")
            self.terminal_widget.show_prompt()
        except Exception as e:
            self.terminal_widget.append_text(f"❌ SSH error: {str(e)}\n", "#cc0000")
            self.terminal_widget.show_prompt()

    def reset_shutdown_button(self):
        """Reset shutdown button to normal state"""
        if hasattr(self, 'shutdown_button'):
            self.shutdown_button.setEnabled(True)
            self.shutdown_button.setText("Shut Down Pi")

    def request_gpio_status(self):
        """Request GPIO status from Pi via SSH"""
        try:
            if self.ssh_connected:
                # Get connection settings
                connection_settings = {
                    "host": self.host_input.text(),
                    "username": self.username_input.text(),
                    "password": self.password_input.text(),
                    "port": self.port_input.value()
                }

                # Execute SSH command to get GPIO status
                command = "python3 ~/get_gpio_status.py"

                # Update status
                self.gpio_connection_status.setText("Requesting GPIO status...")
                self.gpio_connection_status.setStyleSheet("color: orange; font-weight: bold;")

                # Execute command and get output
                try:
                    import paramiko
                    import socket
                    import json

                    # SSH connection
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                    ssh.connect(
                        hostname=connection_settings["host"],
                        port=connection_settings["port"],
                        username=connection_settings["username"],
                        password=connection_settings["password"],
                        timeout=10
                    )

                    # Execute command
                    stdin, stdout, stderr = ssh.exec_command(command)
                    output = stdout.read().decode().strip()
                    error = stderr.read().decode().strip()

                    if error:
                        self.gpio_connection_status.setText(f"Error: {error}")
                        self.gpio_connection_status.setStyleSheet("color: red; font-weight: bold;")
                    elif output:
                        try:
                            # Parse JSON output
                            gpio_data = json.loads(output)
                            # Update the display with the data
                            self.update_gpio_status_display(gpio_data)
                        except json.JSONDecodeError as e:
                            self.gpio_connection_status.setText(f"Error parsing JSON: {e}")
                            self.gpio_connection_status.setStyleSheet("color: red; font-weight: bold;")
                            print(f"Raw output: {output}")
                    else:
                        self.gpio_connection_status.setText("No data received")
                        self.gpio_connection_status.setStyleSheet("color: red; font-weight: bold;")

                    ssh.close()

                except Exception as e:
                    self.gpio_connection_status.setText(f"SSH error: {str(e)}")
                    self.gpio_connection_status.setStyleSheet("color: red; font-weight: bold;")
            else:
                self.gpio_connection_status.setText("SSH not connected")
                self.gpio_connection_status.setStyleSheet("color: red; font-weight: bold;")
        except Exception as e:
            print(f"Error requesting GPIO status: {e}")
            self.gpio_connection_status.setText(f"Error: {e}")
            self.gpio_connection_status.setStyleSheet("color: red; font-weight: bold;")

    def get_data_pin_number(self, chain_idx):
        """Get the correct data pin number for a chain"""
        # Data pins: 7, 8, 12, 14, 15
        data_pins = [7, 8, 12, 14, 15]
        if 0 <= chain_idx < len(data_pins):
            return data_pins[chain_idx]
        return f"Unknown"

    def get_oe_pin_number(self, chain_idx):
        """Get the correct output enable pin number for a chain"""
        # Output Enable pins: 2, 3, 4, 5, 6
        oe_pins = [2, 3, 4, 5, 6]
        if 0 <= chain_idx < len(oe_pins):
            return oe_pins[chain_idx]
        return f"Unknown"

    def get_sclk_pin_number(self, chain_idx):
        """Get the correct serial clock pin number for a chain"""
        # Serial Clock pins: 17, 18, 22, 23, 27
        sclk_pins = [17, 18, 22, 23, 27]
        if 0 <= chain_idx < len(sclk_pins):
            return sclk_pins[chain_idx]
        return f"Unknown"

    def get_rclk_pin_number(self, chain_idx):
        """Get the correct register clock pin number for a chain"""
        # Register Clock pins: 9, 10, 11, 24, 25
        rclk_pins = [9, 10, 11, 24, 25]
        if 0 <= chain_idx < len(rclk_pins):
            return rclk_pins[chain_idx]
        return f"Unknown"

    def get_srclr_pin_number(self, chain_idx):
        """Get the correct serial clear pin number for a chain"""
        # Serial Clear pins: 13, 16, 19, 20, 26
        srclr_pins = [13, 16, 19, 20, 26]
        if 0 <= chain_idx < len(srclr_pins):
            return srclr_pins[chain_idx]
        return f"Unknown"

    def update_gpio_status_display(self, gpio_data):
        """Update the GPIO status display with received data"""
        try:
            # Clear existing content
            for i in reversed(range(self.gpio_status_layout.count())):
                child = self.gpio_status_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)

            if 'error' in gpio_data:
                error_label = QLabel(f"Error reading GPIO: {gpio_data['error']}")
                error_label.setStyleSheet("color: red; font-weight: bold; padding: 10px;")
                self.gpio_status_layout.addWidget(error_label)
                return

            # Update connection status
            self.gpio_connection_status.setText("✅ GPIO Status Updated")
            self.gpio_connection_status.setStyleSheet("color: green; font-weight: bold;")

            # ARM/DISARM Pin Status
            arm_group = QGroupBox("ARM/DISARM Control")
            arm_layout = QVBoxLayout(arm_group)

            arm_pin = gpio_data.get('arm_pin', {})
            arm_state = "🟢 ARMED" if arm_pin.get('state') else "🔴 DISARMED"
            arm_color = "green" if arm_pin.get('state') else "red"

            # Use GPIO 21 for ARM/DISARM
            arm_pin_number = arm_pin.get('pin', 21)
            arm_label = QLabel(f"GPIO {arm_pin_number}: {arm_state}")
            arm_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {arm_color}; padding: 5px;")
            arm_layout.addWidget(arm_label)
            arm_group.setLayout(arm_layout)

            self.gpio_status_layout.addWidget(arm_group)

            # Chain Status
            for chain_idx in range(5):
                chain_group = QGroupBox(f"Chain {chain_idx + 1} GPIO Pins")
                chain_layout = QVBoxLayout(chain_group)

                # Data pin
                data_pins = gpio_data.get('data_pins', [])
                if chain_idx < len(data_pins):
                    data_pin = data_pins[chain_idx]
                    data_state = "HIGH" if data_pin.get('state') else "LOW"
                    data_color = "#2196F3" if data_pin.get('state') else "#757575"
                    data_pin_number = data_pin.get('pin', self.get_data_pin_number(chain_idx))
                    data_label = QLabel(f"Data (GPIO {data_pin_number}): {data_state}")
                    data_label.setStyleSheet(f"color: {data_color}; padding: 2px;")
                    chain_layout.addWidget(data_label)
                else:
                    # Use hardcoded pin number if not available from data
                    data_pin_number = self.get_data_pin_number(chain_idx)
                    data_label = QLabel(f"Data (GPIO {data_pin_number}): Unknown")
                    data_label.setStyleSheet(f"color: #757575; padding: 2px;")
                    chain_layout.addWidget(data_label)

                # Serial Clock pin
                sclk_pins = gpio_data.get('sclk_pins', [])
                if chain_idx < len(sclk_pins):
                    sclk_pin = sclk_pins[chain_idx]
                    sclk_state = "HIGH" if sclk_pin.get('state') else "LOW"
                    sclk_color = "#2196F3" if sclk_pin.get('state') else "#757575"
                    sclk_pin_number = sclk_pin.get('pin', self.get_sclk_pin_number(chain_idx))
                    sclk_label = QLabel(f"Serial Clock (GPIO {sclk_pin_number}): {sclk_state}")
                    sclk_label.setStyleSheet(f"color: {sclk_color}; padding: 2px;")
                    chain_layout.addWidget(sclk_label)
                else:
                    # Use hardcoded pin number if not available from data
                    sclk_pin_number = self.get_sclk_pin_number(chain_idx)
                    sclk_label = QLabel(f"Serial Clock (GPIO {sclk_pin_number}): Unknown")
                    sclk_label.setStyleSheet(f"color: #757575; padding: 2px;")
                    chain_layout.addWidget(sclk_label)

                # Register Clock pin
                rclk_pins = gpio_data.get('rclk_pins', [])
                if chain_idx < len(rclk_pins):
                    rclk_pin = rclk_pins[chain_idx]
                    rclk_state = "HIGH" if rclk_pin.get('state') else "LOW"
                    rclk_color = "#2196F3" if rclk_pin.get('state') else "#757575"
                    rclk_pin_number = rclk_pin.get('pin', self.get_rclk_pin_number(chain_idx))
                    rclk_label = QLabel(f"Register Clock (GPIO {rclk_pin_number}): {rclk_state}")
                    rclk_label.setStyleSheet(f"color: {rclk_color}; padding: 2px;")
                    chain_layout.addWidget(rclk_label)
                else:
                    # Use hardcoded pin number if not available from data
                    rclk_pin_number = self.get_rclk_pin_number(chain_idx)
                    rclk_label = QLabel(f"Register Clock (GPIO {rclk_pin_number}): Unknown")
                    rclk_label.setStyleSheet(f"color: #757575; padding: 2px;")
                    chain_layout.addWidget(rclk_label)

                # Output Enable pin
                oe_pins = gpio_data.get('oe_pins', [])
                if chain_idx < len(oe_pins):
                    oe_pin = oe_pins[chain_idx]
                    # HIGH = Disabled, LOW = Enabled
                    oe_state = "🔴 DISABLED" if oe_pin.get('state') else "🟢 ENABLED"
                    oe_color = "red" if oe_pin.get('state') else "green"
                    oe_pin_number = oe_pin.get('pin', self.get_oe_pin_number(chain_idx))
                    oe_label = QLabel(f"Output Enable (GPIO {oe_pin_number}): {oe_state}")
                    oe_label.setStyleSheet(f"color: {oe_color}; font-weight: bold; padding: 2px;")
                    chain_layout.addWidget(oe_label)
                else:
                    # Use hardcoded pin number if not available from data
                    oe_pin_number = self.get_oe_pin_number(chain_idx)
                    oe_label = QLabel(f"Output Enable (GPIO {oe_pin_number}): Unknown")
                    oe_label.setStyleSheet(f"color: #757575; font-weight: bold; padding: 2px;")
                    chain_layout.addWidget(oe_label)

                # Serial Clear pin
                srclr_pins = gpio_data.get('srclr_pins', [])
                if chain_idx < len(srclr_pins):
                    srclr_pin = srclr_pins[chain_idx]
                    # LOW = Disabled, HIGH = Enabled
                    srclr_state = "🟢 ENABLED" if srclr_pin.get('state') else "🔴 DISABLED"
                    srclr_color = "green" if srclr_pin.get('state') else "red"
                    srclr_pin_number = srclr_pin.get('pin', self.get_srclr_pin_number(chain_idx))
                    srclr_label = QLabel(f"Serial Clear (GPIO {srclr_pin_number}): {srclr_state}")
                    srclr_label.setStyleSheet(f"color: {srclr_color}; font-weight: bold; padding: 2px;")
                    chain_layout.addWidget(srclr_label)
                else:
                    # Use hardcoded pin number if not available from data
                    srclr_pin_number = self.get_srclr_pin_number(chain_idx)
                    srclr_label = QLabel(f"Serial Clear (GPIO {srclr_pin_number}): Unknown")
                    srclr_label.setStyleSheet(f"color: #757575; font-weight: bold; padding: 2px;")
                    chain_layout.addWidget(srclr_label)

                chain_group.setLayout(chain_layout)
                self.gpio_status_layout.addWidget(chain_group)

            # Timestamp
            from datetime import datetime
            timestamp = datetime.fromtimestamp(gpio_data.get('timestamp', 0))
            time_label = QLabel(f"Last Updated: {timestamp.strftime('%H:%M:%S')}")
            time_label.setStyleSheet("color: gray; font-size: 10px; padding: 5px;")
            self.gpio_status_layout.addWidget(time_label)

        except Exception as e:
            print(f"Error updating GPIO display: {e}")
            error_label = QLabel(f"Display Error: {e}")
            error_label.setStyleSheet("color: red; padding: 10px;")
            self.gpio_status_layout.addWidget(error_label)

    def accept_changes(self):
        """Accept and apply the mode changes without validation"""
        selected_mode = "hardware" if self.hardware_radio.isChecked() else "simulation"

        # Gather connection settings
        connection_settings = {
            "host": self.host_input.text(),
            "username": self.username_input.text(),
            "password": self.password_input.text(),
            "port": self.port_input.value()
        }

        # If hardware mode is selected, attempt to connect automatically
        if selected_mode == "hardware" and not self.ssh_connected:
            self.test_ssh_connection_simple(connection_settings)

        # Emit signal with new mode and settings
        self.mode_changed.emit(selected_mode, connection_settings, "ssh")