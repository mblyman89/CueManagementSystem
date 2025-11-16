"""
Watchdog Timer Manager
======================

Monitors connection health and automatically disables outputs if connection is lost for a specified duration.

Features:
- Connection health monitoring
- Automatic output disabling on connection loss
- Configurable timeout duration
- Failure tracking and statistics
- Success rate calculation
- Signal emission for status updates
- Safety interlock integration

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

from PySide6.QtCore import QObject, QTimer, Signal, QThread
from datetime import datetime
import time
from typing import Optional, Dict, Any
import json


class WatchdogTimer(QObject):
    """
    Watchdog timer that monitors connection health and takes action on failures.

    Signals:
        status_changed: Emitted when watchdog status changes (active/inactive/triggered)
        connection_lost: Emitted when connection is lost
        connection_restored: Emitted when connection is restored
        timeout_triggered: Emitted when watchdog timeout is reached
        health_check_completed: Emitted after each health check with result
    """

    # Signals
    status_changed = Signal(str)  # "active", "inactive", "triggered", "disabled"
    connection_lost = Signal()
    connection_restored = Signal()
    timeout_triggered = Signal()
    health_check_completed = Signal(bool, float)  # (success, latency_ms)

    def __init__(self, system_mode_controller, parent=None):
        """
        Initialize watchdog timer.

        Args:
            system_mode_controller: Reference to SystemModeController for SSH operations
            parent: Parent QObject
        """
        super().__init__(parent)

        self.system_mode_controller = system_mode_controller

        # Configuration
        self.check_interval_ms = 3000  # Check every 3 seconds
        self.timeout_threshold_ms = 10000  # Trigger after 10 seconds of failed checks
        self.max_consecutive_failures = 3  # Number of failures before triggering

        # State
        self.is_active = False
        self.is_monitoring = False
        self.consecutive_failures = 0
        self.last_successful_check = None
        self.last_check_time = None
        self.connection_lost_time = None
        self.total_checks = 0
        self.successful_checks = 0
        self.failed_checks = 0

        # Timer
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self._perform_health_check)

        # Event log
        self.event_log = []

        self._log_event("Watchdog initialized", "info")

    def start_monitoring(self):
        """Start watchdog monitoring."""
        if self.is_monitoring:
            self._log_event("Watchdog already monitoring", "warning")
            return

        self.is_monitoring = True
        self.is_active = True
        self.consecutive_failures = 0
        self.last_successful_check = datetime.now()
        self.connection_lost_time = None

        self.check_timer.start(self.check_interval_ms)
        self.status_changed.emit("active")
        self._log_event("Watchdog monitoring started", "info")

    def stop_monitoring(self):
        """Stop watchdog monitoring."""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        self.is_active = False
        self.check_timer.stop()

        self.status_changed.emit("inactive")
        self._log_event("Watchdog monitoring stopped", "info")

    def pause_monitoring(self):
        """Temporarily pause monitoring (e.g., during intentional disconnection)."""
        if not self.is_monitoring:
            return

        self.check_timer.stop()
        self.status_changed.emit("paused")
        self._log_event("Watchdog monitoring paused", "info")

    def resume_monitoring(self):
        """Resume monitoring after pause."""
        if not self.is_monitoring:
            return

        self.check_timer.start(self.check_interval_ms)
        self.status_changed.emit("active")
        self._log_event("Watchdog monitoring resumed", "info")

    def _perform_health_check(self):
        """Perform a connection health check."""
        if not self.is_monitoring:
            return

        self.total_checks += 1
        self.last_check_time = datetime.now()

        # Perform health check
        start_time = time.perf_counter()
        success = self._check_connection_health()
        latency_ms = (time.perf_counter() - start_time) * 1000

        if success:
            self._handle_successful_check(latency_ms)
        else:
            self._handle_failed_check(latency_ms)

        # Emit health check result
        self.health_check_completed.emit(success, latency_ms)

    def _check_connection_health(self) -> bool:
        """
        Check if SSH connection is healthy.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            # Use system_mode_controller's check_connection_health method
            if hasattr(self.system_mode_controller, 'check_connection_health'):
                return self.system_mode_controller.check_connection_health()
            else:
                # Fallback: try a simple echo command
                return self._simple_connection_test()
        except Exception as e:
            self._log_event(f"Health check error: {str(e)}", "error")
            return False

    def _simple_connection_test(self) -> bool:
        """
        Simple connection test using echo command.

        Returns:
            True if connection works, False otherwise
        """
        try:
            import paramiko

            # Get connection settings
            host = self.system_mode_controller.host
            username = self.system_mode_controller.username
            password = self.system_mode_controller.password

            if not all([host, username, password]):
                return False

            # Create temporary connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=username, password=password, timeout=3)

            # Test with echo command
            stdin, stdout, stderr = ssh.exec_command("echo 'watchdog_ping'", timeout=3)
            result = stdout.read().decode().strip()

            ssh.close()

            return result == "watchdog_ping"

        except Exception as e:
            self._log_event(f"Simple connection test failed: {str(e)}", "error")
            return False

    def _handle_successful_check(self, latency_ms: float):
        """Handle a successful health check."""
        self.successful_checks += 1
        self.last_successful_check = datetime.now()

        # Reset failure counter
        if self.consecutive_failures > 0:
            self._log_event(
                f"Connection restored after {self.consecutive_failures} failures "
                f"(latency: {latency_ms:.1f}ms)",
                "info"
            )
            self.connection_restored.emit()

        self.consecutive_failures = 0
        self.connection_lost_time = None

    def _handle_failed_check(self, latency_ms: float):
        """Handle a failed health check."""
        self.failed_checks += 1
        self.consecutive_failures += 1

        # First failure - record time
        if self.consecutive_failures == 1:
            self.connection_lost_time = datetime.now()
            self._log_event("Connection check failed (first failure)", "warning")
            self.connection_lost.emit()

        # Check if we've exceeded threshold
        if self.consecutive_failures >= self.max_consecutive_failures:
            time_since_loss = (datetime.now() - self.connection_lost_time).total_seconds() * 1000

            if time_since_loss >= self.timeout_threshold_ms:
                self._trigger_watchdog()

    def _trigger_watchdog(self):
        """Trigger watchdog timeout - disable outputs and stop show."""
        if not self.is_active:
            return

        self.is_active = False
        self.status_changed.emit("triggered")

        time_since_loss = (datetime.now() - self.connection_lost_time).total_seconds()

        self._log_event(
            f"WATCHDOG TRIGGERED: Connection lost for {time_since_loss:.1f}s "
            f"({self.consecutive_failures} consecutive failures)",
            "critical"
        )

        # Emit timeout signal
        self.timeout_triggered.emit()

        # Attempt to disable outputs via emergency stop
        self._emergency_disable_outputs()

    def _emergency_disable_outputs(self):
        """Attempt to disable outputs via emergency stop."""
        try:
            self._log_event("Attempting emergency output disable", "warning")

            # Try to call emergency stop
            if hasattr(self.system_mode_controller, 'emergency_stop'):
                result = self.system_mode_controller.emergency_stop()
                if result:
                    self._log_event("Emergency stop successful", "info")
                else:
                    self._log_event("Emergency stop failed", "error")
            else:
                self._log_event("Emergency stop method not available", "error")

        except Exception as e:
            self._log_event(f"Emergency disable error: {str(e)}", "error")

    def _log_event(self, message: str, level: str = "info"):
        """
        Log a watchdog event.

        Args:
            message: Event message
            level: Event level (info, warning, error, critical)
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "consecutive_failures": self.consecutive_failures,
            "total_checks": self.total_checks,
            "success_rate": self._calculate_success_rate()
        }

        self.event_log.append(event)

        # Keep only last 100 events
        if len(self.event_log) > 100:
            self.event_log = self.event_log[-100:]

        # Print to console for debugging
        print(f"[WATCHDOG {level.upper()}] {message}")

    def _calculate_success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_checks == 0:
            return 100.0
        return (self.successful_checks / self.total_checks) * 100

    def get_status(self) -> Dict[str, Any]:
        """
        Get current watchdog status.

        Returns:
            Dictionary with status information
        """
        status = {
            "is_monitoring": self.is_monitoring,
            "is_active": self.is_active,
            "consecutive_failures": self.consecutive_failures,
            "total_checks": self.total_checks,
            "successful_checks": self.successful_checks,
            "failed_checks": self.failed_checks,
            "success_rate": self._calculate_success_rate(),
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "last_successful_check": self.last_successful_check.isoformat() if self.last_successful_check else None,
            "connection_lost_time": self.connection_lost_time.isoformat() if self.connection_lost_time else None,
            "check_interval_ms": self.check_interval_ms,
            "timeout_threshold_ms": self.timeout_threshold_ms,
            "max_consecutive_failures": self.max_consecutive_failures
        }

        return status

    def get_event_log(self) -> list:
        """Get event log."""
        return self.event_log.copy()

    def clear_event_log(self):
        """Clear event log."""
        self.event_log.clear()
        self._log_event("Event log cleared", "info")

    def set_check_interval(self, interval_ms: int):
        """Set health check interval in milliseconds."""
        if interval_ms < 1000:
            interval_ms = 1000  # Minimum 1 second

        self.check_interval_ms = interval_ms

        if self.is_monitoring:
            self.check_timer.setInterval(interval_ms)

        self._log_event(f"Check interval set to {interval_ms}ms", "info")

    def set_timeout_threshold(self, threshold_ms: int):
        """Set timeout threshold in milliseconds."""
        if threshold_ms < 5000:
            threshold_ms = 5000  # Minimum 5 seconds

        self.timeout_threshold_ms = threshold_ms
        self._log_event(f"Timeout threshold set to {threshold_ms}ms", "info")

    def set_max_consecutive_failures(self, max_failures: int):
        """Set maximum consecutive failures before triggering."""
        if max_failures < 1:
            max_failures = 1

        self.max_consecutive_failures = max_failures
        self._log_event(f"Max consecutive failures set to {max_failures}", "info")

    def reset(self):
        """Reset watchdog state."""
        self.stop_monitoring()
        self.consecutive_failures = 0
        self.last_successful_check = None
        self.last_check_time = None
        self.connection_lost_time = None
        self.total_checks = 0
        self.successful_checks = 0
        self.failed_checks = 0

    def cleanup(self):
        """Cleanup resources when shutting down."""
        try:
            self.stop_monitoring()
            if hasattr(self, 'check_timer') and self.check_timer:
                self.check_timer.stop()
                self.check_timer.deleteLater()
                self.check_timer = None
        except Exception as e:
            print(f"Error during watchdog cleanup: {e}")

    def __del__(self):
        """Destructor - ensure cleanup happens."""
        try:
            if hasattr(self, 'check_timer') and self.check_timer:
                self.check_timer.stop()
        except:
            pass
        self._log_event("Watchdog reset", "info")