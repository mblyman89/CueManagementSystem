"""
Show Execution Manager for Large-Scale Firework Control

This module handles:
- Sequential execution of up to 1000 cues
- Pause/Resume functionality
- Progress tracking and status updates
- Integration with GPIO controller and MQTT system
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
from PySide6.QtCore import QObject, Signal, QTimer


class ShowState(Enum):
    """Show execution states"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABORTED = "aborted"
    ERROR = "error"


@dataclass
class CueExecutionResult:
    """Result of cue execution"""
    cue_id: str
    success: bool
    message: str
    execution_time: datetime
    duration_ms: int


@dataclass
class ShowProgress:
    """Show execution progress information"""
    total_cues: int
    completed_cues: int
    current_cue_index: int
    current_cue_id: str
    elapsed_time: timedelta
    estimated_remaining: timedelta
    state: ShowState


class ShowExecutionManager(QObject):
    """
    Manages sequential execution of firework shows

    Features:
    - Execute up to 1000 cues in sequence
    - Pause/Resume functionality
    - Progress tracking and reporting
    - Error handling and recovery
    - Integration with MQTT and GPIO systems
    """

    # Signals for show execution events
    show_started = Signal(int)  # total_cues
    show_completed = Signal()  #
    show_paused = Signal(int)  # current_cue_index
    show_resumed = Signal(int)  # current_cue_index
    show_aborted = Signal(str)  # reason
    cue_executed = Signal(str, bool, str)  # cue_id, success, message
    progress_updated = Signal(dict)  # progress_info
    error_occurred = Signal(str)  # error_message

    def __init__(self, system_mode=None, gpio_controller=None):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # System components
        self.system_mode = system_mode
        self.gpio_controller = gpio_controller

        # Show execution state
        self.show_state = ShowState.IDLE
        self.current_show_cues: List[Dict[str, Any]] = []
        self.current_cue_index = 0
        self.execution_results: List[CueExecutionResult] = []

        # Timing
        self.show_start_time: Optional[datetime] = None
        self.pause_start_time: Optional[datetime] = None
        self.total_pause_duration = timedelta()

        # Execution control
        self.execution_task: Optional[asyncio.Task] = None
        self.pause_event = asyncio.Event()
        self.abort_event = asyncio.Event()

        # Progress reporting timer
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self._emit_progress_update)
        self.progress_timer.setInterval(1000)  # Update every second

        self.logger.info("Show Execution Manager initialized")

    def load_show(self, cues: List[Dict[str, Any]]) -> bool:
        """
        Load a show with up to 1000 cues

        Args:
            cues: List of cue dictionaries

        Returns:
            bool: True if loaded successfully
        """
        try:
            if len(cues) > 1000:
                self.logger.warning(f"Show has {len(cues)} cues, limiting to 1000")
                cues = cues[:1000]

            if not cues:
                self.error_occurred.emit("Cannot load empty show")
                return False

            # Validate cues
            for i, cue in enumerate(cues):
                if not self._validate_cue(cue):
                    self.error_occurred.emit(f"Invalid cue at index {i}")
                    return False

            self.current_show_cues = cues.copy()
            self.current_cue_index = 0
            self.execution_results.clear()
            self.show_state = ShowState.IDLE

            self.logger.info(f"Loaded show with {len(cues)} cues")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load show: {e}")
            self.error_occurred.emit(f"Show load failed: {e}")
            return False

    def _validate_cue(self, cue: Dict[str, Any]) -> bool:
        """
        Validate a single cue

        Args:
            cue: Cue dictionary to validate

        Returns:
            bool: True if valid
        """
        required_fields = ['cue_id', 'cue_number']

        for field in required_fields:
            if field not in cue:
                self.logger.error(f"Cue missing required field: {field}")
                return False

        # Validate output values don't exceed 1000 outputs
        output_values = cue.get('output_values', [])
        if any(output > 1000 for output in output_values if isinstance(output, int)):
            self.logger.error(f"Cue {cue['cue_id']} has outputs exceeding 1000")
            return False

        return True

    async def execute_show(self) -> bool:
        """
        Execute the loaded show sequentially

        Returns:
            bool: True if execution started successfully
        """
        try:
            if not self.current_show_cues:
                self.error_occurred.emit("No show loaded")
                return False

            if self.show_state != ShowState.IDLE:
                self.error_occurred.emit(f"Cannot start show - current state: {self.show_state.value}")
                return False

            # Validate system is ready
            if self.gpio_controller:
                ready, message = self.gpio_controller.validate_system_ready_for_execution()
                if not ready:
                    self.error_occurred.emit(f"System not ready: {message}")
                    return False

            # Initialize execution state
            self.show_state = ShowState.RUNNING
            self.current_cue_index = 0
            self.execution_results.clear()
            self.show_start_time = datetime.now()
            self.total_pause_duration = timedelta()

            # Reset control events
            self.pause_event.set()  # Start unpaused
            self.abort_event.clear()

            # Start progress reporting
            self.progress_timer.start()

            # Emit show started signal
            self.show_started.emit(len(self.current_show_cues))

            # Start execution task
            self.execution_task = asyncio.create_task(self._execute_show_sequence())

            self.logger.info(f"Started show execution with {len(self.current_show_cues)} cues")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start show execution: {e}")
            self.error_occurred.emit(f"Show execution start failed: {e}")
            return False

    async def _execute_show_sequence(self):
        """Execute the show sequence (internal method)"""
        try:
            while self.current_cue_index < len(self.current_show_cues):
                # Check for abort
                if self.abort_event.is_set():
                    self.show_state = ShowState.ABORTED
                    self.show_aborted.emit("Show aborted by user")
                    break

                # Wait if paused
                await self.pause_event.wait()

                # Execute current cue
                cue = self.current_show_cues[self.current_cue_index]
                result = await self._execute_single_cue(cue)

                # Store result
                self.execution_results.append(result)

                # Emit cue executed signal
                self.cue_executed.emit(result.cue_id, result.success, result.message)

                # Handle execution failure
                if not result.success:
                    self.logger.error(f"Cue execution failed: {result.message}")
                    # Continue with next cue or abort based on configuration
                    # For now, we continue

                # Move to next cue
                self.current_cue_index += 1

                # Add delay between cues if specified
                cue_delay = cue.get('delay_after', 0)
                if cue_delay > 0:
                    await asyncio.sleep(cue_delay / 1000.0)  # Convert ms to seconds

            # Show completed
            if self.show_state == ShowState.RUNNING:
                self.show_state = ShowState.COMPLETED
                self.show_completed.emit()
                self.logger.info("Show execution completed successfully")

        except Exception as e:
            self.show_state = ShowState.ERROR
            self.logger.error(f"Show execution error: {e}")
            self.error_occurred.emit(f"Show execution error: {e}")

        finally:
            # Stop progress reporting
            self.progress_timer.stop()

            # Update GPIO controller state
            if self.gpio_controller:
                self.gpio_controller.system_state = self.gpio_controller.system_state

    async def _execute_single_cue(self, cue: Dict[str, Any]) -> CueExecutionResult:
        """
        Execute a single cue

        Args:
            cue: Cue dictionary to execute

        Returns:
            CueExecutionResult: Execution result
        """
        start_time = datetime.now()

        try:
            if self.system_mode and hasattr(self.system_mode, 'send_professional_cue'):
                # Use professional MQTT if available
                success, message = await self.system_mode.send_professional_cue(cue)
            elif self.system_mode:
                # Fall back to regular cue sending
                success, message = await self.system_mode.send_cue(cue)
            else:
                # Simulation mode
                success = True
                message = f"Simulated execution of cue {cue.get('cue_id', 'unknown')}"
                await asyncio.sleep(0.1)  # Simulate execution time

            duration = (datetime.now() - start_time).total_seconds() * 1000

            return CueExecutionResult(
                cue_id=cue.get('cue_id', 'unknown'),
                success=success,
                message=message,
                execution_time=start_time,
                duration_ms=int(duration)
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000

            return CueExecutionResult(
                cue_id=cue.get('cue_id', 'unknown'),
                success=False,
                message=f"Execution error: {e}",
                execution_time=start_time,
                duration_ms=int(duration)
            )

    def pause_show(self) -> bool:
        """
        Pause the currently running show

        Returns:
            bool: True if paused successfully
        """
        try:
            if self.show_state != ShowState.RUNNING:
                self.error_occurred.emit(f"Cannot pause - show state: {self.show_state.value}")
                return False

            self.show_state = ShowState.PAUSED
            self.pause_start_time = datetime.now()
            self.pause_event.clear()  # Pause execution

            self.show_paused.emit(self.current_cue_index)
            self.logger.info(f"Show paused at cue index {self.current_cue_index}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to pause show: {e}")
            self.error_occurred.emit(f"Show pause failed: {e}")
            return False

    def resume_show(self) -> bool:
        """
        Resume the paused show

        Returns:
            bool: True if resumed successfully
        """
        try:
            if self.show_state != ShowState.PAUSED:
                self.error_occurred.emit(f"Cannot resume - show state: {self.show_state.value}")
                return False

            # Calculate pause duration
            if self.pause_start_time:
                pause_duration = datetime.now() - self.pause_start_time
                self.total_pause_duration += pause_duration
                self.pause_start_time = None

            self.show_state = ShowState.RUNNING
            self.pause_event.set()  # Resume execution

            self.show_resumed.emit(self.current_cue_index)
            self.logger.info(f"Show resumed at cue index {self.current_cue_index}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to resume show: {e}")
            self.error_occurred.emit(f"Show resume failed: {e}")
            return False

    def abort_show(self, reason: str = "User abort") -> bool:
        """
        Abort the currently running show

        Args:
            reason: Reason for abort

        Returns:
            bool: True if aborted successfully
        """
        try:
            if self.show_state in [ShowState.IDLE, ShowState.COMPLETED, ShowState.ABORTED]:
                return True  # Already stopped

            self.abort_event.set()  # Signal abort to execution task
            self.pause_event.set()  # Ensure execution task can proceed to check abort

            # Emergency abort through GPIO controller
            if self.gpio_controller:
                self.gpio_controller.emergency_abort()

            self.show_state = ShowState.ABORTED
            self.show_aborted.emit(reason)

            self.logger.warning(f"Show aborted: {reason}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to abort show: {e}")
            self.error_occurred.emit(f"Show abort failed: {e}")
            return False

    async def execute_single_cue(self, cue: Dict[str, Any]) -> bool:
        """
        Execute a single cue (not part of a show)

        Args:
            cue: Cue dictionary to execute

        Returns:
            bool: True if executed successfully
        """
        try:
            # Validate system is ready
            if self.gpio_controller:
                ready, message = self.gpio_controller.validate_system_ready_for_execution()
                if not ready:
                    self.error_occurred.emit(f"System not ready: {message}")
                    return False

            # Validate cue
            if not self._validate_cue(cue):
                self.error_occurred.emit("Invalid cue data")
                return False

            # Execute the cue
            result = await self._execute_single_cue(cue)

            # Emit result
            self.cue_executed.emit(result.cue_id, result.success, result.message)

            if result.success:
                self.logger.info(f"Single cue executed successfully: {result.cue_id}")
            else:
                self.logger.error(f"Single cue execution failed: {result.message}")

            return result.success

        except Exception as e:
            self.logger.error(f"Failed to execute single cue: {e}")
            self.error_occurred.emit(f"Single cue execution failed: {e}")
            return False

    def get_show_progress(self) -> ShowProgress:
        """
        Get current show progress

        Returns:
            ShowProgress: Current progress information
        """
        elapsed_time = timedelta()
        estimated_remaining = timedelta()

        if self.show_start_time:
            now = datetime.now()
            elapsed_time = now - self.show_start_time - self.total_pause_duration

            # Add current pause time if paused
            if self.show_state == ShowState.PAUSED and self.pause_start_time:
                current_pause = now - self.pause_start_time
                elapsed_time -= current_pause

            # Estimate remaining time
            if self.current_cue_index > 0 and elapsed_time.total_seconds() > 0:
                avg_time_per_cue = elapsed_time.total_seconds() / self.current_cue_index
                remaining_cues = len(self.current_show_cues) - self.current_cue_index
                estimated_remaining = timedelta(seconds=avg_time_per_cue * remaining_cues)

        current_cue_id = ""
        if 0 <= self.current_cue_index < len(self.current_show_cues):
            current_cue_id = self.current_show_cues[self.current_cue_index].get('cue_id', '')

        return ShowProgress(
            total_cues=len(self.current_show_cues),
            completed_cues=self.current_cue_index,
            current_cue_index=self.current_cue_index,
            current_cue_id=current_cue_id,
            elapsed_time=elapsed_time,
            estimated_remaining=estimated_remaining,
            state=self.show_state
        )

    def _emit_progress_update(self):
        """Emit progress update signal (called by timer)"""
        progress = self.get_show_progress()
        progress_dict = {
            'total_cues': progress.total_cues,
            'completed_cues': progress.completed_cues,
            'current_cue_index': progress.current_cue_index,
            'current_cue_id': progress.current_cue_id,
            'elapsed_seconds': int(progress.elapsed_time.total_seconds()),
            'estimated_remaining_seconds': int(progress.estimated_remaining.total_seconds()),
            'state': progress.state.value,
            'progress_percentage': (
                        progress.completed_cues / progress.total_cues * 100) if progress.total_cues > 0 else 0
        }

        self.progress_updated.emit(progress_dict)

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get summary of show execution

        Returns:
            dict: Execution summary
        """
        successful_cues = sum(1 for result in self.execution_results if result.success)
        failed_cues = len(self.execution_results) - successful_cues

        total_duration = timedelta()
        if self.execution_results:
            total_duration = sum((result.duration_ms for result in self.execution_results), 0)

        return {
            'total_cues': len(self.current_show_cues),
            'executed_cues': len(self.execution_results),
            'successful_cues': successful_cues,
            'failed_cues': failed_cues,
            'success_rate': (successful_cues / len(self.execution_results) * 100) if self.execution_results else 0,
            'total_execution_time_ms': total_duration,
            'show_state': self.show_state.value,
            'execution_results': [
                {
                    'cue_id': result.cue_id,
                    'success': result.success,
                    'message': result.message,
                    'duration_ms': result.duration_ms
                }
                for result in self.execution_results
            ]
        }