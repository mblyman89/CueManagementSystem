"""
Simple Background System - Uses the reference image as the actual background.

This is a much simpler approach that just loads the reference image and displays it,
then renders fireworks on top. No complex sprite generation needed.
"""

import arcade
from pathlib import Path


class SimpleBackgroundSystem:
    """
    Simple system that uses a static image as the background.
    """

    def __init__(self, width: int, height: int, image_path: str = "starry-night-dock-stockcake.jpg"):
        self.width = width
        self.height = height

        # Convert to absolute path if relative
        if not Path(image_path).is_absolute():
            # Get the directory where this file is located
            current_dir = Path(__file__).parent
            self.image_path = str(current_dir / image_path)
        else:
            self.image_path = image_path

        self.background_sprite = None

    def load_background(self):
        """Load the background image and create a sprite."""

        # Check if image exists
        if not Path(self.image_path).exists():
            print(f"Warning: Background image not found: {self.image_path}")
            print("Creating a simple dark background instead...")
            self._create_simple_background()
            return

        try:
            # Load the image as a texture
            texture = arcade.load_texture(self.image_path)

            # Create a sprite from the texture
            self.background_sprite = arcade.Sprite()
            self.background_sprite.texture = texture

            # Position and scale to fill the window
            self.background_sprite.center_x = self.width / 2
            self.background_sprite.center_y = self.height / 2

            # Scale to fit window while maintaining aspect ratio
            scale_x = self.width / texture.width
            scale_y = self.height / texture.height
            scale = max(scale_x, scale_y)  # Use max to ensure it fills the window

            self.background_sprite.scale = scale

            print(f"Background image loaded: {self.image_path}")
            print(f"  Original size: {texture.width}x{texture.height}")
            print(f"  Scale: {scale:.2f}")

        except Exception as e:
            print(f"Error loading background image: {e}")
            self._create_simple_background()

    def _create_simple_background(self):
        """Create a simple dark blue background if image loading fails."""
        # Create a simple solid color texture
        texture = arcade.make_soft_square_texture(
            32,
            (5, 10, 20),  # Very dark blue
            outer_alpha=255
        )

        self.background_sprite = arcade.Sprite()
        self.background_sprite.texture = texture
        self.background_sprite.center_x = self.width / 2
        self.background_sprite.center_y = self.height / 2
        self.background_sprite.width = self.width
        self.background_sprite.height = self.height

    def draw(self):
        """Draw the background."""
        if self.background_sprite:
            # Use arcade's draw_sprite
            arcade.draw_sprite(self.background_sprite)