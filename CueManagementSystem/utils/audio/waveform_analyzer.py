#!/usr/bin/env python3
"""
WaveformAnalyzer for beat detection using madmom library.
This module provides a class-based interface for detecting beats in audio files.
"""

# Apply NumPy compatibility fixes before importing madmom
import numpy as np

# Create compatibility aliases for deprecated NumPy types
# These were deprecated in NumPy 1.20 and removed in NumPy 2.0
if not hasattr(np, 'int'):
    np.int = int
if not hasattr(np, 'float'):
    np.float = float

import sys
import os
from dataclasses import dataclass
from typing import List, Tuple, Optional, Callable, Dict, Any, Union
import logging
import soundfile as sf
import time
from pathlib import Path

# Try to import librosa for additional audio processing capabilities
try:
    import librosa
    import librosa.display

    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

from madmom.features.beats import RNNBeatProcessor, DBNBeatTrackingProcessor
from madmom.audio.signal import Signal
from madmom.processors import Processor

# For PySide6 signal/slot mechanism
try:
    from PySide6.QtCore import Signal, QObject
except ImportError:
    # Fallback for testing environments without PySide6
    class QObject:
        pass


    class Signal:
        def __init__(self, *args):
            self.args = args

        def connect(self, func):
            pass

        def disconnect(self, func):
            pass

        def emit(self, *args):
            pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Peak:
    """
    Data class representing a peak in the audio waveform.

    Attributes:
        time (float): Time in seconds when the peak occurs
        amplitude (float): Amplitude of the peak (0.0 to 1.0)
        confidence (float): Confidence score of the peak detection (0.0 to 1.0)
        type (str): Type of peak (e.g., 'kick', 'snare', 'hi-hat', etc.)
    """
    time: float
    amplitude: float = 1.0
    confidence: float = 1.0
    type: str = 'generic'


class WaveformAnalyzer(QObject):
    """
    A class for analyzing audio waveforms and detecting beats using madmom library.

    This class provides a librosa-compatible interface for beat detection while
    leveraging madmom's state-of-the-art algorithms for improved accuracy.
    """

    # Signal emitted when peak detection is complete
    peak_detection_complete = Signal(bool)

    # Flag to indicate if librosa is available
    LIBROSA_AVAILABLE = LIBROSA_AVAILABLE

    def __init__(self):
        """
        Initialize the WaveformAnalyzer with madmom beat detection processors.
        """
        super().__init__()
        logger.info("Initializing WaveformAnalyzer with madmom processors")

        # Create the beat detection processors
        self.beat_processor = RNNBeatProcessor()
        self.beat_tracker = DBNBeatTrackingProcessor(fps=100)

        # Initialize file-related attributes
        self.file_path = None
        self.original_file_path = None  # Store the original file path if this is a stem
        self.is_drum_stem = False  # Flag to indicate if this is a drum stem
        self.waveform_data = None
        self.sample_rate = None
        self.channels = None
        self.duration = None
        self.duration_seconds = None  # Alias for duration for compatibility
        self.is_analyzed = False
        self.peaks = []

        # Additional attributes for compatibility with existing code
        self.peak_data = {}
        self.peak_types = ['generic', 'kick', 'snare', 'hi-hat', 'cymbal', 'tom']
        self.peak_colors = {
            'generic': (255, 255, 255),  # White
            'kick': (255, 0, 0),  # Red
            'snare': (0, 255, 0),  # Green
            'hi-hat': (0, 0, 255),  # Blue
            'cymbal': (255, 255, 0),  # Yellow
            'tom': (255, 0, 255)  # Magenta
        }

        # Performance monitoring
        self.analysis_time = 0
        self.last_analysis_timestamp = 0

        # Settings
        self.settings = {
            'sensitivity': 0.5,
            'min_peak_distance': 0.05,
            'threshold': 0.1,
            'smoothing': 0.1
        }

        # Librosa-specific attributes
        if LIBROSA_AVAILABLE:
            self.librosa_waveform = None
            self.librosa_sr = None
            self.onset_envelope = None
            self.tempo = None
            self.beat_frames = None

    def has_waveform_data(self) -> bool:
        """
        Check if waveform data is available.

        Returns:
            bool: True if waveform data is loaded, False otherwise
        """
        return self.waveform_data is not None

    def load_file(self, file_path: str) -> bool:
        """
        Load an audio file for analysis.

        Args:
            file_path (str): Path to the audio file to load

        Returns:
            bool: True if file was loaded successfully, False otherwise
        """
        logger.info(f"Loading audio file: {file_path}")

        try:
            # Check if file exists
            if not os.path.isfile(file_path):
                logger.error(f"File not found: {file_path}")
                return False

            # Check if this is a drum stem
            file_path_str = str(file_path).lower()
            self.is_drum_stem = ('drum' in file_path_str or
                                 '/drums.' in file_path_str or
                                 '\\drums.' in file_path_str or
                                 'drum.wav' in file_path_str or
                                 'drums.wav' in file_path_str)

            if self.is_drum_stem:
                logger.info("Detected drum stem file - will optimize analysis for drum patterns")

            # Load audio file using soundfile
            waveform_data, sample_rate = sf.read(file_path, always_2d=True)

            # Store file information
            self.file_path = file_path
            self.waveform_data = waveform_data
            self.sample_rate = sample_rate
            self.channels = waveform_data.shape[1]
            self.duration = len(waveform_data) / sample_rate
            self.duration_seconds = self.duration  # Alias for compatibility
            self.is_analyzed = False
            self.peaks = []
            self.peak_data = {}

            # Load with librosa if available
            if LIBROSA_AVAILABLE:
                try:
                    self.librosa_waveform, self.librosa_sr = librosa.load(file_path, sr=None, mono=True)
                    logger.info("File loaded with librosa successfully")
                except Exception as e:
                    logger.warning(f"Error loading file with librosa: {str(e)}")
                    self.librosa_waveform = None
                    self.librosa_sr = None

            logger.info(f"File loaded successfully: {os.path.basename(file_path)}")
            logger.info(f"Sample rate: {sample_rate} Hz, Channels: {self.channels}, Duration: {self.duration:.2f}s")

            # IMPORTANT: Force the music_file_info path to match the actual loaded file
            # This ensures that the waveform widget displays the correct file
            try:
                from PySide6.QtCore import QCoreApplication
                app = QCoreApplication.instance()
                if app:
                    for widget in app.topLevelWidgets():
                        if hasattr(widget, 'music_file_info') and widget.music_file_info:
                            if 'path' in widget.music_file_info:
                                # Only update if this is a drum stem and the paths don't match
                                if self.is_drum_stem and widget.music_file_info['path'] != file_path:
                                    logger.info(
                                        f"Updating music_file_info path from {widget.music_file_info['path']} to {file_path}")
                                    widget.music_file_info['path'] = file_path
            except Exception as e:
                logger.warning(f"Error updating music_file_info path: {str(e)}")

            return True

        except Exception as e:
            logger.error(f"Error loading file: {str(e)}")
            return False

    def process_waveform(self, callback: Optional[Callable[[bool], None]] = None) -> bool:
        """
        Process the loaded waveform to prepare for analysis.

        Args:
            callback (Callable[[bool], None], optional): Function to call when processing is complete

        Returns:
            bool: True if processing was successful, False otherwise
        """
        logger.info("Processing waveform")

        try:
            if self.waveform_data is None:
                logger.error("No waveform data loaded")
                if callback:
                    callback(False)
                return False

            # For now, just mark as processed
            # Actual processing will happen in detect_peaks

            if callback:
                callback(True)
            return True

        except Exception as e:
            logger.error(f"Error processing waveform: {str(e)}")
            if callback:
                callback(False)
            return False

    def analyze_file(self, file_path: str = None) -> bool:
        """
        Load and analyze an audio file in one step.

        Args:
            file_path (str, optional): Path to the audio file to analyze.
                                      If None, uses the previously loaded file.

        Returns:
            bool: True if analysis was successful, False otherwise
        """
        if file_path is not None:
            if not self.load_file(file_path):
                return False

        if self.file_path is None:
            logger.error("No audio file loaded")
            return False

        try:
            # Detect peaks
            self.detect_peaks()
            return True
        except Exception as e:
            logger.error(f"Error analyzing file: {str(e)}")
            return False

    def detect_peaks(self, audio_file: str = None) -> List[Peak]:
        """
        Detect beats in an audio file using madmom's RNN beat tracker.

        Args:
            audio_file (str, optional): Path to the audio file to analyze.
                                       If None, uses the previously loaded file.

        Returns:
            List[Peak]: List of detected peaks with timing information
        """
        # If audio_file is provided, load it first
        if audio_file is not None:
            self.load_file(audio_file)

        if self.file_path is None:
            logger.error("No audio file loaded")
            return []

        logger.info(f"Detecting peaks in audio file: {self.file_path}")

        try:
            # Record start time for performance monitoring
            start_time = time.time()

            # Process the audio file using madmom
            act = self.beat_processor(self.file_path)
            beat_times = self.beat_tracker(act)

            # Convert beat times to Peak objects
            self.peaks = []

            # If this is a drum stem, we can be more specific with peak types
            if self.is_drum_stem:
                logger.info("Using drum-specific peak detection for drum stem file")

                # For drum stems, we can be more specific with peak types
                # This is a simplified approach - in a real implementation,
                # we would use more sophisticated drum classification
                for i, time_val in enumerate(beat_times):
                    # Alternate between kick and snare for strong beats
                    if i % 4 == 0:
                        peak_type = 'kick'
                        amplitude = 1.0  # Strong beat
                    elif i % 4 == 2:
                        peak_type = 'snare'
                        amplitude = 0.9  # Strong beat
                    elif i % 4 == 1 or i % 4 == 3:
                        peak_type = 'hi-hat'
                        amplitude = 0.7  # Weak beat
                    else:
                        peak_type = 'generic'
                        amplitude = 0.6

                    peak = Peak(
                        time=float(time_val),
                        amplitude=amplitude,
                        confidence=0.9,  # High confidence for all madmom detections
                        type=peak_type
                    )
                    self.peaks.append(peak)
            else:
                # For non-drum files, use simpler peak classification
                for i, time_val in enumerate(beat_times):
                    # Assign alternating types for visualization
                    peak_type = 'kick' if i % 2 == 0 else 'snare'

                    # Create peak with amplitude based on position
                    amplitude = 0.7 + 0.3 * (i % 3) / 2  # Values between 0.7 and 1.0

                    peak = Peak(
                        time=float(time_val),
                        amplitude=amplitude,
                        confidence=0.9,  # High confidence for all madmom detections
                        type=peak_type
                    )
                    self.peaks.append(peak)

            # Organize peaks by type for compatibility with existing code
            self.peak_data = {}
            for peak_type in self.peak_types:
                self.peak_data[peak_type] = [p for p in self.peaks if p.type == peak_type]

            # Record performance metrics
            self.analysis_time = time.time() - start_time
            self.last_analysis_timestamp = time.time()

            # Mark as analyzed
            self.is_analyzed = True

            # Emit signal that peak detection is complete
            self.peak_detection_complete.emit(True)

            logger.info(f"Detected {len(self.peaks)} peaks")
            return self.peaks

        except Exception as e:
            logger.error(f"Error in beat detection: {str(e)}")
            self.peak_detection_complete.emit(False)
            raise

    def get_peaks_by_type(self, peak_type: str = None) -> List[Peak]:
        """
        Get peaks of a specific type.

        Args:
            peak_type (str, optional): Type of peaks to return. If None, returns all peaks.

        Returns:
            List[Peak]: List of peaks of the specified type
        """
        if not self.is_analyzed:
            return []

        if peak_type is None:
            return self.peaks

        return [p for p in self.peaks if p.type == peak_type]

    def get_peak_times(self, peak_type: str = None) -> np.ndarray:
        """
        Get the times of peaks of a specific type.

        Args:
            peak_type (str, optional): Type of peaks to return times for. If None, returns all peak times.

        Returns:
            np.ndarray: Array of peak times in seconds
        """
        peaks = self.get_peaks_by_type(peak_type)
        return np.array([p.time for p in peaks])

    def get_analysis_info(self) -> Dict[str, Any]:
        """
        Get information about the analysis.

        Returns:
            Dict[str, Any]: Dictionary with analysis information
        """
        return {
            'file_path': self.file_path,
            'is_drum_stem': self.is_drum_stem,
            'duration': self.duration,
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'is_analyzed': self.is_analyzed,
            'peak_count': len(self.peaks),
            'analysis_time': self.analysis_time,
            'last_analysis': self.last_analysis_timestamp
        }

    def update_settings(self, settings: Dict[str, Any]) -> None:
        """
        Update analyzer settings.

        Args:
            settings (Dict[str, Any]): Dictionary with settings to update
        """
        for key, value in settings.items():
            if key in self.settings:
                self.settings[key] = value

    def get_waveform_segment(self, start_time: float, end_time: float) -> np.ndarray:
        """
        Get a segment of the waveform data.

        Args:
            start_time (float): Start time in seconds
            end_time (float): End time in seconds

        Returns:
            np.ndarray: Segment of waveform data
        """
        if self.waveform_data is None:
            return np.array([])

        start_sample = int(start_time * self.sample_rate)
        end_sample = int(end_time * self.sample_rate)

        # Ensure within bounds
        start_sample = max(0, min(start_sample, len(self.waveform_data) - 1))
        end_sample = max(0, min(end_sample, len(self.waveform_data)))

        return self.waveform_data[start_sample:end_sample]

    # Additional methods for librosa integration
    def get_waveform_amplitude(self, position: float) -> float:
        """
        Get the amplitude of the waveform at a specific position.

        Args:
            position (float): Position in seconds

        Returns:
            float: Amplitude value
        """
        if self.waveform_data is None:
            return 0.0

        sample = int(position * self.sample_rate)
        if 0 <= sample < len(self.waveform_data):
            # Average across channels
            return float(np.mean(np.abs(self.waveform_data[sample])))
        return 0.0

    def get_waveform_max_amplitude(self) -> float:
        """
        Get the maximum amplitude of the waveform.

        Returns:
            float: Maximum amplitude value
        """
        if self.waveform_data is None:
            return 0.0

        return float(np.max(np.abs(self.waveform_data)))

    def get_waveform_rms(self) -> float:
        """
        Get the RMS (Root Mean Square) value of the waveform.

        Returns:
            float: RMS value
        """
        if self.waveform_data is None:
            return 0.0

        return float(np.sqrt(np.mean(np.square(self.waveform_data))))

    def get_spectrogram(self, n_fft: int = 2048, hop_length: int = 512) -> np.ndarray:
        """
        Get the spectrogram of the waveform.

        Args:
            n_fft (int): FFT window size
            hop_length (int): Hop length between frames

        Returns:
            np.ndarray: Spectrogram data
        """
        if not LIBROSA_AVAILABLE or self.librosa_waveform is None:
            return np.array([])

        return librosa.amplitude_to_db(
            np.abs(librosa.stft(self.librosa_waveform, n_fft=n_fft, hop_length=hop_length)),
            ref=np.max
        )

    def get_mel_spectrogram(self, n_fft: int = 2048, hop_length: int = 512, n_mels: int = 128) -> np.ndarray:
        """
        Get the mel spectrogram of the waveform.

        Args:
            n_fft (int): FFT window size
            hop_length (int): Hop length between frames
            n_mels (int): Number of mel bands

        Returns:
            np.ndarray: Mel spectrogram data
        """
        if not LIBROSA_AVAILABLE or self.librosa_waveform is None:
            return np.array([])

        return librosa.power_to_db(
            librosa.feature.melspectrogram(
                y=self.librosa_waveform, sr=self.librosa_sr,
                n_fft=n_fft, hop_length=hop_length, n_mels=n_mels
            ),
            ref=np.max
        )


# For backward compatibility with existing code that might call the function directly
def detect_peaks(audio_file: str) -> np.ndarray:
    """
    Detect beats in an audio file using madmom (function interface).

    Args:
        audio_file (str): Path to the audio file to analyze

    Returns:
        np.ndarray: Array of beat times in seconds
    """
    analyzer = WaveformAnalyzer()
    peaks = analyzer.detect_peaks(audio_file)
    return np.array([peak.time for peak in peaks])


if __name__ == "__main__":
    # This section can be used for testing the implementation
    pass