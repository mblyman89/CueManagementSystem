"""
LED Panel View Manager
======================

Manages switching between traditional and grouped LED panel views and updates them with cue data.

Features:
- View mode switching (traditional/grouped)
- Dynamic view creation and management
- Cue data updates to LED panels
- User interaction handling
- View state persistence
- Smooth view transitions

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget
from PySide6.QtCore import Qt, Signal
from views.led_panel.led_grid import LedGrid
from views.led_panel.led_grid_grouped import LedGridGrouped
from views.dialogs.led_selector_dialog import LedSelectorDialog


class LedPanelManager(QWidget):
    """Manages both traditional and grouped LED panel views"""

    # Signals for communication with parent application
    cue_selection_changed = Signal(object)  # When cue selection changes
    view_changed = Signal(str)  # When view mode changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_view = "traditional"  # Default view
        self.current_cue_data = None

        # Reference to preview controller (will be set by main window)
        self.preview_controller = None

        # Create both LED grid views
        self.traditional_grid = None
        self.grouped_grid = None
        self.drag_manager = None

        self.setup_ui()
        self.create_led_grids()

    def setup_ui(self):
        """Setup the main UI layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create status bar (no buttons since they're in main button bar)
        self.status_bar = self.create_button_bar()
        layout.addWidget(self.status_bar)

        # Create stacked widget to hold both views
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

        # Style the manager
        self.setStyleSheet("""
            LedPanelManager {
                background-color: #1a1a2e;
            }
        """)

    def create_button_bar(self):
        """Create empty status bar (no labels to save space)"""
        status_bar = QWidget()
        status_bar.setFixedHeight(0)  # Make it invisible to save space
        return status_bar

    def create_led_grids(self):
        """Create both LED grid views"""
        # Traditional grid
        self.traditional_grid = LedGrid()
        self.stacked_widget.addWidget(self.traditional_grid)

        # Grouped grid
        self.grouped_grid = LedGridGrouped()
        self.stacked_widget.addWidget(self.grouped_grid)

        # Drag manager is now integrated directly into the grouped grid

        # Set initial view
        self.switch_to_view(self.current_view)

    def show_view_selector(self):
        """Show the view selector dialog"""
        dialog = LedSelectorDialog(self, self.current_view)
        dialog.view_changed.connect(self.handle_view_change)
        dialog.exec_()

    def handle_view_change(self, new_view):
        """Handle view change from dialog"""
        if new_view.startswith("preview_"):
            # Handle preview mode
            preview_view = new_view.replace("preview_", "")
            self.preview_view(preview_view)
        else:
            # Handle permanent view change
            self.switch_to_view(new_view)

    def preview_view(self, view_name):
        """Preview a view temporarily"""
        # Temporarily switch to the preview view
        old_view = self.current_view
        self.switch_to_view(view_name, is_preview=True)

        # You could add a timer here to automatically switch back
        # or add a "Cancel Preview" button

    def _capture_led_states(self, source_grid):
        """Capture current LED states from a grid

        Returns:
            dict: Mapping of LED numbers to their state info
        """
        led_states = {}
        if not source_grid:
            return led_states

        # Try to get LED states from traditional grid
        if hasattr(source_grid, 'leds') and not hasattr(source_grid, 'led_groups'):
            print(f"[LED_PANEL_MANAGER] Capturing from traditional grid")
            active_count = 0
            for led_num, led_widget in source_grid.leds.items():
                is_active = getattr(led_widget, 'is_active', False)
                cue_type = getattr(led_widget, 'cue_type', None)
                led_states[led_num] = {
                    'active': is_active,
                    'cue_type': cue_type
                }
                if is_active:
                    active_count += 1
            print(f"[LED_PANEL_MANAGER] Captured {active_count} active LEDs from traditional grid")

        # Try to get LED states from grouped grid
        elif hasattr(source_grid, 'led_groups'):
            print(f"[LED_PANEL_MANAGER] Capturing from grouped grid")
            active_count = 0
            for group in source_grid.led_groups:
                if hasattr(group, 'leds'):
                    for led_num, led_widget in group.leds.items():
                        is_active = getattr(led_widget, 'is_active', False)
                        cue_type = getattr(led_widget, 'cue_type', None)
                        led_states[led_num] = {
                            'active': is_active,
                            'cue_type': cue_type
                        }
                        if is_active:
                            active_count += 1
                elif hasattr(group, 'led_numbers'):
                    # For groups that just track LED numbers
                    for led_num in group.led_numbers:
                        led_states[led_num] = {
                            'active': False,  # Default state
                            'cue_type': None
                        }
            print(f"[LED_PANEL_MANAGER] Captured {active_count} active LEDs from grouped grid")

        return led_states

    def _apply_led_states(self, target_grid, led_states):
        """Apply LED states to a target grid

        Args:
            target_grid: The grid to apply states to
            led_states: Dictionary of LED states to apply
        """
        if not target_grid or not led_states:
            print(
                f"[LED_PANEL_MANAGER] _apply_led_states: target_grid={target_grid is not None}, led_states count={len(led_states) if led_states else 0}")
            return

        print(f"[LED_PANEL_MANAGER] _apply_led_states: Applying {len(led_states)} LED states")

        # Apply states to traditional grid
        if hasattr(target_grid, 'leds') and not hasattr(target_grid, 'led_groups'):
            print(f"[LED_PANEL_MANAGER] Applying to traditional grid")
            applied_count = 0
            for led_num, state in led_states.items():
                if led_num in target_grid.leds:
                    led_widget = target_grid.leds[led_num]
                    # Use setState method which exists on LedWidget
                    if state['active'] and state.get('cue_type'):
                        led_widget.setState(state.get('cue_type'))
                        applied_count += 1
                    elif not state['active']:
                        led_widget.setState(None)
            print(f"[LED_PANEL_MANAGER] Applied {applied_count} active LEDs to traditional grid")

        # Apply states to grouped grid
        elif hasattr(target_grid, 'led_groups'):
            print(f"[LED_PANEL_MANAGER] Applying to grouped grid")
            applied_count = 0
            for group in target_grid.led_groups:
                if hasattr(group, 'leds'):
                    for led_num, led_widget in group.leds.items():
                        if led_num in led_states:
                            state = led_states[led_num]
                            # Use setState method which exists on LedWidget
                            if state['active'] and state.get('cue_type'):
                                led_widget.setState(state.get('cue_type'))
                                applied_count += 1
                            elif not state['active']:
                                led_widget.setState(None)
            print(f"[LED_PANEL_MANAGER] Applied {applied_count} active LEDs to grouped grid")

    def switch_to_view(self, view_name, is_preview=False):
        """Switch to the specified view while preserving LED states"""

        print(f"[LED_PANEL_MANAGER] switch_to_view called: view_name={view_name}, is_preview={is_preview}")

        # ===== NEW: Capture states from current grid before switching =====
        current_grid = self.get_current_grid()
        led_states = self._capture_led_states(current_grid)
        print(f"[LED_PANEL_MANAGER] Captured {len(led_states)} LED states")

        # Switch the view
        if view_name == "traditional":
            self.stacked_widget.setCurrentWidget(self.traditional_grid)
            self.current_view = "traditional"
        elif view_name == "grouped":
            self.stacked_widget.setCurrentWidget(self.grouped_grid)
            self.current_view = "grouped"

        # ===== NEW: Apply captured states to the new grid =====
        new_grid = self.get_current_grid()
        self._apply_led_states(new_grid, led_states)
        print(f"[LED_PANEL_MANAGER] Applied LED states to new grid")

        # Update view indicator (removed to save space)
        if not is_preview:
            # Check if we're in preview mode - if so, DON'T refresh from cue data
            # as this would overwrite the preview LED states
            in_preview_mode = self._is_in_preview_mode()
            print(f"[LED_PANEL_MANAGER] Preview mode check: in_preview_mode={in_preview_mode}")

            if not in_preview_mode:
                # Only refresh from cue data if NOT in preview mode
                # Refresh current cue data in new view (if available)
                if self.current_cue_data:
                    print(f"[LED_PANEL_MANAGER] Calling update_from_cue_data")
                    self.update_from_cue_data(self.current_cue_data)
            else:
                print(f"[LED_PANEL_MANAGER] Skipping update_from_cue_data because in preview mode")

            # Emit view changed signal
            self.view_changed.emit(self.current_view)

    def _is_in_preview_mode(self):
        """Check if we're currently in preview mode

        Returns:
            bool: True if preview is active, False otherwise
        """
        print(f"[LED_PANEL_MANAGER] _is_in_preview_mode: Checking preview mode...")

        # First check if we have a direct reference to preview controller
        if self.preview_controller:
            print(f"[LED_PANEL_MANAGER] _is_in_preview_mode: Found preview_controller (direct reference)")

            # Check if preview is playing or paused
            if hasattr(self.preview_controller, 'is_playing'):
                print(f"[LED_PANEL_MANAGER] _is_in_preview_mode: is_playing = {self.preview_controller.is_playing}")
                if self.preview_controller.is_playing:
                    return True

            if hasattr(self.preview_controller, 'is_paused'):
                print(f"[LED_PANEL_MANAGER] _is_in_preview_mode: is_paused = {self.preview_controller.is_paused}")
                if self.preview_controller.is_paused:
                    return True
        else:
            print(f"[LED_PANEL_MANAGER] _is_in_preview_mode: No direct preview_controller reference")

            # Fallback: try to get it from parent
            if hasattr(self, 'parent') and self.parent():
                parent = self.parent()
                print(f"[LED_PANEL_MANAGER] _is_in_preview_mode: Found parent")

                if hasattr(parent, 'preview_controller'):
                    preview_controller = parent.preview_controller
                    print(f"[LED_PANEL_MANAGER] _is_in_preview_mode: Found preview_controller on parent")

                    # Check if preview is playing or paused
                    if hasattr(preview_controller, 'is_playing'):
                        print(f"[LED_PANEL_MANAGER] _is_in_preview_mode: is_playing = {preview_controller.is_playing}")
                        if preview_controller.is_playing:
                            return True

                    if hasattr(preview_controller, 'is_paused'):
                        print(f"[LED_PANEL_MANAGER] _is_in_preview_mode: is_paused = {preview_controller.is_paused}")
                        if preview_controller.is_paused:
                            return True
                else:
                    print(f"[LED_PANEL_MANAGER] _is_in_preview_mode: No preview_controller on parent")
            else:
                print(f"[LED_PANEL_MANAGER] _is_in_preview_mode: No parent found")

        print(f"[LED_PANEL_MANAGER] _is_in_preview_mode: Returning False")
        return False

    def get_current_grid(self):
        """Get the currently active LED grid"""
        if self.current_view == "traditional":
            return self.traditional_grid
        else:
            return self.grouped_grid

    def update_from_cue_data(self, cue_data, force_refresh=False):
        """Update the current LED grid with cue data"""
        self.current_cue_data = cue_data
        current_grid = self.get_current_grid()
        if current_grid:
            current_grid.updateFromCueData(cue_data, force_refresh)

    def handle_cue_selection(self, cue_data=None):
        """Handle cue selection from table"""
        self.current_cue_data = cue_data
        current_grid = self.get_current_grid()
        if current_grid:
            current_grid.handle_cue_selection(cue_data)

        # Emit signal for parent application
        self.cue_selection_changed.emit(cue_data)

    def reset_all_leds(self):
        """Reset all LEDs in current view"""
        current_grid = self.get_current_grid()
        if current_grid:
            current_grid.reset_all_leds()
        self.current_cue_data = None

    def on_groups_rearranged(self):
        """Handle when groups are rearranged in grouped view"""
        # Refresh the current cue data to maintain LED states
        if self.current_cue_data and self.current_view == "grouped":
            self.grouped_grid.updateFromCueData(self.current_cue_data)

    def get_led_count(self):
        """Get total LED count"""
        return 1000

    def get_current_view_name(self):
        """Get current view name"""
        return self.current_view

    def set_view_mode(self, view_name):
        """Programmatically set view mode"""
        if view_name in ["traditional", "grouped"]:
            self.switch_to_view(view_name)

    # Properties for backward compatibility
    @property
    def leds(self):
        """Get LEDs from current grid for backward compatibility"""
        current_grid = self.get_current_grid()
        if current_grid:
            return current_grid.leds
        return {}

    @property
    def animation_controller(self):
        """Get animation controller from current grid"""
        current_grid = self.get_current_grid()
        if current_grid:
            return current_grid.animation_controller
        return None

    # Backward compatibility methods (camelCase versions)
    def updateFromCueData(self, cue_data, force_refresh=False):
        """Backward compatibility wrapper for update_from_cue_data"""
        return self.update_from_cue_data(cue_data, force_refresh)

    def handleCueSelection(self, cue_data=None):
        """Backward compatibility wrapper for handle_cue_selection"""
        return self.handle_cue_selection(cue_data)

    def resetAllLeds(self):
        """Backward compatibility wrapper for reset_all_leds"""
        return self.reset_all_leds()