import math
import os
import wave
import numpy as np
from typing import List, Tuple, Dict, Optional, NamedTuple
import threading
from datetime import datetime, timedelta
from pathlib import Path
import json
import logging

from PySide6.QtCore import Signal, QObject

# Optional imports with fallbacks
try:
    from scipy import signal
    from scipy.interpolate import interp1d

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logging.warning("scipy not available - advanced signal processing disabled")

try:
    import librosa

    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logging.warning("librosa not available - advanced audio analysis disabled")


class Peak(NamedTuple):
    """Represents a detected peak in the audio waveform"""
    position: int  # Sample position
    amplitude: float  # Peak amplitude (0.0-1.0)
    time: float  # Time in seconds
    time_str: str  # Formatted time string (0:00.00)


class WaveformAnalyzer(QObject):
    """
    Advanced audio waveform analyzer optimized for precise peak detection

    Features:
    - High-precision peak detection using multiple algorithms
    - Time-formatted peak data (0:00.00)
    - Waveform visualization support with peak markers
    - Persistent peak data storage
    """
    peak_detection_complete = Signal()

    def __init__(self):
        """Initialize the waveform analyzer"""
        super().__init__()
        # File information
        self.file_path: Optional[Path] = None
        self.filename: Optional[str] = None
        self.duration_seconds: float = 0.0
        self.sample_rate: int = 0
        self.channels: int = 0

        # Audio data
        self.waveform_data: Optional[np.ndarray] = None
        self.peak_data: Optional[np.ndarray] = None  # For visualization

        # Peak detection settings
        self.peaks: List[Peak] = []
        self.detected_peaks = []
        self.detection_threshold: float = 0.26  # Reduced from 1.5 for adaptive threshold
        self.min_peak_distance: float = 0.1  # 100ms minimum between peaks

        # Enhanced peak detection parameters (kept for future use)
        self.amplitude_threshold = 0.15
        self.dynamic_range_db = 40
        self.noise_floor_db = -40
        self.prominence_threshold = 0.1

        # Noise gate settings
        self.noise_gate_threshold: float = 0.01  # Threshold for noise gate
        self.silence_threshold: float = 0.005    # Threshold for silence detection
        self.min_active_duration: float = 0.1    # Minimum duration of active audio (seconds)

        # Analysis state
        self.is_analyzed: bool = False
        self.is_processing: bool = False

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def load_file(self, file_path: str | Path) -> bool:
        """
        Load a WAV file for analysis

        Args:
            file_path: Path to the WAV file

        Returns:
            bool: True if file loaded successfully
        """
        try:
            # Convert to Path object for better path handling
            path = Path(file_path)

            if not path.exists():
                self.logger.error(f"File not found: {path}")
                return False

            if path.suffix.lower() != '.wav':
                self.logger.error(f"Not a WAV file: {path}")
                return False

            # Store file information
            self.file_path = path
            self.filename = path.name

            # Reset state
            self.is_analyzed = False
            self.is_processing = False
            self.waveform_data = None
            self.peaks = []

            # Read WAV file properties
            with wave.open(str(path), 'rb') as wav_file:
                self.channels = wav_file.getnchannels()
                self.sample_rate = wav_file.getframerate()
                frames = wav_file.getnframes()
                self.duration_seconds = frames / float(self.sample_rate)

            self.logger.info(f"Loaded WAV file: {self.filename}")
            self.logger.info(f"Duration: {self._format_time(self.duration_seconds)}")
            self.logger.info(f"Sample rate: {self.sample_rate}Hz")
            self.logger.info(f"Channels: {self.channels}")

            return True

        except Exception as e:
            self.logger.error(f"Error loading WAV file: {str(e)}")
            return False

    def process_waveform(self, callback: Optional[callable] = None) -> None:
        """
        Process the waveform data in a background thread

        Args:
            callback: Optional function to call when processing is complete
        """
        if not self.file_path:
            self.logger.error("No file loaded")
            if callback:
                callback(False)
            return

        if self.is_processing:
            self.logger.warning("Waveform processing already in progress")
            return

        self.is_processing = True

        # Create and start processing thread
        thread = threading.Thread(
            target=self._process_waveform_thread,
            args=(callback,),
            daemon=True
        )
        thread.start()

    def _process_waveform_thread(self, callback: Optional[callable]) -> None:
        """
        Thread function for processing waveform data

        Args:
            callback: Optional function to call when processing is complete
        """
        try:
            # Load and process the WAV file
            with wave.open(str(self.file_path), 'rb') as wav_file:
                # Get basic parameters
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                frames = wav_file.getnframes()

                # Read all frames
                raw_data = wav_file.readframes(frames)

                # Convert to numpy array based on sample width
                if sample_width == 1:  # 8-bit unsigned
                    data = np.frombuffer(raw_data, dtype=np.uint8)
                    data = data.astype(np.float32) / 128.0 - 1.0
                elif sample_width == 2:  # 16-bit signed
                    data = np.frombuffer(raw_data, dtype=np.int16)
                    data = data.astype(np.float32) / 32768.0
                elif sample_width == 3:  # 24-bit signed
                    # Handle 24-bit audio by converting to 32-bit
                    data = np.zeros(len(raw_data) // 3, dtype=np.float32)
                    for i in range(0, len(raw_data), 3):
                        value = (raw_data[i] | (raw_data[i + 1] << 8) | (raw_data[i + 2] << 16))
                        if value & 0x800000:  # Handle negative values
                            value |= ~0xffffff
                        data[i // 3] = value / 8388608.0
                elif sample_width == 4:  # 32-bit signed
                    data = np.frombuffer(raw_data, dtype=np.int32)
                    data = data.astype(np.float32) / 2147483648.0
                else:
                    raise ValueError(f"Unsupported sample width: {sample_width}")

                # Convert stereo to mono if needed
                if channels == 2:
                    data = data.reshape(-1, 2)
                    data = data.mean(axis=1)

                # Store the processed data
                self.waveform_data = data

                # Create visualization data
                self._create_visualization_data()

                # Mark as analyzed
                self.is_analyzed = True

                # Notify callback of success
                if callback:
                    callback(True)

                # Start peak detection in background
                self._detect_peaks_background()

        except Exception as e:
            self.logger.error(f"Error processing waveform: {str(e)}")
            if callback:
                callback(False)
        finally:
            self.is_processing = False

    def _create_visualization_data(self) -> None:
        """Create reduced resolution data for waveform visualization"""
        if self.waveform_data is None:
            return

        # Target about 4 points per pixel for a typical display width
        target_points = 4000

        # Calculate reduction factor
        reduction_factor = max(1, len(self.waveform_data) // target_points)

        try:
            # Reshape data for efficient min/max calculation
            remainder = len(self.waveform_data) % reduction_factor
            if remainder:
                # Pad the data to make it evenly divisible
                pad_size = reduction_factor - remainder
                padded_data = np.pad(self.waveform_data, (0, pad_size), 'constant')
            else:
                padded_data = self.waveform_data

            # Reshape and calculate min/max
            segments = padded_data.reshape(-1, reduction_factor)
            min_values = np.min(segments, axis=1)
            max_values = np.max(segments, axis=1)

            # Combine into peak data for visualization
            self.peak_data = np.column_stack((min_values, max_values))

        except Exception as e:
            self.logger.error(f"Error creating visualization data: {str(e)}")
            self.peak_data = None

    @staticmethod
    def _format_time(seconds: float) -> str:
        """
        Format time in seconds to MM:SS.ss format

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string (e.g., "1:23.45")
        """
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:05.2f}"

    def _detect_peaks_background(self) -> None:
        """Start peak detection in a background thread"""
        if not self.is_analyzed or self.waveform_data is None:
            return

        thread = threading.Thread(
            target=self._detect_peaks_comprehensive,
            daemon=True
        )
        thread.start()

    def _detect_peaks_comprehensive(self) -> None:
        try:
            self.logger.info("Starting comprehensive peak detection...")
            start_time = datetime.now()

            # Get absolute values for amplitude analysis
            abs_data = np.abs(self.waveform_data)

            # Initialize peak storage
            all_peaks = set()

            # 1. Basic amplitude peaks with enhanced filtering
            amplitude_peaks = self._find_amplitude_peaks(abs_data)
            all_peaks.update(amplitude_peaks)

            # 2. Spectral peaks if scipy is available
            if SCIPY_AVAILABLE:
                spectral_peaks = self._find_spectral_peaks()
                # Only add spectral peaks that are near amplitude peaks
                for peak in spectral_peaks:
                    if any(abs(peak - ap) < self.sample_rate * 0.05 for ap in amplitude_peaks):
                        all_peaks.add(peak)

            # 3. Onset peaks if librosa is available
            if LIBROSA_AVAILABLE:
                onset_peaks = self._find_onset_peaks()
                # Only add onset peaks that are near amplitude peaks
                for peak in onset_peaks:
                    if any(abs(peak - ap) < self.sample_rate * 0.05 for ap in amplitude_peaks):
                        all_peaks.add(peak)

            # Convert peaks to sorted list
            peak_list = sorted(all_peaks)

            # Apply musical timing filter
            filtered_peaks = self._filter_peaks_by_timing(peak_list)

            # Create Peak objects
            self.peaks = self._create_peak_objects(filtered_peaks)

            # Update detected_peaks for compatibility
            self.detected_peaks = [(p.position, p.amplitude, p.time) for p in self.peaks]

            # Save peaks to file
            self._save_peaks()

            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Peak detection complete. Found {len(self.peaks)} peaks in {duration:.2f} seconds")

            # Emit signal that peak detection is complete
            if hasattr(self, 'peak_detection_complete'):
                self.peak_detection_complete.emit()

        except Exception as e:
            self.logger.error(f"Error in peak detection: {str(e)}")

    def _find_amplitude_peaks(self, abs_data: np.ndarray) -> set:
        """
        Find peaks based on amplitude changes with improved start handling

        Args:
            abs_data: Absolute amplitude data

        Returns:
            Set of peak positions
        """
        peaks = set()

        try:
            # Find start of actual audio content
            window_size = int(0.02 * self.sample_rate)  # 20ms windows
            energy = np.array([
                np.sqrt(np.mean(abs_data[i:i + window_size] ** 2))
                for i in range(0, len(abs_data), window_size)
            ])

            # Find where energy exceeds silence threshold
            active_windows = np.where(energy > 0.005)[0]  # Lowered threshold for drums

            if len(active_windows) > 0:
                first_active = active_windows[0]
                audio_start = first_active * window_size
                # Small offset before first drum hit
                audio_start = max(0, audio_start - int(0.05 * self.sample_rate))
            else:
                audio_start = 0

            self.logger.info(f"Detected audio start at {audio_start / self.sample_rate:.2f} seconds")

            # Original peak detection logic, but starting from audio_start
            window_size = 1024
            pre_smoothed = np.convolve(abs_data, np.ones(window_size) / window_size, mode='same')

            # Calculate adaptive threshold
            local_max = np.maximum.accumulate(np.maximum.reduceat(
                pre_smoothed,
                np.arange(0, len(pre_smoothed), window_size)
            ))
            local_max = np.repeat(local_max, window_size)[:len(pre_smoothed)]

            threshold = local_max * self.detection_threshold

            # Minimum distance between peaks in samples
            min_samples = int(self.min_peak_distance * self.sample_rate)

            # Find peaks with precise alignment, starting from audio_start
            last_peak = -min_samples

            for i in range(max(window_size, audio_start), len(pre_smoothed) - window_size):
                if (pre_smoothed[i] > pre_smoothed[i - 1] and
                        pre_smoothed[i] >= pre_smoothed[i + 1] and
                        pre_smoothed[i] > threshold[i]):

                    # Fine-tune peak position by looking at local maximum
                    search_window = 50  # Look 50 samples around the detected peak
                    start_idx = max(0, i - search_window)
                    end_idx = min(len(abs_data), i + search_window)
                    local_data = abs_data[start_idx:end_idx]

                    if len(local_data) > 0:
                        # Find the actual peak position within the window
                        local_peak = start_idx + np.argmax(local_data)

                        # Check minimum distance from last peak
                        if local_peak - last_peak >= min_samples:
                            # For the first peak after audio_start, ensure it's significant
                            if len(peaks) == 0:
                                if abs_data[local_peak] > np.mean(abs_data[audio_start:]) * 1.5:
                                    peaks.add(local_peak)
                                    last_peak = local_peak
                            else:
                                peaks.add(local_peak)
                                last_peak = local_peak

            self.logger.info(f"Found {len(peaks)} amplitude peaks")

        except Exception as e:
            self.logger.error(f"Error in amplitude peak detection: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())

        return peaks

    def _find_spectral_peaks(self) -> set:
        """
        Find peaks using spectral analysis

        Returns:
            Set of peak positions
        """
        peaks = set()

        if not SCIPY_AVAILABLE:
            return peaks

        try:
            # Calculate spectrogram
            frequencies, times, Sxx = signal.spectrogram(
                self.waveform_data,
                fs=self.sample_rate,
                nperseg=1024,
                noverlap=512
            )

            # Calculate spectral flux
            spectral_flux = np.diff(np.sum(np.abs(Sxx), axis=0))
            spectral_flux = np.pad(spectral_flux, (1, 0))

            # Normalize flux
            spectral_flux = spectral_flux / np.max(spectral_flux)

            # Interpolate to match waveform length
            time_points = np.linspace(0, len(self.waveform_data), len(spectral_flux))
            full_time_points = np.arange(len(self.waveform_data))

            interpolator = interp1d(
                time_points,
                spectral_flux,
                kind='linear',
                bounds_error=False,
                fill_value=0
            )

            full_flux = interpolator(full_time_points)

            # Find peaks in spectral flux
            for i in range(1, len(full_flux) - 1):
                if (full_flux[i] > full_flux[i - 1] and
                        full_flux[i] >= full_flux[i + 1] and
                        full_flux[i] > self.detection_threshold):
                    peaks.add(i)

        except Exception as e:
            self.logger.error(f"Error in spectral peak detection: {str(e)}")

        return peaks

    def _filter_peaks_by_timing(self, peaks: List[int]) -> List[int]:
        """
        Filter peaks based on musical timing with improved accuracy

        Args:
            peaks: List of peak positions

        Returns:
            Filtered list of peak positions
        """
        if not peaks:
            return []

        try:
            # Convert peak positions to times
            peak_times = np.array([pos / self.sample_rate for pos in peaks])

            if len(peak_times) >= 2:
                # Calculate inter-peak intervals
                intervals = np.diff(peak_times)

                # Use histogram with adaptive binning
                hist, bins = np.histogram(intervals, bins='auto')

                # Find the dominant intervals (might be multiple)
                peak_indices = np.where(hist > np.max(hist) * 0.3)[0]  # Get all significant peaks
                dominant_intervals = bins[peak_indices]

                # Calculate tempo(s) in BPM
                tempos = 60 / dominant_intervals

                # Filter out unreasonable tempos
                valid_tempos = tempos[(tempos >= 60) & (tempos <= 200)]  # Common tempo range

                if len(valid_tempos) > 0:
                    # Use the most common valid tempo
                    target_tempo = valid_tempos[0]
                    beat_interval = 60 / target_tempo

                    # Filter peaks with adaptive tolerance
                    filtered_peaks = []
                    grid_tolerance = beat_interval * 0.2  # 20% tolerance

                    for i, peak in enumerate(peaks):
                        peak_time = peak_times[i]

                        # Find closest beat position
                        beat_position = round(peak_time / beat_interval)
                        expected_time = beat_position * beat_interval

                        if abs(peak_time - expected_time) <= grid_tolerance:
                            filtered_peaks.append(peak)

                    self.logger.info(f"Filtered {len(peaks) - len(filtered_peaks)} peaks based on timing")
                    self.logger.info(f"Detected tempo: {target_tempo:.1f} BPM")
                    return filtered_peaks

            return peaks

        except Exception as e:
            self.logger.error(f"Error in peak timing filtering: {str(e)}")
            return peaks

    def _find_onset_peaks(self) -> set:
        """
        Find peaks using onset detection

        Returns:
            Set of peak positions
        """
        peaks = set()

        if not LIBROSA_AVAILABLE:
            return peaks

        try:
            # Convert to float32 for librosa
            y = self.waveform_data.astype(np.float32)

            # Get onset frames
            onset_frames = librosa.onset.onset_detect(
                y=y,
                sr=self.sample_rate,
                wait=int(self.min_peak_distance * self.sample_rate),
                pre_avg=0.1,
                post_avg=0.1,
                delta=self.detection_threshold,
                normalize=True
            )

            # Convert frames to sample positions
            hop_length = 512  # librosa default
            for frame in onset_frames:
                sample_pos = int(frame * hop_length)
                if 0 <= sample_pos < len(self.waveform_data):
                    peaks.add(sample_pos)

        except Exception as e:
            self.logger.error(f"Error in onset peak detection: {str(e)}")

        return peaks

    def _create_peak_objects(self, peak_positions: List[int]) -> List[Peak]:
        """
        Create Peak objects from peak positions with filtering

        Args:
            peak_positions: List of sample positions for peaks

        Returns:
            List of Peak objects
        """
        peaks = []
        min_samples = int(self.min_peak_distance * self.sample_rate)
        last_peak = -min_samples

        for pos in peak_positions:
            # Apply minimum distance filtering
            if pos - last_peak >= min_samples:
                # Get amplitude at peak
                amplitude = abs(self.waveform_data[pos])

                # Calculate time
                time_seconds = pos / self.sample_rate
                time_str = self._format_time(time_seconds)

                # Create Peak object
                peak = Peak(
                    position=pos,
                    amplitude=amplitude,
                    time=time_seconds,
                    time_str=time_str
                )

                peaks.append(peak)
                last_peak = pos

        return peaks

    def _save_peaks(self) -> None:
        """Save detected peaks to a JSON file"""
        if not self.file_path or not self.peaks:
            return

        try:
            # Create peaks directory if needed
            peaks_dir = self.file_path.parent / 'peaks'
            peaks_dir.mkdir(exist_ok=True)

            # Create peaks file path
            peaks_file = peaks_dir / f"{self.file_path.stem}_peaks.json"

            # Convert peaks to dictionary with native Python types
            peaks_data = {
                'file': str(self.file_path),
                'sample_rate': int(self.sample_rate),
                'duration': float(self.duration_seconds),
                'peaks': [
                    {
                        'position': int(p.position),
                        'amplitude': float(p.amplitude),
                        'time': float(p.time),
                        'time_str': p.time_str
                    }
                    for p in self.peaks
                ]
            }

            # Save to file
            with open(peaks_file, 'w') as f:
                json.dump(peaks_data, f, indent=2)

            self.logger.info(f"Saved {len(self.peaks)} peaks to {peaks_file}")

        except Exception as e:
            self.logger.error(f"Error saving peaks: {str(e)}")

    def load_peaks(self) -> bool:
        """
        Load previously detected peaks from file

        Returns:
            True if peaks were loaded successfully
        """
        if not self.file_path:
            return False

        try:
            peaks_file = self.file_path.parent / 'peaks' / f"{self.file_path.stem}_peaks.json"

            if not peaks_file.exists():
                return False

            with open(peaks_file, 'r') as f:
                data = json.load(f)

            # Verify file match
            if data['file'] != str(self.file_path):
                return False

            # Create Peak objects
            self.peaks = [
                Peak(
                    position=p['position'],
                    amplitude=p['amplitude'],
                    time=p['time'],
                    time_str=p['time_str']
                )
                for p in data['peaks']
            ]

            self.logger.info(f"Loaded {len(self.peaks)} peaks from {peaks_file}")
            return True

        except Exception as e:
            self.logger.error(f"Error loading peaks: {str(e)}")
            return False

    def get_waveform_points(self, width: int, height: int, offset: float = 0.0, zoom_factor: float = 1.0) -> List[
        Tuple[int, int, int]]:
        """
        Get points for drawing the waveform

        Args:
            width: Width of the display area in pixels
            height: Height of the display area in pixels
            offset: Start position as normalized value (0.0-1.0)
            zoom_factor: Zoom factor (1.0 = normal, >1.0 = zoomed in)

        Returns:
            List of (x, y1, y2) points for drawing waveform segments
        """
        if not self.is_analyzed or self.peak_data is None:
            return []

        try:
            # Calculate visible portion of the waveform
            visible_width = 1.0 / zoom_factor
            start_pos = offset
            end_pos = min(1.0, start_pos + visible_width)

            # Calculate center line
            center_y = height / 2

            # Calculate which part of peak_data to use
            peak_data_len = len(self.peak_data)
            start_idx = int(start_pos * peak_data_len)
            end_idx = int(end_pos * peak_data_len)

            # Ensure valid range
            start_idx = max(0, min(peak_data_len - 1, start_idx))
            end_idx = max(start_idx + 1, min(peak_data_len, end_idx))

            # Calculate points per pixel
            points_per_pixel = (end_idx - start_idx) / width

            # Generate points
            points = []
            for x in range(width):
                # Calculate data index for this pixel
                idx = start_idx + int(x * points_per_pixel)
                if idx >= peak_data_len:
                    break

                # Get min/max values
                min_val, max_val = self.peak_data[idx]

                # Calculate y coordinates
                # Scale by 0.9 to leave margin
                y1 = int(center_y - (max_val * height * 0.45))
                y2 = int(center_y - (min_val * height * 0.45))

                # Ensure minimum height for very quiet sections
                if abs(y2 - y1) < 2:
                    y_mid = (y1 + y2) // 2
                    y1 = y_mid - 1
                    y2 = y_mid + 1

                points.append((x, y1, y2))

            return points

        except Exception as e:
            self.logger.error(f"Error generating waveform points: {str(e)}")
            return []

    def get_peak_markers(self, width: int, height: int, offset: float = 0.0, zoom_factor: float = 1.0) -> List[
        Tuple[int, int, int, float]]:
        """
        Get peak markers for visualization

        Args:
            width: Width of the display area in pixels
            height: Height of the display area in pixels
            offset: Start position as normalized value (0.0-1.0)
            zoom_factor: Zoom factor (1.0 = normal, >1.0 = zoomed in)

        Returns:
            List of (x, y1, y2, amplitude) tuples for drawing peak markers
        """
        if not self.peaks:
            return []

        try:
            # Calculate visible time range
            visible_duration = self.duration_seconds / zoom_factor
            start_time = offset * self.duration_seconds
            end_time = start_time + visible_duration

            markers = []

            for peak in self.peaks:
                if start_time <= peak.time <= end_time:
                    # Calculate x position
                    relative_pos = (peak.time - start_time) / visible_duration
                    x = int(relative_pos * width)

                    # Calculate marker height based on amplitude
                    # Use logarithmic scaling for better visibility of smaller peaks
                    marker_height = int(height * 0.3 * (1 + np.log10(peak.amplitude + 0.1)))

                    # Calculate y positions
                    center_y = height // 2
                    y1 = center_y - marker_height
                    y2 = center_y + marker_height

                    markers.append((x, y1, y2, peak.amplitude))

            return markers

        except Exception as e:
            self.logger.error(f"Error generating peak markers: {str(e)}")
            return []

    def get_peak_markers_for_visualization(self) -> List[Tuple[float, float]]:
        """Get peak markers in the format expected by the widget"""
        if not self.peaks:
            return []

        markers = []
        for peak in self.peaks:
            # Convert to normalized position
            if self.duration_seconds > 0:
                position = peak.time / self.duration_seconds
                markers.append((position, peak.amplitude))

        return markers

    def get_time_axis_markers(self, width: int, offset: float = 0.0, zoom_factor: float = 1.0) -> List[Tuple[int, str]]:
        """
        Get time axis markers for visualization

        Args:
            width: Width of the display area in pixels
            offset: Start position as normalized value (0.0-1.0)
            zoom_factor: Zoom factor (1.0 = normal, >1.0 = zoomed in)

        Returns:
            List of (x, time_str) tuples for drawing time markers
        """
        try:
            # Calculate visible time range
            visible_duration = self.duration_seconds / zoom_factor
            start_time = offset * self.duration_seconds
            end_time = start_time + visible_duration

            # Calculate appropriate time step based on zoom level
            if visible_duration <= 5:  # <= 5 seconds visible
                step = 0.5  # Show half-second markers
            elif visible_duration <= 20:  # <= 20 seconds visible
                step = 1.0  # Show 1-second markers
            elif visible_duration <= 60:  # <= 1 minute visible
                step = 5.0  # Show 5-second markers
            else:
                step = 15.0  # Show 15-second markers

            # Generate time markers
            markers = []
            current_time = math.ceil(start_time / step) * step

            while current_time <= end_time:
                # Calculate x position
                relative_pos = (current_time - start_time) / visible_duration
                x = int(relative_pos * width)

                if 0 <= x <= width:
                    time_str = self._format_time(current_time)
                    markers.append((x, time_str))

                current_time += step

            return markers

        except Exception as e:
            self.logger.error(f"Error generating time axis markers: {str(e)}")
            return []

    def get_peak_times(self) -> List[str]:
        """
        Get list of peak times in formatted strings

        Returns:
            List of time strings in format "0:00.00"
        """
        return [peak.time_str for peak in self.peaks]

    def get_peak_data(self) -> List[Peak]:
        """
        Get all peak data

        Returns:
            List of Peak objects
        """
        return self.peaks.copy()

    def _find_audio_start(self, abs_data: np.ndarray) -> int:
        """
        Find the point where actual audio content starts

        Args:
            abs_data: Absolute amplitude data

        Returns:
            Index where actual audio content starts
        """
        try:
            # Calculate RMS energy in windows
            window_size = int(0.02 * self.sample_rate)  # 20ms windows
            energy = np.array([
                np.sqrt(np.mean(abs_data[i:i + window_size] ** 2))
                for i in range(0, len(abs_data), window_size)
            ])

            # Find where energy exceeds silence threshold
            active_windows = np.where(energy > self.silence_threshold)[0]

            if len(active_windows) > 0:
                # Find first substantial audio content
                first_active = active_windows[0]

                # Convert window index back to sample index
                start_index = first_active * window_size

                # Add a small offset to avoid any initial transients
                offset_samples = int(0.05 * self.sample_rate)  # 50ms offset
                return max(0, start_index - offset_samples)

            return 0

        except Exception as e:
            self.logger.error(f"Error finding audio start: {str(e)}")
            return 0
