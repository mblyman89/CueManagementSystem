"""
Preview Timeline Widget
A clean, simple timeline control for preview playback with real-time scrubbing.
Features: Play/Pause button, draggable playhead, time display.
No cue markers - LED panel provides visualization.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal, QRect, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QMouseEvent
from typing import List, Any


class PreviewTimelineWidget(QWidget):
    """
    Timeline widget for preview control with real-time scrubbing

    Features:
    - Play/Pause toggle button
    - Draggable playhead with real-time position updates
    - Time display (current / total)
    - Clean design without cue markers
    """

    # Signals
    seek_requested = Signal(float)  # Emits time in seconds during drag
    scrubbing_started = Signal()  # Emits when user starts dragging
    scrubbing_ended = Signal()  # Emits when user releases drag
    play_pause_toggled = Signal()  # Emits when play/pause clicked

    def __init__(self, parent=None):
        super().__init__(parent)

        # State
        self.current_time = 0.0
        self.total_duration = 0.0
        self.is_playing = False
        self.is_enabled = False
        self.is_dragging = False

        # UI setup
        self.setup_ui()

        # Styling
        self.setMinimumHeight(60)
        self.setMaximumHeight(80)

        # Timeline bar geometry (calculated in paintEvent)
        self.timeline_rect = QRect()
        self.playhead_x = 0

    def setup_ui(self):
        """Setup the widget UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Play/Pause button
        self.play_pause_btn = QPushButton("▶")
        self.play_pause_btn.setFixedSize(40, 40)
        self.play_pause_btn.clicked.connect(self.on_play_pause_clicked)
        self.play_pause_btn.setEnabled(False)
        self.play_pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 2px solid #3d3d3d;
                border-radius: 20px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover:enabled {
                background-color: #3d3d3d;
                border-color: #4d4d4d;
            }
            QPushButton:pressed:enabled {
                background-color: #1d1d1d;
            }
            QPushButton:disabled {
                background-color: #1d1d1d;
                color: #666666;
                border-color: #2d2d2d;
            }
        """)
        layout.addWidget(self.play_pause_btn)

        # Spacer for timeline (will be drawn in paintEvent)
        layout.addStretch()

        # Time display
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-family: monospace;
                background-color: transparent;
            }
        """)
        self.time_label.setMinimumWidth(120)
        self.time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.time_label)

        # Set widget background
        self.setStyleSheet("""
            PreviewTimelineWidget {
                background-color: #1a1a1a;
                border-top: 1px solid #2d2d2d;
                border-bottom: 1px solid #2d2d2d;
            }
        """)

    def on_play_pause_clicked(self):
        """Handle play/pause button click"""
        self.play_pause_toggled.emit()

    def set_playing_state(self, is_playing: bool):
        """
        Update the playing state and button appearance

        Args:
            is_playing: True if playing, False if paused
        """
        self.is_playing = is_playing
        self.play_pause_btn.setText("❚❚" if is_playing else "▶")

    def enable_controls(self, enabled: bool):
        """
        Enable or disable the timeline controls

        Args:
            enabled: True to enable, False to disable
        """
        self.is_enabled = enabled
        self.play_pause_btn.setEnabled(enabled)

        if not enabled:
            self.current_time = 0.0
            self.total_duration = 0.0
            self.is_playing = False
            self.is_dragging = False
            self.play_pause_btn.setText("▶")
            self.update_time_display()

        self.update()

    def update_position(self, current_time: float, total_duration: float):
        """
        Update the timeline position

        Args:
            current_time: Current time in seconds
            total_duration: Total duration in seconds
        """
        self.current_time = current_time
        self.total_duration = total_duration
        self.update_time_display()

        # Only update visual if not dragging (to avoid fighting with user input)
        if not self.is_dragging:
            self.update()

    def update_time_display(self):
        """Update the time label text"""
        current_str = self.format_time(self.current_time)
        total_str = self.format_time(self.total_duration)
        self.time_label.setText(f"{current_str} / {total_str}")

    def format_time(self, seconds: float) -> str:
        """
        Format time in seconds to MM:SS string

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string
        """
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def get_current_position(self) -> float:
        """
        Get the current position in seconds

        Returns:
            Current time in seconds
        """
        return self.current_time

    def paintEvent(self, event):
        """Custom paint event to draw the timeline"""
        super().paintEvent(event)

        if not self.is_enabled:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate timeline bar geometry
        # Leave space for play button (60px) and time label (130px) and margins
        margin_left = 60
        margin_right = 140
        margin_top = 20

        bar_width = self.width() - margin_left - margin_right
        bar_height = 8
        bar_x = margin_left
        bar_y = margin_top

        self.timeline_rect = QRect(bar_x, bar_y, bar_width, bar_height)

        # Draw timeline background (unplayed portion)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(60, 60, 60)))
        painter.drawRoundedRect(self.timeline_rect, 4, 4)

        # Draw timeline progress (played portion)
        if self.total_duration > 0:
            progress_ratio = self.current_time / self.total_duration
            progress_ratio = max(0.0, min(1.0, progress_ratio))  # Clamp to [0, 1]

            progress_width = int(bar_width * progress_ratio)
            if progress_width > 0:
                progress_rect = QRect(bar_x, bar_y, progress_width, bar_height)
                painter.setBrush(QBrush(QColor(100, 150, 255)))
                painter.drawRoundedRect(progress_rect, 4, 4)

            # Draw playhead
            self.playhead_x = bar_x + int(bar_width * progress_ratio)
            playhead_radius = 8

            # Playhead shadow
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
            painter.drawEllipse(
                QPoint(self.playhead_x + 1, bar_y + bar_height // 2 + 1),
                playhead_radius,
                playhead_radius
            )

            # Playhead
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawEllipse(
                QPoint(self.playhead_x, bar_y + bar_height // 2),
                playhead_radius,
                playhead_radius
            )

            # Playhead border
            painter.setPen(QPen(QColor(100, 150, 255), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(
                QPoint(self.playhead_x, bar_y + bar_height // 2),
                playhead_radius,
                playhead_radius
            )

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for scrubbing"""
        if not self.is_enabled:
            return

        # Check if click is on or near the timeline
        if self.is_on_timeline(event.pos()):
            self.is_dragging = True
            self.scrubbing_started.emit()
            self.update_position_from_mouse(event.pos())
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for scrubbing"""
        if self.is_dragging:
            self.update_position_from_mouse(event.pos())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release to end scrubbing"""
        if self.is_dragging:
            self.is_dragging = False
            self.update_position_from_mouse(event.pos())
            self.scrubbing_ended.emit()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def is_on_timeline(self, pos: QPoint) -> bool:
        """
        Check if a point is on or near the timeline

        Args:
            pos: Mouse position

        Returns:
            True if on timeline, False otherwise
        """
        if self.timeline_rect.isEmpty():
            return False

        # Expand hit area vertically for easier clicking
        hit_rect = self.timeline_rect.adjusted(0, -10, 0, 10)
        return hit_rect.contains(pos)

    def update_position_from_mouse(self, pos: QPoint):
        """
        Update position based on mouse position

        Args:
            pos: Mouse position
        """
        if self.timeline_rect.isEmpty() or self.total_duration <= 0:
            return

        # Calculate position ratio
        x = pos.x()
        bar_x = self.timeline_rect.x()
        bar_width = self.timeline_rect.width()

        # Clamp to timeline bounds
        x = max(bar_x, min(x, bar_x + bar_width))

        # Calculate time
        ratio = (x - bar_x) / bar_width
        new_time = ratio * self.total_duration

        # Update current time and emit signal
        self.current_time = new_time
        self.update_time_display()
        self.update()

        # Emit seek request
        self.seek_requested.emit(new_time)