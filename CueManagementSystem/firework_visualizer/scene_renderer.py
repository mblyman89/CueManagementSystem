"""
Scene Renderer - Handles rendering of all scene elements with proper layering
"""

import arcade
from typing import List, Tuple
import config


class RenderLayer:
    """Represents a rendering layer with depth sorting"""
    
    def __init__(self, name: str, z_order: int):
        self.name = name
        self.z_order = z_order  # Higher = rendered later (on top)
        self.draw_calls = []
    
    def add_draw_call(self, draw_func, depth: float = 0):
        """Add a drawing function to this layer with optional depth"""
        self.draw_calls.append((draw_func, depth))
    
    def clear(self):
        """Clear all draw calls"""
        self.draw_calls = []
    
    def render(self):
        """Execute all draw calls, sorted by depth"""
        # Sort by depth (far to near for proper alpha blending)
        sorted_calls = sorted(self.draw_calls, key=lambda x: -x[1])
        
        for draw_func, _ in sorted_calls:
            draw_func()


class SceneRenderer:
    """
    Manages rendering of all scene elements with proper layering and depth sorting
    """
    
    def __init__(self):
        """Initialize renderer with predefined layers"""
        self.layers = {
            'background': RenderLayer('background', 0),      # Sky, far background
            'water': RenderLayer('water', 1),                # Water surface
            'environment': RenderLayer('environment', 2),     # Dock, racks
            'particles': RenderLayer('particles', 3),         # Firework particles
            'effects': RenderLayer('effects', 4),             # Glow, bloom effects
            'ui': RenderLayer('ui', 5),                       # UI elements, text
        }
        
        # Background color
        self.background_color = config.SKY_COLOR_BOTTOM
    
    def clear_all_layers(self):
        """Clear all draw calls from all layers"""
        for layer in self.layers.values():
            layer.clear()
    
    def add_to_layer(self, layer_name: str, draw_func, depth: float = 0):
        """
        Add a draw call to a specific layer
        
        Args:
            layer_name: Name of the layer ('background', 'water', etc.)
            draw_func: Function to call for drawing
            depth: Depth value for sorting (higher = further away)
        """
        if layer_name in self.layers:
            self.layers[layer_name].add_draw_call(draw_func, depth)
    
    def render_all(self):
        """Render all layers in order"""
        # Clear screen with background color
        arcade.set_background_color(self.background_color)
        
        # Render each layer in z-order
        sorted_layers = sorted(self.layers.values(), key=lambda x: x.z_order)
        for layer in sorted_layers:
            layer.render()
    
    def draw_gradient_background(self, color_top: Tuple[int, int, int], 
                                 color_bottom: Tuple[int, int, int]):
        """
        Draw a vertical gradient background (sky)
        
        Args:
            color_top: RGB color at top of screen
            color_bottom: RGB color at bottom of screen
        """
        def draw():
            # Draw gradient using multiple horizontal strips
            strips = 50
            strip_height = config.SCREEN_HEIGHT / strips
            
            for i in range(strips):
                # Interpolate color
                t = i / strips
                r = int(color_bottom[0] + (color_top[0] - color_bottom[0]) * t)
                g = int(color_bottom[1] + (color_top[1] - color_bottom[1]) * t)
                b = int(color_bottom[2] + (color_top[2] - color_bottom[2]) * t)
                
                y = i * strip_height
                arcade.draw_lrtb_rectangle_filled(
                    0, config.SCREEN_WIDTH,
                    y + strip_height, y,
                    (r, g, b)
                )
        
        self.add_to_layer('background', draw, depth=float('inf'))
    
    def draw_water_surface(self, y_position: float, color: Tuple[int, int, int]):
        """
        Draw water surface as a horizontal plane
        
        Args:
            y_position: Y position on screen
            color: RGB color of water
        """
        def draw():
            arcade.draw_lrtb_rectangle_filled(
                0, config.SCREEN_WIDTH,
                y_position, 0,
                color
            )
        
        self.add_to_layer('water', draw, depth=1000)