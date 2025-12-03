"""
Main Window - Firework Visualizer Preview Methods
==================================================

This file contains the firework visualizer preview methods for the main window.
These methods are added to the MainWindow class to handle the Professional
Firework Visualizer integration.

Author: SuperNinja AI
Version: 1.0.0
License: MIT
"""


def _start_firework_visualizer_preview(self, music_file_info):
    """
    Start the Professional Firework Visualizer preview

    Args:
        music_file_info (dict or None): Information about the selected music file,
                                       or None if no music was selected
    """
    try:
        from PySide6.QtWidgets import QMessageBox

        # Connect signals
        self.firework_visualizer_bridge.visualizer_started.connect(self._on_firework_visualizer_started)
        self.firework_visualizer_bridge.visualizer_ready.connect(self._on_firework_visualizer_ready)
        self.firework_visualizer_bridge.visualizer_completed.connect(self._on_firework_visualizer_completed)
        self.firework_visualizer_bridge.visualizer_error.connect(self._on_firework_visualizer_error)

        # Store music file info for playback at T=0
        self.firework_music_file_info = music_file_info

        # Start the visualizer
        success = self.firework_visualizer_bridge.start_visualizer(
            self.cue_table.model._data,
            music_file_info
        )

        if not success:
            # Show error and fall back to LED panel
            QMessageBox.warning(
                self,
                "Visualizer Error",
                "Failed to start Professional Firework Visualizer.\n\n"
                "Falling back to LED Panel Preview."
            )
            self._start_led_preview_with_music(music_file_info)
            return

        # Show status
        if music_file_info:
            music_name = f"{music_file_info['name']}{music_file_info['extension']}"
            self.statusBar().showMessage(f"Professional Firework Visualizer starting with music: {music_name}")
        else:
            self.statusBar().showMessage("Professional Firework Visualizer starting (no music)")

    except Exception as e:
        print(f"Error starting firework visualizer: {str(e)}")
        import traceback
        traceback.print_exc()

        # Show error and fall back to LED panel
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(
            self,
            "Visualizer Error",
            f"Failed to start Professional Firework Visualizer:\n{str(e)}\n\n"
            "Falling back to LED Panel Preview."
        )
        self._start_led_preview_with_music(music_file_info)


def _on_firework_visualizer_started(self):
    """Handle firework visualizer window opened"""
    try:
        self.statusBar().showMessage("Professional Firework Visualizer window opened")
    except Exception as e:
        print(f"Error in firework visualizer start: {str(e)}")


def _on_firework_visualizer_ready(self):
    """Handle firework visualizer ready (T=0)"""
    try:
        # Start music playback at T=0 (critical synchronization point)
        if hasattr(self, 'firework_music_file_info') and self.firework_music_file_info:
            self.music_manager.preview_music(self.firework_music_file_info['path'], volume=0.7)
            print(f"Music started at T=0: {self.firework_music_file_info['path']}")

        self.statusBar().showMessage("Professional Firework Visualizer running")

    except Exception as e:
        print(f"Error in firework visualizer ready: {str(e)}")
        import traceback
        traceback.print_exc()


def _on_firework_visualizer_completed(self):
    """Handle firework visualizer completion"""
    try:
        # Stop music
        self.music_manager.stop_preview()

        self.statusBar().showMessage("Professional Firework Visualizer completed")

        # Disconnect signals
        try:
            self.firework_visualizer_bridge.visualizer_started.disconnect(self._on_firework_visualizer_started)
            self.firework_visualizer_bridge.visualizer_ready.disconnect(self._on_firework_visualizer_ready)
            self.firework_visualizer_bridge.visualizer_completed.disconnect(self._on_firework_visualizer_completed)
            self.firework_visualizer_bridge.visualizer_error.disconnect(self._on_firework_visualizer_error)
        except:
            pass  # Ignore disconnect errors

    except Exception as e:
        print(f"Error in firework visualizer completion: {str(e)}")
        import traceback
        traceback.print_exc()


def _on_firework_visualizer_error(self, error_message: str):
    """Handle firework visualizer error"""
    try:
        from PySide6.QtWidgets import QMessageBox

        # Stop music
        self.music_manager.stop_preview()

        self.statusBar().showMessage(f"Firework visualizer error: {error_message}")

        # Show error dialog
        QMessageBox.critical(
            self,
            "Visualizer Error",
            f"Professional Firework Visualizer error:\n{error_message}\n\n"
            "Falling back to LED Panel Preview."
        )

        # Fall back to LED panel
        if hasattr(self, 'firework_music_file_info'):
            self._start_led_preview_with_music(self.firework_music_file_info)

        # Disconnect signals
        try:
            self.firework_visualizer_bridge.visualizer_started.disconnect(self._on_firework_visualizer_started)
            self.firework_visualizer_bridge.visualizer_ready.disconnect(self._on_firework_visualizer_ready)
            self.firework_visualizer_bridge.visualizer_completed.disconnect(self._on_firework_visualizer_completed)
            self.firework_visualizer_bridge.visualizer_error.disconnect(self._on_firework_visualizer_error)
        except:
            pass  # Ignore disconnect errors

    except Exception as e:
        print(f"Error handling firework visualizer error: {str(e)}")
        import traceback
        traceback.print_exc()