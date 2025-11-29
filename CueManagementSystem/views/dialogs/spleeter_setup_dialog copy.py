"""
Spleeter Setup Configuration Dialog
===================================

Dialog for configuring Spleeter installation including automatic Conda installation or manual path selection.

Features:
- Automatic Conda installation option
- Manual Python path selection
- Installation progress tracking
- Path validation
- Configuration persistence
- User-friendly setup wizard
- Error handling and feedback

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFileDialog, QMessageBox, QTextEdit,
                               QProgressBar)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from pathlib import Path
import subprocess
import os
import tempfile
import shutil


class CondaAndSpleeterInstallWorker(QThread):
    """Background thread for Conda + Spleeter installation"""
    progress = Signal(str)  # Progress messages
    finished = Signal(bool, str)  # Success, message/path

    def run(self):
        """Install Conda (if needed) and Spleeter"""
        try:
            # Step 1: Check if conda exists
            self.progress.emit("Checking for conda installation...")

            conda_cmd = self._find_conda()

            if not conda_cmd:
                self.progress.emit("Conda not found. Installing Miniforge...")
                conda_cmd = self._install_miniforge()

                if not conda_cmd:
                    self.finished.emit(False,
                                       "Failed to install Miniforge. Please install manually from:\nhttps://github.com/conda-forge/miniforge")
                    return

                self.progress.emit("✓ Miniforge installed successfully!")
            else:
                self.progress.emit(f"✓ Found conda at: {conda_cmd}")

            # Step 2: Create Spleeter environment
            self.progress.emit("Creating Spleeter environment...")

            env_name = "spleeter_arm"
            result = subprocess.run(
                [conda_cmd, "create", "-n", env_name, "python=3.8", "-y"],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                self.finished.emit(False, f"Failed to create conda environment:\n{result.stderr}")
                return

            self.progress.emit("✓ Environment created successfully!")

            # Step 3: Get Python path
            conda_base = os.path.dirname(os.path.dirname(conda_cmd))
            python_path = os.path.join(conda_base, "envs", env_name, "bin", "python")

            if not os.path.exists(python_path):
                self.finished.emit(False, f"Python not found at expected location: {python_path}")
                return

            # Step 4: Install TensorFlow
            self.progress.emit("Installing TensorFlow for macOS...")

            result = subprocess.run(
                [python_path, "-m", "pip", "install", "tensorflow-macos==2.9.2"],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                self.finished.emit(False, f"Failed to install TensorFlow:\n{result.stderr}")
                return

            self.progress.emit("✓ TensorFlow installed!")

            # Step 5: Install Spleeter
            self.progress.emit("Installing Spleeter...")

            result = subprocess.run(
                [python_path, "-m", "pip", "install", "spleeter"],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                self.finished.emit(False, f"Failed to install Spleeter:\n{result.stderr}")
                return

            self.progress.emit("✓ Spleeter installed!")

            # Step 6: Verify installation
            self.progress.emit("Verifying installation...")

            result = subprocess.run(
                [python_path, "-m", "spleeter", "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                self.finished.emit(False, "Spleeter installed but verification failed")
                return

            self.progress.emit("✓ Installation complete!")
            self.finished.emit(True, python_path)

        except subprocess.TimeoutExpired:
            self.finished.emit(False, "Installation timed out. Please try again.")
        except Exception as e:
            self.finished.emit(False, f"Installation error: {str(e)}")

    def _find_conda(self):
        """Find existing conda installation"""
        conda_paths = [
            os.path.expanduser("~/miniforge3/bin/conda"),
            os.path.expanduser("~/miniconda3/bin/conda"),
            os.path.expanduser("~/anaconda3/bin/conda"),
            "/opt/homebrew/bin/conda",
        ]

        for path in conda_paths:
            if os.path.exists(path):
                return path

        # Try to find in PATH
        result = subprocess.run(
            ["which", "conda"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()

        return None

    def _install_miniforge(self):
        """Install Miniforge for Apple Silicon"""
        try:
            self.progress.emit("Downloading Miniforge installer...")

            # Determine architecture
            result = subprocess.run(
                ["uname", "-m"],
                capture_output=True,
                text=True
            )
            arch = result.stdout.strip()

            # Choose appropriate installer
            if arch == "arm64":
                installer_url = "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh"
            else:
                installer_url = "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-x86_64.sh"

            # Download installer
            temp_dir = tempfile.mkdtemp()
            installer_path = os.path.join(temp_dir, "miniforge.sh")

            self.progress.emit(f"Downloading from {installer_url}...")

            result = subprocess.run(
                ["curl", "-L", "-o", installer_path, installer_url],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                return None

            self.progress.emit("✓ Download complete!")

            # Make executable
            os.chmod(installer_path, 0o755)

            # Install Miniforge
            install_dir = os.path.expanduser("~/miniforge3")

            self.progress.emit(f"Installing Miniforge to {install_dir}...")
            self.progress.emit("(This may take a few minutes...)")

            result = subprocess.run(
                [installer_path, "-b", "-p", install_dir],
                capture_output=True,
                text=True,
                timeout=600
            )

            # Clean up
            shutil.rmtree(temp_dir, ignore_errors=True)

            if result.returncode != 0:
                return None

            # Return conda path
            conda_path = os.path.join(install_dir, "bin", "conda")
            if os.path.exists(conda_path):
                return conda_path

            return None

        except Exception as e:
            self.progress.emit(f"Error installing Miniforge: {e}")
            return None


class SpleeterSetupDialog(QDialog):
    """Dialog for Spleeter configuration with automatic Conda + Spleeter installation"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_path = None
        self.install_worker = None
        self.setWindowTitle("Spleeter Setup")
        self.setMinimumWidth(700)
        self.setMinimumHeight(850)
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI"""
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # Title
        title = QLabel("🎵 Spleeter Audio Separation Setup")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Description
        desc = QLabel(
            "Spleeter is an <b>optional feature</b> that separates drum tracks from music.\n"
            "This improves beat detection accuracy for complex audio files."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #d97706; font-size: 13px; font-weight: bold;")
        layout.addWidget(desc)

        # Installation section
        install_label = QLabel("Option 1: Automatic Installation (Recommended)")
        install_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2563eb;")
        layout.addWidget(install_label)

        install_desc = QLabel(
            "Click the button below to automatically install everything needed.\n"
            "This will install Conda (if needed) and Spleeter with all dependencies."
        )
        install_desc.setWordWrap(True)
        install_desc.setStyleSheet("font-size: 13px; color: white; font-weight: 500; margin-left: 20px;")
        layout.addWidget(install_desc)

        # Install button
        self.install_btn = QPushButton("🚀 Install Everything Automatically")
        self.install_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:disabled {
                background-color: #9ca3af;
            }
        """)
        self.install_btn.clicked.connect(self.install_everything)
        layout.addWidget(self.install_btn)

        # Progress area
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setMaximumHeight(150)
        self.progress_text.setStyleSheet("""
            QTextEdit {
                background-color: #1f2937;
                color: #10b981;
                border: 1px solid #374151;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        self.progress_text.hide()
        layout.addWidget(self.progress_text)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Separator
        separator = QLabel("─" * 80)
        separator.setAlignment(Qt.AlignCenter)
        separator.setStyleSheet("color: #d1d5db;")
        layout.addWidget(separator)

        # Manual configuration section
        manual_label = QLabel("Option 2: Manual Configuration")
        manual_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2563eb;")
        layout.addWidget(manual_label)

        manual_desc = QLabel(
            "If you already have Spleeter installed, you can manually select its Python path."
        )
        manual_desc.setWordWrap(True)
        manual_desc.setStyleSheet("font-size: 13px; color: white; font-weight: 500; margin-left: 20px;")
        layout.addWidget(manual_desc)

        # Manual buttons
        button_layout = QHBoxLayout()

        self.browse_btn = QPushButton("📁 Browse for Python...")
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.browse_btn.clicked.connect(self.browse_for_python)
        button_layout.addWidget(self.browse_btn)

        self.auto_find_btn = QPushButton("🔍 Auto-Find Spleeter")
        self.auto_find_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.auto_find_btn.clicked.connect(self.auto_find_spleeter)
        button_layout.addWidget(self.auto_find_btn)

        layout.addLayout(button_layout)

        # Selected path display
        self.path_label = QLabel("No path selected")
        self.path_label.setStyleSheet("""
            color: #495057;
            font-size: 14px;
            font-weight: bold;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 4px;
        """)
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label)

        # Bottom buttons
        bottom_layout = QHBoxLayout()

        self.skip_btn = QPushButton("Skip for Now")
        self.skip_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 13px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.skip_btn.clicked.connect(self.skip_setup)
        bottom_layout.addWidget(self.skip_btn)

        bottom_layout.addStretch()

        self.save_btn = QPushButton("Save Configuration")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:disabled {
                background-color: #9ca3af;
            }
        """)
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_configuration)
        bottom_layout.addWidget(self.save_btn)

        layout.addLayout(bottom_layout)

        self.setLayout(layout)

    def install_everything(self):
        """Start automatic Conda + Spleeter installation"""
        reply = QMessageBox.question(
            self,
            "Install Conda + Spleeter",
            "This will automatically install:\n\n"
            "1. Miniforge (if conda not found)\n"
            "2. Python 3.8 environment\n"
            "3. TensorFlow for macOS\n"
            "4. Spleeter\n\n"
            "This may take 10-15 minutes depending on your internet speed.\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        # Disable buttons during installation
        self.install_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.auto_find_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)

        # Show progress
        self.progress_text.show()
        self.progress_bar.show()
        self.progress_text.clear()

        # Start installation
        self.install_worker = CondaAndSpleeterInstallWorker()
        self.install_worker.progress.connect(self.on_install_progress)
        self.install_worker.finished.connect(self.on_install_finished)
        self.install_worker.start()

    def on_install_progress(self, message):
        """Handle installation progress updates"""
        self.progress_text.append(f"➤ {message}")
        # Auto-scroll to bottom
        cursor = self.progress_text.textCursor()
        cursor.movePosition(cursor.End)
        self.progress_text.setTextCursor(cursor)

    def on_install_finished(self, success, result):
        """Handle installation completion"""
        self.progress_bar.hide()

        # Re-enable buttons
        self.install_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.auto_find_btn.setEnabled(True)
        self.skip_btn.setEnabled(True)

        if success:
            self.progress_text.append(f"\n✅ SUCCESS! Everything installed at:\n{result}")
            self.selected_path = result
            self.path_label.setText(f"✓ Selected: {result}")
            self.path_label.setStyleSheet("""
                color: #059669;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                background-color: #d1fae5;
                border-radius: 4px;
            """)
            self.save_btn.setEnabled(True)

            QMessageBox.information(
                self,
                "Installation Complete",
                f"Conda and Spleeter have been successfully installed!\n\n"
                f"Python path: {result}\n\n"
                f"Click 'Save Configuration' to finish setup."
            )
        else:
            self.progress_text.append(f"\n❌ FAILED:\n{result}")
            QMessageBox.critical(
                self,
                "Installation Failed",
                f"Failed to install:\n\n{result}\n\n"
                f"You can try manual configuration instead."
            )

    def browse_for_python(self):
        """Browse for Python executable"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Python Executable",
            str(Path.home()),
            "Python Executable (python*)"
        )

        if file_path:
            if self.validate_spleeter_path(file_path):
                self.selected_path = file_path
                self.path_label.setText(f"✓ Selected: {file_path}")
                self.path_label.setStyleSheet("""
                    color: #059669;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 10px;
                    background-color: #d1fae5;
                    border-radius: 4px;
                """)
                self.save_btn.setEnabled(True)
            else:
                QMessageBox.warning(
                    self,
                    "Invalid Path",
                    f"Spleeter is not installed in this Python environment:\n{file_path}"
                )

    def auto_find_spleeter(self):
        """Auto-discover Spleeter installation"""
        from utils.audio.spleeter_service import find_spleeter_python

        path = find_spleeter_python()

        if path:
            self.selected_path = path
            self.path_label.setText(f"✓ Found: {path}")
            self.path_label.setStyleSheet("""
                color: #059669;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                background-color: #d1fae5;
                border-radius: 4px;
            """)
            self.save_btn.setEnabled(True)
            QMessageBox.information(
                self,
                "Spleeter Found",
                f"Found Spleeter at:\n{path}"
            )
        else:
            QMessageBox.information(
                self,
                "Not Found",
                "Could not find Spleeter installation.\n\n"
                "Try automatic installation or browse manually."
            )

    def validate_spleeter_path(self, path):
        """Validate that path has Spleeter installed"""
        from utils.audio.spleeter_service import validate_spleeter_path
        return validate_spleeter_path(path)

    def skip_setup(self):
        """Skip Spleeter setup"""
        self.selected_path = None
        self.accept()

    def save_configuration(self):
        """Save Spleeter configuration"""
        if self.selected_path:
            from config_manager import get_config_manager
            config = get_config_manager()
            config.set_spleeter_path(self.selected_path)
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "No Path Selected",
                "Please select a Spleeter Python path or skip setup."
            )