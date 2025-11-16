"""
Waveform Analysis and Visualization Dialog
==========================================

Comprehensive dialog for displaying and interacting with music waveforms including real-time analysis and playback.

Features:
- Real-time waveform visualization
- Background waveform analysis
- Audio playback controls
- Interactive zoom and pan
- Performance monitoring
- Beat detection display
- Multiple rendering modes
- Progress tracking

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

import traceback
from datetime import datetime
import time

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QSplitter, QWidget,
    QProgressBar, QSlider, QDialogButtonBox,
    QMessageBox, QStyle, QApplication, QTabWidget, QSpinBox, QTableWidgetItem, QComboBox, QCheckBox)
from PySide6.QtCore import (
    Qt, Signal, QRect, Slot, QUrl, QTimer, QThread, QObject,
    QMetaObject, Q_ARG, QModelIndex)
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

import os
import math
import logging
from typing import Optional, Dict, List
from pathlib import Path
from utils.audio.performance_monitor import profile_method

from views.waveform.waveform_widget import WaveformView
from utils.audio.waveform_analyzer import WaveformAnalyzer
from utils.musical_generator import MusicalGenerator
from controllers.waveform_controller import WaveformControlsPanel

# Import JSON utilities for safe serialization
try:
    from utils.json_utils import safe_json_dumps, safe_json_loads, clean_data_for_json
except ImportError:
    # Fallback if json_utils is not available
    import json


    def safe_json_dumps(data, **kwargs):
        return json.dumps(data, **kwargs)


    def safe_json_loads(data, **kwargs):
        return json.loads(data, **kwargs)


    def clean_data_for_json(data):
        return data


class WaveformAnalysisDialog(QDialog):
    """
    OPTIMIZED: Dialog for displaying and interacting with music waveforms

    Features:
    - Real-time waveform visualization with lazy loading
    - Background processing for analysis
    - Audio playback controls
    - Interactive zoom and navigation
    - Optimized peak detection visualization
    - Time and amplitude markers
    - Performance monitoring
    """

    # Signal emitted when waveform analysis is complete and ready for show generation
    show_generation_ready = Signal(dict)

    def __init__(self, music_file_info: Dict, parent: Optional[QWidget] = None, led_panel=None, cue_table=None):
        """
        Initialize the optimized waveform analysis dialog.

        Args:
            music_file_info: Dictionary containing music file information.
            parent: Parent widget.
            led_panel: Reference to the LedGrid instance.
            cue_table: Reference to the CueTableView instance.
        """
        super().__init__(parent)
        self.setWindowTitle("Waveform Analysis")
        # Set window flags to include minimize button and ensure it's functional
        # Also keep dialog on top of main window for consistency with music_analysis_dialog
        self.setWindowFlags(
            Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        print(f"🎛️ Initializing OptimizedWaveformAnalysisDialog")

        # Store music file information and references
        self.music_file_info = music_file_info
        self.led_panel = led_panel
        self.cue_table = cue_table

        # Configure logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Initialize analyzer to None - will be set by set_analyzer method
        self.analyzer = None

        # OPTIMIZATION: Background processing
        self.analysis_thread = None
        self.analysis_start_time = None

        # OPTIMIZATION: Performance monitoring
        self.ui_update_times = []
        self.peak_display_times = []

        # ENHANCEMENT: Smooth position updates (60fps)
        self.position_update_timer = QTimer()
        self.position_update_timer.timeout.connect(self._update_smooth_position)
        self.position_update_timer.setInterval(16)  # ~60fps (16ms)

        # Initialize signal connection tracking
        self._signal_connected = False

        # Initialize media playback
        self._init_media_player()

        # Initialize timers
        self._init_timers()

        # Set up the UI
        self._init_ui()

        # Connect signals
        self._connect_signals()

        # Processing state
        self.is_processing = False

        # We'll set the analyzer in the waveform view after it's passed to us via set_analyzer()

        # We'll load the waveform data after the analyzer is set via set_analyzer()

    def _init_media_player(self) -> None:
        """Initialize media player and audio output"""
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)

    def _init_timers(self) -> None:
        """Initialize timers for UI updates"""
        # Timer for smooth playback position updates
        self.position_update_timer = QTimer(self)
        self.position_update_timer.setInterval(16)  # ~60fps
        self.position_update_timer.timeout.connect(self._update_position_from_player)

        # Timer for peak detection updates - OPTIMIZED with reduced frequency
        self.peak_check_timer = QTimer(self)
        self.peak_check_timer.setInterval(2000)  # Increased to 2000ms (2 seconds) for better performance
        self.peak_check_timer.timeout.connect(self._update_peak_info_optimized)
        self._is_updating_peak_info = False  # Flag to prevent concurrent updates

        # ENHANCEMENT: Add timeout safety mechanism to prevent infinite loops
        self._peak_check_start_time = None
        self._peak_check_max_duration = 180.0  # Maximum 180 seconds of checking (increased for large files)
        self._peak_check_timeout_warnings = 0  # Track timeout warnings
        self._processing_timeout_threshold = 120.0  # 120 seconds for processing timeout (increased for large files)

        # ENHANCEMENT: Performance and configuration options
        self._peak_update_throttle = 0.2  # Minimum seconds between updates
        self._max_file_size_mb = 500  # Maximum file size in MB
        self._enable_detailed_logging = True  # Can be configured
        self._memory_cleanup_interval = 10  # Clean up every 10 timer cycles

        # INTELLIGENT TIMEOUT SYSTEM - Initialize missing variables
        self._last_progress_time = None
        self._last_peak_count = 0
        self._progress_stall_count = 0
        self._last_processing_state = False

        # Initialize dynamic timeout defaults
        self._dynamic_processing_timeout = 300.0  # 5 minutes default
        self._max_stall_time = 120  # 120s without progress (more reasonable for large files)
        self._max_stall_count = 12  # 12 stalls before timeout (more forgiving)

        # Try to calculate dynamic timeouts (will use defaults if this fails)
        try:
            self._calculate_dynamic_timeouts()
        except Exception as e:
            self.logger.debug(f"Could not calculate dynamic timeouts during init: {e}")

        # Don't start the timer immediately - will be started when processing begins

    def _init_ui(self) -> None:
        """Initialize the user interface"""
        # Configure dialog properties
        self.resize_to_screen()

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Add header section
        self._init_header(main_layout)

        # Create main splitter for resizable sections
        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)

        # Add waveform section
        splitter.addWidget(self._create_waveform_section())

        # Add controls section
        splitter.addWidget(self._create_controls_section())

        # Set initial splitter sizes (85% waveform, 15% controls) - Balanced for all controls
        splitter.setSizes([850, 150])
        main_layout.addWidget(splitter, 1)  # 1 = stretch factor

        # Add dialog buttons - REMOVED to save space for waveform widget
        # self._init_dialog_buttons(main_layout)

        # Set up keyboard shortcuts
        self._setup_shortcuts()

    def _init_header(self, layout: QVBoxLayout) -> None:
        """
        Initialize the header section with title and progress bar

        Args:
            layout: Parent layout to add header to
        """
        # Title with file info
        title_text = (f"Waveform: {self.music_file_info['filename']} - "
                      f"{self.music_file_info['duration']}"
                      if self.music_file_info else "Waveform Analysis")

        self.title_label = QLabel(title_text)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        # Check if librosa is available and show warning if not
        if hasattr(self.analyzer, 'LIBROSA_AVAILABLE') and not self.analyzer.LIBROSA_AVAILABLE:
            warning_label = QLabel("Warning: Advanced audio analysis is limited (librosa not available)")
            warning_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            warning_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(warning_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)  # Determinate progress (0-100%)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFormat("Initializing... %p%")
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

    def _create_waveform_section(self) -> QWidget:
        """
        Create the waveform visualization section

        Returns:
            QWidget containing waveform view and time controls
        """
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(5)

        # Waveform view
        self.waveform_view = WaveformView()
        content_layout.addWidget(self.waveform_view, 1)

        # Time info display
        time_info_layout = QHBoxLayout()
        time_info_layout.setContentsMargins(0, 0, 0, 0)

        # Position display
        self.position_label = QLabel("Position: 00:00.000")
        self.position_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        time_info_layout.addWidget(self.position_label)

        time_info_layout.addStretch()

        # Duration display
        self.duration_label = QLabel("Duration: 00:00.000")
        self.duration_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        time_info_layout.addWidget(self.duration_label)

        content_layout.addLayout(time_info_layout)

        # Time slider
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setRange(0, 1000)
        self.time_slider.setValue(0)
        self.time_slider.setTracking(True)
        self.time_slider.setMinimumHeight(20)
        content_layout.addWidget(self.time_slider)

        return content_widget

    def _create_controls_section(self) -> QWidget:
        """
        Create the controls section with tabbed interface

        Returns:
            QWidget containing all controls
        """
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(5, 5, 5, 5)  # Reduced margins
        controls_layout.setSpacing(5)  # Reduced spacing

        # Create tab widget
        tab_widget = QTabWidget()
        self._style_tab_widget(tab_widget)  # Apply styling

        # Add Professional Waveform Controls tab (FIRST)
        self.waveform_controls_panel = WaveformControlsPanel()
        tab_widget.addTab(self.waveform_controls_panel, "Waveform Controls")

        # Add Generator Controls tab (SECOND)
        generator_tab = self._create_generator_tab()
        tab_widget.addTab(generator_tab, "Generator Controls")

        # Add Audio Playback Controls tab (THIRD)
        playback_tab = self._create_playback_tab()
        tab_widget.addTab(playback_tab, "Audio Playback Controls")

        # Add tab widget to layout
        controls_layout.addWidget(tab_widget)

        return controls_widget

    def _create_playback_tab(self) -> QWidget:
        """
        Create the playback controls tab

        Returns:
            QWidget containing playback controls
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)  # Reduced margins
        layout.setSpacing(5)  # Reduced spacing

        # Add playback controls group
        layout.addWidget(self._create_playback_group())

        # Beat detection group moved to Waveform Controls tab

        # Add stretch to push everything to the top
        layout.addStretch()

        return tab

    def _create_generator_tab(self) -> QWidget:
        """
        Create the generator controls tab

        Returns:
            QWidget containing generator controls
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)  # Reduced margins
        layout.setSpacing(5)  # Reduced spacing

        # Create and add the musical generator widget
        print(f"🔧 Creating musical generator widget")
        print(f"🔧 Current analyzer state: {getattr(self, 'analyzer', 'NOT SET')}")

        self.musical_generator = MusicalGenerator(
            parent=tab,
            waveform_view=self.waveform_view,
            cue_table=self.cue_table
        )

        # Set analyzer if it's already available
        if hasattr(self, 'analyzer') and self.analyzer:
            print(f"🔧 Setting analyzer in generator during creation: {self.analyzer}")
            self.musical_generator.set_analyzer(self.analyzer)
        else:
            print(f"🔧 No analyzer available during generator creation")

        layout.addWidget(self.musical_generator)

        return tab

    @Slot(bool)
    def _on_select_all_changed(self, checked):
        """Handle Select All checkbox toggle."""
        if not self.analyzer:
            return

        if checked:
            # Use get_peak_data() to get the peaks
            peaks = self.analyzer.get_peak_data()
            peak_indices = set(range(len(peaks)))
        else:
            peak_indices = set()

        self.waveform_view.selected_peaks = peak_indices
        self.waveform_view.update()
        self._update_custom_outputs()  # Update the spinbox after Select All

    def _on_manual_peak_mode_changed(self, checked: bool):
        """Handle Manual Peak Refinement Mode checkbox toggle."""
        if hasattr(self.waveform_view, 'set_manual_peak_mode'):
            self.waveform_view.set_manual_peak_mode(checked)

            # Keep detected peaks visible in manual refinement mode
            # Users can now hide individual detected peaks by clicking them
            self.waveform_view.show_analyzer_peaks = True

            # Update the waveform display
            self.waveform_view.update()

        self.logger.info(f"Manual peak placement mode: {'enabled' if checked else 'disabled'}")

    def _on_double_shot_mode_changed(self, checked: bool):
        """Handle Double Shot Mode checkbox toggle."""
        if hasattr(self.waveform_view, 'set_double_shot_mode'):
            self.waveform_view.set_double_shot_mode(checked)

            # Update the waveform display
            self.waveform_view.update()

        self.logger.info(f"Double shot mode: {'enabled' if checked else 'disabled'}")

    def _on_analyze_file(self):
        """Handle ANALYZE FILE button click to trigger comprehensive drum analysis."""
        if not self.analyzer:
            self._show_warning_message("Error", "No analyzer available. Please load an audio file first.")
            return

        if not hasattr(self.analyzer, 'waveform_data') or not self.analyzer.has_waveform_data():
            self._show_warning_message("Error", "No audio data loaded. Please load an audio file first.")
            return

        # Disable the analyze button during processing (it's in the controls panel)
        if hasattr(self, 'waveform_controls_panel') and hasattr(self.waveform_controls_panel, 'analyze_button'):
            self.waveform_controls_panel.analyze_button.setEnabled(False)
            self.waveform_controls_panel.analyze_button.setText("ANALYZING...")

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)  # Determinate progress
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Starting analysis... %p%")

        # Reset peak count display
        self._force_peak_display()

        self.logger.info("Starting comprehensive drum analysis...")

        # Configure analyzer for drum-focused analysis
        if hasattr(self.analyzer, 'config'):
            self.analyzer.config['target_segments'] = ['medium', 'high', 'very_high']
            self.analyzer.config['drum_classification'] = True
            self.analyzer.config['noise_reduction'] = True
            self.analyzer.config['transient_filtering'] = True

        # Connect to enhanced progress updates
        if hasattr(self.analyzer, 'analysis_progress'):
            self.analyzer.analysis_progress.connect(self._on_analysis_progress)
        if hasattr(self.analyzer, 'analysis_status'):
            self.analyzer.analysis_status.connect(self._on_analysis_status)
        if hasattr(self.analyzer, 'analysis_metrics'):
            self.analyzer.analysis_metrics.connect(self._on_analysis_metrics)

        # Start analysis
        def analysis_complete(success):
            """Callback when analysis is complete"""
            # Re-enable the analyze button (it's in the controls panel)
            if hasattr(self, 'waveform_controls_panel') and hasattr(self.waveform_controls_panel, 'analyze_button'):
                self.waveform_controls_panel.analyze_button.setEnabled(True)
                self.waveform_controls_panel.analyze_button.setText("ANALYZE FILE")

            # Hide progress bar
            self.progress_bar.setVisible(False)

            if success:
                # Update peak count display
                peaks = self.analyzer.get_peak_data()
                self._force_peak_display()

                # Save timestamp data for other files to use
                self._save_timestamp_data(peaks)

                # Update waveform view with new peaks
                if hasattr(self.waveform_view, 'update_peaks'):
                    self.waveform_view.update_peaks()
                else:
                    self.waveform_view.update()

                # Show analysis summary
                summary = self.analyzer.get_analysis_summary()
                drum_counts = summary.get('drum_type_counts', {})

                message = f"Analysis Complete!\n\n"
                message += f"Peaks Detected: {len(peaks)}\n"
                message += f"Processing Time: {summary.get('processing_times', {}).get('total_analysis', 0):.2f}s\n\n"

                if drum_counts:
                    message += "Drum Classification:\n"
                    for drum_type, count in drum_counts.items():
                        message += f"  {drum_type.title()}: {count}\n"

                # Add timestamp information
                if peaks:
                    first_time_val = clean_data_for_json(peaks[0].time)
                    last_time_val = clean_data_for_json(peaks[-1].time)
                    first_time = f"{int(first_time_val // 60):02d}:{first_time_val % 60:06.3f}"
                    last_time = f"{int(last_time_val // 60):02d}:{last_time_val % 60:06.3f}"
                    message += f"\nFirst Peak: {first_time}\n"
                    message += f"Last Peak: {last_time}\n"
                    duration_val = clean_data_for_json(self.analyzer.duration_seconds)
                    message += f"Peak Density: {len(peaks) / duration_val:.1f} peaks/second\n"

                self._show_info_message("Analysis Complete", message)
                self.logger.info(f"Analysis completed successfully: {len(peaks)} peaks detected with timestamps saved")

            else:
                self._force_peak_display()
                self._show_error_message("Analysis Error",
                                         "Failed to analyze the audio file. Please check the file format and try again.")
                self.logger.error("Analysis failed")

        # Start the analysis process
        try:
            self.analyzer.process_waveform(analysis_complete)
        except Exception as e:
            self.logger.error(f"Error starting analysis: {e}")
            analysis_complete(False)

    def _on_analysis_progress(self, progress: int):
        """Handle analysis progress updates with detailed status messages."""
        if hasattr(self, 'progress_bar') and self.progress_bar.isVisible():
            self.progress_bar.setValue(progress)

            # Update status message based on progress (fallback if no detailed status)
            if progress <= 10:
                self.progress_bar.setFormat("Analyzing noise characteristics... %p%")
            elif progress <= 20:
                self.progress_bar.setFormat("Preprocessing signal... %p%")
            elif progress <= 40:
                self.progress_bar.setFormat("Detecting onset candidates... %p%")
            elif progress <= 60:
                self.progress_bar.setFormat("Refining and filtering peaks... %p%")
            elif progress <= 80:
                self.progress_bar.setFormat("Classifying drum hits... %p%")
            elif progress <= 90:
                self.progress_bar.setFormat("Filtering by amplitude segments... %p%")
            elif progress < 100:
                self.progress_bar.setFormat("Final validation and sorting... %p%")
            else:
                self.progress_bar.setFormat("Analysis complete! %p%")
                # Show completion dialog when analysis is finished
                if progress == 100:
                    QTimer.singleShot(1000, self._show_completion_dialog)  # Delay to show 100% briefly

    def _on_analysis_status(self, status_message: str):
        """Handle detailed analysis status updates."""
        if hasattr(self, 'progress_bar') and self.progress_bar.isVisible():
            # Update progress bar format with detailed status
            current_progress = self.progress_bar.value()
            self.progress_bar.setFormat(f"{status_message} %p%")

        # Log the status for debugging
        self.logger.info(f"Analysis status: {status_message}")

    def _on_analysis_metrics(self, metrics: dict):
        """Handle real-time analysis metrics updates."""
        try:
            # Extract metrics
            stage = metrics.get('stage', 'unknown')
            overall_progress = metrics.get('overall_progress', 0)
            eta = metrics.get('eta', 0)
            peak_count = metrics.get('peak_count', 0)
            processing_speed = metrics.get('samples_per_second', 0)

            # Update progress bar with ETA if available
            if hasattr(self, 'progress_bar') and self.progress_bar.isVisible() and eta > 0:
                eta_str = f"{int(eta)}s" if eta < 60 else f"{int(eta // 60)}m{int(eta % 60)}s"
                current_format = self.progress_bar.format()
                if "ETA:" not in current_format:
                    enhanced_format = f"{current_format.replace(' %p%', '')} - ETA: {eta_str} %p%"
                    self.progress_bar.setFormat(enhanced_format)

            # Log detailed metrics
            memory_mb = metrics.get('memory_mb', 0)
            memory_percent = metrics.get('memory_percent', 0)

            if peak_count > 0:
                self.logger.info(f"Analysis metrics - Stage: {stage}, Progress: {overall_progress}%, "
                                 f"Peaks: {peak_count}, Speed: {processing_speed:,.0f} samples/s, ETA: {eta:.1f}s, "
                                 f"Memory: {memory_mb:.1f}MB ({memory_percent:.1f}%)")

        except Exception as e:
            self.logger.error(f"Error handling analysis metrics: {e}")

    def _show_completion_dialog(self):
        """Show comprehensive analysis completion dialog with summary."""
        try:
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QGroupBox
            from PySide6.QtCore import Qt
            from PySide6.QtGui import QFont

            if not hasattr(self, 'analyzer') or not self.analyzer:
                return

            # Create completion dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("🎉 Analysis Complete!")
            dialog.setModal(True)
            dialog.resize(600, 500)

            layout = QVBoxLayout(dialog)

            # Title
            title_label = QLabel("🎵 Drum Track Analysis Complete!")
            title_font = QFont()
            title_font.setPointSize(16)
            title_font.setBold(True)
            title_label.setFont(title_font)
            title_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(title_label)

            # Summary statistics
            stats_group = QGroupBox("📊 Analysis Summary")
            stats_layout = QVBoxLayout(stats_group)

            # Get analysis results
            peaks = self.analyzer.get_peak_data() if hasattr(self.analyzer, 'get_peak_data') else []
            total_peaks = len(peaks)

            # File information
            file_info = f"📁 File: {self.music_file_info.get('name', 'Unknown')}\n"
            if hasattr(self.analyzer, 'duration_seconds'):
                duration_val = clean_data_for_json(self.analyzer.duration_seconds)
                file_info += f"⏱️ Duration: {duration_val:.1f} seconds\n"
            if hasattr(self.analyzer, 'sample_rate'):
                sample_rate_val = clean_data_for_json(self.analyzer.sample_rate)
                file_info += f"📊 Sample Rate: {sample_rate_val:,} Hz\n"

            # Peak statistics
            peak_info = f"🥁 Total Peaks Detected: {total_peaks}\n"
            if total_peaks > 0:
                if hasattr(self.analyzer, 'duration_seconds') and self.analyzer.duration_seconds > 0:
                    duration_val = clean_data_for_json(self.analyzer.duration_seconds)
                    peak_density = total_peaks / duration_val if duration_val > 0 else 0
                    peak_info += f"📈 Peak Density: {peak_density:.1f} peaks/second\n"

                # Drum type distribution (if classification was enabled)
                if hasattr(self.analyzer, 'config') and self.analyzer.config.get('drum_classification', False):
                    drum_types = {}
                    for peak in peaks:
                        if isinstance(peak, dict) and 'drum_type' in peak:
                            drum_type = peak['drum_type']
                            drum_types[drum_type] = drum_types.get(drum_type, 0) + 1

                    if drum_types:
                        peak_info += "\n🥁 Drum Type Distribution:\n"
                        for drum_type, count in sorted(drum_types.items()):
                            percentage = (count / total_peaks) * 100
                            peak_info += f"   {drum_type}: {count} ({percentage:.1f}%)\n"

            # Processing performance
            performance_info = ""
            if hasattr(self.analyzer, 'progress_tracker'):
                tracker = self.analyzer.progress_tracker
                if tracker.get('start_time'):
                    total_time = time.time() - tracker['start_time']
                    performance_info = f"\n⚡ Processing Performance:\n"
                    performance_info += f"   Total Time: {total_time:.1f} seconds\n"

                    if tracker.get('processing_speed', 0) > 0:
                        speed = tracker['processing_speed']
                        performance_info += f"   Processing Speed: {speed:,.0f} samples/second\n"

                    # Stage timing breakdown
                    stage_times = tracker.get('stage_times', {})
                    if stage_times:
                        performance_info += f"   Stage Breakdown:\n"
                        for stage, duration in stage_times.items():
                            if isinstance(duration, (int, float)) and duration > 0:
                                performance_info += f"     {stage}: {duration:.1f}s\n"

            # Quality metrics
            quality_info = ""
            if hasattr(self.analyzer, 'noise_floor') and hasattr(self.analyzer, 'dynamic_range'):
                quality_info = f"\n🔍 Signal Quality:\n"
                quality_info += f"   Noise Floor: {self.analyzer.noise_floor:.6f}\n"
                quality_info += f"   Dynamic Range: {self.analyzer.dynamic_range:.1f} dB\n"

            # Combine all information
            summary_text = file_info + peak_info + performance_info + quality_info

            summary_label = QLabel(summary_text)
            summary_label.setWordWrap(True)
            summary_label.setAlignment(Qt.AlignLeft)
            stats_layout.addWidget(summary_label)
            layout.addWidget(stats_group)

            # Recommendations
            if total_peaks > 0:
                recommendations_group = QGroupBox("💡 Recommendations")
                recommendations_layout = QVBoxLayout(recommendations_group)

                recommendations = []

                if total_peaks < 10:
                    recommendations.append("• Consider adjusting sensitivity settings for more peak detection")
                elif total_peaks > 1000:
                    recommendations.append(
                        "• Large number of peaks detected - consider filtering or adjusting thresholds")

                if hasattr(self.analyzer, 'dynamic_range') and self.analyzer.dynamic_range < 30:
                    recommendations.append("• Low dynamic range detected - consider audio quality improvement")

                if peak_density > 20:
                    recommendations.append("• High peak density - verify detection accuracy")
                elif peak_density < 1:
                    recommendations.append("• Low peak density - check if all drum hits were detected")

                if not recommendations:
                    recommendations.append("• Analysis results look good! Ready for LED show generation.")

                rec_text = "\n".join(recommendations)
                rec_label = QLabel(rec_text)
                rec_label.setWordWrap(True)
                recommendations_layout.addWidget(rec_label)
                layout.addWidget(recommendations_group)

            # Buttons
            button_layout = QHBoxLayout()

            # Generate Show button
            generate_button = QPushButton("🎆 Generate LED Show")
            generate_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            generate_button.clicked.connect(lambda: (dialog.accept(), self._generate_led_show()))

            # Close button
            close_button = QPushButton("Close")
            close_button.clicked.connect(dialog.accept)

            button_layout.addWidget(generate_button)
            button_layout.addWidget(close_button)
            layout.addLayout(button_layout)

            # Show dialog
            dialog.exec()

        except Exception as e:
            self.logger.error(f"Error showing completion dialog: {e}")

    def _generate_led_show(self):
        """Generate LED show from analysis results."""
        try:
            # This would trigger the LED show generation process
            # Implementation depends on the existing LED show generation logic
            self.logger.info("LED show generation requested from completion dialog")

            # Emit signal if available
            if hasattr(self, 'show_generation_ready'):
                peaks = self.analyzer.get_peak_data() if hasattr(self.analyzer, 'get_peak_data') else []
                # Clean the data before emitting to prevent serialization issues
                clean_peaks = clean_data_for_json(peaks) if peaks else []
                # Only send serializable analyzer data, not the full analyzer object
                analyzer_info = clean_data_for_json({
                    'duration_seconds': getattr(self.analyzer, 'duration_seconds', 0),
                    'sample_rate': getattr(self.analyzer, 'sample_rate', 0),
                    'is_analyzed': getattr(self.analyzer, 'is_analyzed', False),
                    'filename': str(getattr(self.analyzer, 'filename', '')),
                    'peak_count': len(peaks) if peaks else 0
                })
                self.show_generation_ready.emit({'peaks': clean_peaks, 'analyzer': analyzer_info})

        except Exception as e:
            self.logger.error(f"Error generating LED show: {e}")

    def _save_timestamp_data(self, peaks):
        """Save timestamp data for other files to use."""
        try:
            if not peaks:
                return

            # Get detailed timestamp data
            timestamp_data = {
                'file_info': {
                    'filename': str(self.music_file_info.get('filename', 'unknown')),
                    'path': str(self.music_file_info.get('path', '')),
                    'duration_seconds': clean_data_for_json(self.analyzer.duration_seconds),
                    'sample_rate': clean_data_for_json(self.analyzer.sample_rate)
                },
                'analysis_info': {
                    'total_peaks': len(peaks),
                    'analysis_time': clean_data_for_json(time.time()),
                    'target_segments': clean_data_for_json(self.analyzer.config.get('target_segments', [])),
                    'detection_methods': clean_data_for_json(self.analyzer.config.get('onset_methods', []))
                },
                'peaks': []
            }

            # Add detailed peak information with timestamps
            for i, peak in enumerate(peaks):
                # DOUBLE SHOT FIX: Check if this peak is marked as a double shot
                is_double_shot = False
                if hasattr(self.waveform_view, 'double_shot_peaks'):
                    # Check if this is a manual peak or detected peak
                    if hasattr(peak, 'is_manual') and peak.is_manual:
                        # For manual peaks, check using the "m{time}" format
                        manual_peak_id = f"m{peak.time}"
                        is_double_shot = manual_peak_id in self.waveform_view.double_shot_peaks
                    else:
                        # For detected peaks, check using the time value
                        is_double_shot = peak.time in self.waveform_view.double_shot_peaks

                peak_info = {
                    'index': i,
                    'time_seconds': clean_data_for_json(peak.time),
                    'time_milliseconds': clean_data_for_json(peak.time * 1000),
                    'time_samples': int(clean_data_for_json(peak.time * self.analyzer.sample_rate)),
                    'time_formatted': f"{int(clean_data_for_json(peak.time) // 60):02d}:{clean_data_for_json(peak.time) % 60:06.3f}",
                    'amplitude': clean_data_for_json(peak.amplitude),
                    'frequency': clean_data_for_json(peak.frequency),
                    'drum_type': str(peak.drum_type),
                    'confidence': clean_data_for_json(peak.confidence),
                    'segment': clean_data_for_json(peak.segment),
                    'spectral_features': clean_data_for_json(peak.spectral_features),
                    'is_double_shot': is_double_shot  # Add double shot flag
                }
                timestamp_data['peaks'].append(peak_info)

            # Store in analyzer for access by other components
            self.analyzer.timestamp_data = timestamp_data

            # Also store globally for access by other dialogs/components
            if not hasattr(self, '_global_timestamp_storage'):
                self._global_timestamp_storage = {}

            file_key = self.music_file_info.get('path', 'unknown')
            self._global_timestamp_storage[file_key] = timestamp_data

            self.logger.info(f"Timestamp data saved for {len(peaks)} peaks")

        except Exception as e:
            self.logger.error(f"Error saving timestamp data: {e}")

    def get_timestamp_data(self):
        """Get the saved timestamp data."""
        if hasattr(self.analyzer, 'timestamp_data'):
            return self.analyzer.timestamp_data
        return None

    def _style_tab_widget(self, tab_widget: QTabWidget) -> None:
        """
        Apply custom styling to the tab widget

        Args:
            tab_widget: The tab widget to style
        """
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444;
                border-radius: 3px;
                background: #2d2d2d;
            }
            QTabBar::tab {
                background: #2d2d2d;
                color: #ddd;
                padding: 4px 12px;
                border: 1px solid #444;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background: #3d3d3d;
                border-bottom: none;
            }
            QTabBar::tab:hover {
                background: #353535;
            }
        """)

    def _create_playback_group(self) -> QGroupBox:
        """
        Create the playback controls group

        Returns:
            QGroupBox containing playback controls
        """
        playback_group = QGroupBox("Audio Playback Controls")
        playback_layout = QVBoxLayout(playback_group)

        # Transport controls
        transport_layout = QHBoxLayout()

        # Play button
        self.play_btn = QPushButton("Play")
        self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        transport_layout.addWidget(self.play_btn)

        # Pause button
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.pause_btn.setEnabled(False)
        transport_layout.addWidget(self.pause_btn)

        # Stop button
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stop_btn.setEnabled(False)
        transport_layout.addWidget(self.stop_btn)

        playback_layout.addLayout(transport_layout)

        # Zoom controls moved to Waveform Controls tab
        # zoom_layout = QHBoxLayout()
        # self.zoom_out_btn = QPushButton("Zoom Out")
        # self.zoom_in_btn = QPushButton("Zoom In")
        # self.zoom_label = QLabel("1.0x")
        # self.zoom_slider = QSlider(Qt.Horizontal)
        # self.reset_zoom_btn = QPushButton("Reset Zoom")

        # ENHANCEMENT: Volume controls
        volume_layout = QHBoxLayout()

        volume_layout.addWidget(QLabel("Volume:"))

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)  # Default 70% volume
        self.volume_slider.setToolTip("Adjust playback volume")
        volume_layout.addWidget(self.volume_slider)

        self.volume_label = QLabel("70%")
        self.volume_label.setMinimumWidth(40)
        self.volume_label.setAlignment(Qt.AlignCenter)
        self.volume_label.setStyleSheet("font-weight: bold; color: #2980b9;")
        volume_layout.addWidget(self.volume_label)

        playback_layout.addLayout(volume_layout)

        # ENHANCEMENT: Playback speed controls
        speed_layout = QHBoxLayout()

        speed_layout.addWidget(QLabel("Speed:"))

        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.05x", "0.1x", "0.25x", "0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"])
        self.speed_combo.setCurrentText("1.0x")
        self.speed_combo.setToolTip("Adjust playback speed")
        speed_layout.addWidget(self.speed_combo)

        playback_layout.addLayout(speed_layout)

        return playback_group

    # NOTE: _create_beat_detection_group method removed - functionality moved to WaveformControlsPanel

    def _init_dialog_buttons(self, layout: QVBoxLayout) -> None:
        """
        Initialize the dialog buttons

        Args:
            layout: Parent layout to add buttons to
        """
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self._close_dialog)
        layout.addWidget(button_box)

    def _setup_shortcuts(self) -> None:
        """Set up keyboard shortcuts for the dialog"""
        # Zoom shortcuts
        zoom_in = QShortcut(QKeySequence(Qt.Key_Plus), self)
        zoom_in.activated.connect(self._on_zoom_in)

        zoom_out = QShortcut(QKeySequence(Qt.Key_Minus), self)
        zoom_out.activated.connect(self._on_zoom_out)

        reset_zoom = QShortcut(QKeySequence(Qt.Key_0), self)
        reset_zoom.activated.connect(self._on_reset_zoom)

        # Navigation shortcuts
        home = QShortcut(QKeySequence(Qt.Key_Home), self)
        home.activated.connect(lambda: self.waveform_view.set_position(0.0))

        end = QShortcut(QKeySequence(Qt.Key_End), self)
        end.activated.connect(lambda: self.waveform_view.set_position(1.0))

        # Playback shortcuts
        play = QShortcut(QKeySequence(Qt.Key_Space), self)
        play.activated.connect(self._on_play)

        pause = QShortcut(QKeySequence(Qt.Key_P), self)
        pause.activated.connect(self._on_pause)

        stop = QShortcut(QKeySequence(Qt.Key_S), self)
        stop.activated.connect(self._on_stop)

    def resize_to_screen(self) -> None:
        """Resize dialog to fit screen with comfortable margins"""
        from PySide6.QtWidgets import QApplication

        # Get primary screen
        screen = QApplication.primaryScreen()
        if not screen:
            screen = QApplication.screens()[0] if QApplication.screens() else None

        if screen:
            # Get available geometry (excludes menu bar, dock, etc.)
            geometry = screen.availableGeometry()

            # Calculate maximum usable dimensions with margins
            # Leave 40px margin on each side for better fit
            max_width = geometry.width() - 80
            max_height = geometry.height() - 80

            # Use percentage-based sizing but cap at max dimensions
            # This ensures dialog never exceeds screen bounds
            width = min(int(geometry.width() * 0.85), max_width)
            height = min(int(geometry.height() * 0.80), max_height)

            # For smaller screens (laptops), use even more conservative sizing
            if geometry.width() < 1440:  # Typical 13" laptop
                width = min(int(geometry.width() * 0.75), max_width)
                height = min(int(geometry.height() * 0.75), max_height)

            # Center the dialog
            x = geometry.x() + (geometry.width() - width) // 2
            y = geometry.y() + (geometry.height() - height) // 2

            self.setGeometry(x, y, width, height)

            # Set minimum size to ensure usability
            self.setMinimumSize(800, 600)
        else:
            # Fallback size if screen information is not available
            self.resize(900, 650)
            self.setMinimumSize(800, 600)

    def _connect_signals(self) -> None:
        """Connect all signals and slots"""
        # Time slider connections
        self.time_slider.valueChanged.connect(self._on_time_slider_changed)

        # Zoom control connections moved to Waveform Controls tab
        # self.zoom_in_btn.clicked.connect(self._on_zoom_in)
        # self.zoom_out_btn.clicked.connect(self._on_zoom_out)
        # self.reset_zoom_btn.clicked.connect(self._on_reset_zoom)
        # self.zoom_slider.valueChanged.connect(self._on_zoom_slider_changed)

        # Playback control connections
        self.play_btn.clicked.connect(self._on_play)
        self.pause_btn.clicked.connect(self._on_pause)
        self.stop_btn.clicked.connect(self._on_stop)

        # Media player connections
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.player.positionChanged.connect(self._on_player_position_changed)

        # ENHANCEMENT: Volume and speed control connections
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        self.speed_combo.currentTextChanged.connect(self._on_speed_changed)

        # Waveform view connections
        self.waveform_view.zoom_changed.connect(self._on_view_zoom_changed)
        self.waveform_view.position_changed.connect(self._on_view_position_changed)

        # ENHANCEMENT: Connect peak selection changes to update counters
        if hasattr(self.waveform_view, 'peak_selection_changed'):
            self.waveform_view.peak_selection_changed.connect(self._force_peak_display)

        # Professional waveform controls connections
        if hasattr(self, 'waveform_controls_panel'):
            self.waveform_controls_panel.render_mode_changed.connect(self.waveform_view.set_render_mode)
            self.waveform_controls_panel.color_scheme_changed.connect(self.waveform_view.set_color_scheme)
            self.waveform_controls_panel.smoothing_changed.connect(self.waveform_view.set_smoothing_factor)
            self.waveform_controls_panel.dynamic_range_changed.connect(self.waveform_view.set_dynamic_range_db)
            self.waveform_controls_panel.frequency_bands_changed.connect(self.waveform_view.set_frequency_bands)
            # Professional rendering is always enabled - no toggle needed

            # Connect beat detection signals
            self.waveform_controls_panel.analyze_file_requested.connect(self._on_analyze_file)
            self.waveform_controls_panel.manual_peak_mode_changed.connect(self._on_manual_peak_mode_changed)
            self.waveform_controls_panel.double_shot_mode_changed.connect(self._on_double_shot_mode_changed)

            # Connect state management signals
            self.waveform_controls_panel.save_state_requested.connect(self.save_waveform_state)
            self.waveform_controls_panel.load_state_requested.connect(self.load_waveform_state)

            # Connect zoom control signals
            self.waveform_controls_panel.zoom_changed.connect(self._on_zoom_slider_changed)
            self.waveform_controls_panel.zoom_reset_requested.connect(self._on_reset_zoom)

            # CRITICAL FIX: Emit initial control values to ensure waveform displays correctly on load
            # This ensures the waveform view receives the default settings (Frequency Bands, 0.00 smoothing, 40dB range)
            QTimer.singleShot(100, self.waveform_controls_panel._emit_all_current_values)

    def load_waveform_data(self) -> None:
        """Load and process the waveform data"""
        # Check if we're already processing
        if self.is_processing:
            self.logger.info("Already processing waveform data, skipping duplicate request")
            return

        # Check if analyzer is set
        if not self.analyzer:
            self.logger.error("Analyzer not set, cannot load waveform data")
            return

        if not self.music_file_info or 'path' not in self.music_file_info:
            self.logger.error("No valid music file information provided")
            return

        print(f"🔊 load_waveform_data: Using file path from music_file_info: {self.music_file_info['path']}")

        # Print additional info about the music_file_info dictionary
        print(f"🔊 load_waveform_data: music_file_info keys: {self.music_file_info.keys()}")
        if 'is_separated' in self.music_file_info:
            print(f"🔊 load_waveform_data: is_separated: {self.music_file_info['is_separated']}")
        if 'is_drum_stem' in self.music_file_info:
            print(f"🔊 load_waveform_data: is_drum_stem: {self.music_file_info['is_drum_stem']}")
        if 'original_file' in self.music_file_info:
            print(f"🔊 load_waveform_data: original_file: {self.music_file_info['original_file']}")

        file_path = Path(self.music_file_info['path'])
        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            return

        # File size validation
        try:
            file_size = file_path.stat().st_size
            max_size = 500 * 1024 * 1024
            if file_size > max_size:
                self.logger.warning("Large file detected")
        except:
            pass

        # Show loading state
        self.progress_bar.setVisible(True)
        self.title_label.setText(f"Loading: {file_path.name}...")
        self.is_processing = True

        # Start the peak check timer with timeout tracking
        self._peak_check_start_time = datetime.now()
        self._peak_check_timeout_warnings = 0
        self.peak_check_timer.start()
        self.logger.info("Peak check timer started with timeout safety mechanism")

        try:
            # Check if the analyzer already has this file loaded
            if hasattr(self.analyzer, 'file_path') and self.analyzer.file_path == file_path:
                self.logger.info("File already loaded in analyzer, skipping load_file")
                # Check if waveform_data is available
                if hasattr(self.analyzer, 'waveform_data') and self.analyzer.waveform_data is not None:
                    # If the file is loaded but not analyzed, process it
                    if not self.analyzer.is_analyzed:
                        self.analyzer.process_waveform(self._on_waveform_loaded_safe)
                    else:
                        # File is already loaded and analyzed, just update the UI
                        self._on_waveform_loaded_safe(True)
                else:
                    # Waveform data is not available, need to process the file
                    self.logger.info("File loaded in analyzer but waveform_data is None, processing waveform")
                    # Reset is_analyzed flag to ensure proper processing
                    self.analyzer.is_analyzed = False
                    self.analyzer.process_waveform(self._on_waveform_loaded_safe)
                return

            # Load the file in the analyzer
            if not self.analyzer.load_file(file_path):
                self.logger.error(f"Could not load file: {file_path}")
                self.progress_bar.setVisible(False)
                self.is_processing = False
                return

            # For comprehensive analyzer, just load the waveform data without processing
            # The user will click ANALYZE FILE button to start the actual analysis
            if hasattr(self.analyzer, 'waveform_data') and self.analyzer.waveform_data is not None:
                self.logger.info("Waveform data loaded, displaying without analysis")
                self._on_waveform_loaded_safe(True)
            else:
                self.logger.error("Failed to load waveform data")
                self._on_waveform_loaded_safe(False)

        except Exception as e:
            self.logger.error(f"Error loading waveform data: {str(e)}")
            self.progress_bar.setVisible(False)
            self.is_processing = False

    def _on_waveform_loaded_safe(self, success: bool) -> None:
        """
        Thread-safe wrapper for waveform loading completion

        Args:
            success: Whether the waveform was loaded successfully
        """
        # Use QMetaObject to safely call from worker thread
        QMetaObject.invokeMethod(
            self,
            "_on_waveform_loaded",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(bool, success)
        )

    @Slot(bool)
    def _on_waveform_loaded(self, success: bool) -> None:
        """Handle waveform loading completion and set spinbox limits"""
        self.is_processing = False
        self.progress_bar.setVisible(False)

        if not success:
            self.logger.error("Could not process waveform data")
            # Stop the peak check timer if it's running
            if self.peak_check_timer.isActive():
                self.logger.info("Stopping peak check timer due to waveform processing failure")
                self.peak_check_timer.stop()
            return

        try:
            # Update title
            if self.music_file_info:
                title = f"Waveform: {self.music_file_info['filename']} - {self.music_file_info['duration']}"
                self.title_label.setText(title)

            # Create analysis info
            analysis_info = self._create_analysis_info()

            if self.analyzer:
                # DON'T force analyzer as analyzed - let multi-phase system handle completion
                if not self.analyzer.is_analyzed:
                    self.logger.info(
                        "Analyzer not marked as analyzed - multi-phase system will handle completion when ready")
                    # self.analyzer.is_analyzed = True  # REMOVED - causes premature completion

                # Check if waveform_data is available
                if hasattr(self.analyzer, 'waveform_data') and self.analyzer.has_waveform_data():
                    # For comprehensive analyzer, don't auto-analyze - wait for user to click ANALYZE FILE
                    self.logger.info("Waveform data loaded - waiting for user to click ANALYZE FILE button")
                    # Set initial peak count to 0 since no analysis has been done yet
                    self._force_peak_display()
                else:
                    self.logger.warning("Cannot display waveform: waveform_data is None")

                # Make sure the waveform view has the analyzer, but avoid unnecessary reprocessing
                # by checking if the analyzer is already set in the waveform view
                if not hasattr(self.waveform_view, 'analyzer') or self.waveform_view.analyzer is not self.analyzer:
                    self.waveform_view.set_analyzer(self.analyzer)

                # Initialize UI state
                self._init_playback_state()
                self._enable_controls()
                self._update_duration_display()

                # Set up media player
                print(
                    f"🔊 _on_waveform_loaded: About to set up media player with music_file_info path: {self.music_file_info['path'] if self.music_file_info and 'path' in self.music_file_info else 'No path'}")
                self._setup_media_player()

                # Force initial peak display
                self._force_peak_display()

                # CRITICAL FIX: Apply initial waveform control settings after waveform is loaded
                # This ensures the visual display matches the default control values
                if hasattr(self, 'waveform_controls_panel'):
                    QTimer.singleShot(200, self.waveform_controls_panel._emit_all_current_values)

                # For comprehensive analyzer, don't check peaks until analysis is done
                if self.analyzer.is_analyzed:
                    # Get peaks using the proper API method
                    peaks = self.analyzer.get_peak_data()

                    # Check if peaks were found, if not, stop the timer
                    if not peaks:
                        if self.peak_check_timer.isActive():
                            self.logger.info("No peaks found after analysis, stopping peak check timer")
                            self.peak_check_timer.stop()
                            self._peak_check_start_time = None  # Reset timeout tracking
                            self._force_peak_display()
                else:
                    # No analysis done yet - peaks will be shown after ANALYZE FILE is clicked
                    self._force_peak_display()

                # Emit ready signal
                self.show_generation_ready.emit(clean_data_for_json(analysis_info))

                # Force an immediate update of the view
                self.waveform_view.update()
            else:
                self.logger.error("No analyzer available in _on_waveform_loaded")
        except Exception as e:
            self.logger.error(f"Error in waveform loading completion: {str(e)}", exc_info=True)
            # ENHANCEMENT: Show user-friendly error message
            self._show_error_message("Processing Error", f"Error processing audio file:\n{str(e)}")
            # Stop the peak check timer if it's running
            if self.peak_check_timer.isActive():
                self.logger.info("Stopping peak check timer due to exception in waveform loading completion")
                self.peak_check_timer.stop()
                self._peak_check_start_time = None  # Reset timeout tracking

    def _create_analysis_info(self) -> dict:
        """
        Create analysis information dictionary

        Returns:
            Dictionary containing analysis information
        """
        info = dict(self.music_file_info)

        if hasattr(self.analyzer, 'duration_seconds'):
            info['duration_seconds'] = self.analyzer.duration_seconds

        return info

    def _init_playback_state(self) -> None:
        """Initialize playback state and position displays"""
        self._update_position_display(0.0)
        self.time_slider.setValue(0)
        self.time_slider.setRange(0, 1000)

    def _enable_controls(self) -> None:
        """Enable all UI controls"""
        # Enable legacy zoom controls (if they exist)
        if hasattr(self, 'zoom_in_btn'):
            self.zoom_in_btn.setEnabled(True)
        if hasattr(self, 'zoom_out_btn'):
            self.zoom_out_btn.setEnabled(True)
        if hasattr(self, 'reset_zoom_btn'):
            self.reset_zoom_btn.setEnabled(True)
        if hasattr(self, 'zoom_slider'):
            self.zoom_slider.setEnabled(True)

        # Enable controls panel zoom controls
        if hasattr(self, 'waveform_controls_panel') and hasattr(self.waveform_controls_panel,
                                                                'set_zoom_controls_enabled'):
            self.waveform_controls_panel.set_zoom_controls_enabled(True)

        self.play_btn.setEnabled(True)

    def _setup_media_player(self) -> None:
        """Set up the media player with the current file"""
        if not self.music_file_info or 'path' not in self.music_file_info:
            return

        # Use the path directly from music_file_info - this ensures we play the correct file
        # (drum stem or original file)
        file_path = Path(self.music_file_info['path'])
        print(f"🔊 _setup_media_player: Setting media source to {file_path}")

        # Print additional info about the music_file_info dictionary
        print(f"🔊 _setup_media_player: music_file_info keys: {self.music_file_info.keys()}")
        if 'is_separated' in self.music_file_info:
            print(f"🔊 _setup_media_player: is_separated: {self.music_file_info['is_separated']}")
        if 'is_drum_stem' in self.music_file_info:
            print(f"🔊 _setup_media_player: is_drum_stem: {self.music_file_info['is_drum_stem']}")
        if 'original_file' in self.music_file_info:
            print(f"🔊 _setup_media_player: original_file: {self.music_file_info['original_file']}")

        # Verify that the file exists
        if not file_path.exists():
            # If the file doesn't exist but we have an original_file, check if that exists
            if 'original_file' in self.music_file_info and Path(self.music_file_info['original_file']).exists():
                print(f"🔊 _setup_media_player: File not found, but original_file exists. Using original_file instead.")
                file_path = Path(self.music_file_info['original_file'])
            else:
                print(f"🔊 _setup_media_player: File not found and no original_file available.")
                return

        # Double-check that we're using the correct file for playback
        # If this is a separated drum stem, make sure we're using the drum stem file
        if ('is_separated' in self.music_file_info and self.music_file_info['is_separated']) or \
                ('is_drum_stem' in self.music_file_info and self.music_file_info['is_drum_stem']):
            print(
                f"🔊 _setup_media_player: This is a separated drum stem, ensuring we use the correct file for playback")
            # Make sure file_path is the path from music_file_info, not the original file
            file_path = Path(self.music_file_info['path'])
            print(f"🔊 _setup_media_player: Using drum stem file path: {file_path}")
            if not file_path.exists():
                print(f"🔊 _setup_media_player: Drum stem file not found.")
                return

        if file_path.exists():
            self.player.setSource(QUrl.fromLocalFile(str(file_path)))
            self.audio_output.setVolume(1.0)
            print(f"🔊 _setup_media_player: Media source set successfully")

    def _force_peak_display(self) -> None:
        """ENHANCED: Force update of peak detection display with separate counters"""
        if not self.analyzer:
            self._update_all_peak_counters(0, 0)
            return

        # Check if waveform data is available
        if not self.analyzer.has_waveform_data():
            self._update_all_peak_counters(0, 0, status="Load file first")
            return

        # Get detected peaks count (excluding hidden ones)
        detected_count = 0
        if hasattr(self.waveform_view, 'get_detected_peak_count'):
            detected_count = self.waveform_view.get_detected_peak_count()
        else:
            # Fallback to analyzer data
            detected_peaks = self.analyzer.get_peak_data()
            detected_count = len(detected_peaks)

        # Get custom/manual peaks count
        custom_count = 0
        if hasattr(self.waveform_view, 'get_manual_peak_count'):
            custom_count = self.waveform_view.get_manual_peak_count()
        elif hasattr(self.waveform_view, 'manual_peaks'):
            custom_count = len(self.waveform_view.manual_peaks)

        # Update all counters
        if self.analyzer.is_analyzed:
            self._update_all_peak_counters(detected_count, custom_count)
        else:
            self._update_all_peak_counters(detected_count, custom_count, status="Click ANALYZE FILE for more")

    def _update_all_peak_counters(self, detected_count: int, custom_count: int, status: str = None):
        """
        ENHANCEMENT: Update peak counter displays

        Args:
            detected_count: Number of detected peaks
            custom_count: Number of custom/manual peaks
            status: Optional status message (unused now)
        """
        # Update detected peaks counter
        if hasattr(self, 'detected_peak_count'):
            self.detected_peak_count.setText(str(detected_count))

        # Update custom peaks counter
        if hasattr(self, 'custom_peak_count'):
            self.custom_peak_count.setText(str(custom_count))

        # Update total peaks counter
        total_count = detected_count + custom_count
        if hasattr(self, 'total_peak_count'):
            self.total_peak_count.setText(str(total_count))
        self.logger.info(
            f"Updated peak display: {total_count} total peaks ({detected_count} detected + {custom_count} custom)")

        # Update controls panel peak counters
        if hasattr(self, 'waveform_controls_panel') and hasattr(self.waveform_controls_panel, 'update_peak_counts'):
            self.waveform_controls_panel.update_peak_counts(detected_count, custom_count, total_count)

        # Stop the update timer
        if self.peak_check_timer.isActive():
            self.peak_check_timer.stop()

        # Update generator peak counts if available
        if hasattr(self, 'musical_generator'):
            print(f"🔧 Updating generator peak counts and ensuring analyzer is set")
            # Make sure analyzer is set in generator
            if self.analyzer and not self.musical_generator.analyzer:
                print(f"🔧 Generator missing analyzer, setting it now: {self.analyzer}")
                self.musical_generator.set_analyzer(self.analyzer)
            self.musical_generator.update_peak_counts()

    def save_waveform_state(self, file_path: str = None) -> bool:
        """
        Save the current waveform analysis state including peaks and generator settings

        Args:
            file_path: Optional file path to save to

        Returns:
            bool: True if save was successful
        """
        try:
            from datetime import datetime
            from PySide6.QtWidgets import QFileDialog
            from utils.json_utils import safe_json_dumps

            # Get file path if not provided
            if not file_path:
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save Waveform State",
                    f"waveform_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "JSON Files (*.json);;All Files (*)"
                )

                if not file_path:
                    return False

            # Collect comprehensive state data
            state_data = {
                'version': '1.0',
                'timestamp': datetime.now().isoformat(),
                'file_info': self.music_file_info.copy() if self.music_file_info else {},
                'analyzer_state': self._collect_analyzer_state(),
                'waveform_view_state': self._collect_waveform_view_state(),
                'generator_state': self._collect_generator_state(),
                'dialog_state': self._collect_dialog_state()
            }

            print(f"🔧 Saving state data with keys: {list(state_data.keys())}")

            # Use the safe JSON serialization utility
            json_string = safe_json_dumps(state_data)

            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_string)

            print(f"🔧 State saved successfully to {file_path}")
            self.logger.info(f"Waveform state saved to {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving waveform state: {e}")
            print(f"🔧 Save error: {e}")
            return False

    def load_waveform_state(self, file_path: str = None) -> bool:
        """
        Load a previously saved waveform analysis state

        Args:
            file_path: Optional file path to load from

        Returns:
            bool: True if load was successful
        """
        try:
            from PySide6.QtWidgets import QFileDialog, QMessageBox
            from utils.json_utils import safe_json_loads

            # Get file path if not provided
            if not file_path:
                file_path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Load Waveform State",
                    "",
                    "JSON Files (*.json);;All Files (*)"
                )

                if not file_path:
                    return False

            # Load from file with error handling
            print(f"🔧 Loading state from {file_path}")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_string = f.read()

                # Use the safe JSON deserialization utility
                state_data = safe_json_loads(json_string)
                print(f"🔧 JSON loaded successfully")

            except Exception as e:
                print(f"🔧 File read/parse error: {e}")
                QMessageBox.critical(self, "Load Error", f"Could not read or parse file:\n{str(e)}")
                return False

            # Validate state data
            if not self._validate_state_data(state_data):
                QMessageBox.warning(self, "Invalid State", "The selected file contains invalid state data.")
                return False

            # Apply loaded state
            success = self._apply_loaded_state(state_data)

            if success:
                self.logger.info(f"Waveform state loaded from {file_path}")
                print(f"🔧 State loaded successfully from {file_path}")
            else:
                self.logger.error(f"Failed to apply loaded state from {file_path}")

            return success

        except Exception as e:
            self.logger.error(f"Error loading waveform state: {e}")
            print(f"🔧 Load error: {e}")
            return False

    def _collect_analyzer_state(self) -> dict:
        """Collect analyzer state data with safe type conversion"""
        if not self.analyzer:
            return {}

        # Use clean_data_for_json to handle numpy types
        state = {
            'filename': str(getattr(self.analyzer, 'filename', '')),
            'file_path': str(getattr(self.analyzer, 'file_path', '')),
            'duration_seconds': clean_data_for_json(getattr(self.analyzer, 'duration_seconds', 0)),
            'sample_rate': clean_data_for_json(getattr(self.analyzer, 'sample_rate', 0)),
            'is_analyzed': bool(getattr(self.analyzer, 'is_analyzed', False)),
            'config': clean_data_for_json(
                getattr(self.analyzer, 'config', {}).copy() if hasattr(self.analyzer, 'config') else {})
        }

        # Save peak data if available
        if hasattr(self.analyzer, 'get_peak_data'):
            try:
                peaks = self.analyzer.get_peak_data()
                if peaks:
                    peak_data = []
                    for peak in peaks:
                        peak_info = {
                            'time': clean_data_for_json(getattr(peak, 'time', 0)),
                            'amplitude': clean_data_for_json(getattr(peak, 'amplitude', 0)),
                            'frequency': clean_data_for_json(getattr(peak, 'frequency', 0)),
                            'drum_type': str(getattr(peak, 'drum_type', '')),
                            'confidence': clean_data_for_json(getattr(peak, 'confidence', 0)),
                            'segment': clean_data_for_json(getattr(peak, 'segment', 0))
                        }
                        peak_data.append(peak_info)
                    state['detected_peaks'] = peak_data
            except Exception as e:
                self.logger.warning(f"Could not save detected peaks: {e}")

        return state

    def _collect_waveform_view_state(self) -> dict:
        """Collect waveform view state data with safe type conversion"""
        if not self.waveform_view:
            return {}

        state = {
            'zoom_factor': clean_data_for_json(getattr(self.waveform_view, 'zoom_factor', 1.0)),
            'offset': clean_data_for_json(getattr(self.waveform_view, 'offset', 0.0)),
            'manual_peak_mode': bool(getattr(self.waveform_view, 'manual_peak_mode', False)),
            'double_shot_mode': bool(getattr(self.waveform_view, 'double_shot_mode', False)),
            'show_analyzer_peaks': bool(getattr(self.waveform_view, 'show_analyzer_peaks', True)),
            'hidden_detected_peaks': list(getattr(self.waveform_view, 'hidden_detected_peaks', set())),
            'double_shot_peaks': list(getattr(self.waveform_view, 'double_shot_peaks', set()))
        }

        # Save manual peaks
        if hasattr(self.waveform_view, 'manual_peaks') and self.waveform_view.manual_peaks:
            manual_peaks = []
            for peak in self.waveform_view.manual_peaks:
                peak_info = {
                    'position': clean_data_for_json(getattr(peak, 'position', 0)),
                    'amplitude': clean_data_for_json(getattr(peak, 'amplitude', 0.5)),
                    'time': clean_data_for_json(getattr(peak, 'time', 0)),
                    'segment': clean_data_for_json(getattr(peak, 'segment', 0))
                }
                manual_peaks.append(peak_info)
            state['manual_peaks'] = manual_peaks

        return state

    def _collect_generator_state(self) -> dict:
        """Collect generator state data with safe type conversion"""
        if not hasattr(self, 'musical_generator'):
            return {}

        try:
            generator_state = self.musical_generator._collect_current_state()
            return clean_data_for_json(generator_state)
        except Exception as e:
            self.logger.warning(f"Could not collect generator state: {e}")
            return {}

    def _collect_dialog_state(self) -> dict:
        """Collect dialog-specific state data with safe type conversion"""
        state = {
            'window_geometry': {
                'x': int(self.x()),
                'y': int(self.y()),
                'width': int(self.width()),
                'height': int(self.height())
            }
        }

        # Manual peak mode state is now managed by the waveform controls panel
        # No need to save checkbox state here as it's handled by the controls panel

        return clean_data_for_json(state)

    def _validate_state_data(self, state_data: dict) -> bool:
        """Validate loaded state data"""
        required_keys = ['version', 'timestamp']

        for key in required_keys:
            if key not in state_data:
                return False

        return True

    def _apply_loaded_state(self, state_data: dict) -> bool:
        """Apply loaded state data to the dialog"""
        try:
            # Apply analyzer state
            if 'analyzer_state' in state_data and self.analyzer:
                self._apply_analyzer_state(state_data['analyzer_state'])

            # Apply waveform view state
            if 'waveform_view_state' in state_data and self.waveform_view:
                self._apply_waveform_view_state(state_data['waveform_view_state'])

            # Apply generator state
            if 'generator_state' in state_data and hasattr(self, 'musical_generator'):
                self.musical_generator._apply_loaded_state(state_data['generator_state'])

            # Apply dialog state
            if 'dialog_state' in state_data:
                self._apply_dialog_state(state_data['dialog_state'])

            # Update displays
            self._update_all_peak_counters(
                self.waveform_view.get_detected_peak_count() if self.waveform_view else 0,
                self.waveform_view.get_manual_peak_count() if self.waveform_view else 0
            )

            return True

        except Exception as e:
            self.logger.error(f"Error applying loaded state: {e}")
            return False

    def _apply_analyzer_state(self, analyzer_state: dict):
        """Apply analyzer state data"""
        if not self.analyzer:
            return

        # Apply configuration if available
        if 'config' in analyzer_state and hasattr(self.analyzer, 'config'):
            self.analyzer.config.update(analyzer_state['config'])

        # Restore detected peaks if available
        if 'detected_peaks' in analyzer_state and hasattr(self.analyzer, 'peaks'):
            from utils.audio.waveform_analyzer import Peak

            restored_peaks = []
            for peak_data in analyzer_state['detected_peaks']:
                peak = Peak(
                    time=peak_data.get('time', 0),
                    amplitude=peak_data.get('amplitude', 1.0),
                    confidence=peak_data.get('confidence', 1.0),
                    type=peak_data.get('drum_type', 'generic'),
                    frequency=peak_data.get('frequency', 0.0),
                    segment=peak_data.get('segment', 'medium')
                )
                restored_peaks.append(peak)

            self.analyzer.peaks = restored_peaks
            self.analyzer.is_analyzed = True

    def _apply_waveform_view_state(self, view_state: dict):
        """Apply waveform view state data"""
        if not self.waveform_view:
            return

        # Apply view settings
        if 'zoom_factor' in view_state:
            self.waveform_view.zoom_factor = view_state['zoom_factor']

        if 'offset' in view_state:
            self.waveform_view.offset = view_state['offset']

        if 'manual_peak_mode' in view_state:
            self.waveform_view.manual_peak_mode = view_state['manual_peak_mode']

        if 'show_analyzer_peaks' in view_state:
            self.waveform_view.show_analyzer_peaks = view_state['show_analyzer_peaks']

        if 'hidden_detected_peaks' in view_state:
            self.waveform_view.hidden_detected_peaks = set(view_state['hidden_detected_peaks'])

        if 'double_shot_mode' in view_state:
            self.waveform_view.double_shot_mode = view_state['double_shot_mode']

        if 'double_shot_peaks' in view_state:
            self.waveform_view.double_shot_peaks = set(view_state['double_shot_peaks'])

        # Restore manual peaks
        if 'manual_peaks' in view_state:
            from dataclasses import dataclass

            @dataclass
            class ManualPeak:
                position: float
                amplitude: float
                time: float = 0
                segment: int = 0

            manual_peaks = []
            for peak_data in view_state['manual_peaks']:
                peak = ManualPeak(
                    position=peak_data.get('position', 0),
                    amplitude=peak_data.get('amplitude', 0.5),
                    time=peak_data.get('time', 0),
                    segment=peak_data.get('segment', 0)
                )
                manual_peaks.append(peak)

            self.waveform_view.manual_peaks = manual_peaks

        # Update the waveform controls panel to reflect the view state
        if hasattr(self, 'waveform_controls_panel'):
            # Update manual peak checkbox if available
            if hasattr(self.waveform_controls_panel, 'manual_peak_checkbox') and 'manual_peak_mode' in view_state:
                self.waveform_controls_panel.manual_peak_checkbox.setChecked(view_state['manual_peak_mode'])

            # Update double shot checkbox if available
            if hasattr(self.waveform_controls_panel, 'double_shot_checkbox') and 'double_shot_mode' in view_state:
                self.waveform_controls_panel.double_shot_checkbox.setChecked(view_state['double_shot_mode'])

        # Update the view
        self.waveform_view.update()

    def _apply_dialog_state(self, dialog_state: dict):
        """Apply dialog state data"""
        # Apply window geometry
        if 'window_geometry' in dialog_state:
            geom = dialog_state['window_geometry']
            self.setGeometry(geom['x'], geom['y'], geom['width'], geom['height'])

            # Manual peak mode state is now managed by the waveform controls panel
            # Checkbox state restoration is handled by the controls panel
            self._peak_check_start_time = None  # Reset timeout tracking

    def _update_position_display(self, position: float) -> None:
        """
        Update position display with current time

        Args:
            position: Normalized position (0.0-1.0)
        """
        if not self.analyzer:
            self.position_label.setText("Position: 00:00.000")
            return

        time_seconds = position * self.analyzer.duration_seconds
        time_str = self._format_time(time_seconds)
        total_str = self._format_time(self.analyzer.duration_seconds)
        self.position_label.setText(f"{time_str} / {total_str}")

        # ENHANCEMENT: Color coding for time display
        progress_percent = (time_seconds / self.analyzer.duration_seconds) * 100
        if progress_percent < 25:
            color = "#3498db"  # Blue for beginning
        elif progress_percent < 75:
            color = "#f39c12"  # Orange for middle
        else:
            color = "#e74c3c"  # Red for near end

        self.position_label.setStyleSheet(f"font-weight: bold; color: {color}; font-size: 12px;")

    def _update_duration_display(self) -> None:
        """Update the duration display"""
        if not self.analyzer:
            self.duration_label.setText("Duration: 00:00.000")
            return

        duration_str = self._format_time(self.analyzer.duration_seconds)
        self.duration_label.setText(f"Total: {duration_str}")
        self.duration_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")

    def _format_time(self, seconds: float) -> str:
        """
        Format time in seconds to string

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string (MM:SS.mmm)
        """
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        ms = int((remaining_seconds % 1) * 1000)
        seconds = int(remaining_seconds)
        return f"{minutes}:{seconds:02d}.{ms:03d}"

    def _update_zoom_display(self, zoom_factor: float) -> None:
        """
        Update zoom display and slider

        Args:
            zoom_factor: Current zoom factor
        """
        # Update legacy zoom label (if it exists)
        if hasattr(self, 'zoom_label'):
            self.zoom_label.setText(f"{zoom_factor:.1f}x")

        # Update controls panel zoom display
        if hasattr(self, 'waveform_controls_panel') and hasattr(self.waveform_controls_panel, 'update_zoom_display'):
            self.waveform_controls_panel.update_zoom_display(zoom_factor)

        # Update slider without triggering signals
        if hasattr(self, 'zoom_slider'):
            self.zoom_slider.blockSignals(True)

            # Convert zoom factor to slider value (logarithmic scale)
            log_min = math.log(self.waveform_view.min_zoom)
            log_max = math.log(self.waveform_view.max_zoom)
            log_current = math.log(zoom_factor)

            slider_value = int(((log_current - log_min) / (log_max - log_min)) * 100)
            self.zoom_slider.setValue(slider_value)

            self.zoom_slider.blockSignals(False)

        # Update controls panel slider
        if hasattr(self, 'waveform_controls_panel') and hasattr(self.waveform_controls_panel, 'set_zoom_slider_value'):
            if hasattr(self.waveform_view, 'min_zoom') and hasattr(self.waveform_view, 'max_zoom'):
                log_min = math.log(self.waveform_view.min_zoom)
                log_max = math.log(self.waveform_view.max_zoom)
                log_current = math.log(zoom_factor)
                slider_value = int(((log_current - log_min) / (log_max - log_min)) * 100)
                self.waveform_controls_panel.set_zoom_slider_value(slider_value)

    def _update_peak_info_optimized(self) -> None:
        """OPTIMIZED peak info update with intelligent progress monitoring"""

        # Prevent concurrent updates
        if self._is_updating_peak_info:
            return

        self._is_updating_peak_info = True

        try:
            # Initialize timing
            current_time = datetime.now()
            if self._peak_check_start_time is None:
                self._peak_check_start_time = current_time
                self._last_progress_time = current_time
                self.logger.info("Intelligent peak monitoring started")

            elapsed_time = (current_time - self._peak_check_start_time).total_seconds()

            # Check analyzer availability
            if not self.analyzer:
                self._stop_monitoring("No analyzer available")
                return

            # INTELLIGENT PROGRESS DETECTION
            progress_info = self._detect_processing_progress()

            # Update UI with detailed progress
            self._update_progress_display(progress_info, elapsed_time)

            # SMART TIMEOUT DECISION
            if not self._should_continue_monitoring(progress_info, elapsed_time):
                self._finalize_peak_monitoring(progress_info)

        except Exception as e:
            self.logger.error(f"Error in optimized peak monitoring: {str(e)}")
            self._stop_monitoring(f"Error: {str(e)}")
        finally:
            self._is_updating_peak_info = False

    def _update_peak_info(self) -> None:
        """Legacy method - redirects to optimized version"""
        self._update_peak_info_optimized()

    def _peak_data_timeout(self):
        """Handle timeout when getting peak data takes too long with enhanced recovery"""
        self.logger.warning("Timeout while getting peak data - implementing recovery strategy")

        # ENHANCEMENT: Try to recover gracefully
        try:
            if hasattr(self, 'analyzer') and self.analyzer:
                # Check if analyzer is still responsive
                if hasattr(self.analyzer, 'is_processing_complete'):
                    processing_complete = self.analyzer.is_processing_complete()
                    self.logger.info(f"Analyzer processing complete status: {processing_complete}")

                # If analyzer seems stuck, try to reset its state
                if hasattr(self.analyzer, '_peak_detection_in_progress'):
                    if self.analyzer._peak_detection_in_progress:
                        self.logger.warning("Analyzer appears stuck in peak detection, attempting recovery")
                        # Don't directly modify analyzer state, just log the issue

        except Exception as e:
            self.logger.error(f"Error during peak data timeout recovery: {str(e)}")

        # Set empty peaks and reset state
        self._cached_peaks = []
        self._is_updating_peak_info = False

        # ENHANCEMENT: Update UI to show timeout status
        self._force_peak_display()

        self.logger.info("Peak data timeout handled, UI updated")

    def _show_error_message(self, title: str, message: str) -> None:
        """Show user-friendly error message dialog (thread-safe)"""
        try:
            # Use QTimer to ensure we're on the main thread
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self._show_error_message_main_thread(title, message))
        except Exception as e:
            self.logger.error(f"Failed to queue error message: {str(e)}")

    def _show_error_message_main_thread(self, title: str, message: str) -> None:
        """Show error message on main thread"""
        try:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
            self.logger.info(f"Error message shown to user: {title}")
        except Exception as e:
            self.logger.error(f"Failed to show error message: {str(e)}")

    def _show_warning_message(self, title: str, message: str) -> None:
        """Show user-friendly warning message dialog (thread-safe)"""
        try:
            # Use QTimer to ensure we're on the main thread
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self._show_warning_message_main_thread(title, message))
        except Exception as e:
            self.logger.error(f"Failed to queue warning message: {str(e)}")

    def _show_warning_message_main_thread(self, title: str, message: str) -> None:
        """Show warning message on main thread"""
        try:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
            self.logger.info(f"Warning message shown to user: {title}")
        except Exception as e:
            self.logger.error(f"Failed to show warning message: {str(e)}")

    def _show_info_message(self, title: str, message: str) -> None:
        """Show user-friendly info message dialog (thread-safe)"""
        try:
            # Use QTimer to ensure we're on the main thread
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self._show_info_message_main_thread(title, message))
        except Exception as e:
            self.logger.error(f"Failed to queue info message: {str(e)}")

    def _show_info_message_main_thread(self, title: str, message: str) -> None:
        """Show info message on main thread"""
        try:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
            self.logger.info(f"Info message shown to user: {title}")
        except Exception as e:
            self.logger.error(f"Failed to show info message: {str(e)}")

    def _calculate_dynamic_timeouts(self) -> None:
        """Calculate intelligent timeout values based on file characteristics"""
        try:
            # Get file characteristics
            file_path = self.music_file_info.get('file_path', '')
            file_size_mb = 0
            duration_seconds = 0

            if os.path.exists(file_path):
                file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

            duration_seconds = self.music_file_info.get('duration', 0)
            # Ensure duration_seconds is a number
            try:
                duration_seconds = float(duration_seconds) if duration_seconds else 0
            except (ValueError, TypeError):
                duration_seconds = 0
            if duration_seconds == 0:
                duration_seconds = file_size_mb * 10  # Rough estimate

            # INTELLIGENT TIMEOUT CALCULATION - INCREASED FOR COMPLEX PROCESSING
            # Base: 120s, Size factor: 60s/MB (max 600s), Duration factor: 2s/s (max 600s)
            base_timeout = 120  # Increased from 60s
            size_factor = min(file_size_mb * 60, 600)  # Increased from 30s/MB
            duration_factor = min(duration_seconds * 2, 600)  # Increased from 1s/s

            self._dynamic_processing_timeout = base_timeout + size_factor + duration_factor
            self._max_stall_time = 120  # 120s without progress before warning (reasonable for large files)
            self._max_stall_count = 12  # 12 stalls before timeout (more forgiving for complex processing)

            self.logger.info(f"Intelligent timeout: {self._dynamic_processing_timeout}s "
                             f"(file: {file_size_mb:.1f}MB, duration: {duration_seconds}s)")

        except Exception as e:
            # Conservative fallback
            self._dynamic_processing_timeout = 300  # 5 minutes
            self._max_stall_time = 120
            self._max_stall_count = 12
            self.logger.warning(f"Using default timeout settings: {e}")

    def _detect_processing_progress(self) -> Dict:
        """Detect current processing progress and stage with enhanced intelligence"""
        progress_info = {
            'stage': 'Unknown',
            'peaks_found': 0,
            'peaks_created': 0,
            'is_processing': False,
            'is_complete': False,
            'has_progress': False,
            'analyzer_responsive': True
        }

        try:
            # Check analyzer processing state
            if hasattr(self.analyzer, 'is_processing'):
                progress_info['is_processing'] = self.analyzer.is_processing

            # Check for peak detection in progress
            if hasattr(self.analyzer, '_peak_detection_in_progress'):
                if self.analyzer._peak_detection_in_progress:
                    progress_info['stage'] = 'Peak Detection'
                    progress_info['is_processing'] = True

            # Get current peak counts - check peaks regardless of is_analyzed flag
            try:
                # DEBUG: Track analyzer instance
                analyzer_id = id(self.analyzer) if self.analyzer else "None"
                self.logger.debug(f"Checking analyzer instance {analyzer_id} for peaks")

                # Check peaks even during processing to track progress
                peaks_found = False
                if hasattr(self.analyzer, 'peaks') and self.analyzer.peaks:
                    progress_info['peaks_created'] = len(self.analyzer.peaks)
                    self.logger.debug(f"Found {len(self.analyzer.peaks)} peaks in analyzer {analyzer_id}")
                    peaks_found = True
                else:
                    # Check global storage for peaks
                    import __main__
                    if hasattr(__main__, '_global_peaks_storage') and hasattr(self.analyzer, 'file_path'):
                        file_key = str(self.analyzer.file_path) if self.analyzer.file_path else "unknown"
                        if file_key in __main__._global_peaks_storage:
                            stored_data = __main__._global_peaks_storage[file_key]
                            progress_info['peaks_created'] = len(stored_data['peaks'])
                            self.logger.debug(f"Found {len(stored_data['peaks'])} peaks in global storage")
                            peaks_found = True
                            if stored_data['is_analyzed']:
                                progress_info['is_complete'] = True

                    if not peaks_found:
                        self.logger.debug(f"No peaks found in analyzer {analyzer_id} or global storage")

                # Only mark complete if analyzer says it's analyzed or global storage indicates completion
                if peaks_found and hasattr(self.analyzer, 'is_analyzed') and self.analyzer.is_analyzed:
                    progress_info['is_complete'] = True

                # Try to get found peaks count from various sources (safe during processing)
                if hasattr(self.analyzer, '_peaks_found_count'):
                    progress_info['peaks_found'] = self.analyzer._peaks_found_count
                elif hasattr(self.analyzer, '_drum_hits_found'):
                    progress_info['peaks_found'] = self.analyzer._drum_hits_found

            except Exception as e:
                self.logger.debug(f"Could not get peak counts: {e}")
                progress_info['analyzer_responsive'] = False

            # MULTI-PHASE AWARE: Determine processing stage intelligently
            if progress_info['is_processing']:
                if progress_info['peaks_created'] == 0:
                    progress_info['stage'] = 'Audio Analysis'
                elif progress_info['peaks_found'] > 0 and progress_info['peaks_created'] < progress_info['peaks_found']:
                    progress_info['stage'] = 'Peak Creation'
                else:
                    progress_info['stage'] = 'Processing'
            elif progress_info['is_complete']:
                # Only mark as complete if analyzer explicitly says it's complete
                progress_info['stage'] = 'Complete'
            elif progress_info['peaks_created'] > 0:
                # Have peaks but not marked complete - could be multi-phase processing
                if progress_info['peaks_created'] < 200:
                    progress_info['stage'] = 'Multi-Phase Processing'
                    progress_info['is_complete'] = False  # Explicitly not complete
                else:
                    progress_info['stage'] = 'Complete'
                    progress_info['is_complete'] = True

            # Detect meaningful progress
            current_peak_count = progress_info['peaks_created']
            current_processing = progress_info['is_processing']

            if (current_peak_count > self._last_peak_count or
                    current_processing != self._last_processing_state or
                    progress_info['peaks_found'] > 0):

                progress_info['has_progress'] = True
                self._last_progress_time = datetime.now()
                self._progress_stall_count = 0

                self.logger.debug(f"Progress detected: {current_peak_count} peaks, "
                                  f"processing: {current_processing}")
            else:
                # Check for stall
                time_since_progress = (datetime.now() - self._last_progress_time).total_seconds()
                if time_since_progress > self._max_stall_time:
                    self._progress_stall_count += 1
                    self.logger.warning(f"Progress stall #{self._progress_stall_count} "
                                        f"({time_since_progress:.1f}s since last progress)")

            # Update tracking
            self._last_peak_count = current_peak_count
            self._last_processing_state = current_processing

        except Exception as e:
            self.logger.error(f"Error detecting progress: {e}")
            progress_info['analyzer_responsive'] = False

        return progress_info

    def _update_progress_display(self, progress_info: Dict, elapsed_time: float) -> None:
        """Update UI with intelligent progress information"""
        try:
            # Update peak display during progress
            self._force_peak_display()
        except Exception as e:
            self.logger.error(f"Error updating progress display: {e}")

    def _should_continue_monitoring(self, progress_info: Dict, elapsed_time: float) -> bool:
        """FIXED: Intelligent decision on whether to continue monitoring with proper completion detection"""

        # CRITICAL FIX: Check if analyzer is actually marked as analyzed FIRST
        if hasattr(self.analyzer, 'is_analyzed') and self.analyzer.is_analyzed:
            self.logger.info(f"ANALYZER COMPLETE: is_analyzed=True with {progress_info['peaks_created']} peaks")
            return False

        # MULTI-PHASE AWARE TERMINATION: Only stop if we have sufficient peaks AND analyzer is marked complete
        if progress_info['peaks_created'] > 0:
            # SEGMENT-BASED: Accept any number of High/Very High segment peaks
            if progress_info['peaks_created'] >= 1:  # Accept any segment-appropriate peaks
                self.logger.info(
                    f"SEGMENT-BASED PEAKS: Have {progress_info['peaks_created']} High/Very High segment peaks, checking analyzer status")
                # Double-check analyzer status
                if hasattr(self.analyzer, 'is_analyzed') and self.analyzer.is_analyzed:
                    self.logger.info(
                        f"MULTI-PHASE COMPLETE: Processing complete with {progress_info['peaks_created']} peaks")
                    return False
                else:
                    self.logger.info(
                        f"WAITING FOR ANALYZER: Have {progress_info['peaks_created']} peaks but analyzer not marked complete")
                    # Continue monitoring for a bit longer to see if analyzer completes
                    if elapsed_time > 60:  # Give it 1 minute to complete
                        self.logger.info("TIMEOUT: Analyzer taking too long to mark completion, stopping")
                        return False
                    return True
            else:
                self.logger.info(
                    f"SEGMENT-BASED COMPLETE: Found {progress_info['peaks_created']} High/Very High segment peaks")
                return True

        # Stop if processing is complete
        if progress_info['is_complete']:
            self.logger.info("Processing completed successfully")
            return False

        # Continue if actively processing with progress (but limit time)
        if progress_info['is_processing'] and progress_info['has_progress']:
            # Even with progress, don't monitor for too long
            if elapsed_time > 120:  # Maximum 2 minutes of monitoring
                self.logger.info(f"TIMEOUT: Stopping monitoring after {elapsed_time:.1f}s even with progress")
                return False
            return True

        # Check dynamic timeout
        if elapsed_time > self._dynamic_processing_timeout:
            self.logger.warning(f"Dynamic timeout reached: {elapsed_time:.1f}s > "
                                f"{self._dynamic_processing_timeout}s")
            return False

        # Check stall conditions with reduced tolerance
        if self._progress_stall_count >= 6:  # Reduced from 12 to 6 for faster termination
            self.logger.warning(f"Processing stalled: {self._progress_stall_count} stalls, "
                                f"peaks created: {progress_info['peaks_created']}")

            # FINAL CHECK: Look for peaks one more time before giving up
            if hasattr(self.analyzer, 'peaks') and len(self.analyzer.peaks) > 0:
                self.logger.info(f"Found {len(self.analyzer.peaks)} peaks on final check")
                return False

            # Check one more time if processing completed
            if hasattr(self.analyzer, 'is_analyzed') and self.analyzer.is_analyzed:
                self.logger.info("Processing actually completed (detected via is_analyzed flag)")
                return False

            # Only stop if we have no peaks at all
            if progress_info['peaks_created'] == 0:
                self.logger.warning("No peaks found, stopping monitoring")
                return False
            else:
                # We have some peaks, so processing was partially successful
                self.logger.info("Processing stalled but peaks were created, finalizing...")
                return False

        # Continue monitoring
        return True

    def _finalize_peak_monitoring(self, progress_info: Dict) -> None:
        """FIXED: Finalize monitoring and ENABLE widget interaction"""
        try:
            # Get final peak data
            final_peaks = []
            if self.analyzer:
                try:
                    final_peaks = self.analyzer.get_peak_data()
                except Exception as e:
                    self.logger.error(f"Error getting final peak data: {e}")
                    final_peaks = []

            peak_count = len(final_peaks)

            # Update display with final count
            self._force_peak_display()

            # CRITICAL FIX: Enable widget interaction
            if hasattr(self, 'waveform_view'):
                self.logger.info("ENABLING waveform widget interaction")
                self.waveform_view.setEnabled(True)
                self.waveform_view.setFocusPolicy(Qt.StrongFocus)
                # Force waveform view update
                self.waveform_view.update()

            # CRITICAL FIX: Enable all UI controls
            self.setEnabled(True)

            self.logger.info("UI controls enabled for interaction")

            elapsed_time = (datetime.now() - self._peak_check_start_time).total_seconds()

            if peak_count > 0:
                self.logger.info(f"Peak monitoring completed successfully: "
                                 f"{peak_count} peaks in {elapsed_time:.1f}s - UI ENABLED")
            else:
                self.logger.warning(f"Peak monitoring completed with no peaks after {elapsed_time:.1f}s")

            # Stop monitoring
            self._stop_monitoring("Processing finalized")

        except Exception as e:
            self.logger.error(f"Error finalizing peak monitoring: {e}")
            self._stop_monitoring(f"Finalization error: {e}")

    def _stop_monitoring(self, reason: str) -> None:
        """FIXED: Stop peak monitoring with logging and UI cleanup"""
        try:
            # COMPREHENSIVE FINAL CHECK: Multiple fallback mechanisms
            if self.analyzer and "stalled" in reason.lower():
                import time
                self.logger.info("Performing comprehensive final check for peaks...")
                time.sleep(2.0)  # Wait 2 seconds for processing to complete

                # Check 1: Local analyzer peaks
                if hasattr(self.analyzer, 'peaks') and len(self.analyzer.peaks) > 0:
                    self.logger.info(f"FOUND {len(self.analyzer.peaks)} peaks in local analyzer!")
                    return

                # Check 2: Global storage peaks
                import __main__
                if hasattr(__main__, '_global_peaks_storage') and hasattr(self.analyzer, 'file_path'):
                    file_key = str(self.analyzer.file_path) if self.analyzer.file_path else "unknown"
                    if file_key in __main__._global_peaks_storage:
                        stored_peaks = len(__main__._global_peaks_storage[file_key]['peaks'])
                        self.logger.info(f"FOUND {stored_peaks} peaks in global storage!")
                        # Transfer peaks to current analyzer
                        self.analyzer.peaks = __main__._global_peaks_storage[file_key]['peaks']
                        self.analyzer.is_analyzed = True
                        return

                # Check 3: Processing still active
                if hasattr(self.analyzer, 'is_processing') and self.analyzer.is_processing:
                    self.logger.info("Processing still active, extending monitoring...")
                    self._progress_stall_count = 0
                    self._last_progress_time = datetime.now()
                    return

            if hasattr(self, 'peak_check_timer') and self.peak_check_timer.isActive():
                self.peak_check_timer.stop()
                self.logger.info(f"Peak monitoring stopped: {reason}")

            # CRITICAL FIX: Hide progress bar and enable UI
            if hasattr(self, 'progress_bar'):
                self.progress_bar.setVisible(False)
                self.logger.info("Progress bar hidden")

            # CRITICAL FIX: Enable widget interaction
            if hasattr(self, 'waveform_view'):
                self.logger.info("ENABLING waveform widget interaction")
                self.waveform_view.setEnabled(True)
                self.waveform_view.setFocusPolicy(Qt.StrongFocus)

            # CRITICAL FIX: Enable all UI controls
            self.setEnabled(True)

            # Reset state
            self._peak_check_start_time = None
            self._last_progress_time = None
            self._progress_stall_count = 0
            self.is_processing = False

            self.logger.info("UI controls enabled after stopping monitoring")

        except Exception as e:
            self.logger.error(f"Error stopping monitoring: {e}")

    def _perform_memory_cleanup(self) -> None:
        """Perform periodic memory cleanup to optimize performance"""
        try:
            import gc

            # Force garbage collection
            collected = gc.collect()
            if collected > 0:
                self.logger.debug(f"Memory cleanup: collected {collected} objects")

            # Clean up old cached data if it exists
            if hasattr(self, '_cached_peaks') and self._cached_peaks is not None:
                # Only clean if we have a lot of peaks (memory intensive)
                if len(self._cached_peaks) > 10000:
                    self.logger.debug("Cleaning up large cached peak data")
                    # Don't clear completely, just log the size

        except Exception as e:
            self.logger.debug(f"Error during memory cleanup: {str(e)}")

    def _reset_analysis_state(self) -> None:
        """Reset analysis state for new file loading"""
        try:
            # Reset cached data
            if hasattr(self, '_cached_peaks'):
                self._cached_peaks = None

            # Reset timeout tracking
            self._peak_check_start_time = None
            self._peak_check_timeout_warnings = 0

            # Reset processing flags
            self._is_updating_peak_info = False
            self.is_processing = False

            # Reset UI elements
            self._force_peak_display()

            # Stop any running timers
            if hasattr(self, 'peak_check_timer') and self.peak_check_timer.isActive():
                self.peak_check_timer.stop()

            self.logger.debug("Analysis state reset for new file loading")

        except Exception as e:
            self.logger.error(f"Error resetting analysis state: {str(e)}")

    def _on_play(self) -> None:
        """Handle play button click"""
        if not self.analyzer:
            return

        if not self.music_file_info or 'path' not in self.music_file_info:
            self._show_warning_message("Error", "No audio file available for playback.")
            return

        # If already playing, do nothing
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            return

        # If starting fresh or after stop
        if self.player.source().isEmpty() or self.player.playbackState() == QMediaPlayer.StoppedState:
            # Get the file path from music_file_info
            file_path = Path(self.music_file_info['path'])
            print(f"🔊 _on_play: Using file path from music_file_info: {file_path}")

            # Print additional info about the music_file_info dictionary
            print(f"🔊 _on_play: music_file_info keys: {self.music_file_info.keys()}")
            if 'is_separated' in self.music_file_info:
                print(f"🔊 _on_play: is_separated: {self.music_file_info['is_separated']}")
            if 'is_drum_stem' in self.music_file_info:
                print(f"🔊 _on_play: is_drum_stem: {self.music_file_info['is_drum_stem']}")
            if 'original_file' in self.music_file_info:
                print(f"🔊 _on_play: original_file: {self.music_file_info['original_file']}")

            # Verify that the file exists
            if not file_path.exists():
                # If the file doesn't exist but we have an original_file, check if that exists
                if 'original_file' in self.music_file_info and Path(self.music_file_info['original_file']).exists():
                    print(f"🔊 _on_play: File not found, but original_file exists. Using original_file instead.")
                    file_path = Path(self.music_file_info['original_file'])
                else:
                    self._show_warning_message("Error", "Audio file not found.")
                    return

            # Double-check that we're using the correct file for playback
            # If this is a separated drum stem, make sure we're using the drum stem file
            if ('is_separated' in self.music_file_info and self.music_file_info['is_separated']) or \
                    ('is_drum_stem' in self.music_file_info and self.music_file_info['is_drum_stem']):
                print(f"🔊 _on_play: This is a separated drum stem, ensuring we use the correct file for playback")
                # Make sure file_path is the path from music_file_info, not the original file
                file_path = Path(self.music_file_info['path'])
                print(f"🔊 _on_play: Using drum stem file path: {file_path}")
                if not file_path.exists():
                    self._show_warning_message("Error", "Drum stem file not found.")
                    return

            # Use the path from music_file_info which will be the drum stem path if is_drum_stem is True
            print(f"🔊 _on_play: Setting media source to {file_path}")
            self.player.setSource(QUrl.fromLocalFile(str(file_path)))
            self.audio_output.setVolume(1.0)
            print(f"🔊 _on_play: Media source set successfully")

            # Set position based on waveform view
            position_ms = int(self.waveform_view.current_position * self.analyzer.duration_seconds * 1000)
            self.player.setPosition(position_ms)

        # Start playback
        self.player.play()

        # Update UI state
        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)

    def _on_pause(self) -> None:
        """Handle pause button click"""
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()

            # Update UI state
            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)

    def _on_stop(self) -> None:
        """Handle stop button click"""
        self.player.stop()

        # Reset position
        self.waveform_view.set_position(0.0)
        self.time_slider.setValue(0)

        # Update UI state
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)

    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        """
        Handle playback state changes

        Args:
            state: New playback state
        """
        if state == QMediaPlayer.PlayingState:
            self.play_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.position_update_timer.start()

            # Enable centered playhead mode for smooth scrolling during playback
            if hasattr(self.waveform_view, 'set_playback_mode'):
                self.waveform_view.set_playback_mode(True)

        elif state == QMediaPlayer.PausedState:
            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.position_update_timer.stop()

            # Disable centered playhead mode when paused
            if hasattr(self.waveform_view, 'set_playback_mode'):
                self.waveform_view.set_playback_mode(False)

        else:  # Stopped
            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.position_update_timer.stop()

            # Disable centered playhead mode when stopped
            if hasattr(self.waveform_view, 'set_playback_mode'):
                self.waveform_view.set_playback_mode(False)

    def _update_position_from_player(self) -> None:
        """Update position from media player in real-time"""
        if not self.analyzer or not self.analyzer.is_analyzed:
            return

        if self.player.playbackState() != QMediaPlayer.PlayingState:
            return

        position_ms = self.player.position()
        if self.analyzer.duration_seconds > 0:
            norm_pos = position_ms / (self.analyzer.duration_seconds * 1000)

            # Update waveform view
            self.waveform_view.set_position(norm_pos)

            # Update time slider
            self.time_slider.blockSignals(True)
            self.time_slider.setValue(int(norm_pos * 1000))
            self.time_slider.blockSignals(False)

            # Update position display
            self._update_position_display(norm_pos)

    def _on_player_position_changed(self, position_ms: int) -> None:
        """
        Handle major position changes from media player

        Args:
            position_ms: New position in milliseconds
        """
        if not self.analyzer:
            return

        # Convert to normalized position
        if self.analyzer.duration_seconds > 0:
            norm_pos = position_ms / (self.analyzer.duration_seconds * 1000)

            # Update waveform view
            self.waveform_view.set_position(norm_pos)

            # Update time slider
            self.time_slider.blockSignals(True)
            self.time_slider.setValue(int(norm_pos * 1000))
            self.time_slider.blockSignals(False)

            # Update position display
            self._update_position_display(norm_pos)

    def _update_smooth_position(self) -> None:
        """
        ENHANCEMENT: Smooth position updates at 60fps during playback with auto-scroll
        """
        if not self.analyzer or self.player.playbackState() != QMediaPlayer.PlayingState:
            return

        # Get current position from media player
        position_ms = self.player.position()
        if self.analyzer.duration_seconds > 0:
            norm_pos = position_ms / (self.analyzer.duration_seconds * 1000)

            # Update waveform view smoothly
            self.waveform_view.set_position(norm_pos)

            # ENHANCEMENT: Auto-scroll waveform to keep playback position visible
            if hasattr(self.waveform_view, 'auto_scroll_to_position'):
                self.waveform_view.auto_scroll_to_position(norm_pos)

            # Update time slider smoothly
            self.time_slider.blockSignals(True)
            self.time_slider.setValue(int(norm_pos * 1000))
            self.time_slider.blockSignals(False)

            # Update position display
            self._update_position_display(norm_pos)

    def _on_volume_changed(self, value: int) -> None:
        """
        ENHANCEMENT: Handle volume slider changes with visual feedback

        Args:
            value: Volume level (0-100)
        """
        # Update audio output volume
        if hasattr(self, 'audio_output'):
            self.audio_output.setVolume(value / 100.0)

        # Update visual feedback
        self.volume_label.setText(f"{value}%")

        # Color coding for volume levels
        if value == 0:
            self.volume_label.setStyleSheet("font-weight: bold; color: #e74c3c;")  # Red for muted
        elif value < 30:
            self.volume_label.setStyleSheet("font-weight: bold; color: #f39c12;")  # Orange for low
        elif value < 70:
            self.volume_label.setStyleSheet("font-weight: bold; color: #2980b9;")  # Blue for normal
        else:
            self.volume_label.setStyleSheet("font-weight: bold; color: #27ae60;")  # Green for high

    def _on_speed_changed(self, speed_text: str) -> None:
        """
        ENHANCEMENT: Handle playback speed changes

        Args:
            speed_text: Speed selection (e.g., "1.0x", "1.5x")
        """
        try:
            # Extract speed multiplier
            speed_value = float(speed_text.replace('x', ''))

            # Set playback rate
            self.player.setPlaybackRate(speed_value)

            self.logger.info(f"Playback speed changed to {speed_text}")

        except ValueError:
            self.logger.error(f"Invalid speed value: {speed_text}")

    def _on_time_slider_changed(self, value: int) -> None:
        """
        Handle time slider value change

        Args:
            value: New slider value (0-1000)
        """
        if not self.analyzer or not self.analyzer.has_waveform_data():
            return

        # Convert slider value to normalized position
        position = value / 1000.0

        # Update position display
        self._update_position_display(position)

        # Update waveform view
        self.waveform_view.set_position(position)

        # Update media player if playing
        if self.player.playbackState() != QMediaPlayer.StoppedState:
            position_ms = int(position * self.analyzer.duration_seconds * 1000)
            if abs(position_ms - self.player.position()) > 100:
                self.player.setPosition(position_ms)

    def _on_zoom_in(self) -> None:
        """Handle zoom in button click"""
        if hasattr(self.waveform_view, 'zoom_factor'):
            current_zoom = self.waveform_view.zoom_factor
            self.waveform_view.set_zoom(current_zoom * self.waveform_view.zoom_increment, animate=True)

    def _on_zoom_out(self) -> None:
        """Handle zoom out button click"""
        if hasattr(self.waveform_view, 'zoom_factor'):
            current_zoom = self.waveform_view.zoom_factor
            self.waveform_view.set_zoom(current_zoom / self.waveform_view.zoom_increment, animate=True)

    def _on_reset_zoom(self) -> None:
        """Handle reset zoom button click"""
        if hasattr(self.waveform_view, 'set_zoom'):
            self.waveform_view.set_zoom(1.0, animate=True)

    def _on_zoom_slider_changed(self, value: int) -> None:
        """
        Handle zoom slider value change from controls panel

        Args:
            value: New slider value (0-100)
        """
        if not hasattr(self.waveform_view, 'min_zoom'):
            return

        # Convert slider value to zoom factor (logarithmic scale)
        log_min = math.log(self.waveform_view.min_zoom)
        log_max = math.log(self.waveform_view.max_zoom)
        log_zoom = log_min + (value / 100.0) * (log_max - log_min)
        zoom_factor = math.exp(log_zoom)

        # Apply zoom
        self.waveform_view.set_zoom(zoom_factor, animate=True)

    def _on_view_zoom_changed(self, zoom_factor: float) -> None:
        """
        Handle zoom change from waveform view

        Args:
            zoom_factor: New zoom factor
        """
        self._update_zoom_display(zoom_factor)

    def _on_view_position_changed(self, position: float) -> None:
        """
        Handle position change from waveform view

        Args:
            position: New normalized position (0.0-1.0)
        """
        self._update_position_display(position)

        # Update time slider
        self.time_slider.blockSignals(True)
        self.time_slider.setValue(int(position * 1000))
        self.time_slider.blockSignals(False)

    def _close_dialog(self) -> None:
        """Clean up resources and close the dialog"""
        try:
            # Stop timers
            self._stop_timers()

            # Stop playback
            self._stop_playback()

            # Clean up resources
            self._cleanup_resources()

            # Accept the dialog (close it)
            self.accept()

        except Exception as e:
            self.logger.error(f"Error during dialog cleanup: {str(e)}", exc_info=True)
            # Still try to close even if cleanup fails
            self.accept()

    def _stop_timers(self) -> None:
        """Stop all active timers with enhanced cleanup"""
        try:
            if hasattr(self, 'position_update_timer') and self.position_update_timer:
                if self.position_update_timer.isActive():
                    self.position_update_timer.stop()
                    self.logger.debug("Position update timer stopped")

            if hasattr(self, 'peak_check_timer') and self.peak_check_timer:
                if self.peak_check_timer.isActive():
                    self.peak_check_timer.stop()
                    self.logger.debug("Peak check timer stopped")
                self._peak_check_start_time = None  # Reset timeout tracking
                self._peak_check_timeout_warnings = 0

            # ENHANCEMENT: Clean up any other timers
            if hasattr(self, '_peak_data_timer') and self._peak_data_timer:
                if self._peak_data_timer.isActive():
                    self._peak_data_timer.stop()
                    self.logger.debug("Peak data timer stopped")

        except Exception as e:
            self.logger.error(f"Error stopping timers: {str(e)}")

    def _stop_playback(self) -> None:
        """Stop media playback"""
        if hasattr(self, 'player'):
            self.player.stop()
            # Wait for player to actually stop
            while self.player.playbackState() != QMediaPlayer.StoppedState:
                QApplication.processEvents()

    def _cleanup_resources(self) -> None:
        """Clean up media resources"""
        if hasattr(self, 'player'):
            self.player.setSource(QUrl())  # Clear source
            self.audio_output.setVolume(0.0)

    def closeEvent(self, event) -> None:
        """
        Handle window close event

        Args:
            event: Close event
        """
        try:
            self._close_dialog()
            event.accept()
        except Exception as e:
            self.logger.error(f"Error in closeEvent: {str(e)}", exc_info=True)
            event.accept()

    def _handle_error(self, error: str, title: str = "Error") -> None:
        """
        Handle and display errors

        Args:
            error: Error message
            title: Dialog title
        """
        self.logger.error(error)
        self._show_warning_message(title, error)

    def _ensure_analyzer_state(self) -> bool:
        """
        Ensure analyzer is in valid state

        Returns:
            bool: True if analyzer is valid
        """
        if not self.analyzer:
            self._handle_error("No analyzer available")
            return False

        if not self.analyzer.is_analyzed:
            self._handle_error("Waveform not analyzed")
            return False

        return True

    def _ensure_file_loaded(self) -> bool:
        """
        Ensure audio file is properly loaded

        Returns:
            bool: True if file is loaded
        """
        if not self.music_file_info:
            self._handle_error("No music file information available")
            return False

        if 'path' not in self.music_file_info:
            self._handle_error("No file path available")
            return False

        file_path = Path(self.music_file_info['path'])
        if not file_path.exists():
            self._handle_error(f"File not found: {file_path}")
            return False

        return True

    def _create_error_message(self, error: Exception) -> str:
        """
        Create formatted error message from exception

        Args:
            error: Exception object

        Returns:
            str: Formatted error message
        """
        import traceback

        error_type = type(error).__name__
        error_msg = str(error)
        trace = traceback.format_exc()

        self.logger.error(f"{error_type}: {error_msg}\n{trace}")

        return f"{error_type}: {error_msg}"

    def _log_operation(self, operation: str) -> None:
        """
        Log an operation with timestamp

        Args:
            operation: Operation description
        """
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        self.logger.info(f"{timestamp} - {operation}")

    def _get_normalized_position(self, position_ms: int) -> float:
        """
        Convert millisecond position to normalized position

        Args:
            position_ms: Position in milliseconds

        Returns:
            float: Normalized position (0.0-1.0)
        """
        if not self.analyzer or self.analyzer.duration_seconds <= 0:
            return 0.0

        return position_ms / (self.analyzer.duration_seconds * 1000)

    def _get_millisecond_position(self, normalized_pos: float) -> int:
        """
        Convert normalized position to milliseconds

        Args:
            normalized_pos: Normalized position (0.0-1.0)

        Returns:
            int: Position in milliseconds
        """
        if not self.analyzer or self.analyzer.duration_seconds <= 0:
            return 0

        return int(normalized_pos * self.analyzer.duration_seconds * 1000)

    def _format_duration(self, duration_seconds: float) -> str:
        """
        Format duration in seconds to string

        Args:
            duration_seconds: Duration in seconds

        Returns:
            str: Formatted duration string
        """
        from datetime import timedelta

        duration = timedelta(seconds=int(duration_seconds))
        milliseconds = int((duration_seconds % 1) * 1000)

        return f"{duration}.{milliseconds:03d}"

    def _create_debug_info(self) -> dict:
        """
        Create debug information dictionary

        Returns:
            dict: Debug information
        """
        debug_info = {
            'analyzer_state': {
                'initialized': self.analyzer is not None,
                'analyzed': getattr(self.analyzer, 'is_analyzed', False),
                'processing': getattr(self.analyzer, 'is_processing', False),
                'peak_count': len(self.analyzer.get_peak_data()) if self.analyzer is not None else 0
            },
            'player_state': {
                'initialized': hasattr(self, 'player'),
                'playing': self.player.playbackState() == QMediaPlayer.PlayingState if hasattr(self,
                                                                                               'player') else False,
                'position': self.player.position() if hasattr(self, 'player') else 0
            },
            'ui_state': {
                'processing': self.is_processing,
                'zoom_factor': self.waveform_view.zoom_factor if hasattr(self.waveform_view, 'zoom_factor') else 1.0,
                'current_position': self.waveform_view.current_position if hasattr(self.waveform_view,
                                                                                   'current_position') else 0.0
            }
        }

        return debug_info

    @profile_method("set_analyzer")
    def set_analyzer(self, analyzer: WaveformAnalyzer) -> None:
        """Set the analyzer instance and update the view with optimizations"""
        print(f"🎵 Setting analyzer in OptimizedWaveformAnalysisDialog")

        # Print analyzer file path if available
        if hasattr(analyzer, 'file_path') and analyzer.file_path:
            print(f"🔊 set_analyzer: Analyzer file path: {analyzer.file_path}")
        else:
            print(f"🔊 set_analyzer: Analyzer does not have a file path set yet")

        # Print music_file_info path for comparison
        if hasattr(self, 'music_file_info') and self.music_file_info and 'path' in self.music_file_info:
            print(f"🔊 set_analyzer: music_file_info path: {self.music_file_info['path']}")

            # Print additional info about the music_file_info dictionary
            print(f"🔊 set_analyzer: music_file_info keys: {self.music_file_info.keys()}")
            if 'is_separated' in self.music_file_info:
                print(f"🔊 set_analyzer: is_separated: {self.music_file_info['is_separated']}")
            if 'is_drum_stem' in self.music_file_info:
                print(f"🔊 set_analyzer: is_drum_stem: {self.music_file_info['is_drum_stem']}")
            if 'original_file' in self.music_file_info:
                print(f"🔊 set_analyzer: original_file: {self.music_file_info['original_file']}")
        else:
            print(f"🔊 set_analyzer: No music_file_info path available")

        # CRITICAL: Always use the provided analyzer, don't check for same instance
        # This prevents multiple analyzer instance issues
        if hasattr(self, 'analyzer') and self.analyzer is not None:
            self.logger.info(f"Replacing existing analyzer (id: {id(self.analyzer)}) with new one (id: {id(analyzer)})")

        self.analyzer = analyzer
        self.logger.info(f"Setting analyzer in OptimizedWaveformAnalysisDialog (id: {id(analyzer)})")

        # OPTIMIZATION: Record analysis start time
        self.analysis_start_time = time.time()

        if self.analyzer:
            # Connect to peak detection complete signal
            # Check if we have a previous analyzer with the same signal
            if hasattr(self, '_previous_analyzer') and self._previous_analyzer is not None:
                try:
                    # Only try to disconnect if it's a different analyzer
                    if self._previous_analyzer is not self.analyzer:
                        self._previous_analyzer.peak_detection_complete.disconnect(self._update_after_peak_detection)
                        self.logger.info("Disconnected existing peak_detection_complete signal from previous analyzer")
                except (RuntimeError, TypeError, AttributeError, RuntimeWarning) as e:
                    # Signal was not connected or other error, which is fine
                    self.logger.debug(f"No need to disconnect signal: {str(e)}")

            # Store current analyzer for future reference
            self._previous_analyzer = self.analyzer

            # Connect the signal directly - simplify the connection logic
            try:
                # Check if the signal exists before trying to disconnect
                if hasattr(self.analyzer, 'peak_detection_complete'):
                    # Use a safer approach for disconnecting signals
                    # PySide6 doesn't provide a direct way to check if a specific slot is connected
                    # So we'll use a try-except block but with improved error handling
                    try:
                        # Attempt to disconnect only if we think it might be connected
                        # This is still not perfect but reduces the chance of warnings
                        if hasattr(self, '_signal_connected') and self._signal_connected:
                            self.analyzer.peak_detection_complete.disconnect(self._update_after_peak_detection)
                            self.logger.debug("Disconnected from peak_detection_complete signal")
                            self._signal_connected = False
                    except Exception as e:
                        # If disconnection fails, log it but don't raise an error
                        self.logger.debug(f"Could not disconnect signal: {str(e)}")
                        # Reset our tracking flag since we're not sure of the connection state
                        self._signal_connected = False

                    # Now connect
                    self.analyzer.peak_detection_complete.connect(self._update_after_peak_detection)
                    # Set our tracking flag to indicate the signal is connected
                    self._signal_connected = True
                    self.logger.info("Connected to peak_detection_complete signal")
                else:
                    self.logger.warning("Analyzer does not have peak_detection_complete signal")
            except Exception as e:
                self.logger.warning(f"Error handling signal connection: {str(e)}")

            self.logger.info(f"Analyzer state - analyzed: {self.analyzer.is_analyzed}, "
                             f"has_data: {hasattr(self.analyzer, 'waveform_data') and self.analyzer.waveform_data is not None}")

            # Update the waveform view with the analyzer first
            if hasattr(self, 'waveform_view'):
                self.logger.info("Setting analyzer in waveform view")
                self.waveform_view.set_analyzer(self.analyzer)

            # Only load the waveform data if the analyzer is not already analyzed or if it's a new analyzer
            # This prevents unnecessary reprocessing of the waveform data
            if not self.analyzer.is_analyzed or not hasattr(self,
                                                            '_previous_analyzer') or self._previous_analyzer is not self.analyzer:
                self.logger.info("Loading waveform data after setting analyzer")
                # Check if file is already loaded in analyzer
                if hasattr(self.analyzer, 'file_path') and self.analyzer.file_path and Path(
                        self.analyzer.file_path).exists():
                    if self.music_file_info and 'path' in self.music_file_info and Path(
                            self.music_file_info['path']) == Path(self.analyzer.file_path):
                        # Check if waveform_data is available
                        if hasattr(self.analyzer, 'waveform_data') and self.analyzer.waveform_data is not None:
                            self.logger.info(
                                "File already loaded in analyzer with waveform data, updating UI without reprocessing")
                            self._on_waveform_loaded_safe(True)
                            return
                        else:
                            self.logger.info("File loaded in analyzer but waveform_data is None, processing waveform")
                            # Process the waveform to ensure waveform_data is populated
                            QTimer.singleShot(100, self.load_waveform_data)
                            return

                # Only schedule load_waveform_data if we need to load a new file
                QTimer.singleShot(100, self.load_waveform_data)
            else:
                self.logger.info("Analyzer already analyzed, skipping waveform data loading")
                # Update UI with existing data
                self._on_waveform_loaded_safe(True)

        # Initialize generator with analyzer if it exists
        print(f"🔧 Dialog set_analyzer: checking for musical_generator")
        if hasattr(self, 'musical_generator'):
            print(f"🔧 Dialog set_analyzer: Found musical_generator, setting analyzer: {self.analyzer}")
            self.musical_generator.set_analyzer(self.analyzer)
            # Force update of generator status
            self.musical_generator.update_peak_counts()
        else:
            print(f"🔧 Dialog set_analyzer: No musical_generator found yet")

    def _update_ui_safely(self) -> None:
        """Update UI elements in a thread-safe way"""
        if self.analyzer and self.analyzer.is_analyzed:
            # Update waveform view
            if hasattr(self, 'waveform_view'):
                self.waveform_view.set_analyzer(self.analyzer)

            # Update controls
            self._init_playback_state()
            self._enable_controls()
            self._update_duration_display()
            self._force_peak_display()

    @Slot(bool)
    @profile_method("_update_after_peak_detection")
    def _update_after_peak_detection(self, success: bool = True) -> None:
        """OPTIMIZED: Update UI after peak detection completes with performance improvements"""
        print("🎨 Updating UI after optimized peak detection completion")
        ui_update_start = time.time()

        # Stop the peak check timer to prevent UI from becoming unresponsive
        if hasattr(self, 'peak_check_timer') and self.peak_check_timer.isActive():
            self.logger.info("Stopping peak check timer in _update_after_peak_detection")
            self.peak_check_timer.stop()
            self._peak_check_start_time = None  # Reset timeout tracking

        if not self.analyzer:
            self.logger.info("No analyzer available in _update_after_peak_detection")
            return

        # OPTIMIZATION: Calculate analysis time
        if self.analysis_start_time:
            analysis_time = time.time() - self.analysis_start_time
            print(f"✅ Analysis completed in {analysis_time:.2f} seconds")
            self.logger.info(f"Analysis completed in {analysis_time:.2f} seconds")

        # Check analyzer completion status
        self.logger.info(f"Analyzer analyzed status: {self.analyzer.is_analyzed}")

        # Ensure waveform data is available
        if not hasattr(self.analyzer, 'waveform_data') or self.analyzer.waveform_data is None:
            self.logger.error("Analyzer has no waveform data in _update_after_peak_detection")
            return

        # Get peak data using the proper API method
        peaks = self.analyzer.get_peak_data()
        peak_count = len(peaks)
        print(f"🎯 Updating display with {peak_count} peaks")
        self.logger.info(f"Updating display with {peak_count} peaks")

        # Print information about the detected peaks
        self.logger.info(f"Analysis complete for {self.analyzer.filename}")
        self.logger.info(f"Found {peak_count} peaks")

        # Update the peak count display
        self._force_peak_display()

        # Force update of peak info in the dialog
        self._update_peak_info()

        # Update the spinbox maximum to be the lesser of peak_count or 1000
        max_outputs = min(peak_count, 1000) if peak_count > 0 else 1000

        # OPTIMIZATION: Enable UI interaction immediately with lazy loading
        if hasattr(self, 'waveform_view'):
            print("🎉 ENABLING optimized waveform widget interaction")
            self.logger.info("ENABLING optimized waveform widget interaction after peak detection")
            self.waveform_view.setEnabled(True)
            self.waveform_view.setFocusPolicy(Qt.StrongFocus)

            # Ensure the analyzer is set in the waveform view
            if self.waveform_view.analyzer is not self.analyzer:
                self.logger.info("Setting analyzer in waveform view from _update_after_peak_detection")
                self.waveform_view.set_analyzer(self.analyzer)
            else:
                # Force a redraw to show the peaks with lazy loading
                self.waveform_view.update()

        # Enable controls now that we have peaks
        self._enable_controls()

        # Update duration display
        self._update_duration_display()

        # OPTIMIZATION: Enable all UI controls immediately
        self.setEnabled(True)

        # OPTIMIZATION: Record UI update time
        ui_update_time = time.time() - ui_update_start
        self.ui_update_times.append(ui_update_time)
        print(f"⚡ UI updated in {ui_update_time:.3f}s")

        # CRITICAL FIX: Mark processing as complete
        self.is_processing = False

        self.logger.info("UI controls enabled for interaction after peak detection")

    def clear_cues_from_table(self, table):
        """Clear existing cues from the cue table."""
        while table.rowCount() > 0:
            table.removeRow(0)

    def _get_processing_stage(self) -> str:
        """Determine current processing stage for user feedback"""
        try:
            if not hasattr(self, 'analyzer') or not self.analyzer:
                return "Initializing"

            # Check various analyzer states to determine stage
            if hasattr(self.analyzer, 'is_processing') and self.analyzer.is_processing:
                if hasattr(self.analyzer, 'waveform_data') and self.analyzer.waveform_data is not None:
                    return "Peak Detection"
                else:
                    return "Loading Audio"
            elif hasattr(self.analyzer, '_peak_detection_in_progress') and self.analyzer._peak_detection_in_progress:
                return "Finding Peaks"
            elif hasattr(self.analyzer, 'is_analyzed') and self.analyzer.is_analyzed:
                return "Finalizing"
            else:
                return "Processing"

        except Exception as e:
            self.logger.debug(f"Error determining processing stage: {str(e)}")
            return "Processing"

    def _show_status_message(self, message: str, duration: int = 2000):
        """Show a temporary status message"""
        # This would typically show in a status bar or temporary label
        # For now, just log it
        self.logger.info(f"Status: {message}")
