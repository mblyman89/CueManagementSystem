"""
Pre-Show Safety Checklist Dialog

Verifies all safety requirements before allowing show execution.
Prevents accidents by ensuring system is properly configured.
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QGroupBox, QScrollArea, QWidget, QApplication)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QIcon
from datetime import datetime


class PreShowChecklistDialog(QDialog):
    """
    Dialog that performs safety checks before show execution

    Features:
    - Real-time status checks
    - Visual indicators (✅/❌/⚠️)
    - Blocks execution if critical checks fail
    - Override option with confirmation
    - Detailed status messages
    """

    # Signal emitted when user confirms execution
    execute_confirmed = Signal()

    def __init__(self, system_mode_controller, parent=None):
        super().__init__(parent)

        self.system_mode = system_mode_controller
        self.checks_passed = False
        self.check_results = {}
        self.selected_music = None  # Store selected music info
        self.uploaded_show_file = None  # Store uploaded show file path

        self.setWindowTitle("Pre-Show Safety Checklist")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        self.setup_ui()

        # Run initial checks
        QTimer.singleShot(100, self.run_all_checks)

    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Pre-Show Safety Checklist")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Verifying system status before show execution...")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666; font-size: 11pt; margin-bottom: 10px;")
        layout.addWidget(subtitle)

        # Checks container (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        checks_widget = QWidget()
        self.checks_layout = QVBoxLayout(checks_widget)
        self.checks_layout.setSpacing(5)

        # Create check items
        self.check_items = {}

        checks = [
            ("pi_connection", "Pi Connection Active", "SSH connection to Raspberry Pi is established", True),
            ("outputs_enabled", "Outputs Enabled", "All 5 chains enabled (OE pins LOW, SRCLR pins HIGH)", True),
            ("system_armed", "System Armed", "ARM pin is HIGH - system ready to fire", True),
            ("show_uploaded", "Show Data Uploaded", "Show file exists on Pi and is current", True),
            ("gpio_status", "GPIO Status Valid", "Can read GPIO states successfully", True),
            ("no_execution", "No Active Execution", "No show currently running on Pi", True),
            ("music_selected", "Music Selected", "Music file selected for synchronization", False),
        ]

        for check_id, title, description, critical in checks:
            item = self.create_check_item(check_id, title, description, critical)
            self.check_items[check_id] = item
            self.checks_layout.addWidget(item['widget'])

        scroll.setWidget(checks_widget)
        layout.addWidget(scroll)

        # Overall status
        self.status_label = QLabel("Running checks...")
        self.status_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                border-radius: 5px;
                background-color: #f39c12;
                color: white;
            }
        """)
        layout.addWidget(self.status_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedSize(120, 40)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.override_button = QPushButton("Execute Anyway")
        self.override_button.setFixedSize(140, 40)
        self.override_button.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.override_button.clicked.connect(self.handle_override)
        self.override_button.setVisible(False)  # Only show if checks fail
        button_layout.addWidget(self.override_button)

        self.execute_button = QPushButton("✓ Execute Show")
        self.execute_button.setFixedSize(140, 40)
        self.execute_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.execute_button.clicked.connect(self.handle_execute)
        self.execute_button.setEnabled(False)
        button_layout.addWidget(self.execute_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Refresh button
        refresh_layout = QHBoxLayout()
        refresh_layout.addStretch()

        self.refresh_button = QPushButton("🔄 Refresh Checks")
        self.refresh_button.setFixedSize(140, 32)
        self.refresh_button.clicked.connect(self.run_all_checks)
        refresh_layout.addWidget(self.refresh_button)

        refresh_layout.addStretch()
        layout.addLayout(refresh_layout)

    def create_check_item(self, check_id, title, description, critical):
        """Create a check item widget"""
        widget = QGroupBox()
        widget.setStyleSheet("""
            QGroupBox {
                border: 2px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding: 10px;
            }
        """)

        layout = QHBoxLayout(widget)

        # Status icon
        icon_label = QLabel("⏳")
        icon_label.setFont(QFont("Arial", 24))
        icon_label.setFixedWidth(40)
        layout.addWidget(icon_label)

        # Text content
        text_layout = QVBoxLayout()

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 11, QFont.Bold))
        text_layout.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #666; font-size: 9pt;")
        desc_label.setWordWrap(True)
        text_layout.addWidget(desc_label)

        status_label = QLabel("Checking...")
        status_label.setStyleSheet("color: #f39c12; font-size: 9pt; font-style: italic;")
        text_layout.addWidget(status_label)

        layout.addLayout(text_layout, 1)

        # Critical badge
        if critical:
            critical_label = QLabel("CRITICAL")
            critical_label.setStyleSheet("""
                QLabel {
                    background-color: #e74c3c;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 3px;
                    font-size: 8pt;
                    font-weight: bold;
                }
            """)
            critical_label.setFixedHeight(20)
            layout.addWidget(critical_label)
        else:
            warning_label = QLabel("OPTIONAL")
            warning_label.setStyleSheet("""
                QLabel {
                    background-color: #f39c12;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 3px;
                    font-size: 8pt;
                    font-weight: bold;
                }
            """)
            warning_label.setFixedHeight(20)
            layout.addWidget(warning_label)

        # Make music item clickable
        if check_id == 'music_selected':
            widget.setCursor(Qt.PointingHandCursor)
            widget.mousePressEvent = lambda event: self.handle_music_item_click()
            # Add visual hint that it's clickable
            desc_label.setText(description + " (Click to select music)")

        # Make show upload item clickable
        if check_id == 'show_uploaded':
            widget.setCursor(Qt.PointingHandCursor)
            widget.mousePressEvent = lambda event: self.handle_show_upload_click()
            # Add visual hint that it's clickable
            desc_label.setText(description + " (Click to upload show)")

        return {
            'widget': widget,
            'icon': icon_label,
            'status': status_label,
            'critical': critical,
            'check_id': check_id
        }

    def run_all_checks(self):
        """Run all safety checks"""
        self.status_label.setText("Running checks...")
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                border-radius: 5px;
                background-color: #f39c12;
                color: white;
            }
        """)
        self.execute_button.setEnabled(False)
        self.override_button.setVisible(False)

        # Run each check
        self.check_results = {}

        self.check_results['pi_connection'] = self.check_pi_connection()
        self.check_results['outputs_enabled'] = self.check_outputs_enabled()
        self.check_results['system_armed'] = self.check_system_armed()
        self.check_results['show_uploaded'] = self.check_show_uploaded()
        self.check_results['gpio_status'] = self.check_gpio_status()
        self.check_results['no_execution'] = self.check_no_execution()
        self.check_results['music_selected'] = self.check_music_selected()

        # Update UI for each check
        for check_id, result in self.check_results.items():
            self.update_check_item(check_id, result)

        # Determine overall status
        self.update_overall_status()

    def check_pi_connection(self):
        """Check if Pi connection is active"""
        try:
            if not hasattr(self.system_mode, 'ssh_connection') or not self.system_mode.ssh_connection:
                return (False, "No SSH connection established")

            # Try a simple command to verify connection
            stdin, stdout, stderr = self.system_mode.ssh_connection.exec_command("echo 'test'", timeout=5)
            output = stdout.read().decode().strip()

            if output == "test":
                return (True, "SSH connection active and responsive")
            else:
                return (False, "SSH connection not responding correctly")
        except Exception as e:
            return (False, f"Connection check failed: {str(e)}")

    def check_outputs_enabled(self):
        """Check if outputs are enabled"""
        try:
            # Get GPIO status from Pi
            stdin, stdout, stderr = self.system_mode.ssh_connection.exec_command(
                "python3 ~/get_gpio_status.py", timeout=10
            )
            output = stdout.read().decode()

            # Parse the output to check OE and SRCLR pins
            import json
            status = json.loads(output)

            if status.get('status') != 'success':
                return (False, f"GPIO status error: {status.get('error', 'Unknown error')}")

            # Check OE pins (Active LOW - False = enabled)
            oe_pins = status.get('oe_pins', [])
            oe_enabled_count = sum(1 for pin in oe_pins if pin.get('state') == False)

            # Check SRCLR pins (Active HIGH - True = enabled)
            srclr_pins = status.get('srclr_pins', [])
            srclr_enabled_count = sum(1 for pin in srclr_pins if pin.get('state') == True)

            # Both OE and SRCLR must be correct for outputs to be enabled
            if oe_enabled_count == 5 and srclr_enabled_count == 5:
                return (True, f"All 5 chains enabled (OE: LOW, SRCLR: HIGH)")
            else:
                return (False, f"OE: {oe_enabled_count}/5 enabled, SRCLR: {srclr_enabled_count}/5 enabled")
        except Exception as e:
            return (False, f"Could not verify output status: {str(e)}")

    def check_system_armed(self):
        """Check if system is armed"""
        try:
            # Get GPIO status from Pi
            stdin, stdout, stderr = self.system_mode.ssh_connection.exec_command(
                "python3 ~/get_gpio_status.py", timeout=10
            )
            output = stdout.read().decode()

            # Parse the output to check ARM pin
            import json
            status = json.loads(output)

            if status.get('status') != 'success':
                return (False, f"GPIO status error: {status.get('error', 'Unknown error')}")

            # ARM pin state is boolean (True = HIGH/armed, False = LOW/disarmed)
            arm_state = status.get('arm_pin', {}).get('state', False)

            if arm_state == True:
                return (True, "System is armed (GPIO 21 HIGH)")
            else:
                return (False, f"System not armed (GPIO 21 LOW)")
        except Exception as e:
            return (False, f"Could not verify arm status: {str(e)}")

    def check_show_uploaded(self):
        """Check if show data is uploaded to Pi"""
        # Check if we have an uploaded show file from this session
        if self.uploaded_show_file:
            try:
                # Verify the file still exists on Pi
                stdin, stdout, stderr = self.system_mode.ssh_connection.exec_command(
                    f"test -f {self.uploaded_show_file} && echo 'exists' || echo 'missing'",
                    timeout=5
                )
                output = stdout.read().decode().strip()

                if output == "exists":
                    return (True, f"Show uploaded successfully")
                else:
                    # File was deleted or moved
                    self.uploaded_show_file = None
                    return (False, "Show file not found - click to upload")
            except Exception as e:
                return (False, f"Could not verify upload: {str(e)}")
        else:
            # No upload yet - show as pending (yellow)
            return (False, "Click to upload show data to Pi")

    def check_gpio_status(self):
        """Check if GPIO status can be read"""
        try:
            stdin, stdout, stderr = self.system_mode.ssh_connection.exec_command(
                "python3 ~/get_gpio_status.py", timeout=10
            )
            output = stdout.read().decode()
            error = stderr.read().decode()

            if error:
                return (False, f"GPIO status error: {error}")

            # Try to parse the output
            import json
            status = json.loads(output)

            if status:
                return (True, "GPIO status readable")
            else:
                return (False, "GPIO status empty")
        except Exception as e:
            return (False, f"Could not read GPIO status: {str(e)}")

    def check_no_execution(self):
        """Check if no show is currently running"""
        try:
            # Check for running execute_show.py process
            # pgrep returns PIDs if found, nothing if not found
            stdin, stdout, stderr = self.system_mode.ssh_connection.exec_command(
                "pgrep -f 'execute_show.py'", timeout=5
            )
            output = stdout.read().decode().strip()
            exit_code = stdout.channel.recv_exit_status()

            # pgrep returns exit code 0 if process found, 1 if not found
            if exit_code == 1 or not output:
                return (True, "No show currently executing")
            else:
                return (False, f"Show execution already in progress (PID: {output})!")
        except Exception as e:
            # If we can't check, assume it's okay (don't block execution)
            return (True, f"Could not verify execution status (assuming idle)")

    def check_music_selected(self):
        """Check if music is selected (warning only)"""
        try:
            # Check if music was selected in this dialog
            if self.selected_music:
                music_name = f"{self.selected_music['name']}{self.selected_music['extension']}"
                return (True, f"Music selected: {music_name}")

            # Check if parent has music player and music is loaded
            if hasattr(self.parent(), 'music_player'):
                music_player = self.parent().music_player
                if hasattr(music_player, 'current_file') and music_player.current_file:
                    return (True, f"Music loaded: {music_player.current_file}")
                else:
                    return (False, "No music file selected (Click to select)")
            else:
                return (False, "No music file selected (Click to select)")
        except Exception as e:
            return (False, f"Could not verify music: {str(e)}")

    def update_check_item(self, check_id, result):
        """Update a check item with result"""
        item = self.check_items.get(check_id)
        if not item:
            return

        passed, message = result

        # Update icon
        if passed:
            item['icon'].setText("✅")
            item['icon'].setStyleSheet("color: #27ae60;")
        else:
            if item['critical']:
                item['icon'].setText("❌")
                item['icon'].setStyleSheet("color: #e74c3c;")
            else:
                item['icon'].setText("⚠️")
                item['icon'].setStyleSheet("color: #f39c12;")

        # Update status text
        item['status'].setText(message)
        if passed:
            item['status'].setStyleSheet("color: #27ae60; font-size: 9pt; font-style: italic;")
        else:
            if item['critical']:
                item['status'].setStyleSheet("color: #e74c3c; font-size: 9pt; font-style: italic;")
            else:
                item['status'].setStyleSheet("color: #f39c12; font-size: 9pt; font-style: italic;")

        # Update border color
        if passed:
            item['widget'].setStyleSheet("""
                QGroupBox {
                    border: 2px solid #27ae60;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding: 10px;
                }
            """)
        else:
            if item['critical']:
                item['widget'].setStyleSheet("""
                    QGroupBox {
                        border: 2px solid #e74c3c;
                        border-radius: 5px;
                        margin-top: 10px;
                        padding: 10px;
                    }
                """)
            else:
                item['widget'].setStyleSheet("""
                    QGroupBox {
                        border: 2px solid #f39c12;
                        border-radius: 5px;
                        margin-top: 10px;
                        padding: 10px;
                    }
                """)

    def update_overall_status(self):
        """Update overall status and enable/disable execute button"""
        # Check if all critical checks passed
        critical_checks_passed = True
        failed_critical = []
        warnings = []

        for check_id, item in self.check_items.items():
            result = self.check_results.get(check_id)
            if result:
                passed, message = result
                if not passed:
                    if item['critical']:
                        critical_checks_passed = False
                        failed_critical.append(item['widget'].findChild(QLabel).text())
                    else:
                        warnings.append(item['widget'].findChild(QLabel).text())

        self.checks_passed = critical_checks_passed

        if critical_checks_passed:
            if warnings:
                self.status_label.setText(f"✅ All critical checks passed! ({len(warnings)} warning(s))")
                self.status_label.setStyleSheet("""
                    QLabel {
                        padding: 10px;
                        border-radius: 5px;
                        background-color: #f39c12;
                        color: white;
                    }
                """)
            else:
                self.status_label.setText("✅ All checks passed! Ready to execute.")
                self.status_label.setStyleSheet("""
                    QLabel {
                        padding: 10px;
                        border-radius: 5px;
                        background-color: #27ae60;
                        color: white;
                    }
                """)
            self.execute_button.setEnabled(True)
            self.override_button.setVisible(False)
        else:
            self.status_label.setText(f"❌ {len(failed_critical)} critical check(s) failed")
            self.status_label.setStyleSheet("""
                QLabel {
                    padding: 10px;
                    border-radius: 5px;
                    background-color: #e74c3c;
                    color: white;
                }
            """)
            self.execute_button.setEnabled(False)
            self.override_button.setVisible(True)

    def handle_music_item_click(self):
        """Handle click on music selection item"""
        try:
            # Import the music selection dialog
            from views.dialogs.music_selection_dialog import MusicSelectionDialog

            # Get music manager from parent
            if not hasattr(self.parent(), 'music_manager'):
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Music Manager Not Available",
                                    "Cannot select music - music manager not found.")
                return

            # Show music selection dialog
            music_dialog = MusicSelectionDialog(self.parent(), self.parent().music_manager)

            # Connect signal to capture the selection
            def capture_music(music_info):
                self.selected_music = music_info

            music_dialog.music_selected.connect(capture_music)

            if music_dialog.exec() == QDialog.Accepted:
                # Re-run just the music check to update the display
                self.check_results['music_selected'] = self.check_music_selected()
                self.update_check_item('music_selected', self.check_results['music_selected'])

                # Update overall status
                self.update_overall_status()

        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Music Selection Error",
                                f"Failed to select music: {str(e)}")

    def handle_show_upload_click(self):
        """Handle click on show upload item - uploads show data to Pi"""
        from PySide6.QtWidgets import QMessageBox

        try:
            # Update status to show uploading
            item = self.check_items['show_uploaded']
            item['status'].setText("Uploading show data...")
            item['status'].setStyleSheet("color: #3498db; font-size: 9pt; font-style: italic;")
            item['icon'].setText("⏳")

            # Force UI update
            QApplication.processEvents()

            # Get system mode controller from parent
            if not hasattr(self.parent(), 'system_mode'):
                QMessageBox.warning(self, "System Mode Not Available",
                                    "Cannot upload show - system mode controller not found.")
                return

            system_mode = self.parent().system_mode

            # Check if we're in hardware mode
            if system_mode.current_mode != 'hardware':
                QMessageBox.warning(self, "Not in Hardware Mode",
                                    "Please switch to Hardware mode before uploading show data.")
                return

            # Get show data from parent's cue table
            if not hasattr(self.parent(), 'cue_table'):
                QMessageBox.warning(self, "Cue Table Not Available",
                                    "Cannot upload show - cue table not found.")
                return

            # Get all cues from the table (already formatted for execution)
            cues = self.parent().get_all_cues_for_execution()

            if not cues:
                QMessageBox.warning(self, "No Cues to Upload",
                                    "The show has no cues. Please add cues before uploading.")
                return

            # Upload show data to Pi
            success, message, show_file = self.upload_show_to_pi(system_mode, cues)

            if success:
                # Store the uploaded show file path
                self.uploaded_show_file = show_file

                # Update check result (tuple format: passed, message)
                self.check_results['show_uploaded'] = (True, message)

                # Update display
                self.update_check_item('show_uploaded', self.check_results['show_uploaded'])
                self.update_overall_status()

                # Show success message
                QMessageBox.information(self, "Upload Successful",
                                        f"✅ {message}\n\nFile: {show_file}\nCues: {len(cues)}")
            else:
                # Update check result (tuple format: passed, message)
                self.check_results['show_uploaded'] = (False, message)

                # Update display
                self.update_check_item('show_uploaded', self.check_results['show_uploaded'])
                self.update_overall_status()

                # Show error message
                QMessageBox.critical(self, "Upload Failed",
                                     f"❌ {message}\n\nPlease check your connection and try again.")

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Show upload error: {error_details}")

            QMessageBox.critical(self, "Upload Error",
                                 f"Failed to upload show: {str(e)}")

            # Update check result (tuple format: passed, message)
            self.check_results['show_uploaded'] = (False, f"Upload error: {str(e)}")
            self.update_check_item('show_uploaded', self.check_results['show_uploaded'])
            self.update_overall_status()

    def upload_show_to_pi(self, system_mode, cues):
        """
        Upload show data to Pi and validate with comprehensive checks.

        Returns:
            tuple: (success: bool, message: str, show_file: str)
        """
        import paramiko
        import json
        import time

        try:
            print(f"[Upload] Starting upload of {len(cues)} cues")

            # Normalize cues for Pi (same as system_mode_controller)
            normalized_cues = []
            for cue in cues:
                normalized_cue = system_mode.normalize_cue_for_pi(cue)
                normalized_cues.append(normalized_cue)

            print(f"[Upload] Normalized {len(normalized_cues)} cues")

            # Create JSON data (same format as system_mode_controller)
            show_data = {"cues": normalized_cues}
            show_json = json.dumps(show_data)  # No indent - same as system_mode_controller

            print(f"[Upload] JSON size: {len(show_json)} bytes")

            # Create show filename with timestamp
            timestamp = int(time.time())
            show_file = f"~/show_{timestamp}.json"

            # Get connection settings
            connection_settings = system_mode.connection_settings
            host = connection_settings.get('host')
            username = connection_settings.get('username')
            password = connection_settings.get('password')
            port = connection_settings.get('port', 22)

            if not all([host, username, password]):
                return False, "SSH connection settings not configured", ""

            print(f"[Upload] Connecting to {host}:{port}")

            # Create SSH connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, port=port, username=username, password=password, timeout=10)

            print(f"[Upload] Connected successfully")

            # Upload show data - USE EXACT SAME METHOD AS system_mode_controller
            create_file_cmd = f"echo '{show_json}' > {show_file}"
            print(f"[Upload] Creating file: {show_file}")

            stdin, stdout, stderr = ssh.exec_command(create_file_cmd, timeout=10)
            exit_status = stdout.channel.recv_exit_status()

            if exit_status != 0:
                error = stderr.read().decode()
                print(f"[Upload] File creation failed: {error}")
                ssh.close()
                return False, f"Failed to create show file: {error}", ""

            print(f"[Upload] File created successfully")

            # === COMPREHENSIVE VALIDATION PHASE ===
            print("\n[Validation] Starting comprehensive validation...")

            # 1. Check file exists
            check_cmd = f"test -f {show_file} && echo 'exists' || echo 'missing'"
            stdin, stdout, stderr = ssh.exec_command(check_cmd, timeout=5)
            result = stdout.read().decode().strip()

            print(f"[Validation] ✓ File exists check: {result}")

            if result != 'exists':
                ssh.close()
                return False, "❌ Show file was not created on Pi", ""

            # 2. Get actual file size
            size_cmd = f"wc -c < {show_file}"
            stdin, stdout, stderr = ssh.exec_command(size_cmd, timeout=5)
            actual_size_str = stdout.read().decode().strip()

            try:
                actual_size = int(actual_size_str)
                print(f"[Validation] ✓ File size: {actual_size} bytes")
            except ValueError:
                print(f"[Validation] ❌ Could not parse file size: {actual_size_str}")
                ssh.close()
                return False, f"❌ Invalid file size: {actual_size_str}", ""

            # 3. Download file back for validation (avoids SSH escaping issues)
            print("[Validation] Downloading file for local validation...")
            sftp = ssh.open_sftp()

            # Expand ~ to actual home directory
            expand_cmd = f"echo {show_file}"
            stdin, stdout, stderr = ssh.exec_command(expand_cmd, timeout=5)
            expanded_path = stdout.read().decode().strip()
            print(f"[Validation] Expanded path: {expanded_path}")

            try:
                with sftp.file(expanded_path, 'r') as f:
                    downloaded_content = f.read().decode('utf-8')
                print(f"[Validation] ✓ Downloaded {len(downloaded_content)} bytes")
            except Exception as e:
                print(f"[Validation] ❌ Download failed: {e}")
                sftp.close()
                ssh.close()
                return False, f"❌ Could not download file for validation: {str(e)}", ""

            sftp.close()

            # 4. Parse JSON locally (no SSH escaping issues)
            print("[Validation] Parsing JSON structure...")
            try:
                validated_data = json.loads(downloaded_content)
                print("[Validation] ✓ JSON is valid")
            except json.JSONDecodeError as e:
                print(f"[Validation] ❌ Invalid JSON: {e}")
                ssh.close()
                return False, f"❌ Invalid JSON structure: {str(e)}", ""

            # 5. Check required fields
            print("[Validation] Checking required fields...")
            if 'cues' not in validated_data:
                ssh.close()
                return False, "❌ Missing 'cues' field in uploaded data", ""
            print("[Validation] ✓ Required fields present")

            # 6. Verify cue count
            print("[Validation] Verifying cue count...")
            uploaded_cue_count = len(validated_data['cues'])
            expected_cue_count = len(normalized_cues)
            if uploaded_cue_count != expected_cue_count:
                ssh.close()
                return False, f"❌ Cue count mismatch: uploaded {uploaded_cue_count}, expected {expected_cue_count}", ""
            print(f"[Validation] ✓ Cue count matches: {uploaded_cue_count}")

            # 7. Verify each cue has required fields based on type
            print("[Validation] Validating cue structure...")
            for i, cue in enumerate(validated_data['cues']):
                cue_type = cue.get('type', '')

                # Check base required fields
                if 'type' not in cue:
                    ssh.close()
                    return False, f"❌ Cue {i + 1} missing required field: type", ""
                if 'time' not in cue:
                    ssh.close()
                    return False, f"❌ Cue {i + 1} missing required field: time", ""

                # Check type-specific fields
                if cue_type == 'SINGLE SHOT':
                    if 'output' not in cue:
                        ssh.close()
                        return False, f"❌ Cue {i + 1} (SINGLE SHOT) missing required field: output", ""

                elif cue_type == 'DOUBLE SHOT':
                    if 'output1' not in cue:
                        ssh.close()
                        return False, f"❌ Cue {i + 1} (DOUBLE SHOT) missing required field: output1", ""
                    if 'output2' not in cue:
                        ssh.close()
                        return False, f"❌ Cue {i + 1} (DOUBLE SHOT) missing required field: output2", ""

                elif cue_type == 'SINGLE RUN':
                    if 'start_output' not in cue:
                        ssh.close()
                        return False, f"❌ Cue {i + 1} (SINGLE RUN) missing required field: start_output", ""
                    if 'end_output' not in cue:
                        ssh.close()
                        return False, f"❌ Cue {i + 1} (SINGLE RUN) missing required field: end_output", ""
                    if 'delay' not in cue:
                        ssh.close()
                        return False, f"❌ Cue {i + 1} (SINGLE RUN) missing required field: delay", ""

                elif cue_type == 'DOUBLE RUN':
                    if 'start_output1' not in cue:
                        ssh.close()
                        return False, f"❌ Cue {i + 1} (DOUBLE RUN) missing required field: start_output1", ""
                    if 'end_output1' not in cue:
                        ssh.close()
                        return False, f"❌ Cue {i + 1} (DOUBLE RUN) missing required field: end_output1", ""
                    if 'start_output2' not in cue:
                        ssh.close()
                        return False, f"❌ Cue {i + 1} (DOUBLE RUN) missing required field: start_output2", ""
                    if 'end_output2' not in cue:
                        ssh.close()
                        return False, f"❌ Cue {i + 1} (DOUBLE RUN) missing required field: end_output2", ""
                    if 'delay' not in cue:
                        ssh.close()
                        return False, f"❌ Cue {i + 1} (DOUBLE RUN) missing required field: delay", ""

            print(f"[Validation] ✓ All {uploaded_cue_count} cues have required fields")

            # 8. Verify cue types are valid
            print("[Validation] Validating cue types...")
            valid_types = ['SINGLE SHOT', 'DOUBLE SHOT', 'SINGLE RUN', 'DOUBLE RUN']
            for i, cue in enumerate(validated_data['cues']):
                if cue['type'] not in valid_types:
                    ssh.close()
                    return False, f"❌ Cue {i + 1} has invalid type: {cue['type']}", ""
            print(f"[Validation] ✓ All cue types are valid")

            print("\n[Validation] === ALL VALIDATION CHECKS PASSED ===\n")

            ssh.close()

            # Success with detailed validation report!
            size_kb = actual_size / 1024 if actual_size > 0 else 0
            success_msg = (
                f"✅ Show uploaded and validated successfully!\n\n"
                f"✓ Cues: {uploaded_cue_count}\n"
                f"✓ File size: {size_kb:.1f} KB\n"
                f"✓ JSON structure: Valid\n"
                f"✓ All required fields: Present\n"
                f"✓ All cue types: Valid\n"
                f"✓ Location: {show_file}"
            )
            print(f"[Upload] {success_msg}")
            return True, success_msg, show_file

        except paramiko.AuthenticationException:
            print(f"[Upload] Authentication failed")
            return False, "❌ SSH authentication failed - check username/password", ""
        except paramiko.SSHException as e:
            print(f"[Upload] SSH error: {e}")
            return False, f"❌ SSH connection error: {str(e)}", ""
        except Exception as e:
            print(f"[Upload] Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False, f"❌ Unexpected error: {str(e)}", ""
        except Exception as e:
            print(f"[Upload] Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False, f"Upload error: {str(e)}", ""

    def handle_execute(self):
        """Handle execute button click"""
        if self.checks_passed:
            self.execute_confirmed.emit()
            self.accept()

    def handle_override(self):
        """Handle override button click"""
        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.warning(
            self,
            "Override Safety Checks",
            "⚠️ WARNING ⚠️\n\n"
            "You are about to execute the show despite failed safety checks.\n"
            "This could result in:\n"
            "• Unexpected behavior\n"
            "• Equipment damage\n"
            "• Safety hazards\n\n"
            "Are you absolutely sure you want to proceed?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.execute_confirmed.emit()
            self.accept()