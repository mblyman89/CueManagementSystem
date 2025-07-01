from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QMessageBox, QSpinBox, QGroupBox, QFormLayout, QDialogButtonBox,
                               QComboBox, QGridLayout, QSlider, QTabWidget, QWidget, QCheckBox,
                               QDoubleSpinBox, QScrollArea, QFrame, QRadioButton, QButtonGroup,
                               QTextEdit)
from PySide6.QtCore import Qt, Signal
from utils.show_enums import ShowStyle, RhythmPattern, ComplexityLevel


class ShowConfigData:
    """Container for show configuration data"""

    def __init__(self, duration_minutes=0, duration_seconds=0, num_outputs=100, section_intensities=None):
        self.duration_minutes = duration_minutes
        self.duration_seconds = duration_seconds
        self.num_outputs = num_outputs
        # Default to balanced intensities if none provided
        self.section_intensities = section_intensities or [20, 20, 20, 20, 20]

        # New attributes for professional generator
        self.generator_type = "original"  # "original" or "professional"
        self.professional_config = None

    @property
    def total_seconds(self):
        """Get the total duration in seconds"""
        return (self.duration_minutes * 60) + self.duration_seconds

    def get_outputs_for_section(self, section_index):
        """Calculate how many outputs should be in the given section"""
        if section_index < 0 or section_index >= len(self.section_intensities):
            return 0

        percentage = self.section_intensities[section_index]
        return int((percentage / 100.0) * self.num_outputs)

    def is_professional(self):
        """Check if this configuration is for the professional generator"""
        return self.generator_type == "professional"

    def get_professional_config(self):
        """Get the professional configuration dictionary"""
        return self.professional_config if self.professional_config else {}


class RandomShowConfigDialog(QDialog):
    """Dialog for configuring random show parameters"""

    # Signal emitted when configuration is complete
    config_completed = Signal(ShowConfigData)

    # Intensity pattern presets
    INTENSITY_PRESETS = {
        "Balanced": [20, 20, 20, 20, 20],
        "Slow Build": [10, 15, 20, 25, 30],
        "Rapid Start": [30, 25, 20, 15, 10],
        "V-Shape": [25, 15, 10, 15, 35],
        "Finale Heavy": [10, 10, 20, 20, 40],
        "Custom": None  # Will be set by user
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Random Show Configuration")
        self.setMinimumWidth(500)
        self.section_sliders = []
        self.section_labels = []
        self.updating_sliders = False
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components with tabbed interface"""
        # Main layout
        main_layout = QVBoxLayout(self)

        # Title/description
        title_label = QLabel("Configure your show")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Create tabs
        self.create_basic_tab()
        self.create_professional_tab()
        self.create_rhythm_tab()
        self.create_advanced_tab()
        self.create_presets_tab()

        # Buttons
        button_layout = QHBoxLayout()

        # Generator type selection
        self.generator_group = QButtonGroup()
        self.use_original = QRadioButton("Use Original Generator")
        self.use_professional = QRadioButton("Use Professional Generator")
        self.use_original.setChecked(True)  # Default to original

        self.generator_group.addButton(self.use_original)
        self.generator_group.addButton(self.use_professional)

        button_layout.addWidget(self.use_original)
        button_layout.addWidget(self.use_professional)
        button_layout.addStretch()

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        button_layout.addWidget(button_box)

        main_layout.addLayout(button_layout)

        # Set spacing and margins
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Initialize with balanced preset
        self.apply_preset("Balanced")

    def create_basic_tab(self):
        """Create the basic settings tab (original functionality)"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Description
        description = QLabel("Original show generator settings - specify duration, outputs, and intensity pattern.")
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(description)

        # Duration group
        duration_group = QGroupBox("Show Duration")
        duration_layout = QFormLayout()

        # Minutes input
        self.minutes_input = QSpinBox()
        self.minutes_input.setRange(0, 60)
        self.minutes_input.setValue(5)  # Default 5 minutes
        self.minutes_input.setSuffix(" minutes")
        duration_layout.addRow("Minutes:", self.minutes_input)

        # Seconds input
        self.seconds_input = QSpinBox()
        self.seconds_input.setRange(0, 59)
        self.seconds_input.setValue(0)  # Default 0 seconds
        self.seconds_input.setSuffix(" seconds")
        duration_layout.addRow("Seconds:", self.seconds_input)

        duration_group.setLayout(duration_layout)
        layout.addWidget(duration_group)

        # Output configuration group
        output_group = QGroupBox("Output Configuration")
        output_layout = QFormLayout()

        # Number of outputs
        self.num_outputs = QSpinBox()
        self.num_outputs.setRange(1, 1000)
        self.num_outputs.setValue(100)  # Default 100 outputs
        self.num_outputs.setSuffix(" outputs")
        output_layout.addRow("Number of outputs:", self.num_outputs)

        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # Intensity pattern group
        intensity_group = QGroupBox("Intensity Pattern")
        intensity_layout = QVBoxLayout()

        # Preset selector
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Pattern Preset:")
        self.preset_combo = QComboBox()
        for preset_name in self.INTENSITY_PRESETS:
            self.preset_combo.addItem(preset_name)
        self.preset_combo.currentTextChanged.connect(self.apply_preset)
        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(self.preset_combo)
        intensity_layout.addLayout(preset_layout)

        # Section intensity sliders
        sections_layout = QGridLayout()
        sections_layout.addWidget(QLabel("Section"), 0, 0)
        sections_layout.addWidget(QLabel("Intensity (%)"), 0, 1)
        sections_layout.addWidget(QLabel("Outputs"), 0, 2)

        # Create 5 sliders for the sections
        for i in range(5):
            # Section label
            section_label = QLabel(f"Section {i + 1}")
            sections_layout.addWidget(section_label, i + 1, 0)

            # Slider for percentage
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(20)  # Default balanced
            slider.setTickPosition(QSlider.TicksBelow)
            slider.setTickInterval(10)
            slider.valueChanged.connect(lambda val, idx=i: self.update_section_percentage(idx, val))
            sections_layout.addWidget(slider, i + 1, 1)
            self.section_sliders.append(slider)

            # Label for percentage and outputs
            value_label = QLabel("20% (20 outputs)")
            sections_layout.addWidget(value_label, i + 1, 2)
            self.section_labels.append(value_label)

        # Totals row
        sections_layout.addWidget(QLabel("Total:"), 6, 0)
        self.total_percentage_label = QLabel("100%")
        sections_layout.addWidget(self.total_percentage_label, 6, 1)
        self.total_outputs_label = QLabel("100 outputs")
        sections_layout.addWidget(self.total_outputs_label, 6, 2)

        intensity_layout.addLayout(sections_layout)

        # Warning label for percentages
        self.percentage_warning = QLabel("")
        self.percentage_warning.setStyleSheet("color: red;")
        intensity_layout.addWidget(self.percentage_warning)

        intensity_group.setLayout(intensity_layout)
        layout.addWidget(intensity_group)

        # Validation note
        validation_note = QLabel("Note: Show must have a duration of at least 10 seconds.")
        validation_note.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(validation_note)

        self.tab_widget.addTab(tab, "Basic Settings")

    def create_professional_tab(self):
        """Create the professional settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Description
        description = QLabel("Professional show generator with advanced choreography and timing.")
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(description)

        # Professional Duration
        prof_duration_group = QGroupBox("Professional Duration")
        prof_duration_layout = QFormLayout()

        self.prof_duration = QDoubleSpinBox()
        self.prof_duration.setRange(30.0, 1800.0)
        self.prof_duration.setValue(180.0)
        self.prof_duration.setSuffix(" seconds")
        prof_duration_layout.addRow("Show Duration:", self.prof_duration)

        self.prof_outputs = QSpinBox()
        self.prof_outputs.setRange(10, 1000)
        self.prof_outputs.setValue(32)
        prof_duration_layout.addRow("Number of Outputs:", self.prof_outputs)

        prof_duration_group.setLayout(prof_duration_layout)
        layout.addWidget(prof_duration_group)

        # Show Style
        style_group = QGroupBox("Show Style")
        style_layout = QFormLayout()

        self.style_combo = QComboBox()
        for style in ShowStyle:
            display_name = style.value.replace('_', ' ').title()
            self.style_combo.addItem(display_name, style.value)
        self.style_combo.setCurrentText("Classical")
        style_layout.addRow("Style:", self.style_combo)

        self.complexity_combo = QComboBox()
        for complexity in ComplexityLevel:
            display_name = complexity.value.title()
            self.complexity_combo.addItem(display_name, complexity.value)
        self.complexity_combo.setCurrentText("Medium")
        style_layout.addRow("Complexity:", self.complexity_combo)

        style_group.setLayout(style_layout)
        layout.addWidget(style_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Professional")

    def create_rhythm_tab(self):
        """Create the rhythm and timing tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Description
        description = QLabel("Configure rhythm patterns and timing for professional choreography.")
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(description)

        # Rhythm Settings
        rhythm_group = QGroupBox("Rhythm & Timing")
        rhythm_layout = QFormLayout()

        self.rhythm_combo = QComboBox()
        for rhythm in RhythmPattern:
            display_name = rhythm.value.replace('_', ' ').title()
            self.rhythm_combo.addItem(display_name, rhythm.value)
        self.rhythm_combo.setCurrentText("Waltz")
        rhythm_layout.addRow("Rhythm Pattern:", self.rhythm_combo)

        self.bpm_spin = QSpinBox()
        self.bpm_spin.setRange(60, 200)
        self.bpm_spin.setValue(120)
        self.bpm_spin.setSuffix(" BPM")
        rhythm_layout.addRow("Beats Per Minute:", self.bpm_spin)

        self.timing_precision = QDoubleSpinBox()
        self.timing_precision.setRange(0.01, 1.0)
        self.timing_precision.setValue(0.1)
        self.timing_precision.setSuffix(" seconds")
        rhythm_layout.addRow("Timing Precision:", self.timing_precision)

        rhythm_group.setLayout(rhythm_layout)
        layout.addWidget(rhythm_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Rhythm & Timing")

    def create_advanced_tab(self):
        """Create the advanced options tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Description
        description = QLabel("Advanced professional options for expert-level shows.")
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(description)

        # Advanced Options
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QVBoxLayout()

        self.use_crescendo = QCheckBox("Use Crescendo Effects")
        self.use_crescendo.setChecked(True)
        advanced_layout.addWidget(self.use_crescendo)

        self.smart_timing = QCheckBox("Smart Timing Adjustments")
        self.smart_timing.setChecked(True)
        advanced_layout.addWidget(self.smart_timing)

        self.professional_validation = QCheckBox("Professional Validation")
        self.professional_validation.setChecked(True)
        advanced_layout.addWidget(self.professional_validation)

        self.mathematical_precision = QCheckBox("Mathematical Precision Timing")
        self.mathematical_precision.setChecked(True)
        advanced_layout.addWidget(self.mathematical_precision)

        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Advanced Options")

    def create_presets_tab(self):
        """Create the presets tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Description
        description = QLabel("Quick presets for common show types and configurations.")
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(description)

        # Professional Presets
        presets_group = QGroupBox("Professional Presets")
        presets_layout = QVBoxLayout()

        preset_buttons = [
            ("Competition Standard", "High complexity, technical showcase, 180s"),
            ("Wedding Elegant", "Classical style, waltz rhythm, 120s"),
            ("Corporate Professional", "Balanced, corporate style, 150s"),
            ("Rock Concert Energy", "High energy, rock drumming, 240s"),
            ("Patriotic Display", "Marching rhythm, patriotic style, 180s")
        ]

        for preset_name, description in preset_buttons:
            btn = QPushButton(f"{preset_name}")
            btn.setToolTip(description)
            btn.clicked.connect(lambda checked, name=preset_name: self.apply_professional_preset(name))
            presets_layout.addWidget(btn)

        presets_group.setLayout(presets_layout)
        layout.addWidget(presets_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Presets")

    def apply_professional_preset(self, preset_name):
        """Apply a professional preset configuration"""
        presets = {
            "Competition Standard": {
                'duration': 180.0,
                'outputs': 64,
                'style': 'competition',
                'complexity': 'expert',
                'rhythm': 'drumming_jazz',
                'bpm': 140
            },
            "Wedding Elegant": {
                'duration': 120.0,
                'outputs': 32,
                'style': 'wedding',
                'complexity': 'medium',
                'rhythm': 'waltz',
                'bpm': 100
            },
            "Corporate Professional": {
                'duration': 150.0,
                'outputs': 48,
                'style': 'corporate',
                'complexity': 'medium',
                'rhythm': 'marching',
                'bpm': 120
            },
            "Rock Concert Energy": {
                'duration': 240.0,
                'outputs': 96,
                'style': 'rock_concert',
                'complexity': 'complex',
                'rhythm': 'drumming_rock',
                'bpm': 160
            },
            "Patriotic Display": {
                'duration': 180.0,
                'outputs': 64,
                'style': 'patriotic',
                'complexity': 'complex',
                'rhythm': 'marching',
                'bpm': 120
            }
        }

        if preset_name in presets:
            preset = presets[preset_name]

            # Apply professional settings
            self.prof_duration.setValue(preset['duration'])
            self.prof_outputs.setValue(preset['outputs'])

            # Set style
            for i in range(self.style_combo.count()):
                if self.style_combo.itemData(i) == preset['style']:
                    self.style_combo.setCurrentIndex(i)
                    break

            # Set complexity
            for i in range(self.complexity_combo.count()):
                if self.complexity_combo.itemData(i) == preset['complexity']:
                    self.complexity_combo.setCurrentIndex(i)
                    break

            # Set rhythm
            for i in range(self.rhythm_combo.count()):
                if self.rhythm_combo.itemData(i) == preset['rhythm']:
                    self.rhythm_combo.setCurrentIndex(i)
                    break

            # Set BPM
            self.bpm_spin.setValue(preset['bpm'])

            # Switch to professional generator
            self.use_professional.setChecked(True)

    def apply_preset(self, preset_name):
        """Apply a predefined intensity preset"""
        if preset_name not in self.INTENSITY_PRESETS or preset_name == "Custom":
            return

        # Prevent recursive slider updates
        self.updating_sliders = True

        # Get the preset values
        percentages = self.INTENSITY_PRESETS[preset_name]

        # Update sliders with preset values
        for i, slider in enumerate(self.section_sliders):
            if i < len(percentages):
                slider.setValue(percentages[i])

        self.updating_sliders = False

        # Update all labels
        self.update_all_labels()

    def update_section_percentage(self, section_index, value):
        """Update the percentage for a section and adjust other sections if needed"""
        if self.updating_sliders:
            return

        # Switch to custom preset
        self.preset_combo.setCurrentText("Custom")

        # Update labels
        self.update_all_labels()

    def update_all_labels(self):
        """Update all percentage and output labels"""
        total_percentage = 0
        total_outputs = 0
        num_outputs = self.num_outputs.value()

        # Calculate current percentages and outputs
        percentages = []
        for i, slider in enumerate(self.section_sliders):
            percentage = slider.value()
            percentages.append(percentage)
            total_percentage += percentage

            # Calculate outputs for this section
            section_outputs = int((percentage / 100.0) * num_outputs)
            total_outputs += section_outputs

            # Update label
            self.section_labels[i].setText(f"{percentage}% ({section_outputs} outputs)")

        # Update total labels
        self.total_percentage_label.setText(f"{total_percentage}%")
        self.total_outputs_label.setText(f"{total_outputs} outputs")

        # Check if percentages add up to 100%
        if total_percentage != 100:
            self.percentage_warning.setText(f"Warning: Percentages add up to {total_percentage}%, not 100%")
        else:
            self.percentage_warning.setText("")

        # Store current percentages as custom preset
        self.INTENSITY_PRESETS["Custom"] = percentages

    def normalize_percentages(self):
        """Normalize percentages to ensure they add up to 100%"""
        total = 0
        percentages = []

        # Get current values
        for slider in self.section_sliders:
            percentages.append(slider.value())
            total += slider.value()

        # If total is 0, set equal distribution
        if total == 0:
            for i in range(len(percentages)):
                percentages[i] = 20
        # Otherwise normalize to 100%
        elif total != 100:
            for i in range(len(percentages)):
                percentages[i] = int((percentages[i] / total) * 100)
                # Fix rounding errors
                if i == len(percentages) - 1:
                    percentages[i] = 100 - sum(percentages[:-1])

        return percentages

    def validate_and_accept(self):
        """Validate inputs before accepting the dialog"""
        if self.use_original.isChecked():
            # Original generator validation
            minutes = self.minutes_input.value()
            seconds = self.seconds_input.value()
            num_outputs = self.num_outputs.value()

            # Check if duration is at least 10 seconds
            total_seconds = (minutes * 60) + seconds
            if total_seconds < 10:
                QMessageBox.warning(self, "Invalid Duration",
                                    "Show duration must be at least 10 seconds.")
                return

            # Normalize percentages to ensure they add up to 100%
            percentages = self.normalize_percentages()

            # Create config data object
            config_data = ShowConfigData(minutes, seconds, num_outputs, percentages)
            config_data.generator_type = "original"

            # Emit signal with config data
            self.config_completed.emit(config_data)

        else:
            # Professional generator validation
            if self.prof_duration.value() < 30:
                QMessageBox.warning(self, "Invalid Duration", "Professional show duration must be at least 30 seconds.")
                return

            # Create professional configuration
            prof_config = {
                'duration': self.prof_duration.value(),
                'num_outputs': self.prof_outputs.value(),
                'style': self.style_combo.currentData(),
                'complexity': self.complexity_combo.currentData(),
                'rhythm_pattern': self.rhythm_combo.currentData(),
                'bpm': self.bpm_spin.value(),
                'timing_precision': self.timing_precision.value(),
                'use_crescendo': self.use_crescendo.isChecked(),
                'smart_timing': self.smart_timing.isChecked(),
                'professional_validation': self.professional_validation.isChecked(),
                'mathematical_precision': self.mathematical_precision.isChecked()
            }

            # Create a ShowConfigData object with professional data
            config_data = ShowConfigData()
            config_data.professional_config = prof_config
            config_data.generator_type = "professional"

            # Emit signal with config data
            self.config_completed.emit(config_data)

        # Accept the dialog
        self.accept()


class GeneratorPromptDialog(QDialog):
    """Dialog for selecting the type of show to generate"""

    # Define signals for different generation types
    random_show_selected = Signal()
    musical_show_selected = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Show Generator")
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components"""
        # Main layout
        layout = QVBoxLayout(self)

        # Title label
        title_label = QLabel("What type of show would you like to generate?")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title_label)

        # Random Show button
        self.random_button = QPushButton("Random Show")
        self.random_button.setMinimumHeight(50)
        self.random_button.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: white;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
        """)
        self.random_button.clicked.connect(self.on_random_selected)
        layout.addWidget(self.random_button)

        # Musical Show button
        self.musical_button = QPushButton("Musical Show")
        self.musical_button.setMinimumHeight(50)
        self.musical_button.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
        """)
        self.musical_button.clicked.connect(self.on_musical_selected)
        layout.addWidget(self.musical_button)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)

        # Set some spacing for better appearance
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

    def on_random_selected(self):
        """Handle random show selection"""
        self.random_show_selected.emit()
        self.close()  # Close the dialog immediately
        self.accept()

    def on_musical_selected(self):
        """Handle musical show selection"""
        self.musical_show_selected.emit()
        self.close()  # Close the dialog immediately
        self.accept()


class GenerateShowDialog:
    """Main show generator dialog to be implemented later"""
    pass