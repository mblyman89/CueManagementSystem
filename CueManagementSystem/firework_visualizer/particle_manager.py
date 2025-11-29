"""
Particle Manager - Central management system for all particles
Coordinates particle pool, physics, and rendering
"""

import random
import math
from typing import Tuple, List
import config
from firework_visualizer.particle_pool import ParticlePool
from firework_visualizer.particle_renderer import ParticleRenderer
from firework_visualizer.particle import FireworkParticle


class ParticleManager:
    """
    Central particle management system
    Handles particle lifecycle, physics, and rendering
    """
    
    def __init__(self, camera):
        """
        Initialize particle manager
        
        Args:
            camera: Camera3D instance
        """
        self.camera = camera
        
        # Core systems
        self.pool = ParticlePool(config.PARTICLE_POOL_SIZE)
        self.renderer = ParticleRenderer(camera)
        
        # Wind system
        self.wind_enabled = False
        self.wind_speed = config.WIND_SPEED
        self.wind_direction = config.WIND_DIRECTION  # degrees
        
        # Statistics
        self.total_particles_spawned = 0
        
        print("Particle Manager initialized")
        print(f"  - Pool size: {config.PARTICLE_POOL_SIZE}")
        print(f"  - Max particles: {config.MAX_PARTICLES}")
        print(f"  - Culling distance: {config.CULLING_DISTANCE} cm")
    
    def spawn_particle(self, position=None, velocity=None, x=None, y=None, z=None,
                      vx=None, vy=None, vz=None,
                      color: Tuple[int, int, int] = (255, 255, 255),
                      lifetime: float = 1.0,
                      size: float = 3.0,
                      brightness: float = 1.0,
                      sparkle: bool = False) -> FireworkParticle:
        """
        Spawn a single particle
        
        Args:
            position: [x, y, z] list/tuple (alternative to x, y, z)
            velocity: [vx, vy, vz] list/tuple (alternative to vx, vy, vz)
            x, y, z: Initial position (cm)
            vx, vy, vz: Initial velocity (cm/s)
            color: RGB color tuple
            lifetime: Particle lifetime in seconds
            size: Visual size in pixels
            brightness: Brightness multiplier
            sparkle: Whether particle sparkles
        
        Returns:
            FireworkParticle instance or None if pool exhausted
        """
        # Handle position parameter
        if position is not None:
            x, y, z = position
        elif x is None or y is None or z is None:
            x, y, z = 0, 0, 0
            
        # Handle velocity parameter
        if velocity is not None:
            vx, vy, vz = velocity
        elif vx is None or vy is None or vz is None:
            vx, vy, vz = 0, 0, 0
        
        particle = self.pool.spawn_particle(
            x, y, z, vx, vy, vz, color, lifetime, size, brightness, sparkle
        )
        
        if particle:
            self.total_particles_spawned += 1
        
        return particle
    
    def spawn_burst(self, x: float, y: float, z: float,
                   num_particles: int,
                   speed: float,
                   color: Tuple[int, int, int],
                   lifetime: float,
                   size: float = 3.0,
                   spread: float = 1.0) -> List[FireworkParticle]:
        """
        Spawn a burst of particles in all directions
        
        Args:
            x, y, z: Center position
            num_particles: Number of particles to spawn
            speed: Initial speed (cm/s)
            color: RGB color
            lifetime: Particle lifetime
            size: Visual size
            spread: Spread factor (1.0 = full sphere)
        
        Returns:
            List of spawned particles
        """
        particles = []
        
        for _ in range(num_particles):
            # Random direction on sphere
            theta = random.uniform(0, 2 * math.pi)  # Azimuth
            phi = random.acos(random.uniform(-1, 1))  # Inclination
            
            # Apply spread factor
            phi = phi * spread
            
            # Convert to velocity components
            vx = speed * math.sin(phi) * math.cos(theta)
            vy = speed * math.sin(phi) * math.sin(theta)
            vz = speed * math.cos(phi)
            
            # Spawn particle
            particle = self.spawn_particle(
                x, y, z, vx, vy, vz, color, lifetime, size
            )
            
            if particle:
                particles.append(particle)
        
        return particles
    
    def spawn_cone(self, x: float, y: float, z: float,
                  direction: Tuple[float, float, float],
                  num_particles: int,
                  speed: float,
                  cone_angle: float,
                  color: Tuple[int, int, int],
                  lifetime: float,
                  size: float = 3.0) -> List[FireworkParticle]:
        """
        Spawn particles in a cone shape
        
        Args:
            x, y, z: Origin position
            direction: Direction vector (dx, dy, dz)
            num_particles: Number of particles
            speed: Initial speed
            cone_angle: Cone half-angle in degrees
            color: RGB color
            lifetime: Particle lifetime
            size: Visual size
        
        Returns:
            List of spawned particles
        """
        particles = []
        
        # Normalize direction
        dx, dy, dz = direction
        length = math.sqrt(dx**2 + dy**2 + dz**2)
        if length > 0:
            dx /= length
            dy /= length
            dz /= length
        
        cone_rad = math.radians(cone_angle)
        
        for _ in range(num_particles):
            # Random angle within cone
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0, cone_rad)
            
            # Create velocity vector within cone
            # This is simplified - proper cone sampling would use rotation matrices
            vx = speed * (dx + math.sin(phi) * math.cos(theta))
            vy = speed * (dy + math.sin(phi) * math.sin(theta))
            vz = speed * (dz + math.cos(phi))
            
            particle = self.spawn_particle(
                x, y, z, vx, vy, vz, color, lifetime, size
            )
            
            if particle:
                particles.append(particle)
        
        return particles
    
    def update(self, delta_time: float):
        """
        Update all particles
        
        Args:
            delta_time: Time step in seconds
        """
        # Apply wind to all active particles
        if self.wind_enabled and self.wind_speed > 0:
            self._apply_wind(delta_time)
        
        # Update particle pool (physics)
        self.pool.update(delta_time)
    
    def _apply_wind(self, delta_time: float):
        """
        Apply wind force to all active particles
        
        Args:
            delta_time: Time step in seconds
        """
        # Convert wind direction to radians
        wind_rad = math.radians(self.wind_direction)
        
        # Calculate wind force components
        wind_fx = self.wind_speed * math.cos(wind_rad)
        wind_fy = self.wind_speed * math.sin(wind_rad)
        wind_fz = 0  # Wind is horizontal
        
        # Apply to all particles
        for particle in self.pool.get_active_particles():
            particle.apply_force(wind_fx, wind_fy, wind_fz)
    
    def render(self, renderer):
        """
        Render all particles
        
        Args:
            renderer: SceneRenderer instance
        """
        particles = self.pool.get_active_particles()
        
        # Render particle trails first (behind particles)
        self.renderer.render_particle_trails(particles, renderer)
        
        # Render particles
        self.renderer.render_particles(particles, renderer)
    
    def get_active_count(self) -> int:
        """Get number of active particles"""
        return self.pool.get_active_count()
    
    def get_statistics(self) -> dict:
        """
        Get comprehensive statistics
        
        Returns:
            Dictionary with all statistics
        """
        pool_stats = self.pool.get_statistics()
        render_stats = self.renderer.get_statistics()
        
        return {
            'pool': pool_stats,
            'rendering': render_stats,
            'total_spawned': self.total_particles_spawned,
            'wind_enabled': self.wind_enabled,
        }
    
    def print_statistics(self):
        """Print comprehensive statistics"""
        stats = self.get_statistics()
        
        print("\n" + "=" * 60)
        print("Particle System Statistics")
        print("=" * 60)
        
        print("\nParticle Pool:")
        print(f"  Active: {stats['pool']['active']}")
        print(f"  Available: {stats['pool']['available']}")
        print(f"  Peak Active: {stats['pool']['peak_active']}")
        print(f"  Utilization: {stats['pool']['utilization']:.1f}%")
        
        print("\nRendering:")
        print(f"  Rendered: {stats['rendering']['rendered']}")
        print(f"  Culled: {stats['rendering']['culled']}")
        print(f"  Cull Rate: {stats['rendering']['cull_percentage']:.1f}%")
        
        print("\nTotal:")
        print(f"  Total Spawned: {stats['total_spawned']}")
        print(f"  Wind: {'Enabled' if stats['wind_enabled'] else 'Disabled'}")
        
        print("=" * 60)
    
    def clear_all(self):
        """Clear all particles"""
        self.pool.clear_all()
    
    def set_wind(self, speed: float, direction: float):
        """
        Set wind parameters
        
        Args:
            speed: Wind speed in cm/s
            direction: Wind direction in degrees (0 = north, 90 = east)
        """
        self.wind_speed = speed
        self.wind_direction = direction
        self.wind_enabled = speed > 0
    
    def enable_wind(self, enabled: bool = True):
        """Enable or disable wind"""
        self.wind_enabled = enabled