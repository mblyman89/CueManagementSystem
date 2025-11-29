"""
Camera System for 3D Perspective Rendering
Handles view transformation and projection
"""

import math
import arcade
from typing import Tuple
import config


class Camera3D:
    """
    3D Camera system for perspective rendering
    Converts 3D world coordinates to 2D screen coordinates
    """
    
    def __init__(self):
        """Initialize camera with default settings from config"""
        self.position = list(config.CAMERA_POSITION)  # [x, y, z] in cm
        self.rotation = list(config.CAMERA_ROTATION)  # [pitch, yaw, roll] in degrees
        self.fov = config.CAMERA_FOV
        
        # Screen dimensions
        self.screen_width = config.SCREEN_WIDTH
        self.screen_height = config.SCREEN_HEIGHT
        
        # Calculate projection parameters
        self.aspect_ratio = self.screen_width / self.screen_height
        self.near_plane = 10  # cm
        self.far_plane = 1000000  # cm (10 km)
        
        # Perspective projection matrix components
        self._update_projection()
    
    def _update_projection(self):
        """Update projection matrix based on FOV and aspect ratio"""
        fov_rad = math.radians(self.fov)
        self.focal_length = 1.0 / math.tan(fov_rad / 2.0)
        self.scale_x = self.focal_length / self.aspect_ratio
        self.scale_y = self.focal_length
    
    def world_to_screen(self, world_x: float, world_y: float, world_z: float) -> Tuple[float, float, float]:
        """
        Convert 3D world coordinates to 2D screen coordinates
        
        Args:
            world_x: X coordinate in world space (cm)
            world_y: Y coordinate in world space (cm)
            world_z: Z coordinate in world space (cm)
        
        Returns:
            Tuple of (screen_x, screen_y, depth)
            Returns None if point is behind camera or out of view
        """
        # Translate to camera space
        rel_x = world_x - self.position[0]
        rel_y = world_y - self.position[1]
        rel_z = world_z - self.position[2]
        
        # Apply camera rotation (pitch only for now, simplified)
        pitch_rad = math.radians(self.rotation[0])
        
        # Rotate around X axis (pitch)
        rotated_y = rel_y * math.cos(pitch_rad) - rel_z * math.sin(pitch_rad)
        rotated_z = rel_y * math.sin(pitch_rad) + rel_z * math.cos(pitch_rad)
        
        # Check if point is behind camera
        if rotated_y <= self.near_plane:
            return None
        
        # Perspective projection
        depth = rotated_y
        projected_x = rel_x / depth * self.scale_x
        projected_z = rotated_z / depth * self.scale_y
        
        # Convert to screen coordinates
        screen_x = (projected_x + 1.0) * self.screen_width / 2.0
        screen_y = (projected_z + 1.0) * self.screen_height / 2.0
        
        # Check if point is within screen bounds (with margin)
        margin = 500  # pixels
        if (screen_x < -margin or screen_x > self.screen_width + margin or
            screen_y < -margin or screen_y > self.screen_height + margin):
            return None
        
        return (screen_x, screen_y, depth)
    
    def get_scale_at_distance(self, distance: float) -> float:
        """
        Get the scale factor for objects at a given distance
        Used for size-based perspective
        
        Args:
            distance: Distance from camera in cm
        
        Returns:
            Scale factor (1.0 at reference distance)
        """
        if distance <= 0:
            return 1.0
        
        reference_distance = 1000  # cm (10 meters)
        return reference_distance / distance
    
    def set_position(self, x: float, y: float, z: float):
        """Set camera position"""
        self.position = [x, y, z]
    
    def set_rotation(self, pitch: float, yaw: float, roll: float):
        """Set camera rotation in degrees"""
        self.rotation = [pitch, yaw, roll]
    
    def move(self, dx: float, dy: float, dz: float):
        """Move camera by delta amounts"""
        self.position[0] += dx
        self.position[1] += dy
        self.position[2] += dz
    
    def rotate(self, dpitch: float, dyaw: float, droll: float):
        """Rotate camera by delta amounts"""
        self.rotation[0] += dpitch
        self.rotation[1] += dyaw
        self.rotation[2] += droll