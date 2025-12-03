"""
Music Selection Dialog
======================

Dialog for selecting music files from the library to play with preview or show.

Features:
- Music file list display
- File selection interface
- Preview option
- Skip music option
- Cancel functionality
- User-friendly selection

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QListWidget, QListWidgetItem,
                               QComboBox, QGroupBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from views.managers.music_manager import MusicManager


class MusicSelectionDialog(QDialog):
    """Dialog for selecting a music file to play with the preview"""

    music_selected = Signal(dict)  # Signal emitted when music is selected
    preview_led_requested = Signal(dict)  # Signal for LED preview
    preview_vr_requested = Signal(dict, str)  # Signal for VR preview (music, mode)

    def __init__(self, parent=None, music_manager=None, is_hardware_mode=False, ue5_available=False):
        super().__init__(parent)

        # Store mode for UI updates
        self.is_hardware_mode = is_hardware_mode
        self.ue5_available = ue5_available
        self.selected_music = None  # Track selected music

        # Use the provided music manager or create a new one
        if music_manager is not None and isinstance(music_manager, MusicManager):
            self.music_manager = music_manager
        else:
            self.music_manager = MusicManager(music_manager)  # If music_manager is None or a string path

        self._init_ui()
        self._refresh_music_list()

        # Set dialog properties based on mode
        if self.is_hardware_mode:
            self.setWindowTitle("Select Music for Show")
        else:
            self.setWindowTitle("Select Music for Preview")
        self.resize(500, 400)

    def _init_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)

        # Header - dynamic based on mode
        if self.is_hardware_mode:
            header_text = "Select Music File to Play with Show"
        else:
            header_text = "Select Music File to Play with Preview"
        header_label = QLabel(header_text)
        header_label.setFont(QFont("Arial", 12, QFont.Bold))
        main_layout.addWidget(header_label)

        # Music list
        self.music_list = QListWidget()
        self.music_list.setSelectionMode(QListWidget.SingleSelection)
        self.music_list.setMinimumHeight(250)
        main_layout.addWidget(self.music_list)

        # Info label - dynamic based on mode
        if self.is_hardware_mode:
            info_text = "Select a music file or proceed without music."
        else:
            info_text = "Select a music file (optional) and choose preview mode."
        info_label = QLabel(info_text)
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: gray; font-style: italic;")
        main_layout.addWidget(info_label)

        # VR Preview Mode Selector (only for simulation mode)
        if not self.is_hardware_mode:
            self._create_preview_mode_selector(main_layout)

        # Dialog buttons
        button_layout = QHBoxLayout()

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        button_layout.addStretch()

        # For simulation mode, add both preview buttons
        if not self.is_hardware_mode:
            # Preview LED button
            self.preview_led_btn = QPushButton("Preview LED")
            self.preview_led_btn.clicked.connect(self._preview_led)
            button_layout.addWidget(self.preview_led_btn)

            # Preview VR button
            self.preview_vr_btn = QPushButton("Preview VR")
            self.preview_vr_btn.clicked.connect(self._preview_vr)
            button_layout.addWidget(self.preview_vr_btn)
        else:
            # For hardware mode, keep the Select button
            self.select_btn = QPushButton("Select")
            self.select_btn.clicked.connect(self._select_music)
            button_layout.addWidget(self.select_btn)

        main_layout.addLayout(button_layout)

        # Connect selection change
        self.music_list.itemSelectionChanged.connect(self._on_selection_changed)

    def _refresh_music_list(self):
        """Refresh the music file list"""
        # Clear existing items
        self.music_list.clear()

        # Get music files
        music_files = self.music_manager.get_music_files()

        # Add to list
        for file_info in music_files:
            item = QListWidgetItem(f"{file_info['name']}{file_info['extension']}")
            item.setData(Qt.UserRole, file_info)
            self.music_list.addItem(item)

        # Update button states
        self._update_button_states()

    def _update_button_states(self):
        """Update button enabled states based on selection"""
        # In hardware mode, enable/disable Select button based on selection
        if self.is_hardware_mode:
            has_selection = self.music_list.currentItem() is not None
            self.select_btn.setEnabled(has_selection)
        # In simulation mode, preview buttons are always enabled (music is optional)

    def _on_selection_changed(self):
        """Handle selection change in the music list"""
        # Store selected music
        current_item = self.music_list.currentItem()
        if current_item:
            self.selected_music = current_item.data(Qt.UserRole)
        else:
            self.selected_music = None

        self._update_button_states()

    def _select_music(self):
        """Select the current music file and accept dialog (hardware mode)"""
        current_item = self.music_list.currentItem()
        if current_item:
            file_info = current_item.data(Qt.UserRole)
            self.music_selected.emit(file_info)
        self.accept()

    def _preview_led(self):
        """Start LED preview with optional music"""
        self.preview_led_requested.emit(self.selected_music)
        self.accept()

    def _preview_vr(self):
        """Start VR preview with optional music and selected mode"""
        # Get selected mode
        mode = self.mode_combo.currentData() if hasattr(self, 'mode_combo') else "led_panel"

        # Emit signal with music and mode
        self.preview_vr_requested.emit(self.selected_music, mode)
        self.accept()

    def _create_preview_mode_selector(self, parent_layout):
        """Create the preview mode selector group"""
        group_box = QGroupBox("Preview Mode")
        group_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        group_layout = QVBoxLayout()

        # Mode selector
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Visualization Mode:")
        mode_label.setFont(QFont("Arial", 10, QFont.Bold))
        mode_layout.addWidget(mode_label)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("📺 LED Panel Preview (Classic)", "led_panel")
        self.mode_combo.addItem("🎆 Professional Firework Visualizer", "firework_visualizer")

        self.mode_combo.setMinimumWidth(300)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()

        group_layout.addLayout(mode_layout)

        # Description label
        self.mode_description = QLabel()
        self.mode_description.setWordWrap(True)
        self.mode_description.setStyleSheet("color: #666; padding: 5px; font-size: 10pt;")
        self._update_mode_description()
        group_layout.addWidget(self.mode_description)

        group_box.setLayout(group_layout)
        parent_layout.addWidget(group_box)

    def _update_mode_description(self):
        """Update the mode description based on selection"""
        if not hasattr(self, 'mode_combo'):
            return

        mode = self.mode_combo.currentData()

        if mode == "led_panel":
            description = (
                "✓ Preview on LED panel in main window\n"
                "✓ Classic visualization mode\n"
                "✓ No additional windows\n"
                "✓ Quick and simple"
            )
        elif mode == "firework_visualizer":
            description = (
                "✓ Professional-grade particle effects\n"
                "✓ Realistic firework physics\n"
                "✓ Full-screen visualization window\n"
                "✓ 600-800 particles per burst\n"
                "✓ Auto-closes when show ends"
            )
        else:
            description = "Select a preview mode"

        self.mode_description.setText(description)

    def _on_mode_changed(self):
        """Handle preview mode change"""
        self._update_mode_description()