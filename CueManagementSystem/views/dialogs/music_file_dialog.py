from typing import Dict, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QListWidget, QListWidgetItem, QProgressBar,
    QSlider, QWidget, QMessageBox, QSplitter
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFont

from views.managers.music_manager import MusicManager


class MusicListItem(QListWidgetItem):
    """Custom list widget item for music files"""
    
    def __init__(self, file_info: Dict[str, str]):
        super().__init__()
        self.file_info = file_info
        self.setText(f"{file_info['name']}{file_info['extension']} ({file_info['size']})")
        self.setToolTip(file_info['path'])
        
        # Set icon based on file extension
        self._set_icon_based_on_type()
    
    def _set_icon_based_on_type(self):
        """Set an appropriate icon based on file type"""
        ext = self.file_info['extension'].lower()
        # This would use appropriate icons in a real implementation
        # For now, we'll just use generic icons from the Qt style
        self.setIcon(QIcon())


class MusicPlayerControls(QWidget):
    """Widget for music playback controls"""
    
    def __init__(self, music_manager: MusicManager):
        super().__init__()
        self.music_manager = music_manager
        self.current_file = None
        
        self._init_ui()
        
        # Update timer for progress bar
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(100)  # 100ms updates
        self.update_timer.timeout.connect(self._update_progress)
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Now playing label
        self.now_playing_label = QLabel("No file selected")
        self.now_playing_label.setAlignment(Qt.AlignCenter)
        self.now_playing_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.now_playing_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v / %m")
        layout.addWidget(self.progress_bar)
        
        # Time labels
        time_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.total_time_label = QLabel("00:00")
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.total_time_label)
        layout.addLayout(time_layout)
        
        # Slider for seeking
        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setMinimum(0)
        self.seek_slider.setMaximum(100)
        self.seek_slider.sliderMoved.connect(self._seek_to_position)
        self.seek_slider.sliderReleased.connect(self._slider_released)
        layout.addWidget(self.seek_slider)
        
        # Playback controls
        controls_layout = QHBoxLayout()
        
        # Play/Pause button
        self.play_pause_btn = QPushButton("Play")
        self.play_pause_btn.clicked.connect(self._toggle_playback)
        controls_layout.addWidget(self.play_pause_btn)
        
        # Stop button
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._stop_playback)
        controls_layout.addWidget(self.stop_btn)
        
        layout.addLayout(controls_layout)
        
        # Disable controls initially
        self._set_controls_enabled(False)
    
    def _set_controls_enabled(self, enabled: bool):
        """Enable or disable playback controls"""
        self.play_pause_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(enabled)
        self.seek_slider.setEnabled(enabled)
    
    def load_file(self, file_info: Optional[Dict[str, str]]):
        """Load a file without starting playback"""
        if file_info is None:
            self.current_file = None
            self.now_playing_label.setText("No file selected")
            self._set_controls_enabled(False)
            self.update_timer.stop()
            return
        
        # Stop any current playback
        self._stop_playback()
        
        self.current_file = file_info
        self.now_playing_label.setText(f"Selected: {file_info['name']}")
        self._set_controls_enabled(True)
        
        # Load the file without playing
        print(f"Loading file: {file_info['path']}")
        self.music_manager.load_music_file(file_info['path'])
        
        # Update button text to Play
        self.play_pause_btn.setText("Play")
    
    def set_file(self, file_info: Optional[Dict[str, str]]):
        """Set the current file for playback and start playing"""
        if file_info is None:
            self.current_file = None
            self.now_playing_label.setText("No file selected")
            self._set_controls_enabled(False)
            self.update_timer.stop()
            return
        
        self.current_file = file_info
        self.now_playing_label.setText(f"Playing: {file_info['name']}")
        self._set_controls_enabled(True)
        
        # Start playback
        self.music_manager.preview_music(file_info['path'])
        
        # Start update timer
        self.update_timer.start()
        
        # Update button text
        self.play_pause_btn.setText("Pause")
    
    def _toggle_playback(self):
        """Toggle between play and pause"""
        if not self.current_file:
            return
            
        print(f"Toggle playback: Currently playing = {self.music_manager.is_playing()}")
        
        if self.music_manager.is_playing():
            # If playing, pause it
            print("Pausing playback")
            self.music_manager.pause_preview()
            self.play_pause_btn.setText("Play")
            self.update_timer.stop()
        else:
            # If not playing, start/resume it
            print("Starting/resuming playback")
            
            # Get current playback position
            position, _ = self.music_manager.get_playback_position()
            
            if position > 0:
                # If we have a position, resume playback
                print(f"Resuming from position {position}")
                self.music_manager.resume_preview()
            else:
                # If no position (never started or reset), start fresh
                print("Starting fresh playback")
                self.music_manager.preview_music(self.current_file['path'])
            
            self.play_pause_btn.setText("Pause")
            self.update_timer.start()
    
    def _stop_playback(self):
        """Stop playback"""
        if not self.current_file:
            return
            
        self.music_manager.stop_preview()
        self.play_pause_btn.setText("Play")
        self.update_timer.stop()
        self._reset_progress()
    
    def _update_progress(self):
        """Update progress bar and time labels"""
        if not self.current_file:
            return
            
        position, duration = self.music_manager.get_playback_position()
        
        # Update progress bar
        if duration > 0:
            self.progress_bar.setMaximum(duration)
            self.progress_bar.setValue(position)
            self.seek_slider.setMaximum(duration)
            self.seek_slider.setValue(position)
            
            # Update time labels
            self.current_time_label.setText(self._format_time(position))
            self.total_time_label.setText(self._format_time(duration))
        
        # Check if playback has finished
        if position >= duration and duration > 0:
            self.update_timer.stop()
            self.play_pause_btn.setText("Play")
            self._reset_progress()
    
    def _reset_progress(self):
        """Reset progress display"""
        self.progress_bar.setValue(0)
        self.seek_slider.setValue(0)
        self.current_time_label.setText("00:00")
    
    def _seek_to_position(self, position):
        """Seek to position when slider is moved"""
        if not self.current_file:
            return
            
        self.music_manager.set_playback_position(position)
    
    def _slider_released(self):
        """Handle slider released event"""
        if not self.current_file:
            return
            
        position = self.seek_slider.value()
        self.music_manager.set_playback_position(position)
    
    def _format_time(self, ms):
        """Format milliseconds to MM:SS format"""
        total_seconds = ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def stop(self):
        """Stop playback and timer when dialog is closed"""
        self.update_timer.stop()
        self.music_manager.stop_preview()


class MusicFileDialog(QDialog):
    """Dialog for importing and managing music files"""
    
    def __init__(self, parent=None, music_manager=None):
        super().__init__(parent)

        # Use the provided music manager or create a new one
        if music_manager is not None and isinstance(music_manager, MusicManager):
            self.music_manager = music_manager
        else:
            self.music_manager = MusicManager(music_manager)  # If music_manager is None or a string path
                
        self.music_manager.music_updated.connect(self._refresh_music_list)
        
        self._init_ui()
        self._refresh_music_list()
        
        # Set dialog properties
        self.setWindowTitle("Music File Manager")
        self.resize(800, 600)
    
    def _init_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create splitter for list and player
        splitter = QSplitter(Qt.Vertical)
        
        # Music list area
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Music Library")
        header_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        # Import button
        self.import_btn = QPushButton("Import Music")
        self.import_btn.clicked.connect(self._import_music)
        header_layout.addWidget(self.import_btn)
        
        list_layout.addLayout(header_layout)
        
        # Music list
        self.music_list = QListWidget()
        self.music_list.setSelectionMode(QListWidget.SingleSelection)
        self.music_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.music_list.setMinimumHeight(300)
        list_layout.addWidget(self.music_list)
        
        # List actions
        list_actions_layout = QHBoxLayout()
        
        # Delete button
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._delete_selected_music)
        list_actions_layout.addWidget(self.delete_btn)
        
        list_layout.addLayout(list_actions_layout)
        
        # Add list widget to splitter
        splitter.addWidget(list_widget)
        
        # Player controls
        self.player_controls = MusicPlayerControls(self.music_manager)
        splitter.addWidget(self.player_controls)
        
        # Set splitter sizes
        splitter.setSizes([400, 200])
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)
    
    def _refresh_music_list(self):
        """Refresh the music file list"""
        # Clear existing items
        self.music_list.clear()
        
        # Get music files
        music_files = self.music_manager.get_music_files()
        
        # Add to list
        for file_info in music_files:
            item = MusicListItem(file_info)
            self.music_list.addItem(item)
        
        # Select the first item if available
        if self.music_list.count() > 0:
            self.music_list.setCurrentRow(0)
            print(f"Selected first item in list (total items: {self.music_list.count()})")
        else:
            print("No items in music list")
        
        # Update button states
        self._update_button_states()
    
    def _update_button_states(self):
        """Update button enabled states based on selection"""
        current_item = self.music_list.currentItem()
        has_selection = current_item is not None
        
        # Debug print to verify selection state
        print(f"Selection changed - Has selection: {has_selection}")
        if has_selection and isinstance(current_item, MusicListItem):
            print(f"Selected item: {current_item.file_info['name']}{current_item.file_info['extension']}")
        
        # Enable/disable delete button based on selection
        self.delete_btn.setEnabled(has_selection)
    
    def _import_music(self):
        """Open file dialog to import music files"""
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Import Music Files")
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Audio Files (*.mp3 *.wav *.ogg *.flac *.m4a)")
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            imported_count = 0
            
            for file_path in selected_files:
                if self.music_manager.import_music_file(file_path):
                    imported_count += 1
            
            # Show success message
            if imported_count > 0:
                QMessageBox.information(
                    self,
                    "Import Successful",
                    f"Successfully imported {imported_count} music file(s)."
                )
                
                # Select the first item in the list if available
                if self.music_list.count() > 0:
                    self.music_list.setCurrentRow(0)
                    self._update_button_states()
    
    def _get_selected_file_info(self):
        """Get file info for selected item"""
        item = self.music_list.currentItem()
        print(f"Getting selected file info: {item}")
        
        if item is None:
            print("No item selected")
            return None
            
        if not isinstance(item, MusicListItem):
            print(f"Selected item is not a MusicListItem but {type(item)}")
            return None
            
        print(f"Selected item: {item.file_info['name']}{item.file_info['extension']}")
        return item.file_info
    
    def _on_selection_changed(self):
        """Handle selection change in the music list"""
        # Update button states
        self._update_button_states()
        
        # Load the selected file without starting playback
        file_info = self._get_selected_file_info()
        if file_info:
            self.player_controls.load_file(file_info)
    
    def _delete_selected_music(self):
        """Delete the selected music file"""
        file_info = self._get_selected_file_info()
        if not file_info:
            return
            
        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{file_info['name']}{file_info['extension']}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # Stop playback if this is the current file
            if self.player_controls.current_file == file_info:
                print("Stopping playback of file being deleted")
                self.player_controls._stop_playback()
                self.player_controls.current_file = None
                self.player_controls.now_playing_label.setText("No file selected")
                self.player_controls._set_controls_enabled(False)
            
            # Delete the file
            if self.music_manager.delete_music_file(file_info['path']):
                # File deleted successfully
                self._refresh_music_list()
            else:
                QMessageBox.warning(
                    self,
                    "Delete Failed",
                    f"Could not delete '{file_info['name']}{file_info['extension']}'."
                )
    
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        # Stop any playing music
        self.player_controls.stop()
        super().closeEvent(event)
