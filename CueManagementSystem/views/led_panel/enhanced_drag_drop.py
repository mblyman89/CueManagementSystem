from PySide6.QtWidgets import QWidget, QApplication, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QPoint, QRect, QSize, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, Signal, \
    QObject, QTimer, QMimeData
from PySide6.QtGui import QDrag, QPixmap, QPainter, QColor
import math


class EnhancedDragDropManager(QObject):
    """Professional drag and drop manager with interactive repositioning"""

    groups_rearranged = Signal()

    def __init__(self, led_grid_grouped):
        super().__init__()
        self.led_grid = led_grid_grouped
        self.dragging_group = None
        self.drag_preview = None
        self.drop_indicator_position = None
        self.animation_group = None
        self.hover_timer = QTimer()
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self.show_drop_preview)

        # Visual feedback settings
        self.drop_preview_opacity = 0.3
        self.drag_shadow_blur = 15

    def start_drag(self, group):
        """Start professional drag operation with visual feedback"""
        self.dragging_group = group
        print(f"Starting drag for group {group.group_id}")

        # Create drag preview with shadow effect
        self.create_drag_preview(group)

        # Start the drag operation
        drag = QDrag(group)
        mime_data = QMimeData()
        mime_data.setText(f"led_group_{group.group_id}")
        drag.setMimeData(mime_data)

        # Create semi-transparent drag pixmap
        pixmap = self.create_drag_pixmap(group)
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))

        # Execute drag with move action
        print("Executing drag operation...")
        result = drag.exec_(Qt.MoveAction)
        print(f"Drag result: {result}")

        # Clean up
        self.cleanup_drag()

        # Note: The actual rearrangement will be handled in the dropEvent

    def create_drag_pixmap(self, group):
        """Create a transparent drag pixmap to hide the grey box"""
        # Create a small transparent pixmap to hide the drag preview
        transparent_pixmap = QPixmap(1, 1)
        transparent_pixmap.fill(Qt.transparent)
        return transparent_pixmap

    def create_drag_preview(self, group):
        """Create visual preview during drag"""
        # Add glow effect to the dragging group
        glow_effect = QGraphicsDropShadowEffect()
        glow_effect.setBlurRadius(self.drag_shadow_blur)
        glow_effect.setColor(QColor(255, 255, 0, 180))  # Yellow glow
        glow_effect.setOffset(0, 0)
        group.setGraphicsEffect(glow_effect)

    def handle_drag_move(self, group, global_pos):
        """Handle drag move with iOS-style interactive feedback"""
        # Find potential drop position
        new_position = self.find_drop_position(global_pos)

        if new_position != self.drop_indicator_position:
            self.drop_indicator_position = new_position

            # Immediately show interactive repositioning (like iOS)
            self.show_interactive_repositioning()

    def show_interactive_repositioning(self):
        """Show real-time repositioning like iOS app rearrangement"""
        if not self.drop_indicator_position or not self.dragging_group:
            return

        # Calculate new arrangement
        new_arrangement = self.calculate_new_arrangement()

        # Animate other groups to show where they'll move in real-time
        self.animate_interactive_positions(new_arrangement)

    def show_drop_preview(self):
        """Show interactive preview of where the group will be dropped"""
        if not self.drop_indicator_position or not self.dragging_group:
            return

        # Calculate new arrangement
        new_arrangement = self.calculate_new_arrangement()

        # Animate other groups to show preview positions
        self.animate_preview_positions(new_arrangement)

    def find_drop_position(self, global_pos):
        """Find the best drop position based on mouse coordinates"""
        try:
            # Convert to local coordinates
            local_pos = self.led_grid.content_widget.mapFromGlobal(global_pos)

            # Find the closest group position
            min_distance = float('inf')
            closest_position = None

            for group_id, (row, col) in self.led_grid.group_positions.items():
                if group_id == self.dragging_group.group_id:
                    continue

                # Get the center of this group's position
                group_rect = self.led_grid.main_layout.cellRect(row, col)
                group_center = group_rect.center()

                # Calculate distance
                distance = (local_pos - group_center).manhattanLength()

                if distance < min_distance:
                    min_distance = distance
                    closest_position = (row, col)

            return closest_position
        except Exception as e:
            print(f"Error finding drop position: {e}")
            return None

    def calculate_new_arrangement(self):
        """Calculate how groups should be arranged after drop"""
        if not self.drop_indicator_position or not self.dragging_group:
            return {}

        current_positions = dict(self.led_grid.group_positions)
        dragged_group_id = self.dragging_group.group_id
        target_row, target_col = self.drop_indicator_position

        print(f"Calculating arrangement: dragged_group={dragged_group_id}, target=({target_row}, {target_col})")
        print(f"Current positions before: {current_positions}")

        # Find which group is currently at the target position
        target_group_id = None
        for group_id, (row, col) in current_positions.items():
            if row == target_row and col == target_col:
                target_group_id = group_id
                break

        if target_group_id is None:
            print("No target group found, returning current positions")
            return current_positions

        if target_group_id == dragged_group_id:
            print("Target is same as dragged group, no change needed")
            return current_positions

        # Swap positions
        dragged_current_pos = current_positions[dragged_group_id]
        current_positions[dragged_group_id] = (target_row, target_col)
        current_positions[target_group_id] = dragged_current_pos

        print(
            f"Swapped: group {dragged_group_id} -> ({target_row}, {target_col}), group {target_group_id} -> {dragged_current_pos}")
        print(f"Current positions after: {current_positions}")

        return current_positions

    def animate_interactive_positions(self, new_arrangement):
        """Animate groups to show real-time repositioning like iOS"""
        if self.animation_group and self.animation_group.state() == QPropertyAnimation.Running:
            self.animation_group.stop()

        self.animation_group = QParallelAnimationGroup()

        for group_id, (new_row, new_col) in new_arrangement.items():
            if group_id >= len(self.led_grid.led_groups):
                continue

            group = self.led_grid.led_groups[group_id]
            if group == self.dragging_group:
                continue  # Don't animate the dragging group

            # Calculate target position
            target_rect = self.led_grid.main_layout.cellRect(new_row, new_col)
            current_pos = group.pos()
            target_pos = target_rect.topLeft()

            # Only animate if position actually changes
            if current_pos != target_pos:
                animation = QPropertyAnimation(group, b"pos")
                animation.setDuration(150)  # Fast iOS-style animation
                animation.setEasingCurve(QEasingCurve.OutCubic)
                animation.setStartValue(current_pos)
                animation.setEndValue(target_pos)

                self.animation_group.addAnimation(animation)

        if self.animation_group.animationCount() > 0:
            self.animation_group.start()

    def perform_group_rearrangement(self):
        """Perform the final group rearrangement"""
        print("Performing group rearrangement")
        new_arrangement = self.calculate_new_arrangement()

        if not new_arrangement:
            print("No new arrangement calculated")
            return

        print(f"New arrangement: {new_arrangement}")

        # Update the group positions permanently
        self.led_grid.group_positions = new_arrangement

        # Finalize positions immediately (groups are already in place from interactive movement)
        self.finalize_rearrangement()

    def animate_to_final_positions(self, new_arrangement):
        """Animate all groups to their final positions"""
        if self.animation_group and self.animation_group.state() == QPropertyAnimation.Running:
            self.animation_group.stop()

        self.animation_group = QParallelAnimationGroup()

        for group_id, (new_row, new_col) in new_arrangement.items():
            if group_id >= len(self.led_grid.led_groups):
                continue

            group = self.led_grid.led_groups[group_id]

            # Calculate target position
            target_rect = self.led_grid.main_layout.cellRect(new_row, new_col)
            target_pos = target_rect.topLeft()

            animation = QPropertyAnimation(group, b"pos")
            animation.setDuration(400)  # Smooth final animation
            animation.setEasingCurve(QEasingCurve.OutCubic)
            animation.setStartValue(group.pos())
            animation.setEndValue(target_pos)

            self.animation_group.addAnimation(animation)

        # Connect to finalization
        self.animation_group.finished.connect(self.finalize_rearrangement)
        self.animation_group.start()

    def finalize_rearrangement(self):
        """Finalize the rearrangement"""
        print("Finalizing rearrangement")

        # Verify all groups are in correct positions
        self.verify_group_positions()

        # Emit completion signal
        self.groups_rearranged.emit()
        print("Rearrangement finalized")

    def verify_group_positions(self):
        """Verify and fix any missing or misplaced groups"""
        print("Verifying group positions...")

        # Check that all groups are visible and in correct layout positions
        for group_id, (row, col) in self.led_grid.group_positions.items():
            if group_id < len(self.led_grid.led_groups):
                group = self.led_grid.led_groups[group_id]
                target_rect = self.led_grid.main_layout.cellRect(row, col)
                target_pos = target_rect.topLeft()

                # If group is not in the right position, move it there
                if group.pos() != target_pos:
                    print(f"Correcting position for group {group_id}: {group.pos()} -> {target_pos}")
                    group.move(target_pos)

                # Ensure group is visible
                if not group.isVisible():
                    print(f"Making group {group_id} visible")
                    group.setVisible(True)

        print("Group position verification complete")

    def cleanup_drag(self):
        """Clean up drag operation"""
        if self.dragging_group:
            # Remove glow effect
            self.dragging_group.setGraphicsEffect(None)

        self.dragging_group = None
        self.drop_indicator_position = None
        self.hover_timer.stop()