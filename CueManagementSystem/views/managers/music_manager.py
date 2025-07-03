import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


class MusicManager(QObject):
    """
    Controller for managing music files in the application.
    Handles importing, deleting, and accessing music files.
    """
    
    music_updated = Signal()  # Signal emitted when music library changes
    
    def __init__(self, music_dir: str = None):
        super().__init__()
        
        # Set up music directory
        if music_dir is None:
            # Default to a music directory in user's home
            home = str(Path.home())
            music_dir = os.path.join(home, ".cue_management_system", "music")
        
        self.music_dir = music_dir
        self._ensure_directory_exists()
        
        # Audio player for previewing
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        # Current playing state
        self.current_file = None
        
    def _ensure_directory_exists(self) -> None:
        """Ensure the music directory exists"""
        os.makedirs(self.music_dir, exist_ok=True)
    
    def get_music_files(self) -> List[Dict[str, str]]:
        """
        Get a list of all music files in the library
        
        Returns:
            List of dictionaries with file information:
            {
                'name': Display name (filename without extension),
                'path': Full path to the file,
                'extension': File extension,
                'size': File size in human-readable format
            }
        """
        self._ensure_directory_exists()
        music_files = []
        
        # Supported audio formats
        supported_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.m4a']
        
        print(f"Looking for music files in: {self.music_dir}")
        
        try:
            files_in_dir = os.listdir(self.music_dir)
            print(f"Found {len(files_in_dir)} files/directories in music directory")
            
            for file in files_in_dir:
                file_path = os.path.join(self.music_dir, file)
                if os.path.isfile(file_path):
                    _, ext = os.path.splitext(file)
                    if ext.lower() in supported_extensions:
                        # Get file size and convert to readable format
                        size_bytes = os.path.getsize(file_path)
                        size_str = self._format_file_size(size_bytes)
                        
                        file_info = {
                            'name': os.path.splitext(file)[0],
                            'path': file_path,
                            'extension': ext,
                            'size': size_str
                        }
                        
                        print(f"Found music file: {file_info['name']}{file_info['extension']} ({file_info['size']})")
                        music_files.append(file_info)
        
        except Exception as e:
            print(f"Error listing music directory: {e}")
        
        # Sort by name
        music_files.sort(key=lambda x: x['name'].lower())
        print(f"Returning {len(music_files)} music files")
        return music_files
    
    def _format_file_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format
        
        Args:
            size_bytes: File size in bytes
            
        Returns:
            Formatted file size (e.g., "2.5 MB")
        """
        # Handle zero size
        if size_bytes == 0:
            return "0 B"
            
        # Define size units and their names
        units = ['B', 'KB', 'MB', 'GB']
        i = 0
        
        # Find appropriate unit
        while size_bytes >= 1024 and i < len(units) - 1:
            size_bytes /= 1024
            i += 1
            
        # Return formatted size with unit
        return f"{size_bytes:.1f} {units[i]}"
    
    def import_music_file(self, source_path: str) -> bool:
        """
        Import a music file into the library
        
        Args:
            source_path: Path to the source music file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._ensure_directory_exists()
            
            # Get destination path
            filename = os.path.basename(source_path)
            dest_path = os.path.join(self.music_dir, filename)
            
            # Check if file already exists
            if os.path.exists(dest_path):
                # Generate a unique name
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(dest_path):
                    new_filename = f"{base}_{counter}{ext}"
                    dest_path = os.path.join(self.music_dir, new_filename)
                    counter += 1
            
            # Copy the file
            shutil.copy2(source_path, dest_path)
            
            # Emit signal that music library has changed
            self.music_updated.emit()
            
            return True
        except Exception as e:
            print(f"Error importing music file: {str(e)}")
            return False
    
    def delete_music_file(self, file_path: str) -> bool:
        """
        Delete a music file from the library
        
        Args:
            file_path: Path to the music file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if file exists and is within our music directory
            if os.path.exists(file_path) and os.path.dirname(file_path) == self.music_dir:
                # Stop playback if this is the current file
                if self.current_file == file_path:
                    self.stop_preview()
                    self.current_file = None
                
                # Delete the file
                os.remove(file_path)
                
                # Emit signal that music library has changed
                self.music_updated.emit()
                
                return True
            return False
        except Exception as e:
            print(f"Error deleting music file: {str(e)}")
            return False
    
    def load_music_file(self, file_path: str, volume: float = 0.5) -> bool:
        """
        Load a music file without starting playback
        
        Args:
            file_path: Path to the music file to load
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            True if file was loaded successfully, False otherwise
        """
        try:
            if os.path.exists(file_path):
                # Stop any current playback
                self.stop_preview()
                
                # Set the source without playing
                self.player.setSource(QUrl.fromLocalFile(file_path))
                self.audio_output.setVolume(volume)
                
                # Set current file
                self.current_file = file_path
                
                return True
            return False
        except Exception as e:
            print(f"Error loading music file: {str(e)}")
            return False
    
    def preview_music(self, file_path: str, volume: float = 0.5) -> bool:
        """
        Preview a music file
        
        Args:
            file_path: Path to the music file to preview
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            True if playback started, False otherwise
        """
        try:
            if os.path.exists(file_path):
                # Stop any current playback
                self.stop_preview()
                
                # Set the source and play
                self.player.setSource(QUrl.fromLocalFile(file_path))
                self.audio_output.setVolume(volume)
                self.player.play()
                
                # Set current file
                self.current_file = file_path
                
                return True
            return False
        except Exception as e:
            print(f"Error previewing music: {str(e)}")
            return False
    
    def stop_preview(self) -> None:
        """Stop music preview playback"""
        self.player.stop()
    
    def pause_preview(self) -> None:
        """Pause music preview playback"""
        self.player.pause()
    
    def resume_preview(self) -> None:
        """Resume paused music preview"""
        print(f"Resuming playback, current state: {self.player.playbackState()}")
        self.player.play()
    
    def get_playback_position(self) -> Tuple[int, int]:
        """
        Get current playback position and duration
        
        Returns:
            Tuple of (current position in ms, total duration in ms)
        """
        position = self.player.position()
        duration = self.player.duration()
        return position, duration
    
    def set_playback_position(self, position_ms: int) -> None:
        """
        Set playback position
        
        Args:
            position_ms: Position in milliseconds
        """
        self.player.setPosition(position_ms)
    
    def is_playing(self) -> bool:
        """
        Check if music is currently playing
        
        Returns:
            True if playing, False otherwise
        """
        state = self.player.playbackState()
        state_name = "Unknown"
        
        if state == QMediaPlayer.PlayingState:
            state_name = "Playing"
        elif state == QMediaPlayer.PausedState:
            state_name = "Paused"
        elif state == QMediaPlayer.StoppedState:
            state_name = "Stopped"
            
        print(f"Player state check: {state_name} ({state})")
        return state == QMediaPlayer.PlayingState