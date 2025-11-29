"""
Mortar Tube - Individual firework tube rendering and properties
Handles tube geometry, appearance, and angle calculations
"""

import math
import arcade
from typing import Tuple
import config


class MortarTube:
    """
    Represents a single mortar tube in a rack
    """
    
    def __init__(self, world_position: Tuple[float, float, float], 
                 angle_pitch: float, angle_yaw: float, tube_id: int):
        """
        Initialize a mortar tube
        
        Args:
            world_position: (x, y, z) position in world space (cm)
            angle_pitch: Vertical angle in degrees (0 = horizontal, 90 = straight up)
            angle_yaw: Horizontal angle in degrees (0 = forward, 90 = right)
            tube_id: Unique identifier for this tube
        """
        self.position = list(world_position)
        self.angle_pitch = angle_pitch
        self.angle_yaw = angle_yaw
        self.tube_id = tube_id
        
        # Tube physical properties
        self.diameter = config.TUBE_DIAMETER  # 7.62 cm (3 inches)
        self.length = config.TUBE_LENGTH      # 30 cm
        
        # Visual properties
        self.base_color = (60, 60, 65)  # Dark gray metal
        self.rim_color = (80, 80, 85)   # Lighter rim
        self.interior_color = (20, 20, 25)  # Dark interior
        
        # State
        self.has_shell = True  # Whether tube contains a shell
        self.is_fired = False  # Whether tube has been fired
    
    def get_muzzle_position(self) -> Tuple[float, float, float]:
        """
        Calculate the 3D position of the tube's muzzle (opening)
        
        Returns:
            (x, y, z) position of muzzle in world space
        """
        # Convert angles to radians
        pitch_rad = math.radians(self.angle_pitch)
        yaw_rad = math.radians(self.angle_yaw)
        
        # Calculate offset from base to muzzle
        dx = self.length * math.sin(yaw_rad) * math.cos(pitch_rad)
        dy = self.length * math.cos(yaw_rad) * math.cos(pitch_rad)
        dz = self.length * math.sin(pitch_rad)
        
        return (
            self.position[0] + dx,
            self.position[1] + dy,
            self.position[2] + dz
        )
    
    def get_firing_direction(self) -> Tuple[float, float, float]:
        """
        Calculate the normalized firing direction vector
        
        Returns:
            (dx, dy, dz) normalized direction vector
        """
        pitch_rad = math.radians(self.angle_pitch)
        yaw_rad = math.radians(self.angle_yaw)
        
        dx = math.sin(yaw_rad) * math.cos(pitch_rad)
        dy = math.cos(yaw_rad) * math.cos(pitch_rad)
        dz = math.sin(pitch_rad)
        
        return (dx, dy, dz)
    
    def render(self, camera, renderer, depth_offset: float = 0):
        """
        Render the mortar tube
        
        Args:
            camera: Camera3D instance
            renderer: SceneRenderer instance
            depth_offset: Additional depth for sorting
        """
        # Project base and muzzle positions to screen
        base_result = camera.world_to_screen(*self.position)
        muzzle_pos = self.get_muzzle_position()
        muzzle_result = camera.world_to_screen(*muzzle_pos)
        
        if base_result is None or muzzle_result is None:
            return
        
        base_x, base_y, base_depth = base_result
        muzzle_x, muzzle_y, muzzle_depth = muzzle_result
        
        # Calculate tube radius in screen space (perspective scaling)
        scale = camera.get_scale_at_distance(base_depth)
        screen_radius = self.diameter / 2 * scale * 0.5  # Adjust scale factor
        
        # Render tube as a line with circles at ends
        avg_depth = (base_depth + muzzle_depth) / 2 + depth_offset
        
        # Draw tube body
        def draw_tube_body(bx=base_x, by=base_y, mx=muzzle_x, my=muzzle_y, 
                          col=self.base_color, width=screen_radius*2):
            if width > 0.5:  # Only draw if visible
                arcade.draw_line(bx, by, mx, my, col, max(1, int(width)))
        
        renderer.add_to_layer('environment', draw_tube_body, depth=avg_depth)
        
        # Draw muzzle (opening)
        def draw_muzzle(mx=muzzle_x, my=muzzle_y, r=screen_radius, 
                       col=self.rim_color, interior=self.interior_color):
            if r > 1:  # Only draw if visible
                # Outer rim
                arcade.draw_circle_filled(mx, my, r, col)
                # Inner dark circle (interior)
                arcade.draw_circle_filled(mx, my, r * 0.7, interior)
        
        renderer.add_to_layer('environment', draw_muzzle, depth=avg_depth - 1)
        
        # Draw base cap (if visible from camera angle)
        if base_y < muzzle_y:  # Base is lower than muzzle
            def draw_base(bx=base_x, by=base_y, r=screen_radius, col=self.base_color):
                if r > 1:
                    arcade.draw_circle_filled(bx, by, r, col)
            
            renderer.add_to_layer('environment', draw_base, depth=avg_depth + 1)