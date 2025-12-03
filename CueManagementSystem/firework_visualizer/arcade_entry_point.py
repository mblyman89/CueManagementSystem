"""
Arcade Visualizer Entry Point for Multiprocessing
==================================================

This module provides a standalone entry point for the arcade visualizer
that can be safely called from multiprocessing.Process in PyInstaller bundles.

CRITICAL: This solves the issue where multiprocessing.Process would re-execute
main.py and show the welcome page instead of the arcade window.

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

import sys
import time


def run_arcade_visualizer(command_queue, show_duration):
    """
    Entry point for running the arcade visualizer in a separate process.

    This function is designed to be called from multiprocessing.Process
    and works correctly in both development and PyInstaller-bundled environments.

    Args:
        command_queue: Multiprocessing queue for receiving commands
        show_duration: Duration of the show in seconds
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


# This allows the module to be run directly for testing
if __name__ == "__main__":
    import multiprocessing

    # Test with a dummy queue and duration
    test_queue = multiprocessing.Queue()
    test_duration = 30.0

    run_arcade_visualizer(test_queue, test_duration)