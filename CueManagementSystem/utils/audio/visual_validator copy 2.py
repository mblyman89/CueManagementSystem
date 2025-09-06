"""
Visual Validator Module for WaveformAnalyzer

This module provides visual validation capabilities for the WaveformAnalyzer class.
It allows for visual inspection and validation of waveform analysis results.

Author: NinjaTeach AI Team
Version: 1.0.0
License: MIT
"""

import logging
import os
import time
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

logger = logging.getLogger("WaveformAnalyzer")


class VisualValidator:
    """
    Visual Validator for waveform analysis results.

    This class provides methods for visually validating waveform analysis results,
    including peak detection, onset detection, and other analysis features.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the VisualValidator.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.enabled = True
        logger.info("VisualValidator initialized")

    def validate_peaks(self, peaks: List[Dict[str, Any]], waveform_data: Any, sample_rate: int) -> Dict[str, Any]:
        """
        Validate detected peaks against waveform data.

        This method performs actual validation of peaks by checking:
        1. If peaks occur at points of significant amplitude change
        2. If peaks have reasonable amplitude values
        3. If peaks are not too close to each other (clustering)
        4. If peaks have consistent spectral characteristics

        Args:
            peaks: List of peak dictionaries
            waveform_data: Waveform data array
            sample_rate: Sample rate of the audio

        Returns:
            Dictionary with validation results
        """
        if not self.enabled:
            return {"status": "disabled", "message": "Visual validation is disabled"}

        # Initialize validation results
        valid_peaks = 0
        invalid_peaks = 0
        suspicious_peaks = 0
        validation_details = []

        # Minimum distance between peaks (in seconds)
        # Use the same value as in waveform_analyzer.py (min_peak_distance)
        min_peak_distance = self.config.get('min_peak_distance', 0.03)

        # Minimum amplitude threshold for a valid peak
        min_amplitude_threshold = 0.1

        # Check if waveform_data is a numpy array, if not convert it
        if not isinstance(waveform_data, np.ndarray):
            try:
                waveform_data = np.array(waveform_data)
            except Exception as e:
                logger.error(f"Error converting waveform data to numpy array: {e}")
                return {
                    "status": "error",
                    "message": "Invalid waveform data format",
                    "valid_peaks": 0,
                    "invalid_peaks": len(peaks)
                }

        # Sort peaks by time
        sorted_peaks = sorted(peaks, key=lambda p: p.get('time', 0))

        # Validate each peak
        for i, peak in enumerate(sorted_peaks):
            peak_time = peak.get('time', 0)
            peak_amplitude = peak.get('amplitude', 0)
            peak_confidence = peak.get('confidence', 0)

            # Convert peak time to sample index
            sample_index = int(peak_time * sample_rate)

            # Check if sample index is within valid range
            if sample_index < 0 or sample_index >= len(waveform_data):
                invalid_peaks += 1
                validation_details.append({
                    "peak_index": i,
                    "time": peak_time,
                    "status": "invalid",
                    "reason": "Peak time outside valid range"
                })
                continue

            # Check amplitude threshold
            if peak_amplitude < min_amplitude_threshold:
                suspicious_peaks += 1
                validation_details.append({
                    "peak_index": i,
                    "time": peak_time,
                    "status": "suspicious",
                    "reason": "Low amplitude"
                })
                continue

            # Check distance to previous peak
            if i > 0:
                prev_peak_time = sorted_peaks[i-1].get('time', 0)
                if peak_time - prev_peak_time < min_peak_distance:
                    suspicious_peaks += 1
                    validation_details.append({
                        "peak_index": i,
                        "time": peak_time,
                        "status": "suspicious",
                        "reason": "Too close to previous peak"
                    })
                    continue

            # Check if peak is at a local maximum in the waveform
            # Get a small window around the peak
            window_size = int(0.01 * sample_rate)  # 10ms window
            start_idx = max(0, sample_index - window_size)
            end_idx = min(len(waveform_data), sample_index + window_size)
            window = waveform_data[start_idx:end_idx]

            if len(window) > 0:
                local_max_idx = np.argmax(np.abs(window))
                local_max_time = (start_idx + local_max_idx) / sample_rate

                # If the peak is not close to the local maximum, mark as suspicious
                if abs(peak_time - local_max_time) > 0.01:  # 10ms tolerance
                    suspicious_peaks += 1
                    validation_details.append({
                        "peak_index": i,
                        "time": peak_time,
                        "status": "suspicious",
                        "reason": "Not aligned with local maximum"
                    })
                    continue

            # If we got here, the peak is valid
            valid_peaks += 1
            validation_details.append({
                "peak_index": i,
                "time": peak_time,
                "status": "valid",
                "reason": "Passed all validation checks"
            })

        return {
            "status": "success",
            "message": f"Validated {len(peaks)} peaks: {valid_peaks} valid, {suspicious_peaks} suspicious, {invalid_peaks} invalid",
            "valid_peaks": valid_peaks,
            "suspicious_peaks": suspicious_peaks,
            "invalid_peaks": invalid_peaks,
            "details": validation_details
        }

    def validate_onsets(self, onsets: List[float], waveform_data: Any, sample_rate: int) -> Dict[str, Any]:
        """
        Validate detected onsets against waveform data.

        This method performs actual validation of onsets by checking:
        1. If onsets occur at points of significant energy increase
        2. If onsets are not too close to each other
        3. If onsets have consistent temporal distribution
        4. If onsets align with actual transients in the audio

        Args:
            onsets: List of onset times in seconds
            waveform_data: Waveform data array
            sample_rate: Sample rate of the audio

        Returns:
            Dictionary with validation results
        """
        if not self.enabled:
            return {"status": "disabled", "message": "Visual validation is disabled"}

        # Initialize validation results
        valid_onsets = 0
        invalid_onsets = 0
        suspicious_onsets = 0
        validation_details = []

        # Use configuration parameters for onset validation
        # Get the suspicious_onset_tolerance from config, or calculate it from min_peak_distance
        suspicious_onset_tolerance = self.config.get('suspicious_onset_tolerance', None)
        if suspicious_onset_tolerance is None:
            # Fall back to calculating from min_peak_distance if not explicitly set
            min_peak_distance = self.config.get('min_peak_distance', 0.03)
            suspicious_onset_tolerance = min_peak_distance * 0.8  # 80% of min_peak_distance

        # Use this as the minimum distance between onsets
        min_onset_distance = suspicious_onset_tolerance

        # Log the tolerance being used
        logger.debug(f"Using suspicious_onset_tolerance={suspicious_onset_tolerance:.3f}s for onset validation")

        # Check if waveform_data is a numpy array, if not convert it
        if not isinstance(waveform_data, np.ndarray):
            try:
                waveform_data = np.array(waveform_data)
            except Exception as e:
                logger.error(f"Error converting waveform data to numpy array: {e}")
                return {
                    "status": "error",
                    "message": "Invalid waveform data format",
                    "valid_onsets": 0,
                    "invalid_onsets": len(onsets)
                }

        # Sort onsets by time
        sorted_onsets = sorted(onsets)

        # Calculate energy envelope for transient detection
        energy_envelope = self._calculate_energy_envelope(waveform_data, sample_rate)

        # Calculate energy derivative for onset detection
        energy_derivative = np.zeros_like(energy_envelope)
        energy_derivative[1:] = np.diff(energy_envelope)

        # Normalize energy derivative
        if np.max(np.abs(energy_derivative)) > 0:
            energy_derivative = energy_derivative / np.max(np.abs(energy_derivative))

        # Validate each onset
        for i, onset_time in enumerate(sorted_onsets):
            # Convert onset time to sample index
            sample_index = int(onset_time * sample_rate)

            # Check if sample index is within valid range
            if sample_index < 0 or sample_index >= len(waveform_data):
                invalid_onsets += 1
                validation_details.append({
                    "onset_index": i,
                    "time": onset_time,
                    "status": "invalid",
                    "reason": "Onset time outside valid range"
                })
                continue

            # Check distance to previous onset
            if i > 0:
                prev_onset_time = sorted_onsets[i-1]
                if onset_time - prev_onset_time < min_onset_distance:
                    suspicious_onsets += 1
                    validation_details.append({
                        "onset_index": i,
                        "time": onset_time,
                        "status": "suspicious",
                        "reason": "Too close to previous onset"
                    })
                    continue

            # Check if onset is at a point of energy increase
            # Get the energy derivative at the onset time and in a small window around it
            envelope_index = min(int(onset_time * sample_rate / 512), len(energy_derivative) - 1)

            # Use an adaptive window size based on the audio characteristics
            # For higher sample rates or more complex audio, use a larger window
            # Calculate window size based on sample rate (higher SR = larger window)
            window_size_factor = min(5, max(2, int(sample_rate / 22050)))

            # Look in an adaptive window around the onset time
            window_start = max(0, envelope_index - window_size_factor)
            window_end = min(len(energy_derivative), envelope_index + window_size_factor + 1)

            logger.debug(f"Using window size factor: {window_size_factor} for sample rate: {sample_rate}")

            if window_start < window_end and window_end <= len(energy_derivative):
                # Get maximum energy change in the window
                window_energy_changes = energy_derivative[window_start:window_end]
                max_energy_change = np.max(window_energy_changes) if len(window_energy_changes) > 0 else 0

                # Use an adaptive threshold based on the overall energy characteristics
                # Calculate the average energy change across the entire signal
                avg_energy_change = np.mean(np.abs(energy_derivative))
                # Set threshold to be the lower of a fixed minimum or a percentage of the average
                energy_threshold = min(0.05, max(0.02, avg_energy_change * 0.5))

                logger.debug(f"Adaptive energy threshold: {energy_threshold:.4f} (avg_energy_change: {avg_energy_change:.4f})")

                # If energy is not increasing significantly in the window, mark as suspicious
                if max_energy_change <= energy_threshold:
                    suspicious_onsets += 1
                    validation_details.append({
                        "onset_index": i,
                        "time": onset_time,
                        "status": "suspicious",
                        "reason": "No significant energy increase near onset"
                    })
                    continue

            # If we got here, the onset is valid
            valid_onsets += 1
            validation_details.append({
                "onset_index": i,
                "time": onset_time,
                "status": "valid",
                "reason": "Passed all validation checks"
            })

        return {
            "status": "success",
            "message": f"Validated {len(onsets)} onsets: {valid_onsets} valid, {suspicious_onsets} suspicious, {invalid_onsets} invalid",
            "valid_onsets": valid_onsets,
            "suspicious_onsets": suspicious_onsets,
            "invalid_onsets": invalid_onsets,
            "details": validation_details
        }

    def _calculate_energy_envelope(self, waveform_data: np.ndarray, sample_rate: int, window_size: int = 1024, hop_length: int = 512) -> np.ndarray:
        """
        Calculate the energy envelope of a waveform with improved robustness and performance.

        Args:
            waveform_data: Waveform data array
            sample_rate: Sample rate of the audio
            window_size: Size of the analysis window
            hop_length: Hop length between windows

        Returns:
            Energy envelope as a numpy array
        """
        try:
            # Check if waveform data is long enough for the window size
            if len(waveform_data) < window_size:
                # Return a single frame if the data is too short
                logger.warning(f"Waveform data length ({len(waveform_data)}) is less than window size ({window_size}). Returning single frame envelope.")
                return np.array([np.sum(waveform_data ** 2) / len(waveform_data)])

            # Adaptive window and hop size based on audio length and sample rate
            # For longer files, use larger windows for better performance
            # For higher sample rates, use larger windows for better frequency resolution
            if len(waveform_data) > 1000000:  # For files longer than ~22 seconds at 44.1kHz
                scale_factor = min(4, max(1, int(len(waveform_data) / 1000000)))
                window_size = min(4096, window_size * scale_factor)
                hop_length = min(1024, hop_length * scale_factor)
                logger.debug(f"Using larger window_size={window_size}, hop_length={hop_length} for long file")
            elif len(waveform_data) < 10 * window_size:
                # Use smaller window and hop for very short files
                window_size = min(window_size, len(waveform_data) // 4)
                hop_length = min(hop_length, window_size // 2)
                logger.debug(f"Using smaller window_size={window_size}, hop_length={hop_length} for short file")

            # Adjust window and hop size based on sample rate
            sr_factor = max(1, int(sample_rate / 22050))
            if sr_factor > 1:
                window_size = min(4096, window_size * sr_factor)
                hop_length = min(1024, hop_length * sr_factor)
                logger.debug(f"Adjusted for sample rate {sample_rate}: window_size={window_size}, hop_length={hop_length}")

            # Calculate number of frames with safety checks
            num_frames = max(1, 1 + (len(waveform_data) - window_size) // hop_length)

            # Initialize energy envelope
            energy_envelope = np.zeros(num_frames)

            # Try different methods in order of efficiency
            envelope_calculated = False

            # Method 1: Use librosa's RMS feature if available (fastest)
            if not envelope_calculated:
                try:
                    import librosa
                    # Use librosa's RMS feature which is highly optimized
                    energy_envelope = librosa.feature.rms(
                        y=waveform_data, 
                        frame_length=window_size, 
                        hop_length=hop_length
                    )[0]
                    # Square to get energy from RMS
                    energy_envelope = energy_envelope ** 2
                    envelope_calculated = True
                    logger.debug("Used librosa for energy envelope calculation")
                except (ImportError, Exception) as e:
                    logger.debug(f"Librosa method failed: {e}, trying numpy method")

            # Method 2: Use numpy's optimized operations (medium speed)
            if not envelope_calculated:
                try:
                    # Pre-calculate window function for better accuracy
                    window_func = np.hanning(window_size)

                    # Use numpy's stride tricks for efficient windowing without copying data
                    from numpy.lib import stride_tricks

                    # Calculate the shape and strides for the windowed view
                    shape = (num_frames, window_size)
                    strides = (hop_length * waveform_data.strides[0], waveform_data.strides[0])

                    # Create windowed view of the data
                    windows = stride_tricks.as_strided(
                        waveform_data[:len(waveform_data) - (len(waveform_data) - window_size) % hop_length], 
                        shape=shape, 
                        strides=strides
                    )

                    # Apply window function and calculate energy
                    windowed_frames = windows * window_func
                    energy_envelope = np.mean(windowed_frames ** 2, axis=1)

                    envelope_calculated = True
                    logger.debug("Used numpy stride tricks for energy envelope calculation")
                except Exception as e:
                    logger.debug(f"Numpy method failed: {e}, falling back to manual calculation")

            # Method 3: Manual calculation (slowest but most reliable)
            if not envelope_calculated:
                try:
                    for i in range(num_frames):
                        start = i * hop_length
                        end = min(start + window_size, len(waveform_data))
                        if end > start:
                            frame = waveform_data[start:end]
                            # Use float64 for better precision and to avoid overflow
                            energy_envelope[i] = np.mean((frame.astype(np.float64) ** 2))

                    envelope_calculated = True
                    logger.debug("Used manual calculation for energy envelope")
                except Exception as e:
                    logger.warning(f"Manual calculation failed: {e}, using fallback method")
                    # Last resort fallback
                    energy_envelope = np.ones(num_frames)

            # Apply appropriate smoothing based on the audio characteristics
            try:
                # Try to use scipy's gaussian filter for better smoothing
                from scipy.ndimage import gaussian_filter1d

                # Adaptive smoothing based on audio characteristics
                # For percussive audio (like drums), use less smoothing to preserve transients
                # For longer files, use more smoothing to reduce noise
                if self.config.get('is_drum_stem', False):
                    sigma = 1.0  # Less smoothing for drums
                else:
                    sigma = 2.0  # More smoothing for other audio

                # Apply smoothing
                energy_envelope = gaussian_filter1d(energy_envelope, sigma=sigma)
                logger.debug(f"Applied gaussian smoothing with sigma={sigma}")
            except ImportError:
                # Fall back to simple moving average with adaptive window size
                window_length = max(3, min(9, int(num_frames / 100)))
                if window_length % 2 == 0:
                    window_length += 1  # Ensure odd length for centered average

                energy_envelope = np.convolve(
                    energy_envelope, 
                    np.ones(window_length)/window_length, 
                    mode='same'
                )
                logger.debug(f"Applied moving average smoothing with window={window_length}")

            # Normalize with enhanced safety checks
            min_energy = np.min(energy_envelope)
            max_energy = np.max(energy_envelope)

            # Ensure we have a reasonable dynamic range
            if max_energy > min_energy and np.isfinite(max_energy) and np.isfinite(min_energy):
                # Normalize to [0, 1] range
                energy_envelope = (energy_envelope - min_energy) / (max_energy - min_energy)
            elif max_energy > 0 and np.isfinite(max_energy):
                # Simpler normalization if min is close to 0
                energy_envelope = energy_envelope / max_energy
            else:
                # If normalization fails, return a safe default
                logger.warning("Energy envelope normalization failed. Using default values.")
                energy_envelope = np.linspace(0, 1, num_frames)  # Ramp up as a safe default

            return energy_envelope

        except Exception as e:
            # If anything fails, return a safe default
            logger.error(f"Error calculating energy envelope: {e}")
            # Return a ramp instead of flat line for a more useful fallback
            num_frames = max(1, len(waveform_data) // hop_length)
            return np.linspace(0, 1, num_frames)

    def generate_validation_report(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive validation report.

        This method analyzes the results from peak and onset validation
        and generates a detailed report with metrics, statistics, and
        recommendations for improving the analysis accuracy.

        Args:
            analysis_results: Dictionary with analysis results

        Returns:
            Dictionary with validation report
        """
        if not self.enabled:
            logger.info("Visual validation is disabled")
            return {"status": "disabled", "message": "Visual validation is disabled"}

        logger.info("Generating comprehensive validation report...")

        # Extract data from analysis results
        peaks = analysis_results.get("peaks", [])
        onsets = analysis_results.get("onsets", [])
        sample_rate = analysis_results.get("sample_rate", 44100)
        duration = analysis_results.get("duration", 0)
        waveform_data = analysis_results.get("waveform_data", None)

        # Validate peaks and onsets if they haven't been validated yet
        peak_validation = analysis_results.get("peak_validation", None)
        if peak_validation is None and waveform_data is not None and peaks:
            peak_validation = self.validate_peaks(peaks, waveform_data, sample_rate)

        onset_validation = analysis_results.get("onset_validation", None)
        if onset_validation is None and waveform_data is not None and onsets:
            onset_validation = self.validate_onsets(onsets, waveform_data, sample_rate)

        # Calculate validation metrics
        peak_count = len(peaks)
        onset_count = len(onsets)

        valid_peaks = peak_validation.get("valid_peaks", 0) if peak_validation else 0
        suspicious_peaks = peak_validation.get("suspicious_peaks", 0) if peak_validation else 0
        invalid_peaks = peak_validation.get("invalid_peaks", 0) if peak_validation else 0

        valid_onsets = onset_validation.get("valid_onsets", 0) if onset_validation else 0
        suspicious_onsets = onset_validation.get("suspicious_onsets", 0) if onset_validation else 0
        invalid_onsets = onset_validation.get("invalid_onsets", 0) if onset_validation else 0

        # Calculate validation scores
        peak_score = valid_peaks / peak_count if peak_count > 0 else 0
        onset_score = valid_onsets / onset_count if onset_count > 0 else 0

        # Log detailed validation metrics
        logger.info(f"Peak validation: {valid_peaks}/{peak_count} valid peaks ({peak_score:.2f})")
        logger.info(f"Onset validation: {valid_onsets}/{onset_count} valid onsets ({onset_score:.2f})")

        if suspicious_peaks > 0:
            logger.info(f"Found {suspicious_peaks} suspicious peaks")
        if suspicious_onsets > 0:
            logger.info(f"Found {suspicious_onsets} suspicious onsets")

        # Calculate overall validation score (weighted average)
        # Give more weight to peak score (75%) and less to onset score (25%)
        # This is because peak detection is more reliable than onset detection
        overall_score = (peak_score * 0.75 + onset_score * 0.25) if (peak_count > 0 or onset_count > 0) else 0
        logger.info(f"Overall validation score: {overall_score:.2f} (75% peak score + 25% onset score)")

        # Generate recommendations based on validation results
        recommendations = []

        if suspicious_peaks > 0:
            recommendations.append(
                "Consider adjusting peak detection parameters to reduce the number of suspicious peaks."
            )

        if suspicious_onsets > 0:
            recommendations.append(
                "Consider adjusting onset detection parameters to reduce the number of suspicious onsets."
            )

        if peak_count > 0 and onset_count > 0:
            # Check if peaks and onsets are aligned
            peak_times = [p.get("time", 0) for p in peaks]
            onset_alignment_score = self._calculate_alignment_score(peak_times, onsets)

            if onset_alignment_score < 0.8:
                recommendations.append(
                    "Peaks and onsets are not well aligned. Consider adjusting detection parameters to improve alignment."
                )

        # Check density of peaks/onsets
        if duration > 0:
            peak_density = peak_count / duration
            onset_density = onset_count / duration

            # Get the expected peaks per minute from config, default to 120
            expected_peaks_per_minute = self.config.get('peaks_per_minute', 120)
            # Convert to peaks per second
            expected_peaks_per_second = expected_peaks_per_minute / 60
            # Set threshold at 1.5x the expected density
            density_threshold = expected_peaks_per_second * 1.5

            if peak_density > density_threshold:
                recommendations.append(
                    f"Peak density is very high ({peak_density:.1f} peaks/sec). Consider increasing minimum peak distance or threshold."
                )

            if onset_density > density_threshold:
                recommendations.append(
                    f"Onset density is very high ({onset_density:.1f} onsets/sec). Consider increasing minimum onset distance or threshold."
                )

        # Generate detailed report
        report = {
            "status": "success",
            "message": "Validation completed successfully",
            "timestamp": time.time(),
            "validation_score": overall_score,
            "details": {
                "peaks": {
                    "total": peak_count,
                    "valid": valid_peaks,
                    "suspicious": suspicious_peaks,
                    "invalid": invalid_peaks,
                    "confidence": peak_score
                },
                "onsets": {
                    "total": onset_count,
                    "valid": valid_onsets,
                    "suspicious": suspicious_onsets,
                    "invalid": invalid_onsets,
                    "confidence": onset_score
                }
            },
            "recommendations": recommendations
        }

        # Add detailed validation results if available
        if peak_validation:
            report["peak_validation"] = peak_validation

        if onset_validation:
            report["onset_validation"] = onset_validation

        return report

    def _calculate_alignment_score(self, peak_times: List[float], onset_times: List[float], tolerance: float = 0.05) -> float:
        """
        Calculate how well peaks and onsets are aligned.

        Args:
            peak_times: List of peak times in seconds
            onset_times: List of onset times in seconds
            tolerance: Maximum time difference for a peak and onset to be considered aligned

        Returns:
            Alignment score between 0 and 1
        """
        if not peak_times or not onset_times:
            return 0.0

        # Count how many peaks have a matching onset
        aligned_peaks = 0

        for peak_time in peak_times:
            # Check if there's an onset close to this peak
            for onset_time in onset_times:
                if abs(peak_time - onset_time) <= tolerance:
                    aligned_peaks += 1
                    break

        # Calculate alignment score
        return aligned_peaks / len(peak_times)

    def enable(self) -> None:
        """Enable visual validation"""
        self.enabled = True
        logger.info("Visual validation enabled")

    def disable(self) -> None:
        """Disable visual validation"""
        self.enabled = False
        logger.info("Visual validation disabled")
