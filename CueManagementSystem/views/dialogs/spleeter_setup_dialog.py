"""
Spleeter Setup Dialog
Helps users locate their Spleeter installation on first launch
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QMessageBox, QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import os
import subprocess
from pathlib import Path


class SpleeterSetupDialog(QDialog):
    """Dialog to help user locate Spleeter installation"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_path = None
        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("CuePi Setup - Locate Spleeter")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title = QLabel("Welcome to CuePi!")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Professional Firework Cue Management System")
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # Instructions
        instructions = QTextEdit()
        instructions.setReadOnly(True)
        instructions.setMaximumHeight(250)
        instructions.setHtml("""
        <style>
            body { font-size: 13px; line-height: 1.6; }
            h3 { color: #2c3e50; margin-top: 15px; }
            ul { margin-left: 20px; }
            li { margin-bottom: 8px; }
            .highlight { background-color: #fff3cd; padding: 2px 5px; border-radius: 3px; }
        </style>

        <h3>🎵 Audio Separation Setup (Optional)</h3>
        <p>CuePi can use <b>Spleeter</b> to separate audio tracks into individual stems 
        (vocals, drums, bass, etc.). This is an <span class="highlight">optional feature</span> 
        for advanced audio analysis.</p>

        <h3>✅ If you have Spleeter installed:</h3>
        <ul>
            <li>Click <b>"Browse"</b> below to locate your Spleeter Python executable</li>
            <li><b>Common locations:</b>
                <ul>
                    <li><code>~/anaconda3/envs/spleeter_cpu/bin/python</code></li>
                    <li><code>~/miniconda3/envs/spleeter_cpu/bin/python</code></li>
                    <li><code>~/.venvs/spleeter_cpu/bin/python</code></li>
                </ul>
            </li>
        </ul>

        <h3>⏭️ If you don't have Spleeter:</h3>
        <ul>
            <li>Click <b>"Skip"</b> to use CuePi without audio separation</li>
            <li>All other features will work perfectly!</li>
            <li>You can configure Spleeter later in <b>Preferences → Configure Spleeter</b></li>
        </ul>
        """)
        layout.addWidget(instructions)

        # Path display
        self.path_label = QLabel("No path selected")
        self.path_label.setStyleSheet("""
            QLabel {
                padding: 15px;
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label)

        # Browse button
        browse_btn = QPushButton("📁 Browse for Spleeter Python...")
        browse_btn.clicked.connect(self.browse_for_spleeter)
        browse_btn.setMinimumHeight(45)
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        layout.addWidget(browse_btn)

        layout.addSpacing(10)

        # Buttons
        button_layout = QHBoxLayout()

        skip_btn = QPushButton("Skip (Use Without Spleeter)")
        skip_btn.clicked.connect(self.skip_setup)
        skip_btn.setMinimumHeight(40)
        skip_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        button_layout.addWidget(skip_btn)

        button_layout.addStretch()

        self.ok_btn = QPushButton("✓ Continue")
        self.ok_btn.clicked.connect(self.accept_setup)
        self.ok_btn.setEnabled(False)
        self.ok_btn.setMinimumWidth(150)
        self.ok_btn.setMinimumHeight(40)
        self.ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
            QPushButton:disabled {
                background-color: #c3e6cb;
                color: #6c757d;
            }
        """)
        button_layout.addWidget(self.ok_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def validate_spleeter_path(self, path: str) -> bool:
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
            result = subprocess.run(
                [path, "-c", "import spleeter; print('OK')"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0 and "OK" in result.stdout
        except Exception as e:
            print(f"Validation error: {e}")
            return False

    def browse_for_spleeter(self):
        """Open file browser to select Spleeter Python"""
        # Start in home directory
        start_dir = str(Path.home())

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Spleeter Python Executable",
            start_dir,
            "Python Executable (python python3);;All Files (*)"
        )

        if file_path:
            # Show validation message
            self.path_label.setText(f"⏳ Validating: {file_path}\n\nPlease wait...")
            self.path_label.setStyleSheet("""
                QLabel {
                    padding: 15px;
                    background-color: #fff3cd;
                    border: 2px solid #ffc107;
                    border-radius: 6px;
                    font-family: monospace;
                    font-size: 12px;
                    color: #856404;
                }
            """)

            # Process events to show the message
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()

            # Validate the path
            if self.validate_spleeter_path(file_path):
                self.selected_path = file_path
                self.path_label.setText(f"✓ Valid Spleeter installation found!\n\n{file_path}")
                self.path_label.setStyleSheet("""
                    QLabel {
                        padding: 15px;
                        background-color: #d4edda;
                        border: 2px solid #28a745;
                        border-radius: 6px;
                        font-family: monospace;
                        font-size: 12px;
                        color: #155724;
                    }
                """)
                self.ok_btn.setEnabled(True)
            else:
                self.path_label.setText(
                    f"✗ Invalid Spleeter installation\n\n{file_path}\n\nSpleeter is not installed in this Python environment.")
                self.path_label.setStyleSheet("""
                    QLabel {
                        padding: 15px;
                        background-color: #f8d7da;
                        border: 2px solid #dc3545;
                        border-radius: 6px;
                        font-family: monospace;
                        font-size: 12px;
                        color: #721c24;
                    }
                """)
                self.ok_btn.setEnabled(False)

                QMessageBox.warning(
                    self,
                    "Invalid Spleeter Installation",
                    "<b>The selected Python executable does not have Spleeter installed.</b><br><br>"
                    "Please select a Python executable from a Spleeter environment.<br><br>"
                    "<b>To install Spleeter:</b><br>"
                    "1. Create a conda environment: <code>conda create -n spleeter_cpu python=3.8</code><br>"
                    "2. Activate it: <code>conda activate spleeter_cpu</code><br>"
                    "3. Install Spleeter: <code>pip install spleeter</code><br>"
                    "4. Then select the Python executable from that environment."
                )

    def accept_setup(self):
        """Accept and save the selected path"""
        if self.selected_path:
            # Import here to avoid circular imports
            from config_manager import get_config_manager
            config = get_config_manager()
            config.set_spleeter_path(self.selected_path)
            config.mark_launched()
            self.accept()

    def skip_setup(self):
        """Skip Spleeter setup"""
        # Import here to avoid circular imports
        from config_manager import get_config_manager
        config = get_config_manager()
        config.mark_launched()
        self.reject()