"""
Particle - Base particle class with physics simulation
Represents a single particle in the firework system
"""

import math
from typing import Tuple
import config


class Particle:
    """
    Base particle class with position, velocity, and physics
    """
    
    def __init__(self):
        """Initialize particle with default values"""
        # Position in world space (cm)
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        
        # Velocity (cm/s)
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        
        # Acceleration (cm/s²) - used for forces
        self.ax = 0.0
        self.ay = 0.0
        self.az = 0.0
        
        # Visual properties
        self.color = (255, 255, 255)  # RGB
        self.alpha = 255  # 0-255
        self.size = 3.0  # pixels
        
        # Lifetime
        self.lifetime = 0.0  # Total lifetime in seconds
        self.age = 0.0  # Current age in seconds
        self.is_alive = False
        
        # Physics properties
        self.mass = 1.0  # Relative mass (affects drag)
        self.drag_coefficient = config.AIR_DRAG
        
        # Trail properties (for some particle types)
        self.has_trail = False
        self.trail_length = 0
        self.trail_positions = []
    
    def spawn(self, x: float, y: float, z: float,
              vx: float, vy: float, vz: float,
              color: Tuple[int, int, int],
              lifetime: float,
              size: float = 3.0,
              alpha: int = 255):
        """
        Spawn/activate this particle with initial values
        
        Args:
            x, y, z: Initial position (cm)
            vx, vy, vz: Initial velocity (cm/s)
            color: RGB color tuple
            lifetime: Particle lifetime in seconds
            size: Visual size in pixels
            alpha: Initial alpha (0-255)
        """
        self.x = x
        self.y = y
        self.z = z
        
        self.vx = vx
        self.vy = vy
        self.vz = vz
        
        self.ax = 0.0
        self.ay = 0.0
        self.az = config.GRAVITY  # Apply gravity
        
        self.color = color
        self.alpha = alpha
        self.size = size
        
        self.lifetime = lifetime
        self.age = 0.0
        self.is_alive = True
        
        # Clear trail
        self.trail_positions = []
    
    def update(self, delta_time: float):
        """
        Update particle physics and lifetime
        
        Args:
            delta_time: Time step in seconds
        """
        if not self.is_alive:
            return
        
        # Update age
        self.age += delta_time
        
        # Check if particle should die
        if self.age >= self.lifetime:
            self.kill()
            return
        
        # Apply drag to velocity
        drag_factor = self.drag_coefficient ** delta_time
        self.vx *= drag_factor
        self.vy *= drag_factor
        self.vz *= drag_factor
        
        # Apply acceleration (gravity, forces)
        self.vx += self.ax * delta_time
        self.vy += self.ay * delta_time
        self.vz += self.az * delta_time
        
        # Store previous position for trail
        if self.has_trail:
            self.trail_positions.append((self.x, self.y, self.z))
            if len(self.trail_positions) > self.trail_length:
                self.trail_positions.pop(0)
        
        # Update position
        self.x += self.vx * delta_time
        self.y += self.vy * delta_time
        self.z += self.vz * delta_time
        
        # Update alpha based on lifetime (fade out)
        life_remaining = 1.0 - (self.age / self.lifetime)
        self.alpha = int(255 * life_remaining)
    
    def kill(self):
        """Deactivate this particle"""
        self.is_alive = False
        self.age = self.lifetime
    
    def get_position(self) -> Tuple[float, float, float]:
        """Get current position"""
        return (self.x, self.y, self.z)
    
    def get_velocity(self) -> Tuple[float, float, float]:
        """Get current velocity"""
        return (self.vx, self.vy, self.vz)
    
    def get_speed(self) -> float:
        """Get current speed (magnitude of velocity)"""
        return math.sqrt(self.vx**2 + self.vy**2 + self.vz**2)
    
    def apply_force(self, fx: float, fy: float, fz: float):
        """
        Apply a force to the particle
        
        Args:
            fx, fy, fz: Force components (cm/s²)
        """
        self.ax += fx / self.mass
        self.ay += fy / self.mass
        self.az += fz / self.mass
    
    def set_color(self, r: int, g: int, b: int):
        """Set particle color"""
        self.color = (r, g, b)
    
    def set_alpha(self, alpha: int):
        """Set particle alpha"""
        self.alpha = max(0, min(255, alpha))
    
    def enable_trail(self, length: int = 10):
        """
        Enable particle trail
        
        Args:
            length: Number of trail positions to store
        """
        self.has_trail = True
        self.trail_length = length
        self.trail_positions = []
    
    def get_life_fraction(self) -> float:
        """
        Get fraction of life remaining (0-1)
        
        Returns:
            1.0 at birth, 0.0 at death
        """
        if self.lifetime <= 0:
            return 0.0
        return max(0.0, 1.0 - (self.age / self.lifetime))


class FireworkParticle(Particle):
    """
    Specialized particle for firework effects
    Adds firework-specific properties and behaviors
    """
    
    def __init__(self):
        """Initialize firework particle"""
        super().__init__()
        
        # Firework-specific properties
        self.brightness = 1.0  # Brightness multiplier
        self.sparkle = False  # Whether particle sparkles
        self.sparkle_rate = 0.0  # Sparkle frequency
        self.sparkle_phase = 0.0  # Current sparkle phase
        
        # Color transition
        self.color_start = (255, 255, 255)
        self.color_end = (255, 255, 255)
        self.use_color_transition = False
    
    def spawn_firework(self, x: float, y: float, z: float,
                       vx: float, vy: float, vz: float,
                       color: Tuple[int, int, int],
                       lifetime: float,
                       size: float = 3.0,
                       brightness: float = 1.0,
                       sparkle: bool = False):
        """
        Spawn a firework particle with additional properties
        
        Args:
            x, y, z: Initial position
            vx, vy, vz: Initial velocity
            color: RGB color
            lifetime: Lifetime in seconds
            size: Visual size
            brightness: Brightness multiplier
            sparkle: Whether to sparkle
        """
        self.spawn(x, y, z, vx, vy, vz, color, lifetime, size)
        self.brightness = brightness
        self.sparkle = sparkle
        
        if sparkle:
            self.sparkle_rate = 5.0  # 5 Hz
            self.sparkle_phase = 0.0
    
    def set_color_transition(self, start_color: Tuple[int, int, int],
                            end_color: Tuple[int, int, int]):
        """
        Enable color transition over lifetime
        
        Args:
            start_color: RGB color at birth
            end_color: RGB color at death
        """
        self.color_start = start_color
        self.color_end = end_color
        self.use_color_transition = True
    
    def update(self, delta_time: float):
        """Update firework particle with special effects"""
        super().update(delta_time)
        
        if not self.is_alive:
            return
        
        # Update sparkle
        if self.sparkle:
            self.sparkle_phase += delta_time * self.sparkle_rate * 2 * math.pi
            sparkle_factor = (math.sin(self.sparkle_phase) + 1) / 2
            self.brightness = 0.5 + sparkle_factor * 0.5
        
        # Update color transition
        if self.use_color_transition:
            t = self.age / self.lifetime
            r = int(self.color_start[0] + (self.color_end[0] - self.color_start[0]) * t)
            g = int(self.color_start[1] + (self.color_end[1] - self.color_start[1]) * t)
            b = int(self.color_start[2] + (self.color_end[2] - self.color_start[2]) * t)
            self.color = (r, g, b)
    
    def get_render_color(self) -> Tuple[int, int, int]:
        """
        Get color adjusted for brightness
        
        Returns:
            RGB color tuple with brightness applied
        """
        r = int(min(255, self.color[0] * self.brightness))
        g = int(min(255, self.color[1] * self.brightness))
        b = int(min(255, self.color[2] * self.brightness))
        return (r, g, b)