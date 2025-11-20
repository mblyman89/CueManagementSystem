"""
Professional Waveform Renderer
==============================

Advanced waveform rendering engine with multiple visualization modes:
- RMS (Root Mean Square) rendering for better visual representation
- Spectral waveform with frequency-based coloring
- Multi-resolution rendering with adaptive detail levels
- Professional gradient schemes and color mapping
- Stereo channel separation and visualization
- Dynamic range and envelope detection

Author: Enhanced by NinjaTeach AI Team
Version: 3.0.0 - Professional Edition
"""

import numpy as np
import librosa
from typing import List, Tuple, Dict, Optional, Any, Union
from enum import Enum
import colorsys
from dataclasses import dataclass
import logging
from PySide6.QtGui import QColor, QLinearGradient, QRadialGradient, QConicalGradient
from PySide6.QtCore import Qt
import time
from scipy import signal
from scipy.ndimage import gaussian_filter1d

logger = logging.getLogger(__name__)


class WaveformRenderMode(Enum):
    """Different waveform rendering modes"""
    BASIC_MINMAX = "basic_minmax"
    RMS_ENVELOPE = "rms_envelope"
    SPECTRAL_COLOR = "spectral_color"
    DUAL_LAYER = "dual_layer"
    FREQUENCY_BANDS = "frequency_bands"
    ENVELOPE_FOLLOWER = "envelope_follower"
    HARMONIC_PERCUSSIVE = "harmonic_percussive"


class ColorScheme(Enum):
    """Professional color schemes"""
    CLASSIC_BLUE = "classic_blue"
    SPECTRAL_RAINBOW = "spectral_rainbow"
    ENERGY_HEAT = "energy_heat"
    FREQUENCY_BASED = "frequency_based"
    PROFESSIONAL_DARK = "professional_dark"
    STUDIO_MONITOR = "studio_monitor"
    VINTAGE_ANALOG = "vintage_analog"


@dataclass
class RenderingConfig:
    """Configuration for waveform rendering - Optimized defaults for drum analysis"""
    mode: WaveformRenderMode = WaveformRenderMode.FREQUENCY_BANDS  # Optimal for drums
    color_scheme: ColorScheme = ColorScheme.PROFESSIONAL_DARK  # Best contrast
    smoothing_factor: float = 0.15  # Moderate smoothing for cleaner visualization
    dynamic_range_db: float = 60.0  # Professional standard
    frequency_bands: int = 12  # Better frequency resolution for drums
    rms_window_size: int = 512  # Good balance for transient detection
    envelope_attack: float = 0.005  # Fast attack for drum transients
    envelope_release: float = 0.05  # Faster release for percussive content
    spectral_resolution: int = 2048  # Higher resolution for better frequency detail
    enable_antialiasing: bool = True  # Smooth, professional rendering
    stereo_separation: bool = True  # Visualize stereo field
    show_phase_correlation: bool = False  # Not needed for drums


class ProfessionalWaveformRenderer:
    """
    Professional-grade waveform renderer with advanced visualization techniques
    """

    def __init__(self, config: Optional[RenderingConfig] = None):
        self.config = config or RenderingConfig()
        self.logger = logging.getLogger(__name__)

        # Enhanced caching for performance
        self._spectral_cache = {}
        self._rms_cache = {}
        self._envelope_cache = {}
        self._color_cache = {}
        self._render_cache = {}
        self._cache_max_size = 50  # Limit cache size to prevent memory issues

        # Color palettes
        self._color_palettes = self._initialize_color_palettes()

    def _get_cache_key(self, audio_data, sample_rate, width, height, offset, zoom, mode, color_scheme):
        """Generate cache key for rendered data"""
        data_hash = hash(audio_data.tobytes() if hasattr(audio_data, 'tobytes') else str(audio_data))
        return f"{data_hash}_{sample_rate}_{width}_{height}_{offset:.3f}_{zoom:.3f}_{mode}_{color_scheme}"

    def _manage_cache_size(self, cache_dict):
        """Keep cache size under control"""
        if len(cache_dict) > self._cache_max_size:
            # Remove oldest entries (simple FIFO)
            keys_to_remove = list(cache_dict.keys())[:-self._cache_max_size // 2]
            for key in keys_to_remove:
                cache_dict.pop(key, None)

    def _initialize_color_palettes(self) -> Dict[ColorScheme, Dict[str, Any]]:
        """Initialize professional color palettes"""
        palettes = {}

        # Classic Blue - Professional studio look
        palettes[ColorScheme.CLASSIC_BLUE] = {
            'primary': QColor(64, 128, 255),
            'secondary': QColor(32, 96, 224),
            'accent': QColor(128, 192, 255),
            'background': QColor(16, 24, 32),
            'grid': QColor(64, 64, 96, 128),
            'gradient_stops': [(0.0, QColor(32, 64, 128)), (0.5, QColor(64, 128, 255)), (1.0, QColor(128, 192, 255))]
        }

        # Spectral Rainbow - Frequency-based coloring
        palettes[ColorScheme.SPECTRAL_RAINBOW] = {
            'primary': QColor(255, 128, 0),
            'secondary': QColor(255, 64, 128),
            'accent': QColor(128, 255, 64),
            'background': QColor(8, 8, 16),
            'grid': QColor(64, 64, 64, 96),
            'gradient_stops': self._generate_spectral_gradient()
        }

        # Energy Heat - Energy-based visualization
        palettes[ColorScheme.ENERGY_HEAT] = {
            'primary': QColor(255, 64, 0),
            'secondary': QColor(255, 128, 0),
            'accent': QColor(255, 255, 64),
            'background': QColor(16, 8, 8),
            'grid': QColor(96, 48, 48, 128),
            'gradient_stops': [(0.0, QColor(64, 0, 0)), (0.3, QColor(255, 64, 0)), (0.7, QColor(255, 128, 0)),
                               (1.0, QColor(255, 255, 128))]
        }

        # Professional Dark - Modern DAW look
        palettes[ColorScheme.PROFESSIONAL_DARK] = {
            'primary': QColor(0, 255, 128),
            'secondary': QColor(0, 192, 96),
            'accent': QColor(64, 255, 192),
            'background': QColor(24, 24, 28),
            'grid': QColor(64, 64, 72, 128),
            'gradient_stops': [(0.0, QColor(0, 128, 64)), (0.5, QColor(0, 255, 128)), (1.0, QColor(64, 255, 192))]
        }

        # Studio Monitor - Reference monitor colors
        palettes[ColorScheme.STUDIO_MONITOR] = {
            'primary': QColor(0, 255, 0),
            'secondary': QColor(255, 255, 0),
            'accent': QColor(255, 0, 0),
            'background': QColor(0, 0, 0),
            'grid': QColor(32, 32, 32, 128),
            'gradient_stops': [(0.0, QColor(0, 128, 0)), (0.6, QColor(255, 255, 0)), (0.9, QColor(255, 128, 0)),
                               (1.0, QColor(255, 0, 0))]
        }

        # Vintage Analog - Warm analog look
        palettes[ColorScheme.VINTAGE_ANALOG] = {
            'primary': QColor(255, 200, 100),
            'secondary': QColor(255, 150, 50),
            'accent': QColor(255, 220, 150),
            'background': QColor(32, 24, 16),
            'grid': QColor(96, 72, 48, 128),
            'gradient_stops': [(0.0, QColor(128, 64, 32)), (0.5, QColor(255, 150, 50)), (1.0, QColor(255, 220, 150))]
        }

        # Frequency Based - Color-coded frequency bands
        palettes[ColorScheme.FREQUENCY_BASED] = {
            'primary': QColor(128, 255, 128),
            'secondary': QColor(255, 128, 128),
            'accent': QColor(128, 128, 255),
            'background': QColor(16, 16, 24),
            'grid': QColor(64, 64, 80, 128),
            'gradient_stops': [(0.0, QColor(255, 0, 0)), (0.2, QColor(255, 128, 0)), (0.4, QColor(255, 255, 0)),
                               (0.6, QColor(128, 255, 0)), (0.8, QColor(0, 255, 128)), (1.0, QColor(0, 255, 255))]
        }

        return palettes

    def _generate_spectral_gradient(self) -> List[Tuple[float, QColor]]:
        """Generate spectral rainbow gradient stops"""
        stops = []
        for i in range(7):
            hue = i / 6.0  # 0 to 1
            rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            color = QColor(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
            stops.append((i / 6.0, color))
        return stops

    def render_waveform_points(self, audio_data: Union[np.ndarray, List], sample_rate: int,
                               width: int, height: int, offset: float = 0.0,
                               zoom: float = 1.0) -> List[Tuple[float, float, float, Optional[QColor]]]:
        """
        Generate professional waveform visualization points with caching

        Args:
            audio_data: Audio samples (mono or stereo) - can be numpy array or list
            sample_rate: Sample rate in Hz
            width: Widget width in pixels
            height: Widget height in pixels
            offset: Normalized scroll offset (0.0-1.0)
            zoom: Zoom factor (1.0 = normal)

        Returns:
            List of (x, y_top, y_bottom, color) tuples for rendering
        """
        # Check cache first for performance
        cache_key = self._get_cache_key(audio_data, sample_rate, width, height, offset, zoom,
                                        self.config.mode, self.config.color_scheme)
        if cache_key in self._render_cache:
            return self._render_cache[cache_key]
        # Handle your analyzer's specific data format: [numpy_array] (list containing numpy array)
        if isinstance(audio_data, list):
            if len(audio_data) > 0 and isinstance(audio_data[0], np.ndarray):
                # Your analyzer format: waveform_data = [waveform_mono]
                audio_data = audio_data[0]  # Extract the numpy array from the list
            else:
                # Regular list of numbers
                audio_data = np.array(audio_data)

        # Handle different data structures from your analyzer
        if hasattr(audio_data, 'shape'):
            if len(audio_data.shape) == 1:
                # Mono audio
                return self._render_mono_waveform(audio_data, sample_rate, width, height, offset, zoom)
            elif len(audio_data.shape) == 2:
                # Stereo audio - check if it's [channels, samples] or [samples, channels]
                if audio_data.shape[0] == 2 and audio_data.shape[1] > audio_data.shape[0]:
                    # [channels, samples] format
                    if self.config.stereo_separation:
                        return self._render_stereo_separated(audio_data, sample_rate, width, height, offset, zoom)
                    else:
                        # Mix to mono for rendering
                        mono_data = np.mean(audio_data, axis=0)
                        return self._render_mono_waveform(mono_data, sample_rate, width, height, offset, zoom)
                elif audio_data.shape[1] == 2 and audio_data.shape[0] > audio_data.shape[1]:
                    # [samples, channels] format - transpose it
                    audio_data = audio_data.T
                    if self.config.stereo_separation:
                        return self._render_stereo_separated(audio_data, sample_rate, width, height, offset, zoom)
                    else:
                        # Mix to mono for rendering
                        mono_data = np.mean(audio_data, axis=0)
                        return self._render_mono_waveform(mono_data, sample_rate, width, height, offset, zoom)
                else:
                    # Assume first dimension is samples, treat as mono
                    mono_data = audio_data.flatten()
                    return self._render_mono_waveform(mono_data, sample_rate, width, height, offset, zoom)
            else:
                # Multi-dimensional, flatten to mono
                mono_data = audio_data.flatten()
                return self._render_mono_waveform(mono_data, sample_rate, width, height, offset, zoom)
        else:
            # Fallback: treat as 1D array
            audio_data = np.array(audio_data).flatten()
            return self._render_mono_waveform(audio_data, sample_rate, width, height, offset, zoom)

    def _render_mono_waveform(self, audio_data: np.ndarray, sample_rate: int,
                              width: int, height: int, offset: float, zoom: float) -> List[
        Tuple[float, float, float, Optional[QColor]]]:
        """Render mono waveform with selected mode and caching"""

        # Calculate visible range
        total_samples = len(audio_data)
        samples_per_pixel = max(1, int(total_samples / (width * zoom)))
        start_sample = int(offset * total_samples)
        end_sample = min(total_samples, start_sample + int(width * samples_per_pixel))

        # Ensure bounds
        start_sample = max(0, min(start_sample, total_samples - 1))
        end_sample = max(start_sample + 1, min(end_sample, total_samples))

        # Select rendering method based on mode
        result = None
        if self.config.mode == WaveformRenderMode.RMS_ENVELOPE:
            result = self._render_rms_envelope(audio_data, start_sample, end_sample, width, height, samples_per_pixel)
        elif self.config.mode == WaveformRenderMode.SPECTRAL_COLOR:
            result = self._render_spectral_color(audio_data, sample_rate, start_sample, end_sample, width, height,
                                                 samples_per_pixel)
        elif self.config.mode == WaveformRenderMode.DUAL_LAYER:
            result = self._render_dual_layer(audio_data, start_sample, end_sample, width, height, samples_per_pixel)
        elif self.config.mode == WaveformRenderMode.FREQUENCY_BANDS:
            result = self._render_frequency_bands(audio_data, sample_rate, start_sample, end_sample, width, height,
                                                  samples_per_pixel)
        elif self.config.mode == WaveformRenderMode.ENVELOPE_FOLLOWER:
            result = self._render_envelope_follower(audio_data, start_sample, end_sample, width, height,
                                                    samples_per_pixel)
        else:
            # Fallback to basic min/max
            result = self._render_basic_minmax(audio_data, start_sample, end_sample, width, height, samples_per_pixel)

        # Cache the result for future use
        cache_key = self._get_cache_key(audio_data, sample_rate, width, height, offset, zoom, self.config.mode,
                                        self.config.color_scheme)
        self._render_cache[cache_key] = result
        self._manage_cache_size(self._render_cache)

        return result

    def _render_rms_envelope(self, audio_data: np.ndarray, start_sample: int, end_sample: int,
                             width: int, height: int, samples_per_pixel: int) -> List[
        Tuple[float, float, float, Optional[QColor]]]:
        """Render waveform using RMS envelope for better visual representation"""
        points = []
        center_y = height / 2
        # Calculate amplitude scale based on dynamic range setting
        # Convert dB to linear scale: higher dB = more sensitive to quiet sounds
        db_factor = self.config.dynamic_range_db / 60.0  # Normalize to 60dB reference
        amplitude_scale = height * 0.45 * (60.0 / self.config.dynamic_range_db)  # Inverse relationship

        if hasattr(self, '_debug_printed') and not self._debug_printed:
            print(
                f"🔧 DYNAMIC RANGE: Using {self.config.dynamic_range_db:.1f} dB, amplitude_scale={amplitude_scale:.2f}")
            self._debug_printed = True

        # RMS window size
        rms_window = self.config.rms_window_size

        for pixel_x in range(width):
            sample_start = start_sample + int(pixel_x * samples_per_pixel)
            sample_end = min(end_sample, sample_start + samples_per_pixel)

            if sample_start >= len(audio_data):
                break

            # Get pixel data
            pixel_data = audio_data[sample_start:sample_end]
            if len(pixel_data) == 0:
                points.append((float(pixel_x), float(center_y), float(center_y), None))
                continue

            # Calculate RMS value
            rms_value = np.sqrt(np.mean(pixel_data ** 2))

            # Calculate peak values for envelope
            max_val = np.max(np.abs(pixel_data))

            # Apply smoothing
            if self.config.smoothing_factor > 0 and len(points) > 0:
                # Get previous peak value from the last point
                prev_peak_y = points[-1][1]
                prev_max = (center_y - prev_peak_y) / amplitude_scale

                # Apply smoothing to both RMS and peak values
                original_rms = rms_value
                original_max = max_val
                rms_value = (prev_max * 0.8) * (
                        1 - self.config.smoothing_factor) + rms_value * self.config.smoothing_factor
                max_val = prev_max * (1 - self.config.smoothing_factor) + max_val * self.config.smoothing_factor

                if pixel_x == 0:  # Debug print only for first pixel to avoid spam
                    print(
                        f"🔧 RMS SMOOTHING APPLIED: factor={self.config.smoothing_factor:.3f}, rms: {original_rms:.4f}→{rms_value:.4f}, peak: {original_max:.4f}→{max_val:.4f}")

            # Convert to screen coordinates
            rms_y = center_y - (rms_value * amplitude_scale)
            peak_y = center_y - (max_val * amplitude_scale)

            # Ensure bounds
            rms_y = max(0.0, min(float(height), rms_y))
            peak_y = max(0.0, min(float(height), peak_y))

            # Color based on energy level
            color = self._get_energy_color(rms_value)

            points.append((float(pixel_x), float(peak_y), float(center_y + (center_y - peak_y)), color))

        return points

    def _render_spectral_color(self, audio_data: np.ndarray, sample_rate: int, start_sample: int, end_sample: int,
                               width: int, height: int, samples_per_pixel: int) -> List[
        Tuple[float, float, float, Optional[QColor]]]:
        """Render waveform with frequency-based coloring"""
        points = []
        center_y = height / 2
        # Calculate amplitude scale based on dynamic range setting
        amplitude_scale = height * 0.45 * (60.0 / self.config.dynamic_range_db)

        # STFT parameters
        n_fft = self.config.spectral_resolution
        hop_length = max(1, samples_per_pixel // 4)

        for pixel_x in range(width):
            sample_start = start_sample + int(pixel_x * samples_per_pixel)
            sample_end = min(end_sample, sample_start + samples_per_pixel)

            if sample_start >= len(audio_data):
                break

            pixel_data = audio_data[sample_start:sample_end]
            if len(pixel_data) == 0:
                points.append((float(pixel_x), float(center_y), float(center_y), None))
                continue

            # Calculate amplitude
            max_val = np.max(np.abs(pixel_data))
            min_val = np.min(pixel_data)

            # Calculate spectral centroid for coloring
            if len(pixel_data) >= n_fft:
                try:
                    # Pad data if necessary
                    if len(pixel_data) < n_fft:
                        pixel_data = np.pad(pixel_data, (0, n_fft - len(pixel_data)))

                    spectral_centroid = librosa.feature.spectral_centroid(
                        y=pixel_data, sr=sample_rate, n_fft=min(n_fft, len(pixel_data))
                    )[0, 0]

                    # Normalize spectral centroid to 0-1 range
                    normalized_centroid = min(1.0, spectral_centroid / (sample_rate / 4))

                except Exception as e:
                    normalized_centroid = 0.5  # Default to middle frequency
            else:
                normalized_centroid = 0.5

            # Convert to screen coordinates
            y_top = center_y - (max_val * amplitude_scale)
            y_bottom = center_y - (min_val * amplitude_scale)

            # Apply smoothing if enabled
            if self.config.smoothing_factor > 0 and len(points) > 0:
                prev_y_top = points[-1][1]
                prev_y_bottom = points[-1][2]
                # Convert back to amplitude for smoothing
                prev_max = (center_y - prev_y_top) / amplitude_scale
                prev_min = (center_y - prev_y_bottom) / amplitude_scale

                # Apply smoothing
                max_val = prev_max * (1 - self.config.smoothing_factor) + max_val * self.config.smoothing_factor
                min_val = prev_min * (1 - self.config.smoothing_factor) + min_val * self.config.smoothing_factor

                # Recalculate screen coordinates with smoothed values
                y_top = center_y - (max_val * amplitude_scale)
                y_bottom = center_y - (min_val * amplitude_scale)

            # Ensure bounds
            y_top = max(0.0, min(float(height), y_top))
            y_bottom = max(0.0, min(float(height), y_bottom))

            # Color based on spectral centroid
            color = self._get_spectral_color(normalized_centroid, max_val)

            points.append((float(pixel_x), float(y_top), float(y_bottom), color))

        return points

    def _render_dual_layer(self, audio_data: np.ndarray, start_sample: int, end_sample: int,
                           width: int, height: int, samples_per_pixel: int) -> List[
        Tuple[float, float, float, Optional[QColor]]]:
        """Render waveform with dual layer (RMS + peaks)"""
        points = []
        center_y = height / 2
        # Calculate amplitude scale based on dynamic range setting
        amplitude_scale = height * 0.45 * (60.0 / self.config.dynamic_range_db)

        for pixel_x in range(width):
            sample_start = start_sample + int(pixel_x * samples_per_pixel)
            sample_end = min(end_sample, sample_start + samples_per_pixel)

            if sample_start >= len(audio_data):
                break

            pixel_data = audio_data[sample_start:sample_end]
            if len(pixel_data) == 0:
                points.append((float(pixel_x), float(center_y), float(center_y), None))
                continue

            # Calculate both RMS and peak values
            rms_value = np.sqrt(np.mean(pixel_data ** 2))
            max_val = np.max(np.abs(pixel_data))

            # Apply smoothing if enabled
            if self.config.smoothing_factor > 0 and len(points) > 0:
                prev_y_top = points[-1][1]
                prev_y_bottom = points[-1][2]
                # Convert back to amplitude for smoothing
                prev_max = (center_y - prev_y_top) / amplitude_scale
                prev_rms = (center_y - (prev_y_top + prev_y_bottom) / 2) / (amplitude_scale * 0.8)

                # Apply smoothing
                max_val = prev_max * (1 - self.config.smoothing_factor) + max_val * self.config.smoothing_factor
                rms_value = prev_rms * (1 - self.config.smoothing_factor) + rms_value * self.config.smoothing_factor

            # Convert to screen coordinates
            rms_y = center_y - (rms_value * amplitude_scale * 0.8)  # RMS slightly smaller
            peak_y = center_y - (max_val * amplitude_scale)

            # Ensure bounds
            rms_y = max(0.0, min(float(height), rms_y))
            peak_y = max(0.0, min(float(height), peak_y))

            # Color based on dynamic range
            dynamic_range = max_val - rms_value if max_val > 0 else 0
            color = self._get_dynamic_range_color(dynamic_range)

            # Use peak values for outline, RMS for fill
            points.append((float(pixel_x), float(peak_y), float(center_y + (center_y - peak_y)), color))

        return points

    def _render_frequency_bands(self, audio_data: np.ndarray, sample_rate: int, start_sample: int, end_sample: int,
                                width: int, height: int, samples_per_pixel: int) -> List[
        Tuple[float, float, float, Optional[QColor]]]:
        """Render waveform with frequency band analysis"""
        points = []
        center_y = height / 2
        # Calculate amplitude scale based on dynamic range setting
        amplitude_scale = height * 0.45 * (60.0 / self.config.dynamic_range_db)

        # Define frequency bands (in Hz) - using config setting
        freq_bands = np.logspace(np.log10(20), np.log10(sample_rate / 2), self.config.frequency_bands + 1)

        if hasattr(self, '_freq_debug_printed') and not self._freq_debug_printed:
            print(
                f"🔧 FREQUENCY BANDS: Using {self.config.frequency_bands} bands, freq_bands shape: {len(freq_bands) - 1}")
            self._freq_debug_printed = True

        for pixel_x in range(width):
            sample_start = start_sample + int(pixel_x * samples_per_pixel)
            sample_end = min(end_sample, sample_start + samples_per_pixel)

            if sample_start >= len(audio_data):
                break

            pixel_data = audio_data[sample_start:sample_end]
            if len(pixel_data) == 0:
                points.append((float(pixel_x), float(center_y), float(center_y), None))
                continue

            # Calculate amplitude
            max_val = np.max(np.abs(pixel_data))
            min_val = np.min(pixel_data)

            # Analyze frequency content
            if len(pixel_data) >= 64:  # Minimum for meaningful FFT
                try:
                    # Compute FFT
                    fft = np.fft.rfft(pixel_data)
                    freqs = np.fft.rfftfreq(len(pixel_data), 1 / sample_rate)
                    magnitudes = np.abs(fft)

                    # Find dominant frequency band
                    band_energies = []
                    for i in range(len(freq_bands) - 1):
                        band_mask = (freqs >= freq_bands[i]) & (freqs < freq_bands[i + 1])
                        band_energy = np.sum(magnitudes[band_mask])
                        band_energies.append(band_energy)

                    # Get dominant band
                    if band_energies:
                        dominant_band = np.argmax(band_energies)
                        band_ratio = dominant_band / (len(freq_bands) - 1)
                    else:
                        band_ratio = 0.5

                except Exception:
                    band_ratio = 0.5
            else:
                band_ratio = 0.5

            # Convert to screen coordinates
            y_top = center_y - (max_val * amplitude_scale)
            y_bottom = center_y - (min_val * amplitude_scale)

            # Apply smoothing if enabled
            if self.config.smoothing_factor > 0 and len(points) > 0:
                prev_y_top = points[-1][1]
                prev_y_bottom = points[-1][2]
                # Convert back to amplitude for smoothing
                prev_max = (center_y - prev_y_top) / amplitude_scale
                prev_min = (center_y - prev_y_bottom) / amplitude_scale

                # Apply smoothing
                max_val = prev_max * (1 - self.config.smoothing_factor) + max_val * self.config.smoothing_factor
                min_val = prev_min * (1 - self.config.smoothing_factor) + min_val * self.config.smoothing_factor

                # Recalculate screen coordinates with smoothed values
                y_top = center_y - (max_val * amplitude_scale)
                y_bottom = center_y - (min_val * amplitude_scale)

            # Ensure bounds
            y_top = max(0.0, min(float(height), y_top))
            y_bottom = max(0.0, min(float(height), y_bottom))

            # Color based on frequency band
            color = self._get_frequency_band_color(band_ratio, max_val)

            points.append((float(pixel_x), float(y_top), float(y_bottom), color))

        return points

    def _render_envelope_follower(self, audio_data: np.ndarray, start_sample: int, end_sample: int,
                                  width: int, height: int, samples_per_pixel: int) -> List[
        Tuple[float, float, float, Optional[QColor]]]:
        """Render waveform using envelope follower"""
        points = []
        center_y = height / 2
        # Calculate amplitude scale based on dynamic range setting
        amplitude_scale = height * 0.45 * (60.0 / self.config.dynamic_range_db)

        # Envelope follower parameters
        attack_coeff = 1.0 - np.exp(-1.0 / (self.config.envelope_attack * 44100))
        release_coeff = 1.0 - np.exp(-1.0 / (self.config.envelope_release * 44100))

        envelope = 0.0

        for pixel_x in range(width):
            sample_start = start_sample + int(pixel_x * samples_per_pixel)
            sample_end = min(end_sample, sample_start + samples_per_pixel)

            if sample_start >= len(audio_data):
                break

            pixel_data = audio_data[sample_start:sample_end]
            if len(pixel_data) == 0:
                points.append((float(pixel_x), float(center_y), float(center_y), None))
                continue

            # Calculate current amplitude
            current_amp = np.max(np.abs(pixel_data))

            # Apply envelope follower
            if current_amp > envelope:
                envelope += (current_amp - envelope) * attack_coeff
            else:
                envelope += (current_amp - envelope) * release_coeff

            # Convert to screen coordinates
            y_top = center_y - (envelope * amplitude_scale)
            y_bottom = center_y + (envelope * amplitude_scale)

            # Ensure bounds
            y_top = max(0.0, min(float(height), y_top))
            y_bottom = max(0.0, min(float(height), y_bottom))

            # Color based on envelope level
            color = self._get_envelope_color(envelope)

            points.append((float(pixel_x), float(y_top), float(y_bottom), color))

        return points

    def _render_basic_minmax(self, audio_data: np.ndarray, start_sample: int, end_sample: int,
                             width: int, height: int, samples_per_pixel: int) -> List[
        Tuple[float, float, float, Optional[QColor]]]:
        """Basic min/max rendering (fallback)"""
        points = []
        center_y = height / 2
        # Calculate amplitude scale based on dynamic range setting
        amplitude_scale = height * 0.45 * (60.0 / self.config.dynamic_range_db)

        for pixel_x in range(width):
            sample_start = start_sample + int(pixel_x * samples_per_pixel)
            sample_end = min(end_sample, sample_start + samples_per_pixel)

            if sample_start >= len(audio_data):
                break

            pixel_data = audio_data[sample_start:sample_end]
            if len(pixel_data) == 0:
                points.append((float(pixel_x), float(center_y), float(center_y), None))
                continue

            max_val = np.max(pixel_data)
            min_val = np.min(pixel_data)

            # Apply smoothing if enabled
            if self.config.smoothing_factor > 0 and len(points) > 0:
                prev_y_top = points[-1][1]
                prev_y_bottom = points[-1][2]
                # Convert back to amplitude for smoothing
                prev_max = (center_y - prev_y_top) / amplitude_scale
                prev_min = (center_y - prev_y_bottom) / amplitude_scale

                # Apply smoothing
                max_val = prev_max * (1 - self.config.smoothing_factor) + max_val * self.config.smoothing_factor
                min_val = prev_min * (1 - self.config.smoothing_factor) + min_val * self.config.smoothing_factor

            # Convert to screen coordinates
            y_top = center_y - (max_val * amplitude_scale)
            y_bottom = center_y - (min_val * amplitude_scale)

            # Ensure bounds
            y_top = max(0.0, min(float(height), y_top))
            y_bottom = max(0.0, min(float(height), y_bottom))

            points.append((float(pixel_x), float(y_top), float(y_bottom), None))

        return points

    def _get_energy_color(self, energy: float) -> QColor:
        """Get color based on energy level"""
        # Ensure we have the color scheme in our palettes
        if self.config.color_scheme not in self._color_palettes:
            # Fallback to a default color scheme
            color_scheme = ColorScheme.PROFESSIONAL_DARK
        else:
            color_scheme = self.config.color_scheme

        palette = self._color_palettes[color_scheme]

        if self.config.color_scheme == ColorScheme.ENERGY_HEAT:
            # Heat map coloring
            if energy < 0.1:
                return QColor(64, 0, 0)
            elif energy < 0.3:
                return QColor(128, 32, 0)
            elif energy < 0.6:
                return QColor(255, 64, 0)
            elif energy < 0.8:
                return QColor(255, 128, 0)
            else:
                return QColor(255, 255, 128)
        else:
            # Use palette primary color with energy-based alpha
            color = palette['primary']
            alpha = int(128 + min(energy * 127, 127))  # Ensure alpha doesn't exceed 255
            color.setAlpha(alpha)
            return color

    def _get_spectral_color(self, spectral_centroid: float, amplitude: float) -> QColor:
        """Get color based on spectral centroid"""
        if self.config.color_scheme == ColorScheme.SPECTRAL_RAINBOW:
            # Map spectral centroid to hue
            hue = spectral_centroid
            saturation = min(1.0, amplitude * 2)
            value = 0.8 + (amplitude * 0.2)

            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
            return QColor(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
        else:
            # Use palette with spectral modulation
            color_scheme = self.config.color_scheme if self.config.color_scheme in self._color_palettes else ColorScheme.PROFESSIONAL_DARK
            palette = self._color_palettes[color_scheme]
            base_color = palette['primary']

            # Modulate color based on spectral centroid
            r, g, b = base_color.red(), base_color.green(), base_color.blue()

            if spectral_centroid < 0.33:  # Low frequencies - more red
                r = min(255, int(r * (1 + spectral_centroid)))
            elif spectral_centroid < 0.66:  # Mid frequencies - more green
                g = min(255, int(g * (1 + spectral_centroid)))
            else:  # High frequencies - more blue
                b = min(255, int(b * (1 + spectral_centroid)))

            return QColor(r, g, b)

    def _get_dynamic_range_color(self, dynamic_range: float) -> QColor:
        """Get color based on dynamic range"""
        color_scheme = self.config.color_scheme if self.config.color_scheme in self._color_palettes else ColorScheme.PROFESSIONAL_DARK
        palette = self._color_palettes[color_scheme]

        if dynamic_range < 0.1:
            return palette['secondary']  # Low dynamic range
        elif dynamic_range < 0.5:
            return palette['primary']  # Medium dynamic range
        else:
            return palette['accent']  # High dynamic range

    def _get_frequency_band_color(self, band_ratio: float, amplitude: float) -> QColor:
        """Get color based on dominant frequency band"""
        if self.config.color_scheme == ColorScheme.FREQUENCY_BASED:
            # Map frequency bands to colors
            alpha = int(128 + min(amplitude * 127, 127))  # Ensure alpha doesn't exceed 255
            if band_ratio < 0.2:  # Sub-bass/Bass
                return QColor(255, 0, 0, alpha)
            elif band_ratio < 0.4:  # Low-mid
                return QColor(255, 128, 0, alpha)
            elif band_ratio < 0.6:  # Mid
                return QColor(255, 255, 0, alpha)
            elif band_ratio < 0.8:  # High-mid
                return QColor(128, 255, 0, alpha)
            else:  # High/Presence
                return QColor(0, 255, 255, alpha)
        else:
            color_scheme = self.config.color_scheme if self.config.color_scheme in self._color_palettes else ColorScheme.PROFESSIONAL_DARK
            palette = self._color_palettes[color_scheme]
            return palette['primary']

    def _get_envelope_color(self, envelope: float) -> QColor:
        """Get color based on envelope level"""
        color_scheme = self.config.color_scheme if self.config.color_scheme in self._color_palettes else ColorScheme.PROFESSIONAL_DARK
        palette = self._color_palettes[color_scheme]

        # Interpolate between colors based on envelope level
        if envelope < 0.33:
            # Low level - use secondary color
            return palette['secondary']
        elif envelope < 0.66:
            # Medium level - use primary color
            return palette['primary']
        else:
            # High level - use accent color
            return palette['accent']

    def get_gradient_for_scheme(self, width: int, height: int) -> QLinearGradient:
        """Get gradient for current color scheme"""
        color_scheme = self.config.color_scheme if self.config.color_scheme in self._color_palettes else ColorScheme.PROFESSIONAL_DARK
        palette = self._color_palettes[color_scheme]
        gradient = QLinearGradient(0, 0, 0, height)

        for stop, color in palette['gradient_stops']:
            gradient.setColorAt(stop, color)

        return gradient

    def _render_stereo_separated(self, audio_data: np.ndarray, sample_rate: int,
                                 width: int, height: int, offset: float, zoom: float) -> List[
        Tuple[float, float, float, Optional[QColor]]]:
        """Render stereo channels separately"""
        # Split stereo channels
        left_channel = audio_data[0] if audio_data.shape[0] == 2 else audio_data[:, 0]
        right_channel = audio_data[1] if audio_data.shape[0] == 2 else audio_data[:, 1]

        # Render each channel in its own half
        left_points = self._render_mono_waveform(left_channel, sample_rate, width, height // 2, offset, zoom)
        right_points = self._render_mono_waveform(right_channel, sample_rate, width, height // 2, offset, zoom)

        # Combine points with offset for right channel
        combined_points = []
        for i in range(min(len(left_points), len(right_points))):
            left_x, left_y_top, left_y_bottom, left_color = left_points[i]
            right_x, right_y_top, right_y_bottom, right_color = right_points[i]

            # Left channel in top half
            combined_points.append((float(left_x), float(left_y_top), float(left_y_bottom), left_color))

            # Right channel in bottom half (offset by height/2)
            right_y_top_offset = right_y_top + height // 2
            right_y_bottom_offset = right_y_bottom + height // 2
            combined_points.append(
                (float(right_x), float(right_y_top_offset), float(right_y_bottom_offset), right_color))

        return combined_points