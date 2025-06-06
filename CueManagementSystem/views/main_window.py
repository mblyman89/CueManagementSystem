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
from views.led_panel.led_grid import LedGrid
from views.dialogs.cue_creator import CueCreatorDialog
from views.dialogs.cue_editor import CueEditorDialog
from views.dialogs.music_file_dialog import MusicFileDialog
from views.dialogs.generate_show_dialog import GeneratorPromptDialog
from views.button_bar.button_bar import ButtonBar
from views.dialogs.mode_selector_dialog import ModeSelector
from controllers.system_mode import SystemMode
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
        self.cue_table.setStyleSheet("background-color: #ffffff;")

        # Connect double-click on table to edit function
        self.cue_table.doubleClicked.connect(lambda: self.edit_selected_cue())

        # LED Panel (Left)
        self.led_panel = LedGrid()
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

        # Connect button signals to actions
        self.connect_button_signals(button_bar)

        return button_bar

    def connect_button_signals(self, button_bar):
        """Connect ButtonBar signals to MainWindow actions"""
        # Connect execute/preview buttons
        button_bar.execute_all_clicked.connect(self.preview_show)

        # Connect playback control buttons
        button_bar.stop_clicked.connect(self.stop_preview)
        button_bar.pause_clicked.connect(self.pause_preview)
        button_bar.resume_clicked.connect(self.resume_preview)

        # Connect editing buttons
        button_bar.create_cue_clicked.connect(self.show_cue_creator)
        button_bar.edit_cue_clicked.connect(self.edit_selected_cue)
        button_bar.delete_cue_clicked.connect(self.delete_selected_cue)
        button_bar.delete_all_clicked.connect(self.delete_all_cues)

        # Connect additional features
        button_bar.music_clicked.connect(self.show_music_manager)
        button_bar.generate_show_clicked.connect(self.show_generator_prompt)
        button_bar.mode_clicked.connect(self.show_mode_selector)

        # Connect exit (additional handling could be added here)
        button_bar.exit_clicked.connect(self.close)

        # Connect show management features
        button_bar.save_show_clicked.connect(self.show_manager.save_show_as)
        button_bar.load_show_clicked.connect(self.show_manager.load_show)
        button_bar.import_show_clicked.connect(self.show_manager.import_show)
        button_bar.export_show_clicked.connect(self.show_manager.export_show)

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

    def show_mode_selector(self):
        """Show the system mode selector dialog"""
        print("Opening mode selector dialog")
        dialog = ModeSelector(
            current_mode=self.system_mode.get_mode(),
            connection_settings=self.system_mode.connection_settings,
            communication_method=self.system_mode.communication_method,
            parent=self
        )

        # Connect mode changed signal
        dialog.mode_changed.connect(self.queue_mode_change)

        # Show dialog
        if dialog.exec() == QDialog.Accepted:
            print("Mode selector dialog accepted")
        else:
            print("Mode selector dialog cancelled")

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
            await self.system_mode.set_mode(mode, connection_settings)
            print("Mode set successfully")

            # Schedule UI updates to run in the main thread
            self.update_mode_buttons_text()
            mode_name = "Simulation" if mode == "simulation" else "Hardware"
            self.statusBar().showMessage(f"System mode changed to: {mode_name} Mode")

            # If hardware mode, attempt connection
            if mode == "hardware":
                print("Attempting hardware connection...")
                # Create a new event loop for the connection
                connection_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(connection_loop)

                try:
                    success, message = await self.system_mode.connect_to_hardware()
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
                finally:
                    connection_loop.close()

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

        except Exception as e:
            print(f"Error showing music manager: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "Music Manager Error", f"Could not open music manager: {str(e)}")

    def show_generator_prompt(self):
        """Show the generator type selection prompt"""
        try:
            # Create and show the generator prompt dialog
            dialog = GeneratorPromptDialog(self)

            # Connect signals to handler methods
            dialog.random_show_selected.connect(self.generate_random_show)
            dialog.musical_show_selected.connect(self.generate_musical_show)

            # Show the dialog (modal)
            dialog.exec()

        except Exception as e:
            print(f"Error showing generator prompt: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "Generator Error", f"Could not open generator: {str(e)}")

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

            # Show the dialog
            dialog.exec()

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
            # Schedule cleanup
            asyncio.create_task(self._cleanup())
            # Give it a moment to complete
            self.loop.call_later(0.1, super().closeEvent, event)
        except Exception as e:
            print(f"Error during cleanup: {e}")
            super().closeEvent(event)

    async def _cleanup(self):
        """Cleanup async resources"""
        try:
            if self.system_mode:
                await self.system_mode.close_connection()
        except Exception as e:
            print(f"Error in cleanup: {e}")
