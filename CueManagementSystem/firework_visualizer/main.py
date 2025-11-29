"""
Firework Visualizer - Main Entry Point
A realistic firework visualization system with lake scene and wooden mortar racks
"""

import arcade
import config
from firework_visualizer.game_view import FireworkGameView


def main():
    """
    Main function to initialize and run the firework visualizer
    """
    # Create the window
    window = arcade.Window(
        config.SCREEN_WIDTH,
        config.SCREEN_HEIGHT,
        config.SCREEN_TITLE,
        resizable=False,
        update_rate=1/config.TARGET_FPS
    )
    
    # Create and show the game view
    game_view = FireworkGameView()
    window.show_view(game_view)
    
    # Start the game loop
    arcade.run()


if __name__ == "__main__":
    main()