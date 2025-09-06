"""
Musical Generator for Waveform Analysis Dialog

This module provides functionality to generate cues based on detected and manual peaks
from waveform analysis, with support for random and sequential distribution methods.
"""

import random
import json
import os
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QComboBox, QDoubleSpinBox, QGroupBox, QMessageBox,
    QFileDialog, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont


@dataclass
class GeneratedCue:
    """Represents a generated cue with all necessary data"""
    cue_number: int
    cue_type: str
    output: Union[int, List[int]]  # Can be a single int or a list of ints for DOUBLE SHOT
    delay: float
    execute_time: float

    def to_table_format(self) -> List[Any]:
        """Convert to format expected by cue table"""
        # Format execute_time as MM:SS.SSSSSSSS (preserving all decimal places)
        minutes = int(self.execute_time // 60)
        seconds = self.execute_time % 60
        # Use 'g' format to preserve all decimal places without rounding
        formatted_time = f"{minutes:02d}:{seconds:g}"

        # Format output based on type
        if isinstance(self.output, list):
            output_str = ", ".join(str(o) for o in self.output)
        else:
            output_str = str(self.output)

        return [
            self.cue_number,
            self.cue_type,
            output_str,  # Can be multiple outputs for DOUBLE SHOT
            self.delay,
            formatted_time
        ]


class MusicalGenerator(QWidget):
    """
    Musical Generator widget for creating cues from waveform peaks

    Features:
    - Random or Sequential distribution methods
    - Time offset adjustment with millisecond precision
    - Peak type selection (Detected/Manual/Both)
    - Single shot cue generation
    - Save/Load state functionality
    """

    # Signals
    cues_generated = Signal(list)  # Emitted when cues are generated
    state_saved = Signal(str)  # Emitted when state is saved
    state_loaded = Signal(dict)  # Emitted when state is loaded

    def __init__(self, parent=None, waveform_view=None, cue_table=None):
        super().__init__(parent)
        self.waveform_view = waveform_view
        self.cue_table = cue_table
        self.analyzer = None

        # Generator state
        self.last_generated_cues = []
        self.current_state = {}

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)  # Reduced spacing
        layout.setContentsMargins(5, 5, 5, 5)  # Reduced margins

        # Title removed to save space for waveform widget
        # title_label = QLabel("Musical Generator")

        # Distribution Method Group
        self._create_distribution_group(layout)

        # Time Offset Group
        self._create_time_offset_group(layout)

        # Peak Selection Group
        self._create_peak_selection_group(layout)

        # Generation Controls
        self._create_generation_controls(layout)

        # Save/Load Controls moved to Waveform Controls tab
        # self._create_save_load_controls(layout)

        # Status
        self._create_status_section(layout)

        layout.addStretch()

    def _create_distribution_group(self, parent_layout):
        """Create distribution method selection group"""
        group = QGroupBox("Distribution Method")
        layout = QVBoxLayout(group)

        self.distribution_combo = QComboBox()
        self.distribution_combo.addItems(["Random", "Sequential"])
        self.distribution_combo.setCurrentText("Random")

        # Removed "Method:" label to save space - group box title is sufficient
        layout.addWidget(self.distribution_combo)

        parent_layout.addWidget(group)

    def _create_time_offset_group(self, parent_layout):
        """Create time offset adjustment group"""
        group = QGroupBox("Time Offset")
        layout = QVBoxLayout(group)

        # Time offset spinbox with 4-digit precision
        self.time_offset_spinbox = QDoubleSpinBox()
        self.time_offset_spinbox.setRange(-9999.9999, 9999.9999)
        self.time_offset_spinbox.setDecimals(4)
        self.time_offset_spinbox.setValue(0.0000)
        self.time_offset_spinbox.setSuffix(" ms")
        self.time_offset_spinbox.setSingleStep(0.0001)

        # Removed label and example text to save space - group box title is sufficient
        layout.addWidget(self.time_offset_spinbox)

        parent_layout.addWidget(group)

    def _create_peak_selection_group(self, parent_layout):
        """Create peak type selection group"""
        group = QGroupBox("Peak Selection")
        layout = QVBoxLayout(group)

        self.detected_peaks_checkbox = QCheckBox("Include Detected Peaks")
        self.detected_peaks_checkbox.setChecked(True)

        self.manual_peaks_checkbox = QCheckBox("Include Manual Peaks")
        self.manual_peaks_checkbox.setChecked(True)

        layout.addWidget(self.detected_peaks_checkbox)
        layout.addWidget(self.manual_peaks_checkbox)

        parent_layout.addWidget(group)

    def _create_generation_controls(self, parent_layout):
        """Create generation control buttons"""
        group = QGroupBox("Generation Controls")
        layout = QVBoxLayout(group)

        self.generate_button = QPushButton("GENERATE")
        self.generate_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """)

        layout.addWidget(self.generate_button)

        parent_layout.addWidget(group)

    def _create_save_load_controls(self, parent_layout):
        """Create save/load control buttons"""
        group = QGroupBox("State Management")
        layout = QHBoxLayout(group)

        self.save_button = QPushButton("Save State")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 8px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5dade2;
            }
        """)

        self.load_button = QPushButton("Load State")
        self.load_button.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                font-weight: bold;
                padding: 8px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f39c12;
            }
        """)

        layout.addWidget(self.save_button)
        layout.addWidget(self.load_button)

        parent_layout.addWidget(group)

    def _create_status_section(self, parent_layout):
        """Create status display section"""
        group = QGroupBox("Status")
        layout = QVBoxLayout(group)

        self.status_label = QLabel("Ready to generate cues")
        self.status_label.setStyleSheet("color: #2ecc71; font-weight: bold;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)

        parent_layout.addWidget(group)

    def _connect_signals(self):
        """Connect widget signals to handlers"""
        self.generate_button.clicked.connect(self._on_generate_clicked)
        # Save/Load buttons moved to Waveform Controls tab
        # self.save_button.clicked.connect(self._on_save_clicked)
        # self.load_button.clicked.connect(self._on_load_clicked)

    def set_analyzer(self, analyzer):
        """Set the waveform analyzer reference"""
        print(f"🔧 MusicalGenerator.set_analyzer called with: {analyzer}")
        print(f"🔧 Analyzer type: {type(analyzer)}")
        if analyzer:
            print(f"🔧 Analyzer has waveform_data: {hasattr(analyzer, 'waveform_data')}")
            print(f"🔧 Analyzer is_analyzed: {getattr(analyzer, 'is_analyzed', 'N/A')}")

        self.analyzer = analyzer
        self._update_status()
        print(f"🔧 Generator status after set_analyzer: {self.status_label.text()}")

    def _update_status(self):
        """Update status display based on current state"""
        print(f"🔧 _update_status called, analyzer: {self.analyzer}")
        print(f"🔧 waveform_view: {self.waveform_view}")

        # Check if we have any peaks available (detected or manual)
        detected_count = self._get_detected_peak_count()
        manual_count = self._get_manual_peak_count()

        # If no analyzer but we have manual peaks, that's still valid
        if not self.analyzer and manual_count == 0:
            print("🔧 No analyzer and no manual peaks - setting status to 'No analyzer available'")
            self.status_label.setText("Load audio file and add peaks to generate cues")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.generate_button.setEnabled(False)
            return
        elif not self.analyzer and manual_count > 0:
            print(f"🔧 No analyzer but {manual_count} manual peaks available")
            # Continue with status update using manual peaks only

        # Count available peaks
        detected_count = self._get_detected_peak_count()
        manual_count = self._get_manual_peak_count()
        total_peaks = detected_count + manual_count

        # Check which peaks will be included based on checkboxes
        included_peaks = 0
        if self.detected_peaks_checkbox.isChecked():
            included_peaks += detected_count
        if self.manual_peaks_checkbox.isChecked():
            included_peaks += manual_count

        # Create status message with limits
        if included_peaks > 1000:
            status_text = f"ERROR: {included_peaks} peaks selected (MAX: 1000)"
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.generate_button.setEnabled(False)
        elif included_peaks == 0:
            status_text = f"Ready: {detected_count} detected, {manual_count} manual peaks (none selected)"
            self.status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
            self.generate_button.setEnabled(False)
        else:
            status_text = f"Ready: {included_peaks}/{total_peaks} peaks selected (MAX: 1000 cues/outputs)"
            self.status_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
            self.generate_button.setEnabled(True)

    def _get_detected_peak_count(self) -> int:
        """Get count of detected peaks"""
        if not self.waveform_view or not hasattr(self.waveform_view, 'get_detected_peak_count'):
            print(f"🔧 No waveform_view or get_detected_peak_count method")
            return 0
        count = self.waveform_view.get_detected_peak_count()
        print(f"🔧 Detected peak count: {count}")
        return count

    def _get_manual_peak_count(self) -> int:
        """Get count of manual peaks"""
        if not self.waveform_view or not hasattr(self.waveform_view, 'get_manual_peak_count'):
            print(f"🔧 No waveform_view or get_manual_peak_count method")
            return 0
        count = self.waveform_view.get_manual_peak_count()
        print(f"🔧 Manual peak count: {count}")
        return count

    def _on_generate_clicked(self):
        """Handle generate button click with timeout protection"""
        import threading
        import time

        try:
            print(f"🔧 Generate button clicked")
            self._set_status("Generating cues...", "processing")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress

            # Disable generate button to prevent multiple clicks
            self.generate_button.setEnabled(False)

            # Use threading with timeout to prevent UI freeze
            result = {'cues': None, 'error': None, 'completed': False}

            def generate_worker():
                try:
                    print(f"🔧 Worker thread starting cue generation")
                    result['cues'] = self._generate_cues()
                    result['completed'] = True
                    print(f"🔧 Worker thread completed successfully")
                except Exception as e:
                    print(f"🔧 Worker thread error: {e}")
                    result['error'] = str(e)
                    result['completed'] = True

            # Start worker thread
            worker_thread = threading.Thread(target=generate_worker)
            worker_thread.daemon = True
            worker_thread.start()

            # Wait with timeout (30 seconds max)
            timeout_seconds = 30
            start_time = time.time()

            while not result['completed'] and (time.time() - start_time) < timeout_seconds:
                time.sleep(0.1)  # Check every 100ms
                # Process events to keep UI responsive
                from PySide6.QtCore import QCoreApplication
                QCoreApplication.processEvents()

            # Check results
            if not result['completed']:
                print(f"🔧 Generation timed out after {timeout_seconds} seconds")
                self._set_status(f"Generation timed out after {timeout_seconds} seconds", "error")
                self.progress_bar.setVisible(False)
                self.generate_button.setEnabled(True)
                QMessageBox.critical(self, "Generation Timeout",
                                     f"Cue generation took longer than {timeout_seconds} seconds and was cancelled.\n"
                                     "This may indicate too many peaks or a processing issue.")
                return

            if result['error']:
                raise Exception(result['error'])

            cues = result['cues']

            if not cues:
                self._set_status("No cues generated - check peak selection", "error")
                self.progress_bar.setVisible(False)
                self.generate_button.setEnabled(True)
                return

            print(f"🔧 Generated {len(cues)} cues, updating table")

            # Update progress for table operations
            self._set_status(f"Clearing existing cues...", "processing")

            # Clear existing cues from table
            self._clear_cue_table()

            # Update progress for adding cues
            self._set_status(f"Adding {len(cues)} cues to table...", "processing")

            # Add new cues to table
            self._add_cues_to_table(cues)

            # Store generated cues
            self.last_generated_cues = cues

            self._set_status(f"Generated {len(cues)} cues successfully", "success")
            self.progress_bar.setVisible(False)
            self.generate_button.setEnabled(True)

            # Emit signal
            self.cues_generated.emit([cue.to_table_format() for cue in cues])

        except Exception as e:
            print(f"🔧 Error in _on_generate_clicked: {e}")
            self._set_status(f"Error generating cues: {str(e)}", "error")
            self.progress_bar.setVisible(False)
            self.generate_button.setEnabled(True)
            QMessageBox.critical(self, "Generation Error", f"Failed to generate cues:\n{str(e)}")

    def _generate_cues(self) -> List[GeneratedCue]:
        """Generate cues based on current settings"""
        # Collect peaks based on selection
        peaks = self._collect_selected_peaks()

        if not peaks:
            return []

        # Validate peak count against limits
        if len(peaks) > 1000:
            raise ValueError(f"Cannot generate {len(peaks)} cues. Maximum limit is 1000 cues total.")

        # Get settings
        distribution_method = self.distribution_combo.currentText()
        time_offset_ms = self.time_offset_spinbox.value()
        time_offset_seconds = time_offset_ms / 1000.0

        # Generate output assignments (ensures uniqueness and limits)
        # Pass the peaks to the output assignment method so it can handle double shot cues
        output_assignments = self._generate_output_assignments(len(peaks), distribution_method, peaks)

        # Validate that we have the right number of assignments
        if len(output_assignments) != len(peaks):
            raise ValueError(
                f"Output assignment mismatch: {len(output_assignments)} assignments for {len(peaks)} peaks")

        # Create cues
        cues = []
        for i, (peak, output) in enumerate(zip(peaks, output_assignments)):
            # Calculate execute time with offset
            execute_time = peak['time'] + time_offset_seconds

            # Ensure execute time is not negative
            execute_time = max(0.0, execute_time)

            # Determine cue type based on double shot flag
            cue_type = "DOUBLE SHOT" if peak.get('is_double_shot', False) else "SINGLE SHOT"

            cue = GeneratedCue(
                cue_number=i + 1,  # Start from 1
                cue_type=cue_type,
                output=output,  # This can now be either an int or a list of ints
                delay=0.0,  # Single shot cues have no delay
                execute_time=execute_time
            )
            cues.append(cue)

        return cues

    def _collect_selected_peaks(self) -> List[Dict[str, Any]]:
        """Collect peaks based on checkbox selections"""
        peaks = []

        # Collect detected peaks
        if self.detected_peaks_checkbox.isChecked():
            detected_peaks = self._get_detected_peaks()
            peaks.extend(detected_peaks)

        # Collect manual peaks
        if self.manual_peaks_checkbox.isChecked():
            manual_peaks = self._get_manual_peaks()
            peaks.extend(manual_peaks)

        # Sort by time
        peaks.sort(key=lambda x: x['time'])

        return peaks

    def _get_detected_peaks(self) -> List[Dict[str, Any]]:
        """Get detected peaks from analyzer with safety checks"""
        print(f"🔧 _get_detected_peaks called")

        # Only try to get detected peaks if analyzer exists and has been analyzed
        if not self.analyzer or not hasattr(self.analyzer, 'get_peak_data'):
            print(f"🔧 No analyzer or get_peak_data method available")
            return []

        # Check if analyzer has actually been run (has peaks)
        if not getattr(self.analyzer, 'is_analyzed', False):
            print(f"🔧 Analyzer exists but hasn't been analyzed yet")
            return []

        try:
            print(f"🔧 Getting peak data from analyzer...")
            analyzer_peaks = self.analyzer.get_peak_data()

            if not analyzer_peaks:
                print(f"🔧 Analyzer has no peak data")
                return []

            print(f"🔧 Got {len(analyzer_peaks)} peaks from analyzer")

            # Safety check: limit processing to prevent freeze
            if len(analyzer_peaks) > 10000:
                print(f"🔧 WARNING: Too many peaks ({len(analyzer_peaks)}), limiting to 10000")
                analyzer_peaks = analyzer_peaks[:10000]

            # Convert to standard format with progress tracking
            peaks = []
            total_peaks = len(analyzer_peaks)

            for i, peak in enumerate(analyzer_peaks):
                # Progress indicator for large datasets
                if i > 0 and i % 1000 == 0:
                    print(f"🔧 Processing peak {i}/{total_peaks}")

                # Safety check: ensure peak has required attributes
                if not hasattr(peak, 'time') or not hasattr(peak, 'amplitude'):
                    print(f"🔧 WARNING: Peak {i} missing required attributes, skipping")
                    continue

                # Safety check: ensure time is valid
                if not isinstance(peak.time, (int, float)) or peak.time < 0:
                    print(f"🔧 WARNING: Peak {i} has invalid time {peak.time}, skipping")
                    continue

                # Check if this peak is marked as a double shot
                is_double_shot = False
                if self.waveform_view and hasattr(self.waveform_view, 'double_shot_peaks'):
                    # Use peak's time value as the identifier
                    is_double_shot = peak.time in self.waveform_view.double_shot_peaks

                peak_data = {
                    'time': float(peak.time),  # Ensure it's a float
                    'amplitude': float(peak.amplitude),  # Ensure it's a float
                    'type': 'detected',
                    'is_double_shot': is_double_shot  # Add double shot flag
                }
                peaks.append(peak_data)

                # Safety break for extremely large datasets
                if len(peaks) >= 5000:
                    print(f"🔧 WARNING: Reached peak limit (5000), stopping processing")
                    break

            print(f"🔧 Converted {len(peaks)} detected peaks to standard format")

            # Filter out hidden peaks if waveform_view is available
            if self.waveform_view and hasattr(self.waveform_view, 'hidden_detected_peaks'):
                print(f"🔧 Filtering hidden peaks...")
                original_count = len(peaks)
                filtered_peaks = []

                for i, peak in enumerate(peaks):
                    if i not in self.waveform_view.hidden_detected_peaks:
                        filtered_peaks.append(peak)

                    # Safety check during filtering
                    if i > 0 and i % 1000 == 0:
                        print(f"🔧 Filtering peak {i}/{original_count}")

                peaks = filtered_peaks
                print(f"🔧 Filtered from {original_count} to {len(peaks)} peaks")

            print(f"🔧 Retrieved {len(peaks)} detected peaks successfully")
            return peaks

        except Exception as e:
            print(f"🔧 Error getting detected peaks: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _get_manual_peaks(self) -> List[Dict[str, Any]]:
        """Get manual peaks from waveform view"""
        if not self.waveform_view or not hasattr(self.waveform_view, 'manual_peaks'):
            print(f"🔧 No waveform_view or manual_peaks attribute")
            return []

        try:
            manual_peaks = self.waveform_view.manual_peaks
            if not manual_peaks:
                print(f"🔧 No manual peaks found")
                return []

            print(f"🔧 Found {len(manual_peaks)} manual peaks")

            # Convert to standard format
            peaks = []
            for i, peak in enumerate(manual_peaks):
                # Manual peaks store position in samples, convert to time
                if hasattr(peak, 'position'):
                    if self.analyzer and hasattr(self.analyzer, 'sample_rate') and self.analyzer.sample_rate > 0:
                        # Convert samples to seconds using analyzer sample rate
                        time_seconds = peak.position / self.analyzer.sample_rate
                        print(f"🔧 Manual peak {i}: position={peak.position} samples, time={time_seconds:.4f}s")
                    else:
                        # No analyzer or sample rate, assume position is in seconds
                        time_seconds = peak.position
                        print(f"🔧 Manual peak {i}: assuming position={peak.position} is in seconds")
                else:
                    # Fallback to time attribute or default
                    time_seconds = getattr(peak, 'time', 0)
                    print(f"🔧 Manual peak {i}: using time attribute={time_seconds}s")

                # Check if this manual peak is marked as double shot
                is_double_shot = False
                if hasattr(self.waveform_view, 'double_shot_peaks'):
                    # Use peak's time value as the identifier
                    manual_peak_id = f"m{time_seconds}"
                    is_double_shot = manual_peak_id in self.waveform_view.double_shot_peaks

                peak_data = {
                    'time': time_seconds,
                    'amplitude': getattr(peak, 'amplitude', 0.5),
                    'type': 'manual',
                    'is_double_shot': is_double_shot  # Add double shot flag
                }
                peaks.append(peak_data)

            print(f"🔧 Converted {len(peaks)} manual peaks to standard format")
            return peaks

        except Exception as e:
            print(f"Error getting manual peaks: {e}")
            return []

    def _generate_output_assignments(self, num_peaks: int, method: str, peaks: List[Dict[str, Any]]) -> List[Union[int, List[int]]]:
        """
        Generate output assignments based on distribution method

        Args:
            num_peaks: Number of peaks to assign outputs to
            method: Distribution method ("Random" or "Sequential")
            peaks: List of peak data dictionaries

        Returns:
            List of output assignments (int for single shot, list of ints for double shot)
        """
        # Count how many double shot peaks we have
        double_shot_count = sum(1 for peak in peaks if peak.get('is_double_shot', False))
        single_shot_count = num_peaks - double_shot_count

        # Calculate total outputs needed (1 per single shot, 2 per double shot)
        total_outputs_needed = single_shot_count + (double_shot_count * 2)

        # Enforce 1000 output limit
        if total_outputs_needed > 1000:
            raise ValueError(f"Cannot generate cues requiring {total_outputs_needed} outputs. Maximum limit is 1000 outputs total.")

        # Generate the base output numbers
        if method == "Random":
            # Random distribution from 1 to N (where N = total_outputs_needed)
            available_outputs = list(range(1, total_outputs_needed + 1))
            random.shuffle(available_outputs)
        else:  # Sequential or default
            # Sequential distribution from 1 to N
            available_outputs = list(range(1, total_outputs_needed + 1))

        # Assign outputs to peaks
        assignments = []
        output_index = 0

        for peak in peaks:
            if peak.get('is_double_shot', False):
                # Double shot gets two consecutive outputs
                if output_index + 1 < len(available_outputs):
                    # Assign two outputs
                    assignments.append([available_outputs[output_index], available_outputs[output_index + 1]])
                    output_index += 2
                else:
                    # Not enough outputs left, fallback to single output
                    assignments.append(available_outputs[output_index])
                    output_index += 1
            else:
                # Single shot gets one output
                assignments.append(available_outputs[output_index])
                output_index += 1

            # Safety check to prevent index out of range
            if output_index >= len(available_outputs):
                break

        return assignments

    def _clear_cue_table(self):
        """Clear existing cues from the cue table"""
        if self.cue_table and hasattr(self.cue_table, 'delete_all_cues'):
            self.cue_table.delete_all_cues()

    def _add_cues_to_table(self, cues: List[GeneratedCue]):
        """Add generated cues to the cue table"""
        if not self.cue_table or not hasattr(self.cue_table, 'model'):
            return

        # Convert all cues to table format
        cue_data_list = [cue.to_table_format() for cue in cues]

        # Use batch insertion if available, otherwise fall back to individual insertion
        if hasattr(self.cue_table.model, 'add_cues_batch'):
            self.cue_table.model.add_cues_batch(cue_data_list)
        else:
            # Fallback to individual insertion (less efficient)
            for cue_data in cue_data_list:
                self.cue_table.model.add_cue(cue_data)

    def _on_save_clicked(self):
        """Handle save button click"""
        try:
            # Use parent dialog's save method if available
            if self.parent() and hasattr(self.parent(), 'save_waveform_state'):
                success = self.parent().save_waveform_state()
                if success:
                    self._set_status("Waveform state saved successfully", "success")
                else:
                    self._set_status("Failed to save waveform state", "error")
            else:
                # Fallback to generator-only save
                self._save_generator_only()

        except Exception as e:
            self._set_status(f"Error saving state: {str(e)}", "error")
            QMessageBox.critical(self, "Save Error", f"Failed to save state:\n{str(e)}")

    def _on_load_clicked(self):
        """Handle load button click"""
        try:
            # Use parent dialog's load method if available
            if self.parent() and hasattr(self.parent(), 'load_waveform_state'):
                success = self.parent().load_waveform_state()
                if success:
                    self._set_status("Waveform state loaded successfully", "success")
                    self._update_status()  # Refresh generator status
                else:
                    self._set_status("Failed to load waveform state", "error")
            else:
                # Fallback to generator-only load
                self._load_generator_only()

        except Exception as e:
            self._set_status(f"Error loading state: {str(e)}", "error")
            QMessageBox.critical(self, "Load Error", f"Failed to load state:\n{str(e)}")

    def _save_generator_only(self):
        """Fallback method to save generator state only"""
        from PySide6.QtWidgets import QFileDialog

        # Get save file path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Generator State",
            "generator_state.json",
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        # Collect current state
        state = self._collect_current_state()

        # Save to file using safe JSON serialization
        try:
            from json_utils import safe_json_dumps
            json_string = safe_json_dumps(state, indent=2)
            with open(file_path, 'w') as f:
                f.write(json_string)
        except ImportError:
            # Fallback to standard JSON with manual type conversion
            import json
            import numpy as np

            def convert_numpy_types(obj):
                if isinstance(obj, dict):
                    return {key: convert_numpy_types(value) for key, value in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(item) for item in obj]
                elif isinstance(obj, (np.integer, np.signedinteger, np.unsignedinteger)):
                    return int(obj)
                elif isinstance(obj, (np.floating, np.float16, np.float32, np.float64)):
                    return float(obj)
                elif isinstance(obj, np.bool_):
                    return bool(obj)
                elif hasattr(obj, 'dtype'):
                    if hasattr(obj, 'item'):
                        return obj.item()
                    elif hasattr(obj, 'tolist'):
                        return obj.tolist()
                    else:
                        return str(obj)
                else:
                    return obj

            cleaned_state = convert_numpy_types(state)
            with open(file_path, 'w') as f:
                json.dump(cleaned_state, f, indent=2)

        self._set_status(f"Generator state saved to {os.path.basename(file_path)}", "success")
        self.state_saved.emit(file_path)

    def _load_generator_only(self):
        """Fallback method to load generator state only"""
        from PySide6.QtWidgets import QFileDialog

        # Get load file path
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Generator State",
            "",
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        # Load from file
        with open(file_path, 'r') as f:
            state = json.load(f)

        # Apply loaded state
        self._apply_loaded_state(state)

        self._set_status(f"Generator state loaded from {os.path.basename(file_path)}", "success")
        self.state_loaded.emit(state)

    def _collect_current_state(self) -> Dict[str, Any]:
        """Collect current generator state"""
        state = {
            'version': '1.0',
            'timestamp': str(QTimer().remainingTime()),  # Simple timestamp
            'settings': {
                'distribution_method': self.distribution_combo.currentText(),
                'time_offset_ms': float(self.time_offset_spinbox.value()),  # Ensure it's a Python float
                'include_detected_peaks': self.detected_peaks_checkbox.isChecked(),
                'include_manual_peaks': self.manual_peaks_checkbox.isChecked()
            },
            'waveform_state': self._collect_waveform_state(),
            'last_generated_cues': [cue.__dict__ for cue in self.last_generated_cues]
        }

        return state

    def _collect_waveform_state(self) -> Dict[str, Any]:
        """Collect waveform analysis state"""
        waveform_state = {
            'analyzer_available': self.analyzer is not None,
            'detected_peak_count': self._get_detected_peak_count(),
            'manual_peak_count': self._get_manual_peak_count()
        }

        # Add double shot mode and peaks if available
        if self.waveform_view:
            if hasattr(self.waveform_view, 'double_shot_mode'):
                waveform_state['double_shot_mode'] = self.waveform_view.double_shot_mode

            if hasattr(self.waveform_view, 'double_shot_peaks'):
                # Convert set to list for JSON serialization
                waveform_state['double_shot_peaks'] = list(self.waveform_view.double_shot_peaks)

        # Add analyzer info if available
        if self.analyzer:
            try:
                from json_utils import clean_data_for_json
                waveform_state.update({
                    'filename': getattr(self.analyzer, 'filename', 'unknown'),
                    'duration_seconds': clean_data_for_json(getattr(self.analyzer, 'duration_seconds', 0)),
                    'sample_rate': clean_data_for_json(getattr(self.analyzer, 'sample_rate', 0)),
                    'is_analyzed': getattr(self.analyzer, 'is_analyzed', False)
                })
            except ImportError:
                # Fallback without json_utils
                import numpy as np
                duration = getattr(self.analyzer, 'duration_seconds', 0)
                sample_rate = getattr(self.analyzer, 'sample_rate', 0)

                # Convert numpy types manually
                if isinstance(duration, (np.floating, np.float16, np.float32, np.float64)):
                    duration = float(duration)
                if isinstance(sample_rate, (np.integer, np.signedinteger, np.unsignedinteger)):
                    sample_rate = int(sample_rate)

                waveform_state.update({
                    'filename': getattr(self.analyzer, 'filename', 'unknown'),
                    'duration_seconds': duration,
                    'sample_rate': sample_rate,
                    'is_analyzed': getattr(self.analyzer, 'is_analyzed', False)
                })

        # Add manual peaks data if available
        if self.waveform_view and hasattr(self.waveform_view, 'manual_peaks'):
            manual_peaks_data = []
            for peak in self.waveform_view.manual_peaks:
                try:
                    from json_utils import clean_data_for_json
                    peak_data = {
                        'position': clean_data_for_json(getattr(peak, 'position', 0)),
                        'amplitude': clean_data_for_json(getattr(peak, 'amplitude', 0.5)),
                        'time': clean_data_for_json(getattr(peak, 'time', 0))
                    }
                except ImportError:
                    # Fallback without json_utils
                    import numpy as np
                    position = getattr(peak, 'position', 0)
                    amplitude = getattr(peak, 'amplitude', 0.5)
                    time = getattr(peak, 'time', 0)

                    # Convert numpy types manually
                    if isinstance(position, (np.integer, np.signedinteger, np.unsignedinteger)):
                        position = int(position)
                    if isinstance(amplitude, (np.floating, np.float16, np.float32, np.float64)):
                        amplitude = float(amplitude)
                    if isinstance(time, (np.floating, np.float16, np.float32, np.float64)):
                        time = float(time)

                    peak_data = {
                        'position': position,
                        'amplitude': amplitude,
                        'time': time
                    }
                manual_peaks_data.append(peak_data)
            waveform_state['manual_peaks_data'] = manual_peaks_data

        return waveform_state

    def _apply_loaded_state(self, state: Dict[str, Any]):
        """Apply loaded state to the generator"""
        settings = state.get('settings', {})

        # Apply settings
        if 'distribution_method' in settings:
            self.distribution_combo.setCurrentText(settings['distribution_method'])

        if 'time_offset_ms' in settings:
            self.time_offset_spinbox.setValue(settings['time_offset_ms'])

        if 'include_detected_peaks' in settings:
            self.detected_peaks_checkbox.setChecked(settings['include_detected_peaks'])

        if 'include_manual_peaks' in settings:
            self.manual_peaks_checkbox.setChecked(settings['include_manual_peaks'])

        # Restore last generated cues if available
        if 'last_generated_cues' in state:
            cue_dicts = state['last_generated_cues']
            self.last_generated_cues = [
                GeneratedCue(**cue_dict) for cue_dict in cue_dicts
            ]

        # Restore manual peaks to waveform widget
        self._restore_manual_peaks_to_waveform(state)

        self._update_status()

    def _restore_manual_peaks_to_waveform(self, state: Dict[str, Any]):
        """Restore manual peaks to the waveform widget"""
        try:
            # Get waveform state and manual peaks data
            waveform_state = state.get('waveform_state', {})
            manual_peaks_data = waveform_state.get('manual_peaks_data', [])

            if not manual_peaks_data:
                return

            # Check if we have access to the waveform widget
            if not self.waveform_view or not hasattr(self.waveform_view, 'manual_peaks'):
                print("⚠️  No waveform widget available for manual peak restoration")
                return

            print(f"🔧 Restoring {len(manual_peaks_data)} manual peaks to waveform widget...")

            # Clear existing manual peaks
            self.waveform_view.manual_peaks = []

            # Create Peak namedtuple (same structure as in waveform widget)
            from collections import namedtuple
            Peak = namedtuple('Peak', ['position', 'time', 'amplitude', 'segment', 'is_manual'])

            # Restore each manual peak
            restored_count = 0
            for peak_data in manual_peaks_data:
                try:
                    # Calculate segment if not provided (fallback)
                    segment = peak_data.get('segment', 0)
                    if segment == 0 and hasattr(self.waveform_view, '_calculate_segment_for_amplitude'):
                        amplitude = float(peak_data.get('amplitude', 0.0))
                        segment = self.waveform_view._calculate_segment_for_amplitude(amplitude)

                    manual_peak = Peak(
                        position=int(peak_data.get('position', 0)),
                        time=float(peak_data.get('time', 0.0)),
                        amplitude=float(peak_data.get('amplitude', 0.0)),
                        segment=int(segment),
                        is_manual=True
                    )

                    self.waveform_view.manual_peaks.append(manual_peak)
                    restored_count += 1

                    print(
                        f"   Restored peak: pos={manual_peak.position}, time={manual_peak.time:.3f}s, amp={manual_peak.amplitude:.3f}")

                except Exception as e:
                    print(f"   ⚠️  Failed to restore peak {peak_data}: {e}")
                    continue

            # Restore double shot mode and peaks if available
            if hasattr(self.waveform_view, 'set_double_shot_mode') and 'double_shot_mode' in waveform_state:
                self.waveform_view.set_double_shot_mode(waveform_state['double_shot_mode'])
                print(f"🔧 Restored double shot mode: {waveform_state['double_shot_mode']}")

            if hasattr(self.waveform_view, 'double_shot_peaks') and 'double_shot_peaks' in waveform_state:
                # Convert list back to set
                self.waveform_view.double_shot_peaks = set(waveform_state['double_shot_peaks'])
                print(f"🔧 Restored {len(self.waveform_view.double_shot_peaks)} double shot peaks")

            if restored_count > 0:
                # Trigger widget update to show the peaks
                self.waveform_view.update()

                # Emit signal to update peak count
                if hasattr(self.waveform_view, 'peak_selection_changed'):
                    self.waveform_view.peak_selection_changed.emit()

                print(f"✅ Successfully restored {restored_count} manual peaks to waveform widget")
            else:
                print("❌ No manual peaks were successfully restored")

        except Exception as e:
            print(f"❌ Error restoring manual peaks to waveform: {e}")
            import traceback
            traceback.print_exc()

    def _set_status(self, message: str, status_type: str = "info"):
        """Set status message with appropriate styling"""
        colors = {
            "success": "#2ecc71",
            "error": "#e74c3c",
            "processing": "#f39c12",
            "info": "#3498db"
        }

        color = colors.get(status_type, colors["info"])
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def update_peak_counts(self):
        """Update the generator when peak counts change"""
        self._update_status()
