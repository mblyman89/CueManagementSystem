from PySide6.QtWidgets import QWidget, QApplication, QMessageBox
from PySide6.QtCore import Qt, Signal, QRect, QSize, QPoint, Slot
from PySide6.QtGui import (
    QPainter, QPen, QColor, QBrush, QLinearGradient,
    QPainterPath, QFontMetrics
)
import math
import logging
from typing import Optional, List, Tuple


class WaveformView(QWidget):
    """
    Custom widget for rendering audio waveforms with advanced visualization features.

    Features:
    - High-performance waveform rendering
    - Smooth zooming and scrolling
    - Peak markers visualization
    - Time axis with adaptive grid
    - Amplitude scale in dB
    """

    # Signals
    zoom_changed = Signal(float)  # Emitted when zoom level changes
    position_changed = Signal(float)  # Emitted when position changes
    peak_selection_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the waveform widget"""
        super().__init__(parent)

        # Configure widget properties
        self.setMinimumHeight(150)
        self.setMinimumWidth(300)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)

        # Waveform analyzer reference
        self.analyzer = None

        # View state
        self.zoom_factor = 1.0
        self.offset = 0.0  # Normalized scroll position (0.0-1.0)
        self.current_position = 0.0  # Normalized playback position

        # Zoom constraints
        self.min_zoom = 0.1
        self.max_zoom = 50.0
        self.zoom_increment = 1.25

        # Visual settings
        self.amplitude_scale = 0.4
        self.show_grid = True
        self.show_time_markers = True
        self.show_db_scale = True

        # Mouse tracking
        self.mouse_position = None

        # Colors
        self._init_colors()

        # Select all Peaks
        self.selected_peaks = set()

        # Configure logging
        self._init_logging()

    def _init_colors(self):
        """Initialize color scheme for the widget"""
        # Base colors
        self.background_color = QColor(20, 20, 25)
        self.waveform_color = QColor(65, 175, 255)
        self.grid_color = QColor(60, 60, 70)
        self.text_color = QColor(200, 200, 200)

        # Accent colors
        self.position_marker_color = QColor(255, 100, 100)
        self.peak_marker_color = QColor(255, 210, 65)
        self.mouse_marker_color = QColor(200, 200, 200, 120)

        # Gradient colors
        self.gradient_top = QColor(80, 185, 255)
        self.gradient_middle = QColor(50, 150, 250)
        self.gradient_bottom = QColor(45, 145, 235)

    def _init_logging(self):
        """Initialize logging for the widget"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(handler)

    def sizeHint(self) -> QSize:
        """
        Suggest a default size for the widget

        Returns:
            QSize: Recommended widget size
        """
        return QSize(800, 200)

    def resizeEvent(self, event) -> None:
        """
        Handle widget resize events

        Args:
            event: Qt resize event
        """
        super().resizeEvent(event)
        self.update()  # Trigger repaint


    def mousePressEvent(self, event) -> None:
        """Handle mouse clicks for position changes and peak selection."""
        if not self.analyzer or not self.analyzer.is_analyzed:
            return

        if event.button() == Qt.LeftButton:
            click_x = event.position().x()
            content_rect = self._get_content_rect()

            if content_rect.contains(event.position().toPoint()):
                # Position change logic
                normalized_pos = self._pixel_to_position(click_x)
                normalized_pos = max(0.0, min(1.0, normalized_pos))
                self._set_position(normalized_pos)
                self.position_changed.emit(normalized_pos)
                self.logger.debug(f"Position changed via click: {normalized_pos:.3f}")

                # Peak selection logic (nested inside position change logic)
                if self.zoom_factor >= 5.0:
                    markers = self.analyzer.get_peak_markers(
                        content_rect.width(),
                        content_rect.height(),
                        self.offset,
                        self.zoom_factor
                    )
                    peak_index = self._find_peak_index(event.x(), event.y(), markers)

                    if peak_index is not None:
                        if peak_index in self.selected_peaks:
                            self.selected_peaks.remove(peak_index)
                        else:
                            self.selected_peaks.add(peak_index)
                        self.peak_selection_changed.emit()  # Emit signal for updates
                        self.update()

    def mouseMoveEvent(self, event) -> None:
        """
        Handle mouse movement for hover effects and time display

        Args:
            event: Qt mouse event
        """
        self.mouse_position = event.position()
        self.update()

    def wheelEvent(self, event) -> None:
        """
        Handle mouse wheel events for zooming

        Args:
            event: Qt wheel event
        """
        if not self.analyzer or not self.analyzer.is_analyzed:
            return

        # Get mouse position for zoom centering
        mouse_x = event.position().x()
        content_rect = self._get_content_rect()

        if not content_rect.contains(event.position().toPoint()):
            return

        # Calculate the position under the mouse before zooming
        mouse_norm_pos = self._pixel_to_position(mouse_x)

        # Determine zoom direction and calculate new zoom factor
        zoom_in = event.angleDelta().y() > 0
        new_zoom = self.zoom_factor * (self.zoom_increment if zoom_in else 1 / self.zoom_increment)
        new_zoom = self._clamp_zoom(new_zoom)

        if new_zoom != self.zoom_factor:
            # Store old zoom for comparison
            old_zoom = self.zoom_factor
            self.zoom_factor = new_zoom

            # Calculate new offset to maintain mouse position
            new_offset = self._calculate_offset_for_zoom(mouse_norm_pos, mouse_x)
            self._set_offset(new_offset)

            # Emit signal and update
            self.zoom_changed.emit(self.zoom_factor)
            self.logger.debug(f"Zoom changed: {old_zoom:.2f} -> {new_zoom:.2f}")
            self.update()

    def keyPressEvent(self, event) -> None:
        """
        Handle keyboard navigation and controls

        Args:
            event: Qt key event
        """
        if not self.analyzer or not self.analyzer.is_analyzed:
            return

        key = event.key()

        # Zoom controls
        if key in (Qt.Key_Plus, Qt.Key_Equal):
            self._zoom_in()
        elif key == Qt.Key_Minus:
            self._zoom_out()
        elif key == Qt.Key_0:
            self._reset_zoom()

        # Navigation
        elif key == Qt.Key_Left:
            self._move_position(-0.05 / self.zoom_factor)
        elif key == Qt.Key_Right:
            self._move_position(0.05 / self.zoom_factor)
        elif key == Qt.Key_Home:
            self._set_position(0.0)
        elif key == Qt.Key_End:
            self._set_position(1.0)
        elif key == Qt.Key_Space:
            self._center_current_position()

    def _get_content_rect(self) -> QRect:
        """
        Calculate the content rectangle accounting for margins and axes

        Returns:
            QRect: Content drawing area
        """
        width = self.width()
        height = self.height()

        # Account for axes and margins
        left_margin = 45  # Space for amplitude scale
        right_margin = 10
        top_margin = 10
        bottom_margin = 20  # Space for time axis

        return QRect(
            left_margin,
            top_margin,
            width - (left_margin + right_margin),
            height - (top_margin + bottom_margin)
        )

    def _pixel_to_position(self, x: float) -> float:
        """
        Convert pixel X coordinate to normalized position

        Args:
            x: Pixel X coordinate

        Returns:
            float: Normalized position (0.0-1.0)
        """
        content_rect = self._get_content_rect()
        if content_rect.width() <= 0:
            return 0.0

        relative_x = (x - content_rect.left()) / content_rect.width()
        return self.offset + (relative_x / self.zoom_factor)

    def _position_to_pixel(self, position: float) -> float:
        """
        Convert normalized position to pixel X coordinate

        Args:
            position: Normalized position (0.0-1.0)

        Returns:
            float: Pixel X coordinate
        """
        content_rect = self._get_content_rect()
        relative_pos = (position - self.offset) * self.zoom_factor
        return content_rect.left() + (relative_pos * content_rect.width())

    def _clamp_zoom(self, zoom: float) -> float:
        """
        Clamp zoom factor to valid range

        Args:
            zoom: Proposed zoom factor

        Returns:
            float: Clamped zoom factor
        """
        return max(self.min_zoom, min(self.max_zoom, zoom))

    def _calculate_offset_for_zoom(self, mouse_norm_pos: float, mouse_x: float) -> float:
        """
        Calculate new offset to maintain mouse position during zoom

        Args:
            mouse_norm_pos: Normalized position under mouse
            mouse_x: Mouse X coordinate in pixels

        Returns:
            float: New offset value
        """
        content_rect = self._get_content_rect()
        relative_x = (mouse_x - content_rect.left()) / content_rect.width()
        new_offset = mouse_norm_pos - (relative_x / self.zoom_factor)

        # Clamp offset to valid range
        max_offset = max(0.0, 1.0 - (1.0 / self.zoom_factor))
        return max(0.0, min(max_offset, new_offset))

    def paintEvent(self, event) -> None:
        """Main paint event handler"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        try:
            if not self.analyzer:
                self.logger.warning("No analyzer available")
                self._draw_placeholder(painter)
                return

            if not self.analyzer.is_analyzed:
                self.logger.warning("Analyzer not analyzed")
                self._draw_placeholder(painter)
                return

            if not hasattr(self.analyzer, 'waveform_data') or self.analyzer.waveform_data is None:
                self.logger.warning("No waveform data available")
                self._draw_placeholder(painter)
                return

            self.logger.info(f"Drawing waveform with data length: {len(self.analyzer.waveform_data)}")

            # Get content rectangle
            content_rect = self._get_content_rect()

            # Draw background and grid
            self._draw_background(painter, content_rect)
            if self.show_grid:
                self._draw_grid(painter, content_rect)

            # Draw waveform
            self._draw_waveform(painter, content_rect)

            # Draw peaks if available
            self._draw_peak_markers(painter, content_rect)

            # Draw position marker
            self._draw_position_marker(painter, content_rect)

            # Draw time at mouse position
            if self.mouse_position and content_rect.contains(self.mouse_position.toPoint()):
                self._draw_mouse_time_marker(painter, content_rect)

        except Exception as e:
            self.logger.error(f"Error in paintEvent: {str(e)}", exc_info=True)
            self._draw_error_state(painter)
        finally:
            painter.end()

    def _draw_background(self, painter: QPainter, rect: QRect) -> None:
        """
        Draw widget background with gradient

        Args:
            painter: Qt painter
            rect: Content rectangle
        """
        # Draw main background
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, self.background_color.lighter(120))
        gradient.setColorAt(1, self.background_color)
        painter.fillRect(self.rect(), gradient)

        # Draw axis areas
        axis_color = self.background_color.darker(110)

        # Amplitude axis background
        painter.fillRect(
            0, 0, rect.left(), self.height(),
            axis_color
        )

        # Time axis background
        painter.fillRect(
            rect.left(), rect.bottom(), rect.width(), self.height() - rect.bottom(),
            axis_color
        )

        # Draw borders
        border_pen = QPen(self.grid_color.lighter(120))
        painter.setPen(border_pen)
        painter.drawLine(rect.left(), 0, rect.left(), self.height())
        painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())

    def _draw_waveform(self, painter: QPainter, rect: QRect) -> None:
        """Draw the actual waveform visualization"""
        if not self.analyzer or not self.analyzer.is_analyzed:
            self.logger.warning("Cannot draw waveform - analyzer not ready")
            return

        if not hasattr(self.analyzer, 'waveform_data') or self.analyzer.waveform_data is None:
            self.logger.warning("Cannot draw waveform - no waveform data")
            return

        # Get waveform points from analyzer
        points = self.analyzer.get_waveform_points(
            rect.width(),
            rect.height(),
            self.offset,
            self.zoom_factor
        )

        if not points:
            self.logger.warning("No waveform points returned from analyzer")
            return

        # Create gradient for waveform
        gradient = QLinearGradient(0, 0, 0, rect.height())
        gradient.setColorAt(0, self.gradient_top)
        gradient.setColorAt(0.5, self.gradient_middle)
        gradient.setColorAt(1, self.gradient_bottom)

        # Create path for waveform
        path = QPainterPath()
        center_y = rect.top() + (rect.height() / 2)

        # Start at the center
        path.moveTo(rect.left() + points[0][0], center_y)

        # Add top edge
        for x, y1, _ in points:
            path.lineTo(rect.left() + x, y1)

        # Add right edge to center
        if points:
            path.lineTo(rect.left() + points[-1][0], center_y)

        # Add bottom edge (in reverse)
        for x, _, y2 in reversed(points):
            path.lineTo(rect.left() + x, y2)

        # Close path
        path.lineTo(rect.left() + points[0][0], center_y)

        # Draw filled waveform
        painter.setOpacity(0.85)
        painter.fillPath(path, QBrush(gradient))

        # Draw outline
        painter.setOpacity(1.0)
        outline_pen = QPen(self.waveform_color.lighter(120), 1.0)
        painter.setPen(outline_pen)
        painter.drawPath(path)

    def _draw_grid(self, painter: QPainter, rect: QRect) -> None:
        """
        Draw time and amplitude grid

        Args:
            painter: Qt painter
            rect: Content rectangle
        """
        if not self.analyzer:
            return

        # Draw center line
        center_y = rect.top() + (rect.height() / 2)
        painter.setPen(QPen(self.grid_color, 1, Qt.DashLine))
        painter.drawLine(rect.left(), center_y, rect.right(), center_y)

        # Draw amplitude grid lines
        if self.show_db_scale:
            self._draw_db_grid(painter, rect)

        # Draw time grid
        if self.show_time_markers:
            self._draw_time_grid(painter, rect)

    def _draw_db_grid(self, painter: QPainter, rect: QRect) -> None:
        """
        Draw decibel scale grid lines and labels

        Args:
            painter: Qt painter
            rect: Content rectangle
        """
        db_levels = [
            (-24, "−24 dB"),
            (-12, "−12 dB"),
            (-6, "−6 dB"),
            (0, "0 dB"),
            (6, "+6 dB"),
            (12, "+12 dB")
        ]

        center_y = rect.top() + (rect.height() / 2)

        for db, label in db_levels:
            # Convert dB to amplitude ratio
            if db < 0:
                ratio = 1.0 / (10 ** (abs(db) / 20))
            else:
                ratio = 10 ** (db / 20)

            # Calculate y position
            y_offset = ratio * rect.height() * self.amplitude_scale / 2
            y_pos = center_y + (-y_offset if db < 0 else y_offset)

            if rect.top() <= y_pos <= rect.bottom():
                # Draw grid line
                painter.setPen(QPen(self.grid_color.lighter(110), 1, Qt.DotLine))
                painter.drawLine(rect.left(), y_pos, rect.right(), y_pos)

                # Draw label
                painter.setPen(self.text_color)
                metrics = QFontMetrics(painter.font())
                text_rect = metrics.boundingRect(label)
                text_rect.moveRight(rect.left() - 5)
                text_rect.moveCenter(QPoint(text_rect.center().x(), int(y_pos)))
                painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, label)

    def _draw_time_grid(self, painter: QPainter, rect: QRect) -> None:
        """
        Draw time grid lines and labels

        Args:
            painter: Qt painter
            rect: Content rectangle
        """
        if not self.analyzer:
            return

        # Calculate visible duration
        visible_duration = self.analyzer.duration_seconds / self.zoom_factor

        # Choose appropriate time interval based on zoom
        intervals = [
            0.001, 0.005, 0.01, 0.05, 0.1, 0.5,  # Milliseconds
            1, 2, 5, 10, 15, 30,  # Seconds
            60, 120, 300, 600  # Minutes
        ]

        interval = intervals[-1]
        for i in intervals:
            if visible_duration / i < 10:  # Aim for ~10 grid lines
                interval = i
                break

        # Calculate time range
        start_time = self.offset * self.analyzer.duration_seconds
        end_time = start_time + visible_duration

        # Round start time to nearest interval
        grid_time = math.floor(start_time / interval) * interval

        # Track label positions to prevent overlap
        last_label_rect = None

        while grid_time <= end_time:
            # Convert time to x position
            norm_pos = grid_time / self.analyzer.duration_seconds
            x_pos = self._position_to_pixel(norm_pos)

            if rect.left() <= x_pos <= rect.right():
                # Draw grid line
                is_major = (grid_time / interval) % 5 == 0
                painter.setPen(QPen(
                    self.grid_color.lighter(120 if is_major else 100),
                    1,
                    Qt.DashLine if is_major else Qt.DotLine
                ))
                painter.drawLine(x_pos, rect.top(), x_pos, rect.bottom())

                # Format and draw time label
                if is_major:
                    time_str = self._format_time(grid_time)
                    metrics = QFontMetrics(painter.font())
                    text_rect = metrics.boundingRect(time_str)
                    text_rect.moveCenter(QPoint(int(x_pos), rect.bottom() + text_rect.height()))

                    # Check for overlap
                    if not last_label_rect or not text_rect.intersects(last_label_rect):
                        painter.setPen(self.text_color)
                        painter.drawText(text_rect, Qt.AlignCenter, time_str)
                        last_label_rect = text_rect

            grid_time += interval

    def _draw_peak_markers(self, painter: QPainter, rect: QRect) -> None:
        """Draw selectable peak markers, visible at higher zoom levels."""
        if not self.analyzer or not hasattr(self.analyzer, 'peaks'):
            return

        if self.zoom_factor < 5.0:  # Visibility threshold
            return

        markers = self.analyzer.get_peak_markers(
            rect.width(),
            rect.height(),
            self.offset,
            self.zoom_factor
        )

        if not markers:
            return

        painter.save()
        painter.setClipRect(rect)

        for i, (x, y1, _, _) in enumerate(markers):  # Use enumerate to get index
            x_pos = rect.left() + x

            is_selected = i in self.selected_peaks  # Use index for selection
            color = QColor("red") if is_selected else QColor("darkRed")
            pen_width = 2 if is_selected else 1

            painter.setPen(QPen(color, pen_width))

            marker_top_y = y1 - 10
            marker_top_y = max(0, marker_top_y)

            painter.drawLine(x_pos, y1, x_pos, marker_top_y)

            dot_size = 8 if is_selected else 6
            painter.setBrush(color)
            painter.drawEllipse(QPoint(x_pos, marker_top_y), dot_size // 2, dot_size // 2)

        painter.restore()

    def _find_peak_index(self, x: int, y: int, markers: List[Tuple]) -> Optional[int]:
        """Find index of clicked peak marker (adjusted for upward lines)."""
        for i, (mx, my1, _, _) in enumerate(markers):  # Use y1 for click detection
            mx += self._get_content_rect().left()
            marker_top_y = my1 - 10  # Adjust for marker line height
            if abs(x - mx) <= 5 and abs(y - marker_top_y) <= 10:  # Increased y-tolerance
                return i
        return None

    def _draw_position_marker(self, painter: QPainter, rect: QRect) -> None:
        """
        Draw current position marker

        Args:
            painter: Qt painter
            rect: Content rectangle
        """
        if not self.analyzer:
            return

        # Calculate x position
        x_pos = self._position_to_pixel(self.current_position)

        if rect.left() <= x_pos <= rect.right():
            # Draw position line
            painter.setPen(QPen(self.position_marker_color, 2))
            painter.drawLine(x_pos, 0, x_pos, self.height())

            # Draw time label
            if self.analyzer.duration_seconds > 0:
                time_seconds = self.current_position * self.analyzer.duration_seconds
                time_str = self._format_time(time_seconds)

                metrics = QFontMetrics(painter.font())
                text_rect = metrics.boundingRect(time_str)
                text_rect.moveCenter(QPoint(int(x_pos), text_rect.height() + 5))

                # Draw background
                painter.fillRect(
                    text_rect.adjusted(-4, -2, 4, 2),
                    QColor(0, 0, 0, 180)
                )

                # Draw text
                painter.setPen(self.position_marker_color)
                painter.drawText(text_rect, Qt.AlignCenter, time_str)

    def _draw_mouse_time_marker(self, painter: QPainter, rect: QRect) -> None:
        """
        Draw time marker at mouse position

        Args:
            painter: Qt painter
            rect: Content rectangle
        """
        if not self.analyzer or not self.mouse_position:
            return

        mouse_x = self.mouse_position.x()
        if not rect.left() <= mouse_x <= rect.right():
            return

        # Calculate time at mouse position
        norm_pos = self._pixel_to_position(mouse_x)
        if not 0.0 <= norm_pos <= 1.0:
            return

        time_seconds = norm_pos * self.analyzer.duration_seconds
        time_str = self._format_time(time_seconds)

        # Draw marker line
        painter.setPen(QPen(self.mouse_marker_color, 1, Qt.DashLine))
        painter.drawLine(mouse_x, rect.top(), mouse_x, rect.bottom())

        # Draw time label
        metrics = QFontMetrics(painter.font())
        text_rect = metrics.boundingRect(time_str)
        text_rect.moveCenter(QPoint(
            int(mouse_x),
            rect.bottom() - text_rect.height() - 5
        ))

        # Draw background
        painter.fillRect(
            text_rect.adjusted(-4, -2, 4, 2),
            QColor(0, 0, 0, 150)
        )

        # Draw text
        painter.setPen(self.mouse_marker_color)
        painter.drawText(text_rect, Qt.AlignCenter, time_str)

    def _draw_placeholder(self, painter: QPainter) -> None:
        """
        Draw placeholder when no waveform data is available

        Args:
            painter: Qt painter
        """
        # Draw basic background
        painter.fillRect(self.rect(), self.background_color)

        # Draw placeholder text
        painter.setPen(self.text_color)
        painter.drawText(
            self.rect(),
            Qt.AlignCenter,
            "Waveform visualization will appear here"
        )

        # Draw simple sine wave as placeholder
        center_y = self.height() / 2
        amplitude = self.height() * 0.2

        path = QPainterPath()
        path.moveTo(0, center_y)

        for x in range(0, self.width(), 2):
            y = center_y + math.sin(x / 30.0) * amplitude
            path.lineTo(x, y)

        painter.setPen(QPen(self.waveform_color.darker(150), 2))
        painter.drawPath(path)

    def _draw_error_state(self, painter: QPainter) -> None:
        """
        Draw error state visualization

        Args:
            painter: Qt painter
        """
        # Draw error background
        painter.fillRect(self.rect(), self.background_color.darker(120))

        # Draw error message
        painter.setPen(QColor(255, 100, 100))
        painter.drawText(
            self.rect(),
            Qt.AlignCenter,
            "Error rendering waveform"
        )

    def _format_time(self, seconds: float) -> str:
        """
        Format time in seconds to string

        Args:
            seconds: Time in seconds

        Returns:
            str: Formatted time string (MM:SS.mmm)
        """
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60

        if seconds < 1:
            # Show milliseconds for very short times
            return f"{remaining_seconds:.3f}s"
        elif seconds < 60:
            # Show seconds for times under a minute
            return f"{remaining_seconds:.2f}s"
        else:
            # Show MM:SS format for longer times
            return f"{minutes}:{remaining_seconds:05.2f}"

    def set_analyzer(self, analyzer) -> None:
        """Set the waveform analyzer instance"""
        self.logger.info("Setting analyzer in WaveformView")
        self.analyzer = analyzer

        if self.analyzer:
            if self.analyzer.is_analyzed:
                self.logger.info("Analyzer is analyzed")
                if hasattr(self.analyzer, 'waveform_data') and self.analyzer.waveform_data is not None:
                    self.logger.info(f"Waveform data present, length: {len(self.analyzer.waveform_data)}")
                    # Reset view state
                    self.zoom_factor = 1.0
                    self.offset = 0.0
                    self.current_position = 0.0
                else:
                    self.logger.warning("No waveform data available")
            else:
                self.logger.warning("Analyzer not analyzed")
        else:
            self.logger.warning("No analyzer provided")

        self.update()

    def set_position(self, position: float) -> None:
        """
        Set current playback position

        Args:
            position: Normalized position (0.0-1.0)
        """
        self._set_position(position)
        self.update()

    def _set_position(self, position: float) -> None:
        """
        Internal method to set position with validation

        Args:
            position: Normalized position (0.0-1.0)
        """
        self.current_position = max(0.0, min(1.0, position))

        # Center position in view if outside visible area
        visible_start = self.offset
        visible_end = self.offset + (1.0 / self.zoom_factor)
        margin = 0.1 / self.zoom_factor

        if (position < visible_start + margin or
                position > visible_end - margin):
            self._center_current_position()

    def _center_current_position(self) -> None:
        """Center the current position in the view"""
        self._set_offset(
            self.current_position - (0.5 / self.zoom_factor)
        )

    def set_zoom(self, factor: float, animate: bool = False) -> None:
        """
        Set zoom factor with optional animation

        Args:
            factor: New zoom factor
            animate: Whether to animate the zoom transition
        """
        # Clamp zoom factor to valid range
        new_zoom = self._clamp_zoom(factor)

        if new_zoom == self.zoom_factor:
            return

        # Store old zoom for comparison
        old_zoom = self.zoom_factor
        self.zoom_factor = new_zoom

        # Adjust offset to keep center position
        visible_center = self.offset + (0.5 / old_zoom)
        new_offset = visible_center - (0.5 / new_zoom)
        self._set_offset(new_offset)

        # Emit signal and update
        self.zoom_changed.emit(self.zoom_factor)
        self.logger.debug(f"Zoom changed: {old_zoom:.2f} -> {new_zoom:.2f}")
        self.update()

    def _zoom_in(self) -> None:
        """Zoom in by one increment"""
        self.set_zoom(self.zoom_factor * self.zoom_increment, animate=True)

    def _zoom_out(self) -> None:
        """Zoom out by one increment"""
        self.set_zoom(self.zoom_factor / self.zoom_increment, animate=True)

    def _reset_zoom(self) -> None:
        """Reset zoom to default level"""
        self.set_zoom(1.0, animate=True)

    def _set_offset(self, offset: float) -> None:
        """
        Set the horizontal offset with validation

        Args:
            offset: New offset value (0.0-1.0)
        """
        # Calculate maximum valid offset based on zoom
        max_offset = max(0.0, 1.0 - (1.0 / self.zoom_factor))

        # Clamp offset to valid range
        self.offset = max(0.0, min(max_offset, offset))

        # Force update
        self.update()

    def _move_position(self, delta: float) -> None:
        """
        Move the current position by a delta amount

        Args:
            delta: Amount to move position by (-1.0 to 1.0)
        """
        new_pos = self.current_position + delta
        self._set_position(new_pos)
        self.position_changed.emit(new_pos)
        self.update()

    @Slot(bool)
    def _on_waveform_loaded(self, success: bool) -> None:
        """Handle waveform loading completion"""
        self.is_processing = False
        self.progress_bar.setVisible(False)

        if not success:
            QMessageBox.warning(self, "Error", "Could not process waveform data.")
            return

        try:
            # Update title
            if self.music_file_info:
                title = f"Waveform: {self.music_file_info['filename']} - {self.music_file_info['duration']}"
                self.title_label.setText(title)

            # Create analysis info
            analysis_info = self._create_analysis_info()

            # Set up waveform view
            if self.analyzer and self.analyzer.is_analyzed:
                self.waveform_view.set_analyzer(self.analyzer)
                self.waveform_view.update()

                # Initialize UI state
                self._init_playback_state()
                self._enable_controls()
                self._update_duration_display()

                # Force peak display update - Added this line
                self._force_peak_display()

                # Set up media player
                self._setup_media_player()

                # Emit ready signal
                self.show_generation_ready.emit(analysis_info)
            else:
                self.logger.error("Analyzer not ready or not analyzed")
                QMessageBox.warning(self, "Error", "Waveform analysis incomplete")

        except Exception as e:
            self.logger.error(f"Error in waveform loading completion: {str(e)}", exc_info=True)
            QMessageBox.warning(self, "Error", f"Error setting up waveform: {str(e)}")
