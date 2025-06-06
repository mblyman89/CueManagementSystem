import traceback

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QSplitter, QWidget,
    QProgressBar, QSlider, QDialogButtonBox,
    QMessageBox, QStyle, QApplication, QTabWidget, QSpinBox, QTableWidgetItem, QComboBox, QCheckBox)
from PySide6.QtCore import (
    Qt, Signal, QRect, Slot, QUrl, QTimer,
    QMetaObject, Q_ARG, QModelIndex)
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

import os
import math
import logging
from typing import Optional, Dict, List
from pathlib import Path

from views.waveform.waveform_widget import WaveformView
from utils.audio.waveform_analyzer import WaveformAnalyzer
from utils.musical_generator import MusicalShowGenerator


class WaveformAnalysisDialog(QDialog):
    """
    Dialog for displaying and interacting with music waveforms

    Features:
    - Real-time waveform visualization
    - Audio playback controls
    - Interactive zoom and navigation
    - Peak detection visualization
    - Time and amplitude markers
    """

    # Signal emitted when waveform analysis is complete and ready for show generation
    show_generation_ready = Signal(dict)

    def __init__(self, music_file_info: Dict, parent: Optional[QWidget] = None, led_panel=None, cue_table=None):
        """
        Initialize the waveform analysis dialog.

        Args:
            music_file_info: Dictionary containing music file information.
            parent: Parent widget.
            led_panel: Reference to the LedGrid instance.
            cue_table: Reference to the CueTableView instance.
        """
        super().__init__(parent)
        self.setWindowTitle("Waveform Analysis")

        # Store music file information and references
        self.music_file_info = music_file_info
        self.led_panel = led_panel
        self.cue_table = cue_table

        # Configure logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Initialize analyzer
        self.analyzer = None

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

        # Timer for peak detection updates - check more frequently
        self.peak_check_timer = QTimer(self)
        self.peak_check_timer.setInterval(50)  # Check every 50ms
        self.peak_check_timer.timeout.connect(self._update_peak_info)
        self.peak_check_timer.start()

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

        # Set initial splitter sizes (70% waveform, 30% controls)
        splitter.setSizes([700, 300])
        main_layout.addWidget(splitter, 1)  # 1 = stretch factor

        # Add dialog buttons
        self._init_dialog_buttons(main_layout)

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

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setVisible(False)
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
        controls_layout.setContentsMargins(0, 0, 0, 0)

        # Create tab widget
        tab_widget = QTabWidget()
        self._style_tab_widget(tab_widget)  # Apply styling

        # Add Playback Controls tab
        playback_tab = self._create_playback_tab()
        tab_widget.addTab(playback_tab, "Playback Controls")

        # Add Generate Musical tab
        generate_tab = self._create_generate_tab()
        tab_widget.addTab(generate_tab, "Generate Musical")

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

        # Add playback controls group
        layout.addWidget(self._create_playback_group())

        # Add beat detection group
        layout.addWidget(self._create_beat_detection_group())

        # Add stretch to push everything to the top
        layout.addStretch()

        return tab

    def _create_generate_tab(self) -> QWidget:
        """Create the generate musical tab with peak distribution options."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Peak Distribution Selection
        peak_dist_label = QLabel("Peak Distribution:")
        self.peak_dist_combobox = QComboBox()
        self.peak_dist_combobox.addItems(["Custom", "Even"])
        peak_dist_layout = QHBoxLayout()
        peak_dist_layout.addWidget(peak_dist_label)
        peak_dist_layout.addWidget(self.peak_dist_combobox)
        layout.addLayout(peak_dist_layout)

        # Number of Outputs input (initially visible)
        outputs_label = QLabel("Number of Outputs:")
        self.outputs_spinbox = QSpinBox()
        self.outputs_spinbox.setRange(1, 1000)
        self.outputs_spinbox.setValue(10)
        outputs_layout = QHBoxLayout()
        outputs_layout.addWidget(outputs_label)
        outputs_layout.addWidget(self.outputs_spinbox)
        layout.addLayout(outputs_layout)

        # Custom Outputs spinbox (initially hidden, read-only)
        custom_outputs_label = QLabel("Number of Outputs:")
        self.custom_outputs_spinbox = QSpinBox()
        self.custom_outputs_spinbox.setRange(0, 10000)  # Allow 0 for display
        self.custom_outputs_spinbox.setReadOnly(True)
        self.custom_outputs_spinbox.setVisible(False)  # Initially hidden

        custom_outputs_layout = QHBoxLayout()
        custom_outputs_layout.addWidget(custom_outputs_label)
        custom_outputs_layout.addWidget(self.custom_outputs_spinbox)
        layout.addLayout(custom_outputs_layout)

        # Select All checkbox
        self.select_all_checkbox = QCheckBox("Select All Peaks")
        layout.addWidget(self.select_all_checkbox)
        self.select_all_checkbox.toggled.connect(self._update_custom_outputs)

        # Output Mode Selection
        output_mode_label = QLabel("Output Mode:")
        self.output_mode_combobox = QComboBox()
        self.output_mode_combobox.addItems(["Random", "Sequential"])  # Dropdown items
        output_mode_layout = QHBoxLayout()
        output_mode_layout.addWidget(output_mode_label)
        output_mode_layout.addWidget(self.output_mode_combobox)
        layout.addLayout(output_mode_layout)

        # Time Offset input
        time_offset_label = QLabel("Time Offset (ms):")
        self.time_offset_spinbox = QSpinBox()
        self.time_offset_spinbox.setRange(1, 10000)  # Range 1-10000 ms
        self.time_offset_spinbox.setValue(0)  # Default 0 ms
        time_offset_layout = QHBoxLayout()
        time_offset_layout.addWidget(time_offset_label)
        time_offset_layout.addWidget(self.time_offset_spinbox)
        layout.addLayout(time_offset_layout)

        # Generate button
        self.generate_button = QPushButton("Generate Show")
        self.generate_button.clicked.connect(self._on_generate_show)  # Connect to handler
        layout.addWidget(self.generate_button)

        # Add a label to display messages
        self.generation_message = QLabel("")
        self.generation_message.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.generation_message)

        layout.addStretch()  # Push elements to the top

        self.peak_dist_combobox.currentIndexChanged.connect(self._on_peak_dist_changed)
        self.select_all_checkbox.toggled.connect(self._on_select_all_changed)
        self.waveform_view.peak_selection_changed.connect(self._update_custom_outputs)

        return tab

    def _update_custom_outputs(self):
        """Update the custom outputs spinbox based on selected peaks."""
        if self.peak_dist_combobox.currentText() == "Custom":
            selected_count = len(self.waveform_view.selected_peaks)
            self.custom_outputs_spinbox.setValue(selected_count)

    @Slot()
    def _on_peak_dist_changed(self, index):
        """Handle peak distribution mode change."""
        if index == 0:  # Custom
            self.outputs_spinbox.setVisible(False)
            self.custom_outputs_spinbox.setVisible(True)
            self._update_custom_outputs()  # Call the correct method name
        else:  # Manual
            self.custom_outputs_spinbox.setVisible(False)
            self.outputs_spinbox.setVisible(True)

    @Slot(bool)
    def _on_select_all_changed(self, checked):
        """Handle Select All checkbox toggle."""
        if not self.analyzer or not hasattr(self.analyzer, 'peaks'):
            return

        if checked:
            peak_indices = set(range(len(self.analyzer.peaks)))
        else:
            peak_indices = set()

        self.waveform_view.selected_peaks = peak_indices
        self.waveform_view.update()
        self._update_custom_outputs()  # Update the spinbox after Select All

    def _on_generate_show(self):
        """Handler for the Generate Show button (corrected for Even/Custom modes)."""
        if not self.analyzer or not self.analyzer.is_analyzed:
            self._handle_error("Waveform not analyzed yet.")
            return

        if self.peak_dist_combobox.currentText() == "Even":
            num_outputs = self.outputs_spinbox.value()
            if num_outputs <= 0 or num_outputs > 1000:
                self._handle_error("Invalid number of outputs (1-1000).")
                return
            selected_peaks = None  # Use all peaks in Even mode
        elif self.peak_dist_combobox.currentText() == "Custom":
            selected_peaks = self.waveform_view.selected_peaks
            num_outputs = len(selected_peaks)
            if num_outputs == 0:
                self._handle_error("No peaks selected for custom generation.")
                return
            elif num_outputs > 1000:
                QMessageBox.warning(self, "Output Limit", "Number of selected peaks exceeds the limit (1000).")
                return
        else:
            return  # Or handle other cases if needed

        self.generation_message.setText("Generating show...")
        QApplication.processEvents()

        try:
            time_offset_ms = self.time_offset_spinbox.value()
            generator = MusicalShowGenerator()
            output_mode = self.output_mode_combobox.currentText().lower()
            cues = generator.generate_musical_show(
                analysis_data={'beat_markers': self.analyzer.get_peak_data()},
                num_outputs=num_outputs,
                output_mode=output_mode,
                time_offset_ms=time_offset_ms,
                selected_peaks=selected_peaks
            )

            if cues:
                self.generation_message.setText(f"Generated {len(cues)} cues successfully.")

                if self.cue_table is None:
                    self._handle_error("Cue table reference is missing.")
                    return

                table_model = self.cue_table.model
                table_model.beginResetModel()
                table_model._data.clear()
                table_model.endResetModel()

                table_model.beginInsertRows(QModelIndex(), 0, len(cues) - 1)
                table_model._data.extend(cues)
                table_model.endInsertRows()

                if self.led_panel:
                    self.led_panel.updateFromCueData(table_model._data, force_refresh=True)
                else:
                    self.logger.warning("LED panel reference is missing, cannot update.")
            else:
                self.generation_message.setText("Failed to generate cues.")

        except Exception as e:
            self._handle_error(f"Error generating show: {str(e)}")
            traceback.print_exc()
        finally:
            QApplication.processEvents()

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
                padding: 8px 15px;
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
        playback_group = QGroupBox("Playback Controls")
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

        # Zoom controls
        zoom_layout = QHBoxLayout()

        self.zoom_out_btn = QPushButton("Zoom Out")
        self.zoom_out_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowLeft))
        self.zoom_out_btn.setEnabled(False)
        zoom_layout.addWidget(self.zoom_out_btn)

        self.zoom_label = QLabel("1.0x")
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_label.setStyleSheet("font-weight: bold;")
        self.zoom_label.setMinimumWidth(60)
        zoom_layout.addWidget(self.zoom_label)

        self.zoom_in_btn = QPushButton("Zoom In")
        self.zoom_in_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowRight))
        self.zoom_in_btn.setEnabled(False)
        zoom_layout.addWidget(self.zoom_in_btn)

        playback_layout.addLayout(zoom_layout)

        # Zoom slider
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(0, 100)
        self.zoom_slider.setValue(50)
        self.zoom_slider.setEnabled(False)
        playback_layout.addWidget(self.zoom_slider)

        # Reset zoom button
        self.reset_zoom_btn = QPushButton("Reset Zoom")
        self.reset_zoom_btn.setEnabled(False)
        playback_layout.addWidget(self.reset_zoom_btn)

        return playback_group

    def _create_beat_detection_group(self) -> QGroupBox:
        """
        Create the beat detection analysis group

        Returns:
            QGroupBox containing beat detection information
        """
        beat_group = QGroupBox("Beat Detection Analysis")
        beat_layout = QVBoxLayout(beat_group)

        # Total peaks display
        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel("Total Peaks:"))
        self.total_peak_count = QLabel("0")
        self.total_peak_count.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.total_peak_count.setStyleSheet("font-weight: bold; color: #2980b9; font-size: 14px;")
        total_layout.addWidget(self.total_peak_count)
        beat_layout.addLayout(total_layout)

        return beat_group

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
        """Resize dialog to optimal size based on screen dimensions"""
        from PySide6.QtWidgets import QApplication

        # Get primary screen
        screen = QApplication.primaryScreen()
        if not screen:
            screen = QApplication.screens()[0] if QApplication.screens() else None

        if screen:
            # Get available geometry
            geometry = screen.availableGeometry()

            # Use 90% of screen width and height
            width = int(geometry.width() * 0.9)
            height = int(geometry.height() * 0.9)

            # Center the dialog
            x = geometry.x() + (geometry.width() - width) // 2
            y = geometry.y() + (geometry.height() - height) // 2

            self.setGeometry(x, y, width, height)
        else:
            # Fallback size if screen information is not available
            self.resize(1024, 768)

    def _connect_signals(self) -> None:
        """Connect all signals and slots"""
        # Time slider connections
        self.time_slider.valueChanged.connect(self._on_time_slider_changed)

        # Zoom control connections
        self.zoom_in_btn.clicked.connect(self._on_zoom_in)
        self.zoom_out_btn.clicked.connect(self._on_zoom_out)
        self.reset_zoom_btn.clicked.connect(self._on_reset_zoom)
        self.zoom_slider.valueChanged.connect(self._on_zoom_slider_changed)

        # Playback control connections
        self.play_btn.clicked.connect(self._on_play)
        self.pause_btn.clicked.connect(self._on_pause)
        self.stop_btn.clicked.connect(self._on_stop)

        # Media player connections
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.player.positionChanged.connect(self._on_player_position_changed)

        # Waveform view connections
        self.waveform_view.zoom_changed.connect(self._on_view_zoom_changed)
        self.waveform_view.position_changed.connect(self._on_view_position_changed)

        # Select all peaks connections
        self.select_all_checkbox.stateChanged.connect(self._on_select_all_changed)

    def load_waveform_data(self) -> None:
        """Load and process the waveform data"""
        if not self.music_file_info or 'path' not in self.music_file_info:
            QMessageBox.warning(self, "Error", "No valid music file information provided.")
            return

        file_path = Path(self.music_file_info['path'])
        if not file_path.exists():
            QMessageBox.warning(self, "Error", f"File not found: {file_path}")
            return

        # Show loading state
        self.progress_bar.setVisible(True)
        self.title_label.setText(f"Loading: {file_path.name}...")
        self.is_processing = True

        try:
            # Load the file in the analyzer
            if not self.analyzer.load_file(file_path):
                QMessageBox.warning(self, "Error", f"Could not load file: {file_path}")
                self.progress_bar.setVisible(False)
                self.is_processing = False
                return

            # Process the waveform data
            self.analyzer.process_waveform(self._on_waveform_loaded_safe)

        except Exception as e:
            self.logger.error(f"Error loading waveform data: {str(e)}")
            QMessageBox.warning(self, "Error", f"Error loading waveform: {str(e)}")
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
            QMessageBox.warning(self, "Error", "Could not process waveform data.")
            return

        try:
            # Update title
            if self.music_file_info:
                title = f"Waveform: {self.music_file_info['filename']} - {self.music_file_info['duration']}"
                self.title_label.setText(title)

            # Create analysis info
            analysis_info = self._create_analysis_info()

            if self.analyzer and self.analyzer.is_analyzed:
                self.waveform_view.set_analyzer(self.analyzer)
                # Force an immediate update
                self.waveform_view.update()

                # Initialize UI state
                self._init_playback_state()
                self._enable_controls()
                self._update_duration_display()

                # Set up media player
                self._setup_media_player()

                # Force initial peak display
                self._force_peak_display()

                # Emit ready signal
                self.show_generation_ready.emit(analysis_info)

                # Set maximum value for outputs_spinbox based on detected peaks
                if success and self.analyzer and hasattr(self.analyzer, 'peaks'):
                    max_outputs = len(self.analyzer.peaks)
                    self.outputs_spinbox.setMaximum(max_outputs)
                    self.outputs_spinbox.setEnabled(True)
                    self.outputs_spinbox.setValue(min(10, max_outputs))

                    self.logger.info(f"Set maximum outputs to {max_outputs}")
            else:
                self.logger.error("Analyzer not ready or not analyzed")
                QMessageBox.warning(self, "Error", "Waveform analysis incomplete")

        except Exception as e:
            self.logger.error(f"Error in waveform loading completion: {str(e)}", exc_info=True)
            QMessageBox.warning(self, "Error", f"Error setting up waveform: {str(e)}")

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
        self.zoom_in_btn.setEnabled(True)
        self.zoom_out_btn.setEnabled(True)
        self.reset_zoom_btn.setEnabled(True)
        self.zoom_slider.setEnabled(True)
        self.play_btn.setEnabled(True)

    def _setup_media_player(self) -> None:
        """Set up the media player with the current file"""
        if not self.music_file_info or 'path' not in self.music_file_info:
            return

        file_path = Path(self.music_file_info['path'])
        if file_path.exists():
            self.player.setSource(QUrl.fromLocalFile(str(file_path)))
            self.audio_output.setVolume(1.0)

    def _force_peak_display(self) -> None:
        """Force update of peak detection display"""
        if not self.analyzer or not hasattr(self.analyzer, 'peaks'):
            self.total_peak_count.setText("0")
            return

        peak_count = len(self.analyzer.peaks)
        self.total_peak_count.setText(str(peak_count))
        self.logger.info(f"Updated peak display: {peak_count} peaks")

        # Stop the update timer
        if self.peak_check_timer.isActive():
            self.peak_check_timer.stop()

    def _update_position_display(self, position: float) -> None:
        """
        Update position display with current time

        Args:
            position: Normalized position (0.0-1.0)
        """
        if not self.analyzer or not self.analyzer.is_analyzed:
            self.position_label.setText("Position: 00:00.000")
            return

        time_seconds = position * self.analyzer.duration_seconds
        time_str = self._format_time(time_seconds)
        self.position_label.setText(f"Position: {time_str}")

    def _update_duration_display(self) -> None:
        """Update the duration display"""
        if not self.analyzer or not self.analyzer.is_analyzed:
            self.duration_label.setText("Duration: 00:00.000")
            return

        duration_str = self._format_time(self.analyzer.duration_seconds)
        self.duration_label.setText(f"Duration: {duration_str}")

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
        self.zoom_label.setText(f"{zoom_factor:.1f}x")

        # Update slider without triggering signals
        self.zoom_slider.blockSignals(True)

        # Convert zoom factor to slider value (logarithmic scale)
        log_min = math.log(self.waveform_view.min_zoom)
        log_max = math.log(self.waveform_view.max_zoom)
        log_current = math.log(zoom_factor)

        slider_value = int(((log_current - log_min) / (log_max - log_min)) * 100)
        self.zoom_slider.setValue(slider_value)

        self.zoom_slider.blockSignals(False)

    def _update_peak_info(self) -> None:
        """Update peak detection information display"""
        if not self.analyzer:
            self.total_peak_count.setText("0")
            return

        if hasattr(self.analyzer, 'peaks'):
            peak_count = len(self.analyzer.peaks)
            if peak_count > 0:
                self.total_peak_count.setText(str(peak_count))
                self.logger.info(f"Updated peak count display: {peak_count}")
                if self.peak_check_timer.isActive():
                    self.peak_check_timer.stop()
            else:
                # Keep checking if peaks are still being detected
                if hasattr(self.analyzer, 'is_processing') and self.analyzer.is_processing:
                    self.total_peak_count.setText("Analyzing...")
                else:
                    # Check if peaks are in detected_peaks
                    if hasattr(self.analyzer, 'detected_peaks') and self.analyzer.detected_peaks:
                        peak_count = len(self.analyzer.detected_peaks)
                        self.total_peak_count.setText(str(peak_count))
                        self.logger.info(f"Updated peak count from detected_peaks: {peak_count}")
                        if self.peak_check_timer.isActive():
                            self.peak_check_timer.stop()

    def _on_play(self) -> None:
        """Handle play button click"""
        if not self.analyzer or not self.analyzer.is_analyzed:
            return

        if not self.music_file_info or 'path' not in self.music_file_info:
            QMessageBox.warning(self, "Error", "No audio file available for playback.")
            return

        # If already playing, do nothing
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            return

        # If starting fresh or after stop
        if self.player.source().isEmpty() or self.player.playbackState() == QMediaPlayer.StoppedState:
            file_path = Path(self.music_file_info['path'])
            if not file_path.exists():
                QMessageBox.warning(self, "Error", "Audio file not found.")
                return

            self.player.setSource(QUrl.fromLocalFile(str(file_path)))
            self.audio_output.setVolume(1.0)

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

        elif state == QMediaPlayer.PausedState:
            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.position_update_timer.stop()

        else:  # Stopped
            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.position_update_timer.stop()

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
        if not self.analyzer or not self.analyzer.is_analyzed:
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

    def _on_time_slider_changed(self, value: int) -> None:
        """
        Handle time slider value change

        Args:
            value: New slider value (0-1000)
        """
        if not self.analyzer or not self.analyzer.is_analyzed:
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
        Handle zoom slider value change

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
        """Stop all active timers"""
        if hasattr(self, 'position_update_timer'):
            self.position_update_timer.stop()

        if hasattr(self, 'peak_check_timer'):
            self.peak_check_timer.stop()

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
        QMessageBox.warning(self, title, error)

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
                'has_peaks': hasattr(self.analyzer, 'peaks'),
                'peak_count': len(self.analyzer.peaks) if hasattr(self.analyzer, 'peaks') else 0
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

    def set_analyzer(self, analyzer: WaveformAnalyzer) -> None:
        """Set the analyzer instance and update the view"""
        self.analyzer = analyzer
        self.logger.info("Setting analyzer in WaveformAnalysisDialog")

        if self.analyzer:
            self.analyzer.peak_detection_complete.connect(self._update_after_peak_detection)
            self.logger.info(f"Analyzer state - analyzed: {self.analyzer.is_analyzed}, "
                             f"has_data: {hasattr(self.analyzer, 'waveform_data')}")

            # Start processing if needed
            if not self.analyzer.is_analyzed:
                self.load_waveform_data()
            else:
                # Analyzer is already processed, update UI
                if hasattr(self, 'waveform_view'):
                    self.logger.info("Setting analyzer in waveform view")
                    self.waveform_view.set_analyzer(self.analyzer)

                    # Force immediate update of UI
                    self._init_playback_state()
                    self._enable_controls()
                    self._update_duration_display()
                    self._force_peak_display()

                    # Update the view
                    self.waveform_view.update()

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

    @Slot()  # Add this decorator
    def _update_after_peak_detection(self) -> None:
        """Update UI after peak detection completes"""
        if self.analyzer and hasattr(self.analyzer, 'peaks'):
            peak_count = len(self.analyzer.peaks)
            self.logger.info(f"Updating display with {peak_count} peaks")
            self.total_peak_count.setText(str(peak_count))

            # Force update of waveform view to show peak markers
            if hasattr(self, 'waveform_view'):
                self.waveform_view.update()

            # Get the total number of peaks
            peak_count = len(self.analyzer.peaks) if self.analyzer and self.analyzer.peaks else 0
            self.total_peak_count = peak_count

            # Update the spinbox maximum to be the lesser of peak_count or 1000
            max_outputs = min(peak_count, 1000) if peak_count > 0 else 1000
            self.outputs_spinbox.setMaximum(max_outputs)

            # Ensure current value doesn't exceed the new maximum
            if self.outputs_spinbox.value() > max_outputs:
                self.outputs_spinbox.setValue(max_outputs)

    def clear_cues_from_table(self, table):
        """Clear existing cues from the cue table."""
        while table.rowCount() > 0:
            table.removeRow(0)

    def add_cues_to_table(self, cues: List[List], table):
        """Add generated cues to the cue table."""
        for cue in cues:
            row_count = table.rowCount()
            table.insertRow(row_count)
            for col, value in enumerate(cue):
                table.setItem(row_count, col, QTableWidgetItem(str(value)))
