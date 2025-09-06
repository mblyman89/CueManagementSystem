"""
Enhanced Music Analysis Dialog with Spleeter Integration
=======================================================

This is an enhanced version of the MusicAnalysisDialog that integrates Spleeter
audio separation capabilities. It maintains backward compatibility while adding
the ability to automatically separate audio into stems and analyze the drum track.

Key Features:
- Automatic audio separation using Spleeter
- Drum track extraction and analysis
- Progress tracking and user feedback
- Graceful fallback to original workflow
- Error handling and recovery

Author: NinjaTeach AI Team
Version: 1.0.0
License: MIT
"""

import logging
import traceback
from pathlib import Path
import time
import os

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFileDialog, QFrame, QGroupBox,
                               QFormLayout, QDialogButtonBox, QMessageBox,
                               QCheckBox, QProgressBar, QTextEdit)
from PySide6.QtCore import Qt, Signal, QTimer
import wave
import datetime

# Import the Spleeter service
from utils.audio.spleeter_service import SpleeterService, validate_audio_file, SeparationResult

# Import existing components
from utils.audio.waveform_analyzer import WaveformAnalyzer, Peak
from utils.audio.performance_monitor import profile_method, monitor


class MusicAnalysisDialog(QDialog):
    """
    Enhanced Music Analysis Dialog with Spleeter Integration

    This dialog extends the original MusicAnalysisDialog to include automatic
    audio separation capabilities using Spleeter. When enabled, it will:
    1. Separate the selected audio file into 5 stems
    2. Automatically select the drum track for analysis
    3. Load the drum track into the waveform analysis dialog

    The dialog maintains full backward compatibility and gracefully falls back
    to the original workflow if Spleeter is not available or fails.
    """

    # Signal emitted when analysis is ready to proceed
    analysis_ready = Signal(dict)

    def __init__(self, parent=None, led_panel=None, cue_table=None):
        super().__init__(parent)
        self.setWindowTitle("Music Analysis with Audio Separation")
        self.setMinimumWidth(700)
        self.setMinimumHeight(781)

        # Keep dialog on top of main window
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        print("🎵 Initializing Music Analysis Dialog with Spleeter")

        # Configure logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Store music file data and references
        self.music_file_info = None
        self.led_panel = led_panel
        self.cue_table = cue_table
        self.separated_stems = None
        self.separation_result = None

        # Create Spleeter service
        self.spleeter_service = SpleeterService(self)
        self._setup_spleeter_signals()

        # Create optimized analyzer instance
        print("🔧 Creating optimized WaveformAnalyzer instance")
        self.analyzer = WaveformAnalyzer()

        # Performance tracking
        self.dialog_start_time = time.time()

        # Initialize UI
        self.init_ui()

    def _setup_spleeter_signals(self):
        """Setup Spleeter service signal connections"""
        self.spleeter_service.separation_started.connect(self._on_separation_started)
        self.spleeter_service.separation_progress.connect(self._on_separation_progress)
        self.spleeter_service.separation_completed.connect(self._on_separation_completed)
        self.spleeter_service.separation_failed.connect(self._on_separation_failed)

    def init_ui(self):
        """Initialize the enhanced UI components"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Title label
        title_label = QLabel("Music Analysis with Audio Separation")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Check Spleeter availability and show status
        self._add_spleeter_status(main_layout)

        # Description
        description = QLabel(
            "Select a .wav music file to analyze for firework show generation. "
            "With audio separation enabled, the system will automatically extract "
            "the drum track for more precise analysis and synchronization."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("margin-bottom: 15px;")
        main_layout.addWidget(description)

        # Spleeter configuration section
        self._add_spleeter_config(main_layout)

        # File selection area
        self._add_file_selection(main_layout)

        # Separation progress area (initially hidden)
        self._add_separation_progress(main_layout)

        # Analysis note
        analysis_note = QLabel(
            "Note: Audio separation may take 30-60 seconds depending on file size. "
            "The separated drum track will provide more accurate beat detection. "
            "Only .wav files are currently supported for separation."
        )
        analysis_note.setWordWrap(True)
        analysis_note.setStyleSheet("color: gray; font-style: italic; margin-top: 10px;")
        main_layout.addWidget(analysis_note)

        # Button layout
        self._add_dialog_buttons(main_layout)

    def _add_spleeter_status(self, layout):
        """Add Spleeter availability status indicator"""
        status_group = QGroupBox("Audio Separation Status")
        status_layout = QVBoxLayout()

        # Check Spleeter availability
        available, message = self.spleeter_service.check_spleeter_availability()

        status_label = QLabel(message)
        if available:
            status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            icon = "✅"
        else:
            status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            icon = "❌"

        status_text = QLabel(f"{icon} {message}")
        status_text.setStyleSheet(status_label.styleSheet())
        status_layout.addWidget(status_text)

        # Add installation help if not available
        if not available:
            help_text = QLabel(
                "To enable audio separation, install Spleeter:\n"
                "1. conda install -c conda-forge ffmpeg libsndfile\n"
                "2. pip install spleeter"
            )
            help_text.setStyleSheet("color: #7f8c8d; font-family: monospace; font-size: 10px;")
            status_layout.addWidget(help_text)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

    def _add_spleeter_config(self, layout):
        """Add Spleeter configuration options"""
        config_group = QGroupBox("Audio Separation Settings")
        config_layout = QVBoxLayout()

        # Enable/disable separation
        self.enable_separation = QCheckBox("Enable Audio Separation (Recommended)")
        available, _ = self.spleeter_service.check_spleeter_availability()
        self.enable_separation.setChecked(available)
        self.enable_separation.setEnabled(available)
        self.enable_separation.setToolTip(
            "Automatically separate audio into drums, bass, vocals, piano, and other tracks"
        )
        config_layout.addWidget(self.enable_separation)

        # Auto-select drums option
        self.auto_select_drums = QCheckBox("Automatically analyze drum track")
        self.auto_select_drums.setChecked(True)
        self.auto_select_drums.setToolTip(
            "Automatically load the separated drum track for analysis"
        )
        config_layout.addWidget(self.auto_select_drums)

        # Save stems option
        self.save_stems = QCheckBox("Save separated audio files")
        self.save_stems.setChecked(False)
        self.save_stems.setToolTip(
            "Keep the separated audio files for future use"
        )
        config_layout.addWidget(self.save_stems)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

    def _add_file_selection(self, layout):
        """Add file selection area"""
        file_group = QGroupBox("Select Music File")
        file_layout = QVBoxLayout()

        # File selection button
        file_btn_layout = QHBoxLayout()
        self.file_path_label = QLabel("No file selected")
        self.file_path_label.setStyleSheet("color: gray; font-style: italic;")
        self.select_file_btn = QPushButton("Select .WAV File")
        self.select_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: white;
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
        """)
        self.select_file_btn.clicked.connect(self.select_music_file)

        file_btn_layout.addWidget(self.file_path_label)
        file_btn_layout.addWidget(self.select_file_btn)
        file_layout.addLayout(file_btn_layout)

        # Horizontal separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        file_layout.addWidget(separator)

        # File information area
        self.file_info_group = QGroupBox("Music File Information")
        self.file_info_group.setVisible(False)

        file_info_layout = QFormLayout()
        self.filename_label = QLabel("--")
        self.duration_label = QLabel("--")
        self.channels_label = QLabel("--")
        self.sample_rate_label = QLabel("--")
        self.file_size_label = QLabel("--")

        file_info_layout.addRow("Filename:", self.filename_label)
        file_info_layout.addRow("Duration:", self.duration_label)
        file_info_layout.addRow("Channels:", self.channels_label)
        file_info_layout.addRow("Sample Rate:", self.sample_rate_label)
        file_info_layout.addRow("File Size:", self.file_size_label)

        self.file_info_group.setLayout(file_info_layout)
        file_layout.addWidget(self.file_info_group)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

    def _add_separation_progress(self, layout):
        """Add separation progress area"""
        self.progress_group = QGroupBox("Audio Separation Progress")
        self.progress_group.setVisible(False)
        progress_layout = QVBoxLayout()

        # Progress bar
        self.separation_progress_bar = QProgressBar()
        self.separation_progress_bar.setRange(0, 100)
        self.separation_progress_bar.setValue(0)
        progress_layout.addWidget(self.separation_progress_bar)

        # Progress label
        self.progress_label = QLabel("Ready to start separation...")
        progress_layout.addWidget(self.progress_label)

        # Separation results (initially hidden)
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(100)
        self.results_text.setVisible(False)
        progress_layout.addWidget(self.results_text)

        self.progress_group.setLayout(progress_layout)
        layout.addWidget(self.progress_group)

    def _add_dialog_buttons(self, layout):
        """Add dialog buttons"""
        button_layout = QHBoxLayout()

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        # Load Drum Stem button
        self.load_drum_btn = QPushButton("Load Drum Stem")
        self.load_drum_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        self.load_drum_btn.clicked.connect(self.load_drum_stem)

        # Analyze button
        self.analyze_btn = QPushButton("Start Analysis")
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.analyze_btn.clicked.connect(self.start_analysis)

        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.load_drum_btn)
        button_layout.addWidget(self.analyze_btn)

        layout.addLayout(button_layout)

    @profile_method("select_music_file")
    def select_music_file(self):
        """Enhanced file selection with validation"""
        print("📂 Opening enhanced file selection dialog")

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Music File",
            "",
            "WAV Files (*.wav);;All Audio Files (*.wav *.mp3 *.flac *.m4a)"
        )

        if file_path:
            # Validate file
            valid, message = validate_audio_file(file_path)
            if not valid:
                QMessageBox.warning(self, "Invalid File", f"File validation failed:\n{message}")
                return

            try:
                print(f"🎵 Loading file info for: {os.path.basename(file_path)}")
                load_start = time.time()

                # Get file info
                file_info = self.get_wav_file_info(file_path)
                self.music_file_info = file_info

                load_time = time.time() - load_start
                print(f"⚡ File info loaded in {load_time:.3f}s")

                # Update UI
                self.file_path_label.setText(os.path.basename(file_path))
                self.file_path_label.setStyleSheet("font-weight: bold;")

                # Update file information
                self.filename_label.setText(file_info['filename'])
                self.duration_label.setText(file_info['duration'])
                self.channels_label.setText(file_info['channels'])
                self.sample_rate_label.setText(file_info['sample_rate'])
                self.file_size_label.setText(file_info['file_size'])

                # Show file info group
                self.file_info_group.setVisible(True)

                # Enable analyze button
                self.analyze_btn.setEnabled(True)

                # Update button text based on separation settings
                if self.enable_separation.isChecked():
                    self.analyze_btn.setText("Start Separation & Analysis")
                else:
                    self.analyze_btn.setText("Start Analysis")

            except Exception as e:
                QMessageBox.warning(self, "File Error", f"Error reading audio file: {str(e)}")
                print(f"Error reading audio file: {str(e)}")

    def start_analysis(self):
        """Start the analysis process (with or without separation)"""
        if not self.music_file_info:
            QMessageBox.warning(self, "No File Selected", "Please select a music file to analyze.")
            return

        try:
            if self.enable_separation.isChecked():
                # Start with audio separation
                self._start_audio_separation()
            else:
                # Skip separation and go directly to analysis
                self._start_direct_analysis()

        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Could not start analysis: {str(e)}")

    def _start_audio_separation(self):
        """Start the audio separation process"""
        print("🎵 Starting audio separation process")

        # Show progress group
        self.progress_group.setVisible(True)

        # Disable controls during separation
        self.select_file_btn.setEnabled(False)
        self.analyze_btn.setEnabled(False)

        # Configure output directory
        output_dir = None
        if self.save_stems.isChecked():
            # Save to same directory as original file
            original_path = Path(self.music_file_info['path'])
            output_dir = str(original_path.parent / f"{original_path.stem}_stems")

        # Start separation
        self.spleeter_service.separate_audio_async(
            self.music_file_info['path'],
            output_dir,
            show_progress=False  # We handle progress ourselves
        )

    def _start_direct_analysis(self):
        """Start analysis without separation (original workflow)"""
        print("🎵 Starting direct analysis (no separation)")
        self._open_waveform_analysis_dialog(self.music_file_info['path'])

    def _on_separation_started(self):
        """Handle separation started signal"""
        print("🎵 Audio separation started")
        self.progress_label.setText("Starting audio separation...")
        self.separation_progress_bar.setValue(0)

    def _on_separation_progress(self, message: str, percentage: int):
        """Handle separation progress updates"""
        print(f"🎵 Separation progress: {percentage}% - {message}")
        self.progress_label.setText(message)
        self.separation_progress_bar.setValue(percentage)

    def _on_separation_completed(self, result: SeparationResult):
        """Handle successful separation completion"""
        print(f"✅ Audio separation completed in {result.processing_time:.2f}s")

        self.separation_result = result
        self.separated_stems = result.stems

        # Update progress
        self.progress_label.setText(f"Separation completed! Generated {len(result.stems)} stems")
        self.separation_progress_bar.setValue(100)

        # Show results
        self.results_text.setVisible(True)
        results_text = f"Separation completed in {result.processing_time:.2f} seconds\n"
        results_text += f"Generated stems: {', '.join(result.stems.keys())}\n"

        if 'drums' in result.stems:
            results_text += f"Drum track: {os.path.basename(result.stems['drums'])}"

        self.results_text.setPlainText(results_text)

        # Automatically proceed to analysis
        QTimer.singleShot(1000, self._proceed_to_analysis)

    def _on_separation_failed(self, error_message: str):
        """Handle separation failure"""
        print(f"❌ Audio separation failed: {error_message}")

        self.progress_label.setText(f"Separation failed: {error_message}")
        self.separation_progress_bar.setValue(0)

        # Re-enable controls
        self.select_file_btn.setEnabled(True)
        self.analyze_btn.setEnabled(True)

        # Show error and offer fallback
        reply = QMessageBox.question(
            self,
            "Separation Failed",
            f"Audio separation failed:\n{error_message}\n\n"
            "Would you like to proceed with analysis using the original file?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._start_direct_analysis()

    def _proceed_to_analysis(self):
        """Proceed to waveform analysis after successful separation"""
        if self.auto_select_drums.isChecked() and 'drums' in self.separated_stems:
            # Use separated drum track
            drum_path = self.separated_stems['drums']
            print(f"🥁 Using separated drum track: {drum_path}")

            # Create modified file info for drum track
            drum_file_info = self.music_file_info.copy()
            drum_file_info['path'] = drum_path
            drum_file_info['filename'] = f"Drums - {drum_file_info['filename']}"
            drum_file_info['is_separated'] = True
            drum_file_info['original_file'] = self.music_file_info['path']
            drum_file_info['separation_result'] = self.separation_result

            self._open_waveform_analysis_dialog(drum_path, drum_file_info)
        else:
            # Use original file
            self._open_waveform_analysis_dialog(self.music_file_info['path'])

    def _open_waveform_analysis_dialog(self, file_path: str, file_info: dict = None):
        """Open the waveform analysis dialog"""
        try:
            from views.dialogs.waveform_analysis_dialog import WaveformAnalysisDialog

            # Use provided file_info or default to original
            analysis_file_info = file_info or self.music_file_info

            # Check if cue_table reference exists
            if self.cue_table is None:
                self.logger.error("Cue table reference is missing.")
                QMessageBox.critical(self, "Error",
                                     "Cue table reference is missing. Please try again from the main window.")
                return

            print("🎛️ Opening waveform analysis dialog")
            waveform_dialog = WaveformAnalysisDialog(analysis_file_info, self, self.led_panel, self.cue_table)

            # Create analyzer for the selected file
            from utils.audio.waveform_analyzer import WaveformAnalyzer as ComprehensiveAnalyzer
            comprehensive_analyzer = ComprehensiveAnalyzer()

            # Load the file into the analyzer
            if comprehensive_analyzer.load_file(file_path):
                print("🎵 File loaded into comprehensive analyzer")
                waveform_dialog.set_analyzer(comprehensive_analyzer)
            else:
                print("⚠️ Failed to load file into comprehensive analyzer, using fallback")
                waveform_dialog.set_analyzer(self.analyzer)

            waveform_dialog.show_generation_ready.connect(self.handle_waveform_ready)

            # Show waveform dialog and close this dialog
            waveform_dialog.showMaximized()
            QTimer.singleShot(100, self.accept)

        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Could not open waveform analysis: {str(e)}")

    def handle_waveform_ready(self, music_file_info):
        """Handle the signal from waveform dialog when analysis is ready"""
        try:
            # Ensure we have valid music file info
            if not music_file_info:
                print("Warning: Received empty music file info")
                music_file_info = {'filename': 'Unknown', 'duration': '0:00'}

            # Get peak data from analyzer
            peak_data = []
            if self.analyzer and self.analyzer.peaks:
                peak_data = [
                    {
                        'time': peak.time,
                        'time_str': peak.time_str,
                        'amplitude': peak.amplitude
                    }
                    for peak in self.analyzer.peaks
                ]

            # Create complete analysis data dictionary
            analysis_data = {
                'music_file': music_file_info,
                'beat_markers': peak_data,
                'section_markers': [],
                'peak_count': len(peak_data),
                'analyzer_state': {
                    'is_analyzed': self.analyzer.is_analyzed if self.analyzer else False,
                    'sample_rate': self.analyzer.sample_rate if self.analyzer else 0,
                    'duration': self.analyzer.duration_seconds if self.analyzer else 0
                },
                'separation_info': {
                    'was_separated': self.separation_result is not None,
                    'stems_available': list(self.separated_stems.keys()) if self.separated_stems else [],
                    'processing_time': self.separation_result.processing_time if self.separation_result else 0
                }
            }

            print(f"Analysis complete for {music_file_info.get('filename', 'Unknown')}")
            print(f"Found {len(peak_data)} peaks")
            if self.separation_result:
                print(f"Used separated audio with {len(self.separated_stems)} stems")

            # Emit our signal with the complete analysis data
            self.analysis_ready.emit(analysis_data)

        except Exception as e:
            print(f"Error in handle_waveform_ready: {str(e)}")
            import traceback
            traceback.print_exc()

    def get_wav_file_info(self, file_path):
        """Extract information from a WAV file using WaveformAnalyzer"""
        file_info = {}

        try:
            # Use the analyzer to load the file
            if self.analyzer.load_file(file_path):
                # Basic file info
                file_info['path'] = file_path
                file_info['filename'] = os.path.basename(file_path)

                # Get file size
                size_bytes = os.path.getsize(file_path)
                file_info['file_size'] = self.format_file_size(size_bytes)

                # Get audio information from analyzer
                file_info['channels'] = str(self.analyzer.channels) + \
                                        (" (Stereo)" if self.analyzer.channels == 2 else " (Mono)")
                file_info['sample_rate'] = f"{self.analyzer.sample_rate} Hz"
                file_info['duration'] = str(datetime.timedelta(
                    seconds=int(self.analyzer.duration_seconds)))
                file_info['duration_seconds'] = self.analyzer.duration_seconds

                return file_info
            else:
                raise Exception("Failed to load WAV file in analyzer")

        except Exception as e:
            print(f"Error getting WAV file info: {str(e)}")
            # Fallback to basic wave module if analyzer fails
            return self._get_basic_wav_info(file_path)

    def _get_basic_wav_info(self, file_path):
        """Fallback method for basic WAV file information"""
        file_info = {}
        file_info['path'] = file_path
        file_info['filename'] = os.path.basename(file_path)
        size_bytes = os.path.getsize(file_path)
        file_info['file_size'] = self.format_file_size(size_bytes)

        with wave.open(file_path, 'rb') as wav_file:
            channels = wav_file.getnchannels()
            file_info['channels'] = str(channels) + (" (Stereo)" if channels == 2 else " (Mono)")
            sample_rate = wav_file.getframerate()
            file_info['sample_rate'] = f"{sample_rate} Hz"
            frames = wav_file.getnframes()
            duration_seconds = frames / float(sample_rate)
            file_info['duration'] = str(datetime.timedelta(seconds=int(duration_seconds)))
            file_info['duration_seconds'] = duration_seconds

        return file_info

    def format_file_size(self, size_bytes):
        """Format file size in human-readable format"""
        if size_bytes == 0:
            return "0 B"

        units = ['B', 'KB', 'MB', 'GB']
        i = 0

        while size_bytes >= 1024 and i < len(units) - 1:
            size_bytes /= 1024
            i += 1

        return f"{size_bytes:.1f} {units[i]}"

    def load_drum_stem(self):
        """Allow direct loading of a drum stem file for waveform analysis"""
        print("🥁 Opening drum stem file selection dialog")

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Drum Stem File",
            "",
            "WAV Files (*.wav);;All Audio Files (*.wav *.mp3 *.flac *.m4a)"
        )

        if file_path:
            # Validate file
            valid, message = validate_audio_file(file_path)
            if not valid:
                QMessageBox.warning(self, "Invalid File", f"File validation failed:\n{message}")
                return

            try:
                print(f"🥁 Loading drum stem file: {os.path.basename(file_path)}")

                # Get file info
                file_info = self.get_wav_file_info(file_path)

                # Create a modified file info dictionary specifically for drum stem
                drum_file_info = file_info.copy()
                drum_file_info['is_drum_stem'] = True
                drum_file_info['filename'] = f"Drum Stem - {file_info['filename']}"

                # Open the waveform analysis dialog with the drum stem file
                self._open_waveform_analysis_dialog(file_path, drum_file_info)

            except Exception as e:
                QMessageBox.warning(self, "File Error", f"Error reading drum stem file: {str(e)}")
                print(f"Error reading drum stem file: {str(e)}")

    def closeEvent(self, event):
        """Handle dialog close event"""
        try:
            # Clean up Spleeter service
            if hasattr(self, 'spleeter_service'):
                self.spleeter_service.cleanup_temp_files()

            event.accept()
        except Exception as e:
            print(f"Error during dialog cleanup: {str(e)}")
            event.accept()
