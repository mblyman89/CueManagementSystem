"""
Terminal Worker Thread

Handles SSH operations in a background thread to prevent GUI blocking.
"""

from PySide6.QtCore import QThread, Signal
from typing import Tuple


class SSHConnectionWorker(QThread):
    """Worker thread for SSH connection operations"""

    # Signals
    connection_result = Signal(bool, str)  # success, message
    command_result = Signal(bool, str, str)  # success, stdout, stderr

    def __init__(self, operation, *args, **kwargs):
        super().__init__()
        self.operation = operation
        self.args = args
        self.kwargs = kwargs

    def run(self):
        """Execute the operation in background thread"""
        try:
            if self.operation == 'connect':
                self._do_connect()
            elif self.operation == 'execute':
                self._do_execute()
        except Exception as e:
            if self.operation == 'connect':
                self.connection_result.emit(False, f"Error: {str(e)}")
            elif self.operation == 'execute':
                self.command_result.emit(False, "", str(e))

    def _do_connect(self):
        """Connect to SSH server"""
        connection = self.args[0]
        success, message = connection.connect()
        self.connection_result.emit(success, message)

    def _do_execute(self):
        """Execute command"""
        connection = self.args[0]
        command = self.args[1]
        timeout = self.kwargs.get('timeout', 30)

        success, stdout, stderr = connection.execute_command(command, timeout)
        self.command_result.emit(success, stdout, stderr)


class CommandExecutionWorker(QThread):
    """Worker thread for command execution"""

    # Signals
    output_ready = Signal(str)  # Output text
    error_occurred = Signal(str)  # Error message
    execution_complete = Signal(bool)  # Success status

    def __init__(self, session_manager, command):
        super().__init__()
        self.session_manager = session_manager
        self.command = command

    def run(self):
        """Execute command in background"""
        try:
            success, output = self.session_manager.execute_command(self.command)

            if success:
                if output:
                    self.output_ready.emit(output)
                self.execution_complete.emit(True)
            else:
                self.error_occurred.emit(output)
                self.execution_complete.emit(False)

        except Exception as e:
            self.error_occurred.emit(str(e))
            self.execution_complete.emit(False)