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
                               QPushButton, QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from views.managers.music_manager import MusicManager


class MusicSelectionDialog(QDialog):
    """Dialog for selecting a music file to play with the preview"""

    music_selected = Signal(dict)  # Signal emitted when music is selected

    def __init__(self, parent=None, music_manager=None, is_hardware_mode=False):
        super().__init__(parent)

        # Store mode for UI updates
        self.is_hardware_mode = is_hardware_mode

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

        # No music option
        # Dynamic text based on mode
        if self.is_hardware_mode:
            no_music_text = "No music? Just click 'Skip Music' to execute show without audio."
        else:
            no_music_text = "No music? Just click 'Skip Music' to preview without audio."
        no_music_label = QLabel(no_music_text)
        no_music_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(no_music_label)

        # Dialog buttons
        button_layout = QHBoxLayout()

        # Skip music button
        skip_btn = QPushButton("Skip Music")
        skip_btn.clicked.connect(self._skip_music)
        button_layout.addWidget(skip_btn)

        button_layout.addStretch()

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        # Select button
        self.select_btn = QPushButton("Select")
        self.select_btn.clicked.connect(self._select_music)
        self.select_btn.setEnabled(False)  # Disabled until selection made
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
        has_selection = self.music_list.currentItem() is not None
        self.select_btn.setEnabled(has_selection)

    def _on_selection_changed(self):
        """Handle selection change in the music list"""
        self._update_button_states()

    def _select_music(self):
        """Select the current music file and accept dialog"""
        current_item = self.music_list.currentItem()
        if current_item:
            file_info = current_item.data(Qt.UserRole)
            self.music_selected.emit(file_info)
        self.accept()

    def _skip_music(self):
        """Skip music selection and proceed with preview"""
        self.music_selected.emit(None)
        self.accept()