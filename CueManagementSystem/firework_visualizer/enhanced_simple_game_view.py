"""
Enhanced Simple Game View - Realistic fireworks with static background
Integrates the new physics-based launch system with particle effects
"""

import arcade
import random
import config
from simple_background_system import SimpleBackgroundSystem
from enhanced_launch_system import EnhancedLaunchSystem


class EnhancedSimpleFireworkGameView(arcade.Window):
    """
    Enhanced game window with realistic firework physics and effects.
    """

    def __init__(self):
        """Initialize the game window."""
        super().__init__(
            config.WINDOW_WIDTH,
            config.WINDOW_HEIGHT,
            "Firework Visualizer - Enhanced with Realistic Physics",
            resizable=False,
            update_rate=1 / 60
        )

        # Set background color (fallback)
        self.background_color = (5, 10, 20)

        # Initialize background system
        print("\nInitializing Background System...")
        self.background = SimpleBackgroundSystem(
            config.WINDOW_WIDTH,
            config.WINDOW_HEIGHT,
            image_path="starry-night-dock-stockcake.jpg"
        )

        # Initialize enhanced launch system
        print("Initializing Enhanced Launch System...")
        self.launch_system = EnhancedLaunchSystem(
            config.WINDOW_WIDTH,
            config.WINDOW_HEIGHT
        )

        # Game state
        self.paused = False
        self.show_debug = config.DEBUG_MODE
        self.auto_launch = False  # Disabled by default
        self.auto_launch_timer = 0.0
        self.auto_launch_interval = 2.0

        print("Enhanced game view initialized!")

    def setup(self):
        """Set up the game."""
        print("\n" + "=" * 70)
        print("SETTING UP ENHANCED FIREWORK VISUALIZER")
        print("=" * 70 + "\n")

        # Load the background image
        print("Loading background image...")
        self.background.load_background()

        print("\n" + "=" * 70)
        print("SETUP COMPLETE!")
        print("=" * 70)
        print("\nControls:")
        print("  SPACE    - Launch random firework")
        print("  1-8      - Launch specific firework type")
        print("  P        - Pause/Resume")
        print("  D        - Toggle debug info")
        print("  A        - Toggle auto-launch")
        print("  +/-      - Adjust auto-launch interval")
        print("  ESC      - Exit")
        print("=" * 70 + "\n")

        print("Firework Types:")
        print("  1 - Peony (spherical burst)")
        print("  2 - Chrysanthemum (ring burst)")
        print("  3 - Willow (falling trails)")
        print("  4 - Palm (upward burst)")
        print("  5 - Dahlia (dense sphere)")
        print("  6 - Brocade (ring pattern)")
        print("  7 - Crackle (random burst)")
        print("  8 - Multi-effect (combination)")
        print("=" * 70 + "\n")

    def on_draw(self):
        """Render the scene."""
        self.clear()

        # Draw the background image
        self.background.draw()

        # Draw firework effects
        self.launch_system.draw()

        # Draw debug info if enabled
        if self.show_debug:
            self._draw_debug_info()

    def _draw_debug_info(self):
        """Draw debug information."""
        stats = self.launch_system.get_statistics()

        y_offset = self.height - 30
        line_height = 20

        # FPS
        fps_text = f"FPS: {arcade.get_fps():.0f}"
        arcade.draw_text(
            fps_text,
            10, y_offset,
            arcade.color.WHITE,
            14,
            bold=True
        )
        y_offset -= line_height

        # Active shells
        shells_text = f"Active Shells: {stats['active_shells']}"
        arcade.draw_text(
            shells_text,
            10, y_offset,
            arcade.color.WHITE,
            14
        )
        y_offset -= line_height

        # Particle count
        particles_text = f"Particles: {stats['active_particles']}"
        arcade.draw_text(
            particles_text,
            10, y_offset,
            arcade.color.WHITE,
            14
        )
        y_offset -= line_height

        # Emitters
        emitters_text = f"Emitters: {stats['active_emitters']}"
        arcade.draw_text(
            emitters_text,
            10, y_offset,
            arcade.color.WHITE,
            14
        )
        y_offset -= line_height

        # Total launches
        launches_text = f"Total Launches: {stats['total_launches']}"
        arcade.draw_text(
            launches_text,
            10, y_offset,
            arcade.color.WHITE,
            14
        )
        y_offset -= line_height

        # Total bursts
        bursts_text = f"Total Bursts: {stats['total_bursts']}"
        arcade.draw_text(
            bursts_text,
            10, y_offset,
            arcade.color.WHITE,
            14
        )
        y_offset -= line_height

        # Auto-launch status
        if self.auto_launch:
            auto_text = f"Auto-Launch: ON ({self.auto_launch_timer:.1f}s / {self.auto_launch_interval:.1f}s)"
            arcade.draw_text(
                auto_text,
                10, y_offset,
                arcade.color.GREEN,
                14
            )
        else:
            arcade.draw_text(
                "Auto-Launch: OFF",
                10, y_offset,
                arcade.color.RED,
                14
            )

        # Paused status
        if self.paused:
            arcade.draw_text(
                "PAUSED",
                self.width / 2 - 50,
                self.height / 2,
                arcade.color.YELLOW,
                24,
                bold=True
            )

    def on_update(self, delta_time: float):
        """Update game state."""
        if self.paused:
            return

        # Update launch system
        self.launch_system.update(delta_time)

        # Auto-launch logic
        if self.auto_launch:
            self.auto_launch_timer += delta_time
            if self.auto_launch_timer >= self.auto_launch_interval:
                self.auto_launch_timer = 0.0
                self._launch_random_firework()

    def _launch_random_firework(self):
        """Launch a random firework."""
        self.launch_system.launch_random_shell()

    def _launch_specific_firework(self, firework_type: str):
        """Launch a specific type of firework."""
        tube_index = random.randint(0, 49)
        launch_angle = random.uniform(70, 85)
        azimuth = random.uniform(-3, 3)  # Much smaller spread for distant view

        self.launch_system.launch_shell(
            tube_index=tube_index,
            launch_angle=launch_angle,
            azimuth_angle=azimuth,
            shell_type=firework_type,
            color_name="random"
        )

    def on_key_press(self, key, modifiers):
        """Handle key presses."""

        # Space - Launch random firework
        if key == arcade.key.SPACE:
            self._launch_random_firework()

        # Number keys - Launch specific firework types
        elif key == arcade.key.KEY_1:
            self._launch_specific_firework("peony")
        elif key == arcade.key.KEY_2:
            self._launch_specific_firework("chrysanthemum")
        elif key == arcade.key.KEY_3:
            self._launch_specific_firework("willow")
        elif key == arcade.key.KEY_4:
            self._launch_specific_firework("palm")
        elif key == arcade.key.KEY_5:
            self._launch_specific_firework("dahlia")
        elif key == arcade.key.KEY_6:
            self._launch_specific_firework("brocade")
        elif key == arcade.key.KEY_7:
            self._launch_specific_firework("crackle")
        elif key == arcade.key.KEY_8:
            self._launch_specific_firework("multieffect")

        # P - Pause/Resume
        elif key == arcade.key.P:
            self.paused = not self.paused
            print(f"Game {'paused' if self.paused else 'resumed'}")

        # D - Toggle debug
        elif key == arcade.key.D:
            self.show_debug = not self.show_debug
            print(f"Debug mode: {'ON' if self.show_debug else 'OFF'}")

        # A - Toggle auto-launch
        elif key == arcade.key.A:
            self.auto_launch = not self.auto_launch
            print(f"Auto-launch: {'ON' if self.auto_launch else 'OFF'}")

        # + - Increase auto-launch interval
        elif key == arcade.key.PLUS or key == arcade.key.EQUAL:
            self.auto_launch_interval = min(10.0, self.auto_launch_interval + 0.5)
            print(f"Auto-launch interval: {self.auto_launch_interval:.1f}s")

        # - - Decrease auto-launch interval
        elif key == arcade.key.MINUS:
            self.auto_launch_interval = max(0.5, self.auto_launch_interval - 0.5)
            print(f"Auto-launch interval: {self.auto_launch_interval:.1f}s")

        # C - Clear all fireworks
        elif key == arcade.key.C:
            self.launch_system.clear()
            print("Cleared all fireworks")

        # ESC - Exit
        elif key == arcade.key.ESCAPE:
            self.close()

    def on_mouse_press(self, x, y, button, modifiers):
        """Handle mouse clicks."""
        if button == arcade.MOUSE_BUTTON_LEFT:
            self._launch_random_firework()


def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("FIREWORK VISUALIZER - ENHANCED WITH REALISTIC PHYSICS")
    print("=" * 70 + "\n")

    game = EnhancedSimpleFireworkGameView()
    game.setup()
    arcade.run()


if __name__ == "__main__":
    main()