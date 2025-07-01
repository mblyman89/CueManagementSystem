import logging
import traceback
from pathlib import Path
import time

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFileDialog, QFrame, QGroupBox,
                               QFormLayout, QDialogButtonBox, QMessageBox)
from PySide6.QtCore import Qt, Signal, QTimer
import os
import wave
import datetime
from utils.audio.waveform_analyzer import WaveformAnalyzer, Peak
from utils.audio.performance_monitor import profile_method, monitor


class MusicAnalysisDialog(QDialog):
    """
    OPTIMIZED: Dialog for analyzing music files for show generation

    Features:
    - Select .wav music file for analysis
    - Display file information with performance monitoring
    - Optimized beats and patterns analysis for show generation
    - Background processing with immediate UI feedback
    """

    # Signal emitted when analysis is ready to proceed
    analysis_ready = Signal(dict)

    def __init__(self, parent=None, led_panel=None, cue_table=None):
        super().__init__(parent)
        self.setWindowTitle("Optimized Music Analysis for Show Generation")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        # Keep dialog on top of main window
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        print("🎛️ Initializing OptimizedMusicAnalysisDialog")

        # Configure logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Store music file data and references to led_panel and cue_table
        self.music_file_info = None
        self.led_panel = led_panel  # Store the reference
        self.cue_table = cue_table

        # OPTIMIZATION: Create optimized analyzer instance
        print("🔧 Creating optimized WaveformAnalyzer instance")
        self.analyzer = WaveformAnalyzer()

        # OPTIMIZATION: Performance tracking
        self.dialog_start_time = time.time()

        # Initialize UI
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Title label
        title_label = QLabel("Generate Show From Music")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Check if librosa is available and show warning if not
        if hasattr(self.analyzer, 'LIBROSA_AVAILABLE') and not self.analyzer.LIBROSA_AVAILABLE:
            warning_label = QLabel("Warning: Advanced audio analysis is limited (librosa not available)")
            warning_label.setStyleSheet("color: #e74c3c; font-weight: bold; margin-bottom: 10px;")
            warning_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(warning_label)

        # Description
        description = QLabel(
            "Select a .wav music file to analyze for firework show generation. "
            "The system will analyze the music's beats and patterns to create "
            "a synchronized firework show."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("margin-bottom: 15px;")
        main_layout.addWidget(description)

        # File selection area
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
        self.file_info_group.setVisible(False)  # Hide initially

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
        main_layout.addWidget(file_group)

        # Analysis note
        analysis_note = QLabel(
            "Note: Music analysis may take several seconds depending on file size. "
            "Only .wav files are currently supported for analysis."
        )
        analysis_note.setWordWrap(True)
        analysis_note.setStyleSheet("color: gray; font-style: italic; margin-top: 10px;")
        main_layout.addWidget(analysis_note)

        # Custom button layout to ensure correct positioning
        button_layout = QHBoxLayout()

        # Cancel button (left side)
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

        # Generate Waveform button (right side)
        self.analyze_btn = QPushButton("Generate Waveform")
        self.analyze_btn.setEnabled(False)  # Disabled until file selected
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
        self.analyze_btn.clicked.connect(self.analyze_music)

        # Add buttons to layout: Cancel on left, spacer, Generate Waveform on right
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()  # This pushes buttons to opposite sides
        button_layout.addWidget(self.analyze_btn)

        main_layout.addLayout(button_layout)

    @profile_method("select_music_file")
    def select_music_file(self):
        """OPTIMIZED: Open file dialog to select a music file with performance monitoring"""
        print("📂 Opening optimized file selection dialog")

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Music File",
            "",  # Default directory
            "WAV Files (*.wav)"  # Only allow .wav files
        )

        if file_path:
            # Check if it's a valid WAV file
            if not file_path.lower().endswith('.wav'):
                QMessageBox.warning(self, "Invalid File", "Please select a valid .wav file.")
                return

            try:
                print(f"🎵 Loading file info for: {os.path.basename(file_path)}")
                load_start = time.time()

                # Get file info
                file_info = self.get_wav_file_info(file_path)

                # Store file info
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

            except Exception as e:
                QMessageBox.warning(self, "File Error", f"Error reading WAV file: {str(e)}")
                print(f"Error reading WAV file: {str(e)}")

    def format_file_size(self, size_bytes):
        """Format file size in human-readable format"""
        # Handle zero size
        if size_bytes == 0:
            return "0 B"

        # Define size units and their names
        units = ['B', 'KB', 'MB', 'GB']
        i = 0

        # Find appropriate unit
        while size_bytes >= 1024 and i < len(units) - 1:
            size_bytes /= 1024
            i += 1

        # Return formatted size with unit
        return f"{size_bytes:.1f} {units[i]}"

    def get_wav_file_info(self, file_path):
        """
        Extract information from a WAV file using WaveformAnalyzer

        Args:
            file_path: Path to the WAV file

        Returns:
            Dictionary with file information
        """
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

    @profile_method("analyze_music")
    def analyze_music(self):
        """OPTIMIZED: Analyze the selected music file with performance improvements"""
        print("🚀 Starting optimized music analysis workflow")

        if not self.music_file_info:
            QMessageBox.warning(self, "No File Selected", "Please select a music file to analyze.")
            return

        try:
            from views.dialogs.waveform_analysis_dialog import WaveformAnalysisDialog

            # Check if cue_table reference exists
            if self.cue_table is None:
                self.logger.error("Cue table reference is missing.")
                QMessageBox.critical(self, "Error",
                                     "Cue table reference is missing. Please try again from the main window.")
                return

            # OPTIMIZATION: Print performance summary before opening dialog
            if hasattr(self, 'analyzer') and self.analyzer:
                print(f"📊 {monitor.get_performance_summary()}")

            # Pass led_panel and cue_table references to OptimizedWaveformAnalysisDialog
            print("🎛️ Opening optimized waveform analysis dialog")
            waveform_dialog = WaveformAnalysisDialog(self.music_file_info, self, self.led_panel, self.cue_table)

            # Create new comprehensive analyzer for drum detection
            from utils.audio.waveform_analyzer import WaveformAnalyzer as ComprehensiveAnalyzer
            comprehensive_analyzer = ComprehensiveAnalyzer()

            # Load the file into the comprehensive analyzer
            if comprehensive_analyzer.load_file(self.music_file_info['path']):
                print("🎵 File loaded into comprehensive analyzer")
                waveform_dialog.set_analyzer(comprehensive_analyzer)
            else:
                print("⚠️ Failed to load file into comprehensive analyzer, using fallback")
                waveform_dialog.set_analyzer(self.analyzer)

            waveform_dialog.show_generation_ready.connect(self.handle_waveform_ready)

            # CRITICAL FIX: Show waveform dialog BEFORE closing this dialog
            waveform_dialog.showMaximized()  # Show maximized non-modally first

            # Use QTimer to delay closing this dialog to ensure proper display
            QTimer.singleShot(100, self.accept)  # Close this dialog after 100ms delay

        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Could not open waveform analysis: {str(e)}")

    def _show_waveform_dialog(self):
        """Show the waveform analysis dialog with processed analyzer"""
        from views.dialogs.waveform_analysis_dialog import WaveformAnalysisDialog

        # Create waveform dialog
        waveform_dialog = WaveformAnalysisDialog(self.music_file_info, self.parent())

        # Set the analyzer after it's been processed
        waveform_dialog.set_analyzer(self.analyzer)

        # Connect signals
        waveform_dialog.show_generation_ready.connect(self.handle_waveform_ready)

        # Show the waveform analysis dialog first
        waveform_dialog.showMaximized()  # Show maximized non-modally

        # Close this dialog after a short delay
        QTimer.singleShot(100, self.accept)

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
                'beat_markers': peak_data,  # Use detected peaks as beat markers
                'section_markers': [],  # Reserved for future use
                'peak_count': len(peak_data),
                'analyzer_state': {
                    'is_analyzed': self.analyzer.is_analyzed if self.analyzer else False,
                    'sample_rate': self.analyzer.sample_rate if self.analyzer else 0,
                    'duration': self.analyzer.duration_seconds if self.analyzer else 0
                }
            }

            print(f"Analysis complete for {music_file_info.get('filename', 'Unknown')}")
            print(f"Found {len(peak_data)} peaks")

            # Emit our signal with the complete analysis data
            self.analysis_ready.emit(analysis_data)

        except Exception as e:
            print(f"Error in handle_waveform_ready: {str(e)}")
            import traceback
            traceback.print_exc()
