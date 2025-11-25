"""
Professional Waveform Controls Panel
===================================

Advanced control panel for professional waveform rendering modes and settings.
Provides intuitive interface for switching between different visualization modes,
color schemes, and rendering parameters.

Author: Enhanced by NinjaTeach AI Team
Version: 3.0.0 - Professional Edition
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QComboBox,
    QSlider, QLabel, QPushButton, QCheckBox, QSpinBox, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPalette, QColor
from views.waveform.enhanced_waveform_renderer import WaveformRenderMode, ColorScheme
from typing import Optional


class WaveformControlsPanel(QWidget):
    """
    Professional control panel for waveform rendering settings
    """

    # Signals
    render_mode_changed = Signal(WaveformRenderMode)
    color_scheme_changed = Signal(ColorScheme)
    smoothing_changed = Signal(float)
    dynamic_range_changed = Signal(float)
    frequency_bands_changed = Signal(int)
    # professional_rendering_toggled signal removed - always enabled

    # Beat Detection Signals
    analyze_file_requested = Signal()
    manual_peak_mode_changed = Signal(bool)
    double_shot_mode_changed = Signal(bool)

    # Peak Category Signals
    peak_count_changed = Signal(int)  # number of peaks to display

    # State Management Signals
    save_state_requested = Signal()
    load_state_requested = Signal()

    # Zoom Control Signals
    zoom_changed = Signal(float)
    zoom_reset_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        # Performance optimization: Debouncing timers
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._emit_pending_changes)
        self._debounce_delay = 150  # 150ms debounce delay
        self._pending_changes = {}
        self.setWindowTitle("Professional Waveform Controls")
        self.setMinimumHeight(300)  # Increased for all sections to be visible
        # Removed maximum height constraint to allow full expansion

        self._setup_ui()
        self._connect_signals()
        self._connect_additional_signals()  # Connect beat detection and state management signals
        self._apply_styling()

    def _emit_pending_changes(self):
        """Emit all pending changes after debounce delay"""
        for change_type, value in self._pending_changes.items():
            if change_type == 'smoothing':
                self.smoothing_changed.emit(value)
            elif change_type == 'dynamic_range':
                self.dynamic_range_changed.emit(value)
            elif change_type == 'frequency_bands':
                self.frequency_bands_changed.emit(value)
        self._pending_changes.clear()

    def _setup_ui(self):
        """Setup the user interface - vertical layout with proper distribution"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)  # Reasonable main layout spacing
        layout.setContentsMargins(10, 10, 10, 10)  # Reasonable margins

        # Professional Rendering Controls (horizontal layout)
        # Note: Professional rendering is always enabled for optimal visualization
        main_controls_layout = QHBoxLayout()
        main_controls_layout.setSpacing(15)  # Good spacing between sections for better distribution
        main_controls_layout.setContentsMargins(8, 8, 8, 8)  # Reasonable margins

        # Rendering Mode Section
        mode_section = QVBoxLayout()
        mode_section.setSpacing(12)  # Further increased spacing for vertical distribution
        mode_label = QLabel("Rendering Mode")
        mode_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        mode_section.addWidget(mode_label)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Basic Min/Max", WaveformRenderMode.BASIC_MINMAX)
        self.mode_combo.addItem("RMS Envelope", WaveformRenderMode.RMS_ENVELOPE)
        self.mode_combo.addItem("Spectral Color", WaveformRenderMode.SPECTRAL_COLOR)
        self.mode_combo.addItem("Dual Layer", WaveformRenderMode.DUAL_LAYER)
        self.mode_combo.addItem("Frequency Bands", WaveformRenderMode.FREQUENCY_BANDS)
        self.mode_combo.addItem("Envelope Follower", WaveformRenderMode.ENVELOPE_FOLLOWER)
        self.mode_combo.setCurrentIndex(4)  # Default to Frequency Bands (optimal for drums)
        self.mode_combo.setMinimumWidth(150)
        self.mode_combo.setMinimumHeight(30)
        mode_section.addWidget(self.mode_combo)
        main_controls_layout.addLayout(mode_section)

        # Color Scheme Section
        color_section = QVBoxLayout()
        color_section.setSpacing(12)  # Further increased spacing for vertical distribution
        color_label = QLabel("Color Scheme")
        color_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        color_section.addWidget(color_label)

        self.color_combo = QComboBox()
        self.color_combo.addItem("Classic Blue", ColorScheme.CLASSIC_BLUE)
        self.color_combo.addItem("Spectral Rainbow", ColorScheme.SPECTRAL_RAINBOW)
        self.color_combo.addItem("Energy Heat", ColorScheme.ENERGY_HEAT)
        self.color_combo.addItem("Frequency Based", ColorScheme.FREQUENCY_BASED)
        self.color_combo.addItem("Professional Dark", ColorScheme.PROFESSIONAL_DARK)
        self.color_combo.addItem("Studio Monitor", ColorScheme.STUDIO_MONITOR)
        self.color_combo.addItem("Vintage Analog", ColorScheme.VINTAGE_ANALOG)
        self.color_combo.setCurrentIndex(4)  # Default to Professional Dark (best contrast)
        self.color_combo.setMinimumWidth(150)
        self.color_combo.setMinimumHeight(30)
        color_section.addWidget(self.color_combo)
        main_controls_layout.addLayout(color_section)

        # Smoothing Section
        smoothing_section = QVBoxLayout()
        smoothing_section.setSpacing(12)  # Further increased spacing for vertical distribution
        smoothing_label = QLabel("Smoothing")
        smoothing_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        smoothing_section.addWidget(smoothing_label)

        smoothing_controls = QHBoxLayout()
        smoothing_controls.setSpacing(8)
        self.smoothing_slider = QSlider(Qt.Horizontal)
        self.smoothing_slider.setRange(0, 100)
        self.smoothing_slider.setValue(15)  # 0.15 default (moderate smoothing for cleaner visualization)
        self.smoothing_slider.setMinimumWidth(120)
        self.smoothing_slider.setMinimumHeight(20)
        self.smoothing_value_label = QLabel("0.15")
        self.smoothing_value_label.setMinimumWidth(35)
        self.smoothing_value_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #00ff80;")
        smoothing_controls.addWidget(self.smoothing_slider)
        smoothing_controls.addWidget(self.smoothing_value_label)
        smoothing_section.addLayout(smoothing_controls)
        main_controls_layout.addLayout(smoothing_section)

        # Dynamic Range Section
        range_section = QVBoxLayout()
        range_section.setSpacing(12)  # Further increased spacing for vertical distribution
        range_label = QLabel("Dynamic Range")
        range_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        range_section.addWidget(range_label)

        self.range_spinbox = QSpinBox()
        self.range_spinbox.setRange(20, 120)
        self.range_spinbox.setValue(60)  # 60 dB (professional standard)
        self.range_spinbox.setSuffix(" dB")
        self.range_spinbox.setMinimumWidth(70)
        self.range_spinbox.setMinimumHeight(25)
        range_section.addWidget(self.range_spinbox)
        main_controls_layout.addLayout(range_section)

        # Frequency Bands Section
        bands_section = QVBoxLayout()
        bands_section.setSpacing(12)  # Further increased spacing for vertical distribution
        bands_label = QLabel("Frequency Bands")
        bands_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        bands_section.addWidget(bands_label)

        self.bands_spinbox = QSpinBox()
        self.bands_spinbox.setRange(4, 32)
        self.bands_spinbox.setValue(12)  # 12 bands (better frequency resolution for drums)
        self.bands_spinbox.setMinimumWidth(55)
        self.bands_spinbox.setMinimumHeight(25)
        bands_section.addWidget(self.bands_spinbox)
        main_controls_layout.addLayout(bands_section)

        # Quick Presets Section
        presets_section = QVBoxLayout()
        presets_section.setSpacing(12)  # Further increased spacing for vertical distribution
        presets_label = QLabel("Quick Presets")
        presets_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        presets_section.addWidget(presets_label)

        preset_buttons_layout = QHBoxLayout()
        preset_buttons_layout.setSpacing(5)

        self.studio_preset_btn = QPushButton("Studio")
        self.music_preset_btn = QPushButton("Music")
        self.speech_preset_btn = QPushButton("Speech")
        self.analysis_preset_btn = QPushButton("Analysis")

        # Make buttons compact but visible with larger text
        for btn in [self.studio_preset_btn, self.music_preset_btn, self.speech_preset_btn, self.analysis_preset_btn]:
            btn.setMinimumHeight(24)
            btn.setMinimumWidth(55)
            btn.setStyleSheet("font-size: 12px; padding: 6px 10px; font-weight: bold;")

        preset_buttons_layout.addWidget(self.studio_preset_btn)
        preset_buttons_layout.addWidget(self.music_preset_btn)
        preset_buttons_layout.addWidget(self.speech_preset_btn)
        preset_buttons_layout.addWidget(self.analysis_preset_btn)

        presets_section.addLayout(preset_buttons_layout)
        main_controls_layout.addLayout(presets_section)

        # Add the main controls to the layout
        layout.addLayout(main_controls_layout)

        # Add Zoom Controls section
        zoom_group = self._create_zoom_controls_group()
        layout.addWidget(zoom_group)

        # Add Advanced Settings section
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QVBoxLayout(advanced_group)
        advanced_layout.setSpacing(15)  # Good spacing to spread out vertically
        advanced_layout.setContentsMargins(12, 12, 12, 12)  # Reasonable margins

        # Beat Detection Analysis section (directly in Advanced Settings)
        beat_controls = self._create_beat_detection_controls()
        advanced_layout.addLayout(beat_controls)

        # State Management section
        state_group = self._create_state_management_group()
        advanced_layout.addWidget(state_group)

        layout.addWidget(advanced_group)

        # Add stretch at the end to fill remaining space
        layout.addStretch()

    def _connect_signals(self):
        """Connect widget signals to handlers"""
        # Professional rendering toggle removed - always enabled
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self.color_combo.currentIndexChanged.connect(self._on_color_changed)
        self.smoothing_slider.valueChanged.connect(self._on_smoothing_changed)
        self.range_spinbox.valueChanged.connect(self._on_dynamic_range_changed)
        self.bands_spinbox.valueChanged.connect(self._on_frequency_bands_changed)

        # Preset buttons
        self.studio_preset_btn.clicked.connect(self._apply_studio_preset)
        self.music_preset_btn.clicked.connect(self._apply_music_preset)
        self.speech_preset_btn.clicked.connect(self._apply_speech_preset)
        self.analysis_preset_btn.clicked.connect(self._apply_analysis_preset)

        # Beat Detection Signals (will be connected after UI creation)
        # State Management Signals (will be connected after UI creation)
        # Zoom Control Signals (will be connected after UI creation)

    def _connect_additional_signals(self):
        """Connect signals for beat detection, state management, and zoom controls after UI creation"""
        if hasattr(self, 'analyze_button'):
            self.analyze_button.clicked.connect(self.analyze_file_requested.emit)
        if hasattr(self, 'manual_peak_checkbox'):
            # Use toggled signal instead of stateChanged for more reliable detection
            self.manual_peak_checkbox.toggled.connect(self._on_manual_peak_toggled)
            # Keep stateChanged as backup
            self.manual_peak_checkbox.stateChanged.connect(self._on_manual_peak_changed)
        if hasattr(self, 'double_shot_checkbox'):
            # Connect double shot checkbox
            self.double_shot_checkbox.toggled.connect(self._on_double_shot_toggled)
            # Keep stateChanged as backup
            self.double_shot_checkbox.stateChanged.connect(self._on_double_shot_changed)
        if hasattr(self, 'peak_count_slider') and hasattr(self, 'peak_count_spinbox'):
            # Connect slider and spinbox to stay synchronized
            self.peak_count_slider.valueChanged.connect(self._on_slider_changed)
            self.peak_count_spinbox.valueChanged.connect(self._on_spinbox_changed)
        if hasattr(self, 'save_state_btn'):
            self.save_state_btn.clicked.connect(self.save_state_requested.emit)
        if hasattr(self, 'load_state_btn'):
            self.load_state_btn.clicked.connect(self.load_state_requested.emit)
        if hasattr(self, 'zoom_slider'):
            self.zoom_slider.valueChanged.connect(self._on_zoom_slider_changed)
        if hasattr(self, 'reset_zoom_btn'):
            self.reset_zoom_btn.clicked.connect(self.zoom_reset_requested.emit)

    def _apply_styling(self):
        """Apply professional styling"""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 3px;
                margin-top: 5px;
                padding-top: 5px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 5px;
                padding: 0 3px 0 3px;
                font-size: 12px;
                font-weight: bold;
            }

            QComboBox {
                padding: 5px;
                border: 1px solid #666;
                border-radius: 3px;
                background-color: #2a2a2a;
                color: white;
                font-size: 13px;
                min-height: 28px;
            }

            QComboBox::drop-down {
                border: none;
            }

            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #aaa;
            }

            QPushButton {
                padding: 5px 10px;
                border: 1px solid #666;
                border-radius: 3px;
                background-color: #3a3a3a;
                color: white;
                font-weight: bold;
                font-size: 10px;
                min-height: 24px;
            }

            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #888;
            }

            QPushButton:pressed {
                background-color: #2a2a2a;
            }

            QSlider::groove:horizontal {
                border: 1px solid #666;
                height: 12px;
                background: #2a2a2a;
                border-radius: 6px;
            }

            QSlider::handle:horizontal {
                background: #0078d4;
                border: 1px solid #005a9e;
                width: 22px;
                margin: -6px 0;
                border-radius: 11px;
            }

            QSlider::handle:horizontal:hover {
                background: #106ebe;
            }

            QSpinBox {
                padding: 5px;
                border: 1px solid #666;
                border-radius: 3px;
                background-color: #2a2a2a;
                color: white;
                font-size: 13px;
                min-height: 28px;
            }

            QCheckBox {
                spacing: 8px;
            }

            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }

            QCheckBox::indicator:unchecked {
                border: 2px solid #666;
                background-color: #2a2a2a;
                border-radius: 3px;
            }

            QCheckBox::indicator:checked {
                border: 2px solid #0078d4;
                background-color: #0078d4;
                border-radius: 3px;
            }
        """)

    def _on_mode_changed(self, index: int):
        """Handle rendering mode change"""
        mode = self.mode_combo.itemData(index)
        self.render_mode_changed.emit(mode)

    def _on_color_changed(self, index: int):
        """Handle color scheme change"""
        scheme = self.color_combo.itemData(index)
        self.color_scheme_changed.emit(scheme)

    def _on_smoothing_changed(self, value: int):
        """Handle smoothing factor change with debouncing"""
        smoothing = value / 100.0  # Convert to 0.0-1.0 range
        self.smoothing_value_label.setText(f"{smoothing:.2f}")
        print(f"🎛️ CONTROL PANEL: Smoothing slider changed to {smoothing:.3f}")

        # Use debouncing to prevent rapid-fire updates
        self._pending_changes['smoothing'] = smoothing
        self._debounce_timer.start(self._debounce_delay)

    def _on_dynamic_range_changed(self, value: int):
        """Handle dynamic range change with debouncing"""
        print(f"🎛️ CONTROL PANEL: Dynamic range changed to {value} dB")

        # Use debouncing to prevent rapid-fire updates
        self._pending_changes['dynamic_range'] = float(value)
        self._debounce_timer.start(self._debounce_delay)

    def _on_frequency_bands_changed(self, value: int):
        """Handle frequency bands change with debouncing"""
        print(f"🎛️ CONTROL PANEL: Frequency bands changed to {value}")

        # Use debouncing to prevent rapid-fire updates
        self._pending_changes['frequency_bands'] = value
        self._debounce_timer.start(self._debounce_delay)

    def _apply_studio_preset(self):
        """Apply studio monitoring preset - Professional monitoring with accurate level representation"""
        # Temporarily disable signals to avoid multiple updates
        self._disable_signals()

        self.mode_combo.setCurrentIndex(1)  # RMS Envelope (accurate level metering)
        self.color_combo.setCurrentIndex(5)  # Studio Monitor (green/yellow/red VU meters)
        self.smoothing_slider.setValue(10)  # 0.10 smoothing (minimal, professional)
        self.range_spinbox.setValue(60)  # 60 dB (professional standard)
        self.bands_spinbox.setValue(8)  # 8 bands (standard monitoring)

        # Re-enable signals and emit all changes at once
        self._enable_signals()
        self._emit_all_current_values()

    def _apply_music_preset(self):
        """Apply music visualization preset - Optimized for musical content and mixing"""
        # Temporarily disable signals to avoid multiple updates
        self._disable_signals()

        self.mode_combo.setCurrentIndex(4)  # Frequency Bands (excellent for music/drums)
        self.color_combo.setCurrentIndex(1)  # Spectral Rainbow (frequency visualization)
        self.smoothing_slider.setValue(20)  # 0.20 smoothing (musical, smooth)
        self.range_spinbox.setValue(70)  # 70 dB (wide dynamic range for music)
        self.bands_spinbox.setValue(16)  # 16 bands (detailed frequency resolution)

        # Re-enable signals and emit all changes at once
        self._enable_signals()
        self._emit_all_current_values()

    def _apply_speech_preset(self):
        """Apply speech analysis preset - Optimized for voice/dialogue content"""
        # Temporarily disable signals to avoid multiple updates
        self._disable_signals()

        self.mode_combo.setCurrentIndex(1)  # RMS Envelope (good for speech dynamics)
        self.color_combo.setCurrentIndex(0)  # Classic Blue (clean, professional)
        self.smoothing_slider.setValue(30)  # 0.30 smoothing (smooth speech contours)
        self.range_spinbox.setValue(50)  # 50 dB (appropriate for speech)
        self.bands_spinbox.setValue(6)  # 6 bands (speech frequency range)

        # Re-enable signals and emit all changes at once
        self._enable_signals()
        self._emit_all_current_values()

    def _apply_analysis_preset(self):
        """Apply detailed analysis preset - Technical analysis, mastering, forensics"""
        # Temporarily disable signals to avoid multiple updates
        self._disable_signals()

        self.mode_combo.setCurrentIndex(3)  # Dual Layer (transients + sustain)
        self.color_combo.setCurrentIndex(4)  # Professional Dark (best contrast)
        self.smoothing_slider.setValue(5)  # 0.05 smoothing (minimal, preserve detail)
        self.range_spinbox.setValue(80)  # 80 dB (high dynamic range for analysis)
        self.bands_spinbox.setValue(24)  # 24 bands (ultra-detailed frequency analysis)

        # Re-enable signals and emit all changes at once
        self._enable_signals()
        self._emit_all_current_values()

    def _disable_signals(self):
        """Temporarily disable all control signals to prevent multiple updates"""
        self.mode_combo.blockSignals(True)
        self.color_combo.blockSignals(True)
        self.smoothing_slider.blockSignals(True)
        self.range_spinbox.blockSignals(True)
        self.bands_spinbox.blockSignals(True)

    def _enable_signals(self):
        """Re-enable all control signals"""
        self.mode_combo.blockSignals(False)
        self.color_combo.blockSignals(False)
        self.smoothing_slider.blockSignals(False)
        self.range_spinbox.blockSignals(False)
        self.bands_spinbox.blockSignals(False)

    def _emit_all_current_values(self):
        """Emit all current control values at once for batched updates"""
        # Emit all changes in the correct order
        mode = self.mode_combo.itemData(self.mode_combo.currentIndex())
        if mode:
            self.render_mode_changed.emit(mode)

        scheme = self.color_combo.itemData(self.color_combo.currentIndex())
        if scheme:
            self.color_scheme_changed.emit(scheme)

        # Use pending changes for debounced controls
        smoothing = self.smoothing_slider.value() / 100.0
        self._pending_changes['smoothing'] = smoothing

        dynamic_range = float(self.range_spinbox.value())
        self._pending_changes['dynamic_range'] = dynamic_range

        frequency_bands = self.bands_spinbox.value()
        self._pending_changes['frequency_bands'] = frequency_bands

        # Trigger debounced emission
        self._debounce_timer.start(50)  # Shorter delay for presets

    def get_current_settings(self) -> dict:
        """Get current control settings"""
        return {
            'professional_enabled': self.professional_toggle.isChecked(),
            'render_mode': self.mode_combo.currentData(),
            'color_scheme': self.color_combo.currentData(),
            'smoothing': self.smoothing_slider.value() / 100.0,
            'dynamic_range': self.range_spinbox.value(),
            'frequency_bands': self.bands_spinbox.value()
        }

    def set_settings(self, settings: dict):
        """Apply settings to controls"""
        if 'professional_enabled' in settings:
            self.professional_toggle.setChecked(settings['professional_enabled'])

        if 'render_mode' in settings:
            for i in range(self.mode_combo.count()):
                if self.mode_combo.itemData(i) == settings['render_mode']:
                    self.mode_combo.setCurrentIndex(i)
                    break

        if 'color_scheme' in settings:
            for i in range(self.color_combo.count()):
                if self.color_combo.itemData(i) == settings['color_scheme']:
                    self.color_combo.setCurrentIndex(i)
                    break

        if 'smoothing' in settings:
            self.smoothing_slider.setValue(int(settings['smoothing'] * 100))

        if 'dynamic_range' in settings:
            self.range_spinbox.setValue(settings['dynamic_range'])

        if 'frequency_bands' in settings:
            self.bands_spinbox.setValue(settings['frequency_bands'])

    def _create_beat_detection_controls(self) -> QVBoxLayout:
        """Create the beat detection analysis controls (no QGroupBox wrapper)"""
        # Main vertical layout to hold everything
        beat_layout = QVBoxLayout()
        beat_layout.setSpacing(10)

        # Main horizontal layout for all elements
        main_horizontal_layout = QHBoxLayout()
        main_horizontal_layout.setSpacing(20)

        # LEFT SECTION: Three buttons in horizontal layout (side-by-side)
        buttons_section = QHBoxLayout()
        buttons_section.setSpacing(10)

        # ANALYZE button
        self.analyze_button = QPushButton("ANALYZE DRUM STEM")
        self.analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 6px 12px;
                border: none;
                border-radius: 3px;
                min-height: 28px;
                min-width: 250px;
                max-width: 250px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        buttons_section.addWidget(self.analyze_button, alignment=Qt.AlignVCenter)

        buttons_section.addSpacing(20)

        # Peak Selection Controls with label above
        peak_controls_section = QVBoxLayout()
        peak_controls_section.setSpacing(2)  # Reduced spacing to raise slider
        peak_controls_section.setAlignment(Qt.AlignVCenter)

        # Label above slider (with reduced margins)
        peaks_label = QLabel("Peaks Included in Musical")
        peaks_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #ffffff;
                margin-bottom: 0px;
                padding-bottom: 0px;
            }
        """)
        peaks_label.setAlignment(Qt.AlignCenter)
        peak_controls_section.addWidget(peaks_label)

        # Horizontal layout for slider and spinbox
        slider_spinbox_layout = QHBoxLayout()
        slider_spinbox_layout.setSpacing(10)
        slider_spinbox_layout.setAlignment(Qt.AlignVCenter)

        # Slider for peak selection (matching waveform rendering style)
        self.peak_count_slider = QSlider(Qt.Horizontal)
        self.peak_count_slider.setMinimum(0)
        self.peak_count_slider.setMaximum(1000)  # Will be updated after analysis
        self.peak_count_slider.setValue(1000)
        self.peak_count_slider.setEnabled(False)  # Disabled until analysis
        self.peak_count_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #666;
                height: 12px;
                background: #2a2a2a;
                border-radius: 6px;
            }
            QSlider::handle:horizontal {
                background: #0078d4;
                border: 1px solid #005a9e;
                width: 22px;
                margin: -6px 0;
                border-radius: 11px;
            }
            QSlider::handle:horizontal:hover {
                background: #106ebe;
            }
            QSlider::sub-page:horizontal {
                background: #0078d4;
                border: 1px solid #005a9e;
                height: 12px;
                border-radius: 6px;
            }
        """)
        self.peak_count_slider.setMinimumWidth(600)  # Wider slider
        self.peak_count_slider.setFixedHeight(28)  # Fixed height to match button
        slider_spinbox_layout.addWidget(self.peak_count_slider, alignment=Qt.AlignVCenter)

        # Spinbox for precise input (matching waveform rendering style)
        self.peak_count_spinbox = QSpinBox()
        self.peak_count_spinbox.setMinimum(0)
        self.peak_count_spinbox.setMaximum(1000)  # Will be updated after analysis
        self.peak_count_spinbox.setValue(1000)
        self.peak_count_spinbox.setEnabled(False)  # Disabled until analysis
        self.peak_count_spinbox.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                border: 1px solid #666;
                border-radius: 3px;
                background-color: #2a2a2a;
                color: white;
                font-size: 13px;
                min-height: 28px;
                max-height: 28px;
                min-width: 80px;
                max-width: 80px;
            }
            QSpinBox:focus {
                border: 1px solid #0078d4;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #3a3a3a;
                border: 1px solid #666;
                width: 16px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #4a4a4a;
            }
        """)
        slider_spinbox_layout.addWidget(self.peak_count_spinbox, alignment=Qt.AlignVCenter)

        peak_controls_section.addLayout(slider_spinbox_layout)
        buttons_section.addLayout(peak_controls_section)

        # Add buttons section to main layout
        main_horizontal_layout.addLayout(buttons_section)

        # Add small spacing between buttons and checkbox
        main_horizontal_layout.addSpacing(20)

        # CHECKBOX SECTION: Manual Peak and Double Shot checkboxes side by side
        checkbox_section = QHBoxLayout()
        checkbox_section.setSpacing(8)
        checkbox_section.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Manual checkbox
        self.manual_peak_checkbox = QCheckBox()
        self.manual_peak_checkbox.setFixedSize(28, 28)  # Match indicator size exactly
        self.manual_peak_checkbox.setStyleSheet("""
            QCheckBox {
                background-color: transparent;
                border: none;
                outline: none;
                spacing: 0px;
                margin: 0px;
                padding: 0px;
            }
            QCheckBox::indicator {
                width: 28px;
                height: 28px;
                subcontrol-position: center;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #bdc3c7;
                background-color: white;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #27ae60;
                background-color: #27ae60;
                border-radius: 4px;
            }
            QCheckBox:focus {
                outline: none;
                border: none;
            }
        """)
        checkbox_section.addWidget(self.manual_peak_checkbox)

        # Label to the right of manual checkbox
        self.manual_label = QLabel("Add Peaks Disabled")
        self.manual_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #3498db;")
        self.manual_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        checkbox_section.addWidget(self.manual_label)

        # Add spacing between checkboxes
        checkbox_section.addSpacing(20)

        # Double Shot checkbox
        self.double_shot_checkbox = QCheckBox()
        self.double_shot_checkbox.setEnabled(False)  # Disabled by default until manual peak mode is enabled
        self.double_shot_checkbox.setFixedSize(28, 28)  # Match indicator size exactly
        self.double_shot_checkbox.setStyleSheet("""
            QCheckBox {
                background-color: transparent;
                border: none;
                outline: none;
                spacing: 0px;
                margin: 0px;
                padding: 0px;
            }
            QCheckBox::indicator {
                width: 28px;
                height: 28px;
                subcontrol-position: center;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #bdc3c7;
                background-color: white;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #e74c3c;
                background-color: #e74c3c;
                border-radius: 4px;
            }
            QCheckBox:disabled::indicator {
                border: 2px solid #555;
                background-color: #3a3a3a;
            }
            QCheckBox:focus {
                outline: none;
                border: none;
            }
        """)
        checkbox_section.addWidget(self.double_shot_checkbox)

        # Label to the right of double shot checkbox
        self.double_shot_label = QLabel("Double Shot Disabled")
        self.double_shot_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #e74c3c;")
        self.double_shot_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        checkbox_section.addWidget(self.double_shot_label)

        # Add checkbox section to main layout
        main_horizontal_layout.addLayout(checkbox_section)

        # Add large stretch to push counters to far right
        main_horizontal_layout.addStretch(3)

        # RIGHT SECTION: Peak counters with labels below
        counters_section = QHBoxLayout()
        counters_section.setSpacing(25)

        # Detected peaks counter
        detected_section = QVBoxLayout()
        detected_section.setSpacing(2)
        detected_section.setAlignment(Qt.AlignCenter)

        self.detected_peak_count = QLabel("0")
        self.detected_peak_count.setAlignment(Qt.AlignCenter)
        self.detected_peak_count.setStyleSheet("font-weight: bold; color: #3498db; font-size: 18px;")
        detected_section.addWidget(self.detected_peak_count)

        detected_label = QLabel("Detected")
        detected_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #ffffff;")
        detected_label.setAlignment(Qt.AlignCenter)
        detected_section.addWidget(detected_label)

        counters_section.addLayout(detected_section)

        # Custom peaks counter
        custom_section = QVBoxLayout()
        custom_section.setSpacing(2)
        custom_section.setAlignment(Qt.AlignCenter)

        self.custom_peak_count = QLabel("0")
        self.custom_peak_count.setAlignment(Qt.AlignCenter)
        self.custom_peak_count.setStyleSheet("font-weight: bold; color: #e67e22; font-size: 18px;")
        custom_section.addWidget(self.custom_peak_count)

        custom_label = QLabel("Custom")
        custom_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #ffffff;")
        custom_label.setAlignment(Qt.AlignCenter)
        custom_section.addWidget(custom_label)

        counters_section.addLayout(custom_section)

        # Total peaks counter
        total_section = QVBoxLayout()
        total_section.setSpacing(2)
        total_section.setAlignment(Qt.AlignCenter)

        self.total_peak_count = QLabel("0")
        self.total_peak_count.setAlignment(Qt.AlignCenter)
        self.total_peak_count.setStyleSheet("font-weight: bold; color: #2ecc71; font-size: 18px;")
        total_section.addWidget(self.total_peak_count)

        total_label = QLabel("Total")
        total_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #ffffff;")
        total_label.setAlignment(Qt.AlignCenter)
        total_section.addWidget(total_label)

        counters_section.addLayout(total_section)

        # Add counters section to main layout
        main_horizontal_layout.addLayout(counters_section)

        # Add main horizontal layout to the beat layout
        beat_layout.addLayout(main_horizontal_layout)

        return beat_layout

    def _create_state_management_group(self) -> QGroupBox:
        """Create the state management group"""
        state_group = QGroupBox("State Management")
        state_layout = QHBoxLayout(state_group)
        state_layout.setSpacing(20)  # Increased spacing between buttons
        state_layout.setContentsMargins(15, 15, 15, 15)  # Increased margins

        self.save_state_btn = QPushButton("💾 Save State")
        self.save_state_btn.setToolTip("Save current waveform analysis state")
        self.save_state_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 13px;
                min-height: 28px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)

        self.load_state_btn = QPushButton("📁 Load State")
        self.load_state_btn.setToolTip("Load previously saved waveform analysis state")
        self.load_state_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 13px;
                min-height: 28px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)

        state_layout.addWidget(self.save_state_btn)
        state_layout.addWidget(self.load_state_btn)

        return state_group

    def _on_manual_peak_changed(self, state):
        """Handle manual peak mode checkbox change"""
        # Debug logging - show raw state value
        print(f"🔧 Controls Panel: Raw checkbox state received: {state} (type: {type(state)})")
        print(f"🔧 Controls Panel: Qt.Checked value: {Qt.Checked}")
        print(f"🔧 Controls Panel: Qt.Unchecked value: {Qt.Unchecked}")

        # Handle both integer and Qt enum values
        if isinstance(state, int):
            is_checked = state == Qt.Checked.value if hasattr(Qt.Checked, 'value') else state == 2
        else:
            is_checked = state == Qt.Checked

        print(f"🔧 Controls Panel: Manual peak checkbox changed to: {is_checked}")

        # Update label text based on checkbox state
        if is_checked:
            self.manual_label.setText("Add Peaks Enabled")
            print("🔧 Controls Panel: Label updated to 'Enabled'")
            # Enable double shot checkbox when manual peak mode is enabled
            self.double_shot_checkbox.setEnabled(True)
        else:
            self.manual_label.setText("Add Peaks Disabled")
            print("🔧 Controls Panel: Label updated to 'Disabled'")
            # Disable and uncheck double shot checkbox when manual peak mode is disabled
            self.double_shot_checkbox.setEnabled(False)
            self.double_shot_checkbox.setChecked(False)

        # Emit the signal to notify other components
        print(f"🔧 Controls Panel: Emitting manual_peak_mode_changed signal with: {is_checked}")
        self.manual_peak_mode_changed.emit(is_checked)

    def _on_manual_peak_toggled(self, checked):
        """Handle manual peak mode checkbox toggle (more reliable signal)"""
        print(f"🔧 Controls Panel: Toggled signal received: {checked} (type: {type(checked)})")

        # Update label text based on checkbox state
        if checked:
            self.manual_label.setText("Add Peaks Enabled")
            print("🔧 Controls Panel: Label updated to 'Enabled' via toggled")
            # Enable double shot checkbox when manual peak mode is enabled
            self.double_shot_checkbox.setEnabled(True)
        else:
            self.manual_label.setText("Add Peaks Disabled")
            print("🔧 Controls Panel: Label updated to 'Disabled' via toggled")
            # Disable and uncheck double shot checkbox when manual peak mode is disabled
            self.double_shot_checkbox.setEnabled(False)
            self.double_shot_checkbox.setChecked(False)

        # Emit the signal to notify other components
        print(f"🔧 Controls Panel: Emitting manual_peak_mode_changed signal via toggled with: {checked}")
        self.manual_peak_mode_changed.emit(checked)

    def _on_slider_changed(self, value: int):
        """Handle slider value change - update spinbox and emit signal"""
        # Block spinbox signals to avoid circular updates
        self.peak_count_spinbox.blockSignals(True)
        self.peak_count_spinbox.setValue(value)
        self.peak_count_spinbox.blockSignals(False)

        # Emit signal for waveform update
        self.peak_count_changed.emit(value)

    def _on_spinbox_changed(self, value: int):
        """Handle spinbox value change - update slider and emit signal"""
        # Block slider signals to avoid circular updates
        self.peak_count_slider.blockSignals(True)
        self.peak_count_slider.setValue(value)
        self.peak_count_slider.blockSignals(False)

        # Emit signal for waveform update
        self.peak_count_changed.emit(value)

    def _on_double_shot_toggled(self, checked):
        """Handle double shot mode checkbox toggle (more reliable signal)"""
        print(f"🔧 Controls Panel: Double Shot toggled signal received: {checked} (type: {type(checked)})")

        # Update label text based on checkbox state
        if checked:
            self.double_shot_label.setText("Double Shot Enabled")
            print("🔧 Controls Panel: Double Shot label updated to 'Enabled' via toggled")
        else:
            self.double_shot_label.setText("Double Shot Disabled")
            print("🔧 Controls Panel: Double Shot label updated to 'Disabled' via toggled")

        # Emit the signal to notify other components
        print(f"🔧 Controls Panel: Emitting double_shot_mode_changed signal via toggled with: {checked}")
        self.double_shot_mode_changed.emit(checked)

    def _on_double_shot_changed(self, state):
        """Handle double shot mode checkbox change"""
        # Debug logging - show raw state value
        print(f"🔧 Controls Panel: Double Shot raw checkbox state received: {state} (type: {type(state)})")
        print(f"🔧 Controls Panel: Qt.Checked value: {Qt.Checked}")
        print(f"🔧 Controls Panel: Qt.Unchecked value: {Qt.Unchecked}")

        # Handle both integer and Qt enum values
        if isinstance(state, int):
            is_checked = state == Qt.Checked.value if hasattr(Qt.Checked, 'value') else state == 2
        else:
            is_checked = state == Qt.Checked

        print(f"🔧 Controls Panel: Double Shot checkbox changed to: {is_checked}")

        # Update label text based on checkbox state
        if is_checked:
            self.double_shot_label.setText("Double Shot Enabled")
            print("🔧 Controls Panel: Double Shot label updated to 'Enabled'")
        else:
            self.double_shot_label.setText("Double Shot Disabled")
            print("🔧 Controls Panel: Double Shot label updated to 'Disabled'")

        # Emit the signal to notify other components
        print(f"🔧 Controls Panel: Emitting double_shot_mode_changed signal with: {is_checked}")
        self.double_shot_mode_changed.emit(is_checked)

    def update_peak_counts(self, detected: int, custom: int, total: int):
        """Update the peak count displays"""
        self.detected_peak_count.setText(str(detected))
        self.custom_peak_count.setText(str(custom))
        self.total_peak_count.setText(str(total))

    def set_peak_slider_range(self, max_peaks: int):
        """Set the maximum range for peak slider/spinbox after analysis"""
        if max_peaks > 0:
            # Update slider
            self.peak_count_slider.setMaximum(max_peaks)
            self.peak_count_slider.setValue(max_peaks)  # Default to all peaks
            self.peak_count_slider.setEnabled(True)

            # Update spinbox
            self.peak_count_spinbox.setMaximum(max_peaks)
            self.peak_count_spinbox.setValue(max_peaks)  # Default to all peaks
            self.peak_count_spinbox.setEnabled(True)

            print(f"🔧 Peak slider range set to 0-{max_peaks}, default value: {max_peaks}")
        else:
            # No peaks, disable controls
            self.peak_count_slider.setEnabled(False)
            self.peak_count_spinbox.setEnabled(False)

    def _create_zoom_controls_group(self) -> QGroupBox:
        """Create the zoom controls group with compact horizontal layout"""
        zoom_group = QGroupBox("Zoom Controls")
        zoom_layout = QVBoxLayout(zoom_group)
        zoom_layout.setSpacing(8)  # Reduced spacing for more compact layout
        zoom_layout.setContentsMargins(10, 10, 10, 10)  # Reduced margins

        # Single horizontal layout for reset button, slider, and indicator
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)

        # Reset zoom button on the left (much wider)
        self.reset_zoom_btn = QPushButton("Reset Zoom")
        self.reset_zoom_btn.setEnabled(False)  # Will be enabled when waveform loads
        self.reset_zoom_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 14px;
                max-height: 28px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #495057;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        controls_layout.addWidget(self.reset_zoom_btn)

        # Zoom slider (uses full remaining width)
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(0, 100)
        self.zoom_slider.setValue(50)  # Default middle position
        self.zoom_slider.setEnabled(False)  # Will be enabled when waveform loads
        self.zoom_slider.setMinimumHeight(24)  # Original height
        # Use maximum stretch factor to fill all remaining space
        controls_layout.addWidget(self.zoom_slider, 3)  # Higher stretch factor for full width

        # Zoom indicator label
        self.zoom_label = QLabel("1.0x")
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        self.zoom_label.setMinimumWidth(55)
        self.zoom_label.setMaximumWidth(55)  # Fixed width
        controls_layout.addWidget(self.zoom_label)

        zoom_layout.addLayout(controls_layout)

        return zoom_group

    def _on_zoom_slider_changed(self, value: int):
        """Handle zoom slider value change"""
        # Convert slider value to zoom factor (logarithmic scale)
        # This will be connected to the waveform view's zoom functionality
        self.zoom_changed.emit(value)

    def update_zoom_display(self, zoom_factor: float):
        """Update the zoom indicator display"""
        self.zoom_label.setText(f"{zoom_factor:.1f}x")

    def set_zoom_controls_enabled(self, enabled: bool):
        """Enable/disable zoom controls"""
        self.zoom_slider.setEnabled(enabled)
        self.reset_zoom_btn.setEnabled(enabled)

    def set_zoom_slider_value(self, value: int):
        """Set zoom slider value without triggering signals"""
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(value)
        self.zoom_slider.blockSignals(False)
