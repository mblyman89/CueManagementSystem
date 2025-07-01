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

    def switch_to_view(self, view_name, is_preview=False):
        """Switch to the specified view"""
        if view_name == "traditional":
            self.stacked_widget.setCurrentWidget(self.traditional_grid)
            self.current_view = "traditional"
        elif view_name == "grouped":
            self.stacked_widget.setCurrentWidget(self.grouped_grid)
            self.current_view = "grouped"

        # Update view indicator (removed to save space)
        if not is_preview:
            # Refresh current cue data in new view
            if self.current_cue_data:
                self.update_from_cue_data(self.current_cue_data)

            # Emit view changed signal
            self.view_changed.emit(self.current_view)

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