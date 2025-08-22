"""
Simple file editor for use within the terminal interface.
This provides a basic text editing experience similar to nano.
"""

import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
                               QPushButton, QLabel, QLineEdit, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QTextCursor, QShortcut, QKeySequence


class SimpleFileEditor(QDialog):
    def __init__(self, filename, ssh_client=None, parent=None):
        super().__init__(parent)

        self.filename = filename
        self.ssh_client = ssh_client
        self.content = ""
        self.is_new_file = True

        # Set up UI
        self.setWindowTitle(f"Edit: {filename}")
        self.resize(800, 600)
        self.setup_ui()

        # Try to load file content if it exists
        self.load_file_content()

    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout(self)

        # File info
        info_layout = QHBoxLayout()
        self.file_label = QLabel(f"File: {self.filename}")
        info_layout.addWidget(self.file_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)

        # Editor
        self.editor = QTextEdit()
        font = QFont("Courier New", 12)
        font.setStyleHint(QFont.Monospace)
        self.editor.setFont(font)
        self.editor.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #f0f0f0;
                border: 1px solid #444444;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.editor)

        # Help text
        help_text = QLabel("Ctrl+S: Save | Ctrl+Q: Quit | Ctrl+X: Save and Quit")
        help_text.setStyleSheet("color: #888888; font-style: italic;")
        layout.addWidget(help_text)

        # Buttons
        button_layout = QHBoxLayout()

        self.save_button = QPushButton("Save")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.save_button.clicked.connect(self.save_file)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)

        self.save_exit_button = QPushButton("Save & Exit")
        self.save_exit_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.save_exit_button.clicked.connect(self.save_and_exit)

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.save_exit_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        # Set up keyboard shortcuts
        self.setup_shortcuts()

    def setup_shortcuts(self):
        # Ctrl+S: Save
        self.save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.save_shortcut.activated.connect(self.save_file)

        # Ctrl+Q: Quit
        self.quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        self.quit_shortcut.activated.connect(self.reject)

        # Ctrl+X: Save and Quit
        self.save_quit_shortcut = QShortcut(QKeySequence("Ctrl+X"), self)
        self.save_quit_shortcut.activated.connect(self.save_and_exit)

    def load_file_content(self):
        """Load file content from SSH if available"""
        if not self.ssh_client:
            return

        try:
            # Check if file exists
            stdin, stdout, stderr = self.ssh_client.exec_command(f"test -f {self.filename} && echo 'exists'")
            result = stdout.read().decode().strip()

            if result == 'exists':
                self.is_new_file = False
                # Read file content
                stdin, stdout, stderr = self.ssh_client.exec_command(f"cat {self.filename}")
                self.content = stdout.read().decode()
                self.editor.setText(self.content)
                self.file_label.setText(f"Editing existing file: {self.filename}")
            else:
                self.is_new_file = True
                self.file_label.setText(f"Creating new file: {self.filename}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load file: {str(e)}")

    def save_file(self):
        """Save file content via SSH"""
        if not self.ssh_client:
            QMessageBox.warning(self, "Error", "No SSH connection available")
            return

        try:
            # Get content from editor
            content = self.editor.toPlainText()

            # Escape special characters for shell
            escaped_content = content.replace("'", "'\\''")

            # Write content to file
            command = f"echo '{escaped_content}' > {self.filename}"
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()

            if exit_status == 0:
                self.content = content
                self.is_new_file = False
                self.file_label.setText(f"Editing existing file: {self.filename}")
                QMessageBox.information(self, "Success", f"File {self.filename} saved successfully")
                return True
            else:
                error = stderr.read().decode()
                QMessageBox.warning(self, "Error", f"Failed to save file: {error}")
                return False
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save file: {str(e)}")
            return False

    def save_and_exit(self):
        """Save file and close dialog"""
        if self.save_file():
            self.accept()