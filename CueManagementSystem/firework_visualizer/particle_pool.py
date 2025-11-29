"""
Particle Pool - Efficient particle management with object pooling
Pre-allocates particles for reuse to avoid memory allocation overhead
"""

from typing import List, Optional
import config
from firework_visualizer.particle import Particle, FireworkParticle


class ParticlePool:
    """
    Object pool for efficient particle management
    Pre-allocates particles and reuses them to avoid garbage collection
    """
    
    def __init__(self, pool_size: int = None):
        """
        Initialize particle pool
        
        Args:
            pool_size: Number of particles to pre-allocate
        """
        if pool_size is None:
            pool_size = config.PARTICLE_POOL_SIZE
        
        self.pool_size = pool_size
        self.particles: List[FireworkParticle] = []
        self.active_particles: List[FireworkParticle] = []
        self.inactive_particles: List[FireworkParticle] = []
        
        # Statistics
        self.total_spawned = 0
        self.peak_active = 0
        
        # Pre-allocate all particles
        self._initialize_pool()
        
        print(f"Particle Pool initialized: {pool_size} particles pre-allocated")
    
    def _initialize_pool(self):
        """Pre-allocate all particles in the pool"""
        for _ in range(self.pool_size):
            particle = FireworkParticle()
            self.particles.append(particle)
            self.inactive_particles.append(particle)
    
    def spawn_particle(self, x: float, y: float, z: float,
                      vx: float, vy: float, vz: float,
                      color: tuple,
                      lifetime: float,
                      size: float = 3.0,
                      brightness: float = 1.0,
                      sparkle: bool = False) -> Optional[FireworkParticle]:
        """
        Spawn a new particle from the pool
        
        Args:
            x, y, z: Initial position
            vx, vy, vz: Initial velocity
            color: RGB color tuple
            lifetime: Particle lifetime in seconds
            size: Visual size
            brightness: Brightness multiplier
            sparkle: Whether to sparkle
        
        Returns:
            FireworkParticle instance or None if pool exhausted
        """
        # Get an inactive particle
        if not self.inactive_particles:
            # Pool exhausted - could expand pool or return None
            return None
        
        particle = self.inactive_particles.pop()
        
        # Initialize the particle
        particle.spawn_firework(x, y, z, vx, vy, vz, color, lifetime, 
                               size, brightness, sparkle)
        
        # Add to active list
        self.active_particles.append(particle)
        
        # Update statistics
        self.total_spawned += 1
        if len(self.active_particles) > self.peak_active:
            self.peak_active = len(self.active_particles)
        
        return particle
    
    def update(self, delta_time: float):
        """
        Update all active particles
        
        Args:
            delta_time: Time step in seconds
        """
        # Update all active particles
        for particle in self.active_particles[:]:  # Copy list to allow removal
            particle.update(delta_time)
            
            # If particle died, return it to pool
            if not particle.is_alive:
                self.active_particles.remove(particle)
                self.inactive_particles.append(particle)
    
    def get_active_particles(self) -> List[FireworkParticle]:
        """
        Get list of all active particles
        
        Returns:
            List of active FireworkParticle instances
        """
        return self.active_particles
    
    def get_active_count(self) -> int:
        """Get number of active particles"""
        return len(self.active_particles)
    
    def get_available_count(self) -> int:
        """Get number of available (inactive) particles"""
        return len(self.inactive_particles)
    
    def clear_all(self):
        """Kill all active particles and return them to pool"""
        for particle in self.active_particles:
            particle.kill()
        
        self.inactive_particles.extend(self.active_particles)
        self.active_particles.clear()
    
    def get_statistics(self) -> dict:
        """
        Get pool statistics
        
        Returns:
            Dictionary with pool statistics
        """
        return {
            'pool_size': self.pool_size,
            'active': len(self.active_particles),
            'available': len(self.inactive_particles),
            'total_spawned': self.total_spawned,
            'peak_active': self.peak_active,
            'utilization': len(self.active_particles) / self.pool_size * 100
        }
    
    def print_statistics(self):
        """Print pool statistics to console"""
        stats = self.get_statistics()
        print("\nParticle Pool Statistics:")
        print(f"  Pool Size: {stats['pool_size']}")
        print(f"  Active: {stats['active']}")
        print(f"  Available: {stats['available']}")
        print(f"  Total Spawned: {stats['total_spawned']}")
        print(f"  Peak Active: {stats['peak_active']}")
        print(f"  Utilization: {stats['utilization']:.1f}%")