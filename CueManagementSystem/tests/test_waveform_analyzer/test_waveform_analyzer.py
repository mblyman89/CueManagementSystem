"""
Test script for the enhanced WaveformAnalyzer class.

This script demonstrates how to use the WaveformAnalyzer class to analyze
audio files and detect peaks using librosa's advanced audio analysis capabilities.

Usage:
    python test_waveform_analyzer.py <path_to_wav_file>
"""

import sys
import time
from pathlib import Path
from PySide6.QtCore import QCoreApplication
from waveform_analyzer import WaveformAnalyzer

def on_processing_complete(success):
    """Callback function for when processing is complete"""
    if success:
        print("Waveform processing completed successfully.")
    else:
        print("Waveform processing failed.")

def on_peak_detection_complete():
    """Callback function for when peak detection is complete"""
    print(f"Peak detection complete. Found {len(analyzer.peaks)} peaks.")

    # Print the first 10 peaks (or all if less than 10)
    print("\nPeak timestamps with drum types:")
    for i, peak in enumerate(analyzer.peaks[:10]):
        drum_type = peak.drum_type if peak.drum_type else "unknown"
        print(f"  {i+1}. {peak.time_str} (amplitude: {peak.amplitude:.3f}, drum type: {drum_type})")

    if len(analyzer.peaks) > 10:
        print(f"  ... and {len(analyzer.peaks) - 10} more peaks")

    # Get drum type statistics
    drum_types = analyzer.get_drum_types()

    # Print drum type counts
    print("\nDrum type statistics:")
    for drum_type, peaks in drum_types.items():
        print(f"  {drum_type}: {len(peaks)} peaks")

    # Exit the application
    QCoreApplication.quit()

if __name__ == "__main__":
    # Create Qt application (required for signals)
    app = QCoreApplication(sys.argv)

    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python test_waveform_analyzer.py <path_to_wav_file>")
        sys.exit(1)

    # Get file path from command line
    file_path = Path(sys.argv[1])

    # Create analyzer
    analyzer = WaveformAnalyzer()

    # Connect signals
    analyzer.peak_detection_complete.connect(on_peak_detection_complete)

    # Load and process file
    print(f"Loading file: {file_path}")
    if analyzer.load_file(file_path):
        print("File loaded successfully.")
        print(f"Duration: {analyzer._format_time(analyzer.duration_seconds)}")
        print(f"Sample rate: {analyzer.sample_rate}Hz")
        print(f"Channels: {analyzer.channels}")

        # Process waveform
        print("Processing waveform...")
        analyzer.process_waveform(on_processing_complete)

        # Run Qt event loop
        sys.exit(app.exec())
    else:
        print("Failed to load file.")
        sys.exit(1)
