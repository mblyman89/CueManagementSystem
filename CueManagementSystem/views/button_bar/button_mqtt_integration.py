"""
Button-MQTT Integration for Large-Scale Firework Control

This module connects the button bar UI to the MQTT system for:
- 1000 cue management
- 1000 output control
- GPIO state management
- Show execution control
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox, QApplication


class ButtonMQTTIntegration(QObject):
    """
    Integration between button bar and MQTT system

    Handles all button clicks and translates them to MQTT commands
    for the large-scale firework control system.
    """

    # Signals for UI updates
    button_state_changed = Signal(str, bool)  # button_name, enabled
    execution_status_changed = Signal(str)  # status_message
    show_progress_updated = Signal(dict)  # progress_info

    def __init__(self, button_bar, system_mode, main_window=None):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # Components
        self.button_bar = button_bar
        self.system_mode = system_mode
        self.main_window = main_window

        # State tracking
        self.outputs_enabled = False
        self.system_armed = False
        self.show_running = False
        self.show_paused = False
        self.current_wifi_mode = "WiFi"

        # Connect button signals to handlers
        self._connect_button_signals()

        # Connect system mode signals to UI updates
        self._connect_system_signals()

        self.logger.info("Button-MQTT Integration initialized")

    def _connect_button_signals(self):
        """Connect button bar signals to handler methods"""
        try:
            # Core control buttons
            self.button_bar.enable_outputs.connect(self.handle_enable_outputs)
            self.button_bar.arm_outputs.connect(self.handle_arm_outputs)
            self.button_bar.execute_cue_clicked.connect(self.handle_execute_cue)
            self.button_bar.execute_all_clicked.connect(self.handle_execute_show)

            # Show control buttons
            self.button_bar.stop_clicked.connect(self.handle_abort)
            self.button_bar.pause_clicked.connect(self.handle_pause)
            self.button_bar.resume_clicked.connect(self.handle_resume)

            # Mode button
            # Note: mode_clicked is already connected to main_window.show_mode_selector
            # self.button_bar.mode_clicked.connect(self.handle_mode_selector)  # Removed to prevent duplicate calls

            self.logger.info("Button signals connected successfully")

        except Exception as e:
            self.logger.error(f"Failed to connect button signals: {e}")

    def _connect_system_signals(self):
        """Connect system mode signals to UI update methods"""
        try:
            # GPIO controller signals
            if hasattr(self.system_mode, 'gpio_controller'):
                self.system_mode.gpio_controller.gpio_state_changed.connect(self._on_gpio_state_changed)
                self.system_mode.gpio_controller.system_state_changed.connect(self._on_system_state_changed)

            # Show execution manager signals
            if hasattr(self.system_mode, 'show_execution_manager'):
                self.system_mode.show_execution_manager.show_started.connect(self._on_show_started)
                self.system_mode.show_execution_manager.show_completed.connect(self._on_show_completed)
                self.system_mode.show_execution_manager.show_paused.connect(self._on_show_paused)
                self.system_mode.show_execution_manager.show_resumed.connect(self._on_show_resumed)
                self.system_mode.show_execution_manager.show_aborted.connect(self._on_show_aborted)
                self.system_mode.show_execution_manager.progress_updated.connect(self._on_progress_updated)

            # MQTT signals
            self.system_mode.connection_status_changed.connect(self._on_mqtt_status_changed)
            self.system_mode.error_occurred.connect(self._on_system_error)

            self.logger.info("System signals connected successfully")

        except Exception as e:
            self.logger.error(f"Failed to connect system signals: {e}")

    # Button Handler Methods

    def handle_enable_outputs(self):
        """Handle Enable/Disable Outputs button click"""
        try:
            self.logger.info("Enable/Disable Outputs button clicked")

            # Call system mode handler
            new_state = self.system_mode.handle_enable_outputs_button()
            self.outputs_enabled = new_state

            # Update button text and state
            if "ENABLE OUTPUTS" in self.button_bar.buttons:
                button = self.button_bar.buttons["ENABLE OUTPUTS"]
                if new_state:
                    button.setText("DISABLE\nOUTPUTS")
                    button.set_selected(True)
                else:
                    button.setText("ENABLE\nOUTPUTS")
                    button.set_selected(False)

            # Update status
            status = f"Outputs {'ENABLED' if new_state else 'DISABLED'}"
            self.execution_status_changed.emit(status)

            # If disabling outputs, also update arm button
            if not new_state and self.system_armed:
                self.system_armed = False
                if "ARM OUTPUTS" in self.button_bar.buttons:
                    arm_button = self.button_bar.buttons["ARM OUTPUTS"]
                    arm_button.setText("ARM\nOUTPUTS")
                    arm_button.set_selected(False)

        except Exception as e:
            self.logger.error(f"Failed to handle enable outputs: {e}")
            self._show_error_message("Enable Outputs Error", str(e))

    def handle_arm_outputs(self):
        """Handle Arm/Disarm Outputs button click"""
        try:
            self.logger.info("Arm/Disarm Outputs button clicked")

            # Check if outputs are enabled first
            if not self.outputs_enabled:
                self._show_error_message(
                    "Cannot Arm System",
                    "Outputs must be enabled before arming the system."
                )
                return

            # Call system mode handler
            new_state = self.system_mode.handle_arm_outputs_button()
            self.system_armed = new_state

            # Update button text and state
            if "ARM OUTPUTS" in self.button_bar.buttons:
                button = self.button_bar.buttons["ARM OUTPUTS"]
                if new_state:
                    button.setText("DISARM\nOUTPUTS")
                    button.set_selected(True)
                else:
                    button.setText("ARM\nOUTPUTS")
                    button.set_selected(False)

            # Update status
            status = f"System {'ARMED' if new_state else 'DISARMED'}"
            self.execution_status_changed.emit(status)

        except Exception as e:
            self.logger.error(f"Failed to handle arm outputs: {e}")
            self._show_error_message("Arm Outputs Error", str(e))

    def handle_execute_cue(self):
        """Handle Execute Cue button click"""
        try:
            self.logger.info("Execute Cue button clicked")

            # Get selected cue from main window
            selected_cue = self._get_selected_cue()
            if not selected_cue:
                self._show_error_message(
                    "No Cue Selected",
                    "Please select a cue from the table before executing."
                )
                return

            # Check system readiness
            if not self._check_system_ready_for_execution():
                return

            # Execute the cue asynchronously
            asyncio.create_task(self._execute_single_cue(selected_cue))

        except Exception as e:
            self.logger.error(f"Failed to handle execute cue: {e}")
            self._show_error_message("Execute Cue Error", str(e))

    def handle_execute_show(self):
        """Handle Execute Show button click"""
        try:
            self.logger.info("Execute Show button clicked")

            # Get all cues from main window
            show_cues = self._get_all_cues()
            if not show_cues:
                self._show_error_message(
                    "No Cues Available",
                    "Please load cues into the table before executing a show."
                )
                return

            # Check system readiness
            if not self._check_system_ready_for_execution():
                return

            # Confirm show execution
            reply = QMessageBox.question(
                self.main_window,
                "Confirm Show Execution",
                f"Execute show with {len(show_cues)} cues?\n\n"
                f"This will fire all cues in sequence.\n"
                f"Make sure the area is clear and safe.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Execute the show asynchronously
                asyncio.create_task(self._execute_full_show(show_cues))

        except Exception as e:
            self.logger.error(f"Failed to handle execute show: {e}")
            self._show_error_message("Execute Show Error", str(e))

    def handle_pause(self):
        """Handle Pause button click"""
        try:
            self.logger.info("Pause button clicked")

            if not self.show_running:
                self._show_error_message("Cannot Pause", "No show is currently running.")
                return

            success = self.system_mode.handle_pause_button()
            if success:
                self.show_paused = True
                self._update_show_control_buttons()
                self.execution_status_changed.emit("Show PAUSED")

        except Exception as e:
            self.logger.error(f"Failed to handle pause: {e}")
            self._show_error_message("Pause Error", str(e))

    def handle_resume(self):
        """Handle Resume button click"""
        try:
            self.logger.info("Resume button clicked")

            if not self.show_paused:
                self._show_error_message("Cannot Resume", "No show is currently paused.")
                return

            success = self.system_mode.handle_resume_button()
            if success:
                self.show_paused = False
                self._update_show_control_buttons()
                self.execution_status_changed.emit("Show RESUMED")

        except Exception as e:
            self.logger.error(f"Failed to handle resume: {e}")
            self._show_error_message("Resume Error", str(e))

    def handle_abort(self):
        """Handle Abort button click"""
        try:
            self.logger.info("Abort button clicked")

            # Confirm abort
            reply = QMessageBox.question(
                self.main_window,
                "Confirm Abort",
                "EMERGENCY ABORT\n\n"
                "This will immediately:\n"
                "• Stop all show execution\n"
                "• Disable all outputs\n"
                "• Disarm the system\n\n"
                "Continue with abort?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes  # Default to Yes for safety
            )

            if reply == QMessageBox.Yes:
                success = self.system_mode.handle_abort_button()
                if success:
                    # Reset all states
                    self.show_running = False
                    self.show_paused = False
                    self.outputs_enabled = False
                    self.system_armed = False

                    # Update all buttons
                    self._reset_all_buttons()
                    self.execution_status_changed.emit("SYSTEM ABORTED - All outputs disabled")

        except Exception as e:
            self.logger.error(f"Failed to handle abort: {e}")
            self._show_error_message("Abort Error", str(e))

    def handle_mode_selector(self):
        """Handle Mode button click"""
        try:
            self.logger.info("Mode button clicked")

            # Check if dialog is already open to prevent multiple instances
            if (self.main_window and
                hasattr(self.main_window, '_mode_dialog_open') and
                self.main_window._mode_dialog_open):
                self.logger.info("Mode selector dialog already open, ignoring request")
                return

            # This should open the enhanced mode selector dialog
            if self.main_window and hasattr(self.main_window, 'show_mode_selector'):
                self.main_window.show_mode_selector()
            else:
                self.logger.warning("Main window does not have show_mode_selector method")

        except Exception as e:
            self.logger.error(f"Failed to handle mode selector: {e}")
            self._show_error_message("Mode Selector Error", str(e))

    # Async execution methods

    async def _execute_single_cue(self, cue_data: Dict[str, Any]):
        """Execute a single cue asynchronously"""
        try:
            self.execution_status_changed.emit(f"Executing cue {cue_data.get('cue_id', 'unknown')}")

            success = await self.system_mode.handle_execute_cue_button(cue_data)

            if success:
                self.execution_status_changed.emit(f"Cue {cue_data.get('cue_id')} executed successfully")
            else:
                self.execution_status_changed.emit(f"Cue {cue_data.get('cue_id')} execution failed")

        except Exception as e:
            self.logger.error(f"Single cue execution error: {e}")
            self.execution_status_changed.emit(f"Cue execution error: {e}")

    async def _execute_full_show(self, show_cues: List[Dict[str, Any]]):
        """Execute full show asynchronously"""
        try:
            self.show_running = True
            self._update_show_control_buttons()

            self.execution_status_changed.emit(f"Starting show with {len(show_cues)} cues")

            success = await self.system_mode.handle_execute_show_button(show_cues)

            if not success:
                self.show_running = False
                self._update_show_control_buttons()
                self.execution_status_changed.emit("Failed to start show execution")

        except Exception as e:
            self.logger.error(f"Show execution error: {e}")
            self.show_running = False
            self._update_show_control_buttons()
            self.execution_status_changed.emit(f"Show execution error: {e}")

    # Helper methods

    def _get_selected_cue(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected cue from the main window"""
        try:
            if self.main_window and hasattr(self.main_window, 'get_selected_cue'):
                return self.main_window.get_selected_cue()
            else:
                # Fallback - create a test cue for demonstration
                return {
                    'cue_id': 'test_001',
                    'cue_number': 1,
                    'output_values': [1, 2, 3]  # Example outputs
                }
        except Exception as e:
            self.logger.error(f"Failed to get selected cue: {e}")
            return None

    def _get_all_cues(self) -> List[Dict[str, Any]]:
        """Get all cues from the main window"""
        try:
            if self.main_window and hasattr(self.main_window, 'get_all_cues'):
                return self.main_window.get_all_cues()
            else:
                # Fallback - create test cues for demonstration
                return [
                    {'cue_id': f'test_{i:03d}', 'cue_number': i, 'output_values': [i]}
                    for i in range(1, 6)  # 5 test cues
                ]
        except Exception as e:
            self.logger.error(f"Failed to get all cues: {e}")
            return []

    def _check_system_ready_for_execution(self) -> bool:
        """Check if system is ready for cue execution"""
        try:
            if not self.outputs_enabled:
                self._show_error_message(
                    "System Not Ready",
                    "Outputs must be enabled before executing cues."
                )
                return False

            if not self.system_armed:
                self._show_error_message(
                    "System Not Ready",
                    "System must be armed before executing cues."
                )
                return False

            # Check MQTT connection
            if hasattr(self.system_mode, 'use_professional_mqtt') and self.system_mode.use_professional_mqtt:
                if not self.system_mode.is_professional_mqtt_connected:
                    self._show_error_message(
                        "MQTT Not Connected",
                        "Professional MQTT connection required for execution."
                    )
                    return False

            return True

        except Exception as e:
            self.logger.error(f"System readiness check failed: {e}")
            return False

    def _update_show_control_buttons(self):
        """Update show control button states"""
        try:
            # Update PAUSE button
            if "PAUSE" in self.button_bar.buttons:
                self.button_bar.buttons["PAUSE"].set_active(self.show_running and not self.show_paused)

            # Update RESUME button
            if "RESUME" in self.button_bar.buttons:
                self.button_bar.buttons["RESUME"].set_active(self.show_paused)

            # Update STOP/ABORT button
            if "STOP" in self.button_bar.buttons:
                self.button_bar.buttons["STOP"].set_active(self.show_running or self.show_paused)

            # Update EXECUTE SHOW button
            if "EXECUTE SHOW" in self.button_bar.buttons:
                self.button_bar.buttons["EXECUTE SHOW"].set_active(not self.show_running and not self.show_paused)

        except Exception as e:
            self.logger.error(f"Failed to update show control buttons: {e}")

    def _reset_all_buttons(self):
        """Reset all buttons to safe states after abort"""
        try:
            # Reset enable outputs button
            if "ENABLE OUTPUTS" in self.button_bar.buttons:
                button = self.button_bar.buttons["ENABLE OUTPUTS"]
                button.setText("ENABLE\nOUTPUTS")
                button.set_selected(False)

            # Reset arm outputs button
            if "ARM OUTPUTS" in self.button_bar.buttons:
                button = self.button_bar.buttons["ARM OUTPUTS"]
                button.setText("ARM\nOUTPUTS")
                button.set_selected(False)

            # Update show control buttons
            self._update_show_control_buttons()

        except Exception as e:
            self.logger.error(f"Failed to reset buttons: {e}")

    def _show_error_message(self, title: str, message: str):
        """Show error message to user"""
        try:
            if self.main_window:
                QMessageBox.critical(self.main_window, title, message)
            else:
                self.logger.error(f"{title}: {message}")
        except Exception as e:
            self.logger.error(f"Failed to show error message: {e}")

    # System signal handlers

    def _on_gpio_state_changed(self, pin_name: str, state: bool):
        """Handle GPIO state changes"""
        self.logger.debug(f"GPIO {pin_name}: {'HIGH' if state else 'LOW'}")

    def _on_system_state_changed(self, new_state: str):
        """Handle system state changes"""
        self.execution_status_changed.emit(f"System: {new_state}")

    def _on_show_started(self, total_cues: int):
        """Handle show started"""
        self.show_running = True
        self.show_paused = False
        self._update_show_control_buttons()
        self.execution_status_changed.emit(f"Show started: {total_cues} cues")

    def _on_show_completed(self):
        """Handle show completed"""
        self.show_running = False
        self.show_paused = False
        self._update_show_control_buttons()
        self.execution_status_changed.emit("Show completed successfully")

    def _on_show_paused(self, current_cue_index: int):
        """Handle show paused"""
        self.show_paused = True
        self._update_show_control_buttons()
        self.execution_status_changed.emit(f"Show paused at cue {current_cue_index}")

    def _on_show_resumed(self, current_cue_index: int):
        """Handle show resumed"""
        self.show_paused = False
        self._update_show_control_buttons()
        self.execution_status_changed.emit(f"Show resumed at cue {current_cue_index}")

    def _on_show_aborted(self, reason: str):
        """Handle show aborted"""
        self.show_running = False
        self.show_paused = False
        self._update_show_control_buttons()
        self.execution_status_changed.emit(f"Show aborted: {reason}")

    def _on_progress_updated(self, progress_info: dict):
        """Handle show progress updates"""
        self.show_progress_updated.emit(progress_info)

    def _on_mqtt_status_changed(self, connected: bool, status: str):
        """Handle MQTT connection status changes"""
        self.execution_status_changed.emit(f"MQTT: {status}")

    def _on_system_error(self, error_message: str):
        """Handle system errors"""
        self.execution_status_changed.emit(f"Error: {error_message}")