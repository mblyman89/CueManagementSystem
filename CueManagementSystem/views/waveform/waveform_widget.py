from PySide6.QtWidgets import QWidget, QApplication, QMessageBox
from PySide6.QtCore import Qt, Signal, QRect, QSize, QPoint, Slot, QTimer, QThread
from PySide6.QtGui import (
    QPainter, QPen, QColor, QBrush, QLinearGradient,
    QPainterPath, QFontMetrics, QFont
)
import math
import logging
import time
import numpy as np
from typing import Optional, List, Tuple, Dict, Any
from views.waveform.enhanced_waveform_renderer import (
    ProfessionalWaveformRenderer, WaveformRenderMode, ColorScheme, RenderingConfig
)


class BackgroundRenderer(QThread):
    """Background thread for expensive rendering operations"""
    rendering_complete = Signal(object)  # Emits rendered data

    def __init__(self, renderer, audio_data, sample_rate, width, height, offset, zoom):
        super().__init__()
        self.renderer = renderer
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        self.width = width
        self.height = height
        self.offset = offset
        self.zoom = zoom
        self.should_stop = False

    def run(self):
        """Run the rendering in background"""
        if not self.should_stop:
            try:
                result = self.renderer.render_waveform_points(
                    self.audio_data, self.sample_rate,
                    self.width, self.height, self.offset, self.zoom
                )
                if not self.should_stop:
                    self.rendering_complete.emit(result)
            except Exception as e:
                logging.error(f"Background rendering error: {e}")

    def stop(self):
        """Stop the background rendering"""
        self.should_stop = True


try:
    from utils.audio.performance_monitor import profile_method, monitor
except ImportError:
    try:
        from utils.audio.performance_monitor import profile_method, monitor
    except ImportError:
        # Fallback decorators if performance_monitor is not available
        def profile_method(method_name):
            def decorator(func):
                return func

            return decorator


        class MockMonitor:
            def get_performance_summary(self):
                return "Performance monitoring not available"


        monitor = MockMonitor()


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
        """Initialize the optimized waveform widget"""
        super().__init__(parent)
        print("🎨 Initializing OptimizedWaveformWidget")

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

        # OPTIMIZATION: Performance improvements
        self.visible_peaks = []  # Only peaks in current view
        self.peak_cache: Dict[str, Any] = {}  # Cache rendered peak markers
        self.waveform_cache = None  # Cache waveform rendering
        self.last_render_time = 0
        self.render_throttle = 0.016  # 60 FPS max

        # SEGMENT-BASED: No artificial limits - show all segment-appropriate peaks
        self.max_visible_peaks = None  # No artificial limits
        self.peak_render_batch_size = None  # No batching needed
        self.lazy_render_timer = QTimer()
        self.lazy_render_timer.timeout.connect(self._render_next_batch)
        self.pending_peak_batches = []

        # Performance tracking
        self.render_times = []
        self.peak_render_times = []

        # Initialize warning tracking
        self._logged_warnings = {
            'no_analyzer': False,
            'not_analyzed': False,
            'no_waveform_data': False
        }

        # Mouse tracking
        self.mouse_position = None
        self.mouse_drag_start = None
        self.mouse_dragging = False
        self.drag_start_offset = 0.0
        self.mouse_drag_start = None
        self.mouse_dragging = False
        self.drag_start_offset = 0.0

        # Professional renderer
        self.professional_renderer = ProfessionalWaveformRenderer()
        self.rendering_config = RenderingConfig()
        self.current_render_mode = WaveformRenderMode.RMS_ENVELOPE
        self.current_color_scheme = ColorScheme.PROFESSIONAL_DARK
        self.use_professional_rendering = True

        # Background rendering for performance
        self.background_renderer = None
        self.background_render_timer = QTimer()
        self.background_render_timer.setSingleShot(True)
        self.background_render_timer.timeout.connect(self._start_background_render)
        self.background_render_delay = 100  # 100ms delay before background render
        self.cached_render_result = None

        # Initialize warning tracking
        self._logged_warnings = {
            'no_analyzer': False,
            'not_analyzed': False,
            'no_waveform_data': False
        }

        # Selected peaks tracking
        self.selected_peaks = set()

        # Manual peak placement mode
        self.manual_peak_mode = False
        self.manual_peaks = []  # Store manually placed peaks
        self.show_analyzer_peaks = True  # Control visibility of analyzer-detected peaks
        self.hidden_detected_peaks = set()  # Track hidden detected peaks by index

        # Double shot mode
        self.double_shot_mode = False
        self.double_shot_peaks = set()  # Track peaks marked as double shot by their time value

        # Initialize colors first to ensure they're available
        self.background_color = QColor(20, 20, 25)
        self.waveform_color = QColor(65, 175, 255)
        self.grid_color = QColor(60, 60, 70)
        self.text_color = QColor(200, 200, 200)
        self.position_marker_color = QColor(255, 100, 100)
        self.peak_marker_color = QColor(255, 210, 65)
        self.mouse_marker_color = QColor(200, 200, 200, 120)
        self.gradient_top = QColor(80, 185, 255)
        self.gradient_middle = QColor(50, 150, 250)
        self.gradient_bottom = QColor(45, 145, 235)

        # Configure logging
        self._init_logging()

    def smart_update(self):
        """Smart update that uses background rendering for expensive operations"""
        # Check if we need expensive rendering
        complex_modes = [
            WaveformRenderMode.SPECTRAL_COLOR,
            WaveformRenderMode.FREQUENCY_BANDS,
            WaveformRenderMode.HARMONIC_PERCUSSIVE
        ]

        if (self.current_render_mode in complex_modes and
                self.analyzer and hasattr(self.analyzer, 'waveform_data') and
                len(self.analyzer.waveform_data) > 100000):  # Large datasets

            # Use background rendering for large, complex datasets
            self.background_render_timer.start(self.background_render_delay)
        else:
            # Use immediate rendering for simple cases
            self.update()

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
        # OPTIMIZATION: Clear cached positions on resize
        if hasattr(self, '_last_mouse_pos'):
            delattr(self, '_last_mouse_pos')
        self.update()  # Trigger repaint

    def mousePressEvent(self, event) -> None:
        """Handle mouse clicks for position changes, peak selection, and manual peak placement."""
        if not self.analyzer or not self.analyzer.has_waveform_data():
            return

        if event.button() == Qt.LeftButton:
            click_x = event.position().x()
            content_rect = self._get_content_rect()

            if content_rect.contains(event.position().toPoint()):
                # Handle manual peak refinement mode
                if self.manual_peak_mode:
                    # First check if clicking on existing manual peak to delete it
                    manual_peak_index = self._is_manual_peak_at_position(event.position().x(), event.position().y(), content_rect)
                    if manual_peak_index is not False:  # manual_peak_index will be False if no peak is found
                        self._delete_manual_peak_at_index(manual_peak_index)
                        return
                    # Check if clicking on detected peak to hide it
                    elif self._is_detected_peak_at_position(event.position().x(), event.position().y(), content_rect):
                        self._toggle_detected_peak_visibility(event.position().x(), event.position().y(), content_rect)
                        return
                    else:
                        # Add new manual peak
                        self._handle_manual_peak_placement(event, content_rect)
                        return

                # Handle double shot mode
                elif self.double_shot_mode:
                    # First check if clicking on a detected peak to mark it as double shot
                    peak_index = self._is_detected_peak_at_position(event.position().x(), event.position().y(), content_rect)
                    if peak_index is not False:  # peak_index will be False if no peak is found
                        # Get the peak's time value to use as a unique identifier
                        peak_time = self.visible_peaks[peak_index].time

                        # Toggle double shot status for this detected peak
                        if peak_time in self.double_shot_peaks:
                            self.double_shot_peaks.remove(peak_time)
                            self.logger.info(f"Removed detected peak at time {peak_time:.3f}s from double shot peaks")
                        else:
                            self.double_shot_peaks.add(peak_time)
                            self.logger.info(f"Added detected peak at time {peak_time:.3f}s to double shot peaks")
                        self.update()  # Refresh display
                        return

                    # If not a detected peak, check if it's a manual peak
                    manual_peak_index = self._is_manual_peak_at_position(event.position().x(), event.position().y(), content_rect)
                    if manual_peak_index is not False:  # manual_peak_index will be False if no peak is found
                        # Get the manual peak's time value
                        manual_peak_time = self.manual_peaks[manual_peak_index].time

                        # Create a unique identifier for manual peaks to avoid conflicts with detected peaks
                        # Use 'm' prefix followed by the time to distinguish from detected peaks
                        manual_peak_id = f"m{manual_peak_time}"

                        # Toggle double shot status for this manual peak
                        if manual_peak_id in self.double_shot_peaks:
                            self.double_shot_peaks.remove(manual_peak_id)
                            self.logger.info(f"Removed manual peak at time {manual_peak_time:.3f}s from double shot peaks")
                        else:
                            self.double_shot_peaks.add(manual_peak_id)
                            self.logger.info(f"Added manual peak at time {manual_peak_time:.3f}s to double shot peaks")
                        self.update()  # Refresh display
                        return

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
                        # Check if it's a manual peak (for deletion)
                        manual_peak_index = self._is_manual_peak_at_position(event.position().x(), event.position().y(), content_rect)
                        if manual_peak_index is not False:  # manual_peak_index will be False if no peak is found
                            self._delete_manual_peak_at_index(manual_peak_index)
                        else:
                            # Regular peak selection
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

        # OPTIMIZATION: Only update if mouse position changed significantly
        # This prevents excessive redraws during small mouse movements
        current_time = time.time()
        if hasattr(self, '_last_mouse_update_time'):
            if current_time - self._last_mouse_update_time < 0.016:  # ~60fps limit
                return

        self._last_mouse_update_time = current_time

        # FIX: Use full update to prevent grey trails from partial updates
        # Partial updates can cause incomplete background clearing
        self.update()

    def wheelEvent(self, event) -> None:
        """
        Handle mouse wheel events for zooming

        Args:
            event: Qt wheel event
        """
        if not self.analyzer or not self.analyzer.has_waveform_data():
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

            # OPTIMIZATION: Throttle zoom updates
            current_time = time.time()
            if not hasattr(self, '_last_zoom_update') or current_time - self._last_zoom_update > 0.05:
                self._last_zoom_update = current_time
                self.update()

    def keyPressEvent(self, event) -> None:
        """
        Handle keyboard navigation and controls

        Args:
            event: Qt key event
        """
        if not self.analyzer or not self.analyzer.has_waveform_data():
            return

        key = event.key()

        # Zoom controls
        if key in (Qt.Key_Plus, Qt.Key_Equal):
            self._zoom_in()
        elif key == Qt.Key_Minus:
            self._zoom_out()
        elif key == Qt.Key_0:
            self._reset_zoom()

        # Navigation - Scroll through waveform
        elif key == Qt.Key_Left:
            self._scroll_left()
        elif key == Qt.Key_Right:
            self._scroll_right()
        elif key == Qt.Key_Home:
            self._scroll_to_start()
        elif key == Qt.Key_End:
            self._scroll_to_end()
        elif key == Qt.Key_Space:
            self._center_current_position()

        # Position movement (with Shift modifier)
        elif key == Qt.Key_Left and event.modifiers() & Qt.ShiftModifier:
            self._move_position(-0.05 / self.zoom_factor)
        elif key == Qt.Key_Right and event.modifiers() & Qt.ShiftModifier:
            self._move_position(0.05 / self.zoom_factor)
        elif key == Qt.Key_Home and event.modifiers() & Qt.ShiftModifier:
            self._set_position(0.0)
        elif key == Qt.Key_End and event.modifiers() & Qt.ShiftModifier:
            self._set_position(1.0)

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

    # Class variable to track if warnings have been logged
    _logged_warnings = {
        'no_analyzer': False,
        'not_analyzed': False,
        'no_waveform_data': False
    }

    @profile_method("paintEvent")
    def paintEvent(self, event) -> None:
        """Optimized paint event handler with performance improvements"""
        start_time = time.time()

        # OPTIMIZATION: Throttle rendering for performance
        current_time = time.time()
        if current_time - self.last_render_time < self.render_throttle:
            return  # Skip this render to maintain 60 FPS

        self.last_render_time = current_time

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)  # Disable for performance

        # OPTIMIZATION: Only paint the update region if it's a partial update
        update_rect = event.rect()
        if update_rect != self.rect():
            painter.setClipRect(update_rect)

        try:
            if not self.analyzer:
                # Only log this message once
                if not self._logged_warnings['no_analyzer']:
                    self.logger.debug("No analyzer available")
                    self._logged_warnings['no_analyzer'] = True
                self._draw_placeholder(painter)
                return

            # Reset the warning flag if analyzer becomes available
            self._logged_warnings['no_analyzer'] = False

            # We don't need analysis to be complete to show the waveform
            # Just check if we have waveform data

            if not hasattr(self.analyzer, 'waveform_data') or self.analyzer.waveform_data is None:
                # Only log this message once
                if not self._logged_warnings['no_waveform_data']:
                    self.logger.debug("No waveform data available")
                    self._logged_warnings['no_waveform_data'] = True
                self._draw_placeholder(painter)
                return

            # Reset the warning flag if waveform data becomes available
            self._logged_warnings['no_waveform_data'] = False

            # Only log this at debug level to reduce console spam
            self.logger.debug(f"Drawing waveform with data length: {len(self.analyzer.waveform_data)}")

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
        """Draw the actual waveform visualization with professional rendering"""
        if not self.analyzer:
            self.logger.debug("Cannot draw waveform - no analyzer")
            return

        # Check for waveform data - we don't need analysis to be complete to show the waveform
        if not hasattr(self.analyzer, 'waveform_data') or self.analyzer.waveform_data is None:
            self.logger.debug("Cannot draw waveform - no waveform data")
            return

        if not self.analyzer.has_waveform_data():
            self.logger.debug("Cannot draw waveform - waveform data not properly loaded")
            return

        # Use professional rendering if enabled
        if self.use_professional_rendering and hasattr(self.analyzer, 'sample_rate'):
            self._draw_professional_waveform(painter, rect)
        else:
            self._draw_basic_waveform(painter, rect)

    def _draw_professional_waveform(self, painter: QPainter, rect: QRect) -> None:
        """Draw waveform using professional renderer"""
        try:
            # Validate analyzer data first
            if not hasattr(self.analyzer, 'waveform_data') or self.analyzer.waveform_data is None:
                self.logger.debug("No waveform data available for professional rendering")
                self._draw_basic_waveform(painter, rect)
                return

            if not hasattr(self.analyzer, 'sample_rate') or self.analyzer.sample_rate is None:
                self.logger.debug("No sample rate available for professional rendering")
                self._draw_basic_waveform(painter, rect)
                return

            # Update rendering configuration
            self.rendering_config.mode = self.current_render_mode
            self.rendering_config.color_scheme = self.current_color_scheme
            self.professional_renderer.config = self.rendering_config

            # Debug: Show current settings
            if not hasattr(self,
                           '_last_debug_time') or time.time() - self._last_debug_time > 2.0:  # Debug every 2 seconds max
                print(
                    f"🎨 PROFESSIONAL RENDERING: Mode={self.current_render_mode.value}, Colors={self.current_color_scheme.value}")
                print(
                    f"🎛️ SETTINGS: Smoothing={self.rendering_config.smoothing_factor:.3f}, DynamicRange={self.rendering_config.dynamic_range_db:.1f}dB, FreqBands={self.rendering_config.frequency_bands}")
                self._last_debug_time = time.time()

            # Debug: Log data type and structure
            waveform_data = self.analyzer.waveform_data
            self.logger.debug(f"Waveform data type: {type(waveform_data)}")
            if hasattr(waveform_data, 'shape'):
                self.logger.debug(f"Waveform data shape: {waveform_data.shape}")
            elif isinstance(waveform_data, (list, tuple)):
                self.logger.debug(f"Waveform data length: {len(waveform_data)}")
                if len(waveform_data) > 0:
                    self.logger.debug(f"First element type: {type(waveform_data[0])}")

            # Get professional waveform points
            points = self.professional_renderer.render_waveform_points(
                waveform_data,
                self.analyzer.sample_rate,
                rect.width(),
                rect.height(),
                self.offset,
                self.zoom_factor
            )

            if not points:
                self.logger.warning("No professional waveform points returned, falling back to basic rendering")
                self._draw_basic_waveform(painter, rect)
                return

            # Get professional gradient
            gradient = self.professional_renderer.get_gradient_for_scheme(rect.width(), rect.height())

            # Create path for waveform
            path = QPainterPath()
            center_y = rect.top() + (rect.height() / 2)

            if len(points) > 0:
                # Start at the center
                first_point = points[0]
                path.moveTo(rect.left() + first_point[0], center_y)

                # Add top edge with color information
                for x, y_top, y_bottom, color in points:
                    path.lineTo(rect.left() + int(float(x)), rect.top() + int(float(y_top)))

                # Add right edge to center
                if points:
                    last_point = points[-1]
                    path.lineTo(rect.left() + int(float(last_point[0])), center_y)

                # Add bottom edge (in reverse)
                for x, y_top, y_bottom, color in reversed(points):
                    path.lineTo(rect.left() + int(float(x)), rect.top() + int(float(y_bottom)))

                # Close path
                path.lineTo(rect.left() + int(float(points[0][0])), center_y)

                # Draw filled waveform with professional gradient
                painter.setOpacity(0.85)
                painter.fillPath(path, QBrush(gradient))

                # Draw individual colored segments if colors are provided
                if any(point[3] is not None for point in points):
                    self._draw_colored_waveform_segments(painter, rect, points)

                # Draw outline
                painter.setOpacity(1.0)
                # Get outline color with fallback
                color_scheme = self.current_color_scheme if self.current_color_scheme in self.professional_renderer._color_palettes else ColorScheme.PROFESSIONAL_DARK
                outline_color = self.professional_renderer._color_palettes[color_scheme]['primary']
                outline_pen = QPen(outline_color.lighter(120), 1.0)
                painter.setPen(outline_pen)
                painter.drawPath(path)

        except Exception as e:
            self.logger.error(f"Error in professional waveform rendering: {e}", exc_info=True)
            self.logger.info("Falling back to basic waveform rendering")
            self._draw_basic_waveform(painter, rect)

    def _draw_colored_waveform_segments(self, painter: QPainter, rect: QRect,
                                        points: List[Tuple[float, float, float, Optional[QColor]]]) -> None:
        """Draw individual colored segments for spectral/frequency-based rendering"""
        painter.setOpacity(0.7)

        for i, (x, y_top, y_bottom, color) in enumerate(points):
            if color is not None:
                # Draw vertical line segment with specific color
                pen = QPen(color, 1.0)
                painter.setPen(pen)

                # Convert all coordinates to integers to avoid Qt drawing errors
                x_pos = int(rect.left() + float(x))
                y_top_pos = int(rect.top() + float(y_top))
                y_bottom_pos = int(rect.top() + float(y_bottom))

                # Ensure coordinates are within valid ranges
                x_pos = max(0, min(x_pos, 32767))  # Qt coordinate limits
                y_top_pos = max(0, min(y_top_pos, 32767))
                y_bottom_pos = max(0, min(y_bottom_pos, 32767))

                painter.drawLine(x_pos, y_top_pos, x_pos, y_bottom_pos)

    def _draw_basic_waveform(self, painter: QPainter, rect: QRect) -> None:
        """Draw basic waveform (fallback method)"""
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
        Draw amplitude segment grid lines and labels (5 segments)

        Args:
            painter: Qt painter
            rect: Content rectangle
        """
        # Use 5 amplitude segments instead of dB levels (reversed so Very High is at top)
        segment_labels = ["Very High", "High", "Medium", "Low", "Very Low"]

        # Calculate segment boundaries (5 equal segments)
        segment_height = rect.height() / 5
        center_y = rect.top() + (rect.height() / 2)

        # Draw horizontal lines for each segment
        for i, label in enumerate(segment_labels):
            # Calculate y position for this segment boundary
            y_pos = rect.top() + (i * segment_height)

            if rect.top() <= y_pos <= rect.bottom():
                # Draw grid line
                painter.setPen(QPen(self.grid_color.lighter(110), 1, Qt.DotLine))
                painter.drawLine(rect.left(), y_pos, rect.right(), y_pos)

                # Draw label on the left side
                painter.setPen(self.text_color)
                metrics = QFontMetrics(painter.font())
                text_rect = metrics.boundingRect(label)
                text_rect.moveRight(rect.left() - 5)
                text_rect.moveCenter(QPoint(text_rect.center().x(), int(y_pos)))
                painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, label)

        # Draw bottom boundary line
        painter.setPen(QPen(self.grid_color.lighter(110), 1, Qt.DotLine))
        painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())

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

    def _get_peaks_from_any_source(self):
        """Get peaks from analyzer or global storage with comprehensive fallback."""
        if not self.analyzer:
            return []

        # First try: Get peaks directly from analyzer
        if hasattr(self.analyzer, 'peaks') and self.analyzer.peaks:
            return self.analyzer.peaks

        # Second try: Check if analyzer has get_peak_data method
        if hasattr(self.analyzer, 'get_peak_data'):
            try:
                peaks = self.analyzer.get_peak_data()
                if peaks:
                    return peaks
            except Exception as e:
                self.logger.warning(f"Failed to get peaks from analyzer: {e}")

        # Third try: Check global storage
        try:
            import __main__
            if hasattr(__main__, '_global_peaks_storage'):
                possible_keys = []
                if hasattr(self.analyzer, 'file_path') and self.analyzer.file_path:
                    possible_keys.append(str(self.analyzer.file_path))
                if hasattr(self.analyzer, '_original_file_path'):
                    possible_keys.append(str(self.analyzer._original_file_path))
                possible_keys.append("unknown")

                for key in possible_keys:
                    if key in __main__._global_peaks_storage:
                        stored_peaks = __main__._global_peaks_storage[key]['peaks']
                        if stored_peaks:
                            self.logger.info(
                                f"Retrieved {len(stored_peaks)} peaks from global storage with key '{key}'")
                            # Cache peaks in analyzer for future use
                            if not hasattr(self.analyzer, 'peaks') or not self.analyzer.peaks:
                                self.analyzer.peaks = stored_peaks
                                self.analyzer.is_analyzed = True
                            return stored_peaks
        except Exception as e:
            self.logger.warning(f"Failed to retrieve peaks from global storage: {e}")

        return []

    @profile_method("_draw_peak_markers")
    def _draw_peak_markers(self, painter: QPainter, rect: QRect) -> None:
        """OPTIMIZED: Draw peak markers with lazy loading and performance improvements"""
        # OPTIMIZATION: Update visible peaks based on current view
        self._update_visible_peaks(rect)

        # Always render manual peaks regardless of visible_peaks
        has_auto_peaks = bool(self.visible_peaks)
        has_manual_peaks = bool(self.manual_peaks)

        if not has_auto_peaks and not has_manual_peaks:
            return

        # Use appropriate rendering based on zoom level
        if self.zoom_factor >= 5.0:
            # Detailed markers when zoomed in
            self._draw_detailed_peak_markers_optimized(painter, rect)
        else:
            # Simplified dots when zoomed out
            self._draw_simplified_peak_markers_optimized(painter, rect)

    def _get_enhanced_peak_markers_for_rendering(self, width: int, height: int, offset: float, zoom_factor: float):
        """Get peak markers for rendering with enhanced global storage support"""
        # CRITICAL FIX: Use visible_peaks instead of all peaks to prevent visual clutter
        if not self.visible_peaks:
            return []
        peaks = self.visible_peaks

        markers = []
        if not hasattr(self, 'analyzer') or not self.analyzer or not hasattr(self.analyzer,
                                                                             'waveform_data') or self.analyzer.waveform_data is None:
            return []

        waveform_data = self.analyzer.waveform_data[0]  # First channel
        samples_per_pixel = len(waveform_data) / (width * zoom_factor)

        for i, peak in enumerate(peaks):
            # Calculate x position
            sample_pos = peak.position
            x = int((sample_pos / samples_per_pixel) - offset)

            # Only include peaks that are visible in current view
            if 0 <= x <= width:
                # Calculate y positions for waveform
                y1 = height // 2 - int(peak.amplitude * height * 0.4)
                y2 = height // 2 + int(peak.amplitude * height * 0.4)

                # Create marker tuple: (x, y1, y2, amplitude, peak_info)
                markers.append((x, y1, y2, peak.amplitude, peak))

        return markers

        if not markers:
            return

        painter.save()
        painter.setClipRect(rect)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        for i, (x, y1, _, amplitude, peak_info) in enumerate(markers):
            x_pos = rect.left() + x
            is_selected = i in self.selected_peaks
            is_hovered = hasattr(self, '_hovered_peak') and self._hovered_peak == i

            # Professional color scheme
            if is_selected:
                color = QColor(255, 215, 0)  # Gold for selected
                glow_color = QColor(255, 215, 0, 120)
                pen_width = 3
            elif is_hovered:
                color = QColor(255, 165, 0)  # Orange for hovered
                glow_color = QColor(255, 165, 0, 100)
                pen_width = 2
            else:
                # Enhanced amplitude-based coloring
                hue = max(0, min(60, 60 - amplitude * 60))
                hue_int = int(hue)
                color = QColor.fromHsv(hue_int, 200, 255)
                glow_color = QColor.fromHsv(hue_int, 200, 255, 60)
                pen_width = 1

            # Draw enhanced glow effect
            if is_selected or is_hovered:
                glow_pen = QPen(glow_color, pen_width + 6)
                glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(glow_pen)
                painter.drawLine(x_pos, y1, x_pos, rect.top())

            # Draw main marker line with rounded caps
            main_pen = QPen(color, pen_width)
            main_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(main_pen)
            painter.drawLine(x_pos, y1, x_pos, rect.top())

            # Draw professional marker indicator
            if self.zoom_factor > 10:
                # Diamond-shaped indicator for better visibility
                diamond_size = 8 if is_selected else 5
                center_y = rect.top() + diamond_size + 5

                diamond_points = [
                    QPoint(x_pos, center_y - diamond_size),
                    QPoint(x_pos + diamond_size, center_y),
                    QPoint(x_pos, center_y + diamond_size),
                    QPoint(x_pos - diamond_size, center_y)
                ]

                painter.setBrush(QBrush(color))
                painter.setPen(QPen(color.darker(150), 1))
                painter.drawPolygon(diamond_points)
            else:
                # Simple dot for lower zoom levels
                dot_size = 6 if is_selected else 4
                painter.setBrush(QBrush(color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPoint(x_pos, rect.top() + 8), dot_size, dot_size)

            # Draw peak information labels
            if self.zoom_factor > 20 and (is_selected or is_hovered):
                painter.setPen(QPen(QColor(255, 255, 255), 1))
                font = painter.font()
                font.setPointSize(7)
                painter.setFont(font)

                # Peak number
                painter.drawText(x_pos + 10, rect.top() + 15, f"#{i + 1}")

                # Amplitude info
                if 'amplitude' in peak_info:
                    amp_text = f"A:{peak_info['amplitude']:.3f}"
                    painter.drawText(x_pos + 10, rect.top() + 28, amp_text)

        painter.restore()

    def _draw_simplified_peak_markers(self, painter: QPainter, rect: QRect) -> None:
        """Draw simplified peak markers at lower zoom levels."""
        if not self.analyzer or not hasattr(self.analyzer, 'peaks'):
            return

        # Get all peaks as normalized positions
        peak_markers = self.analyzer.get_peak_markers_for_visualization()

        if not peak_markers:
            return

        painter.save()
        painter.setClipRect(rect)

        # Draw small vertical lines at peak positions
        for position, amplitude in peak_markers:
            # Check if peak is in visible range
            if self.offset <= position <= self.offset + (1.0 / self.zoom_factor):
                # Convert to pixel position
                x_pos = self._position_to_pixel(position)

                # Use color based on amplitude
                hue = max(0, min(60, 60 - amplitude * 60))  # 60 (yellow) to 0 (red)
                # Convert hue to integer to avoid TypeError and OverflowError
                hue_int = int(hue)
                color = QColor.fromHsv(hue_int, 255, 230)

                # Draw a small vertical line
                painter.setPen(QPen(color, 1))
                painter.drawLine(x_pos, rect.top(), x_pos, rect.top() + 5)

                # Draw a small dot
                painter.setBrush(color)
                painter.drawEllipse(QPoint(int(x_pos), rect.top() + 3), 2, 2)

        painter.restore()

    def _find_peak_index(self, x: int, y: int, markers: List[Tuple]) -> Optional[int]:
        """Find index of clicked peak marker with improved detection for enhanced markers."""
        content_rect = self._get_content_rect()

        # Different detection logic based on zoom level
        if self.zoom_factor < 5.0:
            # For simplified markers at lower zoom levels
            if not self.analyzer or not hasattr(self.analyzer, 'peaks'):
                return None

            peak_markers = self.analyzer.get_peak_markers_for_visualization()
            if not peak_markers:
                return None

            # Check if click is near the top of the content rect where simplified markers are drawn
            if y > content_rect.top() + 10:
                return None

            # Find the closest peak to the click position
            closest_peak = None
            min_distance = float('inf')

            for i, (position, _) in enumerate(peak_markers):
                # Check if peak is in visible range
                if self.offset <= position <= self.offset + (1.0 / self.zoom_factor):
                    # Convert to pixel position
                    peak_x = self._position_to_pixel(position)
                    distance = abs(x - peak_x)

                    # Use a larger click tolerance at lower zoom levels
                    if distance < min_distance and distance <= 10:
                        min_distance = distance
                        closest_peak = i

            return closest_peak
        else:
            # For detailed markers at higher zoom levels
            for i, marker in enumerate(markers):
                mx = marker['x'] + content_rect.left()

                # Check for clicks on the marker dot at the top
                marker_top_y = content_rect.top() + (10 if i in self.selected_peaks else 7)
                if abs(x - mx) <= 8 and abs(y - marker_top_y) <= 8:
                    return i

                # Check for clicks on the vertical line (extend to bottom of content area)
                if abs(x - mx) <= 5 and content_rect.top() <= y <= content_rect.bottom():
                    return i

                # Check for clicks on the amplitude indicator (for selected peaks)
                if i in self.selected_peaks:
                    indicator_width = 3
                    indicator_height = 20  # Minimum height
                    if abs(x - mx) <= indicator_width and content_rect.top() <= y <= content_rect.top() + indicator_height:
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

    @Slot()
    def _start_background_render(self):
        """Start background rendering for expensive operations"""
        if not self.analyzer or not hasattr(self.analyzer, 'waveform_data') or self.analyzer.waveform_data is None:
            return

        # Stop any existing background rendering
        if self.background_renderer and self.background_renderer.isRunning():
            self.background_renderer.stop()
            self.background_renderer.wait(100)  # Wait up to 100ms

        # Only use background rendering for complex modes
        complex_modes = [
            WaveformRenderMode.SPECTRAL_COLOR,
            WaveformRenderMode.FREQUENCY_BANDS,
            WaveformRenderMode.HARMONIC_PERCUSSIVE
        ]

        if self.current_render_mode in complex_modes:
            # Start background rendering
            self.background_renderer = BackgroundRenderer(
                self.professional_renderer,
                self.analyzer.waveform_data,
                self.analyzer.sample_rate,
                self.width(),
                self.height(),
                self.offset,
                self.zoom_factor
            )
            self.background_renderer.rendering_complete.connect(self._on_background_render_complete)
            self.background_renderer.start()
        else:
            # For simple modes, render immediately
            self.update()

    def _on_background_render_complete(self, result):
        """Handle completion of background rendering"""
        self.cached_render_result = result
        self.update()  # Trigger a repaint with the new data

    def _safe_update(self) -> None:
        """Thread-safe method to update the widget after peak detection completes"""
        self.logger.info("Received peak_detection_complete signal, updating waveform view")
        # Use QMetaObject to safely update from worker thread if needed
        from PySide6.QtCore import QMetaObject, Qt, QTimer

        # Use a single-shot timer to ensure we're on the main thread
        QTimer.singleShot(0, self._perform_safe_update)
        self.logger.info("Waveform view update queued successfully")

    def _perform_safe_update(self) -> None:
        """Perform the actual update on the main thread"""
        try:
            self.update()
            self.logger.debug("Waveform view updated successfully on main thread")
        except Exception as e:
            self.logger.error(f"Error updating waveform view: {e}")

    @profile_method("set_analyzer")
    def set_analyzer(self, analyzer) -> None:
        """Set the waveform analyzer instance with optimizations"""
        self.logger.info("Setting analyzer in OptimizedWaveformView")
        print(f"🎵 Setting analyzer with optimization features")

        # Reset warning flags when setting a new analyzer
        self._logged_warnings = {
            'no_analyzer': False,
            'not_analyzed': False,
            'no_waveform_data': False
        }

        # Initialize signal connection tracking if not already present
        if not hasattr(self, '_signal_connected'):
            self._signal_connected = False

        # Store the analyzer
        self.analyzer = analyzer

        # OPTIMIZATION: Clear caches when setting new analyzer
        self.peak_cache.clear()
        self.visible_peaks.clear()
        self.waveform_cache = None

        if self.analyzer:
            # Check if librosa is available in the analyzer
            librosa_available = getattr(self.analyzer, 'LIBROSA_AVAILABLE', False)
            if not librosa_available:
                self.logger.warning("Analyzer has limited functionality - librosa not available")

            # Connect to peak detection complete signal if it exists
            if hasattr(self.analyzer, 'peak_detection_complete'):
                # Check if we have a previous analyzer with the same signal
                if hasattr(self, '_previous_analyzer') and self._previous_analyzer is not None:
                    try:
                        # Only try to disconnect if it's a different analyzer and we think the signal is connected
                        if self._previous_analyzer is not self.analyzer and self._signal_connected:
                            self._previous_analyzer.peak_detection_complete.disconnect(self.update)
                            self.logger.info(
                                "Disconnected existing peak_detection_complete signal from previous analyzer")
                            self._signal_connected = False
                    except (RuntimeError, TypeError, AttributeError) as e:
                        # Signal was not connected or other error, which is fine
                        self.logger.debug(f"No need to disconnect signal: {str(e)}")
                        # Reset our tracking flag since we're not sure of the connection state
                        self._signal_connected = False

                # Store current analyzer for future reference
                self._previous_analyzer = self.analyzer

                # Use a simpler approach for connecting the signal
                try:
                    # First try to disconnect if we think it's connected
                    if self._signal_connected:
                        try:
                            self.analyzer.peak_detection_complete.disconnect(self.update)
                            self.logger.debug("Disconnected from peak_detection_complete signal")
                            self._signal_connected = False
                        except Exception as e:
                            # If disconnection fails, log it but don't raise an error
                            self.logger.debug(f"Could not disconnect signal: {str(e)}")
                            # Reset our tracking flag since we're not sure of the connection state
                            self._signal_connected = False

                    # Now connect the signal
                    # Use a thread-safe approach to handle the signal
                    self.analyzer.peak_detection_complete.connect(self._safe_update)
                    self._signal_connected = True
                    self.logger.info("Connected to peak_detection_complete signal")
                except Exception as e:
                    self.logger.warning(f"Error handling signal connection: {str(e)}")
                    # Reset our tracking flag since we're not sure of the connection state
                    self._signal_connected = False

            # Check if analyzer is analyzed or has peaks in global storage
            has_peaks = False
            if self.analyzer.is_analyzed:
                self.logger.info("Analyzer is analyzed")
                has_peaks = True
            else:
                # Check global storage for peaks
                import __main__
                if hasattr(__main__, '_global_peaks_storage'):
                    possible_keys = []
                    if hasattr(self.analyzer, 'file_path') and self.analyzer.file_path:
                        possible_keys.append(str(self.analyzer.file_path))
                    if hasattr(self.analyzer, '_original_file_path'):
                        possible_keys.append(str(self.analyzer._original_file_path))
                    possible_keys.append("unknown")

                    for key in possible_keys:
                        if key in __main__._global_peaks_storage:
                            has_peaks = True
                            self.logger.info(f"Found peaks in global storage with key '{key}'")
                            # Transfer peaks to analyzer for rendering
                            if not hasattr(self.analyzer, 'peaks') or not self.analyzer.peaks:
                                self.analyzer.peaks = __main__._global_peaks_storage[key]['peaks']
                                self.analyzer.is_analyzed = True
                            break

            if has_peaks:
                if hasattr(self.analyzer, 'waveform_data') and self.analyzer.waveform_data is not None:
                    self.logger.info(f"Waveform data present, length: {len(self.analyzer.waveform_data)}")
                    # Reset view state
                    self.zoom_factor = 1.0
                    self.offset = 0.0
                    self.current_position = 0.0
                else:
                    self.logger.warning("No waveform data available")
            else:
                self.logger.warning("Analyzer not analyzed and no peaks in global storage")
        else:
            self.logger.warning("No analyzer provided")

        # CRITICAL FIX: Ensure widget is enabled for interaction
        if self.analyzer:
            self.setEnabled(True)
            self.setFocusPolicy(Qt.StrongFocus)
            self.logger.info("Waveform widget enabled for interaction")

        # Force a redraw
        self.update()

    def set_position(self, position: float) -> None:
        """
        Set current playback position

        Args:
            position: Normalized position (0.0-1.0)
        """
        self._set_position(position)

        # FIX: Use full update to ensure clean position line rendering
        # Partial updates can leave artifacts during rapid position changes
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

        # Use a smaller margin (0.001 ms) when in playback mode
        # Convert from milliseconds to normalized units
        if hasattr(self, 'analyzer') and self.analyzer and self.analyzer.sample_rate:
            # 0.001 ms = 0.000001 seconds
            # normalized_value = seconds / total_duration
            if hasattr(self.analyzer, 'duration') and self.analyzer.duration:
                margin = 0.000001 / self.analyzer.duration
            else:
                # Fallback to the original calculation if duration is not available
                margin = 0.1 / self.zoom_factor
        else:
            # Use original margin when not in playback mode or analyzer not available
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

    def _scroll_left(self) -> None:
        """Scroll the waveform view to the left"""
        if not self.analyzer or not self.analyzer.has_waveform_data():
            return

        # Calculate scroll amount based on zoom level
        scroll_amount = 0.1 / self.zoom_factor
        new_offset = self.offset - scroll_amount
        self._set_offset(new_offset)

    def _scroll_right(self) -> None:
        """Scroll the waveform view to the right"""
        if not self.analyzer or not self.analyzer.has_waveform_data():
            return

        # Calculate scroll amount based on zoom level
        scroll_amount = 0.1 / self.zoom_factor
        new_offset = self.offset + scroll_amount
        self._set_offset(new_offset)

    def _scroll_to_start(self) -> None:
        """Scroll to the beginning of the waveform"""
        self._set_offset(0.0)

    def _scroll_to_end(self) -> None:
        """Scroll to the end of the waveform"""
        if not self.analyzer or not self.analyzer.has_waveform_data():
            return

        # Calculate maximum offset based on zoom
        max_offset = max(0.0, 1.0 - (1.0 / self.zoom_factor))
        self._set_offset(max_offset)

    # OPTIMIZATION METHODS

    def _update_visible_peaks(self, rect: QRect):
        """Update list of visible peaks for current view"""
        if not self.analyzer or not hasattr(self.analyzer, 'peaks'):
            self.visible_peaks = []
            return

        # Get auto-detected peaks
        auto_peaks = self._get_peaks_from_any_source()

        # Combine auto-detected peaks with manual peaks
        all_peaks = []
        if auto_peaks:
            all_peaks.extend(auto_peaks)
        if self.manual_peaks:
            all_peaks.extend(self.manual_peaks)

        if not all_peaks:
            self.visible_peaks = []
            return

        peaks = all_peaks

        # Calculate visible range
        if self.analyzer.waveform_data is None or len(
                self.analyzer.waveform_data) == 0 or not self.analyzer.sample_rate:
            self.visible_peaks = []
            return

        total_samples = len(self.analyzer.waveform_data[0])
        samples_per_pixel = total_samples / (rect.width() * self.zoom_factor)
        visible_start = int(self.offset * total_samples)
        visible_end = int(visible_start + rect.width() * samples_per_pixel)

        # Find peaks in visible range with AGGRESSIVE QUALITY FILTERING
        visible_range_peaks = []
        for peak in peaks:
            # Convert peak time to sample index for comparison
            peak_sample_index = int(peak.position * self.analyzer.sample_rate)
            if visible_start <= peak_sample_index <= visible_end:
                visible_range_peaks.append(peak)

        # CRITICAL FIX: Apply aggressive quality filtering
        if visible_range_peaks:
            # Sort by amplitude (highest first) and take only the best peaks
            visible_range_peaks.sort(key=lambda p: p.amplitude, reverse=True)

            # Show all segment-appropriate peaks (no artificial limits)
            max_peaks_to_show = len(visible_range_peaks)  # Show all peaks that reach High/Very High segments

            # Use segment-based filtering only (no additional amplitude thresholds)
            if visible_range_peaks:
                # Use all peaks in visible range - filtering is already done by the analyzer
                # Sort by position for display
                visible_range_peaks.sort(key=lambda p: p.position)
                self.visible_peaks = visible_range_peaks

            else:
                self.visible_peaks = []
        else:
            self.visible_peaks = []

    def _draw_simplified_peak_markers_optimized(self, painter: QPainter, rect: QRect):
        """Draw small dots for peak markers when zoomed out"""
        if not self.visible_peaks and not self.manual_peaks:
            return

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Professional colors for simplified view
        main_color = QColor(0, 255, 255, 200)  # Semi-transparent cyan
        selected_color = QColor(255, 215, 0, 220)  # Gold for selected
        manual_color = QColor(255, 100, 255, 200)  # Magenta for manual peaks

        # Show analyzer-detected peaks only if enabled
        if self.show_analyzer_peaks and self.visible_peaks:
            for i, peak in enumerate(self.visible_peaks):
                # Skip hidden detected peaks
                if i in self.hidden_detected_peaks:
                    continue
                if self.analyzer.waveform_data is None or len(self.analyzer.waveform_data) == 0:
                    continue

                total_samples = len(self.analyzer.waveform_data[0])
                samples_per_pixel = total_samples / (rect.width() * self.zoom_factor)
                # Fix position calculation to prevent clustering
                visible_start_sample = self.offset * total_samples
                # Convert peak time to sample index (position is in seconds)
                peak_sample_index = int(peak.position * self.analyzer.sample_rate)
                x = int((peak_sample_index - visible_start_sample) / samples_per_pixel)

                if 0 <= x <= rect.width():
                    x_pos = rect.left() + x

                    # Position dots at top of window
                    dot_y = rect.top() + 8
                    dot_size = 3

                    # Choose color based on peak type and selection
                    if hasattr(peak, 'is_manual') and peak.is_manual:
                        color = manual_color
                    elif i in self.selected_peaks:
                        color = selected_color
                    else:
                        color = main_color

                    # Draw small dot
                    painter.setBrush(QBrush(color))
                    painter.setPen(QPen(color.darker(150), 1))
                    painter.drawEllipse(x_pos - dot_size // 2, dot_y - dot_size // 2, dot_size, dot_size)

        # Also draw manual peaks separately to ensure they're always visible
        for i, peak in enumerate(self.manual_peaks):
            if self.analyzer.waveform_data is None or len(self.analyzer.waveform_data) == 0:
                continue

            total_samples = len(self.analyzer.waveform_data[0])
            samples_per_pixel = total_samples / (rect.width() * self.zoom_factor)
            visible_start_sample = self.offset * total_samples
            # Peak position is already in samples, not time
            peak_sample_index = int(peak.position)
            x = int((peak_sample_index - visible_start_sample) / samples_per_pixel)

            if 0 <= x <= rect.width():
                x_pos = rect.left() + x
                dot_y = rect.top() + 8
                dot_size = 4  # Slightly larger for manual peaks

                # Draw manual peak dot
                painter.setBrush(QBrush(manual_color))
                painter.setPen(QPen(manual_color.darker(150), 2))
                painter.drawEllipse(x_pos - dot_size // 2, dot_y - dot_size // 2, dot_size, dot_size)

        painter.restore()

    def set_manual_peak_mode(self, enabled: bool):
        """Enable or disable manual peak placement mode"""
        self.manual_peak_mode = enabled
        self.logger.info(f"Manual peak mode set to: {enabled}")

    def set_double_shot_mode(self, enabled: bool):
        """Enable or disable double shot mode for marking peaks as DOUBLE SHOT type"""
        self.double_shot_mode = enabled
        self.logger.info(f"Double shot mode set to: {enabled}")

    def _handle_manual_peak_placement(self, event, content_rect):
        """Handle manual peak placement when in manual mode"""
        if not self.analyzer or self.analyzer.waveform_data is None:
            return

        click_x = event.position().x()
        click_y = event.position().y()

        # Convert click position to sample position
        total_samples = len(self.analyzer.waveform_data[0])
        samples_per_pixel = total_samples / (content_rect.width() * self.zoom_factor)
        sample_position = int((click_x - content_rect.left()) * samples_per_pixel + (self.offset * total_samples))

        # Ensure position is within bounds
        if 0 <= sample_position < total_samples:
            # Get amplitude at this position
            amplitude = abs(self.analyzer.waveform_data[0][sample_position])

            # Create manual peak object
            from collections import namedtuple
            Peak = namedtuple('Peak', ['position', 'time', 'amplitude', 'segment', 'is_manual'])
            manual_peak = Peak(
                position=sample_position,
                time=sample_position / self.analyzer.sample_rate,
                amplitude=amplitude,
                segment=self._calculate_segment_for_amplitude(amplitude),
                is_manual=True
            )

            self.manual_peaks.append(manual_peak)
            self.logger.info(f"Added manual peak at position {sample_position}, amplitude {amplitude:.4f}")
            self.peak_selection_changed.emit()  # Emit signal to update peak count

            # FIX: Use full update to prevent grey artifacts around peaks
            self.update()

    def _is_manual_peak_at_position(self, x, y, content_rect):
        """Check if there's a manual peak at the given position

        Returns:
            int: The index of the manual peak if found, False otherwise
        """
        if not self.manual_peaks:
            return False

        tolerance = 10  # pixels

        for i, peak in enumerate(self.manual_peaks):
            total_samples = len(self.analyzer.waveform_data[0])
            samples_per_pixel = total_samples / (content_rect.width() * self.zoom_factor)
            # Fix position calculation
            visible_start_sample = self.offset * total_samples
            # Peak position is already in samples, not time
            peak_sample_index = int(peak.position)
            peak_x = int((peak_sample_index - visible_start_sample) / samples_per_pixel)
            peak_x_pos = content_rect.left() + peak_x

            if abs(x - peak_x_pos) <= tolerance:
                return i  # Return the index of the manual peak
        return False

    def _delete_manual_peak_at_index(self, index):
        """Delete manual peak at the given index"""
        if 0 <= index < len(self.manual_peaks):
            peak = self.manual_peaks[index]
            del self.manual_peaks[index]
            self.logger.info(f"Deleted manual peak at position {peak.position}")
            self.peak_selection_changed.emit()  # Emit signal to update peak count

            # FIX: Use full update to prevent grey artifacts
            self.update()

    def _delete_manual_peak_at_position(self, x, y, content_rect):
        """Delete manual peak at the given position"""
        manual_peak_index = self._is_manual_peak_at_position(x, y, content_rect)
        if manual_peak_index is not False:
            self._delete_manual_peak_at_index(manual_peak_index)

    def _is_detected_peak_at_position(self, x, y, content_rect):
        """Check if there's a detected peak at the given position"""
        if not self.visible_peaks:
            return False

        tolerance = 10  # pixels

        for i, peak in enumerate(self.visible_peaks):
            if i in self.hidden_detected_peaks:
                continue  # Skip hidden peaks

            total_samples = len(self.analyzer.waveform_data[0])
            samples_per_pixel = total_samples / (content_rect.width() * self.zoom_factor)
            visible_start_sample = self.offset * total_samples
            # Convert peak time to sample index
            peak_sample_index = int(peak.position * self.analyzer.sample_rate)
            peak_x = int((peak_sample_index - visible_start_sample) / samples_per_pixel)
            peak_x_pos = content_rect.left() + peak_x

            if abs(x - peak_x_pos) <= tolerance:
                return i  # Return the peak index

        return False

    def _toggle_detected_peak_visibility(self, x, y, content_rect):
        """Toggle visibility of detected peak at the given position"""
        peak_index = self._is_detected_peak_at_position(x, y, content_rect)

        if peak_index is not False:
            if peak_index in self.hidden_detected_peaks:
                # Show the peak
                self.hidden_detected_peaks.remove(peak_index)
                self.logger.info(f"Showed detected peak at index {peak_index}")
            else:
                # Hide the peak
                self.hidden_detected_peaks.add(peak_index)
                self.logger.info(f"Hidden detected peak at index {peak_index}")

            self.peak_selection_changed.emit()  # Emit signal to update peak count
            self.update()  # Refresh the display

    def get_total_peak_count(self) -> int:
        """Get total number of peaks across entire waveform (analyzer + manual)"""
        # Count total detected peaks (excluding hidden ones)
        total_detected_peaks = 0
        if self.show_analyzer_peaks and self.analyzer and hasattr(self.analyzer, 'get_peak_data'):
            try:
                all_peaks = self.analyzer.get_peak_data()
                total_detected_peaks = len(all_peaks) if all_peaks else 0
                total_detected_peaks = max(0, total_detected_peaks - len(self.hidden_detected_peaks))
            except:
                total_detected_peaks = 0

        manual_peaks = len(self.manual_peaks)
        return total_detected_peaks + manual_peaks

    def get_detected_peak_count(self) -> int:
        """Get total number of detected peaks across entire waveform (minus hidden ones)"""
        if not self.show_analyzer_peaks:
            return 0

        # Get total peaks from analyzer, not just visible ones
        total_peaks = 0
        if self.analyzer and hasattr(self.analyzer, 'get_peak_data'):
            try:
                all_peaks = self.analyzer.get_peak_data()
                total_peaks = len(all_peaks) if all_peaks else 0
            except:
                total_peaks = 0

        # Subtract hidden peaks (but hidden peaks are indexed by visible peaks, so we need to be careful)
        # For now, just return total peaks minus hidden count
        return max(0, total_peaks - len(self.hidden_detected_peaks))

    def get_manual_peak_count(self) -> int:
        """Get number of manual peaks"""
        return len(self.manual_peaks)

    def _calculate_segment_for_amplitude(self, amplitude):
        """Calculate which segment an amplitude belongs to"""
        if not self.analyzer or self.analyzer.waveform_data is None:
            return 0

        # Use the same segmentation logic as the analyzer
        waveform_data = self.analyzer.waveform_data[0]
        abs_data = np.abs(waveform_data)
        min_amp = np.min(abs_data)
        max_amp = np.max(abs_data)

        if max_amp <= min_amp:
            return 0

        boundaries = [
            min_amp,
            min_amp + (max_amp - min_amp) * 0.10,
            min_amp + (max_amp - min_amp) * 0.30,
            min_amp + (max_amp - min_amp) * 0.50,
            min_amp + (max_amp - min_amp) * 0.70,
            max_amp
        ]

        for i in range(len(boundaries) - 1):
            if boundaries[i] <= amplitude < boundaries[i + 1]:
                return i
        return 4  # Very High segment

        painter.restore()

    def _draw_detailed_peak_markers_optimized(self, painter: QPainter, rect: QRect):
        """Draw professional detailed peak markers with precise alignment"""
        if not self.visible_peaks and not self.manual_peaks:
            return

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)  # Enable for professional look

        # Draw auto-detected peaks only if enabled
        if self.show_analyzer_peaks and self.visible_peaks:
            for i, peak in enumerate(self.visible_peaks):
                # Skip hidden detected peaks
                if i in self.hidden_detected_peaks:
                    continue

                if self.analyzer.waveform_data is None or len(self.analyzer.waveform_data) == 0:
                    continue

                total_samples = len(self.analyzer.waveform_data[0])
                samples_per_pixel = total_samples / (rect.width() * self.zoom_factor)
                # Fix position calculation to prevent clustering
                visible_start_sample = self.offset * total_samples
                # Convert peak time to sample index (position is in seconds)
                peak_sample_index = int(peak.position * self.analyzer.sample_rate)
                x = int((peak_sample_index - visible_start_sample) / samples_per_pixel)

                if 0 <= x <= rect.width():
                    x_pos = rect.left() + x

                    # Check if peak is selected or marked as double shot
                    is_selected = i in self.selected_peaks
                    is_double_shot = peak.time in self.double_shot_peaks

                    # PROFESSIONAL PEAK MARKER DESIGN - ENHANCED
                    if is_double_shot:
                        # Double shot peak: Red with glow effect
                        main_color = QColor(255, 0, 0, 255)  # Solid red
                        glow_color = QColor(255, 0, 0, 120)  # Red glow
                        line_width = 4
                    elif is_selected:
                        # Selected peak: Gold with glow effect
                        main_color = QColor(255, 215, 0, 255)  # Solid gold
                        glow_color = QColor(255, 215, 0, 120)  # More visible glow
                        line_width = 4
                    else:
                        # Normal peak: Bright cyan with professional look
                        main_color = QColor(0, 255, 255, 255)  # Bright cyan
                        glow_color = QColor(0, 255, 255, 100)  # More visible glow
                        line_width = 3

                    # Draw glow effect (wider, transparent line behind)
                    painter.setPen(QPen(glow_color, line_width + 2))
                    painter.drawLine(x_pos, rect.top(), x_pos, rect.bottom())

                    # Draw main peak line
                    painter.setPen(QPen(main_color, line_width))
                    painter.drawLine(x_pos, rect.top(), x_pos, rect.bottom())

                    # PRECISION PEAK INDICATOR: Show exact peak position
                    if self.zoom_factor > 5.0:
                        # Calculate precise waveform position for this peak
                        waveform_data = self.analyzer.waveform_data[0]
                        # Convert peak time to sample index
                        sample_index = int(peak.position * self.analyzer.sample_rate)
                        if sample_index < len(waveform_data):
                            # Get the actual amplitude at this position
                            actual_amplitude = abs(waveform_data[sample_index])

                            # Calculate Y position based on actual waveform amplitude
                            center_y = rect.center().y()
                            amplitude_scale = 0.8  # Scale factor for display
                            y_offset = int(actual_amplitude * rect.height() * amplitude_scale / 2)
                            peak_y_top = center_y - y_offset

                            # Position peak marker ABOVE the waveform peak
                            marker_y = peak_y_top - 15  # Position 15 pixels above the peak

                            # Draw diamond-shaped precision marker above the peak
                            diamond_size = 4 if self.zoom_factor > 15.0 else 3
                            diamond_points = [
                                QPoint(x_pos, marker_y - diamond_size),  # Top
                                QPoint(x_pos + diamond_size, marker_y),  # Right
                                QPoint(x_pos, marker_y + diamond_size),  # Bottom
                                QPoint(x_pos - diamond_size, marker_y)  # Left
                            ]

                            painter.setBrush(QBrush(main_color))
                            painter.setPen(QPen(QColor(255, 255, 255), 1))  # White outline
                            painter.drawPolygon(diamond_points)

                            # Draw vertical line from marker to peak (not through it)
                            painter.setPen(QPen(main_color, 2))
                            painter.drawLine(x_pos, marker_y + diamond_size, x_pos, peak_y_top)

                    # PEAK INFO DISPLAY: Show amplitude and time when highly zoomed
                    if self.zoom_factor > 20.0:
                        painter.setPen(QPen(QColor(255, 255, 255), 1))
                        painter.setFont(QFont("Arial", 8))

                        # Show peak info
                        time_str = f"{peak.position:.2f}s"
                        amp_str = f"{peak.amplitude:.3f}"

                        info_text = f"{time_str}\n{amp_str}"
                        text_rect = QRect(x_pos + 5, rect.top() + 5, 60, 30)

                        # Draw background for text
                        painter.fillRect(text_rect, QColor(0, 0, 0, 180))
                        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop, info_text)

        # Draw manual peaks with different color
        for i, peak in enumerate(self.manual_peaks):
            if self.analyzer.waveform_data is None or len(self.analyzer.waveform_data) == 0:
                continue

            total_samples = len(self.analyzer.waveform_data[0])
            samples_per_pixel = total_samples / (rect.width() * self.zoom_factor)
            # Fix position calculation to prevent clustering
            visible_start_sample = self.offset * total_samples
            # Peak position is already in samples, not time
            peak_sample_index = int(peak.position)
            x = int((peak_sample_index - visible_start_sample) / samples_per_pixel)

            if 0 <= x <= rect.width():
                x_pos = rect.left() + x

                # Check if this manual peak is marked as double shot
                manual_peak_id = f"m{peak.time}"
                is_double_shot = manual_peak_id in self.double_shot_peaks

                if is_double_shot:
                    # Double shot manual peak: Red with glow effect
                    main_color = QColor(255, 0, 0, 255)  # Solid red
                    glow_color = QColor(255, 0, 0, 120)  # Red glow
                    line_width = 4
                else:
                    # Regular manual peak colors (magenta/purple)
                    main_color = QColor(255, 100, 255, 255)  # Bright magenta
                    glow_color = QColor(255, 100, 255, 100)  # Magenta glow
                    line_width = 3

                # Draw glow effect
                painter.setPen(QPen(glow_color, line_width + 2))
                painter.drawLine(x_pos, rect.top(), x_pos, rect.bottom())

                # Draw main peak line
                painter.setPen(QPen(main_color, line_width))
                painter.drawLine(x_pos, rect.top(), x_pos, rect.bottom())

                # Draw precision marker above the peak
                if self.zoom_factor > 5.0:
                    waveform_data = self.analyzer.waveform_data[0]
                    # Manual peak position is already in samples
                    sample_index = int(peak.position)
                    if sample_index < len(waveform_data):
                        actual_amplitude = abs(waveform_data[sample_index])
                        center_y = rect.center().y()
                        amplitude_scale = 0.8
                        y_offset = int(actual_amplitude * rect.height() * amplitude_scale / 2)
                        peak_y_top = center_y - y_offset

                        # Position marker above the peak
                        marker_y = peak_y_top - 15

                        # Draw square marker for manual peaks (different from diamond for auto peaks)
                        square_size = 4 if self.zoom_factor > 15.0 else 3
                        square_rect = QRect(x_pos - square_size, marker_y - square_size,
                                            square_size * 2, square_size * 2)

                        painter.setBrush(QBrush(main_color))
                        painter.setPen(QPen(QColor(255, 255, 255), 1))
                        painter.drawRect(square_rect)

                        # Draw line from marker to peak
                        painter.setPen(QPen(main_color, 2))
                        painter.drawLine(x_pos, marker_y + square_size, x_pos, peak_y_top)

        painter.restore()

    def _render_next_batch(self):
        """Render next batch of peaks (for lazy loading)"""
        if not self.pending_peak_batches:
            self.lazy_render_timer.stop()
            print("✅ Lazy peak rendering completed")
            return

        # Render next batch
        batch = self.pending_peak_batches.pop(0)
        batch_start = time.time()

        for peak in batch:
            self._cache_peak_marker(peak)

        batch_time = time.time() - batch_start
        self.peak_render_times.append(batch_time)

        # Update display
        self.update()

    def _cache_peak_marker(self, peak):
        """Cache peak marker for efficient rendering"""
        peak_id = f"{peak.position}_{peak.amplitude:.6f}"
        if peak_id not in self.peak_cache:
            self.peak_cache[peak_id] = {
                'position': peak.position,
                'amplitude': peak.amplitude,
                'cached_time': time.time()
            }

    # Professional Rendering Control Methods
    def set_render_mode(self, mode: WaveformRenderMode):
        """Set the professional rendering mode with smart updating"""
        if self.current_render_mode != mode:
            self.current_render_mode = mode
            self.rendering_config.mode = mode
            self.professional_renderer.config = self.rendering_config
            # Clear render cache when mode changes
            if hasattr(self.professional_renderer, '_render_cache'):
                self.professional_renderer._render_cache.clear()
            self.smart_update()
        # If mode hasn't changed, skip the expensive update

    def set_color_scheme(self, scheme: ColorScheme):
        """Set the professional color scheme with smart updating"""
        if self.current_color_scheme != scheme:
            self.current_color_scheme = scheme
            self.rendering_config.color_scheme = scheme
            self.professional_renderer.config = self.rendering_config
            # Clear color cache when scheme changes
            if hasattr(self.professional_renderer, '_color_cache'):
                self.professional_renderer._color_cache.clear()
            self.smart_update()
        # If scheme hasn't changed, skip the expensive update

    def toggle_professional_rendering(self, enabled: bool = None):
        """Toggle professional rendering on/off"""
        if enabled is None:
            self.use_professional_rendering = not self.use_professional_rendering
        else:
            self.use_professional_rendering = enabled
        self.update()

    def set_smoothing_factor(self, factor: float):
        """Set waveform smoothing factor (0.0 to 1.0) with smart updating"""
        old_factor = self.rendering_config.smoothing_factor
        new_factor = max(0.0, min(1.0, factor))

        # Only update if there's a meaningful change (avoid micro-updates)
        if abs(old_factor - new_factor) > 0.001:  # 0.1% threshold
            self.rendering_config.smoothing_factor = new_factor
            self.professional_renderer.config = self.rendering_config
            print(f"🔧 SMOOTHING: Changed from {old_factor:.3f} to {new_factor:.3f}")
            self.smart_update()
        # Skip update for tiny changes that won't be visually noticeable

    def set_dynamic_range_db(self, db: float):
        """Set dynamic range in dB with smart updating"""
        old_db = self.rendering_config.dynamic_range_db
        new_db = max(20.0, min(120.0, db))

        # Only update if there's a meaningful change (avoid micro-updates)
        if abs(old_db - new_db) > 0.5:  # 0.5 dB threshold
            self.rendering_config.dynamic_range_db = new_db
            self.professional_renderer.config = self.rendering_config
            print(f"🔧 DYNAMIC RANGE: Changed from {old_db:.1f} dB to {new_db:.1f} dB")
            self.smart_update()
        # Skip update for tiny changes that won't be visually noticeable

    def set_frequency_bands(self, bands: int):
        """Set number of frequency bands for frequency-based rendering with smart updating"""
        old_bands = self.rendering_config.frequency_bands
        new_bands = max(4, min(32, bands))

        # Only update if bands actually changed
        if old_bands != new_bands:
            self.rendering_config.frequency_bands = new_bands
            self.professional_renderer.config = self.rendering_config
            # Clear frequency-related caches
            if hasattr(self.professional_renderer, '_spectral_cache'):
                self.professional_renderer._spectral_cache.clear()
            print(f"🔧 FREQUENCY BANDS: Changed from {old_bands} to {new_bands}")
            self.smart_update()
        # Skip update if bands haven't changed

    def get_available_render_modes(self) -> List[WaveformRenderMode]:
        """Get list of available rendering modes"""
        return list(WaveformRenderMode)

    def get_available_color_schemes(self) -> List[ColorScheme]:
        """Get list of available color schemes"""
        return list(ColorScheme)

    def get_current_render_mode(self) -> WaveformRenderMode:
        """Get current rendering mode"""
        return self.current_render_mode

    def get_current_color_scheme(self) -> ColorScheme:
        """Get current color scheme"""
        return self.current_color_scheme
