"""
Excalibur Shell Selector Dialog
================================

Simplified, user-friendly dialog for selecting Excalibur artillery shells.
Automatically configures all physics, colors, timing, and audio based on
authentic Excalibur shell specifications.

Features:
- Single dropdown with 24 authentic Excalibur shells
- Automatic configuration of all parameters
- Fixed launch angle assignment based on output position (-30°, -15°, 0°, +15°, +30°)
- Realistic physics based on actual Excalibur specifications
- No tabs, no manual configuration - just pick and go!

Author: Michael Lyman
Version: 2.0.0
License: MIT
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QTextEdit, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

import json


class ExcaliburShellSelector(QDialog):
    """Simplified dialog for selecting Excalibur artillery shells"""

    shell_selected = Signal(dict)  # Emits complete visual properties

    # 24 Authentic Excalibur Shells
    EXCALIBUR_SHELLS = [
        "Red Peony",
        "Blue Peony",
        "Green Peony",
        "Purple Peony",
        "Gold Peony",
        "Silver Peony",
        "Multi-Color Peony",
        "Red Chrysanthemum",
        "Blue Chrysanthemum",
        "Green Chrysanthemum",
        "Silver Chrysanthemum",
        "Gold Brocade Crown",
        "Silver Brocade",
        "Golden Willow with Crackle",
        "Silver Willow",
        "Red Dahlia",
        "Purple Dahlia",
        "Silver Crackling Palm",
        "Gold Palm",
        "Jumbo Crackling",
        "Dragon Eggs",
        "Green Glitter with Crackle",
        "Brocade to Blue Whirlwind",
        "Silver Wave to Red Whirlwind"
    ]

    # Color mappings for shells
    SHELL_COLORS = {
        "Red Peony": (255, 0, 0),
        "Blue Peony": (0, 100, 255),
        "Green Peony": (0, 255, 0),
        "Purple Peony": (148, 0, 211),
        "Gold Peony": (255, 215, 0),
        "Silver Peony": (192, 192, 192),
        "Multi-Color Peony": (255, 0, 0),  # Primary red, will add secondary
        "Red Chrysanthemum": (255, 0, 0),
        "Blue Chrysanthemum": (0, 100, 255),
        "Green Chrysanthemum": (0, 255, 0),
        "Silver Chrysanthemum": (192, 192, 192),
        "Gold Brocade Crown": (255, 215, 0),
        "Silver Brocade": (192, 192, 192),
        "Golden Willow with Crackle": (255, 215, 0),
        "Silver Willow": (192, 192, 192),
        "Red Dahlia": (255, 0, 0),
        "Purple Dahlia": (148, 0, 211),
        "Silver Crackling Palm": (192, 192, 192),
        "Gold Palm": (255, 215, 0),
        "Jumbo Crackling": (255, 215, 0),
        "Dragon Eggs": (255, 140, 0),
        "Green Glitter with Crackle": (0, 255, 0),
        "Brocade to Blue Whirlwind": (255, 215, 0),
        "Silver Wave to Red Whirlwind": (192, 192, 192)
    }

    # Shell descriptions
    SHELL_DESCRIPTIONS = {
        "Red Peony": "Classic spherical burst with vibrant red stars radiating outward in all directions. Hard break with loud report.",
        "Blue Peony": "Brilliant blue spherical burst with intense color. High altitude break with strong report.",
        "Green Peony": "Bright green spherical burst with vivid emerald stars. Large diameter spread.",
        "Purple Peony": "Rich purple spherical burst with deep violet hues. Impressive visual impact.",
        "Gold Peony": "Traditional golden spherical burst with warm, glittering stars. Classic firework effect.",
        "Silver Peony": "Bright silver-white spherical burst with brilliant stars. Clean, crisp appearance.",
        "Multi-Color Peony": "Spherical burst featuring multiple vibrant colors mixed together. Spectacular variety.",
        "Red Chrysanthemum": "Red burst with long-lasting trailing stars creating a flower-like pattern. Elegant effect.",
        "Blue Chrysanthemum": "Blue burst with beautiful trailing stars. Graceful, flowing appearance.",
        "Green Chrysanthemum": "Green burst with long trails creating a stunning chrysanthemum pattern.",
        "Silver Chrysanthemum": "Silver-white burst with elegant trailing stars. Classic Japanese-style effect.",
        "Gold Brocade Crown": "Thick, glittering golden kamuro trails creating a crown-like effect. Very impressive.",
        "Silver Brocade": "Bright silver kamuro effect with thick, sparkling trails. Stunning visual.",
        "Golden Willow with Crackle": "Drooping golden trails resembling a weeping willow, with loud crackling effects.",
        "Silver Willow": "Elegant silver drooping trails creating a beautiful willow tree pattern.",
        "Red Dahlia": "Large red petals creating a distinctive dahlia flower pattern. Bold and beautiful.",
        "Purple Dahlia": "Large purple petals with dahlia flower appearance. Unique and striking.",
        "Silver Crackling Palm": "Rising silver trails in palm tree pattern with intense crackling sounds.",
        "Gold Palm": "Rising golden trails resembling palm fronds. Tropical-inspired effect.",
        "Jumbo Crackling": "Massive burst of loud crackling stars. Extremely loud and impressive.",
        "Dragon Eggs": "Intense crackling effect with rapid-fire crackles. Very loud and exciting.",
        "Green Glitter with Crackle": "Green glittering stars combined with loud crackling effects. Dual sensation.",
        "Brocade to Blue Whirlwind": "Golden brocade trails transitioning to blue whirlwind pattern. Complex effect.",
        "Silver Wave to Red Whirlwind": "Silver wave pattern transitioning to red whirlwind. Dynamic and colorful."
    }

    def __init__(self, parent=None, cue_data=None):
        super().__init__(parent)
        self.cue_data = cue_data
        self.selected_shell = None

        self.setWindowTitle("Select Excalibur Shell")
        self.setMinimumSize(600, 500)
        self.setModal(True)

        self.init_ui()
        self.apply_dark_theme()

        # Load existing shell if available
        if cue_data and 'visual_properties' in cue_data:
            shell_name = cue_data['visual_properties'].get('shell_name')
            if shell_name and shell_name in self.EXCALIBUR_SHELLS:
                index = self.EXCALIBUR_SHELLS.index(shell_name)
                self.shell_combo.setCurrentIndex(index)

    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("🎆 Select Excalibur Artillery Shell")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setStyleSheet("color: #4CAF50; padding: 10px;")
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # Cue info
        if self.cue_data:
            info_text = f"Cue #{self.cue_data.get('cue_number', 'N/A')} - {self.cue_data.get('cue_type', 'Unknown')}"
            info_label = QLabel(info_text)
            info_label.setStyleSheet("font-size: 11px; color: #aaa; padding: 5px;")
            info_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(info_label)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #444;")
        main_layout.addWidget(line)

        # Shell selection group
        selection_group = QGroupBox("Choose Your Shell")
        selection_layout = QVBoxLayout()
        selection_layout.setSpacing(10)

        # Instruction label
        instruction = QLabel(
            "Select an Excalibur shell from the list below.\nAll effects, colors, and physics will be configured automatically.")
        instruction.setStyleSheet("color: #ccc; font-size: 11px;")
        instruction.setAlignment(Qt.AlignCenter)
        instruction.setWordWrap(True)
        selection_layout.addWidget(instruction)

        # Shell dropdown
        shell_label = QLabel("Excalibur Shell:")
        shell_label.setStyleSheet("font-weight: bold; color: white; font-size: 12px;")
        selection_layout.addWidget(shell_label)

        self.shell_combo = QComboBox()
        self.shell_combo.addItems(self.EXCALIBUR_SHELLS)
        self.shell_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                color: white;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            QComboBox:hover {
                border: 2px solid #45a049;
                background-color: #3d3d3d;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid white;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: white;
                selection-background-color: #4CAF50;
                selection-color: white;
                border: 1px solid #4CAF50;
            }
        """)
        self.shell_combo.currentTextChanged.connect(self.update_description)
        selection_layout.addWidget(self.shell_combo)

        selection_group.setLayout(selection_layout)
        main_layout.addWidget(selection_group)

        # Description group
        desc_group = QGroupBox("Shell Description")
        desc_layout = QVBoxLayout()

        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setMaximumHeight(100)
        self.description_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #ddd;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 10px;
                font-size: 11px;
            }
        """)
        desc_layout.addWidget(self.description_text)

        desc_group.setLayout(desc_layout)
        main_layout.addWidget(desc_group)

        # Auto-configuration info
        auto_info = QLabel(
            "✓ Launch angle will be assigned based on output position\n"
            "✓ All physics parameters configured automatically\n"
            "✓ Colors and effects set based on authentic Excalibur specifications\n"
            "✓ Audio levels optimized for realistic Excalibur sound"
        )
        auto_info.setStyleSheet("""
            QLabel {
                background-color: #1a3a1a;
                color: #90EE90;
                border: 1px solid #4CAF50;
                border-radius: 5px;
                padding: 10px;
                font-size: 10px;
            }
        """)
        auto_info.setWordWrap(True)
        main_layout.addWidget(auto_info)

        # Spacer
        main_layout.addStretch()

        # Button bar
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(100, 35)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #666;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        # Apply button
        apply_btn = QPushButton("Apply Shell")
        apply_btn.setFixedSize(120, 35)
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        apply_btn.clicked.connect(self.apply_shell)
        button_layout.addWidget(apply_btn)

        main_layout.addLayout(button_layout)

        # Initialize description
        self.update_description(self.shell_combo.currentText())

    def update_description(self, shell_name):
        """Update the description when shell selection changes"""
        description = self.SHELL_DESCRIPTIONS.get(shell_name, "Select a shell to see description")
        self.description_text.setText(description)
        self.selected_shell = shell_name

    def get_shell_configuration(self, shell_name):
        """Generate complete configuration for selected shell"""
        # Calculate launch angle based on output number (fixed angles per column)
        launch_angle = self._calculate_launch_angle_from_output()

        # Get primary color
        primary_color = self.SHELL_COLORS.get(shell_name, (255, 215, 0))

        # Base configuration for all Excalibur shells
        config = {
            'shell_name': shell_name,
            'effect_type': self._get_effect_type(shell_name),
            'size': 'large',  # All Excalibur are large (60g)

            # Colors
            'primary_color': primary_color,
            'primary_brightness': self._get_brightness(shell_name),
            'primary_intensity': 1.0,

            # Physics - Excalibur specifications
            'velocity_multiplier': 1.2,  # Excalibur standard
            'launch_angle': launch_angle,  # Random from 5 options
            'gravity_multiplier': 1.0,
            'wind_speed': 0.0,  # Clear, windless night
            'wind_direction': 0,
            'position': [0.0, 0.0, 0.0],  # Ground level
            'star_count': self._get_star_count(shell_name),
            'spread_angle': self._get_spread_angle(shell_name),

            # Timing - Excalibur specifications
            'time_to_burst': 2.5,  # ~250 feet
            'explosion_duration': self._get_explosion_duration(shell_name),
            'fade_start_delay': 0.5,
            'fade_duration': self._get_fade_duration(shell_name),
            'trail_duration': self._get_trail_duration(shell_name),
            'trail_fade_rate': 0.5,

            # Audio - Excalibur is LOUD
            'master_volume': 1.2,
            'launch_volume': 0.9,
            'explosion_volume': self._get_explosion_volume(shell_name),
            'crackle_volume': self._get_crackle_volume(shell_name),
            'whistle_volume': 0.0
        }

        # Add secondary color for multi-color shells
        if "Multi-Color" in shell_name:
            config['secondary_color'] = (0, 100, 255)  # Blue
            config['secondary_brightness'] = 1.0
            config['secondary_intensity'] = 1.0

        # Add trail color for willow/brocade shells
        if "Willow" in shell_name or "Brocade" in shell_name or "Palm" in shell_name:
            config['trail_color'] = (255, 140, 0)  # Orange trail
            config['trail_brightness'] = 0.8

        return config

    def _get_effect_type(self, shell_name):
        """Determine effect type from shell name"""
        if "Peony" in shell_name:
            return "peony"
        elif "Chrysanthemum" in shell_name:
            return "chrysanthemum"
        elif "Brocade" in shell_name:
            return "brocade"
        elif "Willow" in shell_name:
            return "willow"
        elif "Palm" in shell_name:
            return "palm"
        elif "Dahlia" in shell_name:
            return "dahlia"
        elif "Crackling" in shell_name or "Dragon Eggs" in shell_name:
            return "crackle"
        elif "Whirlwind" in shell_name or "Wave" in shell_name:
            return "multi_effect"
        else:
            return "peony"  # Default

    def _get_brightness(self, shell_name):
        """Get brightness based on shell type"""
        if "Silver" in shell_name or "White" in shell_name:
            return 1.3  # Brighter
        elif "Brocade" in shell_name:
            return 1.2
        else:
            return 1.0

    def _get_star_count(self, shell_name):
        """Get star count based on shell type"""
        if "Jumbo" in shell_name or "Crackling" in shell_name or "Dragon Eggs" in shell_name:
            return 200  # More stars for crackle
        elif "Chrysanthemum" in shell_name:
            return 130
        elif "Willow" in shell_name or "Brocade" in shell_name:
            return 110
        elif "Palm" in shell_name:
            return 90
        elif "Dahlia" in shell_name:
            return 110
        else:  # Peony
            return 170

    def _calculate_launch_angle_from_output(self):
        """
        Calculate launch angle based on output number

        Setup: 40 boxes of 50 shots each (5 columns × 10 rows per box)
        Fixed angles per column:
        - Outputs 1-10, 51-60, 101-110, etc. (column 1): -30°
        - Outputs 11-20, 61-70, 111-120, etc. (column 2): -15°
        - Outputs 21-30, 71-80, 121-130, etc. (column 3): 0°
        - Outputs 31-40, 81-90, 131-140, etc. (column 4): 15°
        - Outputs 41-50, 91-100, 141-150, etc. (column 5): 30°

        Returns:
            int: Launch angle in degrees
        """
        # Default angle if no cue data
        if not self.cue_data or 'outputs' not in self.cue_data:
            return 0

        # Get the first output number from the cue
        outputs_str = self.cue_data.get('outputs', '1')

        try:
            # Parse outputs (could be "1", "1,2,3", "1-5", etc.)
            if ',' in outputs_str:
                # Multiple outputs: "1,2,3"
                first_output = int(outputs_str.split(',')[0].strip())
            elif '-' in outputs_str:
                # Range: "1-5"
                first_output = int(outputs_str.split('-')[0].strip())
            else:
                # Single output: "1"
                first_output = int(outputs_str.strip())

            # Calculate position within 50-shot box (1-50)
            position_in_box = ((first_output - 1) % 50) + 1

            # Determine column (1-5) based on position
            # Outputs 1-10 = column 1, 11-20 = column 2, etc.
            if 1 <= position_in_box <= 10:
                return -30  # Column 1
            elif 11 <= position_in_box <= 20:
                return -15  # Column 2
            elif 21 <= position_in_box <= 30:
                return 0  # Column 3
            elif 31 <= position_in_box <= 40:
                return 15  # Column 4
            elif 41 <= position_in_box <= 50:
                return 30  # Column 5
            else:
                return 0  # Default fallback

        except (ValueError, IndexError) as e:
            # If parsing fails, return default angle
            print(f"Warning: Could not parse output '{outputs_str}': {e}")
            return 0

    def _get_spread_angle(self, shell_name):
        """Get spread angle based on shell type"""
        if "Willow" in shell_name:
            return 100  # Narrower for drooping effect
        elif "Palm" in shell_name:
            return 90  # Narrow for rising effect
        else:
            return 120  # Standard spherical

    def _get_explosion_duration(self, shell_name):
        """Get explosion duration based on shell type"""
        if "Crackling" in shell_name or "Dragon Eggs" in shell_name:
            return 0.7  # Longer for crackle
        else:
            return 0.5

    def _get_fade_duration(self, shell_name):
        """Get fade duration based on shell type"""
        if "Chrysanthemum" in shell_name or "Willow" in shell_name:
            return 4.0  # Longer trails
        elif "Brocade" in shell_name:
            return 3.5
        else:
            return 3.0

    def _get_trail_duration(self, shell_name):
        """Get trail duration based on shell type"""
        if "Chrysanthemum" in shell_name:
            return 2.0
        elif "Willow" in shell_name or "Brocade" in shell_name:
            return 2.5
        elif "Palm" in shell_name:
            return 1.8
        else:
            return 1.0

    def _get_explosion_volume(self, shell_name):
        """Get explosion volume based on shell type"""
        if "Crackling" in shell_name or "Dragon Eggs" in shell_name:
            return 1.4  # Very loud
        elif "Jumbo" in shell_name:
            return 1.3
        else:
            return 1.2  # Standard Excalibur loud

    def _get_crackle_volume(self, shell_name):
        """Get crackle volume based on shell type"""
        if "Crackling" in shell_name or "Dragon Eggs" in shell_name or "Crackle" in shell_name:
            return 1.5  # Very loud crackle
        else:
            return 0.0  # No crackle

    def apply_shell(self):
        """Apply the selected shell configuration"""
        if not self.selected_shell:
            return

        # Generate complete configuration
        config = self.get_shell_configuration(self.selected_shell)

        # Emit signal with configuration
        self.shell_selected.emit(config)

        # Close dialog
        self.accept()

    def apply_dark_theme(self):
        """Apply dark theme styling"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
                color: white;
            }
            QLabel {
                color: white;
            }
            QGroupBox {
                color: white;
                border: 2px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                font-size: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)


# Test the dialog
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # Test with sample cue data
    test_cue = {
        'cue_number': 1,
        'cue_type': 'SINGLE SHOT',
        'outputs': '1,2,3',
        'delay': 0.5
    }

    dialog = ExcaliburShellSelector(cue_data=test_cue)


    def on_shell_selected(config):
        print("\n=== Shell Configuration ===")
        print(json.dumps(config, indent=2))


    dialog.shell_selected.connect(on_shell_selected)
    dialog.exec()

    sys.exit(0)