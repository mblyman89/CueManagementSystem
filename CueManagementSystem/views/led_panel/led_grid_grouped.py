"""
Grouped LED Grid Widget
=======================

Custom Qt widget displaying LEDs in draggable, rearrangeable groups with drag-and-drop functionality.

Features:
- LED groups of 50 LEDs each
- Drag-and-drop group rearrangement
- Visual group borders
- LED state management
- Animation controller integration
- 5x10 LED arrangement per group
- Interactive group manipulation

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

from PySide6.QtWidgets import (QWidget, QGridLayout, QFrame, QSizePolicy,
                               QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QApplication)
from PySide6.QtCore import Qt, QSize, QPoint, QRect, Signal, QMimeData, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QDrag, QPixmap
from views.led_panel.led_widget import LedWidget
from views.led_panel.led_animations import LedAnimationController
from views.led_panel.enhanced_drag_drop import EnhancedDragDropManager
import math


class LedGroup(QFrame):
    """A draggable group of 50 LEDs arranged in 5x10 grid"""

    group_moved = Signal(int, int)  # Signal emitted when group is moved (from_pos, to_pos)

    def __init__(self, group_id, start_led_number, parent=None):
        super().__init__(parent)
        self.group_id = group_id
        self.start_led_number = start_led_number
        self.leds = {}
        self.is_dragging = False
        self.drag_start_position = QPoint()
        self.original_position = None
        self.enhanced_drag_manager = None  # Will be set by parent

        self.setup_ui()
        self.setAcceptDrops(True)

        # Style the group with visible border
        self.setStyleSheet("""
            LedGroup {
                border: 3px solid #4CAF50;
                border-radius: 8px;
                background-color: #1e1e2e;
                margin: 0px;
            }
            LedGroup:hover {
                border-color: #66BB6A;
                background-color: #252535;
            }
        """)

    def setup_ui(self):
        """Setup the LED group UI with 5x10 grid"""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(2, 2, 2, 2)

        # Group header removed - cleaner appearance

        # LED grid (5 columns x 10 rows = 50 LEDs)
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(0)  # No spacing between LEDs
        grid_layout.setContentsMargins(0, 0, 0, 0)  # No margins around the grid

        led_number = self.start_led_number
        # Change LED order: bottom-to-top in each column, then next column
        for col in range(5):  # 5 columns first
            for row in range(9, -1, -1):  # 10 rows, bottom to top (9 to 0)
                led = LedWidget(led_number)
                # Make LEDs expand to fill available space like standard mode
                led.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                led.setMinimumSize(20, 20)  # Larger minimum size

                grid_layout.addWidget(led, row, col)
                self.leds[led_number] = led
                led_number += 1

        layout.addWidget(grid_widget)

        # Set size policies
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setMinimumSize(150, 200)
        self.setMaximumSize(200, 250)

    def mousePressEvent(self, event):
        """Handle mouse press for drag initiation"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
            self.original_position = self.pos()

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if not (event.buttons() & Qt.LeftButton):
            return

        # Use a smaller drag distance for tighter groups
        drag_distance = max(5, QApplication.startDragDistance() // 2)
        if ((event.pos() - self.drag_start_position).manhattanLength() < drag_distance):
            return

        if not self.is_dragging:
            self.start_drag()
        elif self.enhanced_drag_manager:
            # Send drag move events to enhanced manager
            self.enhanced_drag_manager.handle_drag_move(self, event.globalPos())

    def start_drag(self):
        """Initiate enhanced drag operation"""
        if self.enhanced_drag_manager:
            self.enhanced_drag_manager.start_drag(self)
        else:
            # Fallback to basic drag
            self.basic_drag_operation()

    def basic_drag_operation(self):
        """Fallback basic drag operation"""
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"led_group_{self.group_id}")
        drag.setMimeData(mime_data)

        # Create drag pixmap
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(self.drag_start_position)

        # Execute drag
        self.is_dragging = True
        drop_action = drag.exec_(Qt.MoveAction)
        self.is_dragging = False

        if drop_action != Qt.MoveAction:
            # Drag was cancelled, restore original position
            if self.original_position:
                self.move(self.original_position)

    def get_led_numbers(self):
        """Get list of LED numbers in this group"""
        return list(self.leds.keys())

    def update_led_states(self, cue_data_list):
        """Update LED states based on cue data (matches standard view behavior)"""
        # Reset all LEDs in this group first
        for led in self.leds.values():
            led.setState(None)
            led.is_active = False
            led.cue_type = None

        if not cue_data_list:
            return

        # Process all cues in the list (same logic as standard view)
        for cue_data in cue_data_list:
            if not cue_data or len(cue_data) < 3:
                continue

            cue_type = cue_data[1]  # TYPE is at index 1
            outputs = cue_data[2]  # OUTPUTS is at index 2

            try:
                # Parse outputs string into list of numbers (same as standard view)
                output_list = []
                if ";" in outputs:  # Handle double run format with semicolons
                    for pair in outputs.split(";"):
                        for value in pair.split(","):
                            if value.strip() and value.strip().isdigit():
                                output_list.append(int(value.strip()))
                else:  # Handle regular comma-separated format
                    output_list = [int(x.strip()) for x in outputs.split(',') if x.strip().isdigit()]

                # Set LEDs active based on outputs (only for LEDs in this group)
                for output in output_list:
                    if output in self.leds:
                        self.leds[output].setState(cue_type)

            except (ValueError, AttributeError) as e:
                print(f"Error processing outputs in group {self.group_id}: {e}")
                continue


class LedGridGrouped(QScrollArea):
    """LED grid with grouped view and drag-and-drop functionality"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = 40
        self.cols = 25
        self.total_leds = 1000
        self.groups_per_row = 4  # 4 groups per row (20 groups total in 5 rows)
        self.groups_per_col = 5
        self.total_groups = 20

        self.led_groups = []
        self.group_positions = {}  # {group_id: (row, col)}
        self.animation_controller = None

        # Configure scroll area
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setAcceptDrops(True)  # Enable drop events for the scroll area

        # Initialize enhanced drag-drop manager first
        self.enhanced_drag_manager = EnhancedDragDropManager(self)
        self.enhanced_drag_manager.groups_rearranged.connect(self.on_groups_rearranged)

        self.setup_ui()
        self.create_led_groups()
        self.arrange_groups()

        # Set size policies
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(800, 600)

        # Initialize animation controller
        self.animation_controller = LedAnimationController(self)

    def setup_ui(self):
        """Setup the main UI with scroll area"""
        # Create the main content widget
        self.content_widget = QWidget()
        self.content_widget.setAcceptDrops(True)  # Enable drops on content widget
        self.main_layout = QGridLayout(self.content_widget)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Set the content widget as the scroll area's widget
        self.setWidget(self.content_widget)

        # Style the scroll area and content
        self.setStyleSheet("""
            QScrollArea {
                background-color: #1a1a2e;
                border: none;
            }
            QWidget {
                background-color: #1a1a2e;
                padding: 0px;
                margin: 0px;
            }
        """)

    def create_led_groups(self):
        """Create 20 LED groups of 50 LEDs each"""
        for group_id in range(self.total_groups):
            start_led = (group_id * 50) + 1
            group = LedGroup(group_id, start_led, self)
            group.group_moved.connect(self.handle_group_move)
            group.enhanced_drag_manager = self.enhanced_drag_manager  # Connect to enhanced manager
            self.led_groups.append(group)

    def arrange_groups(self):
        """Arrange groups in snake pattern: bottom-left, up, right, down, left"""
        # Clear existing layout
        for i in reversed(range(self.main_layout.count())):
            self.main_layout.itemAt(i).widget().setParent(None)

        self.group_positions.clear()

        # Snake pattern arrangement
        group_index = 0

        # Start from bottom-left, work in columns
        for col in range(self.groups_per_row):  # 4 columns
            if col % 2 == 0:  # Even columns: bottom to top
                for row in range(self.groups_per_col - 1, -1, -1):  # 5 rows, bottom to top
                    if group_index < len(self.led_groups):
                        group = self.led_groups[group_index]
                        self.main_layout.addWidget(group, row, col)
                        self.group_positions[group_index] = (row, col)
                        group_index += 1
            else:  # Odd columns: top to bottom
                for row in range(self.groups_per_col):  # 5 rows, top to bottom
                    if group_index < len(self.led_groups):
                        group = self.led_groups[group_index]
                        self.main_layout.addWidget(group, row, col)
                        self.group_positions[group_index] = (row, col)
                        group_index += 1

    def handle_group_move(self, from_group_id, to_position):
        """Handle when a group is moved to a new position"""
        # This will be implemented for drag-and-drop functionality
        # For now, we'll rearrange the groups
        self.rearrange_groups_after_move(from_group_id, to_position)

    def rearrange_groups_after_move(self, moved_group_id, new_position):
        """Rearrange groups after a move operation"""
        # Remove the moved group from its current position
        moved_group = self.led_groups[moved_group_id]

        # Create new arrangement
        # This is a simplified version - in a full implementation,
        # you'd calculate the new positions based on the drop location
        self.arrange_groups()

    def on_groups_rearranged(self):
        """Handle when groups are rearranged by enhanced drag-drop"""
        # Refresh current cue data to maintain LED states after rearrangement
        if hasattr(self, 'current_cue_data') and self.current_cue_data:
            self.updateFromCueData(self.current_cue_data)

        # Force update
        self.update()

    def on_groups_rearranged(self):
        """Handle when groups are rearranged by enhanced drag-drop"""
        # Refresh current cue data to maintain LED states after rearrangement
        if hasattr(self, 'current_cue_data') and self.current_cue_data:
            self.updateFromCueData(self.current_cue_data)

        # Force update
        self.update()

    def get_all_leds(self):
        """Get dictionary of all LEDs {led_number: led_widget}"""
        all_leds = {}
        for group in self.led_groups:
            all_leds.update(group.leds)
        return all_leds

    @property
    def leds(self):
        """Property to maintain compatibility with existing code"""
        return self.get_all_leds()

    def updateFromCueData(self, cue_data, force_refresh=False):
        """Update LEDs based on cue data from table (matches standard view exactly)"""
        print(f"Grouped view updateFromCueData called with: {cue_data}")

        # Reset all LEDs first
        for group in self.led_groups:
            for led in group.leds.values():
                led.setState(None)
                led.is_active = False
                led.cue_type = None

        # Force update
        self.update()

        # Update LEDs based on cue data (same logic as standard view)
        if cue_data:
            for cue in cue_data:
                cue_type = cue[1]  # TYPE is at index 1
                outputs = cue[2]  # OUTPUTS is at index 2

                print(f"Processing cue: type={cue_type}, outputs={outputs}")

                try:
                    # Parse outputs string into list of numbers (same as standard view)
                    output_list = []
                    if ";" in outputs:  # Handle double run format with semicolons
                        for pair in outputs.split(";"):
                            for value in pair.split(","):
                                if value.strip() and value.strip().isdigit():
                                    output_list.append(int(value.strip()))
                    else:  # Handle regular comma-separated format
                        output_list = [int(x.strip()) for x in outputs.split(',') if x.strip().isdigit()]

                    print(f"Parsed outputs: {output_list}")

                    # Set LEDs active based on outputs
                    for output in output_list:
                        # Find which group contains this LED
                        for group in self.led_groups:
                            if output in group.leds:
                                print(f"Setting LED {output} to {cue_type} in group {group.group_id}")
                                group.leds[output].setState(cue_type)
                                break

                except (ValueError, AttributeError) as e:
                    print(f"Error processing outputs: {e}")
                    continue

    def handle_cue_selection(self, cue_data=None):
        """Handle cue selection from table"""
        if self.animation_controller:
            if cue_data:
                self.animation_controller.start_animation(cue_data)
            else:
                self.animation_controller.stop_animation()

    def reset_all_leds(self):
        """Reset all LEDs to inactive state"""
        if self.animation_controller:
            self.animation_controller.stop_animation()

        for group in self.led_groups:
            group.update_led_states(None)

        self.update()

    def sizeHint(self):
        """Provide a reasonable default size"""
        return QSize(1000, 800)

    def minimumSizeHint(self):
        """Provide a reasonable minimum size"""
        return QSize(800, 600)

    def dragEnterEvent(self, event):
        """Handle drag enter for the scroll area"""
        print("Drag Enter Event on LedGridGrouped")
        if event.mimeData().hasText() and event.mimeData().text().startswith("led_group_"):
            print("Drag enter accepted")
            event.acceptProposedAction()
        else:
            print("Drag enter ignored")
            event.ignore()

    def dragMoveEvent(self, event):
        """Handle drag move for the scroll area"""
        if event.mimeData().hasText() and event.mimeData().text().startswith("led_group_"):
            event.acceptProposedAction()
            # Update drop indicator using enhanced manager
            if self.enhanced_drag_manager:
                # Convert local position to global position
                global_pos = self.mapToGlobal(event.pos())
                self.enhanced_drag_manager.handle_drag_move(None, global_pos)

    def dropEvent(self, event):
        """Handle drop for the scroll area"""
        print("Drop Event on LedGridGrouped")
        if event.mimeData().hasText() and event.mimeData().text().startswith("led_group_"):
            event.acceptProposedAction()
            print("Drop accepted")
            # Handle the drop using enhanced manager
            if self.enhanced_drag_manager:
                # Convert local position to global position
                global_pos = self.mapToGlobal(event.pos())
                position = self.enhanced_drag_manager.find_drop_position(global_pos)
                self.enhanced_drag_manager.drop_indicator_position = position
                self.enhanced_drag_manager.perform_group_rearrangement()
        else:
            print("Drop ignored")
            event.ignore()


# Import QApplication for drag distance
from PySide6.QtWidgets import QApplication
