from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                              QMessageBox, QSpinBox, QGroupBox, QFormLayout, QDialogButtonBox,
                              QComboBox, QGridLayout, QSlider)
from PySide6.QtCore import Qt, Signal

class ShowConfigData:
    """Container for show configuration data"""
    def __init__(self, duration_minutes=0, duration_seconds=0, num_outputs=100, section_intensities=None):
        self.duration_minutes = duration_minutes
        self.duration_seconds = duration_seconds
        self.num_outputs = num_outputs
        # Default to balanced intensities if none provided
        self.section_intensities = section_intensities or [20, 20, 20, 20, 20]
        
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
        """Initialize the UI components"""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Title/description
        title_label = QLabel("Configure your random show")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        description = QLabel("Please specify the duration, output count, and intensity pattern for your show.")
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        main_layout.addWidget(description)
        
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
        
        # Set duration group layout
        duration_group.setLayout(duration_layout)
        main_layout.addWidget(duration_group)
        
        # Output configuration group
        output_group = QGroupBox("Output Configuration")
        output_layout = QFormLayout()
        
        # Number of outputs
        self.num_outputs = QSpinBox()
        self.num_outputs.setRange(1, 1000)
        self.num_outputs.setValue(100)  # Default 100 outputs
        self.num_outputs.setSuffix(" outputs")
        output_layout.addRow("Number of outputs:", self.num_outputs)
        
        # Set output group layout
        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)
        
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
            section_label = QLabel(f"Section {i+1}")
            sections_layout.addWidget(section_label, i+1, 0)
            
            # Slider for percentage
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(20)  # Default balanced
            slider.setTickPosition(QSlider.TicksBelow)
            slider.setTickInterval(10)
            slider.valueChanged.connect(lambda val, idx=i: self.update_section_percentage(idx, val))
            sections_layout.addWidget(slider, i+1, 1)
            self.section_sliders.append(slider)
            
            # Label for percentage and outputs
            value_label = QLabel("20% (20 outputs)")
            sections_layout.addWidget(value_label, i+1, 2)
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
        main_layout.addWidget(intensity_group)
        
        # Validation note
        validation_note = QLabel("Note: Show must have a duration of at least 10 seconds.")
        validation_note.setStyleSheet("color: gray; font-style: italic;")
        main_layout.addWidget(validation_note)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        
        # Set spacing and margins
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Initialize with balanced preset
        self.apply_preset("Balanced")
        
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
        self.accept()
        
    def on_musical_selected(self):
        """Handle musical show selection"""
        self.musical_show_selected.emit()
        self.accept()

class GenerateShowDialog:
    """Main show generator dialog to be implemented later"""
    pass