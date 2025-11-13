#!/usr/bin/env python3
"""
Professional Waveform Analyzer for Drum Detection using madmom
=============================================================

A comprehensive, production-level waveform analyzer specifically designed for drum hit detection
and analysis. This analyzer incorporates madmom's state-of-the-art beat detection algorithms
along with advanced features including:

- RNN-based beat detection with DBN beat tracking
- Multi-method onset detection with intelligent fusion
- Advanced spectral analysis (MFCC, spectral centroid, spectral contrast, spectral flux)
- Multi-band frequency analysis for precise drum classification
- Machine learning-based transient detection and validation
- Advanced noise filtering and adaptive signal processing
- Intelligent amplitude segment-based filtering with adaptive thresholds
- Professional drum classification (kick, snare, hi-hat, cymbal, tom)
- Sub-sample timing accuracy with confidence scoring
- Parallel processing and performance optimization
- Comprehensive error handling and timeout protection
- Real-time progress reporting and detailed analysis metrics

Author: NinjaTeach AI Team
Version: 3.0.0 - Enhanced Professional Edition with madmom Integration
License: MIT
"""
import concurrent
import math
import os
import sys
import wave
import numpy as np
from typing import List, Tuple, Dict, Optional, NamedTuple, Union, Any
import threading
from datetime import datetime, timedelta
from pathlib import Path
import json
import logging
import time
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
import warnings
from functools import wraps, lru_cache
import multiprocessing as mp
import psutil  # For memory monitoring

# Import visual validator
try:
    from utils.audio.visual_validator import VisualValidator
    VISUAL_VALIDATOR_AVAILABLE = True
except ImportError:
    VISUAL_VALIDATOR_AVAILABLE = False
    logger = logging.getLogger("WaveformAnalyzer")
    logger.warning("VisualValidator not available: No module named 'utils.audio.visual_validator'")
    logger.warning("Visual validation features will be disabled")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("WaveformAnalyzer")

# Apply NumPy compatibility fixes before importing madmom
if not hasattr(np, 'int'):
    np.int = int
if not hasattr(np, 'float'):
    np.float = float

# Optional scipy import for advanced filtering
try:
    import scipy.signal
    import scipy.stats
    from scipy.ndimage import gaussian_filter1d
    from scipy.fft import fft, fftfreq

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("⚠️  scipy not available - some advanced filtering features disabled")

# Optional sklearn imports
try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import IsolationForest

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("⚠️  sklearn not available - some machine learning features disabled")

# Optional matplotlib imports for visualization
try:
    import matplotlib

    backends_to_try = ['Agg', 'TkAgg', 'Qt5Agg', 'MacOSX']
    backend_set = False

    for backend in backends_to_try:
        try:
            matplotlib.use(backend, force=True)
            if matplotlib.get_backend() == backend:
                logging.info(f"Successfully set matplotlib backend to {backend}")
                backend_set = True
                break
        except Exception as e:
            continue

    if not backend_set:
        logging.warning("Could not set any preferred matplotlib backend")

    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("⚠️  matplotlib not available - visualization features disabled")

# Try to import librosa for waveform loading and display
try:
    import librosa
    import librosa.display

    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("⚠️  librosa not available - some audio processing features disabled")

# Import madmom for beat detection
try:
    from madmom.features.beats import RNNBeatProcessor, DBNBeatTrackingProcessor
    from madmom.audio.signal import Signal
    from madmom.processors import Processor
    from madmom.features.onsets import OnsetPeakPickingProcessor, SpectralOnsetProcessor
    from madmom.features.onsets import RNNOnsetProcessor
    from madmom.audio.spectrogram import SpectrogramProcessor, LogarithmicFilteredSpectrogramProcessor
    from madmom.audio.stft import ShortTimeFourierTransformProcessor
    from madmom.features.tempo import TempoEstimationProcessor

    MADMOM_AVAILABLE = True
except ImportError as e:
    MADMOM_AVAILABLE = False
    logger.warning(f"⚠️  madmom not available - beat detection features disabled: {e}")
    import traceback
    traceback.print_exc()

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

# Import performance monitor
try:
    from utils.audio.performance_monitor import PerformanceMonitor

    PERFORMANCE_MONITOR_AVAILABLE = True
except ImportError:
    PERFORMANCE_MONITOR_AVAILABLE = False
    logger.warning("⚠️  performance_monitor not available - performance tracking disabled")


    # Create a simple fallback performance monitor
    class PerformanceMonitor:
        def __init__(self):
            self.timings = {}
            self.call_counts = {}

        def timing_decorator(self, func_name=None):
            def decorator(func):
                @wraps(func)
                def wrapper(*args, **kwargs):
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    end_time = time.time()
                    return result

                return wrapper

            return decorator

# Create performance monitor instance
performance_monitor = PerformanceMonitor()


# Decorator for profiling methods
def profile_method(method_name):
    """Decorator for profiling method execution time"""
    return performance_monitor.timing_decorator(method_name)


# Timeout decorator for preventing long-running operations
def timeout(timeout_seconds=60):
    """
    Decorator to timeout functions after specified seconds.

    This decorator will run the function in a separate thread and raise a TimeoutError
    if the function takes longer than timeout_seconds to complete.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Create a ThreadPoolExecutor to run the function
                with ThreadPoolExecutor(max_workers=1) as executor:
                    # Submit the function to the executor
                    future = executor.submit(func, *args, **kwargs)

                    try:
                        # Wait for the function to complete with a timeout
                        start_time = time.time()
                        result = future.result(timeout=timeout_seconds)
                        elapsed = time.time() - start_time

                        # Log a warning if the function took a long time
                        if elapsed > timeout_seconds * 0.8:
                            logger.warning(
                                f"{func.__name__} took {elapsed:.2f}s (approaching timeout of {timeout_seconds}s)")

                        return result
                    except concurrent.futures.TimeoutError:
                        # Log an error and raise a TimeoutError if the function times out
                        logger.error(f"{func.__name__} timed out after {timeout_seconds}s")
                        raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds} seconds")
            except Exception as e:
                if not isinstance(e, TimeoutError):
                    logger.error(f"Error in {func.__name__}: {e}")
                raise

        return wrapper

    return decorator


# Enhanced profiling decorator with memory tracking
def enhanced_profile_method(method_name: str):
    """
    Enhanced decorator for method profiling with detailed metrics
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            start_time = time.time()

            # Try to get memory usage if psutil is available
            try:
                process = psutil.Process()
                start_memory = process.memory_info().rss / 1024 / 1024  # MB
            except (ImportError, NameError):
                pass

            try:
                result = func(self, *args, **kwargs)
                execution_time = time.time() - start_time

                # Store timing information
                if hasattr(self, 'processing_times'):
                    self.processing_times[method_name] = execution_time

                # Log performance metrics
                memory_info = ""
                try:
                    process = psutil.Process()
                    end_memory = process.memory_info().rss / 1024 / 1024  # MB
                    memory_delta = end_memory - start_memory
                    memory_info = f", Memory: {memory_delta:+.1f}MB"
                except (ImportError, NameError, UnboundLocalError):
                    pass

                logger.info(f"{method_name} completed in {execution_time:.3f}s{memory_info}")
                return result
            except Exception as e:
                logger.error(f"Error in {method_name}: {e}")
                execution_time = time.time() - start_time
                logger.error(f"Failed after {execution_time:.3f}s")
                raise

        return wrapper

    return decorator


@dataclass
class Peak:
    """
    Data class representing a peak in the audio waveform.

    Attributes:
        time (float): Time in seconds when the peak occurs
        amplitude (float): Amplitude of the peak (0.0 to 1.0)
        confidence (float): Confidence score of the peak detection (0.0 to 1.0)
        type (str): Type of peak (e.g., 'kick', 'snare', 'hi-hat', etc.)
        frequency (float): Estimated frequency of the peak (Hz)
        drum_type (str): Alias for 'type' to maintain compatibility with external code
        segment (str): Amplitude segment type where the peak occurs (e.g., 'low', 'medium', 'high', 'very_high')
        spectral_features (Dict): Dictionary containing spectral analysis features for this peak
    """
    time: float
    amplitude: float = 1.0
    confidence: float = 1.0
    type: str = 'generic'
    frequency: float = 0.0
    segment: str = 'medium'  # Default segment type

    def __init__(self, time: float, amplitude: float = 1.0, confidence: float = 1.0,
                 type: str = 'generic', frequency: float = 0.0, segment: str = 'medium'):
        """
        Initialize a Peak object with comprehensive attributes.

        Args:
            time: Time in seconds when the peak occurs
            amplitude: Amplitude of the peak (0.0 to 1.0)
            confidence: Confidence score of the peak detection (0.0 to 1.0)
            type: Type of peak (e.g., 'kick', 'snare', 'hi-hat', etc.)
            frequency: Estimated frequency of the peak (Hz)
            segment: Amplitude segment type where the peak occurs
        """
        self.time = time
        self.amplitude = amplitude
        self.confidence = confidence
        self.type = type
        self.frequency = frequency
        self.segment = segment
        self._drum_type = type

        # Initialize spectral features dictionary
        self.spectral_features = {
            'centroid': 0.0,
            'bandwidth': 0.0,
            'contrast': 0.0,
            'flatness': 0.0,
            'rolloff': 0.0,
            'flux': 0.0,
            'zero_crossing_rate': 0.0,
            'attack_time': 0.0,
            'decay_time': 0.0
        }

    @property
    def drum_type(self) -> str:
        """Alias for type to maintain compatibility with external code"""
        return self.type

    @drum_type.setter
    def drum_type(self, value: str):
        """Setting drum_type also updates type for consistency"""
        self.type = value
        self._drum_type = value

    @property
    def position(self) -> float:
        """Alias for time for compatibility with existing code"""
        return self.time

    @property
    def segment_type(self) -> str:
        """Alias for segment to maintain compatibility with external code"""
        return self.segment

    @segment_type.setter
    def segment_type(self, value: str):
        """Setting segment_type also updates segment for consistency"""
        self.segment = value

    def set_spectral_features(self, features: Dict[str, float]) -> None:
        """
        Set spectral features for this peak.

        Args:
            features: Dictionary of spectral features
        """
        if features and isinstance(features, dict):
            # Update only the keys that exist in both dictionaries
            for key, value in features.items():
                if key in self.spectral_features:
                    self.spectral_features[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert peak to dictionary for serialization"""
        return {
            'time': self.time,
            'amplitude': self.amplitude,
            'confidence': self.confidence,
            'type': self.type,
            'drum_type': self.type,  # Include drum_type as an alias to type
            'frequency': self.frequency,
            'segment': self.segment,  # Include segment information
            'segment_type': self.segment,  # Include segment_type as an alias to segment
            'spectral_features': self.spectral_features  # Include spectral features
        }


class DrumClassificationModel:
    """
    Model for classifying drum hits based on spectral characteristics.

    This is a simplified model for demonstration purposes. In a production
    environment, this would be replaced with a more sophisticated model
    trained on a large dataset of drum sounds.
    """

    def __init__(self):
        self.frequency_ranges = {
            'kick': (20, 200),  # Low frequencies
            'snare': (200, 1200),  # Mid frequencies with some high
            'hi-hat': (800, 16000),  # High frequencies
            'cymbal': (1000, 16000),  # High frequencies with long decay
            'tom': (100, 500)  # Low-mid frequencies
        }


class AdvancedSignalProcessor:
    """
    Advanced signal processing utilities for audio analysis.
    """

    def __init__(self):
        self.stft_cache = {}
        self.max_cache_size = 10  # Maximum number of STFT matrices to cache
        self.energy_envelope_cache = {}  # Cache for energy envelopes

    def _calculate_energy_safely(self, normalized, max_abs):
        """
        Calculate signal energy in a numerically stable way that prevents overflow.

        Args:
            normalized: Normalized signal array
            max_abs: Maximum absolute value used for normalization

        Returns:
            Safely calculated energy value
        """
        # Calculate energy on normalized signal
        normalized_energy = np.sum(normalized * normalized)

        # Use logarithmic calculation to prevent overflow when scaling back
        if max_abs > 1.0:
            # Use logarithm to avoid overflow in large numbers
            log_scale = 2.0 * np.log(max_abs)
            energy = normalized_energy * np.exp(log_scale)
        else:
            # For small values, direct calculation is safe
            energy = normalized_energy * (max_abs * max_abs)

        return energy

    def multi_resolution_spectral_analysis(self, signal: np.ndarray, sr: int, window_sizes=None) -> Dict[
        int, Dict[str, np.ndarray]]:
        """
        Perform multi-resolution spectral analysis for better transient detection.

        This expert-level technique analyzes the signal at multiple time-frequency resolutions,
        which helps detect both fast transients (small windows) and tonal content (large windows).
        The multi-resolution approach provides complementary information that significantly
        improves drum hit detection accuracy.

        Args:
            signal: Input audio signal
            sr: Sample rate
            window_sizes: List of window sizes to use (in samples)

        Returns:
            Dictionary containing spectral features at multiple resolutions
        """
        if not LIBROSA_AVAILABLE:
            logger.warning("Librosa not available. Multi-resolution spectral analysis disabled.")
            return {}

        if window_sizes is None:
            # Default window sizes from small (good time resolution) to large (good frequency resolution)
            window_sizes = [256, 512, 1024, 2048, 4096]

        results = {}

        for window_size in window_sizes:
            hop_length = window_size // 4  # 75% overlap for better time resolution

            # Compute STFT with this window size
            if len(signal) >= window_size:
                try:
                    # Apply appropriate window function for better frequency resolution
                    stft = librosa.stft(signal, n_fft=window_size, hop_length=hop_length,
                                        win_length=window_size, window='hann')
                    mag_spec = np.abs(stft)

                    # Calculate spectral flux at this resolution (sensitive to transients)
                    diff = np.diff(mag_spec, axis=1)
                    diff = np.maximum(0, diff)  # Keep only positive changes
                    flux = np.sum(diff, axis=0)

                    # Calculate spectral derivative (rate of change of spectral flux)
                    # This is extremely effective for detecting sharp transients like drum hits
                    if len(flux) > 1:
                        flux_derivative = np.diff(flux)
                        # Emphasize positive changes (onsets) and suppress negative changes (offsets)
                        flux_derivative = np.concatenate(([0], np.maximum(0, flux_derivative)))
                    else:
                        flux_derivative = np.zeros_like(flux)

                    # Calculate spectral centroid (indicates where the "center of mass" of the spectrum is)
                    # Higher values indicate more high-frequency content (e.g., cymbals, hi-hats)
                    if mag_spec.shape[1] > 0:
                        freqs = librosa.fft_frequencies(sr=sr, n_fft=window_size)
                        freqs_2d = freqs[:, np.newaxis]  # Make it 2D for broadcasting

                        # Avoid division by zero
                        mag_spec_sum = np.sum(mag_spec, axis=0)
                        mag_spec_sum[mag_spec_sum == 0] = 1e-10

                        centroid = np.sum(freqs_2d * mag_spec, axis=0) / mag_spec_sum
                    else:
                        centroid = np.array([])

                    # Calculate spectral contrast (difference between peaks and valleys in the spectrum)
                    # This helps distinguish between different drum types
                    if hasattr(librosa.feature, 'spectral_contrast') and mag_spec.shape[1] > 0:
                        contrast = librosa.feature.spectral_contrast(S=mag_spec, sr=sr)
                        # Average across bands for a single contrast value per frame
                        mean_contrast = np.mean(contrast, axis=0) if contrast.size > 0 else np.array([])
                    else:
                        mean_contrast = np.array([])

                    # Store results for this resolution
                    results[window_size] = {
                        'flux': flux,
                        'flux_derivative': flux_derivative,
                        'centroid': centroid,
                        'contrast': mean_contrast,
                        'mag_spec': mag_spec,
                        'hop_length': hop_length,
                        'times': librosa.frames_to_time(np.arange(mag_spec.shape[1]), sr=sr, hop_length=hop_length)
                    }
                except Exception as e:
                    logger.warning(f"Error in multi-resolution analysis with window size {window_size}: {e}")
                    results[window_size] = None
            else:
                results[window_size] = None

        return results

    def spectral_flux_derivative_analysis(self, signal: np.ndarray, sr: int) -> Dict[str, np.ndarray]:
        """
        Perform spectral flux derivative analysis for precise onset detection.

        This expert technique focuses on the rate of change of spectral flux,
        which is particularly effective for detecting sharp transients like drum hits.
        The derivative emphasizes sudden changes in the spectrum, making it
        ideal for accurate drum hit detection.

        Args:
            signal: Input audio signal
            sr: Sample rate

        Returns:
            Dictionary containing onset detection features
        """
        if not LIBROSA_AVAILABLE:
            logger.warning("Librosa not available. Spectral flux derivative analysis disabled.")
            return {}

        try:
            # Use multiple window sizes for complementary information
            window_sizes = [512, 1024, 2048]
            results = {}

            for window_size in window_sizes:
                hop_length = window_size // 4

                # Compute STFT
                stft = librosa.stft(signal, n_fft=window_size, hop_length=hop_length, window='hann')
                mag_spec = np.abs(stft)

                # Calculate spectral flux
                diff = np.diff(np.concatenate((np.zeros((mag_spec.shape[0], 1)), mag_spec), axis=1), axis=1)
                diff = np.maximum(0, diff)  # Keep only positive changes
                flux = np.sum(diff, axis=0)

                # Calculate first derivative of flux (rate of change)
                if len(flux) > 1:
                    first_derivative = np.diff(np.concatenate(([0], flux)))
                    first_derivative = np.maximum(0, first_derivative)  # Keep only increases
                else:
                    first_derivative = np.zeros_like(flux)

                # Calculate second derivative (acceleration of change)
                if len(first_derivative) > 1:
                    second_derivative = np.diff(np.concatenate(([0], first_derivative)))
                    second_derivative = np.maximum(0, second_derivative)  # Keep only increases
                else:
                    second_derivative = np.zeros_like(first_derivative)

                # Normalize for consistent scaling
                if np.max(flux) > 0:
                    flux = flux / np.max(flux)
                if np.max(first_derivative) > 0:
                    first_derivative = first_derivative / np.max(first_derivative)
                if np.max(second_derivative) > 0:
                    second_derivative = second_derivative / np.max(second_derivative)

                # Calculate onset detection function by combining flux and derivatives
                # This weighted combination provides excellent drum hit detection
                onset_function = (0.3 * flux + 0.5 * first_derivative + 0.2 * second_derivative)

                # Calculate times for each frame
                times = librosa.frames_to_time(np.arange(len(onset_function)), sr=sr, hop_length=hop_length)

                results[window_size] = {
                    'flux': flux,
                    'first_derivative': first_derivative,
                    'second_derivative': second_derivative,
                    'onset_function': onset_function,
                    'times': times
                }

            return results
        except Exception as e:
            logger.error(f"Error in spectral flux derivative analysis: {e}")
            return {}

    def calculate_adaptive_snr(self, signal: np.ndarray, window_size: int = 2048, overlap: float = 0.75) -> Dict[
        str, np.ndarray]:
        """
        Calculate adaptive Signal-to-Noise Ratio (SNR) with local context awareness.

        This expert-level implementation uses a sliding window approach to calculate
        local SNR values that adapt to changing signal characteristics. This is crucial
        for accurate drum hit detection in varying acoustic environments.

        Args:
            signal: Input audio signal
            window_size: Size of analysis window
            overlap: Overlap between consecutive windows (0.0-1.0)

        Returns:
            Dictionary containing SNR analysis results
        """
        if len(signal) < window_size:
            return {
                'snr': np.array([]),
                'noise_floor': 0.0,
                'signal_power': np.array([]),
                'noise_power': np.array([])
            }

        try:
            # Calculate hop length based on overlap
            hop_length = int(window_size * (1 - overlap))
            if hop_length < 1:
                hop_length = 1

            # Number of frames
            n_frames = 1 + (len(signal) - window_size) // hop_length

            # Initialize arrays
            signal_power = np.zeros(n_frames)
            noise_power = np.zeros(n_frames)
            snr_values = np.zeros(n_frames)

            # Process each frame
            for i in range(n_frames):
                start = i * hop_length
                end = start + window_size

                if end <= len(signal):
                    frame = signal[start:end]

                    # Sort frame values by magnitude
                    sorted_frame = np.sort(np.abs(frame))

                    # Use lower percentiles as noise estimate
                    # This is more robust than using the minimum values
                    noise_percentile = 20  # Lower 20% is considered noise
                    noise_idx = int(len(sorted_frame) * noise_percentile / 100)

                    # Calculate noise power (average of lower percentile)
                    noise_est = sorted_frame[:noise_idx + 1]
                    noise_power[i] = np.mean(noise_est ** 2) if len(noise_est) > 0 else 1e-10

                    # Calculate signal power (average of upper percentile)
                    signal_percentile = 80  # Upper 20% is considered signal
                    signal_idx = int(len(sorted_frame) * signal_percentile / 100)
                    signal_est = sorted_frame[signal_idx:]
                    signal_power[i] = np.mean(signal_est ** 2) if len(signal_est) > 0 else 0.0

                    # Calculate SNR with protection against division by zero
                    if noise_power[i] > 1e-10:
                        snr_values[i] = 10 * np.log10(signal_power[i] / noise_power[i])
                    else:
                        snr_values[i] = 100.0  # High SNR for very low noise

            # Apply median filtering to smooth SNR values
            if len(snr_values) > 3:
                snr_values = scipy.signal.medfilt(snr_values, 3)

            # Calculate global noise floor (10th percentile of all noise power values)
            noise_floor = np.percentile(noise_power, 10) if len(noise_power) > 0 else 0.0

            return {
                'snr': snr_values,
                'noise_floor': noise_floor,
                'signal_power': signal_power,
                'noise_power': noise_power
            }
        except Exception as e:
            logger.error(f"Error calculating adaptive SNR: {e}")
            return {
                'snr': np.array([]),
                'noise_floor': 0.0,
                'signal_power': np.array([]),
                'noise_power': np.array([])
            }

    def calculate_bayesian_snr(self, signal: np.ndarray, prior_snr: float = 10.0, prior_weight: float = 0.2) -> float:
        """
        Calculate SNR using Bayesian estimation for more accurate noise floor detection.

        This expert technique uses prior knowledge about expected SNR values in drum recordings
        to produce more stable and accurate SNR estimates, especially in challenging conditions.

        Args:
            signal: Input audio signal
            prior_snr: Prior estimate of SNR in dB
            prior_weight: Weight of prior in final estimate (0.0-1.0)

        Returns:
            Estimated SNR in dB
        """
        if len(signal) == 0:
            return prior_snr

        try:
            # Convert prior from dB to linear scale
            prior_snr_linear = 10 ** (prior_snr / 10)

            # Calculate signal statistics
            signal_abs = np.abs(signal)

            # Use robust statistics to estimate signal and noise
            # Sort values by magnitude
            sorted_signal = np.sort(signal_abs)

            # Use lower 20% as noise estimate
            noise_idx = int(len(sorted_signal) * 0.2)
            noise_est = sorted_signal[:noise_idx + 1]
            noise_power = np.mean(noise_est ** 2) if len(noise_est) > 0 else 1e-10

            # Use upper 20% as signal estimate
            signal_idx = int(len(sorted_signal) * 0.8)
            signal_est = sorted_signal[signal_idx:]
            signal_power = np.mean(signal_est ** 2) if len(signal_est) > 0 else 0.0

            # Calculate measured SNR
            if noise_power > 1e-10:
                measured_snr_linear = signal_power / noise_power
            else:
                measured_snr_linear = 1000.0  # High SNR for very low noise

            # Apply Bayesian estimation
            # Combine prior and measured SNR using weighted average
            posterior_snr_linear = (prior_weight * prior_snr_linear +
                                    (1 - prior_weight) * measured_snr_linear)

            # Convert back to dB
            posterior_snr_db = 10 * np.log10(posterior_snr_linear)

            return posterior_snr_db
        except Exception as e:
            logger.error(f"Error calculating Bayesian SNR: {e}")
            return prior_snr

    def calculate_perceptual_snr(self, signal: np.ndarray, sr: int) -> float:
        """
        Calculate perceptually weighted SNR that emphasizes frequencies important for drum detection.

        This expert implementation applies psychoacoustic principles to weight different
        frequency bands according to their perceptual importance for drum hit detection.

        Args:
            signal: Input audio signal
            sr: Sample rate

        Returns:
            Perceptually weighted SNR in dB
        """
        if not LIBROSA_AVAILABLE or len(signal) == 0:
            return 0.0

        try:
            # Define frequency bands important for different drum types
            # These bands are based on the typical frequency ranges of common drum components
            bands = {
                'kick': (50, 200),  # Low frequencies for kick drums
                'snare': (200, 500),  # Mid-low frequencies for snare body
                'snare_high': (800, 1200),  # Mid-high frequencies for snare wire sound
                'hihat': (5000, 10000),  # High frequencies for hi-hats
                'toms': (100, 400),  # Low-mid frequencies for toms
                'cymbals': (8000, 16000)  # Very high frequencies for cymbals
            }

            # Define perceptual weights for each band
            # These weights emphasize the most important frequency ranges for drum detection
            weights = {
                'kick': 1.5,  # Emphasize kick drums
                'snare': 1.2,  # Emphasize snare drums
                'snare_high': 1.0,
                'hihat': 0.8,
                'toms': 1.0,
                'cymbals': 0.7
            }

            # Calculate STFT
            n_fft = 2048
            stft = librosa.stft(signal, n_fft=n_fft)
            mag_spec = np.abs(stft)

            # Get frequency bins
            freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

            # Calculate SNR for each band with perceptual weighting
            weighted_snr_sum = 0.0
            weight_sum = 0.0

            for band_name, (low_freq, high_freq) in bands.items():
                # Find frequency bin indices for this band
                band_indices = np.where((freqs >= low_freq) & (freqs <= high_freq))[0]

                if len(band_indices) > 0:
                    # Extract the band's spectrogram
                    band_spec = mag_spec[band_indices, :]

                    # Calculate statistics for this band
                    band_mean = np.mean(band_spec)
                    band_std = np.std(band_spec)

                    # Calculate SNR for this band (mean/std is a simple SNR measure)
                    if band_std > 1e-10:
                        band_snr = band_mean / band_std
                    else:
                        band_snr = 10.0  # Default for very low variance

                    # Apply perceptual weighting
                    weight = weights.get(band_name, 1.0)
                    weighted_snr_sum += band_snr * weight
                    weight_sum += weight

            # Calculate final weighted SNR
            if weight_sum > 0:
                perceptual_snr = weighted_snr_sum / weight_sum
            else:
                perceptual_snr = 1.0  # Default value

            # Convert to dB
            perceptual_snr_db = 10 * np.log10(perceptual_snr) if perceptual_snr > 0 else 0.0

            return perceptual_snr_db
        except Exception as e:
            logger.error(f"Error calculating perceptual SNR: {e}")
            return 0.0

    def calculate_bayesian_confidence(self, peak_features: Dict[str, float]) -> float:
        """
        Calculate Bayesian confidence score for a peak based on multiple features.

        This expert-level implementation uses Bayesian probability to combine multiple
        evidence sources into a single confidence score. This approach is much more
        robust than simple thresholding and can adapt to different signal characteristics.

        Args:
            peak_features: Dictionary of peak features

        Returns:
            Confidence score (0.0-1.0)
        """
        # Prior probability that this is a true drum hit (base rate)
        prior_prob = 0.5

        # Feature likelihoods for true positives (expert-calibrated values)
        # These values represent P(feature|true_hit)
        feature_weights = {
            'amplitude': {
                'very_low': 0.1,  # Very low amplitude is unlikely for true hits
                'low': 0.3,
                'medium': 0.7,
                'high': 0.9,
                'very_high': 0.95
            },
            'snr': {
                'very_low': 0.2,
                'low': 0.4,
                'medium': 0.7,
                'high': 0.85,
                'very_high': 0.95
            },
            'transient_sharpness': {
                'very_low': 0.1,
                'low': 0.3,
                'medium': 0.6,
                'high': 0.85,
                'very_high': 0.95
            },
            'spectral_flux': {
                'very_low': 0.2,
                'low': 0.4,
                'medium': 0.6,
                'high': 0.8,
                'very_high': 0.9
            },
            'rhythmic_alignment': {
                'very_low': 0.3,
                'low': 0.5,
                'medium': 0.7,
                'high': 0.85,
                'very_high': 0.95
            }
        }

        # Feature likelihoods for false positives
        # These values represent P(feature|false_hit)
        false_positive_weights = {
            'amplitude': {
                'very_low': 0.9,
                'low': 0.7,
                'medium': 0.4,
                'high': 0.2,
                'very_high': 0.1
            },
            'snr': {
                'very_low': 0.8,
                'low': 0.6,
                'medium': 0.4,
                'high': 0.2,
                'very_high': 0.1
            },
            'transient_sharpness': {
                'very_low': 0.9,
                'low': 0.7,
                'medium': 0.5,
                'high': 0.3,
                'very_high': 0.1
            },
            'spectral_flux': {
                'very_low': 0.8,
                'low': 0.6,
                'medium': 0.4,
                'high': 0.3,
                'very_high': 0.15
            },
            'rhythmic_alignment': {
                'very_low': 0.7,
                'low': 0.5,
                'medium': 0.4,
                'high': 0.2,
                'very_high': 0.1
            }
        }

        # Calculate likelihood ratio for each feature
        likelihood_ratio = 1.0

        for feature, value in peak_features.items():
            if feature in feature_weights:
                # Convert numerical values to categorical ratings
                if isinstance(value, (int, float)):
                    if value < 0.2:
                        category = 'very_low'
                    elif value < 0.4:
                        category = 'low'
                    elif value < 0.6:
                        category = 'medium'
                    elif value < 0.8:
                        category = 'high'
                    else:
                        category = 'very_high'
                else:
                    category = value  # Already a category string

                # Get likelihood values
                if category in feature_weights[feature] and category in false_positive_weights[feature]:
                    p_feature_given_true = feature_weights[feature][category]
                    p_feature_given_false = false_positive_weights[feature][category]

                    # Avoid division by zero
                    if p_feature_given_false > 0:
                        feature_lr = p_feature_given_true / p_feature_given_false
                    else:
                        feature_lr = 10.0  # High likelihood ratio if feature is very unlikely for false positives

                    likelihood_ratio *= feature_lr

        # Calculate posterior probability using Bayes' theorem
        posterior_odds = likelihood_ratio * (prior_prob / (1 - prior_prob))
        posterior_prob = posterior_odds / (1 + posterior_odds)

        # Ensure result is in valid range
        confidence = max(0.0, min(1.0, posterior_prob))

        return confidence

    def detect_statistical_outliers(self, peaks: List[Dict[str, Any]], feature: str = 'amplitude',
                                    z_threshold: float = 2.5) -> List[bool]:
        """
        Detect statistical outliers among peaks for false positive reduction.

        This expert technique uses statistical methods to identify peaks that are
        significantly different from the majority, which often indicates false positives.

        Args:
            peaks: List of peak dictionaries
            feature: Feature to analyze for outliers
            z_threshold: Z-score threshold for outlier detection

        Returns:
            List of boolean values (True for outliers)
        """
        if not peaks:
            return []

        try:
            # Extract feature values
            values = []
            for peak in peaks:
                if feature in peak and isinstance(peak[feature], (int, float)):
                    values.append(peak[feature])
                else:
                    values.append(0.0)  # Default value if feature is missing

            values = np.array(values)

            # Calculate robust statistics (less affected by outliers)
            median_val = np.median(values)

            # Use median absolute deviation (MAD) instead of standard deviation
            # MAD is more robust to outliers
            mad = np.median(np.abs(values - median_val))

            # Convert MAD to equivalent standard deviation
            # For normal distribution, std ≈ 1.4826 * MAD
            robust_std = 1.4826 * mad

            # Avoid division by zero
            if robust_std < 1e-10:
                robust_std = 1.0

            # Calculate modified Z-scores
            z_scores = np.abs(values - median_val) / robust_std

            # Identify outliers
            outliers = z_scores > z_threshold

            return outliers.tolist()
        except Exception as e:
            logger.error(f"Error detecting statistical outliers: {e}")
            return [False] * len(peaks)

    def analyze_autocorrelation(self, peak_times: List[float], max_lag: float = 2.0) -> Dict[str, Any]:
        """
        Analyze autocorrelation of peak times for rhythmic consistency validation.

        This expert technique examines the temporal pattern of peaks to identify
        rhythmic structure, which is crucial for validating drum hits in musical context.

        Args:
            peak_times: List of peak times in seconds
            max_lag: Maximum lag time to analyze in seconds

        Returns:
            Dictionary containing autocorrelation analysis results
        """
        if len(peak_times) < 3:
            return {
                'has_rhythm': False,
                'tempo_bpm': 0.0,
                'confidence': 0.0,
                'autocorr': np.array([])
            }

        try:
            # Sort times to ensure they're in order
            peak_times = sorted(peak_times)

            # Convert to numpy array
            times = np.array(peak_times)

            # Calculate all pairwise time differences
            time_diffs = []
            for i in range(len(times)):
                for j in range(i + 1, len(times)):
                    diff = times[j] - times[i]
                    if diff <= max_lag:  # Only consider differences up to max_lag
                        time_diffs.append(diff)

            if not time_diffs:
                return {
                    'has_rhythm': False,
                    'tempo_bpm': 0.0,
                    'confidence': 0.0,
                    'autocorr': np.array([])
                }

            # Create histogram of time differences
            hist_bins = 100  # Number of bins in histogram
            hist, bin_edges = np.histogram(time_diffs, bins=hist_bins, range=(0, max_lag))
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

            # Smooth histogram
            if len(hist) > 5:
                hist_smooth = scipy.signal.savgol_filter(hist, 5, 2)
            else:
                hist_smooth = hist

            # Find peaks in histogram (these represent common time intervals)
            if len(hist_smooth) > 3:
                peaks, _ = scipy.signal.find_peaks(hist_smooth, height=max(hist_smooth) * 0.5)
                peak_times = bin_centers[peaks]
                peak_heights = hist_smooth[peaks]
            else:
                peak_times = []
                peak_heights = []

            # Check if we found any significant peaks
            if len(peak_times) > 0:
                # Sort by height (most common intervals first)
                sorted_indices = np.argsort(-peak_heights)
                sorted_peak_times = peak_times[sorted_indices]
                sorted_peak_heights = peak_heights[sorted_indices]

                # Calculate tempo from most prominent peak
                if len(sorted_peak_times) > 0:
                    beat_duration = sorted_peak_times[0]  # Most common interval
                    if beat_duration > 0:
                        tempo_bpm = 60.0 / beat_duration
                    else:
                        tempo_bpm = 120.0  # Default
                else:
                    tempo_bpm = 120.0  # Default

                # Calculate confidence based on peak prominence
                if len(sorted_peak_heights) > 0 and np.sum(hist_smooth) > 0:
                    # Ratio of the highest peak to the total sum
                    confidence = sorted_peak_heights[0] / np.sum(hist_smooth)
                else:
                    confidence = 0.0

                return {
                    'has_rhythm': True,
                    'tempo_bpm': tempo_bpm,
                    'confidence': confidence,
                    'autocorr': hist_smooth,
                    'peak_intervals': sorted_peak_times,
                    'peak_strengths': sorted_peak_heights
                }
            else:
                return {
                    'has_rhythm': False,
                    'tempo_bpm': 0.0,
                    'confidence': 0.0,
                    'autocorr': hist_smooth
                }
        except Exception as e:
            logger.error(f"Error analyzing autocorrelation: {e}")
            return {
                'has_rhythm': False,
                'tempo_bpm': 0.0,
                'confidence': 0.0,
                'autocorr': np.array([])
            }

    def calculate_consensus_score(self, detection_methods: Dict[str, List[float]],
                                  tolerance: float = 0.05) -> Dict[float, float]:
        """
        Calculate consensus score across multiple detection methods using cross-correlation.

        This expert technique combines results from different detection algorithms to
        produce more reliable drum hit detections. Peaks detected by multiple methods
        receive higher confidence scores.

        Args:
            detection_methods: Dictionary mapping method names to lists of detected peak times
            tolerance: Time tolerance for matching peaks between methods (in seconds)

        Returns:
            Dictionary mapping peak times to consensus scores
        """
        if not detection_methods:
            return {}

        try:
            # Collect all unique peak times
            all_peaks = set()
            for method, peaks in detection_methods.items():
                all_peaks.update(peaks)

            all_peaks = sorted(all_peaks)

            # Calculate consensus for each peak
            consensus_scores = {}

            for peak_time in all_peaks:
                # Count how many methods detected this peak (within tolerance)
                count = 0
                total_methods = len(detection_methods)

                for method, peaks in detection_methods.items():
                    # Check if this method detected a peak close to peak_time
                    for p in peaks:
                        if abs(p - peak_time) <= tolerance:
                            count += 1
                            break

                # Calculate consensus score (0.0-1.0)
                if total_methods > 0:
                    score = count / total_methods
                else:
                    score = 0.0

                consensus_scores[peak_time] = score

            return consensus_scores
        except Exception as e:
            logger.error(f"Error calculating consensus score: {e}")
            return {}

    def analyze_hierarchical_beat_structure(self, peak_times: List[float],
                                            min_tempo: float = 60.0,
                                            max_tempo: float = 200.0) -> Dict[str, Any]:
        """
        Analyze hierarchical beat structure (meter, beat, subdivision) for advanced rhythm validation.

        This expert-level technique identifies the hierarchical rhythmic structure in the peaks,
        which is crucial for validating drum hits in a musical context. It can identify the
        meter (e.g., 4/4, 3/4), beat positions, and subdivisions.

        Args:
            peak_times: List of peak times in seconds
            min_tempo: Minimum tempo to consider in BPM
            max_tempo: Maximum tempo to consider in BPM

        Returns:
            Dictionary containing hierarchical beat analysis results
        """
        if len(peak_times) < 4:
            return {
                'success': False,
                'meter': 4,  # Default to 4/4
                'tempo': 120.0,  # Default tempo
                'beat_duration': 0.5,  # 500ms per beat at 120 BPM
                'confidence': 0.0
            }

        try:
            # Sort times
            peak_times = sorted(peak_times)

            # Calculate inter-onset intervals (IOIs)
            iois = np.diff(peak_times)

            # Find the most common IOI using histogram analysis
            hist, bin_edges = np.histogram(iois, bins=50, range=(60.0 / max_tempo, 60.0 / min_tempo))
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

            # Find peaks in histogram
            if len(hist) > 3:
                # Smooth histogram for better peak detection
                hist_smooth = scipy.signal.savgol_filter(hist, 5, 2)
                peaks, _ = scipy.signal.find_peaks(hist_smooth, height=max(hist_smooth) * 0.5)
                peak_iois = bin_centers[peaks]
                peak_heights = hist_smooth[peaks]
            else:
                peak_iois = []
                peak_heights = []

            if not peak_iois:
                return {
                    'success': False,
                    'meter': 4,
                    'tempo': 120.0,
                    'beat_duration': 0.5,
                    'confidence': 0.0
                }

            # Sort by peak height (most common IOIs first)
            sorted_indices = np.argsort(-peak_heights)
            sorted_iois = peak_iois[sorted_indices]

            # The most common IOI is likely the beat duration or a subdivision
            candidate_durations = sorted_iois[:min(3, len(sorted_iois))]

            # Try to identify the beat level (not subdivision or multiple beats)
            beat_duration = candidate_durations[0]  # Start with most common IOI

            # Check if this is likely a subdivision
            for cand in candidate_durations:
                # If there's an IOI about twice as long, this might be a subdivision
                for other in candidate_durations:
                    ratio = other / cand
                    if 1.8 < ratio < 2.2:  # Close to 2:1 ratio
                        # The longer one is more likely the beat
                        beat_duration = other
                        break

            # Calculate tempo from beat duration
            tempo = 60.0 / beat_duration

            # Determine meter (time signature)
            # Count how many peaks fall on each beat position
            beat_positions = []
            for t in peak_times:
                # Calculate position within beat (0 to beat_duration)
                beat_pos = t % beat_duration
                # Normalize to 0-1 range
                normalized_pos = beat_pos / beat_duration
                beat_positions.append(normalized_pos)

            # Create histogram of beat positions
            pos_hist, pos_bins = np.histogram(beat_positions, bins=16, range=(0, 1))

            # Count peaks at strong beat positions for different meters
            meter_scores = {}
            for meter in [2, 3, 4, 6, 8]:
                score = 0
                # Check how many peaks fall on the 1st beat (strongest)
                first_beat_count = sum(pos_hist[i] for i in range(len(pos_hist))
                                       if abs(pos_bins[i] - 0.0) < 0.1)
                score += first_beat_count * 2  # Double weight for the 1st beat

                # Check other strong beats based on meter
                if meter == 2:  # 2/4: strong beats at 1
                    pass  # Already counted the 1st beat
                elif meter == 3:  # 3/4: strong beats at 1
                    pass  # Already counted the 1st beat
                elif meter == 4:  # 4/4: strong beats at 1 and 3
                    third_beat_count = sum(pos_hist[i] for i in range(len(pos_hist))
                                           if abs(pos_bins[i] - 0.5) < 0.1)
                    score += third_beat_count
                elif meter == 6:  # 6/8: strong beats at 1 and 4
                    fourth_beat_count = sum(pos_hist[i] for i in range(len(pos_hist))
                                            if abs(pos_bins[i] - 0.5) < 0.1)
                    score += fourth_beat_count
                elif meter == 8:  # 8/8: strong beats at 1 and 5
                    fifth_beat_count = sum(pos_hist[i] for i in range(len(pos_hist))
                                           if abs(pos_bins[i] - 0.5) < 0.1)
                    score += fifth_beat_count

                meter_scores[meter] = score

            # Choose meter with highest score
            best_meter = max(meter_scores.items(), key=lambda x: x[1])[0]

            # Calculate confidence based on how well peaks align with beat grid
            aligned_count = 0
            total_count = len(peak_times)

            for t in peak_times:
                # Calculate position within beat
                beat_pos = t % beat_duration
                # Check if it's close to a beat subdivision
                for i in range(best_meter):
                    subdiv_pos = i * beat_duration / best_meter
                    if abs(beat_pos - subdiv_pos) < 0.05 * beat_duration:  # 5% tolerance
                        aligned_count += 1
                        break

            confidence = aligned_count / total_count if total_count > 0 else 0.0

            return {
                'success': True,
                'meter': best_meter,
                'tempo': tempo,
                'beat_duration': beat_duration,
                'confidence': confidence,
                'beat_positions': beat_positions,
                'position_histogram': pos_hist.tolist()
            }
        except Exception as e:
            logger.error(f"Error analyzing hierarchical beat structure: {e}")
            return {
                'success': False,
                'meter': 4,
                'tempo': 120.0,
                'beat_duration': 0.5,
                'confidence': 0.0
            }

    def match_groove_template(self, peak_times: List[float], peak_types: List[str] = None) -> Dict[str, Any]:
        """
        Match peaks against common drum groove templates for pattern-based validation.

        This expert technique compares the detected peaks against a library of common
        drum patterns to identify known structures, which helps validate the detections
        and identify false positives.

        Args:
            peak_times: List of peak times in seconds
            peak_types: Optional list of drum types corresponding to peak_times

        Returns:
            Dictionary containing groove matching results
        """
        if len(peak_times) < 4:
            return {
                'matched': False,
                'pattern_name': 'unknown',
                'confidence': 0.0
            }

        try:
            # Define common drum groove templates
            # Each template is defined as a list of (position, drum_type) tuples
            # Position is normalized to 0-1 range within a measure
            templates = {
                'basic_rock': [
                    (0.0, 'kick'),  # Beat 1: kick
                    (0.0, 'crash'),  # Beat 1: crash (optional)
                    (0.25, 'snare'),  # Beat 2: snare
                    (0.5, 'kick'),  # Beat 3: kick
                    (0.75, 'snare'),  # Beat 4: snare
                    # Hi-hat on eighth notes
                    (0.0, 'hi-hat'), (0.125, 'hi-hat'), (0.25, 'hi-hat'), (0.375, 'hi-hat'),
                    (0.5, 'hi-hat'), (0.625, 'hi-hat'), (0.75, 'hi-hat'), (0.875, 'hi-hat')
                ],
                'basic_funk': [
                    (0.0, 'kick'),  # Beat 1: kick
                    (0.25, 'snare'),  # Beat 2: snare
                    (0.375, 'kick'),  # Beat 2&: kick
                    (0.5, 'kick'),  # Beat 3: kick
                    (0.75, 'snare'),  # Beat 4: snare
                    # Hi-hat on sixteenth notes
                    (0.0, 'hi-hat'), (0.0625, 'hi-hat'), (0.125, 'hi-hat'), (0.1875, 'hi-hat'),
                    (0.25, 'hi-hat'), (0.3125, 'hi-hat'), (0.375, 'hi-hat'), (0.4375, 'hi-hat'),
                    (0.5, 'hi-hat'), (0.5625, 'hi-hat'), (0.625, 'hi-hat'), (0.6875, 'hi-hat'),
                    (0.75, 'hi-hat'), (0.8125, 'hi-hat'), (0.875, 'hi-hat'), (0.9375, 'hi-hat')
                ],
                'jazz_ride': [
                    (0.0, 'ride'),  # Beat 1: ride
                    (0.0, 'kick'),  # Beat 1: kick
                    (0.25, 'ride'),  # Beat 2: ride
                    (0.5, 'ride'),  # Beat 3: ride
                    (0.5, 'kick'),  # Beat 3: kick
                    (0.75, 'ride'),  # Beat 4: ride
                    (0.33, 'snare'),  # Swing snare on 2
                    (0.67, 'snare')  # Swing snare on 4
                ],
                'half_time': [
                    (0.0, 'kick'),  # Beat 1: kick
                    (0.5, 'snare'),  # Beat 3: snare
                    # Hi-hat on quarter notes
                    (0.0, 'hi-hat'), (0.25, 'hi-hat'), (0.5, 'hi-hat'), (0.75, 'hi-hat')
                ]
            }

            # First, estimate the tempo and measure length
            # Use autocorrelation to find the beat duration
            autocorr_result = self.analyze_autocorrelation(peak_times)

            if not autocorr_result['has_rhythm'] or autocorr_result['tempo_bpm'] < 40:
                return {
                    'matched': False,
                    'pattern_name': 'unknown',
                    'confidence': 0.0
                }

            # Estimate measure length (assuming 4/4 time signature)
            beat_duration = 60.0 / autocorr_result['tempo_bpm']
            measure_duration = 4 * beat_duration  # 4 beats per measure in 4/4

            # Normalize peak times to positions within measures
            normalized_positions = []
            for t in peak_times:
                # Position within measure (0-1 range)
                pos = (t % measure_duration) / measure_duration
                normalized_positions.append(pos)

            # Match against templates
            best_match = 'unknown'
            best_confidence = 0.0

            for pattern_name, template in templates.items():
                # Extract template positions
                template_positions = [pos for pos, _ in template]

                # Count matches
                matches = 0
                total_template_points = len(template_positions)

                for template_pos in template_positions:
                    # Check if any peak is close to this template position
                    for peak_pos in normalized_positions:
                        # Calculate circular distance (to handle wrapping around measure boundaries)
                        dist = min(abs(peak_pos - template_pos), 1 - abs(peak_pos - template_pos))
                        if dist < 0.05:  # 5% tolerance
                            matches += 1
                            break

                # If peak_types are provided, also check drum type matches
                if peak_types and len(peak_types) == len(peak_times):
                    type_matches = 0
                    total_type_checks = 0

                    for i, peak_pos in enumerate(normalized_positions):
                        peak_type = peak_types[i]

                        # Find closest template position
                        closest_idx = -1
                        closest_dist = float('inf')

                        for j, (template_pos, _) in enumerate(template):
                            dist = min(abs(peak_pos - template_pos), 1 - abs(peak_pos - template_pos))
                            if dist < closest_dist:
                                closest_dist = dist
                                closest_idx = j

                        # Check if drum type matches
                        if closest_idx >= 0 and closest_dist < 0.05:
                            template_type = template[closest_idx][1]
                            if peak_type == template_type:
                                type_matches += 1
                            total_type_checks += 1

                    # Adjust match score based on type matches
                    if total_type_checks > 0:
                        type_match_ratio = type_matches / total_type_checks
                        matches = matches * (0.5 + 0.5 * type_match_ratio)  # Weighted combination

                # Calculate confidence
                confidence = matches / total_template_points if total_template_points > 0 else 0.0

                # Keep track of best match
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = pattern_name

            return {
                'matched': best_confidence > 0.6,  # Require 60% confidence for a match
                'pattern_name': best_match,
                'confidence': best_confidence
            }
        except Exception as e:
            logger.error(f"Error matching groove template: {e}")
            return {
                'matched': False,
                'pattern_name': 'unknown',
                'confidence': 0.0
            }

    def calculate_adaptive_grid_alignment(self, peak_times: List[float],
                                          tolerance_range: Tuple[float, float] = (0.03, 0.1)) -> Dict[str, Any]:
        """
        Calculate adaptive grid alignment with confidence scoring for rhythm validation.

        This expert technique analyzes how well peaks align with an adaptive rhythmic grid,
        adjusting the grid parameters to find the best fit. This is crucial for validating
        drum hits in complex musical contexts.

        Args:
            peak_times: List of peak times in seconds
            tolerance_range: Range of tolerance values to try (min, max)

        Returns:
            Dictionary containing grid alignment results
        """
        if len(peak_times) < 4:
            return {
                'aligned': False,
                'grid_tempo': 120.0,
                'grid_offset': 0.0,
                'alignment_score': 0.0,
                'aligned_peaks': []
            }

        try:
            # Sort times
            peak_times = sorted(peak_times)

            # Calculate inter-onset intervals (IOIs)
            iois = np.diff(peak_times)

            # Find the most common IOI using histogram analysis
            hist, bin_edges = np.histogram(iois, bins=50)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

            # Find peaks in histogram
            if len(hist) > 3:
                # Smooth histogram for better peak detection
                hist_smooth = scipy.signal.savgol_filter(hist, 5, 2)
                peaks, _ = scipy.signal.find_peaks(hist_smooth, height=max(hist_smooth) * 0.3)
                peak_iois = bin_centers[peaks]
                peak_heights = hist_smooth[peaks]
            else:
                peak_iois = []
                peak_heights = []

            if not peak_iois:
                # Fallback: use median IOI
                median_ioi = np.median(iois)
                peak_iois = [median_ioi]
                peak_heights = [1.0]

            # Sort by peak height (most common IOIs first)
            sorted_indices = np.argsort(-peak_heights)
            sorted_iois = peak_iois[sorted_indices]

            # Try different grid configurations
            best_score = 0.0
            best_grid_tempo = 120.0
            best_grid_offset = 0.0
            best_aligned_peaks = []
            best_tolerance = 0.05

            # Try different base IOIs (could be beat duration or subdivisions)
            for base_ioi in sorted_iois[:min(3, len(sorted_iois))]:
                # Try different subdivisions
                for subdivision in [1, 2, 3, 4, 6, 8]:
                    grid_interval = base_ioi / subdivision

                    # Convert to tempo in BPM
                    grid_tempo = 60.0 / grid_interval

                    # Skip unreasonable tempos
                    if grid_tempo < 40 or grid_tempo > 300:
                        continue

                    # Try different offsets
                    for offset_fraction in [0.0, 0.125, 0.25, 0.375, 0.5]:
                        grid_offset = grid_interval * offset_fraction

                        # Try different tolerance values
                        min_tol, max_tol = tolerance_range
                        for tolerance_factor in [0.5, 0.75, 1.0, 1.25, 1.5]:
                            tolerance = min_tol + tolerance_factor * (max_tol - min_tol)

                            # Count aligned peaks
                            aligned_peaks = []

                            for peak_time in peak_times:
                                # Calculate distance to nearest grid point
                                adjusted_time = peak_time - grid_offset
                                grid_position = adjusted_time % grid_interval
                                distance = min(grid_position, grid_interval - grid_position)

                                # Check if peak aligns with grid
                                if distance <= tolerance * grid_interval:
                                    aligned_peaks.append(peak_time)

                            # Calculate alignment score
                            alignment_score = len(aligned_peaks) / len(peak_times)

                            # Adjust score based on grid complexity
                            # Prefer simpler grids when scores are similar
                            complexity_penalty = 0.02 * (subdivision - 1)
                            adjusted_score = alignment_score - complexity_penalty

                            # Keep track of best configuration
                            if adjusted_score > best_score:
                                best_score = adjusted_score
                                best_grid_tempo = grid_tempo * subdivision  # Convert to beat-level tempo
                                best_grid_offset = grid_offset
                                best_aligned_peaks = aligned_peaks
                                best_tolerance = tolerance

            return {
                'aligned': best_score > 0.7,  # Require 70% alignment for success
                'grid_tempo': best_grid_tempo,
                'grid_offset': best_grid_offset,
                'alignment_score': best_score,
                'aligned_peaks': best_aligned_peaks,
                'tolerance': best_tolerance
            }
        except Exception as e:
            logger.error(f"Error calculating adaptive grid alignment: {e}")
            return {
                'aligned': False,
                'grid_tempo': 120.0,
                'grid_offset': 0.0,
                'alignment_score': 0.0,
                'aligned_peaks': []
            }

    def detect_polyrhythms(self, peak_times: List[float], peak_types: List[str] = None) -> Dict[str, Any]:
        """
        Detect polyrhythms and complex rhythmic structures in peak patterns.

        This expert technique identifies multiple simultaneous rhythmic layers,
        which is crucial for correctly handling complex drum patterns with polyrhythms.

        Args:
            peak_times: List of peak times in seconds
            peak_types: Optional list of drum types corresponding to peak_times

        Returns:
            Dictionary containing polyrhythm detection results
        """
        if len(peak_times) < 8:
            return {
                'has_polyrhythm': False,
                'layers': [],
                'confidence': 0.0
            }

        try:
            # Group peaks by drum type if available
            type_groups = {}

            if peak_types and len(peak_types) == len(peak_times):
                for i, peak_time in enumerate(peak_times):
                    peak_type = peak_types[i]
                    if peak_type not in type_groups:
                        type_groups[peak_type] = []
                    type_groups[peak_type].append(peak_time)
            else:
                # If no type information, treat all peaks as one group
                type_groups['generic'] = peak_times

            # Analyze each group for rhythmic patterns
            rhythmic_layers = []

            for drum_type, times in type_groups.items():
                if len(times) < 4:
                    continue  # Need enough peaks to detect a pattern

                # Sort times
                times = sorted(times)

                # Calculate IOIs
                iois = np.diff(times)

                # Find the most common IOI using histogram
                hist, bin_edges = np.histogram(iois, bins=30)
                bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

                # Find peaks in histogram
                if len(hist) > 3:
                    # Smooth histogram for better peak detection
                    hist_smooth = scipy.signal.savgol_filter(hist, 5, 2)
                    peaks, _ = scipy.signal.find_peaks(hist_smooth, height=max(hist_smooth) * 0.3)
                    peak_iois = bin_centers[peaks]
                    peak_heights = hist_smooth[peaks]

                    if len(peak_iois) > 0:
                        # Sort by peak height
                        sorted_indices = np.argsort(-peak_heights)
                        sorted_iois = peak_iois[sorted_indices]

                        # Calculate tempo from most common IOI
                        main_ioi = sorted_iois[0]
                        tempo = 60.0 / main_ioi

                        # Calculate regularity (how consistent the pattern is)
                        # Count peaks that are close to expected grid points
                        grid_aligned = 0
                        for i in range(1, len(times)):
                            expected_time = times[0] + i * main_ioi
                            closest_peak = min(times, key=lambda t: abs(t - expected_time))
                            if abs(closest_peak - expected_time) < 0.1 * main_ioi:
                                grid_aligned += 1

                        regularity = grid_aligned / (len(times) - 1) if len(times) > 1 else 0.0

                        # Add this rhythmic layer
                        rhythmic_layers.append({
                            'drum_type': drum_type,
                            'tempo': tempo,
                            'ioi': main_ioi,
                            'regularity': regularity,
                            'peak_count': len(times)
                        })

            # Check for polyrhythm by comparing tempos/IOIs between layers
            has_polyrhythm = False
            polyrhythm_confidence = 0.0

            if len(rhythmic_layers) >= 2:
                # Sort layers by regularity (most regular first)
                rhythmic_layers.sort(key=lambda x: x['regularity'], reverse=True)

                # Compare the top layers
                for i in range(len(rhythmic_layers) - 1):
                    for j in range(i + 1, len(rhythmic_layers)):
                        layer1 = rhythmic_layers[i]
                        layer2 = rhythmic_layers[j]

                        # Only consider layers with good regularity
                        if layer1['regularity'] < 0.7 or layer2['regularity'] < 0.7:
                            continue

                        # Calculate tempo ratio
                        tempo_ratio = layer1['tempo'] / layer2['tempo'] if layer2['tempo'] > 0 else 0

                        # Check for common polyrhythm ratios (e.g., 3:2, 4:3, 5:4)
                        common_ratios = [(3, 2), (4, 3), (5, 4), (5, 3), (7, 4), (7, 5)]

                        for num, denom in common_ratios:
                            expected_ratio = num / denom
                            ratio_error = abs(tempo_ratio - expected_ratio) / expected_ratio

                            if ratio_error < 0.1:  # Within 10% of expected ratio
                                has_polyrhythm = True
                                polyrhythm_confidence = max(polyrhythm_confidence,
                                                            1.0 - ratio_error)  # Higher confidence for closer match

                                # Add polyrhythm information to layers
                                layer1['polyrhythm_role'] = f"{num}:{denom} (numerator)"
                                layer2['polyrhythm_role'] = f"{num}:{denom} (denominator)"
                                break

            return {
                'has_polyrhythm': has_polyrhythm,
                'layers': rhythmic_layers,
                'confidence': polyrhythm_confidence
            }
        except Exception as e:
            logger.error(f"Error detecting polyrhythms: {e}")
            return {
                'has_polyrhythm': False,
                'layers': [],
                'confidence': 0.0
            }

    def _update_config_for_file_duration(self, duration_seconds: float) -> None:
        """
        Update configuration parameters based on file duration.

        This method adjusts various configuration parameters to optimize
        processing for files of different lengths, ensuring that long files
        are processed efficiently while maintaining accuracy.

        Args:
            duration_seconds: Duration of the audio file in seconds
        """
        if duration_seconds <= 0:
            # Default values for when duration is unknown
            self.config['max_peaks'] = 2000
            return

        # Calculate appropriate max_peaks based on file duration
        # For longer files, we expect more peaks
        minutes = duration_seconds / 60.0

        # Calculate max peaks based on expected peaks per minute
        # with a reasonable upper limit
        calculated_max_peaks = int(minutes * self.config['peaks_per_minute'])

        # Ensure we have a reasonable minimum and maximum
        min_peaks = 1000  # Minimum peaks to detect
        max_peaks = 10000  # Maximum peaks to avoid memory issues

        self.config['max_peaks'] = max(min_peaks, min(calculated_max_peaks, max_peaks))

        # Adjust other parameters based on file duration
        if duration_seconds > 300:  # Files longer than 5 minutes
            # For very long files, be more selective to avoid too many peaks
            self.config['madmom_onset_threshold'] = 0.45  # Slightly more selective

            # Enable memory optimization for long files
            self.config['memory_optimization'] = True

            # Log the adjustments
            logger.info(f"Adjusted configuration for long file ({minutes:.1f} minutes): "
                        f"max_peaks={self.config['max_peaks']}, "
                        f"onset_threshold={self.config['madmom_onset_threshold']}")
            print(f"📊 Adjusted configuration for long file ({minutes:.1f} minutes): "
                  f"max_peaks={self.config['max_peaks']}")
        else:
            # For shorter files, we can be less selective
            self.config['madmom_onset_threshold'] = 0.4

            # Log the adjustments
            logger.info(f"Using standard configuration for {minutes:.1f} minute file: "
                        f"max_peaks={self.config['max_peaks']}")
            print(f"📊 Using standard configuration for {minutes:.1f} minute file: "
                  f"max_peaks={self.config['max_peaks']}")

    def _get_cached_stft(self, signal_hash: int, hop_length: int, n_fft: int, stft=None):
        """
        Get cached STFT or compute and cache it.

        Args:
            signal_hash: Hash of the signal
            hop_length: Hop length for STFT
            n_fft: FFT size
            stft: STFT matrix to cache if not already cached

        Returns:
            Cached STFT matrix or None if not in cache and no new STFT provided
        """
        cache_key = f"{signal_hash}_{hop_length}_{n_fft}"
        if cache_key in self.stft_cache:
            return self.stft_cache[cache_key]

        # If a new STFT is provided, cache it
        if stft is not None:
            # If cache is full, remove the oldest entry
            if len(self.stft_cache) >= self.max_cache_size:
                oldest_key = next(iter(self.stft_cache))
                del self.stft_cache[oldest_key]

            # Add new entry to cache
            self.stft_cache[cache_key] = stft
            return stft

        return None

    def adaptive_threshold(self, signal: np.ndarray, window_size: int = 1024) -> np.ndarray:
        """
        Apply adaptive thresholding to a signal.

        Args:
            signal: Input signal
            window_size: Size of the moving window

        Returns:
            Thresholded signal
        """
        if not SCIPY_AVAILABLE:
            return signal

        # Calculate moving average
        window = np.ones(window_size) / window_size
        moving_avg = np.convolve(np.abs(signal), window, mode='same')

        # Apply threshold
        threshold = moving_avg * 1.5
        thresholded = np.where(np.abs(signal) > threshold, signal, 0)

        return thresholded

    @staticmethod
    def spectral_flux(stft_matrix: np.ndarray) -> np.ndarray:
        """
        Calculate spectral flux from STFT matrix with improved error handling.

        Args:
            stft_matrix: Short-time Fourier transform matrix

        Returns:
            Spectral flux array
        """
        # Check if STFT matrix is valid
        if stft_matrix is None or stft_matrix.size == 0:
            logger.warning("Empty STFT matrix provided to spectral_flux. Returning empty array.")
            return np.array([])

        # Check for NaN or infinite values
        if not np.all(np.isfinite(stft_matrix)):
            logger.warning("STFT matrix contains NaN or infinite values. Cleaning matrix...")
            stft_matrix = np.nan_to_num(stft_matrix, nan=0.0, posinf=0.0, neginf=0.0)

        try:
            # Calculate magnitude spectrogram
            mag_spec = np.abs(stft_matrix)

            # Ensure we have at least 2 frames for diff
            if mag_spec.shape[1] < 2:
                logger.warning("STFT matrix has fewer than 2 frames. Cannot calculate flux.")
                return np.zeros(1)

            # Calculate difference between consecutive frames
            diff = np.diff(mag_spec, axis=1)

            # Keep only positive differences (increases in energy)
            diff = np.maximum(0, diff)

            # Sum across frequency bins
            flux = np.sum(diff, axis=0)

            # Check for NaN or infinite values in result
            if not np.all(np.isfinite(flux)):
                logger.warning("Spectral flux contains NaN or infinite values. Returning zeros.")
                return np.zeros_like(flux)

            return flux

        except Exception as e:
            logger.warning(f"Error calculating spectral flux: {e}. Returning empty array.")
            # Return empty array with same number of frames as input (minus 1 for diff)
            if stft_matrix.ndim > 1 and stft_matrix.shape[1] > 1:
                return np.zeros(stft_matrix.shape[1] - 1)
            else:
                return np.array([0.0])

    @staticmethod
    def high_frequency_content(stft_matrix: np.ndarray, sr: int) -> np.ndarray:
        """
        Calculate high frequency content from STFT matrix with improved error handling.

        Args:
            stft_matrix: Short-time Fourier transform matrix
            sr: Sample rate

        Returns:
            High frequency content array
        """
        # Check if STFT matrix is valid
        if stft_matrix is None or stft_matrix.size == 0:
            logger.warning("Empty STFT matrix provided to high_frequency_content. Returning empty array.")
            return np.array([])

        # Check for NaN or infinite values
        if not np.all(np.isfinite(stft_matrix)):
            logger.warning("STFT matrix contains NaN or infinite values. Cleaning matrix...")
            stft_matrix = np.nan_to_num(stft_matrix, nan=0.0, posinf=0.0, neginf=0.0)

        try:
            # Calculate magnitude spectrogram
            mag_spec = np.abs(stft_matrix)

            # Validate dimensions
            if mag_spec.ndim < 2 or mag_spec.shape[0] < 2:
                logger.warning("Invalid STFT matrix dimensions for high_frequency_content.")
                return np.zeros(1 if mag_spec.ndim < 2 else mag_spec.shape[1])

            # Create frequency weights (higher weights for higher frequencies)
            n_fft = (mag_spec.shape[0] - 1) * 2
            freqs = np.linspace(0, sr / 2, mag_spec.shape[0])
            weights = freqs / (sr / 2)  # Normalize to [0, 1]

            # Apply weights and sum
            weighted_spec = mag_spec * weights[:, np.newaxis]
            hfc = np.sum(weighted_spec, axis=0)

            # Check for NaN or infinite values in result
            if not np.all(np.isfinite(hfc)):
                logger.warning("High frequency content contains NaN or infinite values. Returning zeros.")
                return np.zeros_like(hfc)

            return hfc

        except Exception as e:
            logger.warning(f"Error calculating high frequency content: {e}. Returning empty array.")
            # Return empty array with same number of frames as input
            if stft_matrix.ndim > 1:
                return np.zeros(stft_matrix.shape[1])
            else:
                return np.array([0.0])

    @staticmethod
    def complex_domain_onset(stft_matrix: np.ndarray) -> np.ndarray:
        """
        Calculate complex domain onset detection function with improved error handling.

        Args:
            stft_matrix: Short-time Fourier transform matrix

        Returns:
            Complex domain onset detection function
        """
        # Check if STFT matrix is valid
        if stft_matrix is None or stft_matrix.size == 0:
            logger.warning("Empty STFT matrix provided to complex_domain_onset. Returning empty array.")
            return np.array([])

        # Check for NaN or infinite values
        if not np.all(np.isfinite(stft_matrix)):
            logger.warning("STFT matrix contains NaN or infinite values. Cleaning matrix...")
            stft_matrix = np.nan_to_num(stft_matrix, nan=0.0, posinf=0.0, neginf=0.0)

        try:
            # Validate dimensions
            if stft_matrix.ndim < 2 or stft_matrix.shape[1] < 2:
                logger.warning("STFT matrix must have at least 2 frames for complex domain onset detection.")
                return np.zeros(1 if stft_matrix.ndim < 2 else max(1, stft_matrix.shape[1] - 1))

            # Calculate phase and magnitude
            phase = np.angle(stft_matrix)
            mag = np.abs(stft_matrix)

            # Calculate phase deviation
            phase_dev = np.diff(phase, axis=1)

            # Wrap to [-pi, pi]
            phase_dev = np.mod(phase_dev + np.pi, 2 * np.pi) - np.pi

            # Calculate predicted magnitude
            pred_mag = mag[:, :-1]

            # Calculate complex domain deviation with error checking
            complex_term = pred_mag * np.exp(1j * phase_dev)

            # Check for NaN or infinite values
            if not np.all(np.isfinite(complex_term)):
                logger.warning("Complex term contains NaN or infinite values. Using fallback method.")
                # Simpler fallback calculation
                complex_dev = np.sum(np.abs(np.diff(mag, axis=1)), axis=0)
            else:
                complex_dev = np.sum(np.abs(mag[:, 1:] - complex_term), axis=0)

            # Final check for NaN or infinite values
            if not np.all(np.isfinite(complex_dev)):
                logger.warning("Complex domain onset contains NaN or infinite values. Returning zeros.")
                return np.zeros_like(complex_dev)

            return complex_dev

        except Exception as e:
            logger.warning(f"Error calculating complex domain onset: {e}. Returning empty array.")
            # Return empty array with same number of frames as input (minus 1 for diff)
            if stft_matrix.ndim > 1 and stft_matrix.shape[1] > 1:
                return np.zeros(stft_matrix.shape[1] - 1)
            else:
                return np.array([0.0])

    def percussive_harmonic_separation(self, signal: np.ndarray, sr: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Separate percussive and harmonic components of a signal with improved error handling.

        Args:
            signal: Input signal
            sr: Sample rate

        Returns:
            Tuple of (percussive, harmonic) components
        """
        if not LIBROSA_AVAILABLE:
            return signal, np.zeros_like(signal)

        # Check if signal contains NaN or infinite values
        if not np.all(np.isfinite(signal)):
            logger.warning("Signal contains NaN or infinite values before HPSS. Cleaning signal...")
            signal = np.nan_to_num(signal, nan=0.0, posinf=0.0, neginf=0.0)

        # Ensure signal is not empty
        if len(signal) == 0:
            logger.warning("Empty signal provided to percussive_harmonic_separation. Returning zeros.")
            return np.zeros(1), np.zeros(1)

        try:
            # Use librosa's HPSS with error handling
            harmonic, percussive = librosa.effects.hpss(signal, margin=3.0)

            # Check for NaN or infinite values in results
            if not np.all(np.isfinite(harmonic)) or not np.all(np.isfinite(percussive)):
                logger.warning("HPSS produced NaN or infinite values. Using fallback method.")

                # Fallback: simple lowpass/highpass filtering if scipy is available
                if SCIPY_AVAILABLE:
                    # Lowpass filter for harmonic content (below 200 Hz is mostly percussive)
                    nyquist = sr / 2
                    cutoff = 200 / nyquist
                    b, a = scipy.signal.butter(4, cutoff, btype='highpass')
                    harmonic = scipy.signal.filtfilt(b, a, signal)

                    # Highpass filter for percussive content
                    cutoff = 2000 / nyquist
                    b, a = scipy.signal.butter(4, cutoff, btype='lowpass')
                    percussive = scipy.signal.filtfilt(b, a, signal)

                    # Ensure results are finite
                    harmonic = np.nan_to_num(harmonic, nan=0.0, posinf=0.0, neginf=0.0)
                    percussive = np.nan_to_num(percussive, nan=0.0, posinf=0.0, neginf=0.0)
                else:
                    # If scipy is not available, just return the original signal as percussive
                    percussive = signal
                    harmonic = np.zeros_like(signal)

            return percussive, harmonic

        except Exception as e:
            logger.warning(f"Error in percussive_harmonic_separation: {e}. Using fallback.")
            # Return original signal as percussive component
            return signal, np.zeros_like(signal)

    def multi_band_onset_detection(self, signal: np.ndarray, sr: int) -> Dict[str, np.ndarray]:
        """
        Perform onset detection in multiple frequency bands.

        Args:
            signal: Input signal
            sr: Sample rate

        Returns:
            Dictionary of onset detection functions for each band
        """
        if not SCIPY_AVAILABLE:
            return {'full_band': np.zeros(len(signal) // 1024)}

        # Check if signal contains NaN or infinite values
        if not np.all(np.isfinite(signal)):
            logger.warning("Input signal contains NaN or infinite values. Cleaning signal...")
            # Replace NaN or infinite values with zeros
            signal = np.nan_to_num(signal, nan=0.0, posinf=0.0, neginf=0.0)

        # Define frequency bands
        bands = {
            'low': (20, 200),  # Kick drum range
            'mid_low': (200, 800),  # Low tom range
            'mid': (800, 2500),  # Snare range
            'high': (2500, 8000),  # Hi-hat range
            'very_high': (8000, sr / 2)  # Cymbal range
        }

        # Initialize result dictionary
        onset_functions = {}

        # Process each band
        for band_name, (low_freq, high_freq) in bands.items():
            try:
                # Apply bandpass filter
                filtered = self._bandpass_filter(signal, low_freq, high_freq, sr)

                # Check if filtered signal contains NaN or infinite values
                if not np.all(np.isfinite(filtered)):
                    logger.warning(
                        f"Filtered signal for band {band_name} contains NaN or infinite values. Skipping band.")
                    continue

                # Compute STFT
                n_fft = 2048
                hop_length = 512

                if LIBROSA_AVAILABLE:
                    # Apply a window function to reduce edge effects
                    windowed = filtered * np.hanning(len(filtered))

                    # Ensure signal is finite before STFT
                    if not np.all(np.isfinite(windowed)):
                        logger.warning(
                            f"Windowed signal for band {band_name} contains NaN or infinite values. Skipping band.")
                        continue

                    stft = librosa.stft(windowed, n_fft=n_fft, hop_length=hop_length)

                    # Calculate spectral flux
                    flux = self.spectral_flux(stft)

                    # Normalize
                    max_flux = np.max(flux)
                    if max_flux > 0 and np.isfinite(max_flux):
                        flux = flux / max_flux
                    else:
                        # If max is zero or not finite, use ones
                        flux = np.ones_like(flux) * 0.01

                    onset_functions[band_name] = flux
                else:
                    # Fallback if librosa not available
                    onset_functions[band_name] = np.zeros(len(signal) // hop_length)
            except Exception as e:
                logger.warning(f"Error processing band {band_name}: {e}")
                # Provide a fallback for this band
                onset_functions[band_name] = np.zeros(len(signal) // hop_length)

        # If no bands were processed successfully, return a default
        if not onset_functions:
            logger.warning("No bands were processed successfully. Returning default.")
            return {'full_band': np.zeros(len(signal) // 1024)}

        return onset_functions

    def _bandpass_filter(self, signal: np.ndarray, low_freq: float, high_freq: float, sr: int) -> np.ndarray:
        """
        Apply bandpass filter to signal with improved error handling.

        Args:
            signal: Input signal
            low_freq: Low cutoff frequency
            high_freq: High cutoff frequency
            sr: Sample rate

        Returns:
            Filtered signal
        """
        if not SCIPY_AVAILABLE:
            return signal

        # Check if signal contains NaN or infinite values
        if not np.all(np.isfinite(signal)):
            logger.warning("Signal contains NaN or infinite values before filtering. Cleaning signal...")
            signal = np.nan_to_num(signal, nan=0.0, posinf=0.0, neginf=0.0)

        # Ensure signal is not empty
        if len(signal) == 0:
            logger.warning("Empty signal provided to bandpass filter. Returning zeros.")
            return np.zeros(1)

        # Validate frequency ranges
        nyquist = sr / 2
        if low_freq >= nyquist or high_freq <= 0 or low_freq >= high_freq:
            logger.warning(
                f"Invalid frequency range: {low_freq}-{high_freq} Hz with Nyquist frequency {nyquist} Hz. Using default filter.")
            # Return original signal if frequency range is invalid
            return signal

        # Normalize frequencies
        low = max(0.001, min(0.999, low_freq / nyquist))  # Clamp to valid range
        high = max(low + 0.001, min(0.999, high_freq / nyquist))  # Ensure high > low and within range

        try:
            # First, ensure the input signal doesn't contain any NaN or infinite values
            clean_signal = np.nan_to_num(signal, nan=0.0, posinf=0.0, neginf=0.0)

            # Use more stable SOS-based filtering as the primary method
            try:
                # SOS (second-order sections) is more numerically stable than b,a coefficients
                sos = scipy.signal.butter(4, [low, high], btype='band', output='sos', fs=sr)
                filtered = scipy.signal.sosfilt(sos, clean_signal)

                # Check for NaN or infinite values in filtered signal
                if not np.all(np.isfinite(filtered)):
                    logger.warning("SOS filtering produced NaN values. Using robust fallback method.")

                    # Try a more conservative filter order
                    sos_conservative = scipy.signal.butter(2, [low, high], btype='band', output='sos', fs=sr)
                    filtered = scipy.signal.sosfilt(sos_conservative, clean_signal)
            except Exception as e:
                logger.warning(f"SOS filtering failed: {str(e)}. Trying traditional filter.")
                # Fall back to traditional filtering
                try:
                    b, a = scipy.signal.butter(2, [low, high], btype='band')
                    filtered = scipy.signal.filtfilt(b, a, clean_signal)
                except Exception as e2:
                    logger.warning(f"Traditional filtering failed: {str(e2)}. Trying simple filter.")
                    # Try an even simpler filter
                    try:
                        b, a = scipy.signal.butter(1, [low / nyquist, high / nyquist], btype='band')
                        filtered = scipy.signal.lfilter(b, a, clean_signal)
                    except Exception as e3:
                        logger.warning(f"Simple filtering failed: {str(e3)}. Using median filter.")
                        # Last resort: use a simple median filter
                        try:
                            window_size = int(sr / 100)  # 10ms window
                            if window_size % 2 == 0:
                                window_size += 1  # Ensure odd window size
                            filtered = scipy.signal.medfilt(clean_signal, window_size)
                        except Exception as e4:
                            logger.warning(f"All filtering methods failed: {str(e4)}. Returning original signal.")
                            filtered = clean_signal

            # Final safety check - replace any remaining NaN/inf values
            if not np.all(np.isfinite(filtered)):
                logger.warning("Filtering produced NaN values despite fallbacks. Using clean original signal.")
                return clean_signal

            return filtered

        except Exception as e:
            logger.warning(f"Error in bandpass filter: {e}. Returning original signal.")
            return signal

    def calculate_energy_envelope(self, signal: np.ndarray, sr: int, window_size: int = 1024,
                                  hop_length: int = 256) -> np.ndarray:
        """
        Calculate the energy envelope of a signal with multi-resolution analysis.

        Args:
            signal: Input signal
            sr: Sample rate
            window_size: Size of the analysis window
            hop_length: Number of samples between windows

        Returns:
            Energy envelope of the signal
        """
        # Check if we have a cached result
        signal_hash = hash(signal.tobytes())
        cache_key = f"{signal_hash}_{window_size}_{hop_length}"

        if cache_key in self.energy_envelope_cache:
            return self.energy_envelope_cache[cache_key]

        if len(signal) == 0:
            return np.array([])

        # Calculate energy in overlapping windows
        num_frames = 1 + (len(signal) - window_size) // hop_length
        energy = np.zeros(num_frames)

        for i in range(num_frames):
            start = i * hop_length
            end = start + window_size
            if end <= len(signal):
                # Apply window function to reduce edge effects
                windowed_frame = signal[start:end] * np.hanning(window_size)
                # Calculate energy
                energy[i] = np.sum(windowed_frame ** 2) if len(windowed_frame) > 0 else 0.0

        # Apply multi-resolution analysis for better transient detection
        if SCIPY_AVAILABLE and len(energy) > 3:
            # Calculate first derivative (rate of change of energy)
            energy_diff1 = np.diff(energy)
            energy_diff1 = np.concatenate(([0], energy_diff1))  # Pad to match original length

            # Calculate second derivative (acceleration of energy change)
            energy_diff2 = np.diff(energy_diff1)
            energy_diff2 = np.concatenate(([0], energy_diff2, [0]))  # Pad to match original length

            # Combine original energy with derivatives for enhanced detection
            # Emphasize positive first derivative (energy increase) and
            # negative second derivative (energy peaks)
            enhanced_energy = energy + 0.5 * np.maximum(0, energy_diff1) - 0.3 * np.minimum(0, energy_diff2)

            # Normalize
            if np.max(enhanced_energy) > 0:
                enhanced_energy = enhanced_energy / np.max(enhanced_energy)

            # Apply adaptive thresholding to enhance peaks
            if hasattr(scipy.ndimage, 'gaussian_filter1d'):
                # Calculate moving average
                smoothed = scipy.ndimage.gaussian_filter1d(enhanced_energy, sigma=2)
                # Enhance peaks by subtracting the smoothed signal
                enhanced_energy = np.maximum(0, enhanced_energy - 0.5 * smoothed)
                # Normalize again
                if np.max(enhanced_energy) > 0:
                    enhanced_energy = enhanced_energy / np.max(enhanced_energy)
        else:
            # If scipy not available, just normalize the energy
            if np.max(energy) > 0:
                enhanced_energy = energy / np.max(energy)
            else:
                enhanced_energy = energy

        # Cache the result
        if len(self.energy_envelope_cache) >= self.max_cache_size:
            # Remove oldest entry if cache is full
            oldest_key = next(iter(self.energy_envelope_cache))
            del self.energy_envelope_cache[oldest_key]

        self.energy_envelope_cache[cache_key] = enhanced_energy

        return enhanced_energy

    def detect_transients_from_envelope(self, envelope: np.ndarray, sr: int, hop_length: int = 256,
                                        threshold: float = 0.2, min_distance_samples: int = 1024) -> List[float]:
        """
        Detect transients from an energy envelope.

        Args:
            envelope: Energy envelope
            sr: Sample rate
            hop_length: Number of samples between windows (used in envelope calculation)
            threshold: Detection threshold
            min_distance_samples: Minimum distance between transients in samples

        Returns:
            List of transient times in seconds
        """
        if not SCIPY_AVAILABLE or len(envelope) == 0:
            return []

        # Convert min_distance from samples to envelope frames
        min_distance_frames = max(1, min_distance_samples // hop_length)

        # Find peaks in the envelope
        peaks, _ = scipy.signal.find_peaks(envelope, height=threshold, distance=min_distance_frames)

        # Convert peak positions to time in seconds
        peak_times = [(peak * hop_length) / sr for peak in peaks]

        return peak_times

    def enhanced_onset_strength(self, signal: np.ndarray, sr: int) -> np.ndarray:
        """
        Calculate enhanced onset strength signal with improved transient detection.

        Args:
            signal: Input signal
            sr: Sample rate

        Returns:
            Onset strength signal
        """
        hop_length = 512
        n_fft = 2048

        # First, calculate the energy envelope for better transient detection
        energy_envelope = self.calculate_energy_envelope(signal, sr)

        if LIBROSA_AVAILABLE:
            # Use librosa's onset strength function if available
            onset_env = librosa.onset.onset_strength(
                y=signal,
                sr=sr,
                hop_length=hop_length,
                n_fft=n_fft,
                lag=1,
                max_size=3
            )

            # Combine with energy envelope for better detection
            if len(energy_envelope) > 0 and len(onset_env) > 0:
                # Resample energy envelope to match onset_env length
                if len(energy_envelope) != len(onset_env):
                    if SCIPY_AVAILABLE:
                        energy_envelope_resampled = scipy.signal.resample(energy_envelope, len(onset_env))
                    else:
                        # Simple resampling
                        indices = np.linspace(0, len(energy_envelope) - 1, len(onset_env))
                        indices = indices.astype(int)
                        energy_envelope_resampled = energy_envelope[indices]
                else:
                    energy_envelope_resampled = energy_envelope

                # Combine the two onset detectors
                combined_onset = onset_env + 0.5 * energy_envelope_resampled

                # Normalize
                if np.max(combined_onset) > 0:
                    combined_onset = combined_onset / np.max(combined_onset)

                return combined_onset
            else:
                return onset_env

        # Fallback implementation using scipy if available
        if SCIPY_AVAILABLE:
            logger.info("Using scipy fallback for onset strength calculation")

            # Calculate STFT
            signal_hash = hash(signal.tobytes())
            stft = self._get_cached_stft(signal_hash, hop_length, n_fft)

            if stft is None:
                # Compute STFT using scipy
                frames = range(0, len(signal) - n_fft + 1, hop_length)
                stft = np.array([np.fft.rfft(signal[i:i + n_fft] * np.hanning(n_fft)) for i in frames])
                stft = stft.T  # Transpose to match librosa's format

                # Cache the computed STFT
                self._get_cached_stft(signal_hash, hop_length, n_fft, stft)

            # Calculate spectral flux (difference between consecutive frames)
            mag_spec = np.abs(stft)

            # Calculate difference between consecutive frames
            diff = np.diff(mag_spec, axis=1)

            # Keep only positive differences (increases in energy)
            diff = np.maximum(0, diff)

            # Sum across frequency bins and apply smoothing
            flux = np.sum(diff, axis=0)

            # Apply smoothing if available
            if hasattr(scipy.ndimage, 'gaussian_filter1d'):
                flux = scipy.ndimage.gaussian_filter1d(flux, sigma=2)

            # Combine with energy envelope if available
            if len(energy_envelope) > 0 and len(flux) > 0:
                # Resample energy envelope to match flux length
                if len(energy_envelope) != len(flux):
                    energy_envelope_resampled = scipy.signal.resample(energy_envelope, len(flux))
                else:
                    energy_envelope_resampled = energy_envelope

                # Combine the two onset detectors
                combined_flux = flux + 0.5 * energy_envelope_resampled

                # Normalize
                if np.max(combined_flux) > 0:
                    combined_flux = combined_flux / np.max(combined_flux)

                return combined_flux
            else:
                return flux

        # If neither librosa nor scipy is available, return energy envelope or zeros
        if len(energy_envelope) > 0:
            return energy_envelope
        else:
            logger.warning("Neither librosa nor scipy available for onset strength calculation")
            return np.zeros(len(signal) // hop_length)


class NoiseFilter:
    """
    Advanced noise filtering for audio signals.
    """

    def __init__(self, sr: int):
        """
        Initialize noise filter.

        Args:
            sr: Sample rate
        """
        self.sr = sr
        self.noise_profile = None
        self.noise_threshold = 0.01  # Default threshold

    def estimate_noise_profile(self, signal: np.ndarray, frame_length: int = 2048, hop_length: int = 512) -> np.ndarray:
        """
        Estimate noise profile from signal.

        Args:
            signal: Input signal
            frame_length: Length of each frame
            hop_length: Number of samples between frames

        Returns:
            Noise profile
        """
        if not LIBROSA_AVAILABLE or not SCIPY_AVAILABLE:
            return np.zeros(frame_length // 2 + 1)

        # Calculate spectrogram
        stft = librosa.stft(signal, n_fft=frame_length, hop_length=hop_length)
        mag_spec = np.abs(stft)

        # Estimate noise profile as the minimum magnitude in each frequency bin
        noise_profile = np.min(mag_spec, axis=1)

        # Apply smoothing
        noise_profile = scipy.ndimage.gaussian_filter1d(noise_profile, sigma=2)

        self.noise_profile = noise_profile
        return noise_profile

    def apply_noise_reduction(self, signal: np.ndarray, frame_length: int = 2048, hop_length: int = 512) -> np.ndarray:
        """
        Apply noise reduction to signal.

        Args:
            signal: Input signal
            frame_length: Length of each frame
            hop_length: Number of samples between frames

        Returns:
            Noise-reduced signal
        """
        if not LIBROSA_AVAILABLE or not SCIPY_AVAILABLE:
            return signal

        # Calculate spectrogram
        stft = librosa.stft(signal, n_fft=frame_length, hop_length=hop_length)
        mag_spec = np.abs(stft)
        phase_spec = np.angle(stft)

        # Estimate noise profile if not already done
        if self.noise_profile is None:
            self.estimate_noise_profile(signal, frame_length, hop_length)

        # Apply spectral subtraction
        gain = np.maximum(0, 1 - self.noise_profile[:, np.newaxis] / (mag_spec + 1e-10))
        mag_spec_clean = mag_spec * gain

        # Reconstruct signal
        stft_clean = mag_spec_clean * np.exp(1j * phase_spec)
        signal_clean = librosa.istft(stft_clean, hop_length=hop_length, length=len(signal))

        return signal_clean

    def adaptive_noise_gate(self, signal: np.ndarray, threshold_factor: float = 2.0) -> np.ndarray:
        """
        Apply adaptive noise gate to signal.

        Args:
            signal: Input signal
            threshold_factor: Factor to multiply noise level by for threshold

        Returns:
            Noise-gated signal
        """
        if not SCIPY_AVAILABLE:
            return signal

        # Estimate noise level
        noise_level = np.percentile(np.abs(signal), 10)
        threshold = noise_level * threshold_factor

        # Apply gate
        gated = np.where(np.abs(signal) > threshold, signal, 0)

        return gated

    def multi_stage_denoising(self, signal: np.ndarray) -> np.ndarray:
        """
        Apply multi-stage denoising to signal.

        Args:
            signal: Input signal

        Returns:
            Denoised signal
        """
        # Stage 1: Adaptive noise gate
        gated = self.adaptive_noise_gate(signal)

        # Stage 2: Spectral subtraction
        denoised = self.apply_noise_reduction(gated)

        return denoised


class DrumClassifier:
    """
    Advanced classifier for drum sounds based on spectral characteristics and machine learning techniques.
    """

    def __init__(self, model: DrumClassificationModel):
        """
        Initialize drum classifier.

        Args:
            model: Drum classification model
        """
        self.model = model
        self.previous_classifications = []  # Store recent classifications for context
        self.max_history = 10  # Maximum number of previous classifications to store

    def classify_drum_hit(self, signal: np.ndarray, sr: int, time: float) -> Tuple[str, float]:
        """
        Classify a drum hit with enhanced spectral analysis.

        Args:
            signal: Full audio signal
            sr: Sample rate
            time: Time of the drum hit in seconds

        Returns:
            Tuple of (drum_type, confidence)
        """
        if not LIBROSA_AVAILABLE or not SCIPY_AVAILABLE:
            return 'generic', 0.5

        # Extract a short segment around the hit with adaptive window size
        center_sample = int(time * sr)

        # Use larger window for low-frequency analysis (kicks)
        window_size = int(0.15 * sr)  # 150ms window (increased from 100ms)

        start = max(0, center_sample - window_size // 2)
        end = min(len(signal), center_sample + window_size // 2)
        segment = signal[start:end]

        if len(segment) == 0:
            return 'generic', 0.5

        # Calculate comprehensive spectral features
        spectral_centroid = librosa.feature.spectral_centroid(y=segment, sr=sr)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=segment, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=segment, sr=sr)[0]

        # Additional features for better classification
        spectral_contrast = librosa.feature.spectral_contrast(y=segment, sr=sr)[0] if hasattr(librosa.feature,
                                                                                              'spectral_contrast') else np.zeros(
            1)
        spectral_flatness = librosa.feature.spectral_flatness(y=segment)[0] if hasattr(librosa.feature,
                                                                                       'spectral_flatness') else np.zeros(
            1)

        # Calculate zero crossing rate (useful for distinguishing hi-hats)
        zero_crossing_rate = librosa.feature.zero_crossing_rate(segment)[0]

        # Calculate energy envelope for attack analysis
        if len(segment) > sr // 50:  # Ensure segment is long enough
            attack_segment = segment[:sr // 50]  # First 20ms
            attack_energy = np.cumsum(attack_segment ** 2)
            if len(attack_energy) > 0 and attack_energy[-1] > 0:
                attack_energy = attack_energy / attack_energy[-1]  # Normalize
                attack_time = np.argmax(attack_energy > 0.5) / (sr / 50) if np.any(attack_energy > 0.5) else 0.5
            else:
                attack_time = 0.5
        else:
            attack_time = 0.5

        # Calculate decay characteristics
        if len(segment) > sr // 10:  # Ensure segment is long enough
            segment_rms = librosa.feature.rms(y=segment, frame_length=sr // 100, hop_length=sr // 200)[0]
            if len(segment_rms) > 2:
                peak_pos = np.argmax(segment_rms)
                if peak_pos < len(segment_rms) - 1:
                    decay_segment = segment_rms[peak_pos:]
                    if len(decay_segment) > 1 and decay_segment[0] > 0:
                        decay_ratio = decay_segment[-1] / decay_segment[0]
                    else:
                        decay_ratio = 1.0
                else:
                    decay_ratio = 1.0
            else:
                decay_ratio = 1.0
        else:
            decay_ratio = 1.0

        # Calculate energy in different frequency bands with improved resolution
        band_energies = {}
        detailed_band_energies = {}

        # Define more detailed frequency bands for better discrimination
        detailed_bands = {
            'sub_bass': (20, 60),
            'bass': (60, 120),
            'low_mid': (120, 250),
            'mid': (250, 500),
            'high_mid': (500, 2000),
            'high': (2000, 7000),
            'very_high': (7000, 20000)
        }

        # Calculate energy in standard drum type bands
        for drum_type, (low_freq, high_freq) in self.model.frequency_ranges.items():
            # Apply bandpass filter
            try:
                nyquist = sr / 2
                low = low_freq / nyquist
                high = high_freq / nyquist

                # Design filter with higher order for sharper cutoff
                b, a = scipy.signal.butter(6, [low, high], btype='band')

                # Apply filter
                filtered = scipy.signal.filtfilt(b, a, segment)

                # Calculate energy with robust overflow protection
                try:
                    # Convert to float64 for higher precision
                    filtered_64 = filtered.astype(np.float64)

                    # Use a safer approach to calculate energy
                    # Normalize the signal first to prevent overflow
                    if len(filtered_64) > 0:
                        max_abs = np.max(np.abs(filtered_64))
                        if max_abs > 0:
                            # Normalize to [-1, 1] range
                            normalized = filtered_64 / max_abs
                            # Calculate energy on normalized signal and scale back
                            # Calculate energy using logarithmic approach to prevent overflow
                            normalized_energy = np.sum(normalized * normalized)
                            # Use logarithmic calculation to prevent overflow when scaling back
                            if max_abs > 1.0:
                                # Limit log_scale to prevent overflow in exp
                                log_scale = min(2.0 * np.log(max_abs), 700.0)  # np.exp(709) is max for float64
                                try:
                                    energy = normalized_energy * np.exp(log_scale)
                                    # Safety check for overflow
                                    if not np.isfinite(energy):
                                        # Fallback to a simpler calculation with clamping
                                        energy = normalized_energy * min(max_abs * max_abs, 1e6)
                                except OverflowError:
                                    # Fallback if overflow occurs
                                    energy = normalized_energy * min(max_abs * max_abs, 1e6)
                            else:
                                # For small values, direct calculation is safe
                                energy = normalized_energy * (max_abs * max_abs)
                        else:
                            energy = 0.0
                    else:
                        energy = 0.0

                    band_energies[drum_type] = float(energy)  # Convert back to standard float
                except Exception as e:
                    logger.warning(f"Error calculating band energy for {drum_type}: {e}")
                    band_energies[drum_type] = 0.0  # Safe fallback
            except Exception as e:
                logger.warning(f"Error calculating band energy for {drum_type}: {e}")
                band_energies[drum_type] = 0

        # Calculate energy in detailed bands
        for band_name, (low_freq, high_freq) in detailed_bands.items():
            try:
                nyquist = sr / 2
                low = low_freq / nyquist
                high = high_freq / nyquist

                # Design filter
                b, a = scipy.signal.butter(6, [low, high], btype='band')

                # Apply filter
                filtered = scipy.signal.filtfilt(b, a, segment)

                # Calculate energy with robust overflow protection
                try:
                    # Convert to float64 for higher precision
                    filtered_64 = filtered.astype(np.float64)

                    # Use a safer approach to calculate energy
                    # Normalize the signal first to prevent overflow
                    if len(filtered_64) > 0:
                        max_abs = np.max(np.abs(filtered_64))
                        if max_abs > 0:
                            # Normalize to [-1, 1] range
                            normalized = filtered_64 / max_abs
                            # Calculate energy using logarithmic approach to prevent overflow
                            try:
                                # Use a more numerically stable approach to prevent overflow
                                # First calculate energy on normalized signal (values between -1 and 1)
                                normalized_energy = np.sum(normalized * normalized)

                                # Then apply scaling using logarithmic domain to prevent overflow
                                if max_abs > 0 and normalized_energy > 0:
                                    try:
                                        # Use log-domain calculation to prevent overflow
                                        # Limit log_energy to prevent overflow in 10.0**log_energy
                                        log_energy = min(np.log10(normalized_energy) + 2 * np.log10(max_abs), 307.0)  # 10.0**308 is max for float64
                                        energy = 10.0 ** log_energy

                                        # Safety check for overflow
                                        if not np.isfinite(energy):
                                            # Fallback to a simpler calculation with clamping
                                            energy = normalized_energy * min(max_abs * max_abs, 1e6)
                                    except (OverflowError, FloatingPointError):
                                        # Fallback if any calculation fails
                                        # Use a more conservative approach with explicit clamping
                                        max_abs_squared = min(max_abs * max_abs, 1e6)
                                        energy = min(normalized_energy * max_abs_squared, 1e12)  # Explicit upper bound
                                else:
                                    energy = 0.0
                            except Exception:
                                # Ultimate fallback if any calculation fails
                                energy = normalized_energy
                        else:
                            energy = 0.0
                    else:
                        energy = 0.0

                    detailed_band_energies[band_name] = float(energy)  # Convert back to standard float
                except Exception as e:
                    logger.warning(f"Error calculating detailed band energy for {band_name}: {e}")
                    detailed_band_energies[band_name] = 0.0  # Safe fallback
            except Exception as e:
                logger.warning(f"Error calculating detailed band energy for {band_name}: {e}")
                detailed_band_energies[band_name] = 0

        # Normalize band energies
        total_energy = sum(band_energies.values()) + 1e-10
        for drum_type in band_energies:
            band_energies[drum_type] /= total_energy

        # Normalize detailed band energies
        total_detailed_energy = sum(detailed_band_energies.values()) + 1e-10
        for band in detailed_band_energies:
            detailed_band_energies[band] /= total_detailed_energy

        # Calculate spectral flux for transient analysis
        if len(segment) > 1024:
            half_point = len(segment) // 2
            pre_spec = np.abs(np.fft.rfft(segment[:half_point] * np.hanning(half_point)))
            post_spec = np.abs(np.fft.rfft(segment[half_point:half_point + half_point] * np.hanning(half_point)))

            # Normalize spectra
            if np.sum(pre_spec) > 0:
                pre_spec = pre_spec / np.sum(pre_spec)
            if np.sum(post_spec) > 0:
                post_spec = post_spec / np.sum(post_spec)

            spectral_flux = np.sum(np.maximum(0, post_spec - pre_spec))
        else:
            spectral_flux = 0

        # Advanced classification logic using multiple features

        # Kick drum detection
        kick_score = (
                (3.0 * band_energies.get('kick', 0)) +
                (2.0 * detailed_band_energies.get('sub_bass', 0)) +
                (1.5 * detailed_band_energies.get('bass', 0)) -
                (1.0 * detailed_band_energies.get('high', 0)) -
                (1.0 * detailed_band_energies.get('very_high', 0)) +
                (0.5 if np.mean(spectral_centroid) < 300 else 0) +
                (0.5 if attack_time < 0.2 else 0) +
                (0.5 if decay_ratio < 0.3 else 0) +
                (0.5 if np.mean(zero_crossing_rate) < 0.1 else 0)
        )

        # Snare drum detection
        snare_score = (
                (2.0 * band_energies.get('snare', 0)) +
                (1.0 * detailed_band_energies.get('low_mid', 0)) +
                (1.5 * detailed_band_energies.get('mid', 0)) +
                (1.0 * detailed_band_energies.get('high_mid', 0)) +
                (0.5 * detailed_band_energies.get('high', 0)) -
                (1.0 * detailed_band_energies.get('sub_bass', 0)) +
                (0.5 if 300 <= np.mean(spectral_centroid) < 2000 else 0) +
                (0.5 if attack_time < 0.15 else 0) +
                (0.5 if 0.2 < decay_ratio < 0.6 else 0) +
                (0.5 if 0.1 <= np.mean(zero_crossing_rate) < 0.3 else 0) +
                (0.5 if np.mean(spectral_flatness) > 0.2 else 0)
        )

        # Hi-hat detection
        hihat_score = (
                (2.0 * band_energies.get('hi-hat', 0)) +
                (0.5 * detailed_band_energies.get('high_mid', 0)) +
                (2.0 * detailed_band_energies.get('high', 0)) +
                (2.0 * detailed_band_energies.get('very_high', 0)) -
                (2.0 * detailed_band_energies.get('sub_bass', 0)) -
                (1.0 * detailed_band_energies.get('bass', 0)) +
                (1.0 if np.mean(spectral_centroid) >= 3000 else 0) +
                (1.0 if np.mean(zero_crossing_rate) > 0.3 else 0) +
                (0.5 if attack_time < 0.1 else 0) +
                (0.5 if decay_ratio > 0.5 else 0) +
                (1.0 if np.mean(spectral_flatness) > 0.3 else 0)
        )

        # Tom drum detection
        tom_score = (
                (2.0 * band_energies.get('tom', 0)) +
                (1.0 * detailed_band_energies.get('low_mid', 0)) +
                (1.5 * detailed_band_energies.get('mid', 0)) -
                (1.0 * detailed_band_energies.get('very_high', 0)) +
                (0.5 if 200 <= np.mean(spectral_centroid) < 800 else 0) +
                (0.5 if attack_time < 0.2 else 0) +
                (0.5 if decay_ratio < 0.4 else 0) +
                (0.5 if np.mean(zero_crossing_rate) < 0.2 else 0)
        )

        # Cymbal detection
        cymbal_score = (
                (2.0 * band_energies.get('cymbal', 0)) +
                (0.5 * detailed_band_energies.get('high_mid', 0)) +
                (1.5 * detailed_band_energies.get('high', 0)) +
                (2.0 * detailed_band_energies.get('very_high', 0)) -
                (2.0 * detailed_band_energies.get('sub_bass', 0)) -
                (1.0 * detailed_band_energies.get('bass', 0)) +
                (1.0 if np.mean(spectral_centroid) >= 4000 else 0) +
                (0.5 if decay_ratio > 0.7 else 0) +  # Cymbals have longer decay
                (0.5 if np.mean(spectral_flatness) > 0.25 else 0)
        )

        # Normalize scores to positive values
        min_score = min(kick_score, snare_score, hihat_score, tom_score, cymbal_score)
        if min_score < 0:
            kick_score -= min_score
            snare_score -= min_score
            hihat_score -= min_score
            tom_score -= min_score
            cymbal_score -= min_score

        # Find drum type with highest score
        scores = {
            'kick': kick_score,
            'snare': snare_score,
            'hi-hat': hihat_score,
            'tom': tom_score,
            'cymbal': cymbal_score
        }

        drum_type = max(scores, key=scores.get)

        # Calculate confidence based on how dominant the score is
        total_score = sum(scores.values()) + 1e-10
        confidence = scores[drum_type] / total_score

        # Apply context-based corrections using previous classifications
        if self.previous_classifications:
            # Check for common patterns
            if len(self.previous_classifications) >= 2:
                # Pattern: kick-snare alternation
                if (self.previous_classifications[-1][0] == 'kick' and
                        self.previous_classifications[-2][0] == 'snare' and
                        drum_type == 'kick'):
                    confidence = min(0.95, confidence * 1.1)

                # Pattern: hi-hat every other beat
                if (self.previous_classifications[-2][0] == 'hi-hat' and
                        drum_type == 'hi-hat'):
                    confidence = min(0.95, confidence * 1.1)

                # Pattern: kick on downbeats
                recent_types = [c[0] for c in self.previous_classifications[-4:]]
                if drum_type == 'kick' and recent_types.count('kick') >= 2:
                    # Check if kicks appear at regular intervals
                    confidence = min(0.95, confidence * 1.05)

        # Store this classification for future context
        self.previous_classifications.append((drum_type, confidence, time))

        # Keep only the most recent classifications
        if len(self.previous_classifications) > self.max_history:
            self.previous_classifications.pop(0)

        return drum_type, confidence

    def classify_multiple_hits(self, signal: np.ndarray, sr: int, times: List[float]) -> List[Tuple[str, float]]:
        """
        Classify multiple drum hits.

        Args:
            signal: Full audio signal
            sr: Sample rate
            times: List of hit times in seconds

        Returns:
            List of (drum_type, confidence) tuples
        """
        results = []

        for time in times:
            drum_type, confidence = self.classify_drum_hit(signal, sr, time)
            results.append((drum_type, confidence))

        return results

    def classify_with_context(self, signal: np.ndarray, sr: int, times: List[float]) -> List[Tuple[str, float]]:
        """
        Classify drum hits with contextual awareness.

        Args:
            signal: Full audio signal
            sr: Sample rate
            times: List of hit times in seconds

        Returns:
            List of (drum_type, confidence) tuples
        """
        # First pass: classify each hit individually
        initial_classifications = self.classify_multiple_hits(signal, sr, times)

        # Second pass: apply contextual rules
        final_classifications = []

        for i, (time, (drum_type, confidence)) in enumerate(zip(times, initial_classifications)):
            # Apply pattern-based rules
            if i > 0 and i < len(times) - 1:
                prev_type = initial_classifications[i - 1][0]

                # Common pattern: kick followed by snare
                if prev_type == 'kick' and drum_type == 'generic':
                    drum_type = 'snare'
                    confidence = 0.7

                # Common pattern: alternating hi-hat
                if i % 2 == 0 and prev_type == 'hi-hat' and drum_type == 'generic':
                    drum_type = 'hi-hat'
                    confidence = 0.7

            final_classifications.append((drum_type, confidence))

        return final_classifications


class AmplitudeSegmentAnalyzer:
    """
    Analyzer for segmenting audio based on amplitude characteristics.
    """

    def __init__(self):
        """Initialize amplitude segment analyzer."""
        self.segments = {}

    def analyze_amplitude_segments(self, signal: np.ndarray, sr: int) -> Dict[str, List[Tuple[float, float]]]:
        """
        Analyze amplitude segments in signal with enhanced sensitivity to prominent peaks.

        Args:
            signal: Input signal
            sr: Sample rate

        Returns:
            Dictionary of segment types with time ranges
        """
        if not SCIPY_AVAILABLE:
            return {'medium': [(0, len(signal) / sr)]}

        # Calculate RMS energy with smaller frame for better peak detection
        frame_length = 1024  # Smaller frame for better temporal resolution
        hop_length = 256  # Smaller hop for more precise segment boundaries
        rms = librosa.feature.rms(y=signal, frame_length=frame_length, hop_length=hop_length)[0]

        # Calculate time for each frame
        times = librosa.times_like(rms, sr=sr, hop_length=hop_length)

        # Calculate enhanced thresholds with better sensitivity to peaks
        # Use more nuanced percentile values for better segmentation
        very_low_threshold = np.percentile(rms, 15)  # Increased from 10
        low_threshold = np.percentile(rms, 30)  # Increased from 25
        medium_threshold = np.percentile(rms, 50)  # Same
        high_threshold = np.percentile(rms, 70)  # Decreased from 75
        very_high_threshold = np.percentile(rms, 85)  # Decreased from 90

        # Calculate additional peak-focused threshold
        # This helps identify short but prominent peaks that might be missed
        peak_threshold = np.percentile(rms, 95)  # Very high threshold for peak detection

        # Segment signal
        segments = {
            'very_low': [],
            'low': [],
            'medium': [],
            'high': [],
            'very_high': []
        }

        # Add peak detection to identify short but prominent peaks
        peak_indices = []
        for i in range(1, len(rms) - 1):
            if (rms[i] > rms[i - 1] and rms[i] > rms[i + 1] and rms[i] > peak_threshold):
                peak_indices.append(i)

        # Convert peak indices to time ranges
        peak_segments = []
        for idx in peak_indices:
            # Create a small segment around the peak
            peak_time = times[idx]
            # Ensure the peak segment is at least 50ms wide (25ms on each side)
            segment_width = max(0.05, hop_length / sr * 2)
            start_time = max(0, peak_time - segment_width / 2)
            end_time = min(times[-1], peak_time + segment_width / 2)
            peak_segments.append((start_time, end_time))

        # Merge overlapping peak segments
        if peak_segments:
            peak_segments.sort()
            merged_peaks = [peak_segments[0]]
            for current in peak_segments[1:]:
                previous = merged_peaks[-1]
                if current[0] <= previous[1]:
                    # Merge overlapping segments
                    merged_peaks[-1] = (previous[0], max(previous[1], current[1]))
                else:
                    merged_peaks.append(current)
            peak_segments = merged_peaks

        # Standard segmentation
        current_segment = None
        current_start = 0

        for i, (time, energy) in enumerate(zip(times, rms)):
            if energy >= very_high_threshold:
                segment_type = 'very_high'
            elif energy >= high_threshold:
                segment_type = 'high'
            elif energy >= medium_threshold:
                segment_type = 'medium'
            elif energy >= low_threshold:
                segment_type = 'low'
            else:
                segment_type = 'very_low'

            if current_segment is None:
                current_segment = segment_type
                current_start = time
            elif segment_type != current_segment:
                segments[current_segment].append((current_start, time))
                current_segment = segment_type
                current_start = time

        # Add final segment
        if current_segment is not None:
            segments[current_segment].append((current_start, times[-1]))

        # Add peak segments as 'very_high' segments
        # This ensures short but prominent peaks are properly categorized
        segments['very_high'].extend(peak_segments)

        # Sort all segments by start time
        for segment_type in segments:
            segments[segment_type].sort()

        self.segments = segments
        return segments

    def get_segment_at_time(self, time: float) -> str:
        """
        Get segment type at a specific time.

        Args:
            time: Time in seconds

        Returns:
            Segment type
        """
        for segment_type, ranges in self.segments.items():
            for start, end in ranges:
                if start <= time < end:
                    return segment_type

        return 'medium'  # Default if not found


class WaveformAnalyzer(QObject):
    """
    Professional-grade waveform analyzer for drum detection using madmom

    This analyzer incorporates multiple advanced detection methods and provides
    comprehensive drum hit detection and classification capabilities.
    """

    # Class attributes for library availability
    LIBROSA_AVAILABLE = LIBROSA_AVAILABLE
    SCIPY_AVAILABLE = SCIPY_AVAILABLE
    SKLEARN_AVAILABLE = SKLEARN_AVAILABLE
    MATPLOTLIB_AVAILABLE = MATPLOTLIB_AVAILABLE
    MADMOM_AVAILABLE = MADMOM_AVAILABLE

    # Signals for UI integration
    peak_detection_complete = Signal(bool)
    analysis_progress = Signal(int)  # Progress percentage
    analysis_status = Signal(str)  # Detailed status message
    analysis_metrics = Signal(dict)  # Real-time metrics (ETA, speed, etc.)

    @profile_method("waveform_analyzer_init")
    def __init__(self):
        super().__init__()

        # Core properties
        self.file_path: Optional[Path] = None
        self.original_file_path: Optional[Path] = None  # Store the original file path if this is a stem
        self.filename: str = ""
        self.waveform_data: Optional[np.ndarray] = None
        self.sample_rate: int = 22050
        self.duration_seconds: float = 0.0
        self.channels: int = 1  # Number of audio channels
        self.is_analyzed: bool = False
        self.is_processing: bool = False
        self.is_drum_stem: bool = False  # Flag to indicate if this is a drum stem

        # Analysis results
        self.peaks: List[Peak] = []
        self.noise_floor: float = 0.0
        self.dynamic_range: float = 0.0

        # Processing components
        self.signal_processor = AdvancedSignalProcessor()
        self.noise_filter: Optional[NoiseFilter] = None
        self.drum_classifier: Optional[DrumClassifier] = None
        self.amplitude_analyzer = AmplitudeSegmentAnalyzer()

        # Visual validation (will be initialized after config is set)
        self.visual_validator: Optional[VisualValidator] = None

        # madmom processors
        if MADMOM_AVAILABLE:
            self.beat_processor = RNNBeatProcessor()
            self.beat_tracker = DBNBeatTrackingProcessor(fps=100)
            self.onset_processor = RNNOnsetProcessor()
            # Enhanced configuration for the OnsetPeakPickingProcessor
            # Optimized for drum detection with better transient handling
            self.onset_peak_picker = OnsetPeakPickingProcessor(
                threshold=0.25,  # Lower threshold for better sensitivity to subtle drum hits
                pre_max=0.04,  # Increased from 30ms to 40ms for better rising edge detection
                post_max=0.04,  # Increased from 30ms to 40ms to ensure we catch the true peak
                pre_avg=0.15,  # Increased from 100ms to 150ms for better baseline estimation
                post_avg=0.05,  # Reduced from 100ms to 50ms for faster response after peak
                combine=0.06,  # Increased from 50ms to 60ms to better combine closely spaced onsets
                delay=0.0  # No artificial delay
            )
            self.spectral_processor = SpectralOnsetProcessor()
            self.tempo_processor = TempoEstimationProcessor(fps=100)

        # Enhanced progress tracking
        self.progress_tracker = {
            'start_time': None,
            'stage_times': {},
            'current_stage': None,
            'total_stages': 7,
            'stage_weights': {  # Relative time weights for each stage
                'noise_analysis': 0.05,
                'preprocessing': 0.15,
                'onset_detection': 0.35,
                'peak_refinement': 0.25,
                'classification': 0.10,
                'amplitude_filtering': 0.05,
                'final_validation': 0.05
            },
            'peak_count': 0,
            'processing_speed': 0.0  # samples per second
        }

        # Professional Configuration with Adaptive Parameters for Large Files
        # Calculate base configuration values
        base_max_peaks = 2000  # Base value for maximum peaks

        # Initialize configuration with enhanced values for optimal performance and accuracy
        self.config = {
            # Peak Detection Settings
            'target_segments': ['high', 'very_high'],  # Focus on high amplitude segments for clearer drum hits
            'min_peak_distance': 0.045,  # Further increased to 45ms to better reduce suspicious onsets
            'cluster_refinement_distance': 0.055,  # Further increased to 55ms for better separation of drum hits
            'aggressive_clustering': True,  # Enable aggressive post-clustering refinement
            'onset_methods': ['energy', 'hfc', 'spectral_flux', 'complex'],  # Added 'complex' for better onset detection
            'max_peaks': base_max_peaks,  # Will be adjusted based on file duration
            'peaks_per_minute': 95,  # Further reduced to 95 for more realistic drum patterns

            # Adaptive Processing Settings
            'enable_adaptive_processing': True,  # Enable adaptive processing for large files
            'chunk_size_seconds': 25,  # Optimized to 25s for better balance between memory usage and context
            'overlap_seconds': 4,  # Increased to 4s for better continuity between chunks
            'progressive_confidence_threshold': True,  # Adjust confidence threshold based on file position

            # Signal Processing Settings
            'noise_reduction': True,
            'multi_stage_denoising': False,  # Disabled for better performance
            'percussive_separation': True,  # Critical for drum detection, keep enabled
            'adaptive_thresholding': True,

            # Analysis Settings
            'transient_filtering': True,  # Enhanced transient detection for drums
            'drum_classification': True,  # Keep enabled for accurate drum hit classification
            'temporal_consistency': True,  # Improved rhythm-based filtering
            'confidence_scoring': True,
            'min_confidence_threshold': 0.45,  # Added explicit minimum confidence threshold

            # Performance Settings
            'multi_threading': True,
            'parallel_processing': True,
            'use_caching': True,
            'memory_optimization': True,  # Enable memory optimization for large files
            'batch_size': 1024,  # Added explicit batch size for better memory management

            # madmom Settings
            'use_madmom_beat_tracking': True,
            'use_madmom_onset_detection': True,
            'madmom_onset_threshold': 0.32,  # Further reduced to 0.32 for better sensitivity to subtle onsets
            'madmom_fps': 100,
            'madmom_beat_tracking_method': 'default',  # 'default', 'comb', 'acf'
            'madmom_tempo_range': (60, 220),  # Expanded upper range to 220 BPM for faster drum patterns

            # Visual Validation Settings
            'use_visual_validation': True,  # Enable visual validation by default
            'validation_threshold': 0.7,  # Reduced from 0.8 to 0.7 for more lenient validation
            'is_drum_stem': False,  # Will be set based on file analysis

            # Advanced Settings
            'adaptive_window_size': True,  # Enable adaptive window sizing based on audio characteristics
            'energy_threshold_factor': 0.5,  # Factor for adaptive energy threshold calculation
            'suspicious_onset_tolerance': 0.06  # Tolerance for considering onsets as suspicious (60ms)
        }

        # This will be updated when a file is loaded
        self._update_config_for_file_duration(0)

        # Performance tracking
        self.processing_times = {}
        self.last_analysis_timestamp = None
        self.analysis_time = 0.0

        # Initialize logger
        logger.info("WaveformAnalyzer initialized with madmom integration")

        # Initialize visual validator if available
        if VISUAL_VALIDATOR_AVAILABLE and self.config.get('use_visual_validation', False):
            try:
                self.visual_validator = VisualValidator(self.config)
                logger.info("Visual validator initialized")
            except Exception as e:
                logger.warning(f"Error initializing visual validator: {e}")
                logger.warning("Visual validation features will be disabled")

    def _update_config_for_file_duration(self, duration_seconds: float) -> None:
        """
        Update configuration parameters based on file duration.

        This method adjusts various configuration parameters to optimize
        processing for files of different lengths, ensuring that long files
        are processed efficiently while maintaining accuracy.

        Args:
            duration_seconds: Duration of the audio file in seconds
        """
        if duration_seconds <= 0:
            # Default values for when duration is unknown
            self.config['max_peaks'] = 2000
            return

        # Calculate appropriate max_peaks based on file duration
        # For longer files, we expect more peaks
        minutes = duration_seconds / 60.0

        # Calculate max peaks based on expected peaks per minute
        # with a reasonable upper limit
        calculated_max_peaks = int(minutes * self.config['peaks_per_minute'])

        # Ensure we have a reasonable minimum and maximum
        min_peaks = 1000  # Minimum peaks to detect
        max_peaks = 10000  # Maximum peaks to avoid memory issues

        self.config['max_peaks'] = max(min_peaks, min(calculated_max_peaks, max_peaks))

        # Adjust other parameters based on file duration

    @enhanced_profile_method("load_file")
    def load_file(self, file_path: Union[str, Path]) -> bool:
        """
        Load audio file for analysis

        Args:
            file_path: Path to audio file

        Returns:
            bool: True if file loaded successfully
        """
        try:
            self.file_path = Path(file_path)
            self.filename = self.file_path.name

            print(f"\n{'=' * 80}")
            print(f"🎵 LOADING AUDIO FILE: {self.filename}")
            print(f"{'=' * 80}")
            logger.info(f"Loading audio file: {self.filename}")

            if not self.file_path.exists():
                print(f"❌ File not found: {self.file_path}")
                logger.error(f"File not found: {self.file_path}")
                return False

            # Check if this is a drum stem
            file_path_str = str(file_path).lower()
            self.is_drum_stem = ('drum' in file_path_str or
                                 '/drums.' in file_path_str or
                                 '\\drums.' in file_path_str or
                                 'drum.wav' in file_path_str or
                                 'drums.wav' in file_path_str)

            # If this is not a drum stem, try to find the drum stem file
            if not self.is_drum_stem:
                # Store the original file path
                self.original_file_path = self.file_path
                print(f"⚠️ WARNING: File does not appear to be a drum stem: {self.filename}")
                print(f"🔍 Searching for drum stem file...")

                # Try to find the drum stem file
                file_dir = os.path.dirname(file_path)
                file_name = os.path.splitext(os.path.basename(file_path))[0]

                # Possible drum stem file paths
                drum_stem_paths = [
                    os.path.join(file_dir, f"{file_name}_stems", file_name, "drums.wav"),
                    os.path.join(file_dir, f"{file_name}_stems", "drums.wav"),
                    os.path.join(file_dir, "drums.wav"),
                ]

                # Check if any of the drum stem paths exist
                drum_stem_found = False
                for drum_path in drum_stem_paths:
                    if os.path.isfile(drum_path):
                        print(f"🥁 Found drum stem file: {drum_path}")
                        logger.info(f"Found drum stem file: {drum_path}")
                        # Update file path to use the drum stem
                        self.file_path = Path(drum_path)
                        self.filename = self.file_path.name
                        self.is_drum_stem = True
                        drum_stem_found = True
                        break

                if not drum_stem_found:
                    print(f"⚠️ WARNING: No drum stem file found. Using original file: {self.filename}")
                    logger.warning(f"No drum stem file found. Using original file: {self.filename}")

            if self.is_drum_stem:
                print(f"\n{'=' * 80}")
                print(f"🥁 CONFIRMED: ANALYZING DRUM STEM FILE: {self.filename}")
                print(f"{'=' * 80}")
                logger.info(f"CONFIRMED: Analyzing drum stem file: {self.filename}")
            else:
                print(f"\n{'=' * 80}")
                print(f"⚠️ WARNING: NOT A DRUM STEM FILE: {self.filename}")
                print(f"{'=' * 80}")
                logger.warning(f"Not a drum stem file: {self.filename}")

            print("📚 Checking librosa availability...")
            if not LIBROSA_AVAILABLE:
                print("❌ librosa not available - cannot load audio file")
                logger.error("librosa not available - cannot load audio file")
                return False

            # Load audio with librosa
            print("🔄 Loading audio data with librosa...")
            start_time = time.time()
            waveform_mono, self.sample_rate = librosa.load(
                str(self.file_path),
                sr=None,  # Keep original sample rate
                mono=True  # Convert to mono
            )
            print(f"✅ Audio loaded: length={len(waveform_mono)}, sr={self.sample_rate}")

            # Convert to 2D array format expected by waveform widget
            # Widget expects waveform_data[0] to access the audio data
            self.waveform_data = [waveform_mono]  # Wrap in list to make it 2D-like
            print("🔄 Converted to 2D format for widget compatibility")

            # Set channels (mono after librosa.load with mono=True)
            self.channels = 1

            self.duration_seconds = len(waveform_mono) / self.sample_rate
            self.processing_times['file_loading'] = time.time() - start_time
            print(f"📊 Duration: {self.duration_seconds:.2f}s, Channels: {self.channels}")

            # Print absolute file path to confirm exactly which file is being analyzed
            abs_path = os.path.abspath(str(self.file_path))
            print(f"\n🔍 ABSOLUTE PATH OF AUDIO FILE BEING ANALYZED:")
            print(f"📂 {abs_path}")
            logger.info(f"Absolute path of audio file being analyzed: {abs_path}")

            # Update configuration based on file duration
            self._update_config_for_file_duration(self.duration_seconds)

            # Update config with drum stem information
            self.config['is_drum_stem'] = self.is_drum_stem
            logger.info(f"Updated config with is_drum_stem={self.is_drum_stem}")

            # Re-initialize visual validator with updated config if needed
            if VISUAL_VALIDATOR_AVAILABLE and self.config.get('use_visual_validation', False):
                if self.visual_validator is None:
                    try:
                        self.visual_validator = VisualValidator(self.config)
                        logger.info("Visual validator initialized with updated config")
                    except Exception as e:
                        logger.warning(f"Error initializing visual validator: {e}")
                else:
                    # Update existing validator with new config
                    self.visual_validator.config = self.config
                    logger.info("Updated existing visual validator with new config")

            print("\n🔧 Initializing noise filter...")
            # Initialize processing components
            self.noise_filter = NoiseFilter(self.sample_rate)

            print("🥁 Initializing drum classifier...")
            self.drum_classifier = DrumClassifier(DrumClassificationModel())

            # Reset analysis state
            self.is_analyzed = False
            self.peaks = []
            print("🔄 Reset analysis state")

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
                                if self.is_drum_stem and widget.music_file_info['path'] != str(self.file_path):
                                    logger.info(
                                        f"Updating music_file_info path from {widget.music_file_info['path']} to {self.file_path}")
                                    widget.music_file_info['path'] = str(self.file_path)
                                    print(f"🔄 Updated music_file_info path to: {self.file_path}")
            except Exception as e:
                logger.warning(f"Error updating music_file_info path: {str(e)}")

            return True

        except Exception as e:
            print(f"❌ Error loading file: {str(e)}")
            logger.error(f"Error loading file: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    @enhanced_profile_method("process_waveform")
    def process_waveform(self, callback=None) -> None:
        """
        Process waveform data and detect drum hits with enhanced algorithms

        Args:
            callback: Optional callback function to call when processing is complete
        """
        print("\n" + "=" * 80)
        print("🎵 STARTING WAVEFORM PROCESSING WITH COMPREHENSIVE DEBUG")
        print("=" * 80)

        if self.waveform_data is None or len(self.waveform_data) == 0:
            print("❌ ERROR: No waveform data loaded")
            logger.error("No waveform data loaded")
            if callback:
                callback(False)
            return

        print(f"✅ Waveform data available: shape={np.array(self.waveform_data).shape}")
        print(f"📊 Sample rate: {self.sample_rate}")
        print(f"⏱️ Duration: {self.duration_seconds}s")
        print(f"🥁 Is drum stem: {self.is_drum_stem}")

        self.is_processing = True

        # Initialize enhanced progress tracking
        self._init_progress_tracking()

        def _process():
            try:
                print("\n🚀 Starting comprehensive waveform analysis...")
                logger.info("Starting comprehensive waveform analysis...")
                start_time = time.time()

                # Step 1: Noise analysis and filtering
                print("\n📊 STEP 1: Analyzing noise characteristics...")
                self._update_stage_progress('noise_analysis', 0.0, "🔍 Analyzing noise characteristics...")
                self._analyze_noise_characteristics()
                print(f"   ✅ Noise analysis complete - noise_floor: {self.noise_floor:.6f}")
                self._update_stage_progress('noise_analysis', 1.0,
                                            f"✅ Noise analysis complete - floor: {self.noise_floor:.6f}")

                # Step 2: Signal preprocessing
                print("\n🔧 STEP 2: Signal preprocessing...")
                self._update_stage_progress('preprocessing', 0.0, "🔧 Preprocessing signal...")
                processed_signal = self._preprocess_signal()
                print(f"   ✅ Preprocessing complete - signal shape: {processed_signal.shape}")
                print(
                    f"   📈 Signal stats: min={np.min(processed_signal):.6f}, max={np.max(processed_signal):.6f}, mean={np.mean(processed_signal):.6f}")
                self._update_stage_progress('preprocessing', 1.0,
                                            f"✅ Preprocessing complete - {processed_signal.shape[0]} samples")

                # Step 3: Multi-method onset detection
                if MADMOM_AVAILABLE:
                    print("\n🎯 STEP 3: Multi-method onset detection with madmom...")
                    self._update_stage_progress('onset_detection', 0.0, "🎯 Detecting onsets with madmom...")
                else:
                    print("\n🎯 STEP 3: Multi-method onset detection (fallback mode - madmom not available)...")
                    self._update_stage_progress('onset_detection', 0.0, "🎯 Detecting onsets with fallback methods...")
                onset_candidates = self._detect_onsets_multi_method(processed_signal)
                print(f"   ✅ Onset detection complete - found {len(onset_candidates)} candidates")
                if len(onset_candidates) > 0:
                    candidate_times = [f"{c['time']:.3f}s" for c in onset_candidates[:5]]
                    print(f"   📍 First 5 candidates: {candidate_times}")
                else:
                    print("   ⚠️ WARNING: No onset candidates found!")
                self._update_stage_progress('onset_detection', 1.0, f"✅ Found {len(onset_candidates)} onset candidates",
                                            len(onset_candidates))

                # Step 4: Peak refinement and filtering
                print("\n🔍 STEP 4: Peak refinement and filtering...")
                self._update_stage_progress('peak_refinement', 0.0, "🔍 Refining and filtering peaks...")
                refined_peaks = self._refine_and_filter_peaks(onset_candidates, processed_signal)
                print(f"   ✅ Peak refinement complete - {len(refined_peaks)} peaks after refinement")
                self._update_stage_progress('peak_refinement', 1.0, f"✅ Refined to {len(refined_peaks)} peaks",
                                            len(refined_peaks))

                # Step 5: Drum classification
                print("\n🥁 STEP 5: Drum classification...")
                self._update_stage_progress('classification', 0.0, "🥁 Classifying drum types...")
                if self.config['drum_classification']:
                    print("   🔄 Running drum classification...")
                    classified_peaks = self._classify_drum_hits(refined_peaks, processed_signal)
                    print(f"   ✅ Classification complete - {len(classified_peaks)} classified peaks")
                    self._update_stage_progress('classification', 1.0,
                                                f"✅ Classified {len(classified_peaks)} drum hits",
                                                len(classified_peaks))
                else:
                    print("   ⏭️ Skipping drum classification (disabled)")
                    classified_peaks = refined_peaks
                    self._update_stage_progress('classification', 1.0, "⏭️ Classification skipped (disabled)",
                                                len(classified_peaks))

                # Step 6: Amplitude segment filtering
                print("\n📏 STEP 6: Amplitude segment filtering...")
                self._update_stage_progress('amplitude_filtering', 0.0, "📏 Filtering by amplitude segments...")
                final_peaks = self._filter_by_amplitude_segments(classified_peaks)
                print(f"   ✅ Amplitude filtering complete - {len(final_peaks)} peaks after filtering")
                self._update_stage_progress('amplitude_filtering', 1.0,
                                            f"✅ Amplitude filtering: {len(final_peaks)} peaks", len(final_peaks))

                # Step 7: Final validation and sorting
                print("\n✅ STEP 7: Final validation and sorting...")
                self._update_stage_progress('final_validation', 0.0, "✅ Final validation and sorting...")
                self.peaks = self._validate_and_sort_peaks(final_peaks)
                print(f"   ✅ Validation complete - {len(self.peaks)} final peaks")
                self._update_stage_progress('final_validation', 1.0,
                                            f"✅ Validation complete - {len(self.peaks)} final peaks", len(self.peaks))

                # Analysis complete
                self.is_analyzed = True
                self.is_processing = False
                self.analysis_time = time.time() - start_time

                # Run visual validation if enabled
                if self.config.get('use_visual_validation', False) and VISUAL_VALIDATOR_AVAILABLE:
                    print("\n🔍 Running visual validation...")
                    logger.info("Running visual validation on analysis results")
                    logger.info("Generating comprehensive validation report...")

                    # Get validation report
                    validation_report = self.validate_analysis_results()
                    validation_score = validation_report.get('validation_score', 0)
                    validation_threshold = self.config.get('validation_threshold', 0.7)

                    # Get detailed metrics from the report
                    peak_details = validation_report.get('details', {}).get('peaks', {})
                    onset_details = validation_report.get('details', {}).get('onsets', {})

                    # Calculate percentages for better context
                    peak_valid_percent = (peak_details.get('valid', 0) / peak_details.get('total', 1)) * 100 if peak_details.get('total', 0) > 0 else 0
                    onset_valid_percent = (onset_details.get('valid', 0) / onset_details.get('total', 1)) * 100 if onset_details.get('total', 0) > 0 else 0

                    # Log detailed metrics with percentages
                    print(f"   📊 Peak validation: {peak_details.get('valid', 0)}/{peak_details.get('total', 0)} valid peaks ({peak_valid_percent:.1f}%)")
                    print(f"   📊 Onset validation: {onset_details.get('valid', 0)}/{onset_details.get('total', 0)} valid onsets ({onset_valid_percent:.1f}%)")

                    # Log suspicious counts for more context
                    suspicious_peaks = peak_details.get('suspicious', 0)
                    suspicious_onsets = onset_details.get('suspicious', 0)
                    if suspicious_peaks > 0:
                        print(f"   ⚠️ Found {suspicious_peaks} suspicious peaks")
                        logger.info(f"Found {suspicious_peaks} suspicious peaks")
                    if suspicious_onsets > 0:
                        print(f"   ⚠️ Found {suspicious_onsets} suspicious onsets")
                        logger.info(f"Found {suspicious_onsets} suspicious onsets")

                    # Print validation result with more context
                    if validation_score >= validation_threshold:
                        print(f"   ✅ Visual validation passed with score: {validation_score:.2f} (threshold: {validation_threshold})")
                        logger.info(f"Visual validation passed with score: {validation_score:.2f}")
                        if validation_score >= 0.9:
                            print(f"   🌟 Excellent analysis quality (score: {validation_score:.2f})")
                        elif validation_score >= 0.8:
                            print(f"   ✨ Good analysis quality (score: {validation_score:.2f})")
                        else:
                            print(f"   👍 Acceptable analysis quality (score: {validation_score:.2f})")
                    else:
                        print(f"   ⚠️ Visual validation score below threshold: {validation_score:.2f} < {validation_threshold}")
                        logger.warning(f"Visual validation score below threshold: {validation_score:.2f} < {validation_threshold}")
                        print(f"   👉 Consider adjusting analysis parameters or using manual peak editing")

                    # Print recommendations if any
                    recommendations = validation_report.get('recommendations', [])
                    if recommendations:
                        print("   📋 Validation recommendations:")
                        logger.info(f"Validation generated {len(recommendations)} recommendations")
                        for i, rec in enumerate(recommendations):
                            print(f"      {i+1}. {rec}")
                            logger.info(f"Recommendation {i+1}: {rec}")

                    # Add a summary line
                    print(f"   📈 Overall validation: {validation_score:.2f} score ({peak_valid_percent:.1f}% valid peaks, {onset_valid_percent:.1f}% valid onsets)")
                else:
                    print("   ⏭️ Visual validation skipped (disabled or not available)")
                    logger.info("Visual validation skipped (disabled or not available)")

                # Print summary
                print("\n" + "=" * 80)
                print(f"✅ ANALYSIS COMPLETE - {len(self.peaks)} peaks detected in {self.analysis_time:.2f}s")
                print(f"   🔍 Noise floor: {self.noise_floor:.6f}")
                print(f"   📊 Dynamic range: {self.dynamic_range:.6f}")
                print(f"   ⚡ Processing speed: {len(self.waveform_data[0]) / self.analysis_time:.2f} samples/sec")
                print("=" * 80)

                # Emit signal that peak detection is complete
                self.peak_detection_complete.emit(True)

                # Call callback if provided
                if callback:
                    callback(True)

            except Exception as e:
                print(f"❌ Error in waveform processing: {str(e)}")
                logger.error(f"Error in waveform processing: {str(e)}")
                import traceback
                traceback.print_exc()
                self.is_processing = False
                self.peak_detection_complete.emit(False)
                if callback:
                    callback(False)

        # Run processing in a separate thread
        if self.config['multi_threading']:
            print("🧵 Starting processing in separate thread...")
            threading.Thread(target=_process).start()
        else:
            print("🔄 Processing in main thread...")
            _process()

    def _detect_spectral_peaks(self, signal: np.ndarray, sr: int) -> List[Dict[str, Any]]:
        """
        Detect peaks using spectral analysis.

        Args:
            signal: Input signal
            sr: Sample rate

        Returns:
            List of detected peaks
        """
        if not SCIPY_AVAILABLE:
            return []

        # Calculate spectrogram
        n_fft = 2048
        hop_length = 512

        if LIBROSA_AVAILABLE:
            stft = librosa.stft(signal, n_fft=n_fft, hop_length=hop_length)
            mag_spec = np.abs(stft)

            # Calculate spectral flux
            flux = self.signal_processor.spectral_flux(stft)

            # Normalize
            if np.max(flux) > 0:
                flux = flux / np.max(flux)

            # Find peaks in flux
            peaks = scipy.signal.find_peaks(flux, height=0.1, distance=int(sr * 0.015 / hop_length))[0]

            # Convert to time
            peak_times = librosa.frames_to_time(peaks, sr=sr, hop_length=hop_length)

            # Create peak dictionaries
            peak_dicts = []
            for i, time in enumerate(peak_times):
                peak_dict = {
                    'time': float(time),
                    'amplitude': float(flux[peaks[i]]),
                    'confidence': 0.7,
                    'method': 'spectral_flux',
                    'type': 'generic'
                }
                peak_dicts.append(peak_dict)

            return peak_dicts
        else:
            return []

    def _analyze_noise_characteristics(self) -> None:
        """
        Analyze noise characteristics of the waveform.
        """
        if self.waveform_data is None or len(self.waveform_data) == 0:
            self.noise_floor = 0.01
            self.dynamic_range = 1.0
            return

        signal = self.waveform_data[0]

        # Divide signal into chunks for analysis
        chunk_size = min(44100, len(signal))  # 1 second at 44.1kHz or smaller if signal is shorter
        num_chunks = max(10, len(signal) // chunk_size)  # At least 10 chunks

        # Analyze each chunk
        noise_floors = []
        for i in range(num_chunks):
            start = i * (len(signal) // num_chunks)
            end = (i + 1) * (len(signal) // num_chunks)
            chunk = signal[start:end]

            # Estimate noise floor for this chunk
            noise_floor = self._estimate_chunk_noise_floor(chunk, i)
            noise_floors.append(noise_floor)

        # Use the median of the chunk noise floors
        self.noise_floor = np.median(noise_floors)

        # Calculate dynamic range
        signal_max = np.max(np.abs(signal))
        if self.noise_floor > 0:
            self.dynamic_range = signal_max / self.noise_floor
        else:
            self.dynamic_range = 1000.0  # Arbitrary large value

        print(f"   📊 Noise analysis: floor={self.noise_floor:.6f}, dynamic_range={self.dynamic_range:.2f}")

    def _estimate_chunk_noise_floor(self, chunk: np.ndarray, chunk_num: int) -> float:
        """
        Estimate noise floor for a chunk of audio.

        Args:
            chunk: Audio chunk
            chunk_num: Chunk number for logging

        Returns:
            Estimated noise floor
        """
        # Method 1: Percentile-based estimation
        noise_floor_1 = np.percentile(np.abs(chunk), 5)

        # Method 2: RMS of the quietest section
        if len(chunk) >= 1024:
            section_size = 1024
            num_sections = len(chunk) // section_size
            if num_sections > 0:
                section_rms = []
                for i in range(num_sections):
                    section = chunk[i * section_size:(i + 1) * section_size]
                    rms = np.sqrt(np.mean(section ** 2))
                    section_rms.append(rms)
                noise_floor_2 = np.min(section_rms) if section_rms else noise_floor_1
            else:
                noise_floor_2 = noise_floor_1
        else:
            noise_floor_2 = noise_floor_1

        # Method 3: Statistical estimation
        if SCIPY_AVAILABLE:
            # Assume noise follows a normal distribution
            # Estimate standard deviation of the noise
            sorted_abs = np.sort(np.abs(chunk))
            # Use the first 20% of samples (assumed to be mostly noise)
            noise_samples = sorted_abs[:int(len(sorted_abs) * 0.2)]
            if len(noise_samples) > 0:
                noise_floor_3 = np.mean(noise_samples) + 2 * np.std(noise_samples)
            else:
                noise_floor_3 = noise_floor_1
        else:
            noise_floor_3 = noise_floor_1

        # Combine estimates (weighted average)
        noise_floor = 0.4 * noise_floor_1 + 0.4 * noise_floor_2 + 0.2 * noise_floor_3

        # Ensure minimum value to prevent division by zero
        noise_floor = max(noise_floor, 1e-6)

        return float(noise_floor)

    def _preprocess_signal(self) -> np.ndarray:
        """
        Preprocess signal for analysis.

        Returns:
            Preprocessed signal
        """
        if self.waveform_data is None or len(self.waveform_data) == 0:
            return np.array([])

        signal = self.waveform_data[0].copy()

        # Apply noise reduction if enabled
        if self.config['noise_reduction'] and self.noise_filter is not None:
            print("   🔄 Applying noise reduction...")
            if self.config['multi_stage_denoising']:
                signal = self.noise_filter.multi_stage_denoising(signal)
                print("   ✅ Multi-stage denoising complete")
            else:
                signal = self.noise_filter.apply_noise_reduction(signal)
                print("   ✅ Basic noise reduction complete")

        # Apply percussive separation if enabled
        if self.config['percussive_separation'] and LIBROSA_AVAILABLE:
            print("   🔄 Applying percussive/harmonic separation...")
            percussive, _ = self.signal_processor.percussive_harmonic_separation(signal, self.sample_rate)
            signal = percussive
            print("   ✅ Percussive separation complete")

        # Apply adaptive thresholding if enabled
        if self.config['adaptive_thresholding'] and SCIPY_AVAILABLE:
            print("   🔄 Applying adaptive thresholding...")
            signal = self.signal_processor.adaptive_threshold(signal)
            print("   ✅ Adaptive thresholding complete")

        return signal

    def _detect_onsets_multi_method(self, signal: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect onsets using multiple methods including madmom.

        Args:
            signal: Preprocessed signal

        Returns:
            List of onset candidates
        """
        print("   🔄 Detecting onsets with multiple methods...")
        onset_candidates = []

        # Method 1: madmom RNN-based onset detection (primary method)
        if MADMOM_AVAILABLE and self.config['use_madmom_onset_detection']:
            print("   🔄 Running madmom RNN-based onset detection...")
            try:
                # Create a temporary file for madmom to process
                # (madmom works best with file input rather than numpy arrays)
                import tempfile
                import soundfile as sf

                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_path = temp_file.name

                # Write signal to temporary file
                sf.write(temp_path, signal, self.sample_rate)

                # Process with madmom
                act = self.onset_processor(temp_path)
                onset_times = self.onset_peak_picker(act)

                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass

                # Convert to onset candidates
                for time in onset_times:
                    onset_candidates.append({
                        'time': float(time),
                        'amplitude': 1.0,  # Will be refined later
                        'confidence': 0.9,  # High confidence for madmom detections
                        'method': 'madmom_rnn',
                        'type': 'generic'
                    })

                print(f"   ✅ madmom RNN onset detection found {len(onset_times)} onsets")
            except Exception as e:
                print(f"   ⚠️ Error in madmom RNN onset detection: {e}")
                logger.error(f"Error in madmom RNN onset detection: {e}")
        elif not MADMOM_AVAILABLE:
            print("   ⚠️ madmom not available - skipping RNN-based onset detection")

        # Method 2: madmom beat tracking (for rhythmic structure)
        if MADMOM_AVAILABLE and self.config['use_madmom_beat_tracking']:
            print("   🔄 Running madmom beat tracking...")
            try:
                # Create a temporary file for madmom to process
                import tempfile
                import soundfile as sf

                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_path = temp_file.name

                # Write signal to temporary file
                sf.write(temp_path, signal, self.sample_rate)

                # Process with madmom
                act = self.beat_processor(temp_path)
                beat_times = self.beat_tracker(act)

                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass

                # Convert to onset candidates
                for time in beat_times:
                    onset_candidates.append({
                        'time': float(time),
                        'amplitude': 0.95,  # Slightly lower confidence than onsets
                        'confidence': 0.85,
                        'method': 'madmom_beat',
                        'type': 'generic'
                    })

                print(f"   ✅ madmom beat tracking found {len(beat_times)} beats")
            except Exception as e:
                print(f"   ⚠️ Error in madmom beat tracking: {e}")
                logger.error(f"Error in madmom beat tracking: {e}")
        elif not MADMOM_AVAILABLE:
            print("   ⚠️ madmom not available - skipping beat tracking")

        # If madmom is not available, make sure we emphasize the fallback methods
        if not MADMOM_AVAILABLE:
            print("   🔄 Using fallback detection methods since madmom is not available...")

        # Method 3: Spectral flux (backup method)
        if LIBROSA_AVAILABLE and SCIPY_AVAILABLE:
            print("   🔄 Running spectral flux onset detection...")
            try:
                spectral_peaks = self._detect_spectral_peaks(signal, self.sample_rate)
                onset_candidates.extend(spectral_peaks)
                print(f"   ✅ Spectral flux detection found {len(spectral_peaks)} onsets")
            except Exception as e:
                print(f"   ⚠️ Error in spectral flux detection: {e}")
                logger.error(f"Error in spectral flux detection: {e}")

        # Method 4: Multi-band onset detection (for frequency-specific onsets)
        if SCIPY_AVAILABLE:
            print("   🔄 Running multi-band onset detection...")
            try:
                # Get onset functions for each band
                onset_functions = self.signal_processor.multi_band_onset_detection(signal, self.sample_rate)

                # Process each band
                for band_name, onset_function in onset_functions.items():
                    if len(onset_function) == 0:
                        continue

                    # Find peaks in onset function
                    hop_length = 512  # Same as used in multi_band_onset_detection
                    peaks = scipy.signal.find_peaks(onset_function, height=0.1,
                                                    distance=int(self.sample_rate * 0.015 / hop_length))[0]

                    # Convert to time
                    peak_times = librosa.frames_to_time(peaks, sr=self.sample_rate, hop_length=hop_length)

                    # Add to candidates
                    for i, time in enumerate(peak_times):
                        # Assign confidence based on band
                        if band_name == 'low':
                            confidence = 0.8  # High confidence for kick drum range
                            peak_type = 'kick'
                        elif band_name == 'mid':
                            confidence = 0.75  # Good confidence for snare range
                            peak_type = 'snare'
                        elif band_name == 'high':
                            confidence = 0.7  # Medium confidence for hi-hat range
                            peak_type = 'hi-hat'
                        else:
                            confidence = 0.6  # Lower confidence for other bands
                            peak_type = 'generic'

                        onset_candidates.append({
                            'time': float(time),
                            'amplitude': float(onset_function[peaks[i]]),
                            'confidence': confidence,
                            'method': f'multi_band_{band_name}',
                            'type': peak_type
                        })

                multi_band_count = sum(1 for c in onset_candidates if 'multi_band' in c['method'])
                print(f"   ✅ Multi-band detection found {multi_band_count} onsets")
            except Exception as e:
                print(f"   ⚠️ Error in multi-band detection: {e}")
                logger.error(f"Error in multi-band detection: {e}")

        # Method 5: librosa onset detection (if available)
        if LIBROSA_AVAILABLE:
            print("   🔄 Running librosa onset detection...")
            try:
                # Use librosa's onset detection
                onset_env = librosa.onset.onset_strength(y=signal, sr=self.sample_rate)
                onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=self.sample_rate)
                onset_times = librosa.frames_to_time(onset_frames, sr=self.sample_rate)

                # Add to candidates
                for time in onset_times:
                    onset_candidates.append({
                        'time': float(time),
                        'amplitude': 0.8,  # Medium confidence
                        'confidence': 0.7,
                        'method': 'librosa_onset',
                        'type': 'generic'
                    })

                print(f"   ✅ librosa onset detection found {len(onset_times)} onsets")
            except Exception as e:
                print(f"   ⚠️ Error in librosa onset detection: {e}")
                logger.error(f"Error in librosa onset detection: {e}")

        # Cross-validate detections from different methods
        if len(onset_candidates) > 0:
            print("   🔄 Cross-validating detections from different methods...")
            validated_candidates = self._cross_validate_detections(onset_candidates, signal, self.sample_rate)
            print(f"   ✅ Cross-validation complete - {len(validated_candidates)} validated candidates")
            return validated_candidates
        else:
            print("   ⚠️ No onset candidates found with any method")
            return []

    def _cross_validate_detections(self, candidates: List[Dict[str, Any]], signal: np.ndarray, sr: int) -> List[
        Dict[str, Any]]:
        """
        Cross-validate detections from different methods.

        Args:
            candidates: List of onset candidates
            signal: Input signal
            sr: Sample rate

        Returns:
            List of validated candidates
        """
        if len(candidates) == 0:
            return []

        # Sort candidates by time
        candidates = sorted(candidates, key=lambda x: x['time'])

        # Group candidates that are close in time
        groups = []
        current_group = [candidates[0]]

        for i in range(1, len(candidates)):
            if candidates[i]['time'] - current_group[-1]['time'] < 0.03:  # 30ms window
                current_group.append(candidates[i])
            else:
                groups.append(current_group)
                current_group = [candidates[i]]

        # Add the last group
        if current_group:
            groups.append(current_group)

        # Process each group
        validated_candidates = []

        for group in groups:
            # If multiple methods detected the same onset, increase confidence
            if len(group) > 1:
                # Calculate weighted average time based on confidence
                total_weight = sum(c['confidence'] for c in group)
                avg_time = sum(c['time'] * c['confidence'] for c in group) / total_weight

                # Find the candidate with highest confidence
                best_candidate = max(group, key=lambda x: x['confidence'])

                # Create a new candidate with merged information
                merged_candidate = {
                    'time': avg_time,
                    'amplitude': max(c['amplitude'] for c in group),
                    'confidence': min(0.95, best_candidate['confidence'] + 0.05 * (len(group) - 1)),
                    'method': 'merged',
                    'original_methods': [c['method'] for c in group],
                    'type': best_candidate['type']
                }

                validated_candidates.append(merged_candidate)
            else:
                # Single detection - keep as is
                validated_candidates.append(group[0])

        return validated_candidates

    def _init_progress_tracking(self) -> None:
        """
        Initialize progress tracking for analysis.
        """
        self.progress_tracker['start_time'] = time.time()
        self.progress_tracker['stage_times'] = {}
        self.progress_tracker['current_stage'] = None
        self.progress_tracker['peak_count'] = 0
        self.progress_tracker['processing_speed'] = 0.0

        # Initialize stage times
        for stage in self.progress_tracker['stage_weights']:
            self.progress_tracker['stage_times'][stage] = {
                'start': None,
                'end': None,
                'duration': 0.0
            }

    def _estimate_processing_time(self, signal_length: int) -> float:
        """
        Estimate total processing time based on signal length.

        Args:
            signal_length: Length of signal in samples

        Returns:
            Estimated processing time in seconds
        """
        # Base time for overhead
        base_time = 2.0

        # Time proportional to signal length
        # This is a rough estimate - actual time depends on many factors
        length_factor = signal_length / 44100  # Seconds of audio
        length_time = length_factor * 0.5  # 0.5 seconds of processing per second of audio

        # Additional time for enabled features
        feature_time = 0.0
        if self.config['noise_reduction']:
            feature_time += length_factor * 0.2
        if self.config['percussive_separation']:
            feature_time += length_factor * 0.3
        if self.config['drum_classification']:
            feature_time += length_factor * 0.2

        total_estimate = base_time + length_time + feature_time

        return total_estimate

    def _update_stage_progress(self, stage_name: str, stage_progress: float = 0.0,
                               status_message: str = "", peak_count: int = 0) -> None:
        """
        Update progress for the current processing stage.

        Args:
            stage_name: Name of the current stage
            stage_progress: Progress within the stage (0.0 to 1.0)
            status_message: Status message to display
            peak_count: Number of peaks detected so far
        """
        # Update stage tracking
        if self.progress_tracker['current_stage'] != stage_name:
            # Finalize previous stage if there was one
            if self.progress_tracker['current_stage'] is not None:
                prev_stage = self.progress_tracker['current_stage']
                self.progress_tracker['stage_times'][prev_stage]['end'] = time.time()
                self.progress_tracker['stage_times'][prev_stage]['duration'] = (
                        self.progress_tracker['stage_times'][prev_stage]['end'] -
                        self.progress_tracker['stage_times'][prev_stage]['start']
                )

            # Start new stage
            self.progress_tracker['current_stage'] = stage_name
            self.progress_tracker['stage_times'][stage_name]['start'] = time.time()

        # Update peak count
        if peak_count > 0:
            self.progress_tracker['peak_count'] = peak_count

        # Calculate overall progress
        total_progress = 0.0
        total_weight = 0.0

        for s, weight in self.progress_tracker['stage_weights'].items():
            if s == stage_name:
                # Current stage - use provided progress
                total_progress += weight * stage_progress
            elif self.progress_tracker['stage_times'][s]['end'] is not None:
                # Completed stage
                total_progress += weight
            # Else: not started yet - 0 progress

            total_weight += weight

        # Normalize progress
        if total_weight > 0:
            overall_progress = int(100 * total_progress / total_weight)
        else:
            overall_progress = 0

        # Calculate ETA
        elapsed_time = time.time() - self.progress_tracker['start_time']
        if overall_progress > 0:
            eta = elapsed_time * (100 - overall_progress) / overall_progress
        else:
            eta = 0

        # Calculate processing speed
        if self.waveform_data is not None and len(self.waveform_data) > 0:
            signal_length = len(self.waveform_data[0])
            if elapsed_time > 0:
                self.progress_tracker['processing_speed'] = signal_length / elapsed_time

        # Prepare metrics
        metrics = {
            'progress': overall_progress,
            'elapsed': elapsed_time,
            'eta': eta,
            'peak_count': self.progress_tracker['peak_count'],
            'processing_speed': self.progress_tracker['processing_speed'],
            'current_stage': stage_name,
            'stage_progress': stage_progress
        }

        # Emit signals
        self.analysis_progress.emit(overall_progress)
        self.analysis_status.emit(status_message)
        self.analysis_metrics.emit(metrics)

    def _get_amplitude_at_time(self, signal: np.ndarray, time: float) -> float:
        """
        Get signal amplitude at a specific time.

        Args:
            signal: Input signal
            time: Time in seconds

        Returns:
            Amplitude at the specified time
        """
        sample_index = int(time * self.sample_rate)
        if 0 <= sample_index < len(signal):
            return abs(signal[sample_index])
        return 0.0

    def _refine_and_filter_peaks(self, onset_candidates: List[Dict[str, Any]], signal: np.ndarray) -> List[
        Dict[str, Any]]:
        """
        Refine and filter peak candidates.

        Args:
            onset_candidates: List of onset candidates
            signal: Input signal

        Returns:
            List of refined peaks
        """
        if len(onset_candidates) == 0:
            return []

        # First, cluster and validate onsets
        clustered_peaks = self._cluster_and_validate_onsets(onset_candidates, signal)

        # Apply post-clustering refinement
        if self.config['aggressive_clustering']:
            refined_peaks = self._post_cluster_refinement(clustered_peaks, signal)
        else:
            refined_peaks = clustered_peaks

        # Apply traditional peak filtering
        filtered_peaks = self._traditional_peak_filtering(refined_peaks, signal)

        # Apply intelligent peak selection
        selected_peaks = self._intelligent_peak_selection(filtered_peaks)

        # Add quality metrics
        peaks_with_metrics = self._add_quality_metrics(selected_peaks, signal)

        return peaks_with_metrics

    def _cluster_and_validate_onsets(self, onset_candidates: List[Dict[str, Any]], signal: np.ndarray) -> List[
        Dict[str, Any]]:
        """
        Cluster and validate onset candidates.

        Args:
            onset_candidates: List of onset candidates
            signal: Input signal

        Returns:
            List of clustered and validated onsets
        """
        if len(onset_candidates) == 0:
            return []

        # Sort by time
        sorted_candidates = sorted(onset_candidates, key=lambda x: x['time'])

        # Initialize clusters
        clusters = []
        current_cluster = [sorted_candidates[0]]

        # Cluster based on time proximity
        min_distance = self.config['min_peak_distance']

        for i in range(1, len(sorted_candidates)):
            if sorted_candidates[i]['time'] - current_cluster[-1]['time'] < min_distance:
                current_cluster.append(sorted_candidates[i])
            else:
                clusters.append(current_cluster)
                current_cluster = [sorted_candidates[i]]

        # Add the last cluster
        if current_cluster:
            clusters.append(current_cluster)

        # Process each cluster
        clustered_peaks = []

        for cluster in clusters:
            # For single-candidate clusters, just add the candidate
            if len(cluster) == 1:
                clustered_peaks.append(cluster[0])
                continue

            # For multi-candidate clusters, merge them
            merged_peak = self._intelligent_cluster_merge(cluster, signal)
            if merged_peak:
                clustered_peaks.append(merged_peak)

        return clustered_peaks

    def _post_cluster_refinement(self, clustered_peaks: List[Dict[str, Any]], signal: np.ndarray) -> List[
        Dict[str, Any]]:
        """
        Apply post-clustering refinement to peaks.

        Args:
            clustered_peaks: List of clustered peaks
            signal: Input signal

        Returns:
            List of refined peaks
        """
        if len(clustered_peaks) <= 1:
            return clustered_peaks

        # Sort by time
        sorted_peaks = sorted(clustered_peaks, key=lambda x: x['time'])

        # Apply adaptive distance clustering
        refined_peaks = []
        current_cluster = [sorted_peaks[0]]

        for i in range(1, len(sorted_peaks)):
            # Calculate adaptive distance based on peak characteristics
            adaptive_distance = self._calculate_adaptive_distance(current_cluster[-1], sorted_peaks[i], signal)

            if sorted_peaks[i]['time'] - current_cluster[-1]['time'] < adaptive_distance:
                current_cluster.append(sorted_peaks[i])
            else:
                # Select most prominent peak from cluster
                selected_peak = self._select_most_prominent_peak(current_cluster, signal)
                if selected_peak:
                    refined_peaks.append(selected_peak)
                current_cluster = [sorted_peaks[i]]

        # Process the last cluster
        if current_cluster:
            selected_peak = self._select_most_prominent_peak(current_cluster, signal)
            if selected_peak:
                refined_peaks.append(selected_peak)

        return refined_peaks

    def _select_most_prominent_peak(self, peak_candidates: List[Dict[str, Any]], signal: np.ndarray) -> Optional[
        Dict[str, Any]]:
        """
        Select the most prominent peak from a list of candidates.

        Args:
            peak_candidates: List of peak candidates
            signal: Input signal

        Returns:
            Most prominent peak or None if no candidates
        """
        if not peak_candidates:
            return None

        if len(peak_candidates) == 1:
            return peak_candidates[0]

        # Calculate prominence score for each candidate
        scores = []

        for peak in peak_candidates:
            # Get amplitude at peak time
            amplitude = self._get_amplitude_at_time(signal, peak['time'])

            # Calculate score based on amplitude and confidence
            score = amplitude * peak['confidence']

            # Bonus for certain methods
            if peak['method'] == 'madmom_rnn':
                score *= 1.2  # Bonus for madmom RNN detections
            elif peak['method'] == 'madmom_beat':
                score *= 1.1  # Bonus for madmom beat detections
            elif 'merged' in peak['method']:
                score *= 1.15  # Bonus for merged detections

            scores.append((peak, score))

        # Select peak with highest score
        best_peak = max(scores, key=lambda x: x[1])[0]

        return best_peak

    def _calculate_adaptive_distance(self, onset1: Dict[str, Any], onset2: Dict[str, Any], signal: np.ndarray) -> float:
        """
        Calculate adaptive distance threshold between two onsets.

        Args:
            onset1: First onset
            onset2: Second onset
            signal: Input signal

        Returns:
            Adaptive distance threshold
        """
        # Base distance
        base_distance = self.config['cluster_refinement_distance']

        # Adjust based on onset characteristics
        adjustments = 0.0

        # Adjust based on methods
        if onset1['method'] != onset2['method']:
            # Different methods are more likely to be separate onsets
            adjustments -= 0.005

        # Adjust based on types
        if 'type' in onset1 and 'type' in onset2 and onset1['type'] != onset2['type']:
            # Different types are more likely to be separate onsets
            adjustments -= 0.005

        # Adjust based on amplitude difference
        amp1 = self._get_amplitude_at_time(signal, onset1['time'])
        amp2 = self._get_amplitude_at_time(signal, onset2['time'])
        amp_diff = abs(amp1 - amp2)

        if amp_diff > 0.3:
            # Large amplitude difference suggests separate onsets
            adjustments -= 0.005

        # Apply adjustments
        adjusted_distance = base_distance + adjustments

        # Ensure minimum distance
        return max(0.015, adjusted_distance)

    def _intelligent_cluster_merge(self, cluster: List[Dict[str, Any]], signal: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Intelligently merge a cluster of onset candidates with drum-specific optimizations.

        Args:
            cluster: List of onset candidates in a cluster
            signal: Input signal

        Returns:
            Merged onset or None if cluster is empty
        """
        if not cluster:
            return None

        if len(cluster) == 1:
            return cluster[0]

        # First, check if we have drum type information in the cluster
        drum_types = [onset.get('type', 'generic') for onset in cluster if 'type' in onset]

        # If we have multiple drum types in the same cluster, this might be a complex hit
        # (e.g., kick + hi-hat played simultaneously)
        unique_drum_types = set(drum_types)

        # Special handling for multi-drum hits
        if len(unique_drum_types) > 1 and 'generic' not in unique_drum_types:
            # This might be a complex drum hit - prioritize certain drum types
            priority_order = {'kick': 3, 'snare': 2, 'tom': 1, 'hi-hat': 0, 'cymbal': 0}

            # Find the highest priority drum type in the cluster
            highest_priority = -1
            primary_type = 'generic'

            for drum_type in unique_drum_types:
                if drum_type in priority_order and priority_order[drum_type] > highest_priority:
                    highest_priority = priority_order[drum_type]
                    primary_type = drum_type

            # Find the best onset of the primary type
            primary_onsets = [onset for onset in cluster if onset.get('type', 'generic') == primary_type]
            if primary_onsets:
                best_primary = max(primary_onsets, key=lambda x: x['confidence'])

                # Use the time from the best primary onset but boost confidence due to multiple detections
                merged_onset = best_primary.copy()
                merged_onset['confidence'] = min(0.95, best_primary['confidence'] + 0.1)
                merged_onset['method'] = 'merged_multi_drum'
                merged_onset['original_methods'] = [onset['method'] for onset in cluster]
                merged_onset['drum_types_detected'] = list(unique_drum_types)

                return merged_onset

        # Calculate weighted average time based on confidence, method, and drum type
        weights = []

        for onset in cluster:
            weight = onset['confidence']

            # Adjust weight based on method
            if onset['method'] == 'madmom_rnn':
                weight *= 1.4  # Highest weight for madmom RNN - increased from 1.3
            elif onset['method'] == 'madmom_beat':
                weight *= 1.2  # High weight for madmom beat
            elif 'merged' in onset['method']:
                weight *= 1.25  # High weight for already merged onsets
            elif 'multi_band' in onset['method']:
                weight *= 1.15  # Medium-high weight for multi-band - increased from 1.1

                # Further adjust weight based on frequency band for multi-band detections
                if 'multi_band_low' in onset['method']:
                    # Low frequency band is good for kick drums
                    weight *= 1.1
                elif 'multi_band_mid' in onset['method']:
                    # Mid frequency band is good for snares
                    weight *= 1.05

            # Adjust weight based on drum type if available
            if 'type' in onset:
                if onset['type'] == 'kick' or onset['type'] == 'snare':
                    weight *= 1.2  # Prioritize kick and snare detections
                elif onset['type'] == 'hi-hat':
                    weight *= 1.1  # Slightly prioritize hi-hat detections

            # Check if this onset has been verified as a transient
            if 'transient_verified' in onset and onset['transient_verified']:
                weight *= 1.2  # Prioritize verified transients

            weights.append(weight)

        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        else:
            weights = [1.0 / len(cluster)] * len(cluster)

        # Calculate weighted average time
        avg_time = sum(onset['time'] * weight for onset, weight in zip(cluster, weights))

        # Find the onset with highest confidence
        best_onset = max(cluster, key=lambda x: x['confidence'])

        # For drum hits, we want to preserve the sharp attack, so bias toward the earliest detection
        # within a small window around the weighted average
        earliest_within_window = None
        window_size = 0.01  # 10ms window

        for onset in sorted(cluster, key=lambda x: x['time']):
            if abs(onset['time'] - avg_time) <= window_size:
                earliest_within_window = onset
                break

        # Use the earliest detection within window if available, otherwise use weighted average
        final_time = earliest_within_window['time'] if earliest_within_window else avg_time

        # Create merged onset with enhanced confidence calculation
        confidence_boost = 0.05 * (len(cluster) - 1)  # Base boost from multiple detections

        # Additional boost if multiple detection methods agree
        methods = set(onset['method'] for onset in cluster)
        if len(methods) > 1:
            confidence_boost += 0.05

        # Additional boost if both madmom and traditional methods agree
        has_madmom = any('madmom' in onset['method'] for onset in cluster)
        has_traditional = any('madmom' not in onset['method'] for onset in cluster)
        if has_madmom and has_traditional:
            confidence_boost += 0.05

        merged_onset = {
            'time': final_time,
            'amplitude': max(onset['amplitude'] for onset in cluster),
            'confidence': min(0.95, best_onset['confidence'] + confidence_boost),
            'method': 'merged',
            'original_methods': [onset['method'] for onset in cluster],
            'type': best_onset['type'] if 'type' in best_onset else 'generic'
        }

        return merged_onset

    def _validate_temporal_consistency(self, peaks: List[Dict[str, Any]], signal: np.ndarray) -> List[Dict[str, Any]]:
        """
        Validate peaks based on temporal consistency with enhanced drum pattern recognition.

        Args:
            peaks: List of peaks
            signal: Input signal

        Returns:
            List of temporally consistent peaks
        """
        if len(peaks) <= 2:
            return peaks

        # Sort by time
        sorted_peaks = sorted(peaks, key=lambda x: x['time'])

        # Calculate inter-onset intervals (IOIs)
        iois = [sorted_peaks[i + 1]['time'] - sorted_peaks[i]['time'] for i in range(len(sorted_peaks) - 1)]

        # Calculate IOI statistics
        if len(iois) >= 3:
            median_ioi = np.median(iois)
            ioi_std = np.std(iois)

            # Detect common drum pattern tempos (in seconds between beats)
            # 60-180 BPM range converted to seconds between beats
            tempo_range = [60 / bpm for bpm in range(60, 181)]

            # Check if median IOI corresponds to a common drum tempo
            # or a subdivision of a common tempo (half, quarter, etc.)
            tempo_match = False
            tempo_factor = 1.0

            for tempo in tempo_range:
                # Check if IOI matches tempo or subdivision
                for division in [1, 2, 4]:
                    expected_ioi = tempo / division
                    if abs(median_ioi - expected_ioi) < 0.03:  # Within 30ms
                        tempo_match = True
                        tempo_factor = 1.1  # Boost confidence for peaks in a valid tempo
                        break
                if tempo_match:
                    break

            # Identify outliers with enhanced criteria
            outliers = []
            for i, ioi in enumerate(iois):
                # Check if this IOI is an outlier based on standard deviation
                if abs(ioi - median_ioi) > 1.5 * ioi_std:  # Reduced from 2.0 to 1.5 for stricter filtering
                    # This IOI is an outlier
                    # Mark the later peak as suspicious
                    outliers.append(i + 1)

                # Check if this IOI breaks a consistent pattern
                if i > 0 and abs(ioi - iois[i - 1]) > 0.5 * median_ioi:
                    # Sudden change in rhythm - mark as suspicious
                    outliers.append(i + 1)

            # Adjust confidence of outlier peaks
            for i in outliers:
                if i < len(sorted_peaks):
                    sorted_peaks[i]['confidence'] *= 0.7  # Reduced from 0.8 to 0.7 for stronger penalty
                    sorted_peaks[i]['temporal_outlier'] = True

            # Boost confidence of peaks that fit the pattern
            for i in range(len(sorted_peaks)):
                if i not in outliers and i > 0 and i < len(sorted_peaks) - 1:
                    # Check if this peak is part of a consistent pattern
                    prev_ioi = sorted_peaks[i]['time'] - sorted_peaks[i - 1]['time']
                    next_ioi = sorted_peaks[i + 1]['time'] - sorted_peaks[i]['time']

                    # If both IOIs are similar, this is likely part of a pattern
                    if abs(prev_ioi - next_ioi) < 0.1 * median_ioi:
                        sorted_peaks[i]['confidence'] = min(0.95, sorted_peaks[i]['confidence'] * tempo_factor)
                        sorted_peaks[i]['pattern_match'] = True

            # Identify common drum patterns (e.g., kick-snare alternation)
            if len(sorted_peaks) >= 4:
                for i in range(len(sorted_peaks) - 3):
                    # Check for kick-snare-kick-snare pattern
                    if (sorted_peaks[i].get('type') == 'kick' and
                            sorted_peaks[i + 1].get('type') == 'snare' and
                            sorted_peaks[i + 2].get('type') == 'kick' and
                            sorted_peaks[i + 3].get('type') == 'snare'):

                        # Boost confidence for all peaks in this pattern
                        for j in range(4):
                            sorted_peaks[i + j]['confidence'] = min(0.95, sorted_peaks[i + j]['confidence'] * 1.15)
                            sorted_peaks[i + j]['drum_pattern_match'] = True

        # Apply temporal smoothing
        smoothed_peaks = self._apply_temporal_smoothing(sorted_peaks)

        return smoothed_peaks

    def _apply_temporal_smoothing(self, peaks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply temporal smoothing to peak times.

        Args:
            peaks: List of peaks

        Returns:
            List of peaks with smoothed times
        """
        if len(peaks) <= 2:
            return peaks

        # Copy peaks to avoid modifying originals
        smoothed_peaks = peaks.copy()

        # Apply light smoothing to times
        for i in range(1, len(smoothed_peaks) - 1):
            # Skip high-confidence peaks
            if smoothed_peaks[i]['confidence'] > 0.9:
                continue

            # Skip peaks marked as temporal outliers
            if 'temporal_outlier' in smoothed_peaks[i] and smoothed_peaks[i]['temporal_outlier']:
                continue

            # Apply weighted average with neighbors
            prev_time = smoothed_peaks[i - 1]['time']
            curr_time = smoothed_peaks[i]['time']
            next_time = smoothed_peaks[i + 1]['time']

            # Weight current time more heavily
            smoothed_time = 0.8 * curr_time + 0.1 * prev_time + 0.1 * next_time

            # Update time
            smoothed_peaks[i]['time'] = smoothed_time

        return smoothed_peaks

    def _select_best_from_cluster(self, cluster: List[Dict[str, Any]], signal: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Select the best peak from a cluster.

        Args:
            cluster: List of peaks in a cluster
            signal: Input signal

        Returns:
            Best peak or None if cluster is empty
        """
        if not cluster:
            return None

        if len(cluster) == 1:
            return cluster[0]

        # Calculate score for each peak
        scores = []

        for peak in cluster:
            # Base score is confidence
            score = peak['confidence']

            # Adjust based on method
            if peak['method'] == 'madmom_rnn':
                score *= 1.3
            elif peak['method'] == 'madmom_beat':
                score *= 1.2
            elif 'merged' in peak['method']:
                score *= 1.25

            # Adjust based on amplitude
            amplitude = self._get_amplitude_at_time(signal, peak['time'])
            score *= (0.5 + 0.5 * amplitude)  # Scale factor between 0.5 and 1.0

            scores.append((peak, score))

        # Select peak with highest score
        best_peak = max(scores, key=lambda x: x[1])[0]

        return best_peak

    def apply_aggressive_clustering(self, target_peak_count: int = 1000) -> List[Peak]:
        """
        Apply aggressive clustering to reduce peak count.

        Args:
            target_peak_count: Target number of peaks

        Returns:
            List of clustered peaks
        """
        if len(self.peaks) <= target_peak_count:
            return self.peaks

        # Start with a small distance and increase until we reach target count
        min_distance = 0.01  # 10ms
        max_distance = 0.5  # 500ms
        step = 0.01

        current_distance = min_distance
        clustered_peaks = self.peaks

        while len(clustered_peaks) > target_peak_count and current_distance < max_distance:
            clustered_peaks = self._apply_distance_clustering(self.peaks, current_distance)
            current_distance += step

        return clustered_peaks

    def _apply_distance_clustering(self, peaks: List[Peak], min_distance: float) -> List[Peak]:
        """
        Apply distance-based clustering to peaks.

        Args:
            peaks: List of peaks
            min_distance: Minimum distance between peaks

        Returns:
            List of clustered peaks
        """
        if len(peaks) <= 1:
            return peaks

        # Sort by time
        sorted_peaks = sorted(peaks, key=lambda p: p.time)

        # Group peaks that are close in time
        clusters = []
        current_cluster = [sorted_peaks[0]]

        for i in range(1, len(sorted_peaks)):
            if sorted_peaks[i].time - current_cluster[-1].time < min_distance:
                current_cluster.append(sorted_peaks[i])
            else:
                clusters.append(current_cluster)
                current_cluster = [sorted_peaks[i]]

        # Add the last cluster
        if current_cluster:
            clusters.append(current_cluster)

        # Select most prominent peak from each cluster
        clustered_peaks = []

        for cluster in clusters:
            selected_peak = self._select_most_prominent_from_cluster(cluster)
            if selected_peak:
                clustered_peaks.append(selected_peak)

        return clustered_peaks

    def _select_most_prominent_from_cluster(self, cluster_candidates: List[Peak]) -> Optional[Peak]:
        """
        Select the most prominent peak from a cluster.

        Args:
            cluster_candidates: List of peaks in a cluster

        Returns:
            Most prominent peak or None if cluster is empty
        """
        if not cluster_candidates:
            return None

        if len(cluster_candidates) == 1:
            return cluster_candidates[0]

        # Select peak with highest confidence * amplitude
        scores = [(p, p.confidence * p.amplitude) for p in cluster_candidates]
        best_peak = max(scores, key=lambda x: x[1])[0]

        return best_peak

    def _set_clustered_peaks(self, clustered_peaks: List[Peak]):
        """
        Set the peaks to a clustered subset.

        Args:
            clustered_peaks: List of clustered peaks
        """
        self.peaks = clustered_peaks

        # Update peak data dictionary
        self.peak_data = {}
        for peak_type in ['generic', 'kick', 'snare', 'hi-hat', 'cymbal', 'tom']:
            self.peak_data[peak_type] = [p for p in self.peaks if p.type == peak_type]

    def _traditional_peak_filtering(self, onset_candidates: List[Dict[str, Any]], signal: np.ndarray) -> List[
        Dict[str, Any]]:
        """
        Apply professional peak filtering techniques with adaptive thresholds.

        Args:
            onset_candidates: List of onset candidates
            signal: Input signal

        Returns:
            List of filtered peaks
        """
        if len(onset_candidates) == 0:
            return []

        print(f"   🔍 Starting peak filtering with {len(onset_candidates)} candidates")

        # Calculate adaptive confidence threshold based on signal characteristics
        # and file duration
        adaptive_threshold = self._calculate_adaptive_confidence_threshold(signal)

        # For very large files, we need to be more selective to avoid memory issues
        # but still process the entire file
        if len(onset_candidates) > self.config['max_peaks'] * 2:
            logger.info(f"Very large number of candidates ({len(onset_candidates)}), "
                        f"using progressive filtering")
            print(f"   ⚠️ Large number of candidates ({len(onset_candidates)}), using progressive filtering")

            # Sort by confidence first
            sorted_by_confidence = sorted(onset_candidates, key=lambda x: x['confidence'], reverse=True)

            # Take the top candidates up to max_peaks
            high_confidence_candidates = sorted_by_confidence[:self.config['max_peaks']]

            # For the remaining candidates, apply a stricter threshold
            remaining_candidates = sorted_by_confidence[self.config['max_peaks']:]
            stricter_threshold = adaptive_threshold + 0.1  # Higher threshold for remaining candidates

            # Filter remaining candidates with stricter threshold
            additional_candidates = [p for p in remaining_candidates if p['confidence'] >= stricter_threshold]

            # Combine high confidence candidates with additional filtered candidates
            onset_candidates = high_confidence_candidates + additional_candidates

            print(f"   ✅ Progressive filtering: kept {len(high_confidence_candidates)} high confidence + "
                  f"{len(additional_candidates)} additional candidates")

        # Apply adaptive confidence threshold
        filtered_peaks = [p for p in onset_candidates if p['confidence'] >= adaptive_threshold]
        print(f"   ✅ After confidence filtering (threshold={adaptive_threshold:.2f}): {len(filtered_peaks)} peaks")

        # Filter by transient detection if enabled
        if self.config['transient_filtering']:
            transient_filtered = []
            for peak in filtered_peaks:
                # Use the simpler transient detection method for more reliable results
                if self._is_genuine_transient(signal, peak['time']):
                    peak['transient_verified'] = True
                    transient_filtered.append(peak)
                elif peak['confidence'] > 0.75:  # Very high threshold for non-transients
                    # Keep only very high-confidence peaks even if transient detection fails
                    peak['transient_verified'] = False
                    transient_filtered.append(peak)
            filtered_peaks = transient_filtered
            print(f"   ✅ After transient filtering: {len(filtered_peaks)} peaks")

        # Additional filtering based on peak amplitude
        amplitude_filtered = []
        for peak in filtered_peaks:
            # Get amplitude at peak time
            sample_index = int(peak['time'] * self.sample_rate)
            if 0 <= sample_index < len(signal):
                # Calculate local amplitude with a smaller window focused on the transient
                pre_window_size = min(512, sample_index)
                post_window_size = min(1536, len(signal) - sample_index)

                if pre_window_size > 0 and post_window_size > 0:
                    # Get pre and post windows
                    pre_window = signal[sample_index - pre_window_size:sample_index]
                    post_window = signal[sample_index:sample_index + post_window_size]

                    # Calculate amplitude increase (key characteristic of drum hits)
                    pre_max = np.max(np.abs(pre_window[-100:]))  # Last 100 samples before peak
                    post_max = np.max(np.abs(post_window[:100]))  # First 100 samples after peak

                    amplitude_increase = post_max - pre_max

                    # Only keep peaks with significant amplitude increase
                    if amplitude_increase > 0.15:  # Significant increase for drum hits
                        amplitude_filtered.append(peak)
                    elif post_max > 0.25 and peak['confidence'] > 0.7:  # High absolute amplitude and good confidence
                        amplitude_filtered.append(peak)
                    elif peak['confidence'] > 0.85:  # Very high confidence can override amplitude check
                        amplitude_filtered.append(peak)
                else:
                    # If we can't check amplitude properly, rely on confidence
                    if peak['confidence'] > 0.75:
                        amplitude_filtered.append(peak)
            else:
                # If index is out of bounds, rely on confidence
                if peak['confidence'] > 0.75:
                    amplitude_filtered.append(peak)

        print(f"   ✅ After amplitude filtering: {len(amplitude_filtered)} peaks")

        # Filter out peaks at the very beginning of the track (first 1 second)
        # This helps remove false positives that often appear at the start
        start_filtered = [p for p in amplitude_filtered if p['time'] > 1.0]
        print(f"   ✅ After removing early peaks: {len(start_filtered)} peaks")

        # Improved filtering for isolated peaks
        if len(start_filtered) > 2:
            # Sort by time
            sorted_peaks = sorted(start_filtered, key=lambda x: x['time'])

            # Calculate time differences between consecutive peaks
            time_diffs = [sorted_peaks[i + 1]['time'] - sorted_peaks[i]['time'] for i in range(len(sorted_peaks) - 1)]

            # Calculate median time difference as a reference for rhythm
            if time_diffs:
                median_diff = np.median(time_diffs)

                # Filter out isolated peaks
                non_isolated = []
                for i, peak in enumerate(sorted_peaks):
                    is_isolated = False

                    # Check if this peak is isolated (far from neighbors)
                    if i == 0:  # First peak
                        if len(sorted_peaks) > 1 and sorted_peaks[1]['time'] - peak['time'] > 3 * median_diff:
                            is_isolated = True
                    elif i == len(sorted_peaks) - 1:  # Last peak
                        if peak['time'] - sorted_peaks[i - 1]['time'] > 3 * median_diff:
                            is_isolated = True
                    else:  # Middle peaks
                        if (peak['time'] - sorted_peaks[i - 1]['time'] > 3 * median_diff and
                                sorted_peaks[i + 1]['time'] - peak['time'] > 3 * median_diff):
                            is_isolated = True

                    # Keep non-isolated peaks or high confidence isolated peaks
                    if not is_isolated or peak['confidence'] > 0.85:
                        non_isolated.append(peak)

                print(f"   ✅ After removing isolated peaks: {len(non_isolated)} peaks")
                return non_isolated
            else:
                return sorted_peaks
        else:
            return start_filtered

    def _calculate_adaptive_confidence_threshold(self, signal: np.ndarray) -> float:
        """
        Calculate adaptive confidence threshold based on signal characteristics.

        This professional implementation uses statistical analysis of the signal
        to determine an optimal confidence threshold, taking into account:
        - Signal-to-noise ratio
        - Dynamic range
        - Transient density
        - Overall signal energy
        - File duration

        Args:
            signal: Input signal

        Returns:
            Adaptive confidence threshold
        """
        # Base threshold - starting point for adjustments
        base_threshold = 0.4

        # Initialize adjustments
        snr_adjustment = 0.0
        range_adjustment = 0.0
        density_adjustment = 0.0
        duration_adjustment = 0.0

        try:
            # Calculate signal-to-noise ratio with advanced perceptual weighting
            if len(signal) > 1000:
                try:
                    # Use multiple methods for more robust SNR estimation

                    # Method 1: Percentile-based SNR calculation
                    sorted_signal = np.sort(np.abs(signal))

                    # Use bottom 5% as noise estimate (more focused on true noise floor)
                    noise_level_p = np.mean(sorted_signal[:int(len(sorted_signal) * 0.05)])

                    # Use top 2% as signal estimate (more focused on true peaks)
                    signal_level_p = np.mean(sorted_signal[int(len(sorted_signal) * 0.98):])

                    # Calculate percentile-based SNR with protection against division by zero
                    if noise_level_p > 1e-10:
                        snr_p = signal_level_p / noise_level_p
                    else:
                        snr_p = 100  # Default high value if noise is zero

                    # Method 2: Frequency-domain SNR calculation for better drum detection
                    if LIBROSA_AVAILABLE and len(signal) >= 2048:
                        # Calculate spectrogram
                        n_fft = 2048
                        hop_length = 512
                        stft = librosa.stft(signal, n_fft=n_fft, hop_length=hop_length)
                        mag_spec = np.abs(stft)

                        # Calculate SNR in frequency bands relevant to drums
                        drum_bands = {
                            'kick': (50, 200),  # Low frequencies for kick drums
                            'snare': (200, 500),  # Mid-low frequencies for snare body
                            'hihat': (5000, 10000),  # High frequencies for hi-hats
                        }

                        band_snrs = []
                        for band_name, (low_freq, high_freq) in drum_bands.items():
                            # Convert frequencies to bin indices
                            low_bin = int(low_freq * n_fft / self.sample_rate)
                            high_bin = int(high_freq * n_fft / self.sample_rate)

                            # Ensure valid bin range
                            low_bin = max(0, min(low_bin, mag_spec.shape[0] - 1))
                            high_bin = max(low_bin + 1, min(high_bin, mag_spec.shape[0]))

                            # Extract band spectrum
                            band_spec = mag_spec[low_bin:high_bin, :]

                            if band_spec.size > 0:
                                # Calculate band statistics
                                band_mean = np.mean(band_spec)
                                band_std = np.std(band_spec)

                                # Calculate band SNR
                                if band_std > 1e-10:
                                    band_snr = band_mean / band_std
                                    band_snrs.append(band_snr)

                        # Calculate weighted average of band SNRs
                        if band_snrs:
                            snr_f = np.mean(band_snrs)
                        else:
                            snr_f = snr_p  # Fall back to percentile-based SNR
                    else:
                        snr_f = snr_p  # Fall back to percentile-based SNR

                    # Combine SNR estimates with emphasis on frequency-domain SNR for drums
                    snr = 0.3 * snr_p + 0.7 * snr_f

                    # Apply more sophisticated threshold adjustment based on SNR
                    # This curve provides better sensitivity for drum detection
                    if snr > 100:  # Extremely clean signal
                        snr_adjustment = -0.06  # Lower threshold significantly for very clean signals
                    elif snr > 50:  # Very clean signal
                        snr_adjustment = -0.04  # Lower threshold for clean signals
                    elif snr > 25:  # Clean signal
                        snr_adjustment = -0.02  # Slightly lower threshold
                    elif snr > 15:  # Moderate SNR
                        snr_adjustment = 0.0  # No adjustment
                    elif snr > 8:  # Somewhat noisy
                        snr_adjustment = 0.02  # Slightly higher threshold
                    else:  # Very noisy
                        snr_adjustment = 0.04  # Higher threshold for noisy signals

                    logger.info(f"Calculated SNR: {snr:.1f}, adjustment: {snr_adjustment:.3f}")
                except Exception as e:
                    logger.warning(f"Error calculating SNR: {e}, using default adjustment")
                    snr_adjustment = 0.0

            # Calculate dynamic range with advanced statistical analysis
            if len(signal) > 0:
                try:
                    # Use multiple methods for more comprehensive dynamic range assessment

                    # Method 1: Enhanced percentile-based dynamic range
                    # Using 98th and 2nd percentiles to better capture true dynamic range
                    # while avoiding outliers
                    signal_abs = np.abs(signal)
                    percentile_98 = np.percentile(signal_abs, 98)
                    percentile_2 = np.percentile(signal_abs, 2)
                    dynamic_range_p = percentile_98 - percentile_2

                    # Method 2: RMS-based dynamic range (better for musical content)
                    if LIBROSA_AVAILABLE and len(signal) > 1024:
                        # Calculate RMS energy in frames
                        frame_length = 1024
                        hop_length = 512
                        rms = librosa.feature.rms(y=signal, frame_length=frame_length, hop_length=hop_length)[0]

                        if len(rms) > 0:
                            # Calculate dynamic range from RMS values
                            rms_sorted = np.sort(rms)
                            if len(rms_sorted) > 10:  # Ensure enough frames for percentiles
                                rms_high = np.percentile(rms_sorted, 95)
                                rms_low = np.percentile(rms_sorted, 5)

                                # Avoid division by zero
                                if rms_low > 1e-10:
                                    dynamic_range_rms = 20 * np.log10(rms_high / rms_low)  # in dB
                                    # Normalize to 0-1 range for consistency
                                    dynamic_range_rms = min(1.0, dynamic_range_rms / 60.0)  # 60dB is full scale
                                else:
                                    dynamic_range_rms = dynamic_range_p
                            else:
                                dynamic_range_rms = dynamic_range_p
                        else:
                            dynamic_range_rms = dynamic_range_p
                    else:
                        dynamic_range_rms = dynamic_range_p

                    # Method 3: Crest factor analysis (peak-to-average ratio)
                    # This is particularly useful for detecting transient-rich content like drums
                    if len(signal) > 1000:
                        peak_value = np.max(np.abs(signal))
                        rms_value = np.sqrt(np.mean(signal ** 2))

                        if rms_value > 1e-10:
                            crest_factor = peak_value / rms_value
                            # Normalize to 0-1 range
                            crest_factor_norm = min(1.0, crest_factor / 10.0)  # 10 is a typical maximum
                        else:
                            crest_factor_norm = 0.5  # Default value
                    else:
                        crest_factor_norm = 0.5  # Default value

                    # Combine the different measures with weights favoring methods that work well for drums
                    dynamic_range = (0.3 * dynamic_range_p +
                                     0.3 * dynamic_range_rms +
                                     0.4 * crest_factor_norm)  # Higher weight for crest factor (good for drums)

                    # Apply sophisticated adjustment based on dynamic range
                    # This curve is optimized for drum detection
                    if dynamic_range > 0.85:  # Extremely high dynamic range (typical for clean drum recordings)
                        range_adjustment = -0.05  # Lower threshold significantly
                    elif dynamic_range > 0.7:  # Very high dynamic range
                        range_adjustment = -0.04  # Lower threshold considerably
                    elif dynamic_range > 0.5:  # High dynamic range
                        range_adjustment = -0.02  # Lower threshold moderately
                    elif dynamic_range > 0.3:  # Moderate dynamic range
                        range_adjustment = 0.0  # No adjustment
                    elif dynamic_range > 0.15:  # Low dynamic range
                        range_adjustment = 0.02  # Raise threshold moderately
                    else:  # Very low dynamic range
                        range_adjustment = 0.04  # Raise threshold considerably

                    logger.info(f"Calculated dynamic range: {dynamic_range:.3f}, adjustment: {range_adjustment:.3f}")
                except Exception as e:
                    logger.warning(f"Error calculating dynamic range: {e}, using default adjustment")
                    range_adjustment = 0.0

            # Calculate transient density with advanced detection methods
            if len(signal) > 10000:
                try:
                    # Use multiple complementary methods for robust transient detection

                    # Method 1: Enhanced time-domain derivative analysis
                    if SCIPY_AVAILABLE:
                        # Calculate the derivative of the signal
                        derivative = np.diff(signal)

                        # Apply adaptive thresholding for transient detection
                        # Use multiple percentile thresholds for better accuracy
                        thresholds = [
                            np.percentile(np.abs(derivative), 95),  # Very strong transients
                            np.percentile(np.abs(derivative), 90),  # Strong transients
                            np.std(derivative) * 2.5  # Statistical threshold
                        ]

                        # Count transients at different sensitivity levels
                        transient_counts = [
                            np.sum(np.abs(derivative) > threshold)
                            for threshold in thresholds
                        ]

                        # Calculate weighted average (emphasizing stronger transients)
                        if transient_counts:
                            transient_count_td = (0.5 * transient_counts[0] +
                                                  0.3 * transient_counts[1] +
                                                  0.2 * transient_counts[2])
                        else:
                            transient_count_td = 0
                    else:
                        transient_count_td = 0

                    # Method 2: Spectral flux analysis for transient detection
                    # This is particularly effective for drum transients
                    if LIBROSA_AVAILABLE and len(signal) >= 2048:
                        # Calculate spectrogram
                        n_fft = 2048
                        hop_length = 512
                        stft = librosa.stft(signal, n_fft=n_fft, hop_length=hop_length)
                        mag_spec = np.abs(stft)

                        # Calculate spectral flux (difference between consecutive frames)
                        diff = np.diff(mag_spec, axis=1)
                        # Keep only positive changes (increases in energy)
                        diff = np.maximum(0, diff)
                        # Sum across frequency bins
                        flux = np.sum(diff, axis=0)

                        # Detect peaks in spectral flux
                        if len(flux) > 3:
                            # Normalize flux
                            if np.max(flux) > 0:
                                flux_norm = flux / np.max(flux)
                            else:
                                flux_norm = flux

                            # Adaptive threshold based on flux statistics
                            flux_threshold = np.mean(flux_norm) + 1.5 * np.std(flux_norm)

                            # Count peaks above threshold
                            transient_count_sf = np.sum(flux_norm > flux_threshold)
                        else:
                            transient_count_sf = 0
                    else:
                        transient_count_sf = 0

                    # Combine transient counts from different methods
                    # with weights favoring spectral flux for drum detection
                    if transient_count_td > 0 or transient_count_sf > 0:
                        if LIBROSA_AVAILABLE:
                            # When both methods are available, use weighted combination
                            transient_count = (0.4 * transient_count_td +
                                               0.6 * transient_count_sf)  # Favor spectral flux for drums
                        else:
                            # Fall back to time-domain method only
                            transient_count = transient_count_td
                    else:
                        # Fallback estimate based on signal statistics
                        transient_count = len(signal) / 1000

                    # Calculate density as transients per second
                    if self.duration_seconds > 0:
                        density = transient_count / self.duration_seconds

                        # Apply sophisticated adjustment based on transient density
                        # This curve is optimized for drum detection
                        if density > 15:  # Extremely high density (likely many false positives)
                            density_adjustment = 0.06  # Much higher threshold to filter out noise
                        elif density > 10:  # Very high density
                            density_adjustment = 0.05  # Higher threshold for high density
                        elif density > 7:  # High density
                            density_adjustment = 0.03  # Moderately higher threshold
                        elif density > 4:  # Moderate-high density
                            density_adjustment = 0.01  # Slightly higher threshold
                        elif density > 2:  # Moderate density (typical for drum tracks)
                            density_adjustment = 0.0  # No adjustment
                        elif density > 1:  # Low-moderate density
                            density_adjustment = -0.02  # Slightly lower threshold
                        else:  # Low density
                            density_adjustment = -0.04  # Lower threshold for low density

                        logger.info(
                            f"Calculated transient density: {density:.1f}/s, adjustment: {density_adjustment:.3f}")
                except Exception as e:
                    logger.warning(f"Error calculating transient density: {e}, using default adjustment")
                    density_adjustment = 0.0

            # Adjust based on file duration with more nuanced scaling
            if self.duration_seconds > 0:
                try:
                    # For longer files, use a higher threshold to avoid too many peaks
                    # but with a more gradual curve for better scaling
                    if self.duration_seconds > 600:  # 10+ minutes (very long)
                        duration_adjustment = 0.05
                    elif self.duration_seconds > 300:  # 5+ minutes (long)
                        duration_adjustment = 0.03
                    elif self.duration_seconds > 180:  # 3+ minutes (medium-long)
                        duration_adjustment = 0.02
                    elif self.duration_seconds > 60:  # 1+ minute (medium)
                        duration_adjustment = 0.01
                    elif self.duration_seconds > 30:  # 30+ seconds (short)
                        duration_adjustment = 0.0
                    else:  # Very short
                        duration_adjustment = -0.01  # Lower threshold for very short files

                    logger.info(f"File duration: {self.duration_seconds:.1f}s, adjustment: {duration_adjustment:.3f}")
                except Exception as e:
                    logger.warning(f"Error calculating duration adjustment: {e}, using default")
                    duration_adjustment = 0.0

            # Add spectral complexity analysis for better drum detection
            spectral_adjustment = 0.0
            try:
                if LIBROSA_AVAILABLE and len(signal) >= 2048:
                    # Calculate spectral statistics
                    n_fft = 2048
                    hop_length = 512
                    stft = librosa.stft(signal, n_fft=n_fft, hop_length=hop_length)
                    mag_spec = np.abs(stft)

                    # Calculate spectral centroid and its variation over time
                    if mag_spec.shape[1] > 0:
                        # Calculate spectral centroid
                        freqs = librosa.fft_frequencies(sr=self.sample_rate, n_fft=n_fft)
                        freqs_2d = freqs[:, np.newaxis]  # Make it 2D for broadcasting

                        # Calculate centroid for each frame
                        spec_sum = np.sum(mag_spec, axis=0)
                        spec_sum[spec_sum == 0] = 1e-10  # Avoid division by zero
                        centroid = np.sum(freqs_2d * mag_spec, axis=0) / spec_sum

                        # Calculate statistics of centroid
                        if len(centroid) > 0:
                            centroid_mean = np.mean(centroid)
                            centroid_std = np.std(centroid)

                            # Calculate spectral complexity (variation in spectral content)
                            # Higher values indicate more complex spectral content (e.g., mixed drums)
                            spectral_complexity = min(1.0, centroid_std / (centroid_mean * 0.5 + 1e-10))

                            # Adjust threshold based on spectral complexity
                            if spectral_complexity > 0.8:  # Very complex spectrum (mixed drums)
                                spectral_adjustment = 0.03  # Higher threshold for complex content
                            elif spectral_complexity > 0.5:  # Moderately complex
                                spectral_adjustment = 0.01
                            elif spectral_complexity > 0.3:  # Somewhat simple
                                spectral_adjustment = 0.0
                            else:  # Very simple spectrum (e.g., single drum type)
                                spectral_adjustment = -0.02  # Lower threshold for simple content

                            logger.info(
                                f"Spectral complexity: {spectral_complexity:.3f}, adjustment: {spectral_adjustment:.3f}")
            except Exception as e:
                logger.warning(f"Error calculating spectral adjustment: {e}, using default")
                spectral_adjustment = 0.0

            # Add rhythm analysis for better drum pattern detection
            rhythm_adjustment = 0.0
            try:
                # Use peaks instead of onset_candidates for rhythm analysis
                # This fixes the "name 'onset_candidates' is not defined" error
                if hasattr(self, 'peaks') and len(self.peaks) >= 10:
                    # Extract peak times from existing peaks
                    peak_times = [p.time for p in self.peaks]
                    peak_times.sort()

                    # Calculate inter-onset intervals
                    iois = np.diff(peak_times)

                    if len(iois) > 0:
                        # Calculate IOI statistics
                        ioi_mean = np.mean(iois)
                        ioi_std = np.std(iois)

                        # Calculate coefficient of variation (lower means more regular rhythm)
                        if ioi_mean > 0:
                            ioi_cv = ioi_std / ioi_mean

                            # Calculate rhythm regularity (inverse of CV, normalized to 0-1)
                            rhythm_regularity = max(0.0, min(1.0, 1.0 - ioi_cv))

                            # Adjust threshold based on rhythm regularity
                            # For regular rhythms (likely true drum patterns), lower the threshold
                            if rhythm_regularity > 0.8:  # Very regular rhythm
                                rhythm_adjustment = -0.03  # Lower threshold significantly
                            elif rhythm_regularity > 0.6:  # Fairly regular
                                rhythm_adjustment = -0.02  # Lower threshold moderately
                            elif rhythm_regularity > 0.4:  # Somewhat regular
                                rhythm_adjustment = -0.01  # Lower threshold slightly
                            elif rhythm_regularity > 0.2:  # Somewhat irregular
                                rhythm_adjustment = 0.0  # No adjustment
                            else:  # Very irregular
                                rhythm_adjustment = 0.01  # Raise threshold slightly

                            logger.info(
                                f"Rhythm regularity: {rhythm_regularity:.3f}, adjustment: {rhythm_adjustment:.3f}")
            except Exception as e:
                logger.warning(f"Error calculating rhythm adjustment: {e}, using default")
                rhythm_adjustment = 0.0

            # Calculate final threshold with all adjustments including new spectral and rhythm factors
            adjustments = (
                    snr_adjustment +
                    range_adjustment +
                    density_adjustment +
                    duration_adjustment +
                    spectral_adjustment +
                    rhythm_adjustment
            )
            final_threshold = base_threshold + adjustments

            # Ensure threshold is within reasonable bounds
            # Use a wider range for more adaptability to different content
            final_threshold = max(0.32, min(0.65, final_threshold))

            logger.info(f"Calculated adaptive threshold: {final_threshold:.3f} (base={base_threshold}, "
                        f"adjustments={adjustments:.3f}, components=[SNR:{snr_adjustment:.3f}, "
                        f"DR:{range_adjustment:.3f}, Dens:{density_adjustment:.3f}, "
                        f"Dur:{duration_adjustment:.3f}, Spec:{spectral_adjustment:.3f}, "
                        f"Rhythm:{rhythm_adjustment:.3f}])")

            return final_threshold

        except Exception as e:
            # Fallback in case of any errors
            logger.error(f"Error in adaptive threshold calculation: {e}, using default threshold")
            return 0.38  # Slightly lower default threshold for better sensitivity

    def _calculate_segment_amplitude_thresholds(self, signal: np.ndarray) -> List[float]:
        """
        Calculate amplitude thresholds for different segments of the signal.

        Args:
            signal: Input signal

        Returns:
            List of amplitude thresholds for each segment
        """
        # Divide signal into 10-second segments
        segment_length = 10 * self.sample_rate
        num_segments = max(1, int(np.ceil(len(signal) / segment_length)))
        thresholds = []

        for i in range(num_segments):
            start = i * segment_length
            end = min((i + 1) * segment_length, len(signal))
            segment = signal[start:end]

            if len(segment) > 0:
                # Calculate statistics for this segment
                segment_max = np.max(np.abs(segment))
                segment_mean = np.mean(np.abs(segment))
                segment_std = np.std(np.abs(segment))

                # Calculate threshold based on segment characteristics
                if segment_max > 0.8:  # High amplitude segment
                    segment_threshold = 0.2  # Higher threshold for loud segments
                elif segment_max > 0.5:
                    segment_threshold = 0.15
                elif segment_max > 0.3:
                    segment_threshold = 0.12
                else:
                    segment_threshold = 0.1  # Lower threshold for quiet segments

                # Adjust based on standard deviation (dynamic range within segment)
                if segment_std > 0.2:  # High variation
                    segment_threshold *= 0.9  # Lower threshold for high variation
                elif segment_std < 0.05:  # Low variation
                    segment_threshold *= 1.2  # Higher threshold for low variation

                thresholds.append(segment_threshold)
            else:
                thresholds.append(0.15)  # Default threshold

        # Ensure we have at least one threshold
        if not thresholds:
            thresholds = [0.15]

        return thresholds

    def _apply_context_aware_filtering(self, peaks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply context-aware filtering to remove isolated peaks.

        Args:
            peaks: List of peaks

        Returns:
            Filtered list of peaks
        """
        if len(peaks) <= 2:
            return peaks

        # Sort by time
        sorted_peaks = sorted(peaks, key=lambda x: x['time'])

        # Calculate time differences between consecutive peaks
        time_diffs = [sorted_peaks[i + 1]['time'] - sorted_peaks[i]['time'] for i in range(len(sorted_peaks) - 1)]

        # Calculate median time difference
        if time_diffs:
            median_diff = np.median(time_diffs)
        else:
            median_diff = 0.5  # Default value

        # Identify isolated peaks (peaks that are far from their neighbors)
        isolated_indices = []

        for i in range(len(sorted_peaks)):
            is_isolated = False

            if i == 0:  # First peak
                if len(sorted_peaks) > 1 and sorted_peaks[1]['time'] - sorted_peaks[0]['time'] > 3 * median_diff:
                    is_isolated = True
            elif i == len(sorted_peaks) - 1:  # Last peak
                if sorted_peaks[i]['time'] - sorted_peaks[i - 1]['time'] > 3 * median_diff:
                    is_isolated = True
            else:  # Middle peaks
                prev_diff = sorted_peaks[i]['time'] - sorted_peaks[i - 1]['time']
                next_diff = sorted_peaks[i + 1]['time'] - sorted_peaks[i]['time']

                if prev_diff > 3 * median_diff and next_diff > 3 * median_diff:
                    is_isolated = True

            if is_isolated:
                isolated_indices.append(i)

        # Filter out isolated peaks unless they have very high confidence
        filtered_peaks = []

        for i, peak in enumerate(sorted_peaks):
            if i in isolated_indices:
                # Only keep isolated peaks if they have very high confidence
                if peak['confidence'] > 0.85 and peak.get('transient_verified', False):
                    filtered_peaks.append(peak)
            else:
                filtered_peaks.append(peak)

        return filtered_peaks

    def _intelligent_peak_selection(self, peaks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply intelligent peak selection.

        Args:
            peaks: List of peaks

        Returns:
            List of selected peaks
        """
        if len(peaks) == 0:
            return []

        # Sort by time
        sorted_peaks = sorted(peaks, key=lambda x: x['time'])

        # Apply temporal consistency validation
        if self.config['temporal_consistency']:
            sorted_peaks = self._validate_temporal_consistency(sorted_peaks, self.waveform_data[0])

        # Limit to maximum number of peaks
        if len(sorted_peaks) > self.config['max_peaks']:
            # Sort by confidence and take top N
            sorted_by_confidence = sorted(sorted_peaks, key=lambda x: x['confidence'], reverse=True)
            sorted_peaks = sorted_by_confidence[:self.config['max_peaks']]
            # Re-sort by time
            sorted_peaks = sorted(sorted_peaks, key=lambda x: x['time'])

        return sorted_peaks

    def _calculate_temporal_consistency_score(self, onset: Dict[str, Any], signal: np.ndarray) -> float:
        """
        Calculate temporal consistency score for an onset.

        Args:
            onset: Onset dictionary
            signal: Input signal

        Returns:
            Temporal consistency score
        """
        # This is a placeholder for a more sophisticated temporal consistency calculation
        # In a real implementation, this would analyze the local context around the onset

        # For now, return a default score
        return 0.8

    def _add_quality_metrics(self, peaks: List[Dict[str, Any]], signal: np.ndarray) -> List[Dict[str, Any]]:
        """
        Add quality metrics to peaks.

        Args:
            peaks: List of peaks
            signal: Input signal

        Returns:
            List of peaks with quality metrics
        """
        if len(peaks) == 0:
            return []

        for peak in peaks:
            # Add sub-sample timing
            if self.config['confidence_scoring']:
                peak['precise_time'] = self._calculate_sub_sample_timing(peak, signal)
            else:
                peak['precise_time'] = peak['time']

            # Add SNR estimate
            peak['snr'] = self._estimate_peak_snr(peak, signal)

            # Add spectral centroid
            peak['spectral_centroid'] = self._calculate_peak_spectral_centroid(peak, signal)

        return peaks

    def _calculate_sub_sample_timing(self, peak: Dict[str, Any], signal: np.ndarray) -> float:
        """
        Calculate sub-sample timing for a peak with enhanced precision.

        This method uses advanced peak interpolation to find the exact moment of the drum hit,
        fixing the issue where peaks were detected slightly before the actual hit.

        Args:
            peak: Peak dictionary
            signal: Input signal

        Returns:
            Sub-sample time in seconds with precise alignment to actual drum hit
        """
        time = peak['time']
        sample_index = int(time * self.sample_rate)

        # Use a wider window for better peak detection
        window_size = 5  # Look at 5 samples before and after

        # Check bounds
        if sample_index < window_size or sample_index >= len(signal) - window_size:
            return time

        # Extract window around the peak
        window_start = sample_index - window_size
        window_end = sample_index + window_size + 1
        window = signal[window_start:window_end]
        window_abs = np.abs(window)

        # Find the true maximum in the window
        local_max_idx = np.argmax(window_abs)
        true_peak_idx = window_start + local_max_idx

        # If the true peak is different from the original peak, adjust
        if true_peak_idx != sample_index:
            # The peak was misaligned, use the true peak position
            base_time = true_peak_idx / self.sample_rate

            # For even more precision, use quadratic interpolation around the true peak
            if true_peak_idx > 0 and true_peak_idx < len(signal) - 1:
                prev_sample = abs(signal[true_peak_idx - 1])
                peak_sample = abs(signal[true_peak_idx])
                next_sample = abs(signal[true_peak_idx + 1])

                # Only interpolate if this is truly a local maximum
                if peak_sample > prev_sample and peak_sample > next_sample:
                    # Parabolic interpolation for sub-sample precision
                    denominator = prev_sample - 2 * peak_sample + next_sample

                    # Avoid division by zero or unstable interpolation
                    if abs(denominator) > 1e-6:
                        offset = 0.5 * (prev_sample - next_sample) / denominator

                        # Limit offset to [-0.5, 0.5] range
                        offset = max(-0.5, min(0.5, offset))

                        # Apply a small positive bias to ensure peaks align with the actual hit
                        # This fixes the issue where peaks were detected slightly before the hit
                        offset_with_bias = offset + 0.05  # Add a small delay to align with actual hit
                        offset_with_bias = max(-0.5, min(0.5, offset_with_bias))

                        # Calculate final sub-sample time
                        return base_time + offset_with_bias / self.sample_rate

            # If interpolation isn't applicable, return the true peak time
            return base_time
        else:
            # The original peak was correct, but still apply quadratic interpolation
            prev_sample = abs(signal[sample_index - 1])
            peak_sample = abs(signal[sample_index])
            next_sample = abs(signal[sample_index + 1])

            # Only interpolate if this is truly a local maximum
            if peak_sample > prev_sample and peak_sample > next_sample:
                # Parabolic interpolation
                denominator = prev_sample - 2 * peak_sample + next_sample

                # Avoid division by zero or unstable interpolation
                if abs(denominator) > 1e-6:
                    offset = 0.5 * (prev_sample - next_sample) / denominator

                    # Limit offset to [-0.5, 0.5] range
                    offset = max(-0.5, min(0.5, offset))

                    # Apply a small positive bias to ensure peaks align with the actual hit
                    offset_with_bias = offset + 0.05  # Add a small delay to align with actual hit
                    offset_with_bias = max(-0.5, min(0.5, offset_with_bias))

                    # Calculate sub-sample time
                    return time + offset_with_bias / self.sample_rate

            # If interpolation isn't applicable, return the original time
            return time

    def _estimate_peak_snr(self, peak: Dict[str, Any], signal: np.ndarray) -> float:
        """
        Estimate signal-to-noise ratio for a peak.

        Args:
            peak: Peak dictionary
            signal: Input signal

        Returns:
            SNR estimate
        """
        time = peak['time']
        sample_index = int(time * self.sample_rate)

        # Check bounds
        if sample_index < 100 or sample_index >= len(signal) - 100:
            return 1.0

        # Get peak amplitude
        peak_amplitude = abs(signal[sample_index])

        # Get surrounding signal for noise estimate
        # Use two windows before and after the peak, skipping the immediate vicinity
        pre_window = signal[sample_index - 100:sample_index - 20]
        post_window = signal[sample_index + 20:sample_index + 100]

        # Calculate noise level as RMS of surrounding signal
        if len(pre_window) > 0 and len(post_window) > 0:
            noise_level = np.sqrt(np.mean(np.concatenate([pre_window ** 2, post_window ** 2])))
        elif len(pre_window) > 0:
            noise_level = np.sqrt(np.mean(pre_window ** 2))
        elif len(post_window) > 0:
            noise_level = np.sqrt(np.mean(post_window ** 2))
        else:
            noise_level = 0.01  # Default if windows are empty

        # Avoid division by zero
        if noise_level < 1e-6:
            noise_level = 1e-6

        # Calculate SNR
        snr = peak_amplitude / noise_level

        return float(snr)

    def _calculate_peak_spectral_centroid(self, peak: Dict[str, Any], signal: np.ndarray) -> float:
        """
        Calculate spectral centroid at peak time.

        Args:
            peak: Peak dictionary
            signal: Input signal

        Returns:
            Spectral centroid in Hz
        """
        if not LIBROSA_AVAILABLE:
            return 0.0

        time = peak['time']
        sample_index = int(time * self.sample_rate)

        # Check bounds
        if sample_index < 1024 or sample_index >= len(signal) - 1024:
            return 0.0

        # Extract a window around the peak
        window = signal[sample_index - 1024:sample_index + 1024]

        # Calculate spectral centroid
        try:
            centroid = librosa.feature.spectral_centroid(y=window, sr=self.sample_rate)[0]
            return float(np.mean(centroid))
        except Exception as e:
            logger.warning(f"Error calculating spectral centroid: {e}")
            return 0.0

    def _is_genuine_transient_enhanced(self, signal: np.ndarray, peak_time: float) -> bool:
        """
        Enhanced check for genuine transients with advanced drum-specific frequency domain analysis.

        Args:
            signal: Input signal
            peak_time: Peak time in seconds

        Returns:
            True if the peak is a genuine drum transient
        """
        if not SCIPY_AVAILABLE:
            return self._is_genuine_transient(signal, peak_time)

        sample_index = int(peak_time * self.sample_rate)

        # Check bounds with expanded window for better analysis
        window_size = 200  # Increased from 100 to 200 samples
        if sample_index < window_size or sample_index >= len(signal) - window_size:
            return False  # Be conservative near boundaries

        # Extract windows before and after peak with larger windows for better frequency resolution
        pre_window = signal[sample_index - window_size:sample_index]
        post_window = signal[sample_index:sample_index + window_size]

        # Calculate energy increase
        pre_energy = np.sum(pre_window ** 2) if len(pre_window) > 0 else 0.0
        post_energy = np.sum(post_window ** 2) if len(post_window) > 0 else 0.0

        if pre_energy < 1e-10:
            pre_energy = 1e-10  # Avoid division by zero

        energy_ratio = post_energy / pre_energy

        # Advanced frequency-domain analysis
        if len(pre_window) >= 128 and len(post_window) >= 128:
            # Use a larger FFT size for better frequency resolution
            fft_size = 512  # Increased for better frequency resolution
            pre_spec = np.abs(np.fft.rfft(pre_window * np.hanning(len(pre_window)), n=fft_size))
            post_spec = np.abs(np.fft.rfft(post_window * np.hanning(len(post_window)), n=fft_size))

            # Frequency bins
            freqs = np.linspace(0, self.sample_rate / 2, len(pre_spec))

            # Normalize spectra
            if np.sum(pre_spec) > 0:
                pre_spec = pre_spec / np.sum(pre_spec)
            if np.sum(post_spec) > 0:
                post_spec = post_spec / np.sum(post_spec)

            # Calculate overall spectral difference
            spec_diff = np.sum(np.abs(post_spec - pre_spec))

            # Define frequency bands specific to drum components
            bands = {
                'sub_bass': (20, 60),  # Sub-bass frequencies (kick drum fundamentals)
                'bass': (60, 200),  # Bass frequencies (kick drum body)
                'low_mid': (200, 500),  # Low-mids (snare fundamentals, tom fundamentals)
                'mid': (500, 2000),  # Mids (snare body, tom body)
                'high_mid': (2000, 5000),  # High-mids (snare crack, hi-hat)
                'high': (5000, 10000),  # Highs (hi-hat, cymbal)
                'very_high': (10000, 20000)  # Very highs (cymbal shimmer)
            }

            # Calculate spectral differences in each band
            band_diffs = {}
            band_energy_ratios = {}

            for band_name, (low_freq, high_freq) in bands.items():
                # Find indices corresponding to this frequency band
                band_indices = np.where((freqs >= low_freq) & (freqs <= high_freq))[0]

                if len(band_indices) > 0:
                    # Calculate spectral difference in this band
                    band_pre_spec = pre_spec[band_indices]
                    band_post_spec = post_spec[band_indices]

                    # Normalize if needed
                    if np.sum(band_pre_spec) > 0:
                        band_pre_spec = band_pre_spec / np.sum(band_pre_spec)
                    if np.sum(band_post_spec) > 0:
                        band_post_spec = band_post_spec / np.sum(band_post_spec)

                    # Calculate difference
                    band_diff = np.sum(np.abs(band_post_spec - band_pre_spec))
                    band_diffs[band_name] = band_diff

                    # Calculate energy ratio in this band
                    band_pre_energy = np.sum(pre_spec[band_indices] ** 2) if len(pre_spec[band_indices]) > 0 else 0.0
                    band_post_energy = np.sum(post_spec[band_indices] ** 2) if len(post_spec[band_indices]) > 0 else 0.0

                    if band_pre_energy > 0:
                        band_energy_ratios[band_name] = band_post_energy / band_pre_energy
                    else:
                        band_energy_ratios[band_name] = 1.0
                else:
                    band_diffs[band_name] = 0
                    band_energy_ratios[band_name] = 1.0

            # Calculate spectral centroid change
            if np.sum(pre_spec) > 0 and np.sum(post_spec) > 0:
                pre_centroid = np.sum(freqs * pre_spec) / np.sum(pre_spec)
                post_centroid = np.sum(freqs * post_spec) / np.sum(post_spec)
                centroid_change = abs(post_centroid - pre_centroid) / (self.sample_rate / 4)
            else:
                centroid_change = 0

            # Calculate spectral flux (sum of positive changes)
            spectral_flux = np.sum(np.maximum(0, post_spec - pre_spec))

            # Calculate spectral flatness (measure of noise vs. tonal content)
            if np.prod(post_spec + 1e-10) > 0:
                post_flatness = np.exp(np.mean(np.log(post_spec + 1e-10))) / (np.mean(post_spec) + 1e-10)
            else:
                post_flatness = 0
        else:
            spec_diff = 0
            centroid_change = 0
            spectral_flux = 0
            post_flatness = 0
            band_diffs = {band: 0 for band in ['sub_bass', 'bass', 'low_mid', 'mid', 'high_mid', 'high', 'very_high']}
            band_energy_ratios = {band: 1.0 for band in
                                  ['sub_bass', 'bass', 'low_mid', 'mid', 'high_mid', 'high', 'very_high']}

        # Check for sudden amplitude increase - key characteristic of drum hits
        amp_increase = np.max(np.abs(post_window[:20])) - np.max(np.abs(pre_window[-20:]))

        # Check for rapid decay after onset - typical for drum hits
        if len(post_window) >= 100:  # Increased window size
            initial_amp = np.max(np.abs(post_window[:20]))  # Increased from 10 to 20
            later_amp = np.max(np.abs(post_window[80:100]))  # Adjusted for larger window
            if initial_amp > 0:
                decay_ratio = later_amp / initial_amp
            else:
                decay_ratio = 1.0
        else:
            decay_ratio = 1.0

        # Analyze attack time - drums have very fast attacks
        if len(post_window) >= 50:
            # Find the peak amplitude position in the post window
            peak_pos = np.argmax(np.abs(post_window[:50]))
            # Normalize by window size - lower values mean faster attacks
            attack_time = peak_pos / 50.0
        else:
            attack_time = 0.5  # Default value

        # Drum-specific detection criteria using frequency band analysis

        # Kick drum criteria
        is_kick = (
                (band_energy_ratios.get('sub_bass', 0) > 2.5 or band_energy_ratios.get('bass', 0) > 2.5) and
                (band_diffs.get('sub_bass', 0) > 0.4 or band_diffs.get('bass', 0) > 0.4) and
                (decay_ratio < 0.7) and
                (attack_time < 0.3)
        )

        # Snare drum criteria
        is_snare = (
                (band_energy_ratios.get('low_mid', 0) > 2.0 or band_energy_ratios.get('mid', 0) > 2.0) and
                (band_diffs.get('mid', 0) > 0.5) and
                (band_diffs.get('high_mid', 0) > 0.4) and
                (decay_ratio < 0.8) and
                (attack_time < 0.25)
        )

        # Hi-hat criteria
        is_hihat = (
                (band_energy_ratios.get('high_mid', 0) > 1.8 or band_energy_ratios.get('high', 0) > 1.8) and
                (band_diffs.get('high', 0) > 0.6 or band_diffs.get('very_high', 0) > 0.6) and
                (post_flatness > 0.3)  # Hi-hats have more noise-like spectrum
        )

        # General drum transient criteria - more stringent to filter out non-drum sounds
        is_drum_transient = (
                (energy_ratio > 2.2) and  # Increased from 2.0 to 2.2
                (amp_increase > 0.18) and  # Increased from 0.15 to 0.18
                (spec_diff > 0.65 or centroid_change > 0.25) and  # Increased thresholds
                (decay_ratio < 0.75) and  # More strict decay requirement
                (attack_time < 0.4) and  # Fast attack time
                (spectral_flux > 0.3)  # Significant spectral flux
        )

        # Alternative criteria for softer drum hits
        is_soft_drum = (
                (energy_ratio > 1.8) and  # Increased from 1.7
                (amp_increase > 0.1) and  # Increased from 0.08
                (spec_diff > 0.7) and
                (centroid_change > 0.3) and
                (spectral_flux > 0.2)
        )

        # Return true if any of the specific drum criteria or general criteria are met
        return is_kick or is_snare or is_hihat or is_drum_transient or is_soft_drum

    def _is_genuine_transient(self, signal: np.ndarray, peak_time: float) -> bool:
        """
        Simple but effective check for genuine drum transients.

        Args:
            signal: Input signal
            peak_time: Peak time in seconds

        Returns:
            True if the peak is likely a genuine drum transient
        """
        if not SCIPY_AVAILABLE:
            return True

        sample_index = int(peak_time * self.sample_rate)

        # Check bounds
        if sample_index < 100 or sample_index >= len(signal) - 100:
            return False  # Be conservative near boundaries

        # Extract windows before and after peak
        pre_window = signal[sample_index - 100:sample_index]
        post_window = signal[sample_index:sample_index + 100]

        # Calculate energy increase
        pre_energy = np.sum(pre_window ** 2) if len(pre_window) > 0 else 0.0
        post_energy = np.sum(post_window ** 2) if len(post_window) > 0 else 0.0

        if pre_energy < 1e-10:
            pre_energy = 1e-10  # Avoid division by zero

        energy_ratio = post_energy / pre_energy

        # Check for sudden amplitude increase
        amp_increase = np.max(np.abs(post_window[:20])) - np.max(np.abs(pre_window[-20:]))

        # Check for rapid decay after onset
        if len(post_window) >= 50:
            initial_amp = np.max(np.abs(post_window[:10]))
            later_amp = np.max(np.abs(post_window[40:50]))
            if initial_amp > 0:
                decay_ratio = later_amp / initial_amp
            else:
                decay_ratio = 1.0
        else:
            decay_ratio = 1.0

        # Simple but effective criteria for drum transients
        is_transient = (
                (energy_ratio > 2.0) and  # Significant energy increase
                (amp_increase > 0.15) and  # Significant amplitude increase
                (decay_ratio < 0.8)  # Some decay after onset
        )

        return is_transient

    def _classify_drum_hits(self, peaks: List[Dict[str, Any]], signal: np.ndarray) -> List[Dict[str, Any]]:
        """
        Classify drum hits with enhanced accuracy and contextual awareness.

        Args:
            peaks: List of peaks
            signal: Input signal

        Returns:
            List of classified peaks
        """
        if len(peaks) == 0 or self.drum_classifier is None:
            return peaks

        # Sort peaks by time for sequential processing
        sorted_peaks = sorted(peaks, key=lambda x: x['time'])

        # Extract peak times
        peak_times = [p['time'] for p in sorted_peaks]

        # Classify with context
        classifications = self.drum_classifier.classify_with_context(signal, self.sample_rate, peak_times)

        # Update peaks with classifications
        classified_peaks = []

        # First pass: Apply initial classifications
        for peak, (drum_type, confidence) in zip(sorted_peaks, classifications):
            # Create a copy of the peak
            classified_peak = peak.copy()

            # Update with classification
            classified_peak['type'] = drum_type
            classified_peak['drum_confidence'] = confidence

            # Adjust overall confidence based on classification confidence
            # Give more weight to the classification confidence for more accurate results
            classified_peak['confidence'] = 0.6 * peak['confidence'] + 0.4 * confidence

            classified_peaks.append(classified_peak)

        # Second pass: Apply rhythm pattern analysis for better classification
        if len(classified_peaks) >= 4:
            # Analyze for common drum patterns
            for i in range(1, len(classified_peaks) - 1):
                current_peak = classified_peaks[i]
                prev_peak = classified_peaks[i - 1]
                next_peak = classified_peaks[i + 1]

                # Calculate time differences
                prev_diff = current_peak['time'] - prev_peak['time']
                next_diff = next_peak['time'] - current_peak['time']

                # Pattern: Regular hi-hat pattern
                if current_peak['type'] == 'hi-hat':
                    # Check if this hi-hat is part of a regular pattern
                    if i >= 2 and i < len(classified_peaks) - 2:
                        prev_prev_peak = classified_peaks[i - 2]
                        next_next_peak = classified_peaks[i + 2]

                        if (prev_prev_peak['type'] == 'hi-hat' and next_next_peak['type'] == 'hi-hat' and
                                abs((current_peak['time'] - prev_prev_peak['time']) -
                                    (next_next_peak['time'] - current_peak['time'])) < 0.05):
                            # This is likely part of a regular hi-hat pattern
                            current_peak['confidence'] = min(0.95, current_peak['confidence'] * 1.15)
                            current_peak['pattern_match'] = 'regular_hihat'

                # Pattern: Kick-snare alternation
                if i >= 1 and i < len(classified_peaks) - 2:
                    if (current_peak['type'] == 'kick' and next_peak['type'] == 'snare' or
                            current_peak['type'] == 'snare' and next_peak['type'] == 'kick'):
                        # This is likely part of a kick-snare pattern
                        current_peak['confidence'] = min(0.95, current_peak['confidence'] * 1.1)
                        next_peak['confidence'] = min(0.95, next_peak['confidence'] * 1.1)
                        current_peak['pattern_match'] = 'kick_snare'
                        next_peak['pattern_match'] = 'kick_snare'

                # Pattern: Kick on strong beats
                if current_peak['type'] == 'kick':
                    # Check if this kick is on a strong beat (regular spacing)
                    if i >= 3:
                        # Look for previous kicks
                        prev_kicks = [j for j in range(i - 3, i) if classified_peaks[j]['type'] == 'kick']
                        if prev_kicks:
                            # Calculate average spacing between kicks
                            kick_spacings = [current_peak['time'] - classified_peaks[j]['time'] for j in prev_kicks]
                            if kick_spacings:
                                avg_spacing = sum(kick_spacings) / len(kick_spacings)
                                # Check if any spacing is close to a multiple of the average
                                for spacing in kick_spacings:
                                    ratio = spacing / avg_spacing
                                    if abs(ratio - round(ratio)) < 0.15:  # Within 15% of a multiple
                                        current_peak['confidence'] = min(0.95, current_peak['confidence'] * 1.1)
                                        current_peak['pattern_match'] = 'regular_kick'
                                        break

                # Resolve ambiguous classifications based on context
                if current_peak['drum_confidence'] < 0.6:  # Low confidence classification
                    # Check surrounding peaks for context
                    surrounding_types = [prev_peak['type'], next_peak['type']]

                    # If surrounded by the same type, likely the same
                    if prev_peak['type'] == next_peak['type'] and prev_peak['drum_confidence'] > 0.7:
                        current_peak['type'] = prev_peak['type']
                        current_peak['confidence'] = min(0.9, current_peak['confidence'] * 1.05)
                        current_peak['context_corrected'] = True

                    # If this is classified as tom but surrounded by kicks/snares, might be misclassified
                    if current_peak['type'] == 'tom' and 'kick' in surrounding_types and 'snare' in surrounding_types:
                        # Re-classify based on spectral centroid
                        sample_index = int(current_peak['time'] * self.sample_rate)
                        if 0 <= sample_index < len(signal) - 1024:
                            segment = signal[sample_index:sample_index + 1024]
                            if LIBROSA_AVAILABLE:
                                centroid = librosa.feature.spectral_centroid(y=segment, sr=self.sample_rate)[0]
                                if np.mean(centroid) < 500:
                                    current_peak['type'] = 'kick'
                                else:
                                    current_peak['type'] = 'snare'
                                current_peak['context_corrected'] = True

        # Third pass: Final confidence adjustments based on transient verification
        for peak in classified_peaks:
            # Boost confidence for verified transients
            if peak.get('transient_verified', False):
                peak['confidence'] = min(0.95, peak['confidence'] * 1.1)

            # Penalize confidence for peaks that don't match their expected spectral profile
            if 'type' in peak and peak['type'] != 'generic':
                if peak['type'] == 'kick' and peak.get('spectral_centroid', 0) > 1000:
                    peak['confidence'] *= 0.9  # Penalize high-frequency kicks
                elif peak['type'] == 'hi-hat' and peak.get('spectral_centroid', 0) < 2000:
                    peak['confidence'] *= 0.9  # Penalize low-frequency hi-hats

            # Final minimum confidence threshold
            if peak['confidence'] < 0.4:
                peak['type'] = 'generic'  # Reset to generic if confidence is too low

        return classified_peaks

    def _filter_by_amplitude_segments(self, peaks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter peaks by amplitude segments with improved accuracy.

        Args:
            peaks: List of peaks

        Returns:
            List of filtered peaks
        """
        if len(peaks) == 0 or self.waveform_data is None or len(self.waveform_data) == 0:
            return peaks

        print(f"   🔍 Starting amplitude segment filtering with {len(peaks)} peaks")

        # Analyze amplitude segments
        segments = self.amplitude_analyzer.analyze_amplitude_segments(self.waveform_data[0], self.sample_rate)

        # Get the signal for additional analysis
        signal = self.waveform_data[0]

        # Filter peaks based on segments with more nuanced approach
        filtered_peaks = []

        # Calculate global peak prominence to identify obvious peaks
        # This helps ensure we don't miss prominent peaks in the waveform
        peak_times = [p['time'] for p in peaks]
        peak_amplitudes = []

        # Get amplitude values at peak times
        for time in peak_times:
            sample_index = int(time * self.sample_rate)
            if 0 <= sample_index < len(signal):
                # Get a window around the peak for more accurate amplitude measurement
                window_start = max(0, sample_index - 256)
                window_end = min(len(signal), sample_index + 256)
                window = signal[window_start:window_end]
                if len(window) > 0:
                    peak_amplitudes.append(np.max(np.abs(window)))
                else:
                    peak_amplitudes.append(0.0)
            else:
                peak_amplitudes.append(0.0)

        # Calculate amplitude statistics for prominence analysis
        if peak_amplitudes:
            median_amplitude = np.median(peak_amplitudes)
            max_amplitude = np.max(peak_amplitudes)
            amplitude_threshold = max(0.3, median_amplitude * 1.5)  # Dynamic threshold

            # Calculate prominence threshold (peaks significantly above median)
            prominence_threshold = max(0.5, median_amplitude * 2.0)

            print(
                f"   ℹ️ Amplitude analysis: median={median_amplitude:.3f}, max={max_amplitude:.3f}, threshold={amplitude_threshold:.3f}")
        else:
            amplitude_threshold = 0.3
            prominence_threshold = 0.5

        for i, peak in enumerate(peaks):
            # Get segment at peak time
            segment_type = self.amplitude_analyzer.get_segment_at_time(peak['time'])

            # Create a copy of the peak with segment info
            peak_copy = peak.copy()
            peak_copy['segment_type'] = segment_type

            # Check if this peak has been verified as a transient
            is_verified_transient = peak.get('transient_verified', False)

            # Get the peak's drum type if available
            drum_type = peak.get('type', 'generic')

            # Calculate local signal characteristics around the peak
            sample_index = int(peak['time'] * self.sample_rate)
            local_energy = 0
            local_max = 0

            if 0 <= sample_index < len(signal):
                # Get a window around the peak
                window_start = max(0, sample_index - 512)
                window_end = min(len(signal), sample_index + 512)
                window = signal[window_start:window_end]

                if len(window) > 0:
                    # Calculate local energy and max amplitude
                    local_energy = np.sum(window ** 2) / len(window) if len(window) > 0 else 0.0
                    local_max = np.max(np.abs(window))

                    # Store amplitude in peak for later use
                    peak_copy['amplitude'] = local_max

            # Get peak prominence if available
            peak_prominence = 0.0
            if i < len(peak_amplitudes):
                peak_prominence = peak_amplitudes[i]
                peak_copy['prominence'] = peak_prominence

            # Decision logic based on multiple factors
            keep_peak = False

            # CRITICAL: Always keep peaks with high prominence
            # This ensures we don't miss obvious peaks in the waveform
            if peak_prominence >= prominence_threshold:
                keep_peak = True
                peak_copy['confidence'] = min(0.98, peak_copy.get('confidence', 0.8) * 1.2)
                peak_copy['rescued'] = True  # Mark as rescued for debugging

            # Very high amplitude segments are very likely to be drum hits
            elif segment_type == 'very_high':
                if is_verified_transient or peak['confidence'] > 0.4:  # Lowered threshold
                    keep_peak = True
                    peak_copy['confidence'] = min(0.95, peak_copy.get('confidence', 0.8) * 1.1)

            # High amplitude segments are likely drum hits
            elif segment_type == 'high':
                if is_verified_transient or peak['confidence'] > 0.5:  # Lowered threshold
                    keep_peak = True
                    peak_copy['confidence'] = min(0.9, peak_copy.get('confidence', 0.8) * 1.05)

            # Medium segments might contain softer drum hits
            elif segment_type == 'medium':
                # For medium segments, be more selective but still reasonable
                if is_verified_transient and peak['confidence'] > 0.6:  # Lowered threshold
                    keep_peak = True
                # Special case for hi-hats which can be softer
                elif drum_type == 'hi-hat' and peak['confidence'] > 0.65:  # Lowered threshold
                    keep_peak = True
                # Special case for cymbals which can have medium amplitude but long decay
                elif drum_type == 'cymbal' and peak['confidence'] > 0.7:  # Lowered threshold
                    keep_peak = True

            # For any segment type, keep high confidence peaks
            if peak.get('confidence', 0) > 0.8:  # Lowered threshold
                keep_peak = True

            # Additional check for local energy and amplitude
            if local_max > amplitude_threshold:
                keep_peak = True
                peak_copy['amplitude_verified'] = True

            if keep_peak:
                filtered_peaks.append(peak_copy)

        print(f"   ✅ After amplitude segment filtering: {len(filtered_peaks)} peaks")

        # Improved filtering to remove clusters of peaks that are too close together
        if len(filtered_peaks) > 1:
            # Sort by time
            sorted_peaks = sorted(filtered_peaks, key=lambda x: x['time'])

            # Calculate adaptive minimum distance based on tempo
            time_diffs = [sorted_peaks[i + 1]['time'] - sorted_peaks[i]['time'] for i in range(len(sorted_peaks) - 1)]
            if time_diffs:
                median_diff = np.median(time_diffs)
                # Use a smaller minimum distance for faster tempos
                min_distance = min(0.05, median_diff * 0.25)  # Either 50ms or 25% of median interval
            else:
                min_distance = 0.05  # Default 50ms

            print(f"   ℹ️ Using minimum peak distance of {min_distance:.3f}s")

            # Filter out peaks that are too close to each other
            filtered_clusters = [sorted_peaks[0]]

            for i in range(1, len(sorted_peaks)):
                time_diff = sorted_peaks[i]['time'] - filtered_clusters[-1]['time']

                if time_diff >= min_distance:
                    filtered_clusters.append(sorted_peaks[i])
                else:
                    # If peaks are too close, use a more sophisticated decision
                    current_peak = sorted_peaks[i]
                    last_peak = filtered_clusters[-1]

                    # Compare confidence scores
                    if current_peak['confidence'] > last_peak['confidence'] + 0.1:
                        # Current peak is significantly more confident
                        filtered_clusters[-1] = current_peak
                    elif current_peak['confidence'] > last_peak['confidence']:
                        # Current peak is slightly more confident, check other factors

                        # Check if current peak is a verified transient
                        if current_peak.get('transient_verified', False) and not last_peak.get('transient_verified',
                                                                                               False):
                            filtered_clusters[-1] = current_peak

                        # Check amplitude
                        current_amplitude = current_peak.get('amplitude', 0)
                        last_amplitude = last_peak.get('amplitude', 0)
                        if current_amplitude > last_amplitude * 1.2:  # 20% higher amplitude
                            filtered_clusters[-1] = current_peak

            print(f"   ✅ After removing clustered peaks: {len(filtered_clusters)} peaks")
            return filtered_clusters
        else:
            return filtered_peaks

    def _validate_and_sort_peaks(self, peaks: List[Dict[str, Any]]) -> List[Peak]:
        """
        Validate and sort peaks, converting to Peak objects with professional accuracy.

        This method implements a sophisticated validation pipeline that:
        1. Applies adaptive confidence thresholds
        2. Performs rhythm analysis and pattern recognition
        3. Validates peaks against musical structure
        4. Handles large datasets efficiently
        5. Preserves important peaks even in complex patterns
        6. Ensures prominent amplitude peaks are never filtered out

        Args:
            peaks: List of peak dictionaries

        Returns:
            List of validated and sorted Peak objects
        """
        if len(peaks) == 0:
            return []

        print(f"   🔍 Starting final validation with {len(peaks)} peaks")

        # For very large datasets, use a more efficient approach
        is_large_dataset = len(peaks) > 1000

        # First, identify peaks with high prominence/amplitude that should always be kept
        # This ensures we don't miss obvious peaks in the waveform
        high_prominence_peaks = []
        standard_peaks = []

        # Calculate amplitude statistics for all peaks
        amplitudes = [p.get('amplitude', 0.0) for p in peaks]
        if amplitudes:
            median_amplitude = np.median(amplitudes)
            max_amplitude = np.max(amplitudes)
            # Dynamic threshold based on signal characteristics
            prominence_threshold = max(0.5, median_amplitude * 2.0)
            print(
                f"   ℹ️ Amplitude stats: median={median_amplitude:.3f}, max={max_amplitude:.3f}, prominence threshold={prominence_threshold:.3f}")
        else:
            prominence_threshold = 0.5

        # Separate peaks into high prominence and standard categories
        for p in peaks:
            # Check if this peak has high amplitude or was marked as rescued
            if (p.get('amplitude', 0.0) >= prominence_threshold or
                    p.get('rescued', False) or
                    p.get('amplitude_verified', False)):
                # Boost confidence for high prominence peaks
                p_copy = p.copy()
                p_copy['confidence'] = min(0.98, p.get('confidence', 0.8) * 1.1)
                p_copy['high_prominence'] = True
                high_prominence_peaks.append(p_copy)
            else:
                standard_peaks.append(p)

        # Apply adaptive confidence threshold based on dataset size
        if is_large_dataset:
            # For large datasets, use a slightly higher threshold
            final_confidence_threshold = 0.60  # Lowered from 0.62
            logger.info(f"Large dataset detected ({len(peaks)} peaks), using threshold: {final_confidence_threshold}")
        else:
            final_confidence_threshold = 0.58  # Lowered from 0.60

        # Apply the confidence threshold filter to standard peaks only
        filtered_standard_peaks = [p for p in standard_peaks if p.get('confidence', 0.0) >= final_confidence_threshold]

        # Combine high prominence peaks with filtered standard peaks
        filtered_peaks = high_prominence_peaks + filtered_standard_peaks

        # Log the results
        print(f"   ✅ After final confidence filtering: {len(filtered_peaks)} peaks")
        print(f"   ℹ️ High prominence peaks preserved: {len(high_prominence_peaks)}")

        # Sort by time for further processing
        filtered_peaks = sorted(filtered_peaks, key=lambda p: p.get('time', 0.0))

        # For empty or very small datasets, skip further filtering
        if len(filtered_peaks) <= 3:
            print("   ℹ️ Too few peaks for rhythm analysis, skipping")
            time_sorted = sorted(filtered_peaks, key=lambda p: p['time'])
        else:
            # Sort by time for temporal analysis
            time_sorted = sorted(filtered_peaks, key=lambda p: p['time'])

            # Calculate time differences between consecutive peaks
            time_diffs = [time_sorted[i + 1]['time'] - time_sorted[i]['time'] for i in range(len(time_sorted) - 1)]

            if time_diffs:
                # Find the median time difference
                median_diff = np.median(time_diffs)

                # Advanced tempo detection
                # Use histogram analysis to find the most common intervals
                if len(time_diffs) > 10:
                    try:
                        # Create histogram of time differences
                        hist, bin_edges = np.histogram(time_diffs, bins=50)
                        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

                        # Find the most common interval
                        most_common_idx = np.argmax(hist)
                        most_common_interval = bin_centers[most_common_idx]

                        # Refine with nearby values for better accuracy
                        common_intervals = []
                        for i, count in enumerate(hist):
                            if count > max(1, hist[most_common_idx] * 0.5):
                                common_intervals.append(bin_centers[i])

                        # Calculate average of common intervals
                        if common_intervals:
                            refined_interval = np.mean(common_intervals)
                        else:
                            refined_interval = most_common_interval

                        # Use this as our beat duration estimate
                        beat_duration = refined_interval
                    except Exception as e:
                        logger.warning(f"Error in histogram analysis: {e}, falling back to median")
                        beat_duration = median_diff
                else:
                    # For small datasets, use simpler approach
                    # Try to detect tempo and rhythmic patterns
                    # Common beat divisions in music: quarter notes, eighth notes, sixteenth notes
                    possible_beat_divisions = [1.0, 0.5, 0.25]

                    # Estimate beat duration (in seconds)
                    beat_duration_candidates = []
                    for division in possible_beat_divisions:
                        beat_duration_candidates.append(median_diff / division)

                    # Find the most likely beat duration (between 0.3s and 1.0s, or 60-200 BPM)
                    beat_duration = median_diff  # Default to median
                    for candidate in beat_duration_candidates:
                        if 0.3 <= candidate <= 1.0:
                            beat_duration = candidate
                            break

                # Calculate tempo in BPM
                if beat_duration > 0:
                    estimated_tempo = 60.0 / beat_duration
                    print(f"   ℹ️ Estimated tempo: {estimated_tempo:.1f} BPM (beat duration: {beat_duration:.3f}s)")
                else:
                    estimated_tempo = 120.0  # Default fallback
                    beat_duration = 0.5
                    print(f"   ⚠️ Could not estimate tempo, using default: {estimated_tempo} BPM")

                # Store tempo information for later use
                self._estimated_tempo = estimated_tempo
                self._beat_duration = beat_duration

                # Identify peaks that fit into the rhythmic grid
                rhythm_filtered = []

                # For large datasets, use a more efficient approach
                if is_large_dataset:
                    # Process in chunks to avoid memory issues
                    chunk_size = 500
                    for chunk_start in range(0, len(time_sorted), chunk_size):
                        chunk_end = min(chunk_start + chunk_size, len(time_sorted))
                        chunk = time_sorted[chunk_start:chunk_end]

                        # Process this chunk
                        for i, peak in enumerate(chunk):
                            # Get global index for neighbor lookups
                            global_idx = chunk_start + i

                            # Default to keeping the peak
                            keep_peak = True

                            # CRITICAL: Always keep high prominence peaks regardless of rhythm
                            if peak.get('high_prominence', False) or peak.get('rescued', False) or peak.get(
                                    'amplitude_verified', False):
                                keep_peak = True
                                # Skip further checks - we always want to keep these peaks
                            else:
                                # For peaks in the middle of the sequence
                                if global_idx > 0 and global_idx < len(time_sorted) - 1:
                                    prev_peak = time_sorted[global_idx - 1]
                                    next_peak = time_sorted[global_idx + 1]

                                    prev_diff = peak['time'] - prev_peak['time']
                                    next_diff = next_peak['time'] - peak['time']

                                    # Check if this peak fits the rhythmic grid
                                    # Calculate how close this peak is to a beat division
                                    beat_position = (peak['time'] % beat_duration) / beat_duration
                                    grid_fit = min(beat_position, 1.0 - beat_position)

                                    # If peak is far from the grid and isolated, it might be a false positive
                                    # But be less strict than before
                                    if grid_fit > 0.25 and prev_diff > 2.5 * median_diff and next_diff > 2.5 * median_diff:
                                        # Only keep if it has decent confidence or is a verified transient
                                        if peak.get('confidence', 0) < 0.75 and not peak.get('transient_verified',
                                                                                             False):
                                            keep_peak = False

                                    # If peak is very isolated (far from neighbors), be more strict but still reasonable
                                    if prev_diff > 3.5 * median_diff and next_diff > 3.5 * median_diff:
                                        # Only keep if it has good confidence
                                        if peak.get('confidence', 0) < 0.8:
                                            keep_peak = False

                            # Always keep peaks with good confidence
                            if peak.get('confidence', 0) > 0.85:  # Lowered from 0.9
                                keep_peak = True

                            # Always keep verified transients with decent confidence
                            if peak.get('transient_verified', False) and peak.get('confidence',
                                                                                  0) > 0.7:  # Lowered from 0.75
                                keep_peak = True

                            # Always keep peaks with moderate amplitude
                            if peak.get('amplitude', 0) > 0.6:  # Lowered from 0.8
                                keep_peak = True

                            # Always keep peaks in high or very high segments
                            if peak.get('segment_type') in ['high', 'very_high']:
                                keep_peak = True

                            if keep_peak:
                                rhythm_filtered.append(peak)
                else:
                    # For smaller datasets, use the enhanced approach
                    for i, peak in enumerate(time_sorted):
                        # Default to keeping the peak
                        keep_peak = True

                        # CRITICAL: Always keep high prominence peaks regardless of rhythm
                        if peak.get('high_prominence', False) or peak.get('rescued', False) or peak.get(
                                'amplitude_verified', False):
                            keep_peak = True
                            # Skip further checks - we always want to keep these peaks
                        else:
                            # For peaks in the middle of the sequence
                            if i > 0 and i < len(time_sorted) - 1:
                                prev_diff = peak['time'] - time_sorted[i - 1]['time']
                                next_diff = time_sorted[i + 1]['time'] - peak['time']

                                # Check if this peak fits the rhythmic grid
                                # Calculate how close this peak is to a beat division
                                beat_position = (peak['time'] % beat_duration) / beat_duration
                                grid_fit = min(beat_position, 1.0 - beat_position)

                                # If peak is far from the grid and isolated, it might be a false positive
                                # But be less strict than before
                                if grid_fit > 0.25 and prev_diff > 2.5 * median_diff and next_diff > 2.5 * median_diff:
                                    # Only keep if it has decent confidence or is a verified transient
                                    if peak.get('confidence', 0) < 0.75 and not peak.get('transient_verified', False):
                                        keep_peak = False

                                # If peak is very isolated (far from neighbors), be more strict but still reasonable
                                if prev_diff > 3.5 * median_diff and next_diff > 3.5 * median_diff:
                                    # Only keep if it has good confidence
                                    if peak.get('confidence', 0) < 0.8:
                                        keep_peak = False

                        # Always keep peaks with good confidence
                        if peak.get('confidence', 0) > 0.85:  # Lowered from 0.9
                            keep_peak = True

                        # Always keep verified transients with decent confidence
                        if peak.get('transient_verified', False) and peak.get('confidence',
                                                                              0) > 0.7:  # Lowered from 0.75
                            keep_peak = True

                        # Always keep peaks with moderate amplitude
                        if peak.get('amplitude', 0) > 0.6:  # Added this check
                            keep_peak = True

                        # Always keep peaks in high or very high segments
                        if peak.get('segment_type') in ['high', 'very_high']:
                            keep_peak = True

                        if keep_peak:
                            rhythm_filtered.append(peak)

                filtered_peaks = rhythm_filtered
                print(f"   ✅ After rhythm filtering: {len(filtered_peaks)} peaks")

        # Convert to Peak objects with professional error handling
        peak_objects = []
        conversion_errors = 0

        for p in filtered_peaks:
            try:
                # Use precise time if available, with additional timing refinement
                # This ensures peaks align exactly with the actual drum hits
                time = p.get('precise_time', p['time'])

                # Apply a small timing adjustment to ensure peaks align with actual drum hits
                # This compensates for any detection algorithms that trigger slightly early
                timing_adjustment = 0.005  # 5ms adjustment for perfect alignment
                adjusted_time = time + timing_adjustment

                # Get amplitude with validation
                amplitude = p.get('amplitude', 1.0)
                if not isinstance(amplitude, (int, float)) or not np.isfinite(amplitude):
                    amplitude = 1.0  # Default if invalid

                # Get confidence with validation
                confidence = p.get('confidence', 0.8)
                if not isinstance(confidence, (int, float)) or not np.isfinite(confidence):
                    confidence = 0.8  # Default if invalid

                # Get type with validation
                peak_type = p.get('type', 'generic')
                if not isinstance(peak_type, str) or peak_type not in ['generic', 'kick', 'snare', 'hi-hat', 'cymbal',
                                                                       'tom']:
                    peak_type = 'generic'  # Default if invalid

                # Estimate frequency based on drum type
                estimated_frequency = 0.0
                if peak_type == 'kick':
                    estimated_frequency = 60.0  # Low frequency for kick drums
                elif peak_type == 'snare':
                    estimated_frequency = 250.0  # Mid frequency for snare drums
                elif peak_type == 'hi-hat':
                    estimated_frequency = 5000.0  # High frequency for hi-hats
                elif peak_type == 'cymbal':
                    estimated_frequency = 8000.0  # Very high frequency for cymbals
                elif peak_type == 'tom':
                    estimated_frequency = 150.0  # Low-mid frequency for toms

                # Get segment type if available
                segment_type = p.get('segment_type', 'medium')  # Default to 'medium' if not specified

                # Extract spectral features if available
                spectral_features = {}
                if 'spectral_centroid' in p:
                    spectral_features['centroid'] = p['spectral_centroid']
                if 'spectral_bandwidth' in p:
                    spectral_features['bandwidth'] = p['spectral_bandwidth']
                if 'spectral_contrast' in p:
                    spectral_features['contrast'] = p['spectral_contrast']
                if 'spectral_rolloff' in p:
                    spectral_features['rolloff'] = p['spectral_rolloff']
                if 'zero_crossing_rate' in p:
                    spectral_features['zero_crossing_rate'] = p['zero_crossing_rate']

                # Create Peak object with frequency, segment and adjusted timing
                peak = Peak(
                    time=adjusted_time,  # Use the adjusted time for perfect alignment
                    amplitude=amplitude,
                    confidence=confidence,
                    type=peak_type,
                    frequency=estimated_frequency,
                    segment=segment_type
                )

                # Set spectral features if available
                if spectral_features:
                    peak.set_spectral_features(spectral_features)

                peak_objects.append(peak)
            except Exception as e:
                # Log error but continue processing other peaks
                logger.error(f"Error converting peak to Peak object: {e}")
                conversion_errors += 1

        if conversion_errors > 0:
            logger.warning(f"Encountered {conversion_errors} errors while converting peaks")

        # Sort by time
        sorted_peaks = sorted(peak_objects, key=lambda p: p.time)

        # Apply a final clustering to remove duplicates that are extremely close in time
        if len(sorted_peaks) > 1:
            # For large datasets, use an optimized approach
            if len(sorted_peaks) > 1000:
                # Use a more efficient algorithm for large datasets
                # This uses a sliding window approach instead of comparing all pairs
                final_peaks = []
                window_start = 0
                min_time_diff = 0.025  # 25ms minimum difference between peaks

                while window_start < len(sorted_peaks):
                    # Start with the first peak in the window
                    best_peak = sorted_peaks[window_start]
                    window_end = window_start + 1

                    # Find all peaks within min_time_diff of the first one
                    while (window_end < len(sorted_peaks) and
                           sorted_peaks[window_end].time - best_peak.time < min_time_diff):
                        # If this peak is better, make it the best peak
                        if self._is_better_peak(sorted_peaks[window_end], best_peak):
                            best_peak = sorted_peaks[window_end]
                        window_end += 1

                    # Add the best peak from this window
                    final_peaks.append(best_peak)

                    # Move to the next window
                    window_start = window_end

                sorted_peaks = final_peaks
            else:
                # For smaller datasets, use the original approach
                final_peaks = [sorted_peaks[0]]
                min_time_diff = 0.025  # 25ms minimum difference between peaks

                for i in range(1, len(sorted_peaks)):
                    time_diff = sorted_peaks[i].time - final_peaks[-1].time

                    if time_diff >= min_time_diff:
                        final_peaks.append(sorted_peaks[i])
                    else:
                        # If peaks are too close, use a more sophisticated decision
                        if self._is_better_peak(sorted_peaks[i], final_peaks[-1]):
                            final_peaks[-1] = sorted_peaks[i]

                sorted_peaks = final_peaks

            print(f"   ✅ After final clustering: {len(sorted_peaks)} peaks")

        # Final validation - ensure we don't exceed system limits
        if len(sorted_peaks) > 10000:
            logger.warning(f"Very large number of peaks detected ({len(sorted_peaks)}), limiting to 10000")
            print(f"   ⚠️ Very large number of peaks detected ({len(sorted_peaks)}), limiting to 10000")
            # Sort by confidence and take the top 10000
            sorted_peaks = sorted(sorted_peaks, key=lambda p: p.confidence, reverse=True)[:10000]
            # Re-sort by time
            sorted_peaks = sorted(sorted_peaks, key=lambda p: p.time)

        return sorted_peaks

    def _is_better_peak(self, peak1: Peak, peak2: Peak) -> bool:
        """
        Determine if peak1 is better than peak2 based on multiple factors.

        Args:
            peak1: First peak
            peak2: Second peak

        Returns:
            True if peak1 is better than peak2
        """
        # First check confidence - higher is better
        if peak1.confidence > peak2.confidence + 0.1:
            return True
        elif peak2.confidence > peak1.confidence + 0.1:
            return False

        # If confidence is similar, prefer certain drum types
        # Kick and snare are usually more important than hi-hat or cymbal
        if peak1.type in ['kick', 'snare'] and peak2.type not in ['kick', 'snare']:
            return True
        elif peak2.type in ['kick', 'snare'] and peak1.type not in ['kick', 'snare']:
            return False

        # If still tied, prefer higher amplitude
        if peak1.amplitude > peak2.amplitude * 1.2:
            return True
        elif peak2.amplitude > peak1.amplitude * 1.2:
            return False

        # If still tied, keep the earlier one
        return peak1.time < peak2.time

    def get_peak_data(self) -> List[Peak]:
        """
        Get all peak data.

        Returns:
            List of Peak objects
        """
        return self.peaks

    def get_peak_timestamps(self) -> List[float]:
        """
        Get list of peak timestamps.

        Returns:
            List of peak times in seconds
        """
        return [p.time for p in self.peaks]

    def get_peaks_with_timestamps(self) -> List[Dict[str, Any]]:
        """
        Get peaks with formatted timestamps.

        Returns:
            List of dictionaries with peak data and formatted timestamps
        """
        result = []

        for peak in self.peaks:
            peak_dict = {
                'time': peak.time,
                'timestamp': self._format_timestamp(peak.time),
                'amplitude': peak.amplitude,
                'confidence': peak.confidence,
                'type': peak.type
            }
            result.append(peak_dict)

        return result

    def _format_timestamp(self, seconds: float) -> str:
        """
        Format seconds as MM:SS.mmm timestamp.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted timestamp
        """
        minutes = int(seconds // 60)
        seconds_part = seconds % 60
        return f"{minutes:02d}:{seconds_part:06.3f}"

    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        Get summary of analysis results.

        Returns:
            Dictionary with analysis summary
        """
        return {
            'peak_count': len(self.peaks),
            'duration': self.duration_seconds,
            'sample_rate': self.sample_rate,
            'noise_floor': self.noise_floor,
            'dynamic_range': self.dynamic_range,
            'analysis_time': self.analysis_time,
            'is_analyzed': self.is_analyzed,
            'is_drum_stem': self.is_drum_stem,
            'peak_types': {
                'generic': len([p for p in self.peaks if p.type == 'generic']),
                'kick': len([p for p in self.peaks if p.type == 'kick']),
                'snare': len([p for p in self.peaks if p.type == 'snare']),
                'hi-hat': len([p for p in self.peaks if p.type == 'hi-hat']),
                'cymbal': len([p for p in self.peaks if p.type == 'cymbal']),
                'tom': len([p for p in self.peaks if p.type == 'tom'])
            }
        }

    def export_peaks_to_json(self, file_path: Union[str, Path]) -> bool:
        """
        Export peaks to JSON file.

        Args:
            file_path: Path to output JSON file

        Returns:
            True if export successful
        """
        try:
            # Convert peaks to dictionaries
            peak_dicts = [p.to_dict() for p in self.peaks]

            # Create output dictionary
            output = {
                'peaks': peak_dicts,
                'metadata': {
                    'file': str(self.file_path) if self.file_path else None,
                    'duration': self.duration_seconds,
                    'sample_rate': self.sample_rate,
                    'peak_count': len(self.peaks),
                    'is_drum_stem': self.is_drum_stem,
                    'export_time': datetime.now().isoformat()
                }
            }

            # Write to file
            with open(file_path, 'w') as f:
                json.dump(output, f, indent=2)

            return True
        except Exception as e:
            logger.error(f"Error exporting peaks to JSON: {e}")
            return False

    def is_processing_complete(self) -> bool:
        """Check if processing is complete."""
        return self.is_analyzed and not self.is_processing

    def get_comprehensive_analysis_report(self) -> Dict[str, Any]:
        """
        Get comprehensive analysis report.

        Returns:
            Dictionary with detailed analysis report
        """
        # Basic information
        report = {
            'file_info': {
                'filename': self.filename if self.file_path else None,
                'path': str(self.file_path) if self.file_path else None,
                'duration': self.duration_seconds,
                'sample_rate': self.sample_rate,
                'channels': self.channels,
                'is_drum_stem': self.is_drum_stem
            },
            'analysis_info': {
                'peak_count': len(self.peaks),
                'noise_floor': self.noise_floor,
                'dynamic_range': self.dynamic_range,
                'analysis_time': self.analysis_time,
                'is_analyzed': self.is_analyzed,
                'is_processing': self.is_processing
            },
            'peak_statistics': {
                'total': len(self.peaks),
                'by_type': {
                    'generic': len([p for p in self.peaks if p.type == 'generic']),
                    'kick': len([p for p in self.peaks if p.type == 'kick']),
                    'snare': len([p for p in self.peaks if p.type == 'snare']),
                    'hi-hat': len([p for p in self.peaks if p.type == 'hi-hat']),
                    'cymbal': len([p for p in self.peaks if p.type == 'cymbal']),
                    'tom': len([p for p in self.peaks if p.type == 'tom'])
                }
            },
            'performance': {
                'processing_times': self.processing_times,
                'total_time': self.analysis_time,
                'samples_per_second': len(self.waveform_data[
                                              0]) / self.analysis_time if self.analysis_time > 0 and self.waveform_data is not None else 0
            },
            'configuration': self.config
        }

        # Add timing statistics if peaks exist
        if len(self.peaks) > 1:
            peak_times = [p.time for p in self.peaks]
            intervals = [peak_times[i + 1] - peak_times[i] for i in range(len(peak_times) - 1)]

            report['timing_statistics'] = {
                'min_interval': min(intervals) if intervals else 0,
                'max_interval': max(intervals) if intervals else 0,
                'mean_interval': sum(intervals) / len(intervals) if intervals else 0,
                'median_interval': sorted(intervals)[len(intervals) // 2] if intervals else 0
            }

            # Try to estimate tempo
            if intervals:
                # Calculate tempo from median interval
                median_interval = sorted(intervals)[len(intervals) // 2]
                if median_interval > 0:
                    estimated_tempo = 60 / median_interval
                    # Round to nearest integer
                    estimated_tempo = round(estimated_tempo)
                    report['timing_statistics']['estimated_tempo'] = estimated_tempo

        return report

    def get_peak_timeline(self, time_resolution: float = 0.1) -> Dict[str, Any]:
        """
        Get timeline of peaks for visualization.

        Args:
            time_resolution: Time resolution in seconds

        Returns:
            Dictionary with timeline data
        """
        if len(self.peaks) == 0 or self.duration_seconds <= 0:
            return {'timeline': [], 'resolution': time_resolution}

        # Create timeline
        timeline = []
        current_time = 0

        while current_time <= self.duration_seconds:
            # Find peaks in this time window
            window_peaks = [p for p in self.peaks if current_time <= p.time < current_time + time_resolution]

            # Create timeline entry
            entry = {
                'time': current_time,
                'timestamp': self._format_timestamp(current_time),
                'peak_count': len(window_peaks),
                'peaks': [p.to_dict() for p in window_peaks]
            }

            timeline.append(entry)
            current_time += time_resolution

        return {
            'timeline': timeline,
            'resolution': time_resolution,
            'duration': self.duration_seconds
        }

    def export_enhanced_analysis(self, output_path: Union[str, Path]) -> bool:
        """
        Export enhanced analysis to JSON file.

        Args:
            output_path: Path to output JSON file

        Returns:
            True if export successful
        """
        try:
            # Get comprehensive report
            report = self.get_comprehensive_analysis_report()

            # Add peak data
            report['peaks'] = [p.to_dict() for p in self.peaks]

            # Add timeline data
            report['timeline'] = self.get_peak_timeline(0.1)['timeline']

            # Write to file
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)

            return True
        except Exception as e:
            logger.error(f"Error exporting enhanced analysis: {e}")
            return False

    def has_waveform_data(self) -> bool:
        """Check if waveform data is available."""
        return self.waveform_data is not None and len(self.waveform_data) > 0

    def get_peak_markers(self, width: int, height: int, offset: float = 0.0, zoom: float = 1.0) -> List[Dict[str, Any]]:
        """
        Get peak markers for visualization.

        Args:
            width: Width of visualization in pixels
            height: Height of visualization in pixels
            offset: Time offset in seconds
            zoom: Zoom factor

        Returns:
            List of peak marker dictionaries
        """
        if len(self.peaks) == 0 or self.duration_seconds <= 0:
            return []

        # Calculate visible time range
        visible_duration = self.duration_seconds / zoom
        start_time = offset
        end_time = offset + visible_duration

        # Find peaks in visible range
        visible_peaks = [p for p in self.peaks if start_time <= p.time <= end_time]

        # Create markers
        markers = []

        for peak in visible_peaks:
            # Calculate x position
            x_pos = int((peak.time - start_time) / visible_duration * width)

            # Create marker
            marker = {
                'x': x_pos,
                'y': height // 2,  # Center vertically
                'time': peak.time,
                'amplitude': peak.amplitude,
                'confidence': peak.confidence,
                'type': peak.type,
                'color': self._get_color_for_peak_type(peak.type)
            }

            markers.append(marker)

        return markers

    def _get_color_for_peak_type(self, peak_type: str) -> Tuple[int, int, int]:
        """
        Get color for peak type.

        Args:
            peak_type: Peak type

        Returns:
            RGB color tuple
        """
        colors = {
            'generic': (255, 255, 255),  # White
            'kick': (255, 0, 0),  # Red
            'snare': (0, 255, 0),  # Green
            'hi-hat': (0, 0, 255),  # Blue
            'cymbal': (255, 255, 0),  # Yellow
            'tom': (255, 0, 255)  # Magenta
        }

        return colors.get(peak_type, (255, 255, 255))

    def get_waveform_points(self, width: int, height: int, offset: float = 0.0, zoom: float = 1.0) -> List[
        Tuple[int, int]]:
        """
        Get waveform points for visualization.

        Args:
            width: Width of visualization in pixels
            height: Height of visualization in pixels
            offset: Time offset in seconds
            zoom: Zoom factor

        Returns:
            List of (x, y) point tuples
        """
        if self.waveform_data is None or len(self.waveform_data) == 0:
            return []

        signal = self.waveform_data[0]

        # Calculate visible sample range
        visible_duration = self.duration_seconds / zoom
        start_time = offset
        end_time = offset + visible_duration

        start_sample = int(start_time * self.sample_rate)
        end_sample = int(end_time * self.sample_rate)

        # Clamp to valid range
        start_sample = max(0, start_sample)
        end_sample = min(len(signal), end_sample)

        if start_sample >= end_sample:
            return []

        # Extract visible samples
        visible_signal = signal[start_sample:end_sample]

        # Downsample to width
        if len(visible_signal) > width * 2:
            # Calculate number of samples per pixel
            samples_per_pixel = len(visible_signal) // width

            # For each pixel, find min and max values
            points = []
            for i in range(width):
                start_idx = i * samples_per_pixel
                end_idx = min(start_idx + samples_per_pixel, len(visible_signal))

                if start_idx < end_idx:
                    chunk = visible_signal[start_idx:end_idx]
                    min_val = np.min(chunk)
                    max_val = np.max(chunk)

                    # Convert to y coordinates
                    y_min = int((1 - min_val) * height / 2)
                    y_max = int((1 - max_val) * height / 2)

                    # Add points
                    points.append((i, y_min))
                    points.append((i, y_max))

            return points
        else:
            # If we have fewer samples than pixels, interpolate
            points = []
            for i in range(width):
                # Calculate sample index
                sample_idx = int(i / width * len(visible_signal))

                if 0 <= sample_idx < len(visible_signal):
                    value = visible_signal[sample_idx]

                    # Convert to y coordinate
                    y = int((1 - value) * height / 2)

                    # Add point
                    points.append((i, y))

            return points

    def enable_visual_validation(self) -> bool:
        """
        Enable visual validation if the module is available.

        Returns:
            bool: True if visual validation was enabled, False otherwise
        """
        if not VISUAL_VALIDATOR_AVAILABLE:
            logger.warning("Cannot enable visual validation: module not available")
            return False

        self.config['use_visual_validation'] = True

        if self.visual_validator is None:
            try:
                self.visual_validator = VisualValidator(self.config)
                logger.info("Visual validator initialized and enabled")
                return True
            except Exception as e:
                logger.warning(f"Error initializing visual validator: {e}")
                self.config['use_visual_validation'] = False
                return False
        else:
            self.visual_validator.enable()
            logger.info("Visual validator enabled")
            return True

    def disable_visual_validation(self) -> None:
        """Disable visual validation"""
        self.config['use_visual_validation'] = False
        if self.visual_validator is not None:
            self.visual_validator.disable()
            logger.info("Visual validator disabled")

    def validate_analysis_results(self) -> Dict[str, Any]:
        """
        Validate analysis results using the visual validator.

        This method performs a comprehensive validation of the analysis results,
        including peak validation, onset validation, and generates a complete
        validation report.

        Returns:
            Dict[str, Any]: Comprehensive validation report
        """
        if not self.config.get('use_visual_validation', False) or self.visual_validator is None:
            return {"status": "disabled", "message": "Visual validation is disabled"}

        if not self.peaks or self.waveform_data is None:
            return {"status": "error", "message": "No peaks or waveform data available for validation"}

        # Convert peaks to the format expected by the validator
        peak_dicts = [p.to_dict() for p in self.peaks]

        # Get peak timestamps for onset validation
        peak_times = [p.time for p in self.peaks]

        # Get the actual waveform data (first channel)
        # The waveform_data is stored as a list of channels, we need the first channel
        actual_waveform_data = self.waveform_data[0]

        # Validate peaks
        peak_validation = self.visual_validator.validate_peaks(peak_dicts, actual_waveform_data, self.sample_rate)

        # Validate onsets
        onset_validation = self.visual_validator.validate_onsets(peak_times, actual_waveform_data, self.sample_rate)

        # Prepare analysis results for comprehensive validation
        analysis_results = {
            "peak_count": len(self.peaks),
            "onset_count": len(peak_times),
            "peaks": peak_dicts,
            "onsets": peak_times,
            "sample_rate": self.sample_rate,
            "duration": len(actual_waveform_data) / self.sample_rate if actual_waveform_data is not None else 0,
            "waveform_data": actual_waveform_data  # Include waveform data for validation
        }

        # Generate comprehensive validation report
        validation_report = self.visual_validator.generate_validation_report(analysis_results)

        # Add individual validation results
        validation_report["peak_validation"] = peak_validation
        validation_report["onset_validation"] = onset_validation

        # Add validation timestamp
        validation_report["timestamp"] = time.time()

        return validation_report


# Standalone function for analyzing a drum file
def analyze_drum_file(file_path: Union[str, Path],
                      use_madmom: bool = True,
                      drum_classification: bool = True) -> Tuple[List[Peak], Dict[str, Any]]:
    """
    Analyze a drum file and return detected peaks.

    Args:
        file_path: Path to audio file
        use_madmom: Whether to use madmom for beat detection
        drum_classification: Whether to classify drum hits

    Returns:
        Tuple of (peaks, analysis_summary)
    """
    # Create analyzer
    analyzer = WaveformAnalyzer()

    # Configure analyzer
    analyzer.config['use_madmom_onset_detection'] = use_madmom
    analyzer.config['use_madmom_beat_tracking'] = use_madmom
    analyzer.config['drum_classification'] = drum_classification

    # Load file
    if not analyzer.load_file(file_path):
        return [], {'error': 'Failed to load file'}

    # Process waveform
    analyzer.process_waveform()

    # Wait for processing to complete
    while not analyzer.is_processing_complete():
        time.sleep(0.1)

    # Get results
    peaks = analyzer.get_peak_data()
    summary = analyzer.get_analysis_summary()

    return peaks, summary
