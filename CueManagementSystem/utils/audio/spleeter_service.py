"""
Spleeter Audio Separation Service
================================

A comprehensive service for integrating Spleeter audio separation into the CueManagementSystem.
This service handles the separation of audio files into multiple stems (vocals, drums, bass, piano, other)
and provides seamless integration with the existing waveform analysis workflow.

Author: NinjaTeach AI Team
Version: 1.0.0
License: MIT
"""

import os
import sys
import tempfile
import subprocess
import shutil
import logging
import hashlib
import platform
from pathlib import Path
from typing import Dict, Optional, Callable, List, Tuple
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal, QThread, QTimer
from PySide6.QtWidgets import QMessageBox, QProgressDialog, QApplication
import time


@dataclass
class SeparationResult:
    """Data class for separation results"""
    success: bool
    stems: Dict[str, str]  # stem_name -> file_path
    original_file: str
    output_directory: str
    processing_time: float
    error_message: Optional[str] = None


class SpleeterWorker(QThread):
    """Background thread for Spleeter audio separation processing"""
    
    # Signals for communication with main thread
    progress_update = Signal(str, int)  # message, percentage
    separation_complete = Signal(object)  # SeparationResult
    separation_error = Signal(str)  # error message
    
    def __init__(self, input_file: str, output_dir: str, model: str = "5stems", spleeter_cmd: str = "spleeter"):
        super().__init__()
        self.input_file = input_file
        self.output_dir = output_dir
        self.model = model
        self.spleeter_cmd = spleeter_cmd
        self.logger = logging.getLogger(__name__)
        self.start_time = None
        
    def run(self):
        """Execute Spleeter separation in background thread"""
        try:
            self.start_time = time.time()
            self.progress_update.emit("Initializing audio separation...", 0)
            
            # Validate input file
            if not os.path.exists(self.input_file):
                raise FileNotFoundError(f"Input file not found: {self.input_file}")
                
            # Create output directory
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Prepare Spleeter command (use resolved command passed in)
            cmd = [
                self.spleeter_cmd, "separate",
                "-p", f"spleeter:{self.model}",
                "-o", self.output_dir,
                self.input_file
            ]
            
            self.logger.info(f"Starting Spleeter separation: {' '.join(cmd)}")
            self.progress_update.emit("Starting audio separation process...", 10)
            
            # Execute Spleeter
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                universal_newlines=True
            )
            
            # Monitor progress
            progress_steps = [20, 40, 60, 80, 90]
            step_index = 0
            
            while process.poll() is None:
                if step_index < len(progress_steps):
                    self.progress_update.emit(
                        f"Processing audio separation... ({progress_steps[step_index]}%)", 
                        progress_steps[step_index]
                    )
                    step_index += 1
                self.msleep(2000)  # Update every 2 seconds
                
            # Check results
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.progress_update.emit("Finalizing separation results...", 95)
                
                # Find and validate separated stems
                stems = self._find_separated_stems()
                processing_time = time.time() - self.start_time
                
                result = SeparationResult(
                    success=True,
                    stems=stems,
                    original_file=self.input_file,
                    output_directory=self.output_dir,
                    processing_time=processing_time
                )
                
                self.progress_update.emit("Audio separation completed!", 100)
                self.separation_complete.emit(result)
                
            else:
                combined_err = (stderr or "") + "\n" + (stdout or "")
                if "compiled to use AVX" in combined_err:
                    arch = platform.machine()
                    guidance = (
                        f"Spleeter failed with return code {process.returncode}.\n"
                        "Detected TensorFlow built with AVX (Intel) which is incompatible with this machine ("
                        f"{arch}).\n\n"
                        "Fix: Use an Apple Silicon arm64 environment and install: \n"
                        "  pip install 'tensorflow-macos' 'tensorflow-metal' 'spleeter'\n"
                        "Then run the app from that environment, or set CUE_SPLEETER_PATH to the spleeter binary."
                    )
                    self.logger.error(guidance)
                    self.separation_error.emit(guidance)
                else:
                    error_msg = f"Spleeter failed with return code {process.returncode}"
                    if combined_err.strip():
                        error_msg += f"\nError output: {combined_err.strip()}"
                    self.logger.error(error_msg)
                    self.separation_error.emit(error_msg)
                
        except Exception as e:
            error_msg = f"Separation error: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.separation_error.emit(error_msg)
            
    def _find_separated_stems(self) -> Dict[str, str]:
        """Find and validate separated stem files"""
        stems = {}
        
        # Get the base filename without extension
        input_path = Path(self.input_file)
        base_name = input_path.stem
        
        # Expected stem names for 5stems model
        expected_stems = ["vocals", "drums", "bass", "piano", "other"]
        
        # Look for separated files
        separation_dir = Path(self.output_dir) / base_name
        
        if separation_dir.exists():
            for stem_name in expected_stems:
                stem_file = separation_dir / f"{stem_name}.wav"
                if stem_file.exists():
                    stems[stem_name] = str(stem_file)
                    self.logger.info(f"Found {stem_name} stem: {stem_file}")
                else:
                    self.logger.warning(f"Missing {stem_name} stem file: {stem_file}")
        else:
            self.logger.error(f"Separation directory not found: {separation_dir}")
            
        return stems


class SpleeterService(QObject):
    """
    Main service class for Spleeter audio separation integration
    
    This service provides a high-level interface for audio separation operations,
    including progress tracking, error handling, and integration with the existing
    CueManagementSystem workflow.
    """
    
    # Signals for UI integration
    separation_started = Signal()
    separation_progress = Signal(str, int)  # message, percentage
    separation_completed = Signal(object)  # SeparationResult
    separation_failed = Signal(str)  # error message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.worker = None
        self.progress_dialog = None
        self.temp_dirs = []  # Track temporary directories for cleanup
        
        # Configuration
        self.config = {
            'model': '5stems',  # 2stems, 4stems, or 5stems
            'auto_select_drums': True,
            'save_stems': False,
            'cache_separations': True,
            'max_cache_size_mb': 1000,
            'temp_cleanup': True,
            'spleeter_command': '/Users/michaellyman/.venvs/cueaudio/bin/spleeter'
        }
        
    def _resolve_spleeter_cmd(self) -> str:
        """Resolve the spleeter executable path from config/env or PATH."""
        try:
            import shutil as _shutil
            cmd = self.config.get('spleeter_command') or 'spleeter'
            # If it's not an absolute path, try to resolve via PATH
            resolved = _shutil.which(cmd)
            return resolved or cmd
        except Exception:
            return self.config.get('spleeter_command') or '/Users/michaellyman/.venvs/cueaudio/bin/spleeter'
        
    def check_spleeter_availability(self) -> Tuple[bool, str]:
        """
        Check if Spleeter is properly installed and available
        
        Returns:
            Tuple of (is_available, status_message)
        """
        try:
            cmd = self._resolve_spleeter_cmd()
            result = subprocess.run(
                [cmd, "--help"], 
                capture_output=True, 
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True, "Spleeter is available and ready"
            
            combined = (result.stderr or "") + "\n" + (result.stdout or "")
            if "compiled to use AVX" in combined:
                arch = platform.machine()
                guidance = (
                    "Spleeter/TensorFlow binary expects AVX (Intel build) but this machine is "
                    f"{arch}. On Apple Silicon, install tensorflow-macos in an arm64 env and reinstall spleeter. "
                    "Activate that environment before running the app. "
                    "Example: create a conda/venv, pip install 'tensorflow-macos' 'tensorflow-metal' 'spleeter'. "
                    "Optionally set CUE_SPLEETER_PATH to point to the spleeter binary in that env."
                )
                return False, guidance
            
            return False, f"Spleeter command failed: {combined.strip()}"
                
        except FileNotFoundError:
            return False, (
                "Spleeter not found on PATH. Install spleeter in your environment and/or set CUE_SPLEETER_PATH "
                "to the full path of the spleeter executable."
            )
        except subprocess.TimeoutExpired:
            return False, "Spleeter command timed out"
        except Exception as e:
            return False, f"Error checking Spleeter: {str(e)}"
            
    def separate_audio_async(self, input_file: str, output_dir: str = None, 
                           show_progress: bool = True) -> None:
        """
        Start asynchronous audio separation process
        
        Args:
            input_file: Path to input WAV file
            output_dir: Output directory (uses temp dir if None)
            show_progress: Whether to show progress dialog
        """
        try:
            # Validate input
            if not os.path.exists(input_file):
                self.separation_failed.emit(f"Input file not found: {input_file}")
                return
                
            # Check Spleeter availability
            available, message = self.check_spleeter_availability()
            if not available:
                self.separation_failed.emit(message)
                return
                
            # Setup output directory
            if output_dir is None:
                output_dir = tempfile.mkdtemp(prefix="spleeter_")
                self.temp_dirs.append(output_dir)
                
            # Create and configure worker thread
            spleeter_cmd = self._resolve_spleeter_cmd()
            self.worker = SpleeterWorker(input_file, output_dir, self.config['model'], spleeter_cmd=spleeter_cmd)
            
            # Connect signals
            self.worker.progress_update.connect(self._handle_progress_update)
            self.worker.separation_complete.connect(self._handle_separation_complete)
            self.worker.separation_error.connect(self._handle_separation_error)
            self.worker.finished.connect(self._cleanup_worker)
            
            # Show progress dialog if requested
            if show_progress:
                self._show_progress_dialog()
                
            # Emit started signal and begin processing
            self.separation_started.emit()
            self.worker.start()
            
            self.logger.info(f"Started audio separation for: {input_file}")
            
        except Exception as e:
            error_msg = f"Failed to start separation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.separation_failed.emit(error_msg)
            
    def _show_progress_dialog(self):
        """Show progress dialog for separation process"""
        self.progress_dialog = QProgressDialog(
            "Preparing audio separation...", 
            "Cancel", 
            0, 100
        )
        self.progress_dialog.setWindowTitle("Audio Separation")
        self.progress_dialog.setModal(True)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.canceled.connect(self._cancel_separation)
        self.progress_dialog.show()
        
    def _handle_progress_update(self, message: str, percentage: int):
        """Handle progress updates from worker thread"""
        self.separation_progress.emit(message, percentage)
        
        if self.progress_dialog:
            self.progress_dialog.setLabelText(message)
            self.progress_dialog.setValue(percentage)
            QApplication.processEvents()  # Keep UI responsive
            
    def _handle_separation_complete(self, result: SeparationResult):
        """Handle successful separation completion"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
            
        self.logger.info(f"Separation completed in {result.processing_time:.2f} seconds")
        self.logger.info(f"Generated stems: {list(result.stems.keys())}")
        
        self.separation_completed.emit(result)
        
    def _handle_separation_error(self, error_message: str):
        """Handle separation errors"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
            
        self.logger.error(f"Separation failed: {error_message}")
        self.separation_failed.emit(error_message)
        
    def _cancel_separation(self):
        """Cancel ongoing separation process"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait(5000)  # Wait up to 5 seconds
            
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
            
        self.separation_failed.emit("Separation cancelled by user")
        
    def _cleanup_worker(self):
        """Clean up worker thread resources"""
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
            
    def get_drum_track_path(self, result: SeparationResult) -> Optional[str]:
        """
        Get the path to the separated drum track
        
        Args:
            result: SeparationResult from completed separation
            
        Returns:
            Path to drums.wav file or None if not found
        """
        return result.stems.get('drums')
        
    def cleanup_temp_files(self):
        """Clean up temporary directories and files"""
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    self.logger.info(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                self.logger.warning(f"Failed to clean up {temp_dir}: {e}")
                
        self.temp_dirs.clear()
        
    def __del__(self):
        """Destructor to ensure cleanup"""
        if self.config.get('temp_cleanup', True):
            self.cleanup_temp_files()


# Utility functions for integration

def create_spleeter_service() -> SpleeterService:
    """Factory function to create a configured SpleeterService instance"""
    service = SpleeterService()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    return service


def validate_audio_file(file_path: str) -> Tuple[bool, str]:
    """
    Validate audio file for Spleeter processing
    
    Args:
        file_path: Path to audio file
        
    Returns:
        Tuple of (is_valid, message)
    """
    try:
        if not os.path.exists(file_path):
            return False, "File does not exist"
            
        # Check file extension
        valid_extensions = ['.wav', '.mp3', '.flac', '.m4a']
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext not in valid_extensions:
            return False, f"Unsupported file format: {file_ext}"
            
        # Check file size (reasonable limits)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > 500:  # 500MB limit
            return False, f"File too large: {file_size_mb:.1f}MB (max 500MB)"
            
        return True, "File is valid for processing"
        
    except Exception as e:
        return False, f"Error validating file: {str(e)}"


# Example usage and testing
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Create service
    service = create_spleeter_service()
    
    # Check availability
    available, message = service.check_spleeter_availability()
    print(f"Spleeter availability: {available} - {message}")
    
    if len(sys.argv) > 1:
        # Test with provided audio file
        test_file = sys.argv[1]
        valid, msg = validate_audio_file(test_file)
        print(f"File validation: {valid} - {msg}")
        
        if valid and available:
            def on_complete(result):
                print(f"Separation completed!")
                print(f"Processing time: {result.processing_time:.2f}s")
                print(f"Stems: {list(result.stems.keys())}")
                app.quit()
                
            def on_error(error):
                print(f"Separation failed: {error}")
                app.quit()
                
            service.separation_completed.connect(on_complete)
            service.separation_failed.connect(on_error)
            
            service.separate_audio_async(test_file)
            app.exec()
    else:
        print("Usage: python spleeter_service.py <audio_file>")