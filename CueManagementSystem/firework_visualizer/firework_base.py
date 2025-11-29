"""
Base Firework Class - Foundation for all firework types
Provides common functionality for particle generation, physics, and lifecycle
"""

import math
import random
from typing import Tuple, List
from config import *


class FireworkBase:
    """
    Base class for all firework types.
    
    Provides common functionality:
    - Particle spawning and management
    - Lifecycle tracking (age, completion)
    - Color management
    - Physics helpers
    """
    
    def __init__(self, position: Tuple[float, float, float], 
                 velocity: Tuple[float, float, float],
                 color: Tuple[int, int, int],
                 particle_manager):
        """
        Initialize base firework.
        
        Args:
            position: (x, y, z) burst position in cm
            velocity: (vx, vy, vz) shell velocity at burst in cm/s
            color: (r, g, b) primary color
            particle_manager: ParticleManager instance for spawning particles
        """
        self.position = list(position)
        self.velocity = list(velocity)
        self.color = color
        self.particle_manager = particle_manager
        
        # Lifecycle
        self.age = 0.0
        self.is_complete = False
        self.duration = 3.0  # Default duration, override in subclasses
        
        # Particle tracking
        self.particles_spawned = 0
        self.max_particles = 1000  # Default, override in subclasses
        
        # Type identification
        self.firework_type = "Base"
        
    def update(self, dt: float):
        """
        Update firework state.
        
        Args:
            dt: Time step in seconds
        """
        self.age += dt
        
        # Check completion
        if self.age >= self.duration:
            self.is_complete = True
    
    def spawn_particles(self, dt: float):
        """
        Spawn particles for this frame.
        Override in subclasses to implement specific patterns.
        
        Args:
            dt: Time step in seconds
        """
        pass
    
    def _spawn_particle(self, position: List[float], velocity: List[float],
                       color: Tuple[int, int, int], lifetime: float,
                       size: float = 3.0, brightness: float = 1.0,
                       sparkle: bool = False):
        """
        Helper to spawn a single particle.
        
        Args:
            position: [x, y, z] position
            velocity: [vx, vy, vz] velocity
            color: (r, g, b) color
            lifetime: Particle lifetime in seconds
            size: Visual size
            brightness: Brightness multiplier
            sparkle: Whether particle sparkles
        """
        if self.particles_spawned < self.max_particles:
            self.particle_manager.spawn_particle(
                position=position,
                velocity=velocity,
                color=color,
                lifetime=lifetime,
                size=size,
                brightness=brightness,
                sparkle=sparkle
            )
            self.particles_spawned += 1
    
    def _spawn_sphere_burst(self, num_particles: int, speed_min: float, 
                           speed_max: float, color: Tuple[int, int, int],
                           lifetime: float, size: float = 3.0,
                           brightness: float = 1.0, sparkle: bool = False):
        """
        Spawn particles in a spherical pattern.
        
        Args:
            num_particles: Number of particles to spawn
            speed_min: Minimum particle speed (cm/s)
            speed_max: Maximum particle speed (cm/s)
            color: Particle color
            lifetime: Particle lifetime
            size: Particle size
            brightness: Brightness multiplier
            sparkle: Whether particles sparkle
        """
        for i in range(num_particles):
            # Random direction on sphere
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0, math.pi)
            
            speed = random.uniform(speed_min, speed_max)
            
            # Convert spherical to cartesian
            vx = speed * math.sin(phi) * math.cos(theta)
            vy = speed * math.sin(phi) * math.sin(theta)
            vz = speed * math.cos(phi)
            
            # Add shell velocity
            vx += self.velocity[0] * 0.1
            vy += self.velocity[1] * 0.1
            vz += self.velocity[2] * 0.1
            
            self._spawn_particle(
                position=list(self.position),
                velocity=[vx, vy, vz],
                color=color,
                lifetime=lifetime,
                size=size,
                brightness=brightness,
                sparkle=sparkle
            )
    
    def _spawn_cone_burst(self, num_particles: int, speed_min: float,
                         speed_max: float, cone_angle: float,
                         direction: Tuple[float, float, float],
                         color: Tuple[int, int, int], lifetime: float,
                         size: float = 3.0, brightness: float = 1.0):
        """
        Spawn particles in a cone pattern.
        
        Args:
            num_particles: Number of particles
            speed_min: Minimum speed
            speed_max: Maximum speed
            cone_angle: Cone half-angle in degrees
            direction: (x, y, z) cone direction (normalized)
            color: Particle color
            lifetime: Particle lifetime
            size: Particle size
            brightness: Brightness multiplier
        """
        # Normalize direction
        mag = math.sqrt(sum(d*d for d in direction))
        if mag > 0:
            direction = tuple(d/mag for d in direction)
        else:
            direction = (0, 0, 1)
        
        cone_rad = math.radians(cone_angle)
        
        for i in range(num_particles):
            # Random angle within cone
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0, cone_rad)
            
            speed = random.uniform(speed_min, speed_max)
            
            # Create velocity in cone
            # This is simplified - proper cone would require rotation matrix
            vx = speed * math.sin(phi) * math.cos(theta)
            vy = speed * math.sin(phi) * math.sin(theta)
            vz = speed * math.cos(phi)
            
            # Rotate to align with direction (simplified)
            vx += direction[0] * speed * 0.5
            vy += direction[1] * speed * 0.5
            vz += direction[2] * speed * 0.5
            
            self._spawn_particle(
                position=list(self.position),
                velocity=[vx, vy, vz],
                color=color,
                lifetime=lifetime,
                size=size,
                brightness=brightness
            )
    
    def _color_variation(self, base_color: Tuple[int, int, int],
                        variation: int = 30) -> Tuple[int, int, int]:
        """
        Create a color variation from base color.
        
        Args:
            base_color: (r, g, b) base color
            variation: Maximum variation per channel
            
        Returns:
            (r, g, b) varied color
        """
        r = max(0, min(255, base_color[0] + random.randint(-variation, variation)))
        g = max(0, min(255, base_color[1] + random.randint(-variation, variation)))
        b = max(0, min(255, base_color[2] + random.randint(-variation, variation)))
        return (r, g, b)
    
    def _interpolate_color(self, color1: Tuple[int, int, int],
                          color2: Tuple[int, int, int],
                          t: float) -> Tuple[int, int, int]:
        """
        Interpolate between two colors.
        
        Args:
            color1: First color
            color2: Second color
            t: Interpolation factor (0-1)
            
        Returns:
            Interpolated color
        """
        t = max(0.0, min(1.0, t))
        r = int(color1[0] + (color2[0] - color1[0]) * t)
        g = int(color1[1] + (color2[1] - color1[1]) * t)
        b = int(color1[2] + (color2[2] - color1[2]) * t)
        return (r, g, b)
    
    def get_stats(self) -> dict:
        """
        Get firework statistics.
        
        Returns:
            Dictionary with stats
        """
        return {
            'type': self.firework_type,
            'age': self.age,
            'duration': self.duration,
            'particles_spawned': self.particles_spawned,
            'is_complete': self.is_complete
        }