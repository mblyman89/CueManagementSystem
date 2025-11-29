"""
Water System - Realistic water surface with animation and reflections
Handles water rendering, wave animation, and reflection effects
"""

import math
import random
import arcade
from typing import List, Tuple
import config


class WaterWave:
    """Represents a single wave component in the water simulation"""
    
    def __init__(self, amplitude: float, wavelength: float, speed: float, direction: float):
        """
        Initialize a water wave
        
        Args:
            amplitude: Height of the wave in pixels
            wavelength: Distance between wave peaks in pixels
            speed: Wave propagation speed
            direction: Wave direction in radians (0 = right, π/2 = up)
        """
        self.amplitude = amplitude
        self.wavelength = wavelength
        self.speed = speed
        self.direction = direction
        self.phase = random.uniform(0, 2 * math.pi)  # Random starting phase
    
    def get_height(self, x: float, y: float, time: float) -> float:
        """
        Calculate wave height at a given position and time
        
        Args:
            x: X position
            y: Y position
            time: Current time in seconds
        
        Returns:
            Wave height offset
        """
        # Calculate wave position along direction
        wave_pos = x * math.cos(self.direction) + y * math.sin(self.direction)
        
        # Wave equation: A * sin(2π/λ * pos - speed * t + phase)
        k = 2 * math.pi / self.wavelength
        omega = self.speed
        
        return self.amplitude * math.sin(k * wave_pos - omega * time + self.phase)


class WaterSystem:
    """
    Manages water surface rendering with realistic animation and reflections
    """
    
    def __init__(self, camera):
        """
        Initialize water system
        
        Args:
            camera: Camera3D instance for coordinate transformation
        """
        self.camera = camera
        
        # Water surface properties
        self.base_height = 0  # Z height in world space (cm)
        self.color = config.WATER_COLOR
        self.reflection_alpha = 80  # Transparency for reflection layer
        
        # Wave system - multiple waves for realistic motion
        self.waves = [
            WaterWave(amplitude=2.0, wavelength=800, speed=0.5, direction=0),
            WaterWave(amplitude=1.5, wavelength=600, speed=0.7, direction=math.pi/4),
            WaterWave(amplitude=1.0, wavelength=400, speed=0.9, direction=math.pi/2),
            WaterWave(amplitude=0.8, wavelength=300, speed=1.1, direction=3*math.pi/4),
        ]
        
        # Animation state
        self.time = 0
        
        # Water mesh for rendering (grid of vertices)
        self.grid_resolution = 40  # Number of vertices per dimension
        self.water_vertices = []
        self._generate_water_mesh()
    
    def _generate_water_mesh(self):
        """Generate the base water mesh grid"""
        # Create a grid of vertices covering the visible water area
        # This will be animated each frame
        
        # Water extends from camera position forward
        water_start_y = self.camera.position[1]  # Start at camera Y
        water_end_y = water_start_y + 200000  # Extend 2km forward
        
        water_start_x = -100000  # 1km to the left
        water_end_x = 100000     # 1km to the right
        
        self.water_bounds = {
            'x_min': water_start_x,
            'x_max': water_end_x,
            'y_min': water_start_y,
            'y_max': water_end_y,
        }
    
    def update(self, delta_time: float):
        """
        Update water animation
        
        Args:
            delta_time: Time since last update in seconds
        """
        self.time += delta_time
    
    def get_wave_height_at(self, x: float, y: float) -> float:
        """
        Get the total wave height at a world position
        
        Args:
            x: World X coordinate
            y: World Y coordinate
        
        Returns:
            Total wave height offset from base height
        """
        total_height = 0
        for wave in self.waves:
            total_height += wave.get_height(x, y, self.time)
        
        return total_height
    
    def render(self, renderer):
        """
        Render the water surface
        
        Args:
            renderer: SceneRenderer instance
        """
        # Render water as a series of horizontal strips with wave animation
        # This creates a realistic animated water surface
        
        num_strips = 30  # Number of horizontal strips
        
        for i in range(num_strips):
            # Calculate Y position in world space
            t = i / num_strips
            world_y = self.water_bounds['y_min'] + t * (self.water_bounds['y_max'] - self.water_bounds['y_min'])
            
            # Calculate wave height at this Y position (sample at center X)
            wave_height = self.get_wave_height_at(0, world_y)
            world_z = self.base_height + wave_height
            
            # Project to screen space
            left_3d = self.camera.world_to_screen(
                self.water_bounds['x_min'], world_y, world_z
            )
            right_3d = self.camera.world_to_screen(
                self.water_bounds['x_max'], world_y, world_z
            )
            
            if left_3d is None or right_3d is None:
                continue
            
            left_x, left_y, left_depth = left_3d
            right_x, right_y, right_depth = right_3d
            
            # Calculate next strip for proper rectangle
            if i < num_strips - 1:
                t_next = (i + 1) / num_strips
                world_y_next = self.water_bounds['y_min'] + t_next * (self.water_bounds['y_max'] - self.water_bounds['y_min'])
                wave_height_next = self.get_wave_height_at(0, world_y_next)
                world_z_next = self.base_height + wave_height_next
                
                left_3d_next = self.camera.world_to_screen(
                    self.water_bounds['x_min'], world_y_next, world_z_next
                )
                right_3d_next = self.camera.world_to_screen(
                    self.water_bounds['x_max'], world_y_next, world_z_next
                )
                
                if left_3d_next is None or right_3d_next is None:
                    continue
                
                left_x_next, left_y_next, _ = left_3d_next
                right_x_next, right_y_next, _ = right_3d_next
            else:
                # Last strip extends to bottom of screen
                left_x_next = left_x
                left_y_next = 0
                right_x_next = right_x
                right_y_next = 0
            
            # Vary color slightly based on wave height for depth effect
            color_variation = int(wave_height * 2)
            r = max(0, min(255, self.color[0] + color_variation))
            g = max(0, min(255, self.color[1] + color_variation))
            b = max(0, min(255, self.color[2] + color_variation))
            
            # Draw the water strip
            def draw_strip(lx=left_x, ly=left_y, rx=right_x, ry=right_y,
                          lxn=left_x_next, lyn=left_y_next, rxn=right_x_next, ryn=right_y_next,
                          col=(r, g, b), depth=left_depth):
                # Draw as a quad (two triangles)
                arcade.draw_polygon_filled(
                    [
                        (lx, ly),      # Top-left
                        (rx, ry),      # Top-right
                        (rxn, ryn),    # Bottom-right
                        (lxn, lyn),    # Bottom-left
                    ],
                    col
                )
            
            renderer.add_to_layer('water', draw_strip, depth=left_depth)
    
    def add_ripple(self, world_x: float, world_y: float, intensity: float = 1.0):
        """
        Add a ripple effect at a world position (for future use - splash effects)
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            intensity: Ripple intensity
        """
        # TODO: Implement ripple system for splash effects when fireworks land
        pass