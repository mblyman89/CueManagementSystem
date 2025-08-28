# Enhanced WaveformAnalyzer

This directory contains the enhanced WaveformAnalyzer class, which provides professional-grade audio analysis and peak detection capabilities.

## Overview

The WaveformAnalyzer class has been completely redesigned to leverage librosa's advanced audio analysis capabilities for more accurate and comprehensive peak detection. The implementation maintains compatibility with the existing codebase while providing improved functionality.

## Key Features

- High-precision peak detection using multiple librosa-based methods:
  - Onset detection (for sudden changes in audio)
  - Beat tracking (for rhythmic beats)
  - Spectral contrast (for significant tonal changes)
- Fallback to amplitude-based detection when librosa is not available
- Accurate timestamp collection for peaks
- Waveform visualization support
- Persistent peak data storage

## Usage

### Basic Usage

```python
from utils.audio.waveform_analyzer import WaveformAnalyzer

# Create analyzer
analyzer = WaveformAnalyzer()

# Load file
analyzer.load_file("path/to/audio.wav")

# Process waveform (with optional callback)
analyzer.process_waveform(callback=on_processing_complete)

# Access peaks after processing is complete
for peak in analyzer.peaks:
    print(f"Peak at {peak.time_str} with amplitude {peak.amplitude}")
```

### Connecting to Signals

The WaveformAnalyzer emits a signal when peak detection is complete:

```python
# Connect to peak detection complete signal
analyzer.peak_detection_complete.connect(on_peak_detection_complete)
```

### Testing

A test script is provided to demonstrate the functionality:

```bash
python test_waveform_analyzer.py path/to/audio.wav
```

## Implementation Details

The enhanced WaveformAnalyzer uses a multi-method approach to peak detection:

1. **Onset Detection**: Uses librosa.onset to find sudden changes in audio, which are often significant moments.

2. **Beat Tracking**: Uses librosa.beat to find rhythmic beats in the audio, which is particularly useful for music files.

3. **Spectral Contrast**: Uses librosa.feature.spectral_contrast to find significant tonal changes in the audio.

4. **Amplitude-based Detection**: Used as a fallback when librosa is not available.

The results from these methods are combined and filtered to ensure a minimum distance between peaks, providing a comprehensive set of significant moments in the audio.

## Dependencies

- librosa (for advanced audio analysis)
- numpy (for numerical operations)
- PySide6 (for Qt integration)
- scipy (optional, for additional signal processing)