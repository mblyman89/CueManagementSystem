import asyncio
import traceback

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QScrollArea, QSizePolicy, QPushButton, QMessageBox, QDialog, QApplication,
                               QStatusBar)
from PySide6.QtCore import Qt, QTimer, QMetaObject, Q_ARG, Slot
from utils.color_utils import lighten_color, darken_color
from views.table.cue_table import CueTableView
from utils.data_utils import get_test_data
from views.led_panel.led_panel_manager import LedPanelManager
from views.dialogs.cue_creator import CueCreatorDialog
from views.dialogs.cue_editor import CueEditorDialog
from views.dialogs.music_file_dialog import MusicFileDialog
from views.dialogs.generate_show_dialog import GeneratorPromptDialog
from views.button_bar.button_bar import ButtonBar
from views.dialogs.mode_selector_dialog import ModeSelector
from controllers.system_mode import SystemMode
from views.button_bar.button_mqtt_integration import ButtonMQTTIntegration
from controllers.gpio_controller import GPIOController
from controllers.show_execution_manager import ShowExecutionManager
from controllers.music_manager import MusicManager
from controllers.show_manager import ShowManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Firework Cue Management System")
        self.showMaximized()
        self.editing_cue_index = None

        # Create an event loop for async operations
        self.loop = asyncio.get_event_loop()

        # Create managers and controllers first
        self.show_manager = ShowManager(self)
        self.system_mode = SystemMode()
        self.music_manager = MusicManager()

        # Get references to MQTT integration components from system_mode
        self.gpio_controller = self.system_mode.gpio_controller
        self.show_execution_manager = self.system_mode.show_execution_manager

        # Note: ButtonMQTTIntegration will be initialized after button_bar is created

        # Initialize UI components
        self.init_ui()

        # Load test data after UI is initialized
        self.load_test_data()

        # Initialize show preview controller after LED panel is created
        from utils.show_preview_controller import ShowPreviewController
        self.preview_controller = ShowPreviewController(self.led_panel)

        # Connect preview controller signals
        self.preview_controller.preview_started.connect(self.handle_preview_started)
        self.preview_controller.preview_ended.connect(self.handle_preview_ended)

        # Connect MQTT integration signals
        self.connect_mqtt_signals()

        # Initialize button text based on current mode
        self.update_mode_buttons_text()

        # Initialize preview control buttons to disabled state
        self.button_bar.initialize_playback_buttons()

    def init_ui(self):
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create status bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")

        # Main vertical layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Button Bar (Top, full width, scrollable)
        self.button_bar = self.create_button_bar()
        main_layout.addWidget(self.button_bar)

        # 2. Lower half with table and LED panel
        lower_half = QWidget()
        lower_layout = QHBoxLayout(lower_half)
        lower_layout.setContentsMargins(0, 0, 0, 0)
        lower_layout.setSpacing(0)

        # Create the cue_table FIRST
        self.cue_table = CueTableView()
        # Remove white background that conflicts with corner button styling
        self.cue_table.setStyleSheet("")

        # Connect double-click on table to edit function
        self.cue_table.doubleClicked.connect(lambda: self.edit_selected_cue())

        # LED Panel (Left) - Now using LED Panel Manager with dual views
        self.led_panel = LedPanelManager()
        self.led_panel.setStyleSheet("background-color: #2c3e50;")
        lower_layout.addWidget(self.led_panel, 1)  # 1:1 ratio

        self.cue_table.selectionModel().selectionChanged.connect(self.handle_cue_selection)

        # Add table to the layout (Right)
        lower_layout.addWidget(self.cue_table, 1)  # 1:1 ratio

        main_layout.addWidget(lower_half)

        self.cue_table.model.led_panel = self.led_panel

        # Set components in ShowManager after they're created
        self.show_manager.set_components(self.cue_table, self.led_panel)

    def create_button_bar(self):
        # Create a ButtonBar instance
        button_bar = ButtonBar(self)

        # Store a reference to the buttons dictionary for easy access
        self.buttons = button_bar.buttons

        # Initialize ButtonMQTTIntegration only if all components are available
        try:
            # Only create MQTT integration if we have all required components
            if hasattr(self, 'system_mode') and hasattr(self, 'gpio_controller'):
                from views.button_bar.button_mqtt_integration import ButtonMQTTIntegration
                self.button_mqtt_integration = ButtonMQTTIntegration(
                    button_bar=button_bar,
                    system_mode=self.system_mode,
                    main_window=self
                )
                print("✓ MQTT integration initialized")
            else:
                self.button_mqtt_integration = None
                print("ℹ MQTT integration not available - using simulation mode only")
        except Exception as e:
            print(f"Warning: Could not initialize MQTT integration: {e}")
            self.button_mqtt_integration = None

        # Connect button signals to actions
        self.connect_button_signals(button_bar)

        return button_bar

    def connect_button_signals(self, button_bar):
        """Connect ButtonBar signals to MainWindow actions"""
        # Connect execute/preview buttons - use mode-aware routing
        button_bar.execute_all_clicked.connect(self.handle_execute_all_button)

        # Connect playback control buttons - use mode-aware routing
        button_bar.stop_clicked.connect(self.handle_stop_button)
        button_bar.pause_clicked.connect(self.handle_pause_button)
        button_bar.resume_clicked.connect(self.handle_resume_button)

        # Connect MQTT control buttons (only if MQTT integration exists)
        # Note: enable_outputs and arm_outputs are handled by button_mqtt_integration.py
        # to avoid duplicate signal connections
        try:
            if hasattr(button_bar, 'execute_cue_clicked'):
                button_bar.execute_cue_clicked.connect(self.handle_execute_cue_button)

            # Note: execute_all_clicked is handled by handle_execute_all_button above
            # which works in both simulation and hardware modes

        except Exception as e:
            print(f"Warning: Could not connect MQTT buttons: {e}")

        # Connect editing buttons
        button_bar.create_cue_clicked.connect(self.show_cue_creator)
        button_bar.edit_cue_clicked.connect(self.edit_selected_cue)
        button_bar.delete_cue_clicked.connect(self.delete_selected_cue)
        button_bar.delete_all_clicked.connect(self.delete_all_cues)

        # Connect additional features
        button_bar.import_music_clicked.connect(self.show_music_manager)
        button_bar.generate_show_clicked.connect(self.show_generator_prompt)
        button_bar.mode_clicked.connect(self.show_mode_selector)
        button_bar.led_panel_clicked.connect(self.show_led_panel_selector)  # New LED panel button

        # Connect exit (additional handling could be added here)
        button_bar.exit_clicked.connect(self.close)

        # Connect show management features
        button_bar.save_show_clicked.connect(self.show_manager.save_show_as)
        button_bar.load_show_clicked.connect(self.show_manager.load_show)
        button_bar.import_show_clicked.connect(self.show_manager.import_show)
        button_bar.export_show_clicked.connect(self.show_manager.export_show)

    # Mode-aware button routing methods
    def handle_execute_all_button(self):
        """Execute show button - works in both simulation and hardware modes"""
        try:
            # ALWAYS show the preview on LED panel (simulation functionality)
            self.preview_show()

            # ALSO send MQTT commands if in hardware mode
            current_mode = getattr(self.system_mode, 'current_mode', 'simulation')
            if current_mode != 'simulation':
                # In hardware mode: Also execute via MQTT
                if hasattr(self, 'button_mqtt_integration') and self.button_mqtt_integration:
                    # Execute show via MQTT (sequential cue execution)
                    self.execute_show_via_mqtt()
                elif hasattr(self.system_mode, 'handle_execute_show_button'):
                    # Direct system mode execution
                    self.execute_show_via_system_mode()
                else:
                    print("Hardware execution not available - preview only")
            else:
                print("Simulation mode: Preview only")

        except Exception as e:
            print(f"Execute all button error: {e}")
            # Always ensure preview works as fallback
            try:
                self.preview_show()
            except:
                pass

    def handle_stop_button(self):
        """Route stop button based on current mode"""
        try:
            current_mode = getattr(self.system_mode, 'current_mode', 'simulation')
            if current_mode == 'simulation':
                # In simulation mode: Stop preview
                self.stop_preview()
            else:
                # In hardware mode: Abort execution
                if hasattr(self, 'button_mqtt_integration') and self.button_mqtt_integration:
                    self.button_mqtt_integration.handle_abort()
                else:
                    # Fallback to stop preview
                    self.stop_preview()
        except Exception as e:
            print(f"Stop button error: {e}")
            # Fallback to simulation mode behavior
            self.stop_preview()

    def handle_pause_button(self):
        """Route pause button based on current mode"""
        try:
            current_mode = getattr(self.system_mode, 'current_mode', 'simulation')
            if current_mode == 'simulation':
                # In simulation mode: Pause preview
                self.pause_preview()
            else:
                # In hardware mode: Pause execution
                if hasattr(self, 'button_mqtt_integration') and self.button_mqtt_integration:
                    self.button_mqtt_integration.handle_pause()
                else:
                    # Fallback to pause preview
                    self.pause_preview()
        except Exception as e:
            print(f"Pause button error: {e}")
            # Fallback to simulation mode behavior
            self.pause_preview()

    def handle_resume_button(self):
        """Route resume button based on current mode"""
        try:
            current_mode = getattr(self.system_mode, 'current_mode', 'simulation')
            if current_mode == 'simulation':
                # In simulation mode: Resume preview
                self.resume_preview()
            else:
                # In hardware mode: Resume execution
                if hasattr(self, 'button_mqtt_integration') and self.button_mqtt_integration:
                    self.button_mqtt_integration.handle_resume()
                else:
                    # Fallback to resume preview
                    self.resume_preview()
        except Exception as e:
            print(f"Resume button error: {e}")
            # Fallback to simulation mode behavior
            self.resume_preview()

    def handle_enable_outputs_button(self):
        """Handle enable outputs button (hardware mode only)"""
        import time
        timestamp = time.time()
        print(f"MainWindow: handle_enable_outputs_button called at {timestamp}")

        # Prevent double processing by checking if we're already processing
        if hasattr(self, '_processing_enable_outputs') and self._processing_enable_outputs:
            print("MainWindow: Already processing enable outputs, skipping duplicate call")
            return

        self._processing_enable_outputs = True
        try:
            if hasattr(self.system_mode, 'handle_enable_outputs_button'):
                # Get the actual state from the backend
                new_state = self.system_mode.handle_enable_outputs_button()
                print(f"MainWindow: Enable outputs button processed at {timestamp}, new state: {new_state}")

                # Update the button UI to reflect the actual backend state
                self.update_enable_outputs_button_ui(new_state)
            else:
                print("Enable outputs: Hardware mode not available")
        except Exception as e:
            print(f"Enable outputs error: {e}")
        finally:
            self._processing_enable_outputs = False

    def update_enable_outputs_button_ui(self, enabled_state):
        """Update the enable outputs button UI to reflect the actual backend state"""
        print(f"MainWindow: update_enable_outputs_button_ui called with state: {enabled_state}")
        try:
            if hasattr(self, 'button_bar') and hasattr(self.button_bar, 'update_enable_outputs_state'):
                print("MainWindow: Calling button_bar.update_enable_outputs_state")
                self.button_bar.update_enable_outputs_state(enabled_state)
                if enabled_state:
                    print("Button UI updated: DISABLE OUTPUTS (red)")
                else:
                    print("Button UI updated: ENABLE OUTPUTS (green)")
            else:
                print("Button bar update method not available")
        except Exception as e:
            print(f"Error updating enable outputs button UI: {e}")

    def handle_arm_outputs_button(self):
        """Handle arm outputs button (hardware mode only)"""
        try:
            if hasattr(self.system_mode, 'handle_arm_outputs_button'):
                # Get the actual state from the backend
                new_state = self.system_mode.handle_arm_outputs_button()
                print(f"Arm outputs button processed, new state: {new_state}")

                # Update the button UI to reflect the actual backend state
                self.update_arm_outputs_button_ui(new_state)
            else:
                print("Arm outputs: Hardware mode not available")
        except Exception as e:
            print(f"Arm outputs error: {e}")

    def update_arm_outputs_button_ui(self, armed_state):
        """Update the arm outputs button UI to reflect the actual backend state"""
        try:
            if hasattr(self, 'button_bar') and hasattr(self.button_bar, 'update_arm_outputs_state'):
                self.button_bar.update_arm_outputs_state(armed_state)
                if armed_state:
                    print("Button UI updated: DISARM OUTPUTS (red)")
                else:
                    print("Button UI updated: ARM OUTPUTS (green)")
            else:
                print("Button bar update method not available")
        except Exception as e:
            print(f"Error updating arm outputs button UI: {e}")

    def handle_execute_cue_button(self):
        """Handle execute cue button (hardware mode only)"""
        try:
            if hasattr(self.system_mode, 'handle_execute_cue_button'):
                # Get selected cue data
                selected_cue = {'cue_id': 'manual', 'name': 'Manual Cue'}
                asyncio.create_task(self.system_mode.handle_execute_cue_button(selected_cue))
            else:
                print("Execute cue: Hardware mode not available")
        except Exception as e:
            print(f"Execute cue error: {e}")

    def execute_show_via_mqtt(self):
        """Execute complete show via MQTT (sequential cue execution)"""
        try:
            # Get all cues from the table
            show_cues = self.get_all_cues_for_execution()

            if show_cues:
                print(f"Executing show via MQTT: {len(show_cues)} cues")
                # Execute via MQTT integration
                if hasattr(self.button_mqtt_integration, 'handle_execute_show'):
                    self.button_mqtt_integration.handle_execute_show(show_cues)
                else:
                    # Fallback to system mode
                    asyncio.create_task(self.system_mode.handle_execute_show_button(show_cues))
            else:
                print("No cues available for execution")

        except Exception as e:
            print(f"MQTT show execution error: {e}")

    def execute_show_via_system_mode(self):
        """Execute complete show via system mode directly"""
        try:
            # Get all cues from the table
            show_cues = self.get_all_cues_for_execution()

            if show_cues:
                print(f"Executing show via system mode: {len(show_cues)} cues")
                asyncio.create_task(self.system_mode.handle_execute_show_button(show_cues))
            else:
                print("No cues available for execution")

        except Exception as e:
            print(f"System mode show execution error: {e}")

    def get_all_cues_for_execution(self):
        """Get all cues from the cue table formatted for execution"""
        try:
            if hasattr(self, 'cue_table') and hasattr(self.cue_table, 'model'):
                # Get cues from the table model
                cues_data = getattr(self.cue_table.model, '_data', [])

                # Format cues for execution
                formatted_cues = []
                for i, cue in enumerate(cues_data):
                    formatted_cue = {
                        'cue_number': i + 1,
                        'cue_id': cue.get('cue_id', f'cue_{i + 1}'),
                        'name': cue.get('name', f'Cue {i + 1}'),
                        'outputs': cue.get('outputs', []),
                        'duration_ms': cue.get('duration_ms', 1000),
                        'delay_ms': cue.get('delay_ms', 0),
                        'description': cue.get('description', '')
                    }
                    formatted_cues.append(formatted_cue)

                return formatted_cues
            else:
                print("Cue table not available")
                return []

        except Exception as e:
            print(f"Error getting cues for execution: {e}")
            return []

    def connect_mqtt_signals(self):
        """Connect MQTT integration signals to UI updates"""
        try:
            # Connect system mode signals
            if hasattr(self.system_mode, 'connection_status_changed'):
                self.system_mode.connection_status_changed.connect(self.update_connection_status)
            if hasattr(self.system_mode, 'error_occurred'):
                self.system_mode.error_occurred.connect(self.handle_mqtt_error)
            if hasattr(self.system_mode, 'hardware_status_updated'):
                self.system_mode.hardware_status_updated.connect(self.update_hardware_status)

            # Connect button integration signals (only if button_mqtt_integration exists)
            if hasattr(self, 'button_mqtt_integration') and self.button_mqtt_integration:
                if hasattr(self.button_mqtt_integration, 'button_state_changed'):
                    self.button_mqtt_integration.button_state_changed.connect(self.update_button_state)
                if hasattr(self.button_mqtt_integration, 'execution_status_changed'):
                    self.button_mqtt_integration.execution_status_changed.connect(self.update_execution_status)
                if hasattr(self.button_mqtt_integration, 'show_progress_updated'):
                    self.button_mqtt_integration.show_progress_updated.connect(self.update_show_progress)

            # Connect show execution manager signals (use correct signal names)
            if hasattr(self, 'show_execution_manager') and self.show_execution_manager:
                if hasattr(self.show_execution_manager, 'cue_executed'):
                    self.show_execution_manager.cue_executed.connect(self.handle_cue_executed)
                if hasattr(self.show_execution_manager, 'show_completed'):
                    self.show_execution_manager.show_completed.connect(self.handle_show_completed)
                if hasattr(self.show_execution_manager, 'show_paused'):  # Correct signal name
                    self.show_execution_manager.show_paused.connect(self.handle_execution_paused)
                if hasattr(self.show_execution_manager, 'show_resumed'):  # Correct signal name
                    self.show_execution_manager.show_resumed.connect(self.handle_execution_resumed)

            # Connect GPIO controller signals (use correct signal names)
            if hasattr(self, 'gpio_controller') and self.gpio_controller:
                if hasattr(self.gpio_controller, 'gpio_state_changed'):  # Correct signal name
                    self.gpio_controller.gpio_state_changed.connect(self.handle_gpio_state_changed)
                if hasattr(self.gpio_controller, 'error_occurred'):
                    self.gpio_controller.error_occurred.connect(self.handle_gpio_error)

        except Exception as e:
            print(f"Warning: Could not connect all MQTT signals: {e}")
            # Continue without MQTT signals - maintain existing functionality

    def update_connection_status(self, connected: bool, status_message: str):
        """Update UI based on MQTT connection status"""
        if connected:
            self.statusBar().showMessage(f"MQTT Connected: {status_message}")
            self.statusBar().setStyleSheet("background-color: #2ecc71; color: white;")
        else:
            self.statusBar().showMessage(f"MQTT Disconnected: {status_message}")
            self.statusBar().setStyleSheet("background-color: #e74c3c; color: white;")

    def handle_mqtt_error(self, error_message: str):
        """Handle MQTT errors"""
        self.statusBar().showMessage(f"MQTT Error: {error_message}")
        self.statusBar().setStyleSheet("background-color: #e74c3c; color: white;")

    def update_hardware_status(self, status_data: dict):
        """Update hardware status display"""
        # Update status bar with hardware info
        if 'outputs_enabled' in status_data:
            enabled_count = sum(status_data['outputs_enabled'])
            total_count = len(status_data['outputs_enabled'])
            self.statusBar().showMessage(f"Hardware: {enabled_count}/{total_count} outputs enabled")

    def update_button_state(self, button_name: str, enabled: bool):
        """Update button enabled/disabled state"""
        if button_name in self.buttons:
            self.buttons[button_name].setEnabled(enabled)

    def update_execution_status(self, status_message: str):
        """Update execution status in UI"""
        self.statusBar().showMessage(status_message)

    def update_show_progress(self, progress_info: dict):
        """Update show execution progress"""
        if 'current_cue' in progress_info and 'total_cues' in progress_info:
            current = progress_info['current_cue']
            total = progress_info['total_cues']
            self.statusBar().showMessage(f"Show Progress: {current}/{total} cues executed")

    def handle_cue_executed(self, cue_id: int):
        """Handle individual cue execution"""
        self.statusBar().showMessage(f"Executed cue {cue_id}")

    def handle_show_completed(self):
        """Handle show completion"""
        self.statusBar().showMessage("Show execution completed")
        self.statusBar().setStyleSheet("background-color: #2ecc71; color: white;")

    def handle_execution_paused(self):
        """Handle show execution pause"""
        self.statusBar().showMessage("Show execution paused")
        self.statusBar().setStyleSheet("background-color: #f39c12; color: white;")

    def handle_execution_resumed(self):
        """Handle show execution resume"""
        self.statusBar().showMessage("Show execution resumed")
        self.statusBar().setStyleSheet("background-color: #3498db; color: white;")

    def handle_gpio_state_changed(self, pin: int, state: bool):
        """Handle GPIO pin state changes"""
        self.statusBar().showMessage(f"GPIO Pin {pin}: {'HIGH' if state else 'LOW'}")

    def handle_gpio_error(self, error_message: str):
        """Handle GPIO errors"""
        self.statusBar().showMessage(f"GPIO Error: {error_message}")
        self.statusBar().setStyleSheet("background-color: #e74c3c; color: white;")

    def load_test_data(self):
        """Load sample data into both table and LED panel for testing"""
        test_data = get_test_data()

        # Update table
        self.cue_table.model._data = test_data['cues']
        self.cue_table.model.layoutChanged.emit()

        # Update LED panel
        self.led_panel.updateFromCueData(test_data['led_panel'])

    def handle_cue_selection(self, selected, deselected):
        """Handle table selection changes"""
        if selected.indexes():
            row = selected.indexes()[0].row()
            if row < len(self.cue_table.model._data):
                cue_data = self.cue_table.model._data[row]
                self.led_panel.handle_cue_selection(cue_data)
        else:
            self.led_panel.handle_cue_selection(None)

    def show_cue_creator(self):
        """Show cue creator dialog"""
        try:
            existing_cues = self.cue_table.model._data
            dialog = CueCreatorDialog(self, existing_cues)
            dialog.cue_validated.connect(self.handle_cue_validated)

            if dialog.exec() == QDialog.Accepted:
                print("Dialog accepted")
            else:
                print("Dialog cancelled")

        except Exception as e:
            print(f"Error showing creator: {str(e)}")
            traceback.print_exc()  # Print full traceback for debugging
            QMessageBox.critical(self, "Creator Error", f"Could not open creator: {str(e)}")

    def handle_cue_validated(self, cue_data):
        """Handle validated cue data from creator"""
        try:
            # Use the formatted data for the table if available
            if "formatted_for_table" in cue_data:
                formatted_cue = cue_data["formatted_for_table"]
            else:
                # Fallback to manual formatting if not available
                cue_type = cue_data["cue_type"]
                is_run = "RUN" in cue_type

                # Process outputs differently based on cue type
                outputs_str = ""
                output_values = cue_data.get("output_values", [])

                if is_run:
                    if "DOUBLE" in cue_type:
                        # For double run, use commas for all outputs
                        outputs_str = ", ".join(map(str, output_values))
                    else:
                        # For single run, list all outputs
                        outputs_str = ", ".join(map(str, output_values))
                else:
                    # For SHOT types
                    if "DOUBLE" in cue_type:
                        if len(output_values) >= 2:
                            outputs_str = f"{output_values[0]}, {output_values[1]}"
                        else:
                            outputs_str = ", ".join(map(str, output_values))
                    else:
                        if output_values:
                            outputs_str = str(output_values[0])
                        else:
                            outputs_str = "1"  # Default

                # Get delay (0 if not present)
                delay = cue_data.get("delay", 0)

                formatted_cue = [
                    cue_data["cue_number"],
                    cue_data["cue_type"],
                    outputs_str,
                    delay,
                    cue_data["execute_time"]
                ]

            # Add new cue
            self.cue_table.model._data.append(formatted_cue)

            # Sort cues by cue number
            self.cue_table.model._data.sort(key=lambda x: x[0])

            # Update the view
            self.cue_table.model.layoutChanged.emit()

            # Update LED panel with force refresh
            self.led_panel.updateFromCueData(self.cue_table.model._data, force_refresh=True)

        except Exception as e:
            print(f"Error handling cue data: {str(e)}")
            traceback.print_exc()  # Print full traceback for debugging
            QMessageBox.critical(self, "Save Error", f"Could not save cue: {str(e)}")

    def edit_selected_cue(self):
        """Open editor for selected cue"""
        selected_rows = self.cue_table.selectionModel().selectedRows()
        if selected_rows:
            row_index = selected_rows[0].row()
            if 0 <= row_index < len(self.cue_table.model._data):
                selected_cue_data = self.cue_table.model._data[row_index]  # Original list data

                # Create a dictionary with only the fields that exist in the data
                cue_data_dict = {
                    "cue_number": selected_cue_data[0] if len(selected_cue_data) > 0 else "",
                    "cue_type": selected_cue_data[1] if len(selected_cue_data) > 1 else "",
                    "outputs": selected_cue_data[2] if len(selected_cue_data) > 2 else "",
                    "delay": selected_cue_data[3] if len(selected_cue_data) > 3 else 0,
                    "execute_time": selected_cue_data[4] if len(selected_cue_data) > 4 else ""
                }

                # Only add duration if it exists
                if len(selected_cue_data) > 5:
                    cue_data_dict["duration"] = selected_cue_data[5]

                # Parse output values if they exist
                if len(selected_cue_data) > 2 and selected_cue_data[2]:
                    try:
                        output_str = str(selected_cue_data[2])
                        output_values = []
                        # Handle different output formats (comma or semicolon separated)
                        if ";" in output_str:
                            # Handle paired outputs
                            for pair in output_str.split(";"):
                                for value in pair.split(","):
                                    if value.strip() and value.strip().isdigit():
                                        output_values.append(int(value.strip()))
                        else:
                            # Handle comma-separated outputs
                            for value in output_str.split(","):
                                if value.strip() and value.strip().isdigit():
                                    output_values.append(int(value.strip()))

                        cue_data_dict["output_values"] = output_values
                    except Exception as e:
                        print(f"Error parsing output values: {str(e)}")
                        cue_data_dict["output_values"] = []

                try:
                    # Get all cues *except* the one being edited
                    existing_cues = [cue for i, cue in enumerate(self.cue_table.model._data) if i != row_index]

                    dialog = CueEditorDialog(self, existing_cues, cue_data_dict)  # Pass the dictionary
                    dialog.cue_edited.connect(lambda data: self.handle_edited_cue(data, row_index))

                    if dialog.exec() == QDialog.Accepted:
                        print("Cue edited successfully")
                    else:
                        print("Edit cancelled")

                except Exception as e:
                    print(f"Error editing cue: {str(e)}")
                    traceback.print_exc()
                    QMessageBox.critical(self, "Edit Error", f"Could not edit cue: {str(e)}")
        else:
            QMessageBox.warning(self, "No Selection", "Please select a cue to edit")

    def _get_selected_cue(self):
        """Returns the currently selected cue data or None"""
        selection = self.cue_table.selectionModel()
        if not selection.hasSelection():
            return None

        selected_rows = selection.selectedRows()
        if not selected_rows:
            return None

        row = selected_rows[0].row()
        if 0 <= row < len(self.cue_table.model._data):
            return self.cue_table.model._data[row]
        return None

    def _get_selected_row(self):
        """Returns the currently selected row or -1 if none"""
        selection = self.cue_table.selectionModel()
        if not selection.hasSelection():
            return -1

        selected_rows = selection.selectedRows()
        if not selected_rows:
            return -1

        return selected_rows[0].row()

    def handle_edited_cue(self, cue_data, row_index):
        """Handle edited cue data from editor"""
        try:
            if "formatted_for_table" in cue_data:
                # First clean up any existing LEDs by stopping any active animations
                self.led_panel.animation_controller.stop_animation()

                # Replace the cue in the data model
                self.cue_table.model._data[row_index] = cue_data["formatted_for_table"]

                # Sort cues by cue number
                self.cue_table.model._data.sort(key=lambda x: x[0])

                # Update the view
                self.cue_table.model.layoutChanged.emit()

                # Clear all LEDs before updating with new data
                for led_number in self.led_panel.leds:
                    self.led_panel.leds[led_number].setState(None)

                # Update LED panel - force complete refresh
                self.led_panel.updateFromCueData(self.cue_table.model._data, force_refresh=True)

                # Process any pending events to ensure UI updates properly
                QApplication.processEvents()

        except Exception as e:
            print(f"Error handling edited cue: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "Save Error", f"Could not save edited cue: {str(e)}")

    def delete_selected_cue(self):
        """Delete the currently selected cue"""
        try:
            # Get the selected cue data
            selected_cue = self._get_selected_cue()

            if not selected_cue:
                QMessageBox.warning(self, "No Selection", "Please select a cue to delete")
                return

            # Show confirmation dialog
            cue_number = selected_cue[0]
            confirm = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete Cue #{cue_number}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if confirm == QMessageBox.Yes:
                # Perform the deletion
                if self.cue_table.delete_selected_cue():
                    print(f"Cue #{cue_number} deleted successfully")

                    # Stop any active animations
                    self.led_panel.animation_controller.stop_animation()

                    # Clear LEDs and update with new data
                    for led_number in self.led_panel.leds:
                        self.led_panel.leds[led_number].setState(None)

                    # Update LED panel with force refresh
                    self.led_panel.updateFromCueData(self.cue_table.model._data, force_refresh=True)
                else:
                    QMessageBox.warning(self, "Delete Failed", "Could not delete the selected cue")

        except Exception as e:
            print(f"Error deleting cue: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "Delete Error", f"Error deleting cue: {str(e)}")

    def delete_all_cues(self):
        """Delete all cues from the table"""
        try:
            # Check if there are any cues to delete
            if not self.cue_table.model._data:
                QMessageBox.information(self, "No Cues", "There are no cues to delete")
                return

            # Show confirmation dialog
            confirm = QMessageBox.question(
                self,
                "Confirm Delete All",
                "Are you sure you want to delete ALL cues? This action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if confirm == QMessageBox.Yes:
                # Perform the deletion
                if self.cue_table.delete_all_cues():
                    print("All cues deleted successfully")

                    # Stop any active animations
                    self.led_panel.animation_controller.stop_animation()

                    # Clear LEDs
                    for led_number in self.led_panel.leds:
                        self.led_panel.leds[led_number].setState(None)
                else:
                    QMessageBox.warning(self, "Delete Failed", "Could not delete all cues")

        except Exception as e:
            print(f"Error deleting all cues: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "Delete Error", f"Error deleting all cues: {str(e)}")

    def show_led_panel_selector(self):
        """Show the LED panel view selector dialog"""
        try:
            # Import the LED selector dialog
            from views.dialogs.led_selector_dialog import LedSelectorDialog

            # Get current view from LED panel manager
            current_view = self.led_panel.get_current_view_name()

            # Create and show dialog
            dialog = LedSelectorDialog(self, current_view)
            dialog.view_changed.connect(self.handle_led_panel_view_change)

            dialog.exec()

        except Exception as e:
            print(f"Error showing LED panel selector: {str(e)}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "LED Panel Error", f"Could not open LED panel selector: {str(e)}")

    def handle_led_panel_view_change(self, new_view):
        """Handle LED panel view change"""
        try:
            if new_view.startswith("preview_"):
                # Handle preview mode
                preview_view = new_view.replace("preview_", "")
                print(f"Previewing LED panel view: {preview_view}")
                # You could implement temporary preview here if desired
            else:
                # Handle permanent view change
                print(f"Changing LED panel view to: {new_view}")
                self.led_panel.switch_to_view(new_view)

                # Update LED PANEL button text
                if hasattr(self, 'button_bar') and hasattr(self.button_bar, 'update_led_panel_button'):
                    self.button_bar.update_led_panel_button(new_view)

                # Update status bar
                self.statusBar().showMessage(f"LED panel view changed to: {new_view.title()}")

        except Exception as e:
            print(f"Error changing LED panel view: {str(e)}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "View Change Error", f"Could not change LED panel view: {str(e)}")

    def show_mode_selector(self):
        """Show the system mode selector dialog"""
        # Prevent multiple dialog instances
        if hasattr(self, '_mode_dialog_open') and self._mode_dialog_open:
            print("Mode selector dialog already open, ignoring request")
            return

        print("Opening mode selector dialog")
        self._mode_dialog_open = True

        try:
            dialog = ModeSelector(
                current_mode=self.system_mode.get_mode(),
                connection_settings=self.system_mode.connection_settings,
                communication_method=self.system_mode.communication_method,
                parent=self
            )

            # Connect mode changed signal
            dialog.mode_changed.connect(self.queue_mode_change)

            # Connect professional MQTT config changes
            if hasattr(dialog, 'professional_mqtt_config_changed'):
                dialog.professional_mqtt_config_changed.connect(self.handle_professional_mqtt_config)

            # Show dialog
            result = dialog.exec()

            if result == QDialog.Accepted:
                print("Mode selector dialog accepted")

                # Handle professional MQTT configuration if available
                if hasattr(dialog, 'professional_mqtt_config'):
                    try:
                        self.system_mode.configure_professional_mqtt(dialog.professional_mqtt_config)
                        self.statusBar().showMessage("Professional MQTT configuration updated")
                    except Exception as e:
                        self.statusBar().showMessage(f"MQTT Config Error: {str(e)}")
                        self.statusBar().setStyleSheet("background-color: #e74c3c; color: white;")
            else:
                print("Mode selector dialog cancelled")

        finally:
            # Always reset the flag when dialog is closed
            self._mode_dialog_open = False

    def handle_professional_mqtt_config(self, config: dict):
        """Handle professional MQTT configuration changes"""
        try:
            self.system_mode.configure_professional_mqtt(config)
            self.statusBar().showMessage("Professional MQTT configuration updated")
        except Exception as e:
            self.statusBar().showMessage(f"MQTT Config Error: {str(e)}")
            self.statusBar().setStyleSheet("background-color: #e74c3c; color: white;")

    def queue_mode_change(self, mode, connection_settings, communication_method="mqtt"):
        """Queue the mode change operation"""
        print(f"Queueing mode change to: {mode}")
        print(f"Connection settings: {connection_settings}")
        print(f"Communication method: {communication_method}")
        asyncio.create_task(self._safe_mode_change(mode, connection_settings, communication_method))

    async def _safe_mode_change(self, mode, connection_settings, communication_method="mqtt"):
        """Safely handle mode changes with proper error handling"""
        try:
            print(f"Starting mode change to: {mode}")
            print(f"Using communication method: {communication_method}")

            # Set the communication method first
            self.system_mode.set_communication_method(communication_method)

            # Then update the system mode
            result = await self.system_mode.set_mode(mode, connection_settings)
            print(f"Mode set successfully, result: {result}")

            # Schedule UI updates to run in the main thread
            self.update_mode_buttons_text()
            mode_name = "Simulation" if mode == "simulation" else "Hardware"
            self.statusBar().showMessage(f"System mode changed to: {mode_name} Mode")

            # If hardware mode, attempt connection
            if mode == "hardware":
                print("Attempting hardware connection...")
                try:
                    # Use the existing event loop instead of creating a new one
                    connection_result = await self.system_mode.connect_to_hardware()
                    if connection_result is None:
                        print("Warning: connect_to_hardware returned None")
                        success, message = False, "Connection method returned None"
                    else:
                        success, message = connection_result
                    print(f"Connection attempt result: {success}, {message}")

                    # Schedule UI updates back in the main thread
                    if success:
                        QMetaObject.invokeMethod(self, "_show_success_message",
                                                 Qt.ConnectionType.QueuedConnection,
                                                 Q_ARG(str, connection_settings['host']),
                                                 Q_ARG(str, message))
                    else:
                        QMetaObject.invokeMethod(self, "_show_warning_message",
                                                 Qt.ConnectionType.QueuedConnection,
                                                 Q_ARG(str, message))
                except Exception as connection_error:
                    print(f"Error during hardware connection: {connection_error}")
                    QMetaObject.invokeMethod(self, "_show_error_message",
                                             Qt.ConnectionType.QueuedConnection,
                                             Q_ARG(str, f"Connection failed: {str(connection_error)}"))

        except Exception as e:
            print(f"Error in _safe_mode_change: {str(e)}")
            QMetaObject.invokeMethod(self, "_show_error_message",
                                     Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(str, str(e)))

    @Slot(str, dict)
    def _update_ui_after_mode_change(self, mode, connection_settings):
        """Update UI elements after mode change (runs in UI thread)"""
        try:
            # Update mode-related buttons text
            self.update_mode_buttons_text()

            # Update UI or status based on mode
            mode_name = "Simulation" if mode == "simulation" else "Hardware"
            self.statusBar().showMessage(f"System mode changed to: {mode_name} Mode")

            # If hardware mode, initiate connection
            if mode == "hardware":
                self.loop.create_task(self._handle_hardware_connection(connection_settings))

        except Exception as e:
            self._show_error_dialog(str(e))

    async def _handle_hardware_connection(self, connection_settings):
        """Handle hardware connection separately"""
        try:
            success, message = await self.system_mode.connect_to_hardware()

            # Update UI safely
            QMetaObject.invokeMethod(self, "_show_connection_result",
                                     Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(bool, success),
                                     Q_ARG(str, message),
                                     Q_ARG(dict, connection_settings))

        except Exception as e:
            QMetaObject.invokeMethod(self, "_show_error_dialog",
                                     Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(str, str(e)))

    @Slot(bool, str, dict)
    def _show_connection_result(self, success, message, connection_settings):
        """Show connection result in UI thread"""
        if success:
            QMessageBox.information(
                self,
                "Hardware Mode Activated",
                f"Connected to: {connection_settings['host']}\n"
                f"Connection status: {message}"
            )
        else:
            QMessageBox.warning(
                self,
                "Hardware Mode Warning",
                f"Connection issue: {message}"
            )

    @Slot(str)
    def _show_error_dialog(self, error_message):
        """Show error dialog in UI thread"""
        QMessageBox.critical(
            self,
            "Error",
            f"An error occurred: {error_message}"
        )

    def update_mode_buttons_text(self):
        """Update button text to reflect current system mode"""
        try:
            # Get current mode
            mode = self.system_mode.get_mode()
            print(f"Updating buttons for mode: {mode}")

            is_simulation_mode = mode == "simulation"

            # Update button bar if it exists
            if hasattr(self, 'button_bar'):
                if hasattr(self.button_bar, 'update_mode_buttons'):
                    self.button_bar.update_mode_buttons(is_simulation_mode)
                elif hasattr(self.button_bar, 'buttons'):
                    # Update button text manually if possible
                    if 'EXECUTE ALL' in self.button_bar.buttons:
                        label = "PREVIEW" if is_simulation_mode else "EXECUTE\nALL"
                        self.button_bar.buttons['EXECUTE ALL'].setText(label)

                    if 'MODE' in self.button_bar.buttons:
                        label = "SIMULATION\nMODE" if is_simulation_mode else "HARDWARE\nMODE"
                        self.button_bar.buttons['MODE'].setText(label)
                        print(f"Updated MODE button to: {label}")

        except Exception as e:
            print(f"Error updating mode buttons: {str(e)}")

    @Slot(str, str)
    def _show_success_message(self, host, message):
        """Show success message in the main thread"""
        QMessageBox.information(
            self,
            "Hardware Mode Activated",
            f"Connected to: {host}\n"
            f"Connection status: {message}"
        )

    @Slot(str)
    def _show_warning_message(self, message):
        """Show warning message in the main thread"""
        QMessageBox.warning(
            self,
            "Hardware Mode Warning",
            f"Connection issue: {message}"
        )

    @Slot(str)
    def _show_error_message(self, error_message):
        """Show error message in the main thread"""
        QMessageBox.critical(
            self,
            "Mode Change Error",
            f"Error changing mode: {error_message}"
        )

    def show_music_manager(self):
        """Show the music file manager dialog"""
        try:
            # Create and show the music file dialog with the music manager
            dialog = MusicFileDialog(self, self.music_manager)

            # Show the dialog
            dialog.exec()

            # Explicitly delete the dialog after it's closed to prevent it from reappearing
            dialog.deleteLater()

        except Exception as e:
            print(f"Error showing music manager: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "Music Manager Error", f"Could not open music manager: {str(e)}")

    def show_generator_prompt(self):
        """Show the generator type selection prompt"""
        try:
            # Create and show the generator prompt dialog
            dialog = GeneratorPromptDialog(self)

            # Connect signals to handler methods with dialog cleanup
            dialog.random_show_selected.connect(lambda: self._handle_random_show_selection(dialog))
            dialog.musical_show_selected.connect(lambda: self._handle_musical_show_selection(dialog))

            # Show the dialog (non-modal to prevent blocking)
            dialog.show()

        except Exception as e:
            print(f"Error showing generator prompt: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "Generator Error", f"Could not open generator: {str(e)}")

    def _handle_random_show_selection(self, dialog):
        """Handle random show selection and cleanup dialog"""
        try:
            # Close and delete the dialog immediately
            dialog.close()
            dialog.deleteLater()

            # Generate the random show
            self.generate_random_show()

        except Exception as e:
            print(f"Error handling random show selection: {str(e)}")
            traceback.print_exc()

    def _handle_musical_show_selection(self, dialog):
        """Handle musical show selection and cleanup dialog"""
        try:
            # Close and delete the dialog immediately
            dialog.close()
            dialog.deleteLater()

            # Generate the musical show
            self.generate_musical_show()

        except Exception as e:
            print(f"Error handling musical show selection: {str(e)}")
            traceback.print_exc()

    def generate_random_show(self):
        """Generate a random show with parameters from dialog"""
        try:
            # Import here to prevent circular imports
            from views.dialogs.generate_show_dialog import RandomShowConfigDialog

            # Create and show configuration dialog
            config_dialog = RandomShowConfigDialog(self)
            config_dialog.config_completed.connect(self.process_random_show_config)

            # Show the dialog
            config_dialog.exec()

            # Explicitly delete the dialog after it's closed to prevent it from reappearing
            config_dialog.deleteLater()

        except Exception as e:
            print(f"Error generating random show: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "Generator Error", f"Could not generate random show: {str(e)}")

    def process_random_show_config(self, config_data):
        """Process the configuration data and generate the random show"""
        try:
            # Import the show generator
            from utils.show_generator import ShowGenerator

            # Create a generator and generate the show
            generator = ShowGenerator()
            generated_cues = generator.generate_random_show(config_data)

            if not generated_cues:
                QMessageBox.warning(self, "Generation Failed",
                                    "Failed to generate cues with the given parameters.")
                return

            # Ask user for confirmation before adding cues
            num_cues = len(generated_cues)
            confirm = QMessageBox.question(
                self,
                "Confirm Show Generation",
                f"Generated {num_cues} cues. Do you want to add them to your show?\n\n"
                f"Note: This will replace any existing cues.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if confirm == QMessageBox.Yes:
                # Clear existing cues
                self.cue_table.delete_all_cues()

                # Add the new cues to the table
                for cue in generated_cues:
                    self.cue_table.model._data.append(cue)

                # Update the table view
                self.cue_table.model.layoutChanged.emit()

                # Update LED panel with force refresh
                self.led_panel.updateFromCueData(self.cue_table.model._data, force_refresh=True)

                QMessageBox.information(self, "Show Generated",
                                        f"Successfully generated a {config_data.duration_minutes}:{config_data.duration_seconds:02d} show "
                                        f"with {num_cues} cues using {config_data.num_outputs} outputs.")

        except Exception as e:
            print(f"Error generating random show: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "Generator Error", f"Could not generate show: {str(e)}")

    def generate_musical_show(self):
        """Generate a show synchronized with music"""
        try:
            # Import the Music Analysis Dialog
            from views.dialogs.music_analysis_dialog import MusicAnalysisDialog

            # Create the dialog with references to LED panel and cue table
            dialog = MusicAnalysisDialog(self, self.led_panel, self.cue_table)

            # Connect the analysis_ready signal to handle the results
            dialog.analysis_ready.connect(self.handle_music_analysis)

            # Show the dialog (non-modal to prevent blocking)
            dialog.show()

            # Note: Dialog will be deleted when closed by user

        except Exception as e:
            print(f"Error generating musical show: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "Generator Error", f"Could not generate musical show: {str(e)}")

    def preview_show(self, is_hardware_execution=False):
        """
        Preview the entire show on the LED panel

        Args:
            is_hardware_execution (bool): Whether this preview is accompanying hardware execution
        """
        try:
            # Check if there are any cues to preview
            if not self.cue_table.model._data:
                QMessageBox.information(self, "No Cues", "There are no cues to preview. Please add cues first.")
                return

            # Import the music selection dialog
            from views.dialogs.music_selection_dialog import MusicSelectionDialog

            # Show music selection dialog with the existing music manager
            music_dialog = MusicSelectionDialog(self, self.music_manager)
            music_dialog.music_selected.connect(self._start_preview_with_music)

            # If dialog is rejected, don't start the preview
            if music_dialog.exec() != QDialog.Accepted:
                return

        except Exception as e:
            print(f"Error preparing show preview: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "Preview Error", f"Could not prepare show preview: {str(e)}")

    def _start_preview_with_music(self, music_file_info):
        """
        Start the preview with selected music file

        Args:
            music_file_info (dict or None): Information about the selected music file,
                                           or None if no music was selected
        """
        try:
            # Load cues into the preview controller
            self.preview_controller.load_cues(self.cue_table.model._data)

            # Play music if selected
            if music_file_info:
                music_name = f"{music_file_info['name']}{music_file_info['extension']}"
                status_message = f"Show preview started with music: {music_name}"

                # Set the music file path in the preview controller
                self.preview_controller.set_music_file(music_file_info['path'])

                # Play the music file using the music manager
                self.music_manager.preview_music(music_file_info['path'], volume=0.7)
                print(f"Playing music: {music_file_info['path']}")
            else:
                status_message = "Show preview started (no music)"

            # Start the preview
            if self.preview_controller.start_preview():
                # Update UI to reflect preview state
                self.statusBar().showMessage(status_message)
            else:
                QMessageBox.warning(self, "Preview Failed", "Could not start the show preview.")

        except Exception as e:
            print(f"Error starting show preview: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "Preview Error", f"Could not start show preview: {str(e)}")

    def stop_preview(self):
        """Stop the show preview"""
        try:
            # Check if preview controller exists and is active
            preview_active = False

            # Safely check preview controller state
            if hasattr(self.preview_controller, 'is_playing'):
                preview_active = preview_active or self.preview_controller.is_playing

            if hasattr(self.preview_controller, 'is_paused'):
                preview_active = preview_active or self.preview_controller.is_paused

            if not preview_active:
                print("Cannot stop: no preview is active")
                return

            # Stop the preview
            self.preview_controller.stop_preview()

            # Stop any playing music
            self.music_manager.stop_preview()

            # Update button states
            self.button_bar.handle_preview_ended()
            self.button_bar.update_playback_button_states()

            self.statusBar().showMessage("Show preview stopped")

        except Exception as e:
            print(f"Error stopping preview: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "Stop Error", f"Could not stop preview: {str(e)}")

    def pause_preview(self):
        """Pause the show preview"""
        try:
            # Check if preview controller exists and is playing
            preview_playing = False

            # Safely check if the preview is playing
            if hasattr(self.preview_controller, 'is_playing'):
                preview_playing = self.preview_controller.is_playing

            if not preview_playing:
                print("Cannot pause: preview is not active")
                return

            # Pause the preview
            self.preview_controller.pause_preview()

            # Pause music playback
            self.music_manager.pause_preview()

            # Update button bar states
            self.button_bar.handle_preview_paused()
            self.button_bar.update_playback_button_states()

            # Update status bar
            self.statusBar().showMessage("Show preview paused")

        except Exception as e:
            print(f"Error pausing preview: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "Pause Error", f"Could not pause preview: {str(e)}")

    def resume_preview(self):
        """Resume the show preview"""
        try:
            # Check if preview controller exists and is paused
            preview_paused = False

            # Safely check if the preview is paused
            if hasattr(self.preview_controller, 'is_paused'):
                preview_paused = self.preview_controller.is_paused

            if not preview_paused:
                print("Cannot resume: preview is not paused")
                return

            # Resume the preview
            self.preview_controller.resume_preview()

            # Resume music playback
            self.music_manager.resume_preview()

            # Update button bar states
            self.button_bar.handle_preview_resumed()
            self.button_bar.update_playback_button_states()

            # Update status bar
            self.statusBar().showMessage("Show preview resumed")

        except Exception as e:
            print(f"Error resuming preview: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "Resume Error", f"Could not resume preview: {str(e)}")

    def handle_preview_started(self):
        """Handle preview started signal"""
        # Update button bar states
        self.button_bar.handle_preview_started()

        # Ensure button states are properly updated
        self.button_bar.update_playback_button_states()

        # Update status bar
        self.statusBar().showMessage("Show preview started")

    def handle_preview_ended(self):
        """Handle preview ended signal"""
        # Update button bar states
        self.button_bar.handle_preview_ended()

        # Ensure button states are properly updated
        self.button_bar.update_playback_button_states()

        # Stop any playing music
        self.music_manager.stop_preview()

        # Update status bar
        self.statusBar().showMessage("Show preview completed")

    def handle_music_analysis(self, analysis_data):
        """Handle the results from music analysis dialog"""
        try:
            if not analysis_data:
                return

            music_file_info = analysis_data.get('music_file')
            if not music_file_info:
                return

            # Show confirmation with file information please.
            QMessageBox.information(
                self,
                "Music Analysis Complete",
                f"Analysis complete for: {music_file_info.get('filename', 'Unknown')}"
            )

        except Exception as e:
            print(f"Error handling music analysis: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "Analysis Error", f"Could not process music analysis: {str(e)}")

    def closeEvent(self, event):
        """Handle application closing"""
        try:
            print("Application closing - starting cleanup")

            # Perform synchronous cleanup to avoid event loop issues
            if self.system_mode:
                self.system_mode.close_connection_sync()

            # Cleanup MQTT integration components
            self.cleanup_mqtt_integration()

            print("Cleanup completed successfully")
            super().closeEvent(event)
        except Exception as e:
            print(f"Error during cleanup: {e}")
            super().closeEvent(event)

    async def _cleanup(self):
        """Cleanup async resources (deprecated - use synchronous cleanup in closeEvent)"""
        try:
            if self.system_mode:
                await self.system_mode.close_connection()

            # Cleanup MQTT integration components
            self.cleanup_mqtt_integration()
        except Exception as e:
            print(f"Error in cleanup: {e}")

    def cleanup_mqtt_integration(self):
        """Cleanup MQTT integration components"""
        try:
            # Disconnect MQTT
            if hasattr(self.system_mode, 'disconnect_professional_mqtt'):
                self.system_mode.disconnect_professional_mqtt()

            # Cleanup GPIO
            if hasattr(self.gpio_controller, 'cleanup'):
                self.gpio_controller.cleanup()

            # Stop show execution
            if hasattr(self.show_execution_manager, 'stop_execution'):
                self.show_execution_manager.stop_execution()

            print("MQTT integration cleaned up successfully")
        except Exception as e:
            print(f"Error during MQTT cleanup: {e}")

