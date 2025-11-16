"""
Spleeter Audio Separation Service
==================================

A comprehensive service for integrating Spleeter audio source separation into the
CuePiShifter application. This service handles automatic discovery of Spleeter
installations, background processing with progress updates, and management of
separated audio stems for drum track analysis.

Features:
- Auto-discovery of Spleeter installations (conda, venv, system-wide)
- Support for both Apple Silicon (spleeter_arm) and Intel (spleeter_cpu) environments
- Background thread processing to prevent UI blocking
- Real-time progress updates with percentage and status messages
- Multiple stem separation models (2stems, 4stems, 5stems)
- Automatic drum track extraction and path resolution
- Comprehensive error handling and validation
- Temporary file management and cleanup
- PyInstaller windowed app compatibility
- Configuration persistence for discovered paths
- Cancellation support for long-running operations

Author: Michael Lyman
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

# Import config manager for dynamic Spleeter path
try:
    from config_manager import get_config_manager
except ImportError:
    # Fallback if config_manager not available
    def get_config_manager():
        return None


def find_spleeter_python() -> Optional[str]:
    """
    Auto-discover Spleeter Python installation

    FIXED: Now searches for both spleeter_arm AND spleeter_cpu

    Returns:
        Path to Spleeter Python executable, or None if not found
    """
    # First check config
    try:
        config = get_config_manager()
        if config:
            saved_path = config.get_spleeter_path()

            if saved_path and validate_spleeter_path(saved_path):
                print(f"✓ Using Spleeter from config: {saved_path}")
                return saved_path
    except Exception as e:
        print(f"Config check failed: {e}")

    # Check environment variable (backward compatibility)
    env_path = os.environ.get('CUE_SPLEETER_PATH')
    if env_path and validate_spleeter_path(env_path):
        print(f"✓ Using Spleeter from CUE_SPLEETER_PATH: {env_path}")
        return env_path

    # Auto-discover common locations
    print("🔍 Auto-discovering Spleeter installation...")

    # FIXED: Search for BOTH spleeter_arm (Apple Silicon) AND spleeter_cpu
    common_paths = [
        # Apple Silicon paths (HIGHEST PRIORITY)
        Path.home() / "miniforge3" / "envs" / "spleeter_arm" / "bin" / "python",
        Path.home() / "anaconda3" / "envs" / "spleeter_arm" / "bin" / "python",
        Path.home() / "miniconda3" / "envs" / "spleeter_arm" / "bin" / "python",

        # Intel/CPU paths
        Path.home() / ".venvs" / "spleeter_cpu" / "bin" / "python",
        Path.home() / "anaconda3" / "envs" / "spleeter_cpu" / "bin" / "python",
        Path.home() / "miniconda3" / "envs" / "spleeter_cpu" / "bin" / "python",

        # System-wide installations
        Path("/opt/anaconda3/envs/spleeter_arm/bin/python"),
        Path("/opt/miniconda3/envs/spleeter_arm/bin/python"),
        Path("/opt/anaconda3/envs/spleeter_cpu/bin/python"),
        Path("/opt/miniconda3/envs/spleeter_cpu/bin/python"),
        Path("/usr/local/anaconda3/envs/spleeter_cpu/bin/python"),
    ]

    for path in common_paths:
        if validate_spleeter_path(str(path)):
            print(f"✓ Found Spleeter at: {path}")
            # Save discovered path to config
            try:
                config = get_config_manager()
                if config:
                    config.set_spleeter_path(str(path))
            except Exception as e:
                print(f"Could not save to config: {e}")
            return str(path)

    print("⚠️  Spleeter not found in common locations")
    return None


def validate_spleeter_path(path: str) -> bool:
    """
    Validate that a path points to a working Spleeter installation

    Args:
        path: Path to Python executable

    Returns:
        True if valid, False otherwise
    """
    if not path or not os.path.exists(path):
        return False

    # Check if it's executable
    if not os.access(path, os.X_OK):
        return False

    # Try to import spleeter
    try:
        # CRITICAL FIX: Added stdin, stdout, stderr and env for PyInstaller windowed apps
        result = subprocess.run(
            [path, "-c", "import spleeter; print('OK')"],
            stdin=subprocess.PIPE,  # CRITICAL: Required for windowed apps
            stdout=subprocess.PIPE,  # Capture output
            stderr=subprocess.PIPE,  # Capture errors
            text=True,
            timeout=10,
            env=os.environ.copy()  # CRITICAL: Pass environment variables
        )
        return result.returncode == 0 and "OK" in result.stdout
    except Exception:
        return False


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

            # FIXED: Properly handle both "python -m spleeter" and direct "spleeter" commands
            if " -m spleeter" in self.spleeter_cmd:
                # It's a Python command like "/path/to/python -m spleeter"
                import shlex
                # Get base filename for flat naming
                base_name = os.path.splitext(os.path.basename(self.input_file))[0]
                cmd_parts = shlex.split(self.spleeter_cmd)
                cmd = cmd_parts + [
                    "separate",
                    "-p", f"spleeter:{self.model}",
                    "-o", self.output_dir,
                    "-f", f"{base_name}_{{instrument}}.{{codec}}",
                    self.input_file
                ]
            else:
                # It's a direct spleeter command
                # Get base filename for flat naming
                base_name = os.path.splitext(os.path.basename(self.input_file))[0]
                cmd = [
                    self.spleeter_cmd, "separate",
                    "-p", f"spleeter:{self.model}",
                    "-o", self.output_dir,
                    "-f", f"{base_name}_{{instrument}}.{{codec}}",
                    self.input_file
                ]

            self.logger.info(f"Starting Spleeter separation: {' '.join(cmd)}")
            self.progress_update.emit("Starting audio separation process...", 10)

            # Execute Spleeter
            # CRITICAL FIX: Added stdin and env for PyInstaller windowed apps
            # Also add ffmpeg to PATH so Spleeter can find it
            env = os.environ.copy()

            # Add common ffmpeg locations to PATH
            ffmpeg_paths = [
                '/opt/homebrew/bin',  # Homebrew on Apple Silicon
                '/usr/local/bin',  # Homebrew on Intel
            ]

            current_path = env.get('PATH', '')
            for ffmpeg_path in ffmpeg_paths:
                if ffmpeg_path not in current_path:
                    env['PATH'] = f"{ffmpeg_path}:{current_path}"
                    current_path = env['PATH']

            # Set Spleeter model directory to a writable location
            # This prevents "Read-only file system" errors when running from app bundle
            model_dir = os.path.expanduser('~/.spleeter_models')
            os.makedirs(model_dir, exist_ok=True)
            env['MODEL_PATH'] = model_dir

            self.logger.info(f"Updated PATH for subprocess: {env['PATH']}")
            self.logger.info(f"Set MODEL_PATH to: {model_dir}")

            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,  # CRITICAL: Required for windowed apps
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True,
                env=env  # CRITICAL: Pass environment with ffmpeg in PATH
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

            # Log subprocess output for debugging
            if stdout:
                self.logger.info(f"Spleeter stdout: {stdout}")
            if stderr:
                self.logger.info(f"Spleeter stderr: {stderr}")
            self.logger.info(f"Spleeter return code: {process.returncode}")

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
        """Find and validate separated stem files, moving them to flat structure"""
        import shutil
        stems = {}

        # Get the base filename without extension
        input_path = Path(self.input_file)
        base_name = input_path.stem

        # Expected stem names for 5stems model
        expected_stems = ["vocals", "drums", "bass", "piano", "other"]

        output_path = Path(self.output_dir)

        # FIRST: Check for flat files (what -f option should create)
        self.logger.info("Checking for flat files first (expected with -f option)")
        flat_files_found = True
        for stem_name in expected_stems:
            stem_file = output_path / f"{base_name}_{stem_name}.wav"
            if stem_file.exists():
                stems[stem_name] = str(stem_file)
                self.logger.info(f"Found {stem_name} stem: {stem_file}")
            else:
                flat_files_found = False
                break

        # If all flat files found, return immediately
        if flat_files_found and len(stems) == len(expected_stems):
            self.logger.info("All stems found in flat structure - success!")
            return stems

        # FALLBACK: Check subdirectories (in case -f didn't work)
        self.logger.info("Flat files not found, checking subdirectories")
        stems = {}  # Reset

        possible_dirs = [
            output_path / base_name / f"{base_name}_stems",  # MUSIC/One/One_stems/
            output_path / base_name,  # MUSIC/One/
            output_path / f"{base_name}_stems",  # MUSIC/One_stems/
        ]

        separation_dir = None
        for dir_path in possible_dirs:
            if dir_path.exists():
                separation_dir = dir_path
                self.logger.info(f"Found Spleeter subdirectory: {separation_dir}")
                break

        if separation_dir:
            for stem_name in expected_stems:
                possible_files = [
                    separation_dir / f"{base_name}_{stem_name}.wav",
                    separation_dir / f"{stem_name}.wav",
                ]

                stem_file_in_subdir = None
                for file_path in possible_files:
                    if file_path.exists():
                        stem_file_in_subdir = file_path
                        break

                if stem_file_in_subdir:
                    flat_stem_file = output_path / f"{base_name}_{stem_name}.wav"

                    try:
                        shutil.move(str(stem_file_in_subdir), str(flat_stem_file))
                        stems[stem_name] = str(flat_stem_file)
                        self.logger.info(f"Moved {stem_name} stem to: {flat_stem_file}")
                    except Exception as e:
                        self.logger.error(f"Failed to move {stem_name} stem: {e}")
                        stems[stem_name] = str(stem_file_in_subdir)
                else:
                    self.logger.warning(f"Missing {stem_name} stem file in {separation_dir}")

            try:
                if separation_dir.exists() and not list(separation_dir.iterdir()):
                    shutil.rmtree(separation_dir)
                    self.logger.info(f"Cleaned up subdirectory: {separation_dir}")

                    parent_dir = separation_dir.parent
                    if parent_dir != output_path and parent_dir.exists() and not list(parent_dir.iterdir()):
                        shutil.rmtree(parent_dir)
                        self.logger.info(f"Cleaned up parent subdirectory: {parent_dir}")
            except Exception as e:
                self.logger.warning(f"Could not remove subdirectory: {e}")

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
            'spleeter_command': os.environ.get('CUE_SPLEETER_PATH') or 'spleeter'
        }

    def _resolve_spleeter_cmd(self) -> str:
        """Resolve the spleeter executable path from config/env or PATH."""
        try:
            # Try to find Python with Spleeter installed
            python_path = find_spleeter_python()

            if python_path:
                # Return command to run spleeter via Python
                return f'"{python_path}" -m spleeter'

            # Fallback: try spleeter command directly
            import shutil as _shutil
            cmd = self.config.get('spleeter_command') or 'spleeter'
            resolved = _shutil.which(cmd)
            return resolved or cmd
        except Exception:
            return self.config.get('spleeter_command') or 'spleeter'

    def check_spleeter_availability(self) -> Tuple[bool, str]:
        """
        Check if Spleeter is properly installed and available

        FIXED: Properly handles commands with spaces and shows actual errors

        Returns:
            Tuple of (is_available, status_message)
        """
        try:
            cmd = self._resolve_spleeter_cmd()

            # FIXED: Properly handle commands with spaces
            if isinstance(cmd, str) and ' -m spleeter' in cmd:
                # It's a Python command like "/path/to/python -m spleeter"
                import shlex
                cmd_parts = shlex.split(cmd)
                cmd_parts.append("--help")
            else:
                cmd_parts = [cmd, "--help"]

            # CRITICAL FIX: Added stdin, stdout, stderr and env for PyInstaller windowed apps
            result = subprocess.run(
                cmd_parts,
                stdin=subprocess.PIPE,  # CRITICAL: Required for windowed apps
                stdout=subprocess.PIPE,  # Capture output
                stderr=subprocess.PIPE,  # Capture errors
                text=True,
                timeout=10,
                env=os.environ.copy()  # CRITICAL: Pass environment variables
            )

            if result.returncode == 0:
                return True, "Spleeter is available and ready"

            # FIXED: Show the actual error message from stderr
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

            # FIXED: Show the actual error - extract the most relevant line
            error_lines = combined.strip().split('\n')
            # Get the most relevant error line (usually the last one with actual content)
            relevant_error = None
            for line in reversed(error_lines):
                if line.strip() and not line.startswith('File '):
                    relevant_error = line.strip()
                    break

            if relevant_error:
                return False, f"Spleeter command failed: {relevant_error}"
            else:
                return False, f"Spleeter command failed with return code {result.returncode}"

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

            # Setup output directory - USE CONFIGURED FOLDER
            if output_dir is None:
                # Import here to avoid circular imports
                config_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                if config_path not in sys.path:
                    sys.path.insert(0, config_path)

                try:
                    from config_manager import ConfigManager

                    config = ConfigManager()
                    output_dir = config.get_stems_folder()

                    if not output_dir:
                        self.separation_failed.emit(
                            "Stems output folder not configured.\n\n"
                            "Please configure in CuePi → Configure Stems Folder."
                        )
                        return

                    # FIXED: Save directly to configured folder (no subdirectories)
                    # This avoids macOS permission issues with subdirectories

                    # Ensure output directory exists
                    os.makedirs(output_dir, exist_ok=True)

                    self.logger.info(f"Using configured stems folder: {output_dir}")

                except Exception as e:
                    error_msg = f"Failed to get stems folder configuration: {str(e)}"
                    self.logger.error(error_msg)
                    # Fallback to temp directory
                    output_dir = tempfile.mkdtemp(prefix="spleeter_")
                    self.temp_dirs.append(output_dir)
                    self.logger.warning(f"Using temporary directory as fallback: {output_dir}")

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