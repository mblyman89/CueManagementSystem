"""
Show Generation Configuration Dialog
====================================

Dialog for configuring and generating random or musical firework shows with customizable parameters.

Features:
- Global show parameters configuration
- Act-specific settings
- Random show generation
- Musical structure generation
- Customizable timing and effects
- Multi-act show support
- User-friendly interface

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QMessageBox, QSpinBox, QGroupBox, QFormLayout, QDialogButtonBox,
                               QComboBox, QGridLayout, QSlider, QTabWidget, QWidget, QCheckBox,
                               QDoubleSpinBox, QScrollArea, QFrame, QRadioButton, QButtonGroup,
                               QTextEdit, QSizePolicy)
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

        # Cue order setting (sequential or random)
        self.sequential_cues = True  # Default to sequential order

        # New attributes for the three-act structure
        self.act_config = {
            "opening": {},
            "buildup": {},
            "finale": {}
        }

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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Random Show Generator")
        self.resize(900, 700)  # Increased size for enhanced statistics

        # Initialize variables
        self.act_percentages = [33, 33, 34]  # Default percentages for the three acts
        self.updating_sliders = False
        self.updating_spinboxes = False
        self.act_sliders = []
        self.act_labels = []
        self.act_spinboxes = []
        self.sequential_order = True  # Default to sequential order

        # Store shot type widgets for each act
        self.shot_type_widgets = {
            "opening": {},
            "buildup": {},
            "finale": {}
        }

        # Set compact layout settings
        self.setStyleSheet("""
            QGroupBox { margin-top: 5px; padding-top: 10px; }
            QVBoxLayout, QHBoxLayout { spacing: 3px; }
            QLabel { margin: 0px; }
        """)

        self.init_ui()

    def init_ui(self):
        """Initialize the UI with three sections: top, middle (tabbed), and bottom"""
        # Main layout
        main_layout = QVBoxLayout(self)

        # ===== TOP SECTION - GLOBAL SETTINGS =====
        top_section = QGroupBox("Global Settings")
        top_layout = QVBoxLayout()  # Changed to QVBoxLayout for better organization

        # Top controls - Output and Duration settings
        top_controls_layout = QHBoxLayout()
        top_controls_layout.setAlignment(Qt.AlignCenter)  # Center horizontally

        # Total Outputs
        outputs_layout = QVBoxLayout()
        outputs_layout.setAlignment(Qt.AlignCenter)  # Center horizontally

        outputs_label = QLabel("Total Outputs:")
        outputs_label.setAlignment(Qt.AlignCenter)
        outputs_layout.addWidget(outputs_label)

        self.total_outputs = QSpinBox()
        self.total_outputs.setRange(1, 1000)
        self.total_outputs.setValue(1000)  # Default to 1000 outputs as per requirements
        # Remove "outputs" suffix from spinbox
        self.total_outputs.valueChanged.connect(self.update_act_labels)
        outputs_layout.addWidget(self.total_outputs)

        top_controls_layout.addLayout(outputs_layout)

        # Add some spacing
        top_controls_layout.addSpacing(40)

        # Total Duration
        duration_layout = QVBoxLayout()
        duration_layout.setAlignment(Qt.AlignCenter)  # Center horizontally

        duration_label = QLabel("Total Duration:")
        duration_label.setAlignment(Qt.AlignCenter)
        duration_layout.addWidget(duration_label)

        self.duration_combo = QComboBox()
        for i in range(5, 16):  # 5 to 15 minutes
            self.duration_combo.addItem(f"{i} minutes", i)
        self.duration_combo.setCurrentIndex(5)  # Default to 10 minutes (index 5 corresponds to 10 minutes)
        self.duration_combo.currentIndexChanged.connect(self.update_all_statistics)
        duration_layout.addWidget(self.duration_combo)

        top_controls_layout.addLayout(duration_layout)

        top_layout.addLayout(top_controls_layout)

        # Minimal spacing between top controls and sliders
        top_layout.addSpacing(5)

        # Act percentage sliders - more compact
        sliders_layout = QVBoxLayout()
        sliders_layout.setAlignment(Qt.AlignCenter)  # Center horizontally
        sliders_layout.setSpacing(2)  # Reduce spacing between sliders

        sliders_label = QLabel("Act Distribution:")
        sliders_label.setAlignment(Qt.AlignCenter)
        sliders_layout.addWidget(sliders_label)

        # Create sliders for the three acts
        act_names = ["Opening Act", "Build-up Act", "Finale Act"]

        # Find the longest act name for alignment
        max_label_width = max(len(name) for name in act_names)

        for i, act_name in enumerate(act_names):
            act_layout = QHBoxLayout()

            # Create a fixed-width label for alignment
            act_label = QLabel(act_name)
            act_label.setMinimumWidth(100)  # Fixed width for alignment
            act_layout.addWidget(act_label)

            # Slider
            slider = QSlider(Qt.Horizontal)
            slider.setRange(10, 80)  # Allow 10% to 80% for each act
            slider.setValue(self.act_percentages[i])
            slider.setTickPosition(QSlider.TicksBelow)
            slider.setTickInterval(10)
            slider.setMinimumWidth(300)  # Set a minimum width for the slider
            slider.valueChanged.connect(lambda val, idx=i: self.update_act_percentage(idx, val))
            act_layout.addWidget(slider)
            self.act_sliders.append(slider)

            # Percentage spinbox
            spinbox = QSpinBox()
            spinbox.setRange(10, 80)
            spinbox.setValue(self.act_percentages[i])
            spinbox.setSuffix("%")
            spinbox.setFixedWidth(70)  # Fixed width for alignment
            spinbox.valueChanged.connect(lambda val, idx=i: self.update_act_spinbox(idx, val))
            act_layout.addWidget(spinbox)
            self.act_spinboxes.append(spinbox)

            # Outputs label
            outputs_label = QLabel(f"({int(self.act_percentages[i] * self.total_outputs.value() / 100)})")
            outputs_label.setFixedWidth(50)  # Fixed width for alignment
            act_layout.addWidget(outputs_label)
            self.act_labels.append(outputs_label)

            sliders_layout.addLayout(act_layout)

        top_layout.addLayout(sliders_layout)

        # Total percentage - centered and side by side
        total_layout = QHBoxLayout()
        total_layout.setAlignment(Qt.AlignCenter)  # Center horizontally

        total_label = QLabel("Total:")
        total_layout.addWidget(total_label)

        self.total_percentage = QLabel("100%")
        total_layout.addWidget(self.total_percentage)

        top_layout.addLayout(total_layout)

        # Cue order options - Sequential or Random
        cue_order_layout = QHBoxLayout()
        cue_order_layout.setAlignment(Qt.AlignCenter)  # Center horizontally

        cue_order_label = QLabel("Cue Order:")
        cue_order_layout.addWidget(cue_order_label)

        # Create a button group for mutual exclusivity
        self.cue_order_group = QButtonGroup(self)

        # Sequential checkbox
        self.sequential_checkbox = QCheckBox("Sequential")
        self.sequential_checkbox.setChecked(True)  # Default to sequential
        self.cue_order_group.addButton(self.sequential_checkbox)
        cue_order_layout.addWidget(self.sequential_checkbox)

        # Random checkbox
        self.random_checkbox = QCheckBox("Random")
        self.cue_order_group.addButton(self.random_checkbox)
        cue_order_layout.addWidget(self.random_checkbox)

        # Connect checkboxes to update the sequential_order variable
        self.sequential_checkbox.toggled.connect(self.update_cue_order)
        self.random_checkbox.toggled.connect(self.update_cue_order)

        top_layout.addLayout(cue_order_layout)

        # Warning for percentages - centered
        self.percentage_warning = QLabel("")
        self.percentage_warning.setStyleSheet("color: red;")
        self.percentage_warning.setAlignment(Qt.AlignCenter)
        top_layout.addWidget(self.percentage_warning)

        top_section.setLayout(top_layout)
        main_layout.addWidget(top_section)

        # ===== MIDDLE SECTION - TABBED INTERFACE =====
        self.tab_widget = QTabWidget()

        # Create tabs for each act
        act_keys = ["opening", "buildup", "finale"]
        for i, (act_name, act_key) in enumerate(zip(act_names, act_keys)):
            tab = self.create_act_tab(act_name, act_key, i)
            self.tab_widget.addTab(tab, act_name)

        main_layout.addWidget(self.tab_widget, 2)  # Reduce the middle section's space

        # ===== BOTTOM SECTION - REMOVED GREEN BUTTON =====
        # The green "GENERATE SHOW" button has been removed
        # Users will use the "Add Cues to Table" button at the bottom instead

        # ===== DIALOG BUTTONS =====
        # Create a custom button layout
        button_layout = QHBoxLayout()

        # Cancel button on the left
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button, 0, Qt.AlignLeft)

        # Spacer to push the OK button to the right
        button_layout.addStretch()

        # OK button renamed to "Add Cues to Table"
        ok_button = QPushButton("Add Cues to Table")
        ok_button.clicked.connect(self.validate_and_accept)
        button_layout.addWidget(ok_button, 0, Qt.AlignRight)

        main_layout.addLayout(button_layout)

        # Update all labels initially
        self.update_act_labels()

        # Set default values for all acts
        self.set_default_values()

    def create_act_tab(self, act_name, act_key, act_index):
        """Create a tab for an act with specific settings"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Remove description to save space

        # Shot Types section
        shot_types_group = QGroupBox("Shot Types")
        shot_types_layout = QGridLayout()
        shot_types_layout.setVerticalSpacing(5)  # Reduce vertical spacing between rows
        shot_types_layout.setHorizontalSpacing(10)  # Reduce horizontal spacing between columns

        # Create header row with labels
        percent_label = QLabel("Percentage")
        percent_label.setAlignment(Qt.AlignCenter)
        shot_types_layout.addWidget(percent_label, 0, 1)

        # Note: Delay parameters removed - now hardcoded in generator for professional timing

        # Shot types with dynamic spinboxes
        shot_types = ["SINGLE SHOT", "DOUBLE SHOT", "SPECIAL EFFECTS"]

        # Store widgets for this act
        self.shot_type_widgets[act_key] = {}

        # Add total percentage tracking
        self.shot_type_widgets[act_key]["total_label"] = None
        self.shot_type_widgets[act_key]["warning_label"] = None

        # Store special effects checkboxes
        self.shot_type_widgets[act_key]["special_effects"] = {}

        for row, shot_type in enumerate(shot_types, 1):
            # Checkbox
            checkbox = QCheckBox(shot_type)
            checkbox.setFixedWidth(150)

            # Create a direct connection function for this specific checkbox
            def make_toggle_func(st=shot_type, ak=act_key):
                return lambda state: self.toggle_shot_type_options(state, st, ak)

            checkbox.stateChanged.connect(make_toggle_func())
            shot_types_layout.addWidget(checkbox, row, 0)

            # Percentage spinbox
            percent_spinbox = QSpinBox()
            percent_spinbox.setRange(0, 100)
            percent_spinbox.setValue(25)  # Default value
            percent_spinbox.setSuffix("%")
            percent_spinbox.setFixedWidth(80)
            percent_spinbox.setEnabled(False)  # Initially disabled

            # Create a direct connection function for this specific spinbox
            def make_value_changed_func(ak=act_key):
                return lambda: self.update_shot_type_total(ak)

            percent_spinbox.valueChanged.connect(make_value_changed_func())
            shot_types_layout.addWidget(percent_spinbox, row, 1, Qt.AlignCenter)

            # Store widgets for later access (no delay parameters)
            self.shot_type_widgets[act_key][shot_type] = {
                "checkbox": checkbox,
                "percent": percent_spinbox,
                "has_delay": False
            }

        # Add total percentage row
        total_row = len(shot_types) + 1

        # Total label
        total_label_text = QLabel("Total:")
        total_label_text.setAlignment(Qt.AlignRight)
        shot_types_layout.addWidget(total_label_text, total_row, 0)

        # Total percentage value
        total_percent_label = QLabel("0%")
        total_percent_label.setAlignment(Qt.AlignCenter)
        shot_types_layout.addWidget(total_percent_label, total_row, 1)

        # Store the total label for later updates
        self.shot_type_widgets[act_key]["total_label"] = total_percent_label

        # Add warning row
        warning_row = total_row + 1
        warning_label = QLabel("")
        warning_label.setStyleSheet("color: red;")
        warning_label.setAlignment(Qt.AlignCenter)
        shot_types_layout.addWidget(warning_label, warning_row, 0, 1, 3)  # Span across all columns

        # Store the warning label for later updates
        self.shot_type_widgets[act_key]["warning_label"] = warning_label

        # Set column stretch to use space more effectively
        shot_types_layout.setColumnStretch(0, 2)  # Checkbox column
        shot_types_layout.setColumnStretch(1, 1)  # Percentage column

        shot_types_group.setLayout(shot_types_layout)
        layout.addWidget(shot_types_group)

        # Effect settings
        effect_group = QGroupBox("Special Effects")
        effect_layout = QGridLayout()  # Grid layout for better organization
        effect_layout.setVerticalSpacing(5)
        effect_layout.setHorizontalSpacing(10)

        # New checkboxes for effects
        effects = [
            "Rock Ballad",
            "Metal Ballad",
            "Trot",
            "Gallop",
            "Step",
            "Chase",
            "Random"
        ]

        # Organize effects in a 2-row grid based on the screenshot
        # First row: Rock Ballad, Metal Ballad, Trot, Gallop
        # Second row: Step, Chase, Random
        effect_positions = {
            "Rock Ballad": (0, 0),
            "Metal Ballad": (0, 1),
            "Trot": (0, 2),
            "Gallop": (0, 3),
            "Step": (1, 0),
            "Chase": (1, 1),
            "Random": (1, 2)
        }

        for effect, (row, col) in effect_positions.items():
            checkbox = QCheckBox(effect)
            effect_layout.addWidget(checkbox, row, col)

            # Store reference to the checkbox
            self.shot_type_widgets[act_key]["special_effects"][effect] = checkbox
            # Connect checkbox to update statistics
            checkbox.stateChanged.connect(lambda state, ak=act_key: self.update_statistics(ak))

        # Add False Finale checkbox only for the finale act
        if act_key == "finale":
            # Add the False Finale checkbox at position (1, 3) - below Gallop and to the right of Random
            false_finale_checkbox = QCheckBox("Add False Finale")
            effect_layout.addWidget(false_finale_checkbox, 1, 3)

            # Store reference to the false finale checkbox
            self.shot_type_widgets[act_key]["special_effects"]["False Finale"] = false_finale_checkbox
            # Connect checkbox to update statistics
            false_finale_checkbox.stateChanged.connect(lambda state, ak=act_key: self.update_statistics(ak))

        effect_group.setLayout(effect_layout)
        layout.addWidget(effect_group)

        # Enhanced Statistics section with scrollable area
        stats_group = QGroupBox("Act Statistics & Configuration")
        stats_layout = QVBoxLayout()

        # Create a scrollable area for statistics
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(200)
        scroll_area.setMaximumHeight(400)

        # Create widget to hold statistics content
        stats_widget = QWidget()
        stats_content_layout = QVBoxLayout(stats_widget)

        # Create a read-only text display for statistics
        stats_text = QLabel()
        stats_text.setWordWrap(True)
        stats_text.setTextFormat(Qt.RichText)
        stats_text.setStyleSheet("""
            background-color: #1a1a1a; 
            color: #ffffff; 
            padding: 15px; 
            border-radius: 5px;
            font-family: 'Courier New', monospace;
        """)

        # Set initial placeholder content with enhanced formatting
        stats_html = f"""
        <div style="font-family: 'Courier New', monospace; font-size: 11px;">
        <h3 style="color: #4CAF50; margin-bottom: 10px; border-bottom: 2px solid #4CAF50; padding-bottom: 5px;">
        📊 {act_name.upper()} ACT OVERVIEW</h3>

        <table style="width: 100%; margin-bottom: 10px;">
        <tr><td style="color: #FFD700;"><b>⏱️ Duration:</b></td><td>0:00</td></tr>
        <tr><td style="color: #FFD700;"><b>🎯 Total Outputs:</b></td><td>0</td></tr>
        <tr><td style="color: #FFD700;"><b>🎆 Estimated Cues:</b></td><td>0</td></tr>
        <tr><td style="color: #FFD700;"><b>⚡ Avg Cues/Min:</b></td><td>0</td></tr>
        </table>

        <h4 style="color: #2196F3; margin-top: 15px; margin-bottom: 5px; border-bottom: 1px solid #2196F3;">
        🎭 Shot Type Distribution</h4>
        <table style="width: 100%; margin-bottom: 10px;">
        <tr><td>• SINGLE SHOT:</td><td>0 outputs (0%)</td></tr>
        <tr><td>• DOUBLE SHOT:</td><td>0 outputs (0%)</td></tr>
        <tr><td>• SINGLE RUN:</td><td>0 outputs (0%)</td></tr>
        <tr><td>• DOUBLE RUN:</td><td>0 outputs (0%)</td></tr>
        </table>

        <h4 style="color: #FF9800; margin-top: 15px; margin-bottom: 5px; border-bottom: 1px solid #FF9800;">
        ✨ Special Effects</h4>
        <p style="margin-left: 10px; color: #CCCCCC;">None selected</p>

        <h4 style="color: #9C27B0; margin-top: 15px; margin-bottom: 5px; border-bottom: 1px solid #9C27B0;">
        ⚙️ Technical Details</h4>
        <table style="width: 100%; margin-bottom: 10px;">
        <tr><td>• Implementation:</td><td>Single-shot based</td></tr>
        <tr><td>• Timing Precision:</td><td>0.125s increments</td></tr>
        <tr><td>• Effect Delays:</td><td>Hardcoded professional</td></tr>
        </table>

        <p style="margin-top: 15px; padding: 8px; background-color: #263238; border-left: 3px solid #4CAF50; color: #B0BEC5; font-size: 10px;">
        <b>ℹ️ Note:</b> All shot types are created using single shots with precise timing. 
        Special effects use professional delay patterns for realistic results.
        </p>
        </div>
        """
        stats_text.setText(stats_html)

        # Store reference to the stats label
        self.shot_type_widgets[act_key]["stats_label"] = stats_text

        stats_content_layout.addWidget(stats_text)
        stats_widget.setLayout(stats_content_layout)
        scroll_area.setWidget(stats_widget)

        stats_layout.addWidget(scroll_area)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        layout.addStretch()
        return tab

    def toggle_shot_type_options(self, state, shot_type, act_key):
        """Enable or disable shot type options based on checkbox state"""
        # Make sure we have a valid act_key and shot_type
        if act_key not in self.shot_type_widgets or shot_type not in self.shot_type_widgets[act_key]:
            return

        widgets = self.shot_type_widgets[act_key][shot_type]

        # Make sure widgets is a dictionary with the expected keys
        if not isinstance(widgets, dict):
            return

        enabled = (state == 2)  # 2 is Qt.Checked

        if "percent" in widgets:
            widgets["percent"].setEnabled(enabled)

        # Update the total percentage for this act
        self.update_shot_type_total(act_key)

        # Update statistics to reflect changes
        self.update_statistics(act_key)

    def update_shot_type_total(self, act_key):
        """Calculate and update the total percentage for shot types in an act"""
        total = 0

        # Sum up percentages of all checked shot types
        for shot_type, widgets in self.shot_type_widgets[act_key].items():
            # Skip non-shot type entries like total_label and warning_label
            if shot_type in ["total_label", "warning_label", "special_effects", "stats_label"]:
                continue

            # Check if this is a dictionary with a checkbox key
            if isinstance(widgets, dict) and "checkbox" in widgets:
                if widgets["checkbox"].isChecked():
                    total += widgets["percent"].value()

        # Update the total label
        total_label = self.shot_type_widgets[act_key]["total_label"]
        total_label.setText(f"{total}%")

        # Update the warning label
        warning_label = self.shot_type_widgets[act_key]["warning_label"]
        if total != 100:
            warning_label.setText(f"Warning: Shot type percentages add up to {total}%, not 100%")
        else:
            warning_label.setText("")

        # Update statistics
        self.update_statistics(act_key)

    def update_statistics(self, act_key):
        """Update the enhanced statistics display based on current settings"""
        # Get the act index and name
        act_keys = ["opening", "buildup", "finale"]
        act_names = ["Opening", "Buildup", "Finale"]
        act_index = act_keys.index(act_key)
        act_name = act_names[act_index]

        # Calculate total outputs for this act
        total_outputs = self.total_outputs.value()
        act_percentage = self.act_percentages[act_index]
        act_outputs = int((act_percentage / 100.0) * total_outputs)

        # Calculate duration for this act
        total_duration_minutes = self.duration_combo.currentData()
        act_duration_seconds = int((act_percentage / 100.0) * total_duration_minutes * 60)
        act_duration_minutes = act_duration_seconds // 60
        act_duration_remaining_seconds = act_duration_seconds % 60

        # Calculate shot type counts and percentages
        shot_type_counts = {}
        shot_type_percentages = {}
        total_checked_percentage = 0

        for shot_type, widgets in self.shot_type_widgets[act_key].items():
            # Skip non-shot type entries
            if shot_type in ["total_label", "warning_label", "special_effects", "stats_label"]:
                continue

            # Check if this is a dictionary with a checkbox key
            if isinstance(widgets, dict) and "checkbox" in widgets:
                if widgets["checkbox"].isChecked():
                    percentage = widgets["percent"].value()
                    total_checked_percentage += percentage
                    count = int((percentage / 100.0) * act_outputs)
                    shot_type_counts[shot_type] = count
                    shot_type_percentages[shot_type] = percentage
                else:
                    shot_type_counts[shot_type] = 0
                    shot_type_percentages[shot_type] = 0

        # Calculate estimated cues (more accurate with special effects)
        estimated_cues = 0
        estimated_cues += shot_type_counts.get("SINGLE SHOT", 0)  # 1 cue per output
        estimated_cues += shot_type_counts.get("DOUBLE SHOT", 0) // 2  # 1 cue per 2 outputs

        # Special effects: estimate based on effect patterns
        special_effects_outputs = shot_type_counts.get("SPECIAL EFFECTS", 0)
        if special_effects_outputs > 0:
            # Average 4 outputs per effect sequence (trot=3, gallop=4, step=4, etc.)
            estimated_cues += special_effects_outputs // 4

        # Calculate average cues per minute
        avg_cues_per_min = (estimated_cues / (act_duration_seconds / 60.0)) if act_duration_seconds > 0 else 0

        # Get selected special effects and their details
        selected_effects = []
        effect_details = {
            "Trot": "Steady 3-beat (0.7s)",
            "Gallop": "Fast triplet (0.15s×3 + 0.5s)",
            "Step": "Walking rhythm (1.0s, 0.5s)",
            "Rock Ballad": "Classic rock (0.8s, 0.4s)",
            "Metal Ballad": "Double bass (0.25s×2 + 0.5s)",
            "Chase": "LED sequence (0.3s uniform)",
            "Random": "Variable delays",
            "False Finale": "Dramatic pause + restart"
        }

        for effect, checkbox in self.shot_type_widgets[act_key]["special_effects"].items():
            if checkbox.isChecked():
                selected_effects.append(effect)

        # Build effects list with details
        if selected_effects:
            effects_html = ""
            for effect in selected_effects:
                detail = effect_details.get(effect, "")
                effects_html += f"<tr><td style='padding-left: 10px;'>• {effect}:</td><td style='color: #B0BEC5;'>{detail}</td></tr>\n"
        else:
            effects_html = "<tr><td colspan='2' style='padding-left: 10px; color: #888;'>None selected</td></tr>"

        # Build shot type distribution table
        shot_type_rows = ""
        shot_type_display = {
            "SINGLE SHOT": "Single Shot",
            "DOUBLE SHOT": "Double Shot",
            "SPECIAL EFFECTS": "Special Effects"
        }

        for shot_type in ["SINGLE SHOT", "DOUBLE SHOT", "SPECIAL EFFECTS"]:
            count = shot_type_counts.get(shot_type, 0)
            pct = shot_type_percentages.get(shot_type, 0)
            display_name = shot_type_display.get(shot_type, shot_type)

            if count > 0:
                shot_type_rows += f"<tr><td>• {display_name}:</td><td>{count} outputs ({pct}%)</td></tr>\n"

        # Calculate intensity metrics
        intensity_score = 0
        if act_duration_seconds > 0:
            # Higher cues/min = higher intensity
            intensity_score = min(100, int((avg_cues_per_min / 10.0) * 100))

        intensity_label = "Low"
        intensity_color = "#4CAF50"
        if intensity_score > 70:
            intensity_label = "Very High"
            intensity_color = "#F44336"
        elif intensity_score > 50:
            intensity_label = "High"
            intensity_color = "#FF9800"
        elif intensity_score > 30:
            intensity_label = "Moderate"
            intensity_color = "#FFC107"

        # Calculate pacing
        if avg_cues_per_min < 3:
            pacing = "Slow &amp; Dramatic"
        elif avg_cues_per_min < 6:
            pacing = "Steady Build"
        elif avg_cues_per_min < 10:
            pacing = "Energetic"
        else:
            pacing = "Rapid Fire"

        # Estimate show cost (rough estimate: $2 per output)
        estimated_cost = act_outputs * 2

        # Calculate effect complexity
        num_effects = len(selected_effects)
        if num_effects == 0:
            complexity = "Simple (No effects)"
        elif num_effects <= 2:
            complexity = "Moderate (Few effects)"
        elif num_effects <= 4:
            complexity = "Complex (Multiple effects)"
        else:
            complexity = "Very Complex (Many effects)"

        # Update the statistics HTML with enhanced formatting
        stats_html = f"""
        <div style="font-family: 'Courier New', monospace; font-size: 11px;">
        <h3 style="color: #4CAF50; margin-bottom: 10px; border-bottom: 2px solid #4CAF50; padding-bottom: 5px;">
        📊 {act_name.upper()} ACT OVERVIEW</h3>

        <table style="width: 100%; margin-bottom: 10px;">
        <tr><td style="color: #FFD700;"><b>⏱️ Duration:</b></td><td>{act_duration_minutes}:{act_duration_remaining_seconds:02d} ({act_percentage}% of show)</td></tr>
        <tr><td style="color: #FFD700;"><b>🎯 Total Outputs:</b></td><td>{act_outputs} outputs ({act_percentage}% of {total_outputs})</td></tr>
        <tr><td style="color: #FFD700;"><b>🎆 Estimated Cues:</b></td><td>~{estimated_cues} cues</td></tr>
        <tr><td style="color: #FFD700;"><b>⚡ Cues per Minute:</b></td><td>{avg_cues_per_min:.1f} cues/min</td></tr>
        <tr><td style="color: #FFD700;"><b>💰 Est. Cost:</b></td><td>${estimated_cost:,} (~$2/output)</td></tr>
        </table>

        <h4 style="color: #2196F3; margin-top: 15px; margin-bottom: 5px; border-bottom: 1px solid #2196F3;">
        🎭 Shot Type Distribution</h4>
        <table style="width: 100%; margin-bottom: 10px;">
        {shot_type_rows}
        </table>

        <h4 style="color: #FF9800; margin-top: 15px; margin-bottom: 5px; border-bottom: 1px solid #FF9800;">
        ✨ Special Effects ({num_effects} selected)</h4>
        <table style="width: 100%; margin-bottom: 10px;">
        {effects_html}
        </table>

        <h4 style="color: #E91E63; margin-top: 15px; margin-bottom: 5px; border-bottom: 1px solid #E91E63;">
        📈 Performance Metrics</h4>
        <table style="width: 100%; margin-bottom: 10px;">
        <tr><td>• Intensity:</td><td><span style="color: {intensity_color}; font-weight: bold;">{intensity_label}</span> ({intensity_score}/100)</td></tr>
        <tr><td>• Pacing:</td><td>{pacing}</td></tr>
        <tr><td>• Complexity:</td><td>{complexity}</td></tr>
        <tr><td>• Avg Time/Cue:</td><td>{f'{(act_duration_seconds / estimated_cues):.2f}s' if estimated_cues > 0 else 'N/A'}</td></tr>
        </table>

        <h4 style="color: #9C27B0; margin-top: 15px; margin-bottom: 5px; border-bottom: 1px solid #9C27B0;">
        ⚙️ Technical Details</h4>
        <table style="width: 100%; margin-bottom: 10px;">
        <tr><td>• Implementation:</td><td>Single-shot based</td></tr>
        <tr><td>• Timing Precision:</td><td>0.125s (125ms) increments</td></tr>
        <tr><td>• Effect Delays:</td><td>Hardcoded professional patterns</td></tr>
        <tr><td>• Output Order:</td><td>{'Sequential (1→{})'.format(total_outputs) if self.sequential_order else 'Random'}</td></tr>
        <tr><td>• Act Position:</td><td>{act_index + 1} of 3</td></tr>
        </table>

        <p style="margin-top: 15px; padding: 8px; background-color: #263238; border-left: 3px solid #4CAF50; color: #B0BEC5; font-size: 10px;">
        <b>ℹ️ Professional Note:</b> All shot types use single ignitions with precise timing. 
        Special effects are created through carefully timed sequences. Double shots = 2 singles at same time.
        Effects use proven professional delay patterns for maximum visual impact.
        </p>
        </div>
        """

        # Update the stats label
        stats_label = self.shot_type_widgets[act_key]["stats_label"]
        stats_label.setText(stats_html)

    def update_act_percentage(self, act_index, value):
        """Update the percentage for an act and adjust other acts if needed"""
        if self.updating_sliders:
            return

        # Update the percentage value
        self.act_percentages[act_index] = value

        # Update the spinbox without triggering its valueChanged signal
        self.updating_spinboxes = True
        self.act_spinboxes[act_index].setValue(value)
        self.updating_spinboxes = False

        # Calculate total
        total = sum(self.act_percentages)

        # Update warning if total is not 100%
        if total != 100:
            self.percentage_warning.setText(f"Warning: Percentages add up to {total}%, not 100%")
        else:
            self.percentage_warning.setText("")

        # Update the total label
        self.total_percentage.setText(f"{total}%")

        # Update all labels
        self.update_act_labels()

    def update_act_spinbox(self, act_index, value):
        """Update the percentage for an act from the spinbox"""
        if self.updating_spinboxes:
            return

        # Update the slider without triggering its valueChanged signal
        self.updating_sliders = True
        self.act_sliders[act_index].setValue(value)
        self.updating_sliders = False

        # Update the percentage value
        self.act_percentages[act_index] = value

        # Calculate total
        total = sum(self.act_percentages)

        # Update warning if total is not 100%
        if total != 100:
            self.percentage_warning.setText(f"Warning: Percentages add up to {total}%, not 100%")
        else:
            self.percentage_warning.setText("")

        # Update the total label
        self.total_percentage.setText(f"{total}%")

        # Update all labels
        self.update_act_labels()

    def update_act_labels(self):
        """Update all act percentage and output labels"""
        total_outputs = self.total_outputs.value()

        for i, slider in enumerate(self.act_sliders):
            percentage = slider.value()
            outputs = int((percentage / 100.0) * total_outputs)
            self.act_labels[i].setText(f"({outputs})")

        # Update statistics for all acts after updating labels
        self.update_all_statistics()

    def update_cue_order(self, checked):
        """Update the cue order setting based on checkbox state"""
        if checked:
            # If Sequential is checked, set sequential_order to True
            # If Random is checked, set sequential_order to False
            self.sequential_order = self.sequential_checkbox.isChecked()
            # Update statistics to reflect the change
            self.update_all_statistics()

    def set_default_values(self):
        """Set default values for all acts based on requirements"""
        # Opening act: single shot and double shot types checked
        opening_act = "opening"
        self.shot_type_widgets[opening_act]["SINGLE SHOT"]["checkbox"].setChecked(True)
        self.shot_type_widgets[opening_act]["DOUBLE SHOT"]["checkbox"].setChecked(True)

        # Ensure percentages add up to 100%
        self.shot_type_widgets[opening_act]["SINGLE SHOT"]["percent"].setValue(60)
        self.shot_type_widgets[opening_act]["DOUBLE SHOT"]["percent"].setValue(40)

        # Build up act: single shot, double shot, and special effects checked
        buildup_act = "buildup"
        self.shot_type_widgets[buildup_act]["SINGLE SHOT"]["checkbox"].setChecked(True)
        self.shot_type_widgets[buildup_act]["DOUBLE SHOT"]["checkbox"].setChecked(True)
        self.shot_type_widgets[buildup_act]["SPECIAL EFFECTS"]["checkbox"].setChecked(True)

        # Ensure percentages add up to 100%
        self.shot_type_widgets[buildup_act]["SINGLE SHOT"]["percent"].setValue(40)
        self.shot_type_widgets[buildup_act]["DOUBLE SHOT"]["percent"].setValue(30)
        self.shot_type_widgets[buildup_act]["SPECIAL EFFECTS"]["percent"].setValue(30)

        # Special effects for build up: trot, step, and chase checked
        self.shot_type_widgets[buildup_act]["special_effects"]["Trot"].setChecked(True)
        self.shot_type_widgets[buildup_act]["special_effects"]["Step"].setChecked(True)
        self.shot_type_widgets[buildup_act]["special_effects"]["Chase"].setChecked(True)

        # Finale act: all shot types checked
        finale_act = "finale"
        self.shot_type_widgets[finale_act]["SINGLE SHOT"]["checkbox"].setChecked(True)
        self.shot_type_widgets[finale_act]["DOUBLE SHOT"]["checkbox"].setChecked(True)
        self.shot_type_widgets[finale_act]["SPECIAL EFFECTS"]["checkbox"].setChecked(True)

        # Ensure percentages add up to 100%
        self.shot_type_widgets[finale_act]["SINGLE SHOT"]["percent"].setValue(30)
        self.shot_type_widgets[finale_act]["DOUBLE SHOT"]["percent"].setValue(30)
        self.shot_type_widgets[finale_act]["SPECIAL EFFECTS"]["percent"].setValue(40)

        # Special effects for finale: rock ballad, metal ballad, gallop, and false finale
        self.shot_type_widgets[finale_act]["special_effects"]["Rock Ballad"].setChecked(True)
        self.shot_type_widgets[finale_act]["special_effects"]["Metal Ballad"].setChecked(True)
        self.shot_type_widgets[finale_act]["special_effects"]["Gallop"].setChecked(True)
        # The "False Finale" checkbox is stored with the key "False Finale"
        self.shot_type_widgets[finale_act]["special_effects"]["False Finale"].setChecked(True)

        # Update statistics for all acts
        self.update_all_statistics()

    def update_all_statistics(self):
        """Update statistics for all acts"""
        for act_key in ["opening", "buildup", "finale"]:
            if act_key in self.shot_type_widgets:
                self.update_statistics(act_key)

    def generate_show(self):
        """Generate the show based on current settings"""
        # This method will be implemented later
        # For now, just update the statistics
        self.update_all_statistics()

    def normalize_percentages(self):
        """Normalize percentages to ensure they add up to 100%"""
        total = sum(self.act_percentages)

        # If total is 0, set equal distribution
        if total == 0:
            return [33, 33, 34]
        # Otherwise normalize to 100%
        elif total != 100:
            normalized = []
            for i in range(len(self.act_percentages)):
                if i < len(self.act_percentages) - 1:
                    normalized.append(int((self.act_percentages[i] / total) * 100))
                else:
                    # Last item gets the remainder to ensure sum is exactly 100
                    normalized.append(100 - sum(normalized))
            return normalized

        return self.act_percentages

    def validate_and_accept(self):
        """Validate inputs before accepting the dialog"""
        # Get duration in minutes
        duration_minutes = self.duration_combo.currentData()

        # Get total outputs
        num_outputs = self.total_outputs.value()

        # Normalize percentages
        percentages = self.normalize_percentages()

        # Create config data object
        config_data = ShowConfigData(duration_minutes, 0, num_outputs, percentages)

        # Set the sequential_cues attribute based on the checkbox selection
        config_data.sequential_cues = self.sequential_order

        # Add act-specific configurations
        act_keys = ["opening", "buildup", "finale"]
        for i, act_key in enumerate(act_keys):
            # Extract settings from the tab
            act_config = {
                "percentage": percentages[i],
                "outputs": int((percentages[i] / 100.0) * num_outputs),
                "shot_types": {},
                "special_effects": {}
            }

            # Extract shot type settings
            for shot_type, widgets in self.shot_type_widgets[act_key].items():
                # Skip non-shot type entries
                if shot_type in ["total_label", "warning_label", "special_effects", "stats_label"]:
                    continue

                # Check if this is a dictionary with a checkbox key
                if isinstance(widgets, dict) and "checkbox" in widgets:
                    # Store the checkbox state in the configuration
                    shot_config = {
                        "checkbox": widgets["checkbox"].isChecked(),
                        "percentage": widgets["percent"].value()
                    }

                    # Note: Delay settings are now hardcoded in the generator
                    # No need to pass them from the dialog

                    # Add to act configuration
                    act_config["shot_types"][shot_type] = shot_config

            # Extract special effects settings
            special_effects = {}
            if "special_effects" in self.shot_type_widgets[act_key]:
                for effect_name, checkbox in self.shot_type_widgets[act_key]["special_effects"].items():
                    if isinstance(checkbox, QCheckBox):
                        special_effects[effect_name] = checkbox.isChecked()

            act_config["special_effects"] = special_effects

            config_data.act_config[act_key] = act_config

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


# This class is kept for compatibility but not used directly
class GenerateShowDialog(QDialog):
    """Improved show generator dialog with three-section layout"""

    # Signal emitted when configuration is complete
    config_completed = Signal(ShowConfigData)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate Show")
        self.resize(900, 700)  # Set a large initial size

        # Initialize variables
        self.act_percentages = [33, 33, 34]  # Default percentages for the three acts
        self.updating_sliders = False
        self.act_sliders = []
        self.act_labels = []
        self.sequential_order = True  # Default to sequential order

        self.init_ui()

    def init_ui(self):
        """Initialize the UI with three sections: top, middle (tabbed), and bottom"""
        # Main layout
        main_layout = QVBoxLayout(self)

        # ===== TOP SECTION - GLOBAL SETTINGS =====
        top_section = QGroupBox("Global Settings")
        top_layout = QHBoxLayout()

        # Left side - Output and Duration settings
        left_layout = QFormLayout()

        # Total Outputs
        self.total_outputs = QSpinBox()
        self.total_outputs.setRange(1, 1000)
        self.total_outputs.setValue(100)
        self.total_outputs.setSuffix(" outputs")
        self.total_outputs.valueChanged.connect(self.update_act_labels)
        left_layout.addRow("Total Outputs:", self.total_outputs)

        # Total Duration
        duration_layout = QHBoxLayout()
        self.duration_combo = QComboBox()
        for i in range(5, 16):  # 5 to 15 minutes
            self.duration_combo.addItem(f"{i} minutes", i)
        self.duration_combo.setCurrentIndex(0)  # Default to 5 minutes
        duration_layout.addWidget(self.duration_combo)
        left_layout.addRow("Total Duration:", duration_layout)

        # Right side - Act percentage sliders
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Act Distribution:"))

        # Create sliders for the three acts
        act_names = ["Opening Act", "Build-up Act", "Finale Act"]
        for i, act_name in enumerate(act_names):
            act_layout = QHBoxLayout()
            act_layout.addWidget(QLabel(act_name))

            # Slider
            slider = QSlider(Qt.Horizontal)
            slider.setRange(10, 80)  # Allow 10% to 80% for each act
            slider.setValue(self.act_percentages[i])
            slider.setTickPosition(QSlider.TicksBelow)
            slider.setTickInterval(10)
            slider.valueChanged.connect(lambda val, idx=i: self.update_act_percentage(idx, val))
            act_layout.addWidget(slider)
            self.act_sliders.append(slider)

            # Percentage label
            label = QLabel(
                f"{self.act_percentages[i]}% ({int(self.act_percentages[i] * self.total_outputs.value() / 100)} outputs)")
            act_layout.addWidget(label)
            self.act_labels.append(label)

            right_layout.addLayout(act_layout)

        # Total percentage
        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel("Total:"))
        self.total_percentage = QLabel("100%")
        total_layout.addWidget(self.total_percentage)
        right_layout.addLayout(total_layout)

        # Warning for percentages
        self.percentage_warning = QLabel("")
        self.percentage_warning.setStyleSheet("color: red;")
        right_layout.addWidget(self.percentage_warning)

        # Cue order options - Sequential or Random
        cue_order_layout = QHBoxLayout()
        cue_order_layout.addWidget(QLabel("Cue Order:"))

        # Create a button group for mutual exclusivity
        self.cue_order_group = QButtonGroup(self)

        # Sequential checkbox
        self.sequential_checkbox = QCheckBox("Sequential")
        self.sequential_checkbox.setChecked(True)  # Default to sequential
        self.cue_order_group.addButton(self.sequential_checkbox)
        cue_order_layout.addWidget(self.sequential_checkbox)

        # Random checkbox
        self.random_checkbox = QCheckBox("Random")
        self.cue_order_group.addButton(self.random_checkbox)
        cue_order_layout.addWidget(self.random_checkbox)

        # Connect checkboxes to update the sequential_order variable
        self.sequential_checkbox.toggled.connect(self.update_cue_order)
        self.random_checkbox.toggled.connect(self.update_cue_order)

        left_layout.addRow("Cue Order:", cue_order_layout)

        # Add layouts to top section
        top_layout.addLayout(left_layout, 1)
        top_layout.addLayout(right_layout, 2)
        top_section.setLayout(top_layout)
        main_layout.addWidget(top_section)

        # ===== MIDDLE SECTION - TABBED INTERFACE =====
        self.tab_widget = QTabWidget()

        # Create tabs for each act
        for i, act_name in enumerate(act_names):
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            tab_layout.addWidget(QLabel(f"{act_name} settings will go here"))
            self.tab_widget.addTab(tab, act_name)

        main_layout.addWidget(self.tab_widget, 3)  # Give the middle section more space

        # ===== BOTTOM SECTION =====
        bottom_section = QGroupBox("Generate Show")
        bottom_layout = QVBoxLayout()

        # Placeholder for future functionality
        bottom_layout.addWidget(QLabel("Generate show controls will go here"))

        bottom_section.setLayout(bottom_layout)
        main_layout.addWidget(bottom_section)

        # ===== DIALOG BUTTONS =====
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        # Update all labels initially
        self.update_act_labels()

    def update_act_percentage(self, act_index, value):
        """Update the percentage for an act and adjust other acts if needed"""
        if self.updating_sliders:
            return

        # Update the percentage value
        self.act_percentages[act_index] = value

        # Calculate total
        total = sum(self.act_percentages)

        # Update warning if total is not 100%
        if total != 100:
            self.percentage_warning.setText(f"Warning: Percentages add up to {total}%, not 100%")
        else:
            self.percentage_warning.setText("")

        # Update the total label
        self.total_percentage.setText(f"{total}%")

        # Update all labels
        self.update_act_labels()

    def update_cue_order(self, checked):
        """Update the cue order setting based on checkbox state"""
        if checked:
            # If Sequential is checked, set sequential_order to True
            # If Random is checked, set sequential_order to False
            self.sequential_order = self.sequential_checkbox.isChecked()

    def update_act_labels(self):
        """Update all act percentage and output labels"""
        total_outputs = self.total_outputs.value()

        for i, slider in enumerate(self.act_sliders):
            percentage = slider.value()
            outputs = int((percentage / 100.0) * total_outputs)
            self.act_labels[i].setText(f"{percentage}% ({outputs} outputs)")

    def normalize_percentages(self):
        """Normalize percentages to ensure they add up to 100%"""
        total = sum(self.act_percentages)

        # If total is 0, set equal distribution
        if total == 0:
            return [33, 33, 34]
        # Otherwise normalize to 100%
        elif total != 100:
            normalized = []
            for i in range(len(self.act_percentages)):
                if i < len(self.act_percentages) - 1:
                    normalized.append(int((self.act_percentages[i] / total) * 100))
                else:
                    # Last item gets the remainder to ensure sum is exactly 100
                    normalized.append(100 - sum(normalized))
            return normalized

        return self.act_percentages

    def validate_and_accept(self):
        """Validate inputs before accepting the dialog"""
        # Get duration in minutes
        duration_minutes = self.duration_combo.currentData()

        # Get total outputs
        num_outputs = self.total_outputs.value()

        # Normalize percentages
        percentages = self.normalize_percentages()

        # Create config data object
        config_data = ShowConfigData(duration_minutes, 0, num_outputs, percentages)

        # Set the sequential_cues attribute based on the checkbox selection
        config_data.sequential_cues = self.sequential_order

        # Emit signal with config data
        self.config_completed.emit(config_data)

        # Accept the dialog
        self.accept()
