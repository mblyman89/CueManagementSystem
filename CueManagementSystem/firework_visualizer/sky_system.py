"""
Sky System - Enhanced sky rendering with atmospheric effects
Handles sky gradient, stars, and atmospheric lighting
"""

import math
import random
import arcade
from typing import List, Tuple
import config


class Star:
    """Represents a single star in the night sky"""
    
    def __init__(self, x: float, y: float, brightness: float, twinkle_speed: float):
        """
        Initialize a star
        
        Args:
            x: Screen X position (0-1, normalized)
            y: Screen Y position (0-1, normalized)
            brightness: Base brightness (0-1)
            twinkle_speed: Speed of twinkling animation
        """
        self.x = x
        self.y = y
        self.base_brightness = brightness
        self.twinkle_speed = twinkle_speed
        self.twinkle_phase = random.uniform(0, 2 * math.pi)
    
    def get_brightness(self, time: float) -> float:
        """
        Get current brightness with twinkling effect
        
        Args:
            time: Current time in seconds
        
        Returns:
            Current brightness (0-1)
        """
        twinkle = math.sin(time * self.twinkle_speed + self.twinkle_phase) * 0.3
        return max(0, min(1, self.base_brightness + twinkle))


class SkySystem:
    """
    Manages sky rendering with gradient, stars, and atmospheric effects
    """
    
    def __init__(self):
        """Initialize sky system"""
        # Sky colors
        self.color_top = config.SKY_COLOR_TOP
        self.color_bottom = config.SKY_COLOR_BOTTOM
        
        # Horizon glow (subtle orange/purple at horizon)
        self.horizon_glow_color = (40, 30, 60)  # Purple-ish
        self.horizon_glow_height = 0.3  # 30% of screen height
        
        # Stars
        self.stars = []
        self._generate_stars()
        
        # Animation state
        self.time = 0
        
        # Atmospheric effects
        self.ambient_light = config.AMBIENT_LIGHT
    
    def _generate_stars(self):
        """Generate stars in the night sky"""
        num_stars = 150  # Number of visible stars
        
        # Use fixed seed for consistent star positions
        random.seed(123)
        
        for _ in range(num_stars):
            # Stars only in upper portion of sky
            x = random.uniform(0, 1)
            y = random.uniform(0.5, 1.0)  # Upper half of screen
            
            # Vary brightness
            brightness = random.uniform(0.3, 1.0)
            
            # Vary twinkle speed
            twinkle_speed = random.uniform(0.5, 2.0)
            
            self.stars.append(Star(x, y, brightness, twinkle_speed))
    
    def update(self, delta_time: float):
        """
        Update sky animation
        
        Args:
            delta_time: Time since last update in seconds
        """
        self.time += delta_time
    
    def render(self, renderer):
        """
        Render the sky with all effects
        
        Args:
            renderer: SceneRenderer instance
        """
        # Render main sky gradient
        self._render_gradient(renderer)
        
        # Render horizon glow
        self._render_horizon_glow(renderer)
        
        # Render stars
        self._render_stars(renderer)
    
    def _render_gradient(self, renderer):
        """Render the main sky gradient"""
        def draw():
            # Draw gradient using multiple horizontal strips
            strips = 60
            strip_height = config.SCREEN_HEIGHT / strips
            
            for i in range(strips):
                # Interpolate color from bottom to top
                t = i / strips
                
                # Use smooth interpolation (ease-in-out)
                t_smooth = t * t * (3 - 2 * t)
                
                r = int(self.color_bottom[0] + (self.color_top[0] - self.color_bottom[0]) * t_smooth)
                g = int(self.color_bottom[1] + (self.color_top[1] - self.color_bottom[1]) * t_smooth)
                b = int(self.color_bottom[2] + (self.color_top[2] - self.color_bottom[2]) * t_smooth)
                
                y = i * strip_height
                arcade.draw_lrbt_rectangle_filled(
                    0, config.SCREEN_WIDTH,
                    y, y + strip_height,
                    (r, g, b)
                )
        
        renderer.add_to_layer('background', draw, depth=float('inf'))
    
    def _render_horizon_glow(self, renderer):
        """Render subtle glow at horizon"""
        def draw():
            # Draw a subtle glow at the horizon line
            glow_height = int(config.SCREEN_HEIGHT * self.horizon_glow_height)
            
            # Multiple layers for smooth gradient
            layers = 20
            for i in range(layers):
                t = i / layers
                alpha = int(30 * (1 - t))  # Fade out upward
                
                y = glow_height * t
                height = glow_height / layers
                
                r, g, b = self.horizon_glow_color
                arcade.draw_lrbt_rectangle_filled(
                    0, config.SCREEN_WIDTH,
                    y, y + height,
                    (r, g, b, alpha)
                )
        
        renderer.add_to_layer('background', draw, depth=float('inf') - 1)
    
    def _render_stars(self, renderer):
        """Render twinkling stars"""
        for star in self.stars:
            # Calculate screen position
            screen_x = star.x * config.SCREEN_WIDTH
            screen_y = star.y * config.SCREEN_HEIGHT
            
            # Get current brightness with twinkling
            brightness = star.get_brightness(self.time)
            
            # Star color (white with brightness variation)
            color_value = int(255 * brightness)
            color = (color_value, color_value, color_value)
            
            # Star size varies with brightness
            size = 1 + brightness * 1.5
            
            def draw_star(x=screen_x, y=screen_y, col=color, s=size):
                # Draw star as a small circle
                arcade.draw_circle_filled(x, y, s, col)
                
                # Add subtle cross-shaped glow for brighter stars
                if brightness > 0.7:
                    glow_alpha = int(100 * (brightness - 0.7) / 0.3)
                    glow_color = (col[0], col[1], col[2], glow_alpha)
                    
                    # Horizontal glow
                    arcade.draw_line(x - 3, y, x + 3, y, glow_color, 1)
                    # Vertical glow
                    arcade.draw_line(x, y - 3, x, y + 3, glow_color, 1)
            
            renderer.add_to_layer('background', draw_star, depth=float('inf') - 2)