"""
SAFE Firework Visualizer Bridge Controller
==========================================

CRITICAL FIX: This version runs Arcade in a separate process to avoid
event loop conflicts with Qt that were causing system crashes on macOS.

Key Changes:
- Runs Arcade in separate process (not thread, not integrated)
- Uses multiprocessing for safe isolation
- No event loop conflicts
- No OpenGL context issues
- Safe for macOS

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QTimer
import multiprocessing
import time
import os


class FireworkVisualizerBridge(QObject):
    """
    SAFE Bridge controller for Professional Firework Visualizer

    Runs Arcade in a completely separate process to avoid crashes.
    """

    # Signals
    visualizer_started = Signal()
    visualizer_ready = Signal()
    visualizer_completed = Signal()
    visualizer_error = Signal(str)
    cue_executed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        # Visualizer state
        self.visualizer_process = None
        self.is_running = False

        # Show data
        self.cues: List[Dict[str, Any]] = []
        self.music_file: Optional[Dict[str, Any]] = None
        self.start_time: Optional[datetime] = None
        self.show_duration: float = 0.0

        # Cue execution tracking
        self.execution_timer = QTimer()
        self.execution_timer.timeout.connect(self._check_cue_execution)
        self.execution_timer.setInterval(50)
        self._executed_cues = set()
        self._last_check_index = 0

        # Process monitoring
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._monitor_process)
        self.monitor_timer.setInterval(100)

        # Communication queue
        self.command_queue = None

        self.logger.info("SAFE FireworkVisualizerBridge initialized (separate process mode)")

    def start_visualizer(self, cues: List[Dict[str, Any]],
                         music_file: Optional[Dict[str, Any]] = None):
        """
        Start the Professional Firework Visualizer in a SEPARATE PROCESS

        Args:
            cues: List of cue dictionaries to visualize
            music_file: Optional music file info dictionary
        """
        if self.is_running:
            self.logger.warning("Visualizer already running")
            return False

        try:
            self.cues = cues
            self.music_file = music_file
            self._executed_cues.clear()
            self._last_check_index = 0

            # Calculate show duration
            self.show_duration = self._calculate_show_duration()

            self.logger.info(f"Starting SAFE Firework Visualizer with {len(cues)} cues")
            self.logger.info(f"Show duration: {self.show_duration:.2f} seconds")

            # Create communication queue
            self.command_queue = multiprocessing.Queue()

            # Start visualizer in separate process
            # CRITICAL FIX: Use the dedicated entry point module instead of a static method
            # This ensures the child process doesn't re-execute main.py in PyInstaller bundles
            from firework_visualizer.arcade_entry_point import run_arcade_visualizer

            self.visualizer_process = multiprocessing.Process(
                target=run_arcade_visualizer,
                args=(self.command_queue, self.show_duration)
            )
            self.visualizer_process.start()

            self.is_running = True
            self.start_time = datetime.now()

            # Start timers
            self.execution_timer.start()
            self.monitor_timer.start()

            self.visualizer_started.emit()
            self.visualizer_ready.emit()

            self.logger.info("✓ Visualizer process started successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start visualizer: {e}")
            import traceback
            traceback.print_exc()
            self.visualizer_error.emit(str(e))
            return False

    @staticmethod
    def _run_arcade_process(command_queue, show_duration):
        """
        Run Arcade in a completely separate process

        This is the SAFE way to run Arcade alongside Qt on macOS.
        """
        try:
            import arcade
            from firework_visualizer.enhanced_simple_game_view import EnhancedSimpleFireworkGameView

            print("🎆 Starting Arcade in separate process...")

            # Create window
            window = EnhancedSimpleFireworkGameView()
            window.set_fullscreen(True)
            window.auto_launch = False
            window.setup()

            print("✓ Arcade window created")

            # Store command queue and show duration
            window.command_queue = command_queue
            window.show_duration = show_duration
            window.show_start_time = time.time()

            # Override on_update to check for commands
            original_on_update = window.on_update

            def on_update_with_commands(delta_time):
                # Check for commands from main process
                try:
                    while not command_queue.empty():
                        cmd = command_queue.get_nowait()
                        if cmd['type'] == 'launch':
                            window.launch_system.launch_shell(**cmd['params'])
                        elif cmd['type'] == 'stop':
                            window.close()
                            return
                except:
                    pass

                # Check if show duration reached
                elapsed = time.time() - window.show_start_time
                if elapsed > show_duration:
                    print(f"✓ Show duration reached: {elapsed:.1f}s")
                    window.close()
                    return

                # Call original update
                original_on_update(delta_time)

            window.on_update = on_update_with_commands

            print("✓ Starting Arcade event loop...")

            # Run Arcade's event loop (THIS IS SAFE IN SEPARATE PROCESS)
            arcade.run()

            print("✓ Arcade process completed")

        except Exception as e:
            print(f"❌ Error in Arcade process: {e}")
            import traceback
            traceback.print_exc()

    def _monitor_process(self):
        """Monitor the visualizer process"""
        if not self.visualizer_process:
            return

        # Check if process is still alive
        if not self.visualizer_process.is_alive():
            self.logger.info("Visualizer process has ended")
            self.stop_visualizer()

    def _check_cue_execution(self):
        """
        Check if any cues should be executed based on current time

        OPTIMIZED: Only checks unexecuted cues starting from last position.
        """
        if not self.is_running or not self.start_time or not self.command_queue:
            return

        # Calculate elapsed time since T=0
        elapsed = (datetime.now() - self.start_time).total_seconds()

        # OPTIMIZED: Only check cues from last position forward
        for i in range(self._last_check_index, len(self.cues)):
            cue_row = self.cues[i]

            # Skip already executed cues
            if i in self._executed_cues:
                self._last_check_index = i + 1
                continue

            # Convert list to dict format
            if len(cue_row) < 5:
                self._executed_cues.add(i)
                continue

            cue_dict = {
                'cue_id': cue_row[0],
                'type': cue_row[1],
                'outputs': cue_row[2],
                'delay': cue_row[3],
                'execute_time': cue_row[4],
                'visual_properties': cue_row[5] if len(cue_row) > 5 else None
            }

            cue_time = self._parse_time_code(cue_dict.get('execute_time', '00:00.0000'))

            # Check if it's time to execute this cue
            if elapsed >= cue_time:
                self._execute_cue(cue_dict)
                self._executed_cues.add(i)
                self._last_check_index = i + 1
                self.logger.debug(
                    f"Executed cue {cue_dict.get('cue_id', 'unknown')} at {elapsed:.3f}s (scheduled: {cue_time:.3f}s)")
            else:
                # Cue not ready yet, stop checking (cues are in order)
                break

    def _execute_cue(self, cue: Dict[str, Any]):
        """
        Execute a single cue by sending command to visualizer process

        Args:
            cue: Cue dictionary to execute
        """
        try:
            if not cue.get('visual_properties'):
                return

            visual_props = cue.get('visual_properties', {})
            firework_type, color_palette = self._map_shell_to_firework(visual_props)

            # Send command to visualizer process
            import random
            command = {
                'type': 'launch',
                'params': {
                    'tube_index': random.randint(0, 49),
                    'launch_angle': random.uniform(70, 85),
                    'azimuth_angle': random.uniform(-3, 3),
                    'shell_type': firework_type,
                    'color_name': color_palette
                }
            }

            self.command_queue.put(command)
            self.cue_executed.emit(cue.get('cue_id', 'unknown'))

        except Exception as e:
            self.logger.error(f"Error executing cue: {e}")

    def stop_visualizer(self):
        """Stop the visualizer process"""
        if not self.is_running:
            return

        try:
            # Send stop command
            if self.command_queue:
                self.command_queue.put({'type': 'stop'})

            # Stop timers
            self.execution_timer.stop()
            self.monitor_timer.stop()

            # Wait for process to end
            if self.visualizer_process:
                self.visualizer_process.join(timeout=2.0)
                if self.visualizer_process.is_alive():
                    self.visualizer_process.terminate()
                    self.visualizer_process.join(timeout=1.0)

            self.is_running = False
            self.visualizer_completed.emit()

            self.logger.info("✓ Visualizer stopped")

        except Exception as e:
            self.logger.error(f"Error stopping visualizer: {e}")

    def _calculate_show_duration(self) -> float:
        """Calculate total show duration from cues"""
        if not self.cues:
            return 0.0

        max_time = 0.0
        for cue_row in self.cues:
            if len(cue_row) >= 5:
                time_code = cue_row[4]
                cue_time = self._parse_time_code(time_code)
                max_time = max(max_time, cue_time)

        return max_time + 5.0  # Add 5 seconds buffer

    def _parse_time_code(self, time_code: str) -> float:
        """Parse MM:SS.SSSS time code to seconds"""
        try:
            if ':' in time_code:
                parts = time_code.split(':')
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            else:
                return float(time_code)
        except:
            return 0.0

    def _map_shell_to_firework(self, visual_props: Dict[str, Any]):
        """Map Excalibur shell to firework type and color"""
        shell_name = visual_props.get('shell_name', 'red_peony')

        # Extract color and type
        parts = shell_name.split('_')
        if len(parts) >= 2:
            color = parts[0]
            effect_type = '_'.join(parts[1:])
        else:
            color = 'red'
            effect_type = 'peony'

        # Map effect types
        effect_map = {
            'peony': 'peony',
            'chrysanthemum': 'chrysanthemum',
            'willow': 'willow',
            'palm': 'palm',
            'dahlia': 'dahlia',
            'brocade': 'brocade',
            'crackle': 'crackle',
            'multieffect': 'multieffect'
        }

        firework_type = effect_map.get(effect_type, 'peony')

        return firework_type, color